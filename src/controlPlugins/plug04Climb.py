#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This Plugin implements the climbing logic for the player"""

#
# PYTHON IMPORTS
#
import math

#
# PANDA3D ENGINE IMPORTS
#
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Point3F

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

class Plugin(DirectObject):

    ANIM_IDLE = "Climb_idle"
    ANIM_LEFT = "Climb_Left"
    ANIM_RIGHT = "Climb_Right"
    ANIM_UP = "climb_UP"
    ANIM_DOWN = "Climb_Down"
    ANIM_UP_LEFT = "Climb_Up_Left"
    ANIM_UP_RIGHT = "Climb_Up_Right"
    ANIM_DOWN_LEFT = "Climb_Down_Left"
    ANIM_DOWN_RIGHT = "Climb_Down_Right"
    ANIM_EXIT_UP = "Climb_Exit_Up"


    STATE_CLIMB = "Climb"
    STATE_CLIMB_EXIT_UP = "ClimbExitUp"
    STATE_CLIMB_VERT = "ClimbVertical"
    STATE_CLIMB_HOR = "ClimbHorizontal"
    STATE_CLIMB_DIAG_UL_BR = "ClimbDiagonal_ul_br"
    STATE_CLIMB_DIAG_BL_UR = "ClimbDiagonal_bl_ur"


    def __init__(self, core, pid):
        self.pluginID = pid
        self.core = core

        self.can_climb = False
        self.do_climb = False

        self.can_move_vertical = False
        self.can_move_horizontal = False

        # climb directions
        self.left = False
        self.right = False
        self.up = False
        self.down = False

        #
        # SETUP STATES
        #
        # register the wall run states
        self.core.plugin_registerState(
            self.STATE_CLIMB,[
                self.STATE_CLIMB_VERT,
                self.STATE_CLIMB_HOR,
                self.STATE_CLIMB_DIAG_UL_BR,
                self.STATE_CLIMB_DIAG_BL_UR]
                + ["*"] #TODO: is this necessary here?
                + self.core.jump_and_fall_states,
            isFlying=True,
            fromAnyState=True,
            isPreventRotation=True)

        self.core.plugin_registerState(
            self.STATE_CLIMB_VERT,[
                self.STATE_CLIMB,
                self.STATE_CLIMB_HOR,
                self.STATE_CLIMB_DIAG_UL_BR,
                self.STATE_CLIMB_DIAG_BL_UR]
                + ["*"] #TODO: is this necessary here?
                + self.core.jump_and_fall_states,
            isFlying=True,
            fromAnyState=True,
            isPreventRotation=True)
        self.core.plugin_registerState(
            self.STATE_CLIMB_HOR,[
                self.STATE_CLIMB_VERT,
                self.STATE_CLIMB,
                self.STATE_CLIMB_DIAG_UL_BR,
                self.STATE_CLIMB_DIAG_BL_UR]
                + ["*"] #TODO: is this necessary here?
                + self.core.jump_and_fall_states,
            isFlying=True,
            fromAnyState=True,
            isPreventRotation=True)
        self.core.plugin_registerState(
            self.STATE_CLIMB_DIAG_UL_BR,[
                self.STATE_CLIMB_VERT,
                self.STATE_CLIMB_HOR,
                self.STATE_CLIMB,
                self.STATE_CLIMB_DIAG_BL_UR]
                + ["*"] #TODO: is this necessary here?
                + self.core.jump_and_fall_states,
            isFlying=True,
            fromAnyState=True,
            isPreventRotation=True)
        self.core.plugin_registerState(
            self.STATE_CLIMB_DIAG_BL_UR,[
                self.STATE_CLIMB_VERT,
                self.STATE_CLIMB_HOR,
                self.STATE_CLIMB_DIAG_UL_BR,
                self.STATE_CLIMB]
                + ["*"] #TODO: is this necessary here?
                + self.core.jump_and_fall_states,
            isFlying=True,
            fromAnyState=True,
            isPreventRotation=True)

        #
        # ANIMATION STATE FUNCTIONS
        #
        self.core.enterClimb = self.enterClimb
        self.core.enterClimbExitUp = self.enterClimbExitUp
        self.core.enterClimbVertical = self.enterClimbVertical
        self.core.enterClimbHorizontal = self.enterClimbHorizontal
        self.core.enterClimbDiagonal_ul_br = self.enterClimbDiagonal_ul_br
        self.core.enterClimbDiagonal_bl_ur = self.enterClimbDiagonal_bl_ur

        #
        # LOAD ANIMATIONS
        #
        #TODO: make animations
        if self.core.plugin_isFirstPersonMode():
            self.core.loadAnims({
                self.ANIM_IDLE: self.core.anim_climb_fp,
                self.ANIM_UP: self.core.anim_climb_up_fp,
                self.ANIM_DOWN: self.core.anim_climb_down_fp,
                self.ANIM_LEFT: self.core.anim_climb_left_fp,
                self.ANIM_RIGHT: self.core.anim_climb_right_fp,
                self.ANIM_UP_LEFT: self.core.anim_climb_left_up_fp,
                self.ANIM_DOWN_LEFT: self.core.anim_climb_left_down_fp,
                self.ANIM_UP_RIGHT: self.core.anim_climb_right_up_fp,
                self.ANIM_DOWN_RIGHT: self.core.anim_climb_right_down_fp,
                self.ANIM_EXIT_UP: self.core.anim_climb_exit_up_fp,})
        else:
            self.core.loadAnims({
                self.ANIM_IDLE: self.core.anim_climb,
                self.ANIM_UP: self.core.anim_climb_up,
                self.ANIM_DOWN: self.core.anim_climb_down,
                self.ANIM_LEFT: self.core.anim_climb_left,
                self.ANIM_RIGHT: self.core.anim_climb_right,
                self.ANIM_UP_LEFT: self.core.anim_climb_left_up,
                self.ANIM_DOWN_LEFT: self.core.anim_climb_left_down,
                self.ANIM_UP_RIGHT: self.core.anim_climb_right_up,
                self.ANIM_DOWN_RIGHT: self.core.anim_climb_right_down,
                self.ANIM_EXIT_UP: self.core.anim_climb_exit_up,})
        # "preload" all animations of the character
        self.core.bindAllAnims()

        #
        # SETUP COLLISION DETECTION
        #
        self.accept("plugin-character-in-collision", self.check_climbing)
        self.accept("plugin-character-out-collision", self.check_climbing)

        # Ray check center to get the climbable entry
        point_a = (0,0,0)
        point_b = (0, -self.core.climb_forward_check_dist, 0)
        self.center_ray = "climb_center_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.center_ray, point_a, point_b)

        # set up collision rays to check if the player would leave the climbable area
        # Ray check above the character
        point_a = (0,0,self.core.player_height)
        point_b = (0, -self.core.climb_forward_check_dist, self.core.player_height)
        self.top_ray = "climb_top_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.top_ray, point_a, point_b)

        # Ray check below the character
        point_a = (0,0,0)
        point_b = (0, -self.core.climb_forward_check_dist, 0)
        self.bottom_ray = "climb_bottom_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.bottom_ray, point_a, point_b)

        # Ray check left to the character
        point_a = (-self.core.player_radius,0,self.core.player_height/2.0)
        point_b = (-self.core.player_radius, -self.core.climb_forward_check_dist, self.core.player_height/2.0)
        self.left_ray = "climb_left_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.left_ray, point_a, point_b)

        # Ray check right the character
        point_a = (self.core.player_radius,0,self.core.player_height/2.0)
        point_b = (self.core.player_radius, -self.core.climb_forward_check_dist, self.core.player_height/2.0)
        self.right_ray = "climb_right_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.right_ray, point_a, point_b)

        #
        # ACTIVATE PLUGIN
        #
        self.active = True

    def updateAnimations(self, firstPersonMode):
        pass

    def check_climbing(self, collision_entry):
        entry_np = collision_entry.getIntoNodePath()
        if "climbable" in entry_np.getNetTag("Type").lower():
            self.climb_area_entry = collision_entry
            direction = entry_np.getNetTag("Direction").lower()
            if direction == "vertical":
                self.can_move_vertical = True
                self.can_move_horizontal = False
            elif direction == "horizontal":
                self.can_move_vertical = False
                self.can_move_horizontal = True
            elif direction == "both":
                self.can_move_vertical = True
                self.can_move_horizontal = True
            else:
                self.can_move_vertical = True
                self.can_move_horizontal = False
            self.can_climb = True

    def useStamina(self):
        return False

    def faceWall(self, entry):
        if entry is not None \
        and self.core.hasSurfaceNormal(entry):
            entry_normal = self.core.getSurfaceNormal(entry, render)

            # set the characters heading
            zx = math.atan2(entry_normal.getZ(), entry_normal.getX())*180/math.pi
            zy = math.atan2(entry_normal.getZ(), entry_normal.getY())*180/math.pi
            zx = abs(zx-90)
            zy = abs(zy-90)
            # face towards the wall
            h = math.atan2(-entry_normal.getX(), entry_normal.getY())*180/math.pi
            self.core.updatePlayerHpr((h, 0, 0))

    def attachToWall(self, entry):
        if entry is not None \
        and self.core.hasSurfacePoint(entry):
            point = self.core.getSurfacePoint(entry, render)
            self.core.updatePlayerPosFix(point)
            self.core.updatePlayerPosFix((0, self.core.player_radius, 0), self.core.mainNode)

    def action(self, intel_action):

        entry = self.core.getFirstCollisionEntryInLine(self.center_ray)
        if entry is not None:
            self.check_climbing(entry)
        else:
            # let go from climb object
            self.do_climb = False
            self.can_climb = False
            self.climb_area_entry = None
            #self.core.toggleFlyMode(False)
            return False

        # check if conditions are met to start climbing
        if (not self.can_climb or not intel_action):
            # check if we actually are in climb mode already
            if not self.do_climb:
                # only return if we are not climbing and not interested
                # in doing so for now
                self.climb_area_entry = None
                return False

        if self.core.do_jump:
            # let go from climb object
            self.do_climb = False
            self.can_climb = False
            self.climb_area_entry = None
            self.core.toggleFlyMode(False)
            self.core.plugin_requestNewState(None)
            return False

        self.do_climb = True

        self.faceWall(self.climb_area_entry)
        self.attachToWall(self.climb_area_entry)
        self.core.rotation = None
        self.core.toggleFlyMode(True)

        #
        # CLIMB LOGIC
        #

        # left, right, up, down
        self.left = self.right = self.up = self.down = False

        direction = self.core.plugin_getMoveDirection()

        if direction is not None:
            if self.can_move_horizontal:
                entry_left = self.core.getFirstCollisionEntryInLine(self.left_ray)
                if entry_left is not None:
                    if direction.getX() > 0:
                        self.left = True
                entry_right = self.core.getFirstCollisionEntryInLine(self.right_ray)
                if entry_right is not None:
                    if direction.getX() < 0:
                        self.right = True

            if self.can_move_vertical:
                fp_mult = 1
                if self.core.plugin_isFirstPersonMode():
                    fp_mult = -1
                entry_top = self.core.getFirstCollisionEntryInLine(self.top_ray)
                if entry_top is not None:
                    if direction.getY()*fp_mult < 0:
                        self.up = True
                else:
                    # exit climb up
                    player_pos = self.core.plugin_getPos()
                    pos = player_pos + Point3F(0, self.core.climb_forward_check_dist/2.0, self.core.player_height)
                    has_enough_space = self.core.checkFutureCharSpace(pos)
                    if has_enough_space:
                        # we want to pull up on a ledge
                        self.core.plugin_requestNewState(self.STATE_CLIMB_EXIT_UP)
                        self.core.updatePlayerPosFix(pos)
                entry_bottom = self.core.getFirstCollisionEntryInLine(self.bottom_ray)
                if entry_bottom is not None:
                    if direction.getY()*fp_mult > 0:
                        self.down = True

            self.core.plugin_requestNewState(None)
            if (self.left or self.right) and not (self.up or self.down):
                self.core.plugin_requestNewState(self.STATE_CLIMB_VERT)
            elif not (self.left or self.right) and (self.up or self.down):
                self.core.plugin_requestNewState(self.STATE_CLIMB_HOR)
            elif (self.left and self.up) or (self.right and self.down):
                self.core.plugin_requestNewState(self.STATE_CLIMB_DIAG_UL_BR)
            elif (self.left and self.down) or (self.right and self.up):
                self.core.plugin_requestNewState(self.STATE_CLIMB_DIAG_BL_UR)
            elif self.core.state != self.STATE_CLIMB:
                self.core.plugin_requestNewState(self.STATE_CLIMB)
        else:
            if self.core.state != self.STATE_CLIMB:
                self.core.plugin_requestNewState(self.STATE_CLIMB)
            else:
                self.core.plugin_requestNewState(None)

        # skip plugins following this one
        return True

    def useStamina(self):
        return False

    def moveRestriction(self):
        if self.do_climb:
            # in climb mode we can, if at all, only move left and right
            # but not rotate the player
            climb_speed = self.core.climb_sidward_move_speed
            if self.left:
                self.core.update_speed.setX(-climb_speed * self.core.dt)
            elif self.right:
                self.core.update_speed.setX(climb_speed * self.core.dt)

            climb_speed = self.core.climb_vertical_move_speed
            if self.up:
                self.core.update_speed.setZ(climb_speed * self.core.dt)
            elif self.down:
                self.core.update_speed.setZ(-climb_speed * self.core.dt)

            self.core.update_speed.setY(0)
        return self.do_climb

    #
    # FSM EXTENSION
    #
    def enterClimb(self):
        self.core.current_animations = [self.ANIM_IDLE]
        self.core.loop(self.ANIM_IDLE)

    def enterClimbExitUp(self):
        self.core.current_animations = [self.ANIM_EXIT_UP]
        self.core.actorInterval(self.ANIM_EXIT_UP).start()

    def enterClimbVertical(self):
        if self.left and self.core.getCurrentAnim() != self.ANIM_LEFT:
            self.core.current_animations = [self.ANIM_LEFT]
            self.core.loop(self.ANIM_LEFT)
        elif self.right and self.core.getCurrentAnim() != self.ANIM_RIGHT:
            self.core.current_animations = [self.ANIM_RIGHT]
            self.core.loop(self.ANIM_RIGHT)

    def enterClimbHorizontal(self):
        if self.up and self.core.getCurrentAnim() != self.ANIM_UP:
            self.core.current_animations = [self.ANIM_UP]
            self.core.loop(self.ANIM_UP)
        if self.down and self.core.getCurrentAnim() != self.ANIM_DOWN:
            self.core.current_animations = [self.ANIM_DOWN]
            self.core.loop(self.ANIM_DOWN)

    def enterClimbDiagonal_ul_br(self):
        if self.up and self.left and self.core.getCurrentAnim() != self.ANIM_UP_LEFT:
            self.core.current_animations = [self.ANIM_UP_LEFT]
            self.core.loop(self.ANIM_UP_LEFT)
        if self.right and self.down and self.core.getCurrentAnim() != self.ANIM_DOWN_RIGHT:
            self.core.current_animations = [self.ANIM_DOWN_RIGHT]
            self.core.loop(self.ANIM_DOWN_RIGHT)

    def enterClimbDiagonal_bl_ur(self):
        if self.down and self.left and self.core.getCurrentAnim() != self.ANIM_DOWN_LEFT:
            self.core.current_animations = [self.ANIM_DOWN_LEFT]
            self.core.loop(self.ANIM_DOWN_LEFT)
        if self.up and self.right and self.core.getCurrentAnim() != self.ANIM_UP_RIGHT:
            self.core.current_animations = [self.ANIM_UP_RIGHT]
            self.core.loop(self.ANIM_UP_RIGHT)
