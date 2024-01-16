import serial.tools.list_ports as port_list
ports = list(port_list.comports())
for p in ports:
    print (p)


import serial
import time

serialPort = serial.Serial(
    port="COM10", baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE
)

serialString = ""

while 1:
    # Wait until there is data waiting in the serial buffer
    if serialPort.in_waiting > 0:

        # Read data out of the buffer until a carraige return / new line is found
        serialString = serialPort.readline()

        # Print the contents of the serial data
        try:
            print(serialString.decode("Ascii"))
        except:
            pass