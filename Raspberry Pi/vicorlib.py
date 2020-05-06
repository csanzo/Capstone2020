import serial
import time
from inspect import getframeinfo, stack
from colorama import Fore

### CONSTANTS ###
ADC_CH_MAX = 7 # range 0 to 7
FSU_CH_MAX = 1 # range 0 to 1
RSNS_CH_MAX = 3 # range from 0 to 3
DUT_PINS = 48 # range from 1 to 48

VMIN = 0.5 # FIXME: change to 0.0 when DAC issues are resolved
VMAX = 5.0

### SERIAL COMMANDS ###
init = "init\n".encode()
sel_pin = "select_pin\n".encode()
sel_r = "select_r\n".encode()
force_v = "force_v\n".encode()
measure_v = "measure_v\n".encode()
force_i = "force_i\n".encode()
measure_i = "measure_i\n".encode()
prog_dut = "program_dut\n".encode()
prog_dut12 = "program_dut12\n".encode()
rd_dut = "read_dut\n".encode()
rd_dut12 = "read_dut12\n".encode()
i2c = "i2c\n".encode()

### GLOBALS ###
init_success = 0

class Arduino():
    def __init__(self, port, rate):
        print("Initializing. Please wait...")
        self.port = port
        self.rate = rate
        self.ser = serial.Serial(self.port, self.rate)

        self.selected_pin = [0, 0]
        self.invalid_pins = [1, 13, 27, 28, 35, 36, 48]

        self.resistor_map = [39000, 2000, 100, 5]
        
        # sleep for short amount of time to allow serial connection to be made
        # before sending out commands
        time.sleep(0.5)
        self.ser.write(init)
        # sleep after command has been written to wait for it to be received
        time.sleep(0.75)
        # read initialization status messages from ADC/API
        while self.ser.in_waiting is not 0:
            print(self.ser.read_until().strip().decode())
            time.sleep(0.5)

        print("Initialization complete.\n")

    def i2cdetect(self):
        print("Performing I2C Detect:")
        self.ser.write(i2c)
        time.sleep(0.75)
        while self.ser.in_waiting is not 0:
            line = self.ser.read_until().decode().strip('\r\n')
            if line: print(line)
            time.sleep(0.5)
        print("I2C Detect complete.")

    def select_pin(self, channel, pin, force=True):
        try:
            channel = int(channel)
            pin = int(pin)
            force = bool(force)
        except:
            ### 4-to-1 MUX
            self.__log_error("invalid input\nExpected arguments:\n"+
                            "\tchannel - specifies FSU channel, integer from 0 to "+str(FSU_CH_MAX)+"\n"+
                            "\tpin - specifies MUX channel to be selected, integer from 0 to 3\n"+
                            "\tforce - boolean flag for enabling force on the selected channel. Default True\n"+
                            "\nNOTE: The following pins should not be accessed:\n\t"+", ".join(map(str, self.invalid_pins)))

        if pin < 0 or pin > 3:
            self.__log_error("invalid MUX channel, must be between 0 and 3")
        elif channel < 0 or channel > FSU_CH_MAX:
            self.__log_error("invalid FSU channel, must be between 0 and "+str(FSU_CH_MAX))
        ### FIXME: 48-to-1 MUX
        #     self.__log_error("invalid input\nExpected arguments:\n"+
        #                      "\tchannel - specifies FSU channel, integer from 0 to "+str(FSU_CH_MAX)+"\n"+
        #                      "\tpin - specifies DUT pin to bet selected, integer from 1 to "+str(DUT_PINS)+"\n"+
        #                      "\tforce - boolean flag for enabling force on the selected channel. Default True\n"+
        #                      "\nNOTE: The following pins cannot be selected:\n\t"+", ".join(map(str, self.invalid_pins)))
        # if pin < 1 or pin > DUT_PINS:
        #     self.__log_error("invalid DUT pin, must be between 1 and "+str(DUT_PINS))
        # elif channel < 0 or channel > FSU_CH_MAX:
        #     self.__log_error("invalid FSU channel, must be between 0 and "+str(FSU_CH_MAX))
        # elif pin in self.invalid_pins:
        #     self.__log_error("invalid DUT pin. Please do not select the following pins:\n\t"+", ".join(map(str, self.invalid_pins)))
        # elif channel == 0 and selected_pin[1] == pin:
        #     self.__log_error("pin "+pin+" is already selected on channel 1. You cannot select the same pin on different channels.")
        # elif channel == 1 and selected_pin[0] == pin:
        #     self.__log_error("pin "+pin+" is already selected on channel 0. You cannot select the same pin on different channels.")
        
        # self.selected_pin[channel] = pin

        self.ser.write(sel_pin)
        self.ser.write(bytes.fromhex('{:02x}'.format(channel) + 
                                    '{:02x}'.format(pin) +
                                    '{:02x}'.format(int(force))))

        ### 4-to-1 MUX
        print("FSU-"+str(channel)+": Set DUT MUX to channel "+str(pin)+" with force " + ("enabled" if force else "disabled"))
        ### FIXME: 48-to-1 MUX
        #print("FSU-"+str(channel)+": Set DUT pin to "+str(pin)+" with force " + ("enabled" if force else "disabled"))

    def select_resistor(self, channel, resistor):
        try:
            channel = int(channel)
            resistor = int(resistor)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\tchannel - specifies FSU channel, integer from 0 to "+str(FSU_CH_MAX)+"\n"+
                             "\tresistor - specifies resistor MUX channel, integer from 0 to "+str(RSNS_CH_MAX)+"\n"+
                             "Note: Resistor values from channel 0 to "+str(RSNS_CH_MAX)+": "+", ".join(map(str, self.resistor_map)))
        if resistor < 0 or resistor > RSNS_CH_MAX:
            self.__log_error("invalid resistor MUX channel, must be between 0 and "+str(RSNS_CH_MAX)+"\n"+
                             "Note: Resistor values from channel 0 to "+str(RSNS_CH_MAX)+": "+", ".join(map(str, self.resistor_map)))
        elif channel < 0 or channel > FSU_CH_MAX:
            self.__log_error("invalid FSU channel, must be between 0 and "+str(FSU_CH_MAX))
            
        self.ser.write(sel_r)
        self.ser.write(bytes.fromhex('{:02x}'.format(channel) + 
                                    '{:02x}'.format(resistor)))

        print("FSU-"+str(channel)+": Set resistor to "+str(resistor_map[channel])+" ohms")

    def force_voltage(self, channel, voltage):
        try:
            channel = int(channel)
            voltage = float(voltage)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\tchannel - specifies FSU channel to send voltage to, integer from 0 to "+str(FSU_CH_MAX)+"\n"+
                             "\tvoltage - specifies voltage to be set, floating point number from "+str(VMIN)+" to "+str(VMAX))
        if voltage < VMIN or voltage > VMAX:
            self.__log_error("invalid voltage, must be between "+str(VMIN)+" and "+str(VMAX)+"V")
        elif channel < 0 or channel > FSU_CH_MAX:
            self.__log_error("invalid FSU channel, must be between 0 and "+str(FSU_CH_MAX))
        
        self.ser.write(force_v)
        self.ser.write(bytes.fromhex('{:02x}'.format(channel)))
        self.ser.write((str(voltage)+"\n").encode())

        ### 4-to-1 MUX
        print("FSU-"+str(channel)+": Forcing "+str(voltage)+"V")
        ### FIXME: 48-to-1 MUX
        #print("FSU-"+str(channel)+": Forcing "+str(voltage)+"V on pin "+str(self.selected_pin[channel]))

    def measure_voltage(self, channel):
        try:
            channel = int(channel)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\tchannel - specifies FSU channel to measure voltage from, integer from 0 to "+str(FSU_CH_MAX))
        
        self.ser.write(measure_v)
        self.ser.write(bytes.fromhex('{:02x}'.format(channel)))
        voltage = float(self.ser.read_until().strip().decode())
        ### 4-to-1 MUX
        print("FSU-"+str(channel)+": Sensing "+str(voltage)+"V")
        ### FIXME: 48-to-1 MUX
        #print("FSU-"+str(channel)+": Sensing "+str(voltage)+"V on pin "+str(self.selected_pin[channel]))
        return voltage

    def extra_sense(self, adc_channel):
        try:
            adc_channel = int(adc_channel)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\tadc_channel - specified ADC channel 6 or 7 for temporary extra sense capabilities")

        if adc_channel != 6 and adc_channel != 7:
            self.__log_error("extra sense capabilities are currently only available on channel 6 and 7 of the ADC")

        self.ser.write(measure_v)
        self.ser.write(bytes.fromhex('{:02x}'.format(adc_channel)))
        voltage = float(self.ser.read_until().strip().decode())
        ### 4-to-1 MUX
        print("FSU-"+str(channel)+": Sensing "+str(voltage)+"V")
        ### FIXME: 48-to-1 MUX
        #print("FSU-"+str(channel)+": Sensing "+str(voltage)+"V on pin "+str(self.selected_pin[channel]))
        return voltage
    
    def force_current(self, channel, current):
        try:
            channel = int(channel)
            current = float(current)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\tchannel - specifies FSU channel to send current to, integer from 0 to "+str(FSU_CH_MAX)+"\n"+
                             "\tcurrent - specifies current to be set, floating point number")
        if current < 10 or current > 500:
            self.__log_error("invalid current")
        elif channel < 0 or channel > FSU_CH_MAX:
            self.__log_Error("invalid FSU channel, must be between 0 and "+str(FSU_CH_MAX))
            
        self.ser.write(force_i)
        self.ser.write(bytes.fromhex('{:02x}'.format(channel)))
        self.ser.write((str(current / 1000000.0)+"\n").encode())
        ### 4-to-1 MUX
        print("FSU-"+str(channel)+": Forcing "+str(current)+"uA")
        ### FIXME: 48-to-1 MUX
        #print("FSU-"+str(channel)+": Forcing "+str(current)+"uA on pin "+str(self.selected_pin[channel]))

    def measure_current(self, channel):
        try:
            channel = int(channel)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\tchannel - specifies FSU channel to measure voltage from, integer from 0 to "+str(FSU_CH_MAX))

        self.ser.write(measure_i)

        self.ser.write(bytes.fromhex('{:02x}'.format(channel)))
        current = 1000000.0*float(self.ser.read_until().strip().decode())
        ### 4-to-1 MUX
        print("FSU-"+str(channel)+": Sensing "+str(current)+"uA")
        ### FIXME: 48-to-1 MUX
        #print("FSU-"+str(channel)+": Sensing "+str(current)+"uA on pin "+str(self.selected_pin[channel]))
        return current
        
    def program_dut(self, addr, payload):
        if payload is list:
            self.__program_dut12(addr, payload)
        else:
            self.__program_dut(addr, payload)

    def __program_dut(self, addr, payload):
        try:
            addr = '{:02x}'.format(addr)
            payload = '{:02x}'.format(payload)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\taddr - specifies address of DUT to write data to, 1 byte hex value\n"+
                             "\tpayload - specifies data to be sent, 1 byte hex value or list of 2 bytes")
        
        self.ser.write(prog_dut)
        self.ser.write(bytes.fromhex(addr+payload))

        readback = self.read_dut(int(addr, 16))
        readback = '{:02x}'.format(readback)

        print("Programming DUT:\n"+
            "\tPAYLOAD: "+payload+"\n"+
            "\tREADBACK: "+readback)

        if readback != payload:
            self.__log_error("readback does not match payload!")

    def __program_dut12(self, addr, payload):
        try:
            addr = '{:02x}'.format(addr)
            payload[0] = '{:02x}'.format(payload[0])
            payload[1] = '{:02x}'.format(payload[1])
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\taddr - specifies address of DUT to write data to, 1 byte hex value\n"+
                             "\tpayload - specifies data to be sent, 1 byte hex value or list of 2 bytes")

        self.ser.write(prog_dut12)
        self.ser.write(bytes.fromhex(addr+payload[0]+payload[1]))

        readback = self.read_dut(int(addr, 16), True)
        readback[0] = '{:02x}'.format(readback[0])
        readback[1] = '{:02x}'.format(readback[1])

        print("Programming DUT:\n"+
            "\tPAYLOAD: "+payload[0]+","+payload[1]+"\n"+
            "\tREADBACK: "+readback[0]+","+readback[1])

        if readback[0] != payload[0] or readback[1] != payload[1]:
            self.__log_error("readback does not match payload!")

    def read_dut(self, addr, two_byte=False):
        try:
            addr = '{:02x}'.format(addr)
            two_byte = bool(two_byte)
        except:
            self.__log_error("invalid input\nExpected arguments:\n"+
                             "\taddr - specifies address of DUT to read from, 1 byte hex value"+
                             "\ttwo_byte - boolean flag, indicates if you are reading 1 byte or 2 bytes. Default False")
        
        if two_byte:
            self.ser.write(rd_dut12)
            self.ser.write(bytes.fromhex(str(addr)))
            readback = []
            readback.append(int(self.ser.read_until().strip(), 16)) # hi
            readback.append(int(self.ser.read_until().strip(), 16)) # lo
            return readback
        else:
            self.ser.write(rd_dut)
            self.ser.write(bytes.fromhex(str(addr)))
            return int(self.ser.read_until().strip(), 16)
    
    def __log_error(self, message):
        local_caller = getframeinfo(stack()[1][0])
        parent_caller = getframeinfo(stack()[2][0])
        file = parent_caller.filename.split('/')[-1]
        lineno = str(parent_caller.lineno)
        func = local_caller.function
        error_format = Fore.RED+"ERROR: "+file+", line "+lineno+": "+func+"():"+" - "
        
        print(error_format + message + "\n")
        exit()
