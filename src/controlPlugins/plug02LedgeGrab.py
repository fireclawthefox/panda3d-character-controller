#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This Plugin implements the ledge grab logic for the player"""

#
# PYTHON IMPORTS
#
import math
#
# PANDA3D ENGINE IMPORTS
#
from panda3d.core import Point3, NodePath
from direct.interval.IntervalGlobal import Sequence, Func

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

class Plugin:
    LEDGE_GRAB = "Ledge_Grab"
    LEDGE_GRAB_UP = "LG_Up"
    LEDGE_GRAB_LEFT = "LG_Left"
    LEDGE_GRAB_RIGHT = "LG_Right"

    STATE_LEDGE_GRAB = "LedgeGrab"
    STATE_LEDGE_GRAB_UP = "LedgeGrabUp"
    STATE_LEDGE_GRAB_LEFT = "LedgeGrabLeft"
    STATE_LEDGE_GRAB_RIGHT = "LedgeGrabRight"

    def __init__(self, core, pid):
        self.pluginID = pid
        self.core = core
        self.do_ledge_grab = False
        self.requestIdle = False

        #
        # SETUP STATES
        #
        # all ledge grab states
        self.ledge_grab_states = [
            self.STATE_LEDGE_GRAB,
            self.STATE_LEDGE_GRAB_LEFT,
            self.STATE_LEDGE_GRAB_RIGHT,
            self.STATE_LEDGE_GRAB_UP]

        # register the wall run states
        self.core.plugin_registerState(
            self.STATE_LEDGE_GRAB,[
                self.core.STATE_FALL,
                self.STATE_LEDGE_GRAB_UP,
                self.STATE_LEDGE_GRAB_LEFT,
                self.STATE_LEDGE_GRAB_RIGHT]
                + ["*"], #TODO: implement logic for any plugin states
            isFlying=True,
            fromAnyState=True,
            isPreventRotation=True)
        self.core.plugin_registerState(
            self.STATE_LEDGE_GRAB_UP,
            ["*"],
            isFlying=True,
            isPreventRotation=True)
        self.core.plugin_registerState(
            self.STATE_LEDGE_GRAB_LEFT,[
                self.core.STATE_FALL]
                + self.ledge_grab_states
                + ["*"], #TODO: implement logic for any plugin states
            isFlying=True,
            isPreventRotation=True)
        self.core.plugin_registerState(
            self.STATE_LEDGE_GRAB_RIGHT,[
                self.core.STATE_FALL]
                + self.ledge_grab_states
                + ["*"], #TODO: implement logic for any plugin states
            isFlying=True,
            isPreventRotation=True)

        #
        # ANIMATION STATE FUNCTIONS
        #
        self.core.enterLedgeGrab = self.enterLedgeGrab
        self.core.enterLedgeGrabUp = self.enterLedgeGrabUp
        self.core.enterLedgeGrabLeft = self.enterLedgeGrabLeft
        self.core.enterLedgeGrabRight = self.enterLedgeGrabRight

        #
        # LOAD ANIMATIONS
        #
        self.updateAnimations(self.core.plugin_isFirstPersonMode())

        #
        # SETUP COLLISION DETECTION
        #
        # Wall check rays to the front of the player
        point_a = (0,0,self.core.player_height)
        point_b = (0, -self.core.wall_run_forward_check_dist, self.core.player_height)
        self.forward_ray = "ledge_grab_forward_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.forward_ray, point_a, point_b)

        # Add a ray checking if there is a grabable ledge
        point_a = (0, -self.core.ledge_forward_check_dist, self.core.ledge_top_check_dist)
        point_b = (0, -self.core.ledge_forward_check_dist, self.core.ledge_bottom_check_dist)
        self.ledge_detect_ray = "ledge_grab_ledge_detect_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.ledge_detect_ray, point_a, point_b)

        # Add a ray checking where the player will stand after pulling up a ledge
        point_a = (0, -self.core.ledge_forward_pull_up_dist, self.core.ledge_top_check_dist)
        point_b = (0, -self.core.ledge_forward_pull_up_dist, self.core.ledge_bottom_check_dist)
        self.ledge_pull_up_pos_ray = "ledge_grab_ledge_pull_up_pos_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.ledge_pull_up_pos_ray, point_a, point_b)

        # Add a ray checking if there is a grabable ledge to the left
        point_a = (self.core.player_radius / 2.0, -self.core.ledge_forward_check_dist, self.core.ledge_top_check_dist)
        point_b = (self.core.player_radius / 2.0, -self.core.ledge_forward_check_dist, self.core.ledge_bottom_check_dist)
        self.ledge_detect_ray_l = "ledge_grab_ledge_detect_ray_l-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.ledge_detect_ray_l, point_a, point_b)

        # Add a ray checking if there is a grabable ledge to the right
        point_a = (-self.core.player_radius / 2.0, -self.core.ledge_forward_check_dist, self.core.ledge_top_check_dist)
        point_b = (-self.core.player_radius / 2.0, -self.core.ledge_forward_check_dist, self.core.ledge_bottom_check_dist)
        self.ledge_detect_ray_r = "ledge_grab_ledge_detect_ray_r-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.ledge_detect_ray_r, point_a, point_b)

        #
        # ACTIVATE PLUGIN
        #
        self.active = True

    def updateAnimations(self, firstPersonMode):
        if firstPersonMode:
            self.core.loadAnims({
                self.LEDGE_GRAB: self.core.anim_ledge_grab_fp,
                self.LEDGE_GRAB_UP: self.core.anim_ledge_grab_up_fp,
                self.LEDGE_GRAB_LEFT: self.core.anim_ledge_grab_left_fp,
                self.LEDGE_GRAB_RIGHT: self.core.anim_ledge_grab_right_fp,})
        else:
            self.core.loadAnims({
                self.LEDGE_GRAB: self.core.anim_ledge_grab,
                self.LEDGE_GRAB_UP: self.core.anim_ledge_grab_up,
                self.LEDGE_GRAB_LEFT: self.core.anim_ledge_grab_left,
                self.LEDGE_GRAB_RIGHT: self.core.anim_ledge_grab_right,})
        # "preload" all animations of the character
        self.core.bindAllAnims()

    def action(self, intel_action):
        #
        # LEDGE GRAB LOGIC
        #
        # check if we want to request to transition to the idle animation
        if self.requestIdle:
            # check for the ledge grab up animation state
            ac = self.core.getAnimControl(self.LEDGE_GRAB_UP)
            if ac.isPlaying():
                # as long as it's playing we won't transition anywhere
                # and do as we're still in normal ledge grab mode
                self.core.plugin_requestNewState(None)
                return True
            else:
                # the pulling up is done, now we can transit to the idle
                # state to continue with normal execution of the character
                # controller
                self.core.plugin_requestNewState(self.core.STATE_IDLE)
                self.requestIdle = False
                return False

        # this variable can be used to check if the player can move left/right
        # when hanging on a ledge
        self.core.ledge_grab_can_move = False

        # Wall checks to the front, left and right side of the player
        char_front_collision = self.core.getFirstCollisionInLine(self.forward_ray)
        char_front_collision_entry = self.core.getFirstCollisionEntryInLine(self.forward_ray)
        ledge_collision = self.core.getFirstCollisionEntryInLine(self.ledge_detect_ray)
        ledge_collision_into = self.core.getFirstCollisionIntoNodeInLine(self.ledge_detect_ray)
        ledge_pull_up_collision = self.core.getFirstCollisionEntryInLine(self.ledge_pull_up_pos_ray)

        # this variable is to determine if we do a ledge grab and will
        # be returned at the end of this function
        self.do_ledge_grab = False

        # check for movement directions and keys
        let_go = False
        if self.core.plugin_isFirstPersonMode():
            let_go = self.core.plugin_getMoveDirection().getY() < -0.8
        else:
            let_go = self.core.plugin_getMoveDirection().getY() > 0.8
        self.move_left = self.core.plugin_getMoveDirection().getX() < 0
        self.move_right = self.core.plugin_getMoveDirection().getX() > 0

        if self.core.state in self.ledge_grab_states \
        and (let_go \
        or self.core.do_pull_up):
            #
            # LET GO / PULL UP
            #
            # We are currently in ledge grab mode
            self.do_ledge_grab = True
            self.core.plugin_requestNewState(None)
            if let_go:
                #
                # LET GO
                #
                self.core.toggleFlyMode(False)
                self.core.plugin_requestNewState(self.core.STATE_FALL)
                self.do_ledge_grab = False
            elif self.core.do_pull_up \
            and ledge_pull_up_collision is not None:
                #
                # PULL UP
                #
                # first get the position where the player should be standing
                # in the end
                pos = None
                if self.core.hasSurfacePoint(ledge_pull_up_collision):
                    pos = self.core.getSurfacePoint(ledge_pull_up_collision, render)
                elif self.core.hasContactPos(ledge_pull_up_collision):
                    pos = self.core.getContactPos(ledge_pull_up_collision, render)

                # check weather the player would actually have enough
                # space to stand there and only continue if so
                has_enough_space = self.core.checkFutureCharSpace(pos)
                if pos is not None and has_enough_space:
                    # we want to pull up on a ledge
                    self.core.plugin_requestNewState(self.STATE_LEDGE_GRAB_UP)
                    pos.setZ(pos.getZ() + 0.05)
                    self.core.updatePlayerPosFix(pos)

        elif self.core.state in self.ledge_grab_states \
        and (self.move_left \
        or self.move_right):
            #
            # LEFT / RIGHT
            #
            self.do_ledge_grab = True
            ledge_move_collision = None
            direction = None
            # check which direction we are moving
            if self.move_left:
                ledge_move_collision = self.core.getFirstCollisionEntryInLine(self.ledge_detect_ray_l)
                direction = "left"
            else:
                ledge_move_collision = self.core.getFirstCollisionEntryInLine(self.ledge_detect_ray_r)
                direction = "right"
            self.core.plugin_requestNewState(None)
            # check if we actually are able to move
            if ledge_move_collision is not None:
                self.core.ledge_grab_can_move = True
                self.core.setCurrentAnimsPlayRate(1.0)
                if direction == "left":
                    if self.core.state != self.STATE_LEDGE_GRAB_LEFT:
                        self.core.plugin_requestNewState(self.STATE_LEDGE_GRAB_LEFT)
                elif direction == "right":
                    if self.core.state != self.STATE_LEDGE_GRAB_RIGHT:
                        self.core.plugin_requestNewState(self.STATE_LEDGE_GRAB_RIGHT)
            elif self.core.state != self.STATE_LEDGE_GRAB:
                # make sure the "idle" ledge grab animation playes if
                # we are in ledge grab mode but can't move
                self.core.plugin_requestNewState(self.STATE_LEDGE_GRAB)

            if ledge_move_collision is None:
                # we can't move, so make sure we don't have any move vars set
                self.move_left = False
                self.move_right = False

            # check if the object we are attached to is a movable object
            self.core.checkFloatingPlatform(ledge_collision_into)
            # make sure we are looking towards the object
            self.faceWall(char_front_collision_entry)
            # make sure we are close to the object we are attached to
            self.attachToWall(char_front_collision, ledge_collision)

        elif self.core.state in self.ledge_grab_states \
        and not self.core.state == self.STATE_LEDGE_GRAB_UP \
        and ledge_collision is not None:
            #
            # STAY IN LEDGE GRAB
            #
            self.do_ledge_grab = True

            self.core.plugin_requestNewState(None)
            if self.core.state != self.STATE_LEDGE_GRAB:
                self.core.plugin_requestNewState(self.STATE_LEDGE_GRAB)

            # check if the object we are attached to is a movable object
            self.core.checkFloatingPlatform(ledge_collision_into)
            # make sure we are looking towards the object
            self.faceWall(char_front_collision_entry)
            # make sure we are close to the object we are attached to
            self.attachToWall(char_front_collision, ledge_collision)

        elif ledge_collision is not None \
        and intel_action \
        and self.core.state not in self.ledge_grab_states:
            #
            # INITIATE LEDGE GRAB
            #
            # only initiate a ledge grab if certain conditions are met
            ledge_normal = None
            if self.core.hasSurfaceNormal(ledge_collision):
                ledge_normal = self.core.getSurfaceNormal(ledge_collision, render)
            if ledge_normal is not None:
                if ledge_normal.getZ() > 0:

                    self.core.checkFloatingPlatform(ledge_collision_into)
                    self.faceWall(char_front_collision_entry)
                    self.attachToWall(char_front_collision, ledge_collision)

                    self.core.plugin_requestNewState(self.STATE_LEDGE_GRAB)
                    self.do_ledge_grab = True
        if self.do_ledge_grab:
            self.core.toggleFlyMode(True)
            self.core.rotation = None
            vec = self.core.plugin_getMoveDirection()
            vec.setY(0)
            self.core.plugin_setMoveDirection(vec)
        return self.do_ledge_grab

    def useStamina(self):
        # this plugin doesn't use stamina
        return False

    def moveRestriction(self):
        if self.core.state in self.ledge_grab_states:
            self.core.update_speed.setX(0)
            self.core.update_speed.setY(0)
            self.core.update_speed.setZ(0)
        if self.do_ledge_grab \
        and self.core.ledge_grab_can_move \
        and self.core.state != self.STATE_LEDGE_GRAB_UP:
            # in ledge grab mode we can only move left and right but not
            # rotate the player
            lg_speed = self.core.ledge_grab_sidward_move_speed
            if self.move_left:
                self.core.update_speed.setX(lg_speed * self.core.dt)
            elif self.move_right:
                self.core.update_speed.setX(-lg_speed * self.core.dt)
            self.core.update_speed.setY(0)
            self.core.update_speed.setZ(0)
        return self.do_ledge_grab

    #
    # LEDGE GRAB HELPER FUNCTIONS
    #
    def faceWall(self, char_front_collision_entry):
        if char_front_collision_entry is not None \
        and self.core.hasSurfaceNormal(char_front_collision_entry):
            wall_normal = self.core.getSurfaceNormal(char_front_collision_entry, render)

            # set the characters heading
            #zx = math.atan2(wall_normal.getZ(), wall_normal.getX())*180/math.pi
            #zy = math.atan2(wall_normal.getZ(), wall_normal.getY())*180/math.pi
            #zx = abs(zx-90)
            #zy = abs(zy-90)
            # face towards the wall
            h = math.atan2(-wall_normal.getX(), wall_normal.getY())*180/math.pi
            self.core.updatePlayerHpr((h, 0, 0))

    def attachToWall(self, wallCollisionPos, entryLedge):
        ledge_z = self.core.plugin_getPos().getZ()
        if entryLedge is not None:
            ledge_z = 0
            if self.core.hasSurfacePoint(entryLedge):
                ledge_z = self.core.getSurfacePoint(entryLedge, render).getZ()
            elif self.core.hasContactPos(entryLedge):
                ledge_z = self.core.getContactPos(entryLedge, render).getZ()

        wallPos = NodePath("WALL-COL-TEMP")
        wallPos.setHpr(self.core.plugin_getHpr())
        if wallCollisionPos is None and entryLedge is not None:
            # This can happen if we hang on a concave ledge shape (e.g. Floating platforms)
            if self.core.hasSurfacePoint(entryLedge):
                wallPos.setPos(self.core.getSurfacePoint(entryLedge, render))
            elif self.core.hasContactPos(entryLedge):
                wallPos.setPos(self.core.getContactPos(entryLedge, render))
        elif wallCollisionPos is not None:
            wallPos.setPos(wallCollisionPos)
        else:
            # we have no positions to work with!
            return
        wallPos.setZ(ledge_z - self.core.player_height - 0.05)
        wallPos.setPos(wallPos, (self.core.plugin_getPos(wallPos).getX(), self.core.player_radius + 0.05, 0))

        self.core.updatePlayerPosFix(wallPos.getPos())

    #
    # FSM EXTENSION
    #
    def enterLedgeGrab(self):
        self.core.loop(self.LEDGE_GRAB)

    def enterLedgeGrabUp(self):
        self.core.current_animations = [self.LEDGE_GRAB_UP]
        if not self.core.getCurrentAnim() == self.LEDGE_GRAB_UP:
            self.requestIdle = True
            self.core.play(self.LEDGE_GRAB_UP)

    def enterLedgeGrabLeft(self):
        self.core.current_animations = [self.LEDGE_GRAB_LEFT]
        if not self.core.getCurrentAnim() == self.LEDGE_GRAB_LEFT:
            self.core.loop(self.LEDGE_GRAB_LEFT)

    def enterLedgeGrabRight(self):
        self.core.current_animations = [self.LEDGE_GRAB_RIGHT]
        if not self.core.getCurrentAnim() == self.LEDGE_GRAB_RIGHT:
            self.core.loop(self.LEDGE_GRAB_RIGHT)
