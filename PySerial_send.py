import serial.tools.list_ports as port_list

ports = list(port_list.comports())
for p in ports:
    print(p)

import serial
import time

serialPort = serial.Serial(
    port="COM11", baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE
)

print("Sending 1st time")
serialPort.write(11)

time.sleep(3)

print("Sending 2nd time")
#serialPort.write(chr(int('10010000', base=2)).encode('latin_1'))
byte1 = 144
serialPort.write(chr(byte1).encode('latin_1'))

# Blinken
#while 1:
    # Bild 1 - weiß
    #serialPort.write(chr(int('10010000', base=2)).encode('latin_1'))  # 144
    #serialPort.write(chr(int('00000001', base=2)).encode('latin_1'))  # Picture Nr. 1
    #serialPort.write(chr(int('11100000', base=2)).encode('latin_1'))  # 224
    #serialPort.write(chr(int('00000010', base=2)).encode('latin_1'))  # BRIGHTNESS
    #serialPort.write(chr(int('00000010', base=2)).encode('latin_1'))  # unused

    #time.sleep(1)

    # Bild 0 - schwarz
    #serialPort.write(chr(int('10010000', base=2)).encode('latin_1'))  # 144
    #serialPort.write(chr(int('00000000', base=2)).encode('latin_1'))  # Picture Nr. 0
    #serialPort.write(chr(int('11100000', base=2)).encode('latin_1'))  # 224
    #serialPort.write(chr(int('00000000', base=2)).encode('latin_1'))  # BRIGHTNESS
    #serialPort.write(chr(int('00000000', base=2)).encode('latin_1'))  # unused

    #time.sleep(1)

while 1:
    # Wait until there is data waiting in the serial buffer
    if serialPort.in_waiting > 0:

        # Read data out of the buffer until a carriage return / new line is found
        serialString = serialPort.readline()
        print("after readLine")

        # Print the contents of the serial data
        try:
            print(serialString.decode("Ascii"))
        except:
            pass
