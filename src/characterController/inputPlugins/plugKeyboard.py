import logging

from panda3d.core import Vec3, KeyboardButton, MouseButton
from .inputMapping import InputMapping

KBD = "Keyboard and Mouse"

class Plugin(InputMapping):
    """This plugin provides gamepad support for arbitrarry gamepads"""
    def __init__(self, core, pid):
        logging.debug("INIT KEYBOARD PLUGIN...")

        InputMapping.__init__(self)

        self.core = core
        self.pluginID = pid
        self.active = True

        self.loadMapConfig()

        actionKey = self.unformatedMapping("action1")
        self.core.accept("{}".format(actionKey), base.messenger.send, ["doAction"])
        self.core.accept("shift-{}".format(actionKey), base.messenger.send, ["doAction"])

        resetKey = self.unformatedMapping("reset-Avatar")
        self.core.accept("{}".format(resetKey), base.messenger.send, ["reset-Avatar"])

        self.isDown = base.mouseWatcherNode.isButtonDown
        logging.debug("INIT KEYBOARD PLUGIN DONE")

    def loadMapConfig(self):
        for key, mapping in self.core.getConfig("deviceMaps")[KBD].items():
            if hasattr(KeyboardButton, mapping):
                self.mapButton(key, getattr(KeyboardButton, mapping)())
            elif hasattr(MouseButton, mapping):
                self.mapButton(key, getattr(MouseButton, mapping)())
            elif mapping != "":
                self.mapButton(key, KeyboardButton.asciiKey(mapping[0]))
            else:
                #unsupported key
                logging.error("Unsupported Button {}:{}".format(key, mapping))

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def centerGamepadAxes(self):
        # Nothing to recalibrate here
        return

    def getMovementVec(self):
        movementVec = Vec3()

        # Move forward / backward
        y_vec = -1 if self.core.plugin_isFirstPersonMode() else 1
        if self.isDown(self.unformatedMapping("forward")):
            movementVec.setY(-y_vec)
        elif self.isDown(self.unformatedMapping("backward")):
            movementVec.setY(y_vec)

        # Move left / right
        if self.isDown(self.unformatedMapping("left")):
            movementVec.setX(-1)
        elif self.isDown(self.unformatedMapping("right")):
            movementVec.setX(1)

        return movementVec

    def getRotationVec(self):
        return Vec3()

    def getCamButton(self, direction):
        #TODO: Maybe we need to do this check in the unformatedMapping function
        #if direction not in self.core.deviceMapKeyboard: return 0.0
        if self.isDown(self.unformatedMapping(direction)): return 1.0
        return 0.0

    def getJumpState(self):
        return self.isDown(self.unformatedMapping("jump"))

    def getCenterCamState(self):
        return self.isDown(self.unformatedMapping("center-camera"))

    def getIntelActionState(self):
        return self.isDown(self.unformatedMapping("intel-action"))

    def getAction1State(self):
        return self.isDown(self.unformatedMapping("action1"))

    def getSprintState(self):
        return self.isDown(self.unformatedMapping("sprint"))

    def getWalkState(self):
        return self.isDown(self.unformatedMapping("walk"))
