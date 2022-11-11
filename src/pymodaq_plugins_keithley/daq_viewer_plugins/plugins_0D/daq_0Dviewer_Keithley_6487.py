import numpy as np
from pyvisa import ResourceManager

from pymodaq.daq_utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.daq_utils.parameter import Parameter
from pymodaq_plugins_keithley.hardware.KeithleyWrapper import Keithley6487Wrapper


class DAQ_0DViewer_Keithley_6487(DAQ_Viewer_base):
    """
            ==================== ========================
            **Attributes**        **Type**
            *data_grabed_signal*  instance of Signal
            *VISA_rm*             ResourceManager
            *com_ports*
            *params*              dictionnary list
            *keithley*
            *settings*
            ==================== ========================
        """

    VISA_rm = ResourceManager()
    com_ports = list(VISA_rm.list_resources())



    params = comon_parameters + [
        {'title': 'VISA:', 'name': 'visa', 'type': 'list', 'limits': com_ports},
        {'title': 'Id:', 'name': 'id', 'type': 'text', 'value': ""},
        {'title': 'Timeout (ms):', 'name': 'timeout', 'type': 'int', 'value': 10000, 'default': 10000, 'min': 2000},
        {'title': 'Configuration:', 'name': 'config', 'type': 'group', 'children':
            [
            {'title': 'Range:', 'name': 'range', 'type': 'list', 'value': '20mA', 'default': '20mA', 'limits': ["20mA", "2mA", "200uA", "20uA", "2uA", "200nA", "20nA", "2nA"]},
            {'title': 'NPLC:', 'name': 'nplc', 'type': 'float', 'value': 5.0, 'default': 5.0, 'min': 0.01, 'max': 50},
            {'title': 'Zerocheck', 'name': 'zerocheck', 'type': 'bool', 'value': True, 'default': True},
            {'title': 'Source Range:', 'name': 'source_range', 'type': 'list', 'value': 10, 'limits': [10, 50, 500]},
            {'title': 'Source Voltage (V):', 'name': 'source_voltage', 'type': 'float', 'value': 0.0, 'default': 5.0, 'min': 0.01, 'max': 50},
            {'title': 'Operate Vsource', 'name': 'source_operate', 'type': 'bool', 'value': False, 'default': False},
            ]
        },
    ]

    def ini_attributes(self):
        self.controller: Keithley6487Wrapper = None

        self.settings.child('visa').setValue("GPIB0::22::INSTR")

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "range":
            self.controller.set_range(range=param.value())  # when writing your own plugin replace this line
        elif param.name() == 'nplc':
            self.controller.set_nplc(nplc=param.value())
        elif param.name() == 'source_range':
            self.controller.set_source_range(range_s=param.value())
        elif param.name() == 'source_voltage':
            self.controller.set_source_voltage(volts=param.value())
        elif param.name() == 'zerocheck':
            self.controller.config_zerocheck(active=param.value())
        elif param.name() == 'source_operate':
            self.controller.operate_source(oper=param.value())

        ##

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.settings.child('controller_status').value() == "Slave":
            keithley_6487 = None
        else:
            keithley_6487 = Keithley6487Wrapper(visa_resource=self.settings.child('visa').value(),
                                                timeout=self.settings.child('timeout').value(), )

        self.ini_detector_init(old_controller=controller,
                               new_controller=keithley_6487)


        # Update things in the interface
        dvc = self.controller.get_device_infos()
        self.settings.child('id').setValue(dvc)

        if self.settings.child('controller_status').value != "Slave":
            # Reset comm state
            self.controller.reset()
            # Update things in the interface
            self.controller.config_mode('CURR')
            self.controller.config_reading()

        # initialize viewers panel with the future type of data
        self.data_grabed_signal_temp.emit([DataFromPlugins(name='Keithley_6487',
                                                           data=[np.array([0.0]), np.array([0.0])],
                                                           dim='Data0D',
                                                           labels=['I', 'Vso'])])

        info = f"Initialized - {self.settings.child('controller_status').value()} {dvc}"
        initialized = True

        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """

        data = self.controller.read_current_and_vsource()
        self.data_grabed_signal.emit([DataFromPlugins(name='Keithley_6487',
                                                      data=data,
                                                      dim='Data0D',
                                                      labels=['I', 'Vso'],
                                                      )])

        #########################################################
        #
        # # asynchrone version (non-blocking function with callback)
        # raise NotImplemented  # when writing your own plugin remove this line
        # when writing your own plugin replace this line
        # self.controller.your_method_to_start_a_grab_snap(self.callback)
        # #########################################################

    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        data_tot = self.controller.your_method_to_get_data_from_buffer()
        self.data_grabed_signal.emit([DataFromPlugins(name='Mock1', data=data_tot,
                                                      dim='Data0D', labels=['dat0', 'data1'])])

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        # raise NotImplemented  # when writing your own plugin remove this line
        # self.controller.your_method_to_stop_acquisition()  # when writing your own plugin replace this line

        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        ##############################
        return ''


if __name__ == '__main__':
    main(__file__)
