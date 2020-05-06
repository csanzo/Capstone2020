import vicorlib

device = vicorlib.Arduino('/dev/ttyACM0',9600)

input("Press ENTER to run pulldown voltage/resistance test\n") 

R=9970

device.program_dut(0x1e, 0x00)

device.select_pin(1, 2)
device.force_voltage(1, 1.5)
Vst=device.measure_voltage(1)

device.select_pin(0, 2, force=False)
device.program_dut(0x1e, 0x01)
Vpd=device.measure_voltage(0)

I=(Vst-Vpd)/R
Rpd=Vpd/I

print("Vst="+str(Vst))
print("Pulldown voltage="+str(Vpd))
print("Current="+str(I))
print("Pulldown resistance="+str(Rpd))