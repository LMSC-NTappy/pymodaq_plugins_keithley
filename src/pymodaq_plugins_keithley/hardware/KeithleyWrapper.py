from pyvisa import ResourceManager
import numpy as np

class Keithley6487Wrapper:

    def __init__(self, visa_resource: str, timeout: int = 1000, ):
        self.visa_rm = ResourceManager()
        # Init timeout
        self.resource = self.visa_rm.open_resource(visa_resource)
        self.resource.write_termination = '\n'
        self.resource.read_termination = '\n'

        self.resource.timeout = timeout

        self.current_V: float = 0.0
        self.current_I: float = 0.0
        self.measurement_obsolete : bool = True

    def get_device_infos(self) -> str:
        return self.resource.query("*IDN?")

    def reset(self) -> None:
        self.resource.write("*rst; status:preset; *cls;")

    def config_mode(self, mode: str = None):
        if mode not in ['CURR', 'VOLT', 'RES', 'CHAR']:
            raise ValueError(f"{mode} not in ['CURR','VOLT','RES','CHAR']")

        self.resource.write(f"CONF:{mode}")

    def config_zerocheck(self, active: bool = False):
        if active:
            self.resource.write("SYST:ZCHeck ON")
        else:
            self.resource.write("SYST:ZCHeck OFF")

    def config_reading(self):
        self.resource.write(f"FORM:DATA REAL")
        self.resource.write(f"FORM:ELEM READing VSOurce")

    def set_nplc(self, NPLC: int = 5):
        self.resource.write(f"CURR: NPLC {NPLC}")

    def set_range(self, range: str = "20mA"):
        RNGEXP = {"20mA": -2,  # 2e-2
                  "2mA": -3,  # 2e-3
                  "200uA": -4,  # 2e-4
                  "20uA": -5,  # 2e-5
                  "2uA": -6,  # 2e-6
                  "200nA": -7,  # 2e-7
                  "20nA": -8,  # 2e-8
                  "2nA": -9}  # 2e-9

        self.resource.write(f"CURR:RANG 2E-{RNGEXP[range]}")

    def set_source_voltage(self, volts: float = 0.0):
        self.resource.write(f"SOUR:VOLT {volts}")

    def set_source_range(self, range_s: int = 10):
        if range_s not in [10, 50, 500]:
            raise ValueError(f"range {range_s} not in [10,50,500]")
        else:
            self.resource.write(f"SOUR:VOLT:RANGe {range_s}")

    def operate_source(self, oper: bool = False):
        if oper:
            self.resource.write("SOURce:VOLT:STATe ON")
        else:
            self.resource.write("SOURce:VOLT:STATe OFF")

    def read_current_and_vsource(self):
        vals = self.resource.query_binary_values('READ?', header_fmt='ieee', data_points=2, is_big_endian=True)
        self.current_I = np.array([vals[0]])
        self.current_V = np.array([vals[1]])
        self.measurement_obsolete = False
        return [self.current_I, self.current_V]


    def close(self):
        self.resource.close()
