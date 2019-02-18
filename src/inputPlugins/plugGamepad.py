#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from panda3d.core import Vec3, ButtonHandle #, loadPrcFileData
#loadPrcFileData("", "notify-level-device debug")
from panda3d.core import InputDevice

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


class Plugin():
    """This plugin provides gamepad support for arbitrarry gamepads"""
    def __init__(self, parent, pid):
        logging.debug("INIT GAMEPAD PLUGIN...")

        self.parent = parent
        self.pluginID = pid
        self.active = False
        self.gamepad = None

        if not self.parent.usedDevice: return
        self.connect(self.parent.usedDevice)
        if not self.checkGamepads(): return

        self.active = True

        self.parent.accept("connect-device", self.connect)
        self.parent.accept("disconnect-device", self.disconnect)

        actionKey = self.parent.deviceMaps[self.parent.selectedDevice].unformatedMapping("action1")
        self.parent.accept("gamepad-{}".format(actionKey), base.messenger.send, ["doAction"])

        resetKey = self.parent.deviceMaps[self.parent.selectedDevice].unformatedMapping("reset")
        self.parent.accept("gamepad-{}".format(resetKey), base.messenger.send, ["reset-Avatar"])

        self.deadzone_x = self.parent.deadzone_x
        self.deadzone_y = self.parent.deadzone_y

        self.centerGamepadAxes(True)

        self.sprintState = False
        logging.debug("INIT GAMEPAD PLUGIN DONE")

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
        if not forceCalibrate:
            if not self.parent.deviceMaps[self.parent.selectedDevice].getValue("recalibrate", self.gamepad): return
        self.rxcenter = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-right-x", self.gamepad)
        self.rycenter = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-right-y", self.gamepad)
        self.lxcenter = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-left-x", self.gamepad)
        self.lycenter = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-left-y", self.gamepad)

    def getMovementVec(self):
        if not self.hasGamepad(): return Vec3()
        movementVec = Vec3()

        y_vec = -1 if self.parent.first_pserson_mode else 1

        # Move left/Right
        axis_x = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-left-x", self.gamepad)
        if abs(axis_x) > self.deadzone_x:
            movementVec.setX(axis_x - self.lxcenter)
        # Move forward/backward
        axis_y = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-left-y", self.gamepad)
        if abs(axis_y) > self.deadzone_y:
            movementVec.setY(-(axis_y - self.lycenter)*y_vec)
        return movementVec

    def getRotationVec(self):
        if not self.hasGamepad(): return Vec3()
        rotationVec = Vec3()
        rx = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-right-x", self.gamepad)
        ry = self.parent.deviceMaps[self.parent.selectedDevice].getValue("axis-right-y", self.gamepad)
        rotationVec.setX(-(rx - self.rxcenter))
        rotationVec.setY(-(ry - self.rycenter))
        return rotationVec

    def getCamButton(self, direction):
        return False

    def getJumpState(self):
        if not self.hasGamepad(): return False
        return self.parent.deviceMaps[self.parent.selectedDevice].getValue("jump", self.gamepad)

    def getCenterCamState(self):
        if not self.hasGamepad(): return False
        return self.parent.deviceMaps[self.parent.selectedDevice].getValue("center-camera", self.gamepad)

    def getIntelActionState(self):
        if not self.hasGamepad(): return False
        return self.parent.deviceMaps[self.parent.selectedDevice].getValue("intel-action", self.gamepad)

    def getAction1State(self):
        if not self.hasGamepad(): return False
        return self.parent.deviceMaps[self.parent.selectedDevice].getValue("action1", self.gamepad)

    def getSprintState(self):
        if not self.hasGamepad(): return False
        return self.parent.deviceMaps[self.parent.selectedDevice].getValue("sprint", self.gamepad)

    def getWalkState(self):
        if not self.hasGamepad(): return False
        return self.parent.deviceMaps[self.parent.selectedDevice].getValue("walk", self.gamepad)
