#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

from panda3d.core import KeyboardButton, MouseButton, ButtonHandle, Point3F, Vec3
from panda3d.core import InputDevice

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


# Deside which physics engine to use
# Panda3D internal engine
USEINTERNAL = True
# Bullet engine
USEBULLET = not USEINTERNAL

#
# PLAYER CONFIGURATIONS
#
class Config:
    """
    This class contains all the configurable variables of the player
    controller module.
    Most of the variables are set to represent a normal modern jump and
    run game feeling. Not to realistic but also not to floaty and should
    fit with characters created with measurements as 1 unit = 1 meter
    """
    def __init__(self, configFile):

        with open(configFile) as json_data_file:
            self.config = json.load(json_data_file)

        self.used_device = None
        for device in base.devices.getDevices(InputDevice.DeviceClass.gamepad):
            if device.name == self.config["selectedDevice"]:
                self.used_device = device

        self.config["win_width_half"] = base.win.getXSize() // 2
        self.config["win_height_half"] = base.win.getYSize() // 2

    def getConfig(self, configString):
        return self.config[configString]

    def setConfig(self, configString, value):
        self.config[configString] = value

    def saveConfig(self, configFile):
        with open(configFile) as json_data_file:
            json.dump(self.config, json_data_file)
