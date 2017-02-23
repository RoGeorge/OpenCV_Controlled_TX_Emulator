# OpenCV_Controlled_TX_Emulator
A Python script that sends radio bitstreams using an Arduino UNO radio Tx while looking at a live USB camera for visual feedback from the radio Rx device which is a Crivit Sports Heart Rate Monitor wrist-watch.

```
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
```