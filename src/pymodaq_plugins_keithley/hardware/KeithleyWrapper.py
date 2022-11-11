from pyvisa import ResourceManager

class Keithley6487Wrapper:

    def __init__(self, visa_resource: str, timeout: int = 1000,):
       self.visa_rm = ResourceManager()
       #Init timeout
       self.resource = self.visa_rm.open_resource(visa_resource)
       self.resource.write_termination = '\n'
       self.resource.read_termination = '\n'

       self.resource.timeout = timeout

    def get_device_infos(self) -> str:
        return self.resource.query("*IDN?")

    def reset(self) -> None:
        self.resource.write("rst; status:preset; *cls;")

    def config_mode(self, mode: str = None):
        if mode not in ['CURR','VOLT','RES','CHAR']:
            raise ValueError(f"{mode} not in ['CURR','VOLT','RES','CHAR']")

        self.resource.write(f"CONF:{mode}")

    def config_reading(self):
        self.resource.write(f"FORM:DATA REAL")
        self.resource.write(f"FORM:ELEM READ VSO")

    def set_NPLC(self, NPLC: int = 5):
        self.resource.write(f"CURR: NPLC {NPLC}")

    def set_range(self, range: str = "20mA"):
        RNGEXP = {"20mA" : -2, # 2e-2
                  "2mA"  : -3, # 2e-3
                  "200uA": -4, # 2e-4
                  "20uA" : -5, # 2e-5
                  "2uA"  : -6, # 2e-6
                  "200nA": -7, # 2e-7
                  "20nA" : -8, # 2e-8
                  "2nA"  : -9} # 2e-9

        self.resource.write(f"CURR:RANG 2E-{RNGEXP[range]}")

    def set_source_voltage(self, volts: float = 0.0):
        self.resource.write(f"SOUR:VOLT {volts}")
        
    def set_source_range(self, range: int = 10):
        if range not in [10, 50, 500]:
            raise ValueError(f"range {range} not in [10,50,500]")
        else:
            self.resource.write(f"SOUR:VOLT:RANGe {range}")

    def operate_source(self, oper: bool = False):
        if oper:
            self.resource.write("SOURce:VOLT:STATe ON")
        else:
            self.resource.write("SOURce:VOLT:STATe ON")

    def read_current_and_vsource(self):
        return self.resource.query_binary_values('READ?')

    def close(self):
        self.resource.close()
