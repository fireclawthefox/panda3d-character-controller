#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

from panda3d.core import (
    InputDevice,
    GamepadButton,
    KeyboardButton,
    MouseButton)

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


class InputMapping(object):
    """A container class for storing a mapping from a string action to either
    an axis or a button.  You could extend this with additional methods to load
    the default mappings from a configuration file. """
    # Define all the possible actions.
    actions = (
        # Keyboard and other Button related movement actions
        "forward",
        "backward",
        "left",
        "right",
        # Analogstick/Axis related movement actions
        "axis-left-x",
        "axis-left-y",
        # Camera movement actions Buttons
        "camera-up",
        "camera-down",
        "camera-left",
        "camera-right",
        # Camera movement actions Analogstick/Axis
        "axis-right-x",
        "axis-right-y",
        # Other Button related
        "jump",
        "intel-action",
        "action1",
        "sprint",
        "walk",
        "crouch",
        "crawl",
        "center-camera",
        # Calibration
        "recalibrate"
    )

    def __init__(self):
        self.__map = dict.fromkeys(self.actions)

    def setDefaultMappingKeyboardAndMouse(self):
        # Default mapping for Keyboard and Mouse usage
        self.mapButton("forward", KeyboardButton.asciiKey(b"w"))
        self.mapButton("backward", KeyboardButton.asciiKey(b"s"))
        self.mapButton("left", KeyboardButton.asciiKey(b"a"))
        self.mapButton("right", KeyboardButton.asciiKey(b"d"))
        self.mapButton("camera-up", KeyboardButton.page_up())
        self.mapButton("camera-down", KeyboardButton.end())
        self.mapButton("camera-left", KeyboardButton._del())
        self.mapButton("camera-right",KeyboardButton.page_down())
        self.mapButton("jump", KeyboardButton.space())
        self.mapButton("intel-action", MouseButton.one())
        self.mapButton("action1", MouseButton.one())
        self.mapButton("sprint", KeyboardButton.shift())
        self.mapButton("walk", KeyboardButton.control())
        self.mapButton("crouch", KeyboardButton.asciiKey(b"c"))
        self.mapButton("crawl", KeyboardButton.asciiKey(b"x"))
        self.mapButton("center-camera", KeyboardButton.home())

    def setDefaultMappingGamepadWiiRemote(self):
        # Default mapping for Wii Remotes
        self.mapAxis("axis-left-x", InputDevice.Axis.left_x)
        self.mapAxis("axis-left-y", InputDevice.Axis.left_y)
        self.mapAxis("axis-right-x", InputDevice.Axis.right_x)
        self.mapAxis("axis-right-y", InputDevice.Axis.right_y)
        self.mapButton("camera-up", GamepadButton.arrow_up())
        self.mapButton("camera-down", GamepadButton.arrow_down())
        self.mapButton("camera-left", GamepadButton.arrow_left())
        self.mapButton("camera-right",GamepadButton.arrow_right())
        self.mapButton("jump", GamepadButton.face_a())
        self.mapButton("intel-action", GamepadButton.face_b())
        self.mapButton("action1", GamepadButton.face_a())
        self.mapButton("sprint", GamepadButton.face_c())
        self.mapButton("center-camera", GamepadButton.face_z())

    def setDefaultMappingGenericGamepad(self):
        # Default mapping for generic gamepad devices
        self.mapAxis("axis-left-x", InputDevice.Axis.left_x)
        self.mapAxis("axis-left-y", InputDevice.Axis.left_y)
        self.mapAxis("axis-right-x", InputDevice.Axis.right_x)
        self.mapAxis("axis-right-y", InputDevice.Axis.right_y)
        self.mapAxis("camera-up", InputDevice.Axis.right_y)
        self.mapAxis("camera-down", InputDevice.Axis.right_y)
        self.mapAxis("camera-left", InputDevice.Axis.right_x)
        self.mapAxis("camera-right", InputDevice.Axis.right_x)
        self.mapButton("jump", GamepadButton.face_a())
        self.mapButton("intel-action", GamepadButton.face_b())
        self.mapButton("action1", GamepadButton.face_a())
        self.mapButton("sprint", GamepadButton.rtrigger())
        self.mapButton("walk", GamepadButton.lshoulder())
        self.mapButton("crouch", GamepadButton.ltrigger())
        self.mapButton("crawl", GamepadButton.face_x())
        self.mapButton("center-camera", GamepadButton.rshoulder())
        self.mapButton("recalibrate", GamepadButton.back())

    def mapButton(self, action, button):
        self.__map[action] = ("button", str(button))

    def mapAxis(self, action, axis):
        self.__map[action] = ("axis", axis.name)

    def unmap(self):
        self.__map[action] = None

    def formatMapping(self, action):
        """Returns a string label describing the mapping for a given action,
        for displaying in a GUI. """
        mapping = self.__map.get(action)
        if not mapping:
            return "Unmapped"

        # Format the symbolic string from Panda nicely.  In a real-world game,
        # you might want to look these up in a translation table, or so.
        label = mapping[1].replace('_', ' ').title()
        if mapping[0] == "axis":
            return "Axis: " + label
        else:
            return "Button: " + label

    def unformatedMapping(self, action):
        """Returns the name of the mapped key/axis as string or Unmapped
        if the action hasn't been mapped yet"""
        mapping = self.__map.get(action)
        return mapping[1] if mapping else "Unmapped"

    def getValue(self, action, device):
        """Returns a floating point value of the indicated actions state """
        mapping = self.__map.get(action)
        if not mapping:
            return 0
        if mapping[0] == "axis":
            for axis in device.axes:
                if axis.axis.name == mapping[1]:
                    return axis.value
            return 0
        else:
            for button in device.buttons:
                if button.handle.name == mapping[1]:
                    return button.pressed
            return False

    def getMappingJSON(self):
        """Write out the mapping as JSON"""
        return json.dumps(self.__map)

    def readMappingJSON(self, jsonString):
        """Read in a mapping from JSON"""
        self.__map = json.loads(jsonString)
