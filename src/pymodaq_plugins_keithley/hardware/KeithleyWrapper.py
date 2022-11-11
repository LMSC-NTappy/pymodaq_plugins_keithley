import threading
import struct

from pyvisa import ResourceManager
import numpy as np


class Keithley6487Wrapper:

    def __init__(self, visa_resource: str, timeout: int = 1000, ):
        self.status = None
        self.time = None
        self.unit = None
        self.visa_rm = ResourceManager()
        # Init timeout
        self.resource = self.visa_rm.open_resource(visa_resource)
        self.resource.write_termination = '\n'
        self.resource.read_termination = '\n'

        self.resource.timeout = timeout

        self.current_V: float = 0.0
        self.current_I: float = 0.0
        self.measurement_obsolete: bool = True

        self.lock = threading.Lock()

    def get_device_infos(self) -> str:
        with self.lock:
            dvc = self.resource.query("*IDN?")
        return dvc

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
        self.resource.write(f"FORM:ELEM ALL")

    def set_nplc(self, nplc: float = 5.0):
        self.resource.write(f"CURR: NPLC {nplc}")

    def set_range(self, rangecurrent: str = "20mA"):
        rngexp = {"20mA": -2,  # 2e-2
                  "2mA": -3,  # 2e-3
                  "200uA": -4,  # 2e-4
                  "20uA": -5,  # 2e-5
                  "2uA": -6,  # 2e-6
                  "200nA": -7,  # 2e-7
                  "20nA": -8,  # 2e-8
                  "2nA": -9}  # 2e-9

        self.resource.write(f"CURR:RANG 2E-{rngexp[rangecurrent]}")

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
        with self.lock:
            self.resource.write('READ?')
            vals = self.resource.read_raw()
            while len(vals) < 20:
                vals = vals + self.resource.read_raw()

        # In the Keithley Language, the first two bytes are the buffer header so we skip it
        # buffer header = struct.unpack('>f',vals[2:6])
        self.current_I = np.array(struct.unpack('>f', vals[2:6]))  # Then we have measured current

        self.unit = struct.unpack('c', vals[6:7])  # Then we have 1 byte for unit (it's A)
        self.time = struct.unpack('>f', vals[7:11])  # Then a float for measurement time
        self.status = struct.unpack('>f', vals[11:15])  # Then a float for status (0 if no error)

        self.current_V = np.array(struct.unpack('>f', vals[15:19]))  # Finally the voltage at source

        self.measurement_obsolete = False
        ret = [self.current_I, self.current_V]
        return ret

    def abort(self):
        self.resource.write("INIT:ABORt")

    def close(self):
        self.resource.close()
