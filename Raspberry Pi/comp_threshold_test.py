import vicorlib
import math

# arduino connected will be on port ttyACMx
# can use console command 'ls /dev/ttyACM*'
# to find which port the Arduino is currently on
device = vicorlib.Arduino('/dev/ttyACM0',9600)

input("Press ENTER to run comparator threshold test going UP\n")

device.program_dut(0x13, 0x40)
device.program_dut(0x14, 0x30)
device.program_dut(0x15, 0x00)

# 48 to 1 mux:
# device.select_pin(1, 39)
# device.select_pin(0, 37)
# 4 to 1 mux:
device.select_pin(1, 3)
device.select_pin(0, 3, force=False)

voltage=1
while voltage < 5:
    device.force_voltage(1, voltage)
    comparator = device.measure_voltage(0)

    if not math.isclose(comparator, 0, abs_tol=0.5):
        threshold = device.measure_voltage(1)
        break
    else:
        voltage += 0.01

if threshold:
    print("Threshold UP found: "+str(threshold))
else:
    print("Threshold not found.")

input("Press ENTER to run comparator threshold test going DOWN\n")
threshold=0

while voltage > 1:
    device.force_voltage(1, voltage)
    comparator = device.measure_voltage(0)

    if not math.isclose(comparator, 5, abs_tol=0.5):
        threshold = device.measure_voltage(1)
        break
    else:
        voltage -= 0.01

if threshold:
    print("Threshold DOWN found: "+str(threshold))
else:
    print("Threshold not found.")