import ctypes
import serial, time

print("Start of Controller")

arduino = serial.Serial('COM3', 115200, timeout=0)
arduino.bytesize = 8
arduino.parity = 'N'
arduino.stopbits = 1

time.sleep(3)


dataArr1 = [144, 1, 224, 10, 10]  # Color
dataArr2 = [144, 99, 224, 0, 10]  # Standby blink
dataArr3 = [144, 0, 224, 0, 10]  # black


def send_function(normArr):
    bytearr = [ctypes.c_ubyte(normArr[0]), ctypes.c_ubyte(normArr[1]), ctypes.c_ubyte(normArr[2]),
               ctypes.c_ubyte(normArr[3]), ctypes.c_ubyte(normArr[4])]
    for x in bytearr:
        bytesWritten = arduino.write(x)


# Go through every LED Poi
for z in range(6):
    dataArr1[0] = 144 + z
    dataArr1[2] = 224 + z
    dataArr2[0] = 144 + z
    dataArr2[2] = 224 + z
    dataArr3[0] = 144 + z
    dataArr3[2] = 224 + z
    # Go through the pictures 0-4
    for y in range(5):
        dataArr1[1] = y
        # First ramp up the brightness
        for x in range(25):
            send_function(dataArr1)
            dataArr1[3] = x
            time.sleep(.01)
        # Then ramp down the brightness
        for x in range(25):
            send_function(dataArr1)
            dataArr1[3] = 25 - x
            time.sleep(.01)

    time.sleep(.1)
    # black and then standby blink
    send_function(dataArr3)
    send_function(dataArr2)

# while True:
# 	data = arduino.readline()
# 	if data:
# 		print ("Data received")
# 		print (data) #strip out the new lines for now
# 		# (better to do .read() in the long run for this reason
