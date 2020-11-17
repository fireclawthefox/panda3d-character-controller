#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# PANDA3D ENGINE IMPORTS
#
from panda3d.core import PandaNode, NodePath, Vec3
from direct.interval.IntervalGlobal import Sequence

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


#
# CAMERA FUNCTIONS
#
class CameraThirdPerson:
    def __init__(self, core, near=0.5, far=5000, fov=90):
        # core will store the PlayerController reference which is
        # necessary to access some features and settings
        self.core = core
        # set the minimum and maximum view distance
        base.camLens.setNearFar(near, far)
        base.camLens.setFov(fov)

        self.last_platform_position_cam = None
        self.last_platform_rotation_cam = None

        self.external_cam_pos_request = None

        self.ival_move_cam = None

        self.ival_camshake = None

        self.cam_ray = "camera_check_ray"
        self.core.registerRayCheck(self.cam_ray, (0,0,0), (0,0,1), render)

    def startCamera(self):
        """Starts the camera module."""
        # to enhance readability
        self.cam_floater = self.core.main_node.attachNewNode(PandaNode("playerCamFloater"))
        pos = Vec3(tuple(self.core.getConfig("cam_floater_pos")))
        self.cam_floater.setPos(pos)
        taskMgr.add(self.updateCamera, "task_camActualisation", priority=-4)

    def stopCamera(self):
        taskMgr.remove("task_camActualisation")
        if self.ival_move_cam is not None and self.ival_move_cam.isPlaying():
            self.ival_move_cam.finish()
            self.ival_move_cam = None
        if self.ival_camshake is not None and self.ival_camshake.isPlaying():
            self.ival_camshake.finish()
            self.ival_camshake = None
        self.cam_floater.removeNode()

    def pauseCamera(self):
        taskMgr.remove("task_camActualisation")

    def resumeCamera(self):
        taskMgr.add(self.updateCamera, "task_camActualisation", priority=-4)

    def centerCamera(self):
        """This method will move the camera centered behind the player model"""
        # Camera Movement Updates
        camdist = self.core.getConfig("cam_distance")#camvec.length()
        # get the cameras current offset to the player model on the z-axis
        offsetZ = self.cam_floater.getZ()
        camera_old_pos = camera.getPos()
        camera.setPos(self.core.main_node, 0, camdist, offsetZ)
        camera_new_pos = camera.getPos()
        camera.setPos(camera_old_pos)

        duration = self.core.getConfig("cam_reposition_duration")

        self.ival_move_cam = camera.posInterval(duration, camera_new_pos)
        self.ival_move_cam.start()

        base.win.movePointer(0, self.core.getConfig("win_width_half"), self.core.getConfig("win_height_half"))
        camera.lookAt(self.cam_floater)

    def requestReposition(self, new_cam_pos):
        self.external_cam_pos_request = new_cam_pos

    def updateCamera(self, task):
        """This function will check the min and max distance of the camera to
        the defined model and will correct the position if the cam is to close
        or to far away"""

        #TODO: Change everything to use the newCamPos and at the end set the camera pos accordingly!
        #newCamPos = NodePath()
        #newCamPos.setPos(camera.getPos())
        if self.external_cam_pos_request is not None:
            #newCamPos.setPos(self.external_cam_pos_request)
            camera.setPos(self.external_cam_pos_request)
            self.external_cam_pos_request = None

        for self.core.plugin in self.core.inputPlugins:
            if self.core.plugin.active:
                cam_left = self.core.plugin.getCamButton("camera-left")
                cam_right = self.core.plugin.getCamButton("camera-right")
                cam_up = self.core.plugin.getCamButton("camera-up")
                cam_down = self.core.plugin.getCamButton("camera-down")
                cam_center = self.core.plugin.getCenterCamState()
                cam_rotation = self.core.plugin.getRotationVec()

        # Camera Movement Updates
        camvec = self.cam_floater.getPos(render) - camera.getPos(render)
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()

        # check if the camera should be centered
        if cam_center:
            # show a letter box when centering the camera
            if base.transitions.letterboxIval:
                if not base.transitions.letterboxIval.isPlaying():
                    base.transitions.letterboxOn(0.15)
            else:
                base.transitions.letterboxOn(0.15)
            self.centerCamera()
            return task.cont

        if base.transitions.letterbox is not None:
            if not base.transitions.letterboxIval.isPlaying() \
            and not base.transitions.letterbox.isStashed():
                base.transitions.letterboxOff(0.15)

        dt = globalClock.getDt()

        # Move camera left/right with the mouse
        if base.mouseWatcherNode.hasMouse() and self.core.getConfig("enable_mouse"):
            mw = base.mouseWatcherNode
            if base.win.movePointer(0, self.core.getConfig("win_width_half"), self.core.getConfig("win_height_half")):
                # Vertical positioning
                mouse_y = mw.getMouseY()
                z = mouse_y * self.core.mouse_speed_y * camdist * dt
                if self.core.getConfig("mouse_invert_vertical"):
                    camera.setZ(camera, z)
                else:
                    camera.setZ(camera, -z)

                # Horizontal positioning
                mouse_x = mw.getMouseX()
                x = mouse_x * self.core.mouse_speed_x * camdist * dt
                if self.core.getConfig("mouse_invert_horizontal"):
                    camera.setX(camera, x)
                else:
                    camera.setX(camera, -x)
        # Move camera with the keyboard
        if cam_left:
            #                   LEFT
            x = cam_left * self.core.keyboard_cam_speed_x * dt
            if self.core.getConfig("keyboard_invert_horizontal"):
                x = -x
            camera.setX(camera, -x)
        elif cam_right:
            #                   RIGHT
            x = cam_right * self.core.keyboard_cam_speed_x * dt
            if self.core.getConfig("keyboard_invert_horizontal"):
                x = -x
            camera.setX(camera, x)
        if cam_up:
            #                    UP
            z = cam_up * self.core.keyboard_cam_speed_y * dt
            if self.core.getConfig("keyboard_invert_vertical"):
                z = -z
            camera.setZ(camera, z)
        elif cam_down:
            #                   DOWN
            z = cam_down * self.core.keyboard_cam_speed_y * dt
            if self.core.getConfig("keyboard_invert_vertical"):
                z = -z
            camera.setZ(camera, -z)

        # Move camera with moving platforms
        if self.core.getActivePlatform() is not None and self.core.state not in self.core.jump_and_fall_states:
            platformPositionAbsolute = self.core.getActivePlatform().getPos()
            # Character on moving platform
            if self.last_platform_position_cam is None:
                self.last_platform_position_cam = platformPositionAbsolute
            platform_speed = platformPositionAbsolute - self.last_platform_position_cam
            self.last_platform_position_cam = platformPositionAbsolute
            # now update the player position according to the platform
            camera.setPos(camera.getPos()+platform_speed)
        else:
            self.last_platform_position_cam = None
            self.last_platform_rotation_cam = None

        # Get the cameras current offset to the player model on the z-axis
        offsetZ = camera.getZ(render) - self.cam_floater.getZ(render)
        # check if the camera is within the min and max z-axis offset
        if offsetZ < self.core.getConfig("min_cam_height_distance"):
            # the cam is to low, so move it up
            camera.setZ(self.cam_floater.getZ(render) + self.core.getConfig("min_cam_height_distance"))
            offsetZ = self.core.getConfig("min_cam_height_distance")
        elif offsetZ > self.core.getConfig("max_cam_height_distance"):
            # the cam is to high, so move it down
            camera.setZ(self.cam_floater.getZ(render) + self.core.getConfig("max_cam_height_distance"))
            offsetZ = self.core.getConfig("max_cam_height_distance")

        # lazy camera positioning
        # if we are not moving up or down, set the cam to an average position
        if offsetZ > self.core.getConfig("cam_height_avg_up"):
            # the cam is higher then the average cam height above the player
            # so move it slowly down
            camera.setZ(camera.getZ(render) - self.core.getConfig("cam_z_justification_speed") * globalClock.getDt())
            newOffsetZ = camera.getZ(render) - self.cam_floater.getZ()
            # check if the cam has reached the desired offset
            #if newOffsetZ < self.core.getConfig("cam_height_avg_down"):
            #    # set the cam z position to exactly the desired offset
            #    camera.setZ(self.cam_floater.getZ(render) + self.core.getConfig("cam_height_avg_down"))
        elif offsetZ < self.core.getConfig("cam_height_avg_down"):
            # the cam is lower then the average cam height above the player
            # so move it slowly up
            camera.setZ(camera.getZ() + self.core.getConfig("cam_z_justification_speed") * globalClock.getDt())
            newOffsetZ = camera.getZ() - self.cam_floater.getZ(render)
            # check if the cam has reached the desired offset
            #if newOffsetZ > self.core.getConfig("cam_height_avg_up"):
            #    # set the cam z position to exactly the desired offset
            #    camera.setZ(self.cam_floater.getZ(render) + self.core.getConfig("cam_height_avg_up"))

        # If the camera is to far from player start following
        if camdist > self.core.getConfig("max_cam_distance"):
            camera.setPos(camera.getPos()+camvec*(camdist-self.core.getConfig("max_cam_distance")))
            camdist = self.core.getConfig("max_cam_distance")

        # camera collision detection
        # always set the cameras position to the first hitpoint on a collision solid
        had_ray_collision = False
        self.core.updateRayPositions(self.cam_ray, self.cam_floater.getPos(render), camera.getPos(render))
        self.core.updatePhysics()
        entry = self.core.getFirstCollisionEntryInLine(self.cam_ray)
        if entry is not None:
            pos = None
            if self.core.hasSurfacePoint(entry):
                # move the camera to the occurrence of the collision
                pos = self.core.getSurfacePoint(entry, render)
            wall_normal = None
            if self.core.hasSurfaceNormal(entry):
                # move the camera off of the wall in the direction the
                # wall is facing
                wall_normal = self.core.getSurfaceNormal(entry, render)
                pos.setX(pos.getX() + wall_normal.getX()/2.0)
                pos.setY(pos.getY() + wall_normal.getY()/2.0)
            if pos is not None:
                had_ray_collision = True
                if self.ival_move_cam is None or self.ival_move_cam.isStopped():
                    offset_z = pos.getZ() - self.cam_floater.getZ(render)
                    if offsetZ < self.core.getConfig("min_cam_height_distance"):
                        # the position is to low, so move it up
                        pos.setZ(self.cam_floater.getZ(render) + self.core.getConfig("min_cam_height_distance"))
                    elif offsetZ > self.core.getConfig("max_cam_height_distance"):
                        # the position is to high, so move it down
                        pos.setZ(self.cam_floater.getZ(render) + self.core.getConfig("max_cam_height_distance"))

                    dist = pos - self.cam_floater.getPos(render)

                    duration = dist.length() * self.core.getConfig("cam_reposition_duration")

                    self.ival_move_cam = camera.posInterval(duration, pos)
                    self.ival_move_cam.start()
                #camera.setPos(pos)
            self.core.clearFirstCollisionEntryOfRay(self.cam_ray)

        # If player is to close move the camera backwards
        if camdist < self.core.getConfig("min_cam_distance"):
            if not had_ray_collision:
                # move the camera backwards
                camera.setPos(camera.getPos()-camvec*(self.core.getConfig("min_cam_distance")-camdist))
                camdist = self.core.getConfig("min_cam_distance")
            else:
                # we can't move the camera back into the wall, so move it up
                #TODO: Maybe change max_cam_height_distance with something like
                #      self.core.min_cam_dist - camdist
                camera.setZ(self.cam_floater.getZ() + self.core.getConfig("max_cam_height_distance"))

        camera.lookAt(self.cam_floater)
        return task.cont

    def camShakeNod(self, distance):
        if self.ival_move_cam is not None and self.ival_move_cam.isPlaying():
            # Hack: We can't run two intervalls at the same time as they will
            # interfere each other.
            return
        if self.ival_camshake is not None and self.ival_camshake.isPlaying():
            self.ival_camshake.finish()
            self.ival_camshake = None
        posA = self.cam_floater.getPos()
        posB = self.cam_floater.getPos()
        posA.setZ(posA.getZ() - distance)
        #posB.setZ(posB.getZ() + distance*0.05)
        ivalA = self.cam_floater.posInterval(0.25, posA)
        ivalB = self.cam_floater.posInterval(0.15, posB)
        ivalC = self.cam_floater.posInterval(0.05, Vec3(tuple(self.core.getConfig("cam_floater_pos"))))
        self.ival_camshake = Sequence(
            ivalA,
            ivalB,
            ivalC,
            name="cam_shake")
        self.ival_camshake.start()
