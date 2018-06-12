from panda3d.core import Vec3, ButtonHandle, loadPrcFileData
#loadPrcFileData("", "notify-level-device debug")
try:
    from panda3d.core import InputDevice
    gamepadsupport = True
except:
    gamepadsupport = False

class Plugin():
    """This plugin provides gamepad support for arbitrarry gamepads"""
    def __init__(self, parent):
        if not gamepadsupport: return
        if not self.checkGamepads(): return

        self.parent = parent
        self.deviceMap = self.parent.deviceMap
        self.usedGamepadID = self.parent.usedGamepadID
        self.deadzone_x = self.parent.deadzone_x
        self.deadzone_y = self.parent.deadzone_y


        # set the center position of the control sticks
        # NOTE: here we assume, that the wheel is centered when the application get started.
        #       In real world applications, you should notice the user and give him enough time
        #       to center the wheel until you store the center position of the controler!
        self.lxcenter = self.gamepads[self.usedGamepadID].findControl(self.deviceMap["axis-left-x"]).state
        self.lycenter = self.gamepads[self.usedGamepadID].findControl(self.deviceMap["axis-left-y"]).state

        self.sprintState = False

    def checkGamepads(self):
        # list of connected gamepad devices
        self.gamepads = base.devices.getDevices(InputDevice.DC_gamepad)
        return len(self.gamepads) > 0

    def hasGamepad(self):
        if not gamepadsupport: return False
        return len(self.gamepads) > 0

    def getMovementVec(self):
        if not self.hasGamepad(): return Vec3()
        movementVec = Vec3()
        # Move left/Right
        axis_x = self.gamepads[self.usedGamepadID].findControl(self.deviceMap["axis-left-x"]).state
        if abs(axis_x) > self.deadzone_x:
            movementVec.setX(axis_x - self.lxcenter)
        # Move forward/backward
        axis_y = self.gamepads[self.usedGamepadID].findControl(self.deviceMap["axis-left-y"]).state
        if abs(axis_y) > self.deadzone_y:
            movementVec.setY(-(axis_y - self.lycenter))
        return movementVec

    def getRotationVec(self):
        if not self.hasGamepad(): return Vec3()
        rotationVec = Vec3()
        rotationVec.setX(self.gamepads[self.usedGamepadID].findControl(self.deviceMap["axis-right-x"]).state - self.rxcenter)
        rotationVec.setY(self.gamepads[self.usedGamepadID].findControl(self.deviceMap["axis-right-y"]).state - self.rycenter)
        return rotationVec

    def getCamButton(self, direction):
        if not self.hasGamepad(): return False
        if direction not in self.deviceMap: return False

        self.checkGamepads()
        return self.gamepads[self.usedGamepadID].findButton(self.deviceMap[direction]).state == InputDevice.S_down

    def getJumpState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.deviceMap["jump"]).state == InputDevice.S_down

    def getCenterCamState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.deviceMap["center-camera"]).state == InputDevice.S_down

    def getIntelActionState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.deviceMap["intel-action"]).state == InputDevice.S_down

    def getAction1State(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.deviceMap["action1"]).state == InputDevice.S_down

    def getSprintState(self):
        if not self.hasGamepad(): return False
        return self.gamepads[self.usedGamepadID].findButton(self.deviceMap["sprint"]).state == InputDevice.S_down
