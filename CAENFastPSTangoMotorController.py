from sardana import State
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Description, DefaultValue, Access, DataAccess

from tango import DeviceProxy
import time

class CAENFastPSTangoMotorController(MotorController):
    MaxDevice = 2
    default_acceleration_time = 0
    default_base_rate = 0
    default_threshold = 0.001
    default_move_grace_time = 3
    
    ctrl_properties = {'tangoFQDN': {Type: str,
                                     Description: 'The FQDN of the CAEN FastPS Tango DS',
                                     DefaultValue: 'domain/family/member'},
                       }
    
    axis_attributes = {
        "Threshold": {
            Type: float,
            Description: "max. allowed deviation from target position",
            DefaultValue: 0.001,
        },
    }
    
    def __init__(self, inst, props, *args, **kwargs):
        super(MotorController, self).__init__(
            inst, props, *args, **kwargs)

        print('CAEN FastPS Initialization ...')
        self.proxy = DeviceProxy(self.tangoFQDN)
        print('SUCCESS')
        self._timeout = 10
        self._update_mode = None
        self._motors = {}
        
    def AddDevice(self, axis):
        self._motors[axis] = {}
        self._motors[axis]['is_moving'] = False
        self._motors[axis]['move_start_time'] = 0
        self._motors[axis]['threshold'] = self.default_threshold
        self._motors[axis]['timeout'] = 0
        pos = self.ReadOne(axis)
        self._motors[axis]['target'] = pos
        self.proxy.ramping = True

    def DeleteDevice(self, axis):
        del self._motors[axis]

    def PreStateAll(self):
        self._update_mode = self.proxy.update_mode

    def StateOne(self, axis):
        limit_switches = MotorController.NoLimitSwitch
        
        pos = self.ReadOne(axis)
        target = self._motors[axis]['target']
        threshold = self._motors[axis]['threshold']
        start_time = self._motors[axis]['move_start_time']
        timeout = self._motors[axis]['timeout']
        now = time.time()
        
        try:
            if self._motors[axis]['is_moving'] == False:
                state = State.On
            elif self._motors[axis]['is_moving'] & (abs(pos - target) > threshold): 
                # moving and not in threshold window
                if (now - start_time) < timeout:
                    # before timeout
                    state = State.Moving
                else:
                    # after timeout
                    self._log.warning('CAEN FAST-PS Timeout')
                    self._motors[axis]['is_moving'] = False
                    state = State.On
            elif self._motors[axis]['is_moving'] & (abs(pos - target) <= threshold): 
                # moving and within threshold window
                self._motors[axis]['is_moving'] = False
                state = State.On
            else:
                state = State.Fault
        except Exception as exc:
            print(f"Exception is StateOne: {exc}")
            state = State.Fault
        
        return state, 'all fine', limit_switches

    def ReadOne(self, axis):
        if axis == 0:
            return self.proxy.current
        else:
            return self.proxy.voltage
    
    def PreStartOne(self, axis, value):
        return self.proxy.update_mode == self.proxy.update_mode.NORMAL

    def StartOne(self, axis, position):
        start_position = self.ReadOne(axis)
        velocity = self.GetAxisPar(axis, "velocity")
        if axis == 0:
            self.proxy.current = position
        else:
            self.proxy.voltage = position
        self._motors[axis]['move_start_time'] = time.time()
        self._motors[axis]['is_moving'] = True
        self._motors[axis]['target'] = position
        self._motors[axis]["timeout"] = abs(position - start_position) / velocity + self.default_move_grace_time

    def AbortOne(self, axis):
        current_position = self.ReadOne(axis)
        if axis == 0:
            self.proxy.current = current_position
        else:
            self.proxy.voltage = current_position
        self._motors[axis]['is_moving'] = False
        self._motors[axis]['target'] = current_position

    def GetAxisPar(self, axis, name):
        name = name.lower()
        if name == "acceleration":
            v = self.default_acceleration_time
        elif name == "deceleration":
            v = self.default_acceleration_time
        elif name == "base_rate":
            v = self.default_base_rate
        elif name == "velocity":
            if axis == 0:
                v = self.proxy.ramp_current
            else:
                v = self.proxy.ramp_voltage
        elif name == "step_per_unit":
            v = 1
        return v

    def SetAxisPar(self, axis, name, value):
        name = name.lower()
        if name == "acceleration":
            pass
        elif name == "deceleration":
            pass
        elif name == "base_rate":
            pass
        elif name == "velocity":
            if axis == 0:
                self.proxy.ramp_current = value
            else:
                self.proxy.ramp_voltage = value
        elif name == "step_per_unit":
            pass
    
    def getThreshold(self, axis):
        return self._motors[axis]["threshold"]
    
    def setThreshold(self, axis, value):
        self._motors[axis]["threshold"] = value

    def SendToCtrl(self, cmd):
        """
        Send custom native commands. The cmd is a space separated string
        containing the command information. Parsing this string one gets
        the command name and the following are the arguments for the given
        command i.e.command_name, [arg1, arg2...]
        :param cmd: string
        :return: string (MANDATORY to avoid OMNI ORB exception)
        """
        # Get the process to send
        mode = cmd.split(' ')[0].lower()

        if mode == 'enable':
            self.proxy.enable()
        elif mode == 'disable':
            self.proxy.disable()
        else:
            self._log.warning('Invalid command')
            return 'ERROR: Invalid command requested.'
        pass
