import numpy as np
import serial
import cv2
import time

#
#TODO - Fix known bug: drag selection must be made from left up to down right
#

# Usage:
#   - plug the USB camera and the Arduino UNO programmed with 'Crivit_ChestBelt_TX_Emulator.ino'
#   - set the 'COM_PORT' number taken by the Arduino UNO
#   - if it's missing, create folder 'captures' near 'OpenCV_Controlled_TX_Emulator.py'
#   - 3 windows will open, 1'st is a color live image, 2'nd a black and white, 3'rd with your selection
#   - put the Crivit HRM wrist-watch in front of the USB camera and set it to HRM monitor mode
#   - in the first 2 windows, adjust the sliders for the camera sensitivity and the black and white threshold
#   - in the 2'nd window, select (by mouse dragging) a blinking area from the blinking heart displayed by the watch
#   - tip: a single point selection (a click instead of a drag) works very good
#   - the selected area will be seen live in the 3'rd window
#   - all the bitstreams written in 'captures/input_bitstreams.txt' will be sent one by one to the radio Tx
#   - the script will look in the 3'rd window if the heart symbol displayed by the wrist-watch is blinking
#   - if blinking, a jpg snapshot will be saved in 'captures'
#   - results will be displayed on the command line, then added to the log file 'captures/working_bitstreams.csv'
#   - NOTE: Do not close the live windows. To exit teh script, press the 'ESC' key.

# Installation:
#   pip install numpy
#   pip install pyserial
#
# to install OpenCV (32-bit) download and unpack, then go to folder
#   'opencv\build\python\2.7\x86\'
#   and copy the file 'cv2.pyd' into folder 'C:\Python27\Lib\site-packages'
#
# To check the OpenCV installation, open Python and type
#   >>> import cv2
#   >>> print cv2.__version__
#   3.2.0
#

# Arduino COM port
COM_PORT = 'COM4'
STEP_TEST_SECONDS = 7
BLINKING_THRESHOLD = 20  # Average white threshold 0..100%

# Radio TX bitstreams
BITSTREAM_KNOWN_GOOD = '1111000101000100011'
BITSTREAM_KNOWN_BAD = '1010101010101010101'

# Global constants
CAM_WIDTH = 640
CAM_HEIGHT = 480

# Naming windows
wnd_1 = 'Live'
wnd_2 = 'Threshold'
wnd_3 = 'Selected'

# Naming sliders
ex = 'Exposure'
th = 'Threshold'

# Global variables for mouse drag selection
img = np.zeros((CAM_HEIGHT, CAM_WIDTH, 3), np.uint8)

drawing = False     # true if mouse is pressed
ix, iy = -1, -1
dragging = False
pix, piy, px, py = -1, -1, -1, -1
finished = False    # true if a drag selection has ended
fx, fy = -1, -1

# Initialize serial port
ser = serial.Serial(port=COM_PORT, baudrate=9600,
                    bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                    timeout=0, xonxoff=False, rtscts=False, dsrdtr=False,
                    write_timeout=0, inter_byte_timeout=None)

# Create windows
cv2.namedWindow(wnd_1)              # if 'flags' is missing, the window will auto-resize,
cv2.namedWindow(wnd_2)              #   and any manual resize is disabled
cv2.namedWindow(wnd_3, flags=0)     # 0 is for a manually adjustable window

# Grab first webcam
first_camera = cv2.VideoCapture(0)

# Set webcam parameters
first_camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
first_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

first_camera.set(cv2.CAP_PROP_FPS, 30)
first_camera.set(cv2.CAP_PROP_EXPOSURE, 15)


# ---------- Sliders --------------
# Workaround function - 'optional' argument is required for trackbar creation parameters
def nothing(x):
    pass

# Slider for webcam exposure
cv2.createTrackbar(ex, wnd_1, 0, 255, nothing)
cv2.setTrackbarPos(ex, wnd_1, 10)

# Slider for threshold filtering
cv2.createTrackbar(th, wnd_2, 0, 255, nothing)
cv2.setTrackbarPos(th, wnd_2, 50)


# ---------- Mouse ----------------
# mouse callback function
def draw_drag(event, x, y, flags, param):
    global ix, iy, drawing
    global pix, piy, px, py, dragging
    global fx, fy, finished

    if x < 0:   x = 0
    if y < 0:   y = 0
    if x >= CAM_WIDTH:  x = CAM_WIDTH - 1
    if y >= CAM_HEIGHT: y = CAM_HEIGHT - 1

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        if finished == True:
            # delete previous
            cv2.rectangle(img, (ix, iy), (fx, fy), (0, 0, 0), 0)

        finished = False
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            if dragging == True:
                # delete previous
                cv2.rectangle(img, (pix, piy), (px, py), (0, 0, 0), 0)

            dragging = True
            cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 0)
            pix, piy, px, py = ix, iy, x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(img, (pix, piy), (px, py), (0, 0, 0), 0)
        dragging = False
        cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 0)
        finished = True
        fx, fy = x, y

# bind the callback function to a specified window
cv2.setMouseCallback(wnd_2, draw_drag)


# ---------- Bitstream combinations to be tested ----------
def get_next_bitstream():
    next_bs = input_bitstreams_file.readline()
    next_bs = next_bs[:-1]
    return next_bs


# ---------- Blinking detection ----------
def was_blinking():
    global sample_integrator
    return sample_integrator > BLINKING_THRESHOLD


# ---------- MAIN ----------
# Open input file
input_bitstreams_file = open('captures/input_bitstreams.txt', 'r')

# Main loop preset
prev_time = time.time()
sample_integrator = 0
frame_counter = 0
next_step = 'Tx the safe bitstream'
# next_step = 'Tx the test bitstream'

# Main loop
while True:
    # ---------- Video processing ----------
    exp = cv2.getTrackbarPos(ex, wnd_1)
    first_camera.set(cv2.CAP_PROP_EXPOSURE, exp)

    ret, color_frame = first_camera.read()
    cv2.imshow(wnd_1, color_frame)

    gray_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
    thr = cv2.getTrackbarPos(th, wnd_2)
    ret, filtered_frame = cv2.threshold(gray_frame, thr, 255, cv2.THRESH_BINARY)

    # mark selected area
    mixed_frame = cv2.cvtColor(filtered_frame, cv2.COLOR_GRAY2RGB)
    cv2.addWeighted(mixed_frame, 0.8, img, 1.0, 0.0, mixed_frame)
    cv2.imshow(wnd_2, mixed_frame)

    if finished == True:
        crop_zone = filtered_frame[iy:fy + 1, ix:fx + 1]
    else:
        crop_zone = filtered_frame[:, :]

    cv2.imshow(wnd_3, crop_zone)

    # keep running the integrator
    sample = crop_zone.mean()
    sample_integrator += sample
    frame_counter += 1

    # ---------- Radio Tx testing algorithm ----------
    now_time = time.time()
    passed_time = now_time - prev_time

    # Testing steps runs once at every 5 seconds until all the numbers were radio transmitted
    if passed_time >= STEP_TEST_SECONDS:
        step_name = next_step
        timestamp = time.strftime('%Y-%m-%d_%H_%M_%S', time.localtime(now_time))
        sample_integrator = int(sample_integrator/frame_counter/2.55)

        if step_name == 'Tx the safe bitstream':
            print
            print '******************************************************************************'
        else:
            print
        print timestamp, '   sample_integrator = ', sample_integrator

        if step_name == 'Tx the safe bitstream':
            print step_name,
            ser.write(BITSTREAM_KNOWN_GOOD + '\n')
            print ': ', BITSTREAM_KNOWN_GOOD
            next_step = 'Check if still blinking'

        elif step_name == 'Check if still blinking':
            print step_name,
            still_blinking = was_blinking()
            print ': ', still_blinking
            if not still_blinking:
                print '!!! ERROR !!! - Can not detect blinking after the safe number was transmitted.'
                next_step = "Error 1"
            else:
                next_step = 'Tx the bad bitstream'

        elif step_name == 'Tx the bad bitstream':
            print step_name,
            ser.write(BITSTREAM_KNOWN_BAD + '\n')
            print ': ', BITSTREAM_KNOWN_BAD
            next_step = 'Wait for inertial blinking to end'

        elif step_name == 'Wait for inertial blinking to end':
            print step_name
            next_step = 'Check if stopped blinking'

        elif step_name == 'Check if stopped blinking':
            print step_name,
            still_blinking = was_blinking()
            print ': ', not still_blinking
            if still_blinking:
                print '!!! ERROR !!! - Still blinking after the bad number was transmitted.'
                next_step = 'Error 2'
            else:
                next_step = 'Tx the test bitstream'

        elif step_name == 'Tx the test bitstream':
            print step_name,
            bitstream_under_test = get_next_bitstream()
            ser.write(bitstream_under_test + '\n')
            print ':                      ', bitstream_under_test
            if len(bitstream_under_test) > 3:
                next_step = 'Check if blinking after the test bitstream'
            else:
                next_step = 'Exit'

        # This step is not necessary, since the blinking was already stopped by sending the bad number
        #   also, a possible blinking start is fast enough to not require a full waiting step for it
        elif step_name == 'Wait for any possible inertial blinking to end':
            print step_name
            next_step = 'Check if still blinking for the tested bitstream'

        elif step_name == 'Check if blinking after the test bitstream':
            print step_name,
            still_blinking = was_blinking()
            print ': ', still_blinking

            # timestamp = time.strftime('%Y-%m-%d_%H_%M_%S', time.localtime(now_time))
            csv_file = open('captures/working_bitstreams.csv', 'a')
            extra_info = ',' + str(sample_integrator) + ',' + str (BLINKING_THRESHOLD)\
                         + ',' + str(STEP_TEST_SECONDS) + '\n'
            if still_blinking:
                print '    *****'
                print '    ***** A good bitstream was found:', bitstream_under_test
                print '    *****'

                # save a webcam snapshot
                # watermark it with timestamp and bitstream
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(color_frame,
                            'Blinking% / THRESHOLD% is ' + str(sample_integrator) + '%/' + str (BLINKING_THRESHOLD)
                            + '% after ' + str(STEP_TEST_SECONDS) + ' seconds',
                            (10, 35), font, 0.5, (255, 255, 255), 1)

                cv2.putText(color_frame, timestamp + ' ' + bitstream_under_test,
                            (10, CAM_HEIGHT - 10), font, 0.5, (255, 255, 255), 1)

                # save image file
                filename = 'captures/' + bitstream_under_test + '_' + timestamp + '_WebCam.jpg'
                cv2.imwrite(filename, color_frame)

                # add new line into the csv file
                csv_file.write(timestamp + ',' + filename[9:] + ',' + bitstream_under_test + ',OK' + extra_info)
            else:
                # add new line into the csv file
                csv_file.write(timestamp + ',' + 'None' + ',' + bitstream_under_test + ',BAD' + extra_info)

            csv_file.close()
            next_step = 'Tx the safe bitstream'

        elif step_name == 'Exit':
            print step_name
            break

        else:
            print '*** ERROR named: "', step_name, '" detected. ***'
            # STEP x - Reset the testing steps (state machine reset)
            next_step = 'Tx the safe bitstream'

        # Reset the integrator
        sample_integrator = 0
        frame_counter = 0
        prev_time = now_time

    # ---------- Clean exit ----------
    # press Esc key to quit, please DO NOT CLOSE the video windows manually
    if (cv2.waitKey(1) & 0xFF == 27) or (next_step == 'Exit'):
        break
first_camera.release()
cv2.destroyAllWindows()
ser.close()

