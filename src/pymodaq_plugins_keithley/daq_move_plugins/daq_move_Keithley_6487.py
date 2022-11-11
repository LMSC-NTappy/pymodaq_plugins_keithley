import numpy as np

from pyvisa import ResourceManager

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_keithley.hardware.KeithleyWrapper import Keithley6487Wrapper

class DAQ_Move_Keithley_6487(DAQ_Move_base):
    """Plugin for the Keithley 6487 voltage source.

    This object inherits all functionality to communicate with PyMoDAQ Module through inheritance via DAQ_Move_base
    It then implements the particular communication with the instrument

    Attributes:
    -----------
    controller:
    # TODO add your particular attributes here if any

    """
    _controller_units = 'V'
    is_multiaxes = False
    axes_names = ['Vsource']

    VISA_rm = ResourceManager()
    com_ports = list(VISA_rm.list_resources())

    params = [{'title': 'Controller Status:', 'name': 'controller_status', 'type': 'list', 'value': 'Master', 'limits': ['Master', 'Slave']},
              {'title': 'VISA:', 'name': 'visa', 'type': 'list', 'limits': com_ports},
              {'title': 'Id:', 'name': 'id', 'type': 'text', 'value': ""},
              {'title': 'Source Range:', 'name': 'source_range', 'type': 'list', 'value': 10, 'limits': [10, 50, 500]},
              {'title': 'Operate Vsource', 'name': 'source_operate', 'type': 'bool', 'value': False, 'default': False},
              ] + comon_parameters_fun(is_multiaxes, axes_names)

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        self.controller: Keithley6487Wrapper = None

        self.settings.child('visa').setValue("GPIB0::22::INSTR")

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        # if self.settings.child('controller_status').value() == "Slave":
        #     if not self.controller.measurement_obsolete:
        #         pos = self.controller.current_V
        #     else:
        #         pos = self.controller.read_current_and_vsource()[1]
        #     self.controller.measurement_obsolete = True
        # else:
        #     pos = self.controller.read_current_and_vsource()[1]
        #
        # pos = self.get_position_with_scaling(pos)
        # print(pos)
        return self.target_value

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close()

    def update_bounds(self,newbound):
        self.settings.child('bounds', 'max_bound').setValue(newbound)
        self.settings.child('bounds', 'min_bound').setValue(-1.0*newbound)

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == 'source_range':
            self.controller.set_source_range(range_s=param.value())
            self.update_bounds(float(param.value()))
        elif param.name() == 'source_operate':
            self.controller.operate_source(oper=param.value())

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

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
                                                timeout=1000)

        self.ini_stage_init(old_controller=controller,
                            new_controller=keithley_6487)

        dvc = self.controller.get_device_infos()
        self.settings.child('id').setValue(dvc)

        if self.settings.child('controller_status').value != "Slave":
            # Reset comm state
            self.controller.reset()
            # Update things in the interface
            self.controller.config_mode('CURR')
            self.controller.config_reading()

        info = "Whatever info you want to log"
        initialized = True
        return info, initialized

    def move_abs(self, value):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.controller.set_source_voltage(volts=value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', [f'Source Voltage set to {value}']))


    def move_rel(self, value):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.set_source_voltage(volts=self.target_value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', [f'Source Voltage set to {self.target_value}']))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.set_source_voltage(volts=0.0)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', [f'Source Voltage set to 0.0']))


    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""
      pass


if __name__ == '__main__':
    main(__file__)
