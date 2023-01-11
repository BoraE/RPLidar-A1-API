import serial
import time
import binascii

ser = serial.Serial("COM4", 115200, timeout=1)
print(ser)

command = b'\xA5\x40'
ser.write(command)
time.sleep(0.001)
s = ser.read(100)
print(s.decode("ascii"))

command = b'\xA5\x25'
ser.write(command)
time.sleep(0.001)

command = b'\xA5\x50'
ser.write(command)
s = ser.read(27)
s = s[7:]
print("Model: {0}  Firmware: {1}.{2} Hardware: {3}".format(s[0], s[2], s[1], s[3]))
time.sleep(0.001)

command = b'\xA5\x20'
ser.write(command)
for i in range(10):
    s = ser.read(200)
    print(s)

ser.close()
