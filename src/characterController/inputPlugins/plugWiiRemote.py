from panda3d.core import Vec3, ButtonHandle, loadPrcFileData
#loadPrcFileData("", "notify-level-device debug")
from .inputMapping import InputMapping
try:
    from panda3d.core import InputDevice
    gamepadsupport = True
except:
    gamepadsupport = False

class Plugin(InputMapping):
    """This plugin provides gamepad support for wii remotes plus nunchuk"""
    def __init__(self, core):
        if not gamepadsupport: return
        if not self.checkGamepads(): return

        InputMapping.__init__(self)

        self.core = core
        self.getConfig("deviceMap")["Nintendo Wii Remote"] = self.core.getConfig("getConfig("deviceMap")["Nintendo Wii Remote"]")
        self.usedGamepadID = self.core.usedGamepadID
        self.deadzone_x = self.core.getConfig("deadzone_x")
        self.deadzone_y = self.core.getConfig("deadzone_y")

        self.loadMapConfig()

        # set the center position of the control sticks
        # NOTE: here we assume, that the wheel is centered when the application get started.
        #       In real world applications, you should notice the user and give him enough time
        #       to center the wheel until you store the center position of the controler!
        self.lxcenter = self.nunchuk.findControl(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["axis-left-x"]).state
        self.lycenter = self.nunchuk.findControl(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["axis-left-y"]).state

        self.sprintState = False

    def checkGamepads(self):
        # list of connected gamepad devices
        self.gamepads = []
        self.nunchuk = None
        connectedDevices = base.devices.getDevices()
        for device in connectedDevices:
            if device.get_device_class() == InputDevice.DC_gamepad \
            and "Nintendo Wii Remote" in device.name \
            and "Nintendo Wii Remote Nunchuk" not in device.name:
                self.gamepads.append(device)
            elif "Nintendo Wii Remote Nunchuk" in device.name:
                self.gamepads.append(device)
                self.nunchuk = device
        return len(self.gamepads) > 0 and self.nunchuk is not None

    def hasGamepad(self):
        if not gamepadsupport: return False
        return len(self.gamepads) > 0 and self.nunchuk is not None

    def loadMapConfig(self):
        for key, mapping in self.core.getConfig("deviceMaps")["Nintendo Wii Remote"].items():
            if hasattr(InputDevice.Axis, mapping):
                self.mapAxis(key, getattr(InputDevice.Axis, mapping)())
            elif hasattr(MouseButton, mapping):
                self.mapButton(key, getattr(GamepadButton, mapping)())
            else:
                #unsupported key or axis
                logging.error("Unsupported Axis or Button {}:{}".format(key, mapping))

    def getMovementVec(self):
        if not self.hasGamepad(): return Vec3()
        movementVec = Vec3()
        # Move left/Right
        axis_x = self.nunchuk.findControl(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["axis-left-x"]).state
        if abs(axis_x) > self.deadzone_x:
            movementVec.setX(axis_x - self.lxcenter)
        # Move forward/backward
        axis_y = self.nunchuk.findControl(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["axis-left-y"]).state
        if abs(axis_y) > self.deadzone_y:
            movementVec.setY(-(axis_y - self.lycenter))
        return movementVec

    def getRotationVec(self):
        if not self.hasGamepad(): return Vec3()
        rotationVec = Vec3()
        return rotationVec

    def getCamButton(self, direction):
        if not self.hasGamepad(): return False
        if direction not in self.core.getConfig("deviceMap")["Nintendo Wii Remote"]: return False

        self.checkGamepads()
        return self.gamepads[self.usedGamepadID].findButton(self.core.getConfig("deviceMap")["Nintendo Wii Remote"][direction]).state == InputDevice.S_down

    def getJumpState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["jump"]).state == InputDevice.S_down

    def getCenterCamState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["center-camera"]).state == InputDevice.S_down

    def getIntelActionState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["intel-action"]).state == InputDevice.S_down

    def getAction1State(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["action1"]).state == InputDevice.S_down

    def getSprintState(self):
        if not self.hasGamepad(): return False
        return self.nunchuk.findButton(self.core.getConfig("deviceMap")["Nintendo Wii Remote"]["sprint"]).state == InputDevice.S_down
