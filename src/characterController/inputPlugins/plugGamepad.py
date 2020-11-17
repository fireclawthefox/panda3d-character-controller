#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from panda3d.core import Vec3, ButtonHandle, GamepadButton#, loadPrcFileData
#loadPrcFileData("", "notify-level-device debug")
from panda3d.core import InputDevice

from .inputMapping import InputMapping

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


class Plugin(InputMapping):
    """This plugin provides gamepad support for arbitrarry gamepads"""
    def __init__(self, core, pid):
        logging.debug("INIT GAMEPAD PLUGIN...")

        InputMapping.__init__(self)

        self.core = core
        self.pluginID = pid
        self.active = False
        self.gamepad = None

        if not self.core.used_device: return
        self.connect(self.core.used_device)
        if not self.checkGamepads(): return

        self.loadMapConfig()

        self.active = True

        self.core.accept("connect-device", self.connect)
        self.core.accept("disconnect-device", self.disconnect)

        devMap = self.core.getConfig("deviceMaps")["Gamepad"]
        actionKey = self.unformatedMapping("action1")
        self.core.accept("gamepad-{}".format(actionKey), base.messenger.send, ["doAction"])

        resetKey = self.unformatedMapping("reset-Avatar")
        self.core.accept("gamepad-{}".format(resetKey), base.messenger.send, ["reset-Avatar"])

        self.deadzone_x = self.core.getConfig("deadzone_x")
        self.deadzone_y = self.core.getConfig("deadzone_y")

        self.centerGamepadAxes(True)

        self.sprintState = False
        logging.debug("INIT GAMEPAD PLUGIN DONE")

    def loadMapConfig(self):
        for key, mapping in self.core.getConfig("deviceMaps")["Gamepad"].items():
            if hasattr(InputDevice.Axis, mapping):
                self.mapAxis(key, getattr(InputDevice.Axis, mapping))
            elif hasattr(GamepadButton, mapping):
                self.mapButton(key, getattr(GamepadButton, mapping)())
            else:
                #unsupported key or axis
                logging.error("Unsupported Axis or Button {}:{}".format(key, mapping))

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
        return len(base.devices.getDevices(InputDevice.DeviceClass.gamepad)) > 0

    def centerGamepadAxes(self, forceCalibrate=False):
        devMap = self.core.getConfig("deviceMaps")["Gamepad"]
        if not forceCalibrate:
            if not self.getValue("recalibrate", self.gamepad): return
        self.rxcenter = self.getValue("axis-right-x", self.gamepad)
        self.rycenter = self.getValue("axis-right-y", self.gamepad)
        self.lxcenter = self.getValue("axis-left-x", self.gamepad)
        self.lycenter = self.getValue("axis-left-y", self.gamepad)

    def getMovementVec(self):
        if not self.hasGamepad(): return Vec3()
        movementVec = Vec3()

        y_vec = -1 if self.core.plugin_isFirstPersonMode() else 1

        devMap = self.core.getConfig("deviceMaps")["Gamepad"]
        # Move left/Right
        axis_x = self.getValue("axis-left-x", self.gamepad)
        if abs(axis_x) > self.deadzone_x:
            movementVec.setX(axis_x - self.lxcenter)
        # Move forward/backward
        axis_y = self.getValue("axis-left-y", self.gamepad)
        if abs(axis_y) > self.deadzone_y:
            movementVec.setY(-(axis_y - self.lycenter)*y_vec)
        return movementVec

    def getRotationVec(self):
        if not self.hasGamepad(): return Vec3()
        rotationVec = Vec3()
        devMap = self.core.getConfig("deviceMaps")["Gamepad"]
        rx = self.getValue("axis-right-x", self.gamepad)
        ry = self.getValue("axis-right-y", self.gamepad)
        rotationVec.setX(-(rx - self.rxcenter))
        rotationVec.setY(-(ry - self.rycenter))
        return rotationVec

    def getCamButton(self, direction):
        amount = self.getValue(direction, self.gamepad)
        if direction.endswith("-up") or direction.endswith("-left"):
            return amount >= 0.3
        else:
            return amount <= -0.3

    def getJumpState(self):
        if not self.hasGamepad(): return False
        return self.getValue("jump", self.gamepad)

    def getCenterCamState(self):
        if not self.hasGamepad(): return False
        return self.getValue("center-camera", self.gamepad)

    def getIntelActionState(self):
        if not self.hasGamepad(): return False
        return self.getValue("intel-action", self.gamepad)

    def getAction1State(self):
        if not self.hasGamepad(): return False
        return self.getValue("action1", self.gamepad)

    def getSprintState(self):
        if not self.hasGamepad(): return False
        return self.getValue("sprint", self.gamepad)

    def getWalkState(self):
        if not self.hasGamepad(): return False
        return self.getValue("walk", self.gamepad)
