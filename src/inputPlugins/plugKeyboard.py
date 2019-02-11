from panda3d.core import Vec3

class Plugin():
    """This plugin provides gamepad support for arbitrarry gamepads"""
    def __init__(self, parent, pid):
        self.parent = parent
        self.pluginID = pid
        self.active = True

        self.isDown = base.mouseWatcherNode.isButtonDown

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def anyKeyInListDown(self, keyMapList):
        for key in keyMapList:
            if self.isDown(key):
                return True

    def getMovementVec(self):
        movementVec = Vec3()

        # Move forward / backward
        y_vec = -1 if self.parent.first_pserson_mode else 1
        if self.anyKeyInListDown(self.parent.deviceMapKeyboard["forward"]):
            movementVec.setY(-y_vec)
        elif self.anyKeyInListDown(self.parent.deviceMapKeyboard["backward"]):
            movementVec.setY(y_vec)

        # Move left / right
        if self.anyKeyInListDown(self.parent.deviceMapKeyboard["left"]):
            movementVec.setX(-1)
        elif self.anyKeyInListDown(self.parent.deviceMapKeyboard["right"]):
            movementVec.setX(1)

        return movementVec

    def getRotationVec(self):
        return Vec3()
        """rotationVec = Vec3()

        # Move camera up / down
        if self.anyKeyInListDown(self.parent.deviceMapKeyboard["camera-up"]):
            rotationVec.setY(-y_vec)
        elif self.anyKeyInListDown(self.parent.deviceMapKeyboard["camera-down"]):
            rotationVec.setY(y_vec)

        # Move camera left / right
        if self.anyKeyInListDown(self.parent.deviceMapKeyboard["camera-left"]):
            rotationVec.setX(-1)
        elif self.anyKeyInListDown(self.parent.deviceMapKeyboard["camera-right"]):
            rotationVec.setX(1)

        return rotationVec"""

    def getCamButton(self, direction):
        if direction not in self.parent.deviceMapKeyboard: return 0.0
        if self.anyKeyInListDown(self.parent.deviceMapKeyboard[direction]): return 1.0
        return 0.0

    def getJumpState(self):
        return self.anyKeyInListDown(self.parent.deviceMapKeyboard["jump"])

    def getCenterCamState(self):
        return self.anyKeyInListDown(self.parent.deviceMapKeyboard["center-camera"])

    def getIntelActionState(self):
        return self.anyKeyInListDown(self.parent.deviceMapKeyboard["intel-action"])

    def getAction1State(self):
        return self.anyKeyInListDown(self.parent.deviceMapKeyboard["action1"])

    def getSprintState(self):
        return self.anyKeyInListDown(self.parent.deviceMapKeyboard["sprint"])

    def getWalkState(self):
        return self.anyKeyInListDown(self.parent.deviceMapKeyboard["walk"])
