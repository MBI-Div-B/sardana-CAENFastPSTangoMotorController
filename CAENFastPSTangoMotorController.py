from tango import DeviceProxy

from sardana import State
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Description, DefaultValue


class CAENFastPSTangoMotorController(MotorController):
    ctrl_properties = {'tangoFQDN': {Type: str,
                                     Description: 'The FQDN of the CAEN FastPS Tango DS',
                                     DefaultValue: 'domain/family/member'},
                       }
    
    MaxDevice = 2
    
    def __init__(self, inst, props, *args, **kwargs):
        super(MotorController, self).__init__(
            inst, props, *args, **kwargs)

        print('PI-MTE Tango Initialization ...')
        self.proxy = DeviceProxy(self.tangoFQDN)
        print('SUCCESS')

        # initialize hardware communication        
        self._motors = {}
        self._isMoving = None
        self._moveStartTime = None
        self._threshold = 0.0001
        self._target = None
        self._timeout = 10
        
    def AddDevice(self, axis):
        self._motors[axis] = True

    def DeleteDevice(self, axis):
        del self._motors[axis]

    def StateOne(self, axis):
        limit_switches = MotorController.NoLimitSwitch
        # pos = self.ReadOne(axis)
        # now = time.time()
        
        # try:
        #     if self._isMoving == False:
        #         state = State.On
        #     elif self._isMoving & (abs(pos-self._target) > self._threshold): 
        #         # moving and not in threshold window
        #         if (now-self._moveStartTime) < self._timeout:
        #             # before timeout
        #             state = State.Moving
        #         else:
        #             # after timeout
        #             self._log.warning('CAEN FAST-PS Timeout')
        #             self._isMoving = False
        #             state = State.On
        #     elif self._isMoving & (abs(pos-self._target) <= self._threshold): 
        #         # moving and within threshold window
        #         self._isMoving = False
        #         state = State.On
        #         #print('Kepco Tagret: %f Kepco Current Pos: %f' % (self._target, pos))
        #     else:
        #         state = State.Fault
        # except:
        #     state = State.Fault
        
        return State.On, 'all fine', limit_switches

    def ReadOne(self, axis):
        if axis == 0:
            return self.proxy.current
        else:
            return self.proxy.voltage

    def StartOne(self, axis, position):
        if axis == 0:
            self.proxy.current = positon
        else:
            self.proxy.voltage = positon

    def StopOne(self, axis):
        pass

    def AbortOne(self, axis):
        pass
    
    def SendToCtrl(self, cmd):
        """
        Send custom native commands. The cmd is a space separated string
        containing the command information. Parsing this string one gets
        the command name and the following are the arguments for the given
        command i.e.command_name, [arg1, arg2...]
        :param cmd: string
        :return: string (MANDATORY to avoid OMNI ORB exception)
        """
        # # Get the process to send
        # mode = cmd.split(' ')[0].lower()
        # #args = cmd.strip().split(' ')[1:]

        # if mode == 'moff':
        #     self.__sendAndReceive('MOFF')
        # elif mode == 'mon':
        #     self.__sendAndReceive('MON')
        # else:
        #     self._log.warning('Invalid command')
        #     return 'ERROR: Invalid command requested.'
        pass
