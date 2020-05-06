import vicorlib

# arduino connected will be on port ttyACMx
# can use console command 'ls /dev/ttyACM*'
# to find which port the Arduino is currently on
device = vicorlib.Arduino('/dev/ttyACM0',9600)

print("MUX TEST")
while True:
    channel=input("FSU Channel: ")
    pin=input("DUT pin: ")
    voltage=input("Voltage: ")

    device.select_pin(channel, pin)
    device.force_voltage(channel, voltage)
    device.measure_voltage(channel)