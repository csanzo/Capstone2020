import vicorlib

device = vicorlib.Arduino('/dev/ttyACM0',9600)
device.i2cdetect()