from PIL import Image
from numpy import asarray
import binascii
from os import listdir
from os.path import isfile, join

mypath = './newGraphics_8_bit_bmp'
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

for f in onlyfiles:
    #input bmp has to be 24bit
    image = Image.open(mypath + "/" + f)
    data = asarray(image)
    #print(data)
    #print (''.join('{:02x}'.format(x) for x in data))
    hexdata = binascii.hexlify(bytearray(data))
    #print (hexdata)
    hexdata1 = hexdata.decode("utf-8")
    #print(hexdata1)
    hexdata_2 = ', 0x'.join(hexdata1[i:i+6] for i in range(0, len(hexdata1), 6))
    #print (hexdata_2)
    hexdata_3 = "const unsigned int arrayx[]PROGMEM = { 0x" + hexdata_2 +"};"
    #print (len(hexdata_3))
    #print (hexdata_3)
    f = open(mypath + "/code" + "/" + f + ".txt", "w")
    f.write(hexdata_3)
    f.close()

#Scaling images in future
#https://opensource.com/life/15/2/resize-images-python