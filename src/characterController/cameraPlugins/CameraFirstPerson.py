#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# PANDA3D ENGINE IMPORTS
#
from panda3d.core import PandaNode, Vec3

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


#
# CAMERA FUNCTIONS
#
class CameraFirstPerson:
    def __init__(self, core, near=0.5, far=5000, fov=90):
        # core will store the PlayerController reference which is
        # necessary to access some features and settings
        self.core = core
        # set the minimum and maximum view distance
        base.camLens.setNearFar(near, far)
        base.camLens.setFov(fov)
        # if this variable is set to True, the camera task will reset
        # the cursor position in one frame bevore it gets read
        # This is to fix the problem that occurs when resuming from
        # pause
        self.reset_cursor_once = False

    def startCamera(self):
        """Starts the camera module."""
        # get the eyes bone of the armature
        self.eyes = self.core.exposeJoint(None, "modelRoot", "fps_eyes")
        camera.setPos(0,0,0)
        camera.setHpr(0,0,0)
        camera.reparentTo(self.eyes)

        # the cam_floater is important to trac the camera to from outside
        # the main camera classes
        self.cam_floater = self.core.main_node
        self.cam_floater = self.core.main_node.attachNewNode(PandaNode("playerCamFloater"))
        pos = Vec3(tuple(self.core.getConfig("cam_floater_pos")))
        self.cam_floater.setPos(pos)

        # this is the part of the armature which we will control using
        # the mouse
        self.TorsorControl = self.core.controlJoint(None,"modelRoot","neck")
        self.torsor_init_rotation = self.TorsorControl.getHpr()
        self.reset_cursor_once = True
        taskMgr.add(self.updateCamera, "task_camActualisation", priority=-4)

    def stopCamera(self):
        camera.reparentTo(render)
        taskMgr.remove("task_camActualisation")
        self.cam_floater.removeNode()

    def pauseCamera(self):
        base.win.movePointer(0, self.core.getConfig("win_width_half"), self.core.getConfig("win_height_half"))
        # make sure the camera is controlable from outside again
        camera.reparentTo(render)
        # initially keep it at the eyes position
        camera.setPos(self.eyes.getPos(render))
        camera.setHpr(self.eyes.getHpr(render))
        taskMgr.remove("task_camActualisation")

    def resumeCamera(self):
        # make sure the camera is correctly placed before it is
        # reparented to the eyes of the character again
        camera.setPos(0,0,0)
        camera.setHpr(0,0,0)
        camera.reparentTo(self.eyes)
        # we want to reset the cursor so we don't respect pre made mouse
        # movements which may occure due to off-center mouse placements
        self.reset_cursor_once = True
        taskMgr.add(self.updateCamera, "task_camActualisation", priority=-4)

    def centerCamera(self):
        """This method will move the camera centered behind the player model"""
        self.TorsorControl.setHpr(self.torsor_init_rotation)
        base.win.movePointer(0, self.core.getConfig("win_width_half"), self.core.getConfig("win_height_half"))

    def requestReposition(self, new_cam_pos):
        pass

    def updateCamera(self, task):
        """This function will check the min and max distance of the camera to
        the defined model and will correct the position if the cam is to close
        or to far away"""
        cam_rotation = Vec3()
        dt = globalClock.getDt()

        cam_left = False
        cam_right = False
        cam_up = False
        cam_down = False
        cam_center = False
        for self.core.plugin in self.core.inputPlugins:
            if self.core.plugin.active:
                cam_left = cam_left or self.core.plugin.getCamButton("camera-left")
                cam_right = cam_right or self.core.plugin.getCamButton("camera-right")
                cam_up = cam_up or self.core.plugin.getCamButton("camera-up")
                cam_down = cam_down or self.core.plugin.getCamButton("camera-down")
                cam_center = cam_center or self.core.plugin.getCenterCamState()
                cam_rotation = self.core.plugin.getRotationVec()
        if cam_rotation != Vec3():
            # we ignore button presses for camera movement if we have an analog style movement
            # this fixes a problem if the cam movement for buttons and rotation are set to the
            # same axis on gamepads
            cam_left = False
            cam_right = False
            cam_up = False
            cam_down = False

        movement_key_pressed = cam_left or cam_right or cam_up or cam_down

        # check if the camera should be centered
        if cam_center:
            # show a letter box when centering the camera
            if base.transitions.letterboxIval:
                if not base.transitions.letterboxIval.isPlaying():
                    base.transitions.letterboxOn(0.15)
            else:
                base.transitions.letterboxOn(0.15)
            self.centerCamera()

        if base.transitions.letterbox is not None:
            if not base.transitions.letterboxIval.isPlaying() \
            and not base.transitions.letterbox.isStashed():
                base.transitions.letterboxOff(0.15)

        # check if we have a mouse to control the camera otherwise we
        # simply stop here.
        if not base.mouseWatcherNode.hasMouse(): return task.cont

        # check if we want to reset the cursor before we head on
        if self.reset_cursor_once:
            base.win.movePointer(0, self.core.getConfig("win_width_half"), self.core.getConfig("win_height_half"))
            self.reset_cursor_once = False

        # get the mouse cursor position
        self.pointer = base.win.getPointer(0)
        mouseX = self.pointer.getX()
        mouseY = self.pointer.getY()

        # some helper functions to check wehter the value is in a
        # specific range.
        # NOTE: maybe we should calculate the difference that the value should change like if value of h is -366 it should move to 354 instead of 360.
        def check_h(h):
            if self.core.state not in self.core.prevent_rotation_states:
                if h < -360:
                    h = 360
                elif h > 360:
                    h = -360
            else:
                if h <= -50:
                    h = -50
                elif h >= 50:
                    h = 50
            return h

        def check_p(p):
            if p <-80:
                p = -80
            elif p > 90:
                p = 90
            return p

        # now place it in the middle of the window so we can see how far
        # the mouse has been moved
        if base.win.movePointer(0, self.core.getConfig("win_width_half"), self.core.getConfig("win_height_half")) or cam_rotation != Vec3() or movement_key_pressed:

            #        VERTICAL
            # calculate the vertical movement speed
            movement_y = cam_rotation.getY() * self.core.keyboard_cam_speed_y * dt

            keyboard_speed = self.core.keyboard_cam_speed_y * dt
            if self.core.getConfig("keyboard_invert_vertical"):
                keyboard_speed = -keyboard_speed
            if cam_up:
                movement_y -= keyboard_speed
            elif cam_down:
                movement_y += keyboard_speed

            if self.core.getConfig("enable_mouse"):
                mouse_speed = (mouseY - self.core.getConfig("win_height_half")) * self.core.mouse_speed_y
                if self.core.getConfig("mouse_invert_vertical"):
                    mouse_speed = -mouse_speed
                movement_y += mouse_speed
            p = self.TorsorControl.getP() + movement_y
            self.TorsorControl.setP(check_p(p))

            #        HORIZONTAL
            # calculate the horizontal movement speed
            # with a distinction between states where the character may
            # not move but only look around

            # gamepad axis movement calculation
            movement_x = cam_rotation.getX() * self.core.keyboard_cam_speed_x * dt

            # keyboard/gamepad keys movement calculation
            keyboard_speed = self.core.keyboard_cam_speed_x * dt
            if self.core.getConfig("keyboard_invert_horizontal"):
                keyboard_speed = -keyboard_speed
            if cam_left:
                movement_x += keyboard_speed
            elif cam_right:
                movement_x -= keyboard_speed

            # mouse movement calculation
            if self.core.getConfig("enable_mouse"):
                mouse_speed = (mouseX - self.core.getConfig("win_width_half")) * self.core.mouse_speed_x
                if not self.core.getConfig("mouse_invert_horizontal"):
                    mouse_speed = -mouse_speed
                movement_x += mouse_speed

            if self.core.state not in self.core.prevent_rotation_states:
                h = check_h(self.core.main_node.getH() + movement_x)
                newHpr = self.core.main_node.getHpr()
                newHpr.setX(h)
                self.core.updatePlayerHpr(newHpr)
                self.TorsorControl.setH(0)
            else:
                # if we are in a mode that prevents rotation, we don't
                # want the character to rotate around but instead give
                # the player a limited movability to the characters head
                h = self.TorsorControl.getH() - movement_x
                self.TorsorControl.setH(check_h(h))

        return task.cont

    def camShakeNod(self, distance):
        pass
