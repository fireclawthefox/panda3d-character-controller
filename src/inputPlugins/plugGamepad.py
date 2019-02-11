from panda3d.core import Vec3, ButtonHandle, loadPrcFileData
#loadPrcFileData("", "notify-level-device debug")
try:
    from panda3d.core import InputDevice
    gamepadsupport = True
except:
    gamepadsupport = False

class Plugin():
    """This plugin provides gamepad support for arbitrarry gamepads"""
    def __init__(self, parent, pid):
        self.parent = parent
        self.pluginID = pid
        self.active = False
        self.gamepad = None
        if not gamepadsupport: return

        self.gamepads = base.devices.getDevices(InputDevice.DeviceClass.gamepad)
        if len(self.gamepads) < 1: return
        self.connect(self.gamepads[self.parent.usedGamepadID])
        if not self.checkGamepads(): return

        self.active = True

        self.parent.accept("connect-device", self.connect)
        self.parent.accept("disconnect-device", self.disconnect)

        self.deviceMap = self.parent.deviceMap
        self.usedGamepadID = self.parent.usedGamepadID
        self.deadzone_x = self.parent.deadzone_x
        self.deadzone_y = self.parent.deadzone_y

        # set the center position of the control sticks
        # NOTE: here we assume, that the wheel is centered when the application get started.
        #       In real world applications, you should notice the user and give him enough time
        #       to center the wheel until you store the center position of the controler!
        self.rxcenter = self.gamepad.findAxis(self.deviceMap["axis-right-x"]).value
        self.rycenter = self.gamepad.findAxis(self.deviceMap["axis-right-y"]).value
        self.lxcenter = self.gamepad.findAxis(self.deviceMap["axis-left-x"]).value
        self.lycenter = self.gamepad.findAxis(self.deviceMap["axis-left-y"]).value

        self.sprintState = False

    def connect(self, device):
        """Event handler that is called when a device is discovered."""

        # We're only interested if this is a gamepad and we don't have a
        # gamepad yet.
        if device.device_class == InputDevice.DeviceClass.gamepad and not self.gamepad:
            self.gamepad = device

            # Enable this device to ShowBase so that we can receive events.
            # We set up the events with a prefix of "gamepad-".
            try:
                base.attachInputDevice(device, prefix="gamepad")
            except:
                # the device has probably already been attached
                pass

    def disconnect(self, device):
        """Event handler that is called when a device is removed."""

        if self.gamepad != device:
            # We don't care since it's not our gamepad.
            return

        # Tell ShowBase that the device is no longer needed.
        base.detachInputDevice(device)
        self.gamepad = None

    def checkGamepads(self):
        # list of connected gamepad devices
        return self.gamepad is not None

    def hasGamepad(self):
        if not gamepadsupport: return False
        return len(self.gamepads) > 0

    def getMovementVec(self):
        if not self.hasGamepad(): return Vec3()
        movementVec = Vec3()

        y_vec = -1 if self.parent.first_pserson_mode else 1

        # Move left/Right
        axis_x = self.gamepad.findAxis(self.deviceMap["axis-left-x"]).value
        if abs(axis_x) > self.deadzone_x:
            movementVec.setX(axis_x - self.lxcenter)
        # Move forward/backward
        axis_y = self.gamepad.findAxis(self.deviceMap["axis-left-y"]).value
        if abs(axis_y) > self.deadzone_y:
            movementVec.setY(-(axis_y - self.lycenter)*y_vec)
        return movementVec

    def getRotationVec(self):
        if not self.hasGamepad(): return Vec3()
        rotationVec = Vec3()
        rotationVec.setX(-(self.gamepad.findAxis(self.deviceMap["axis-right-x"]).value - self.rxcenter))
        rotationVec.setY(-(self.gamepad.findAxis(self.deviceMap["axis-right-y"]).value - self.rycenter))
        return rotationVec

    def getCamButton(self, direction):
        return False
        """
        if not self.hasGamepad(): return False
        if direction not in self.deviceMap: return False

        self.checkGamepads()

        center = 0.0
        if "up" in direction.lower() or "down" in direction.lower():
            center = self.rycenter
        else:
            center = self.rxcenter
        return self.gamepad.findAxis(self.deviceMap[direction]).value -  center
        """
    def getJumpState(self):
        if not self.hasGamepad(): return False
        return self.gamepad.findButton(self.deviceMap["jump"]).pressed

    def getCenterCamState(self):
        if not self.hasGamepad(): return False
        return self.gamepad.findButton(self.deviceMap["center-camera"]).pressed

    def getIntelActionState(self):
        if not self.hasGamepad(): return False
        return self.gamepad.findButton(self.deviceMap["intel-action"]).pressed

    def getAction1State(self):
        if not self.hasGamepad(): return False
        return self.gamepad.findButton(self.deviceMap["action1"]).pressed

    def getSprintState(self):
        if not self.hasGamepad(): return False
        return self.gamepad.findButton(self.deviceMap["sprint"]).pressed

    def getWalkState(self):
        return self.gamepad.findButton(self.deviceMap["walk"]).pressed
