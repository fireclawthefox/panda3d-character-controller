#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This Plugin implements the wall run logic for the player"""

#
# PYTHON IMPORTS
#
import math

#
# PANDA3D IMPORTS
#
from panda3d.core import NodePath

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

class Plugin:
    STATE_WALL_RUN = "WallRun"
    STATE_RUN_TO_WALL_RUN = "RunToWallRun"
    STATE_SPRINT_TO_WALL_RUN = "SprintToWallRun"

    WALLRUN_LEFT = "WR_Left"
    WALLRUN_RIGHT = "WR_Right"
    WALLRUN_UP = "WR_Up"

    def __init__(self, core, pid):
        self.pluginID = pid
        self.core = core
        self.do_wall_run = False

        #
        # SETUP STATES
        #
        # all wall run states
        self.wall_run_states = [
            self.STATE_WALL_RUN,
            self.STATE_RUN_TO_WALL_RUN,
            self.STATE_SPRINT_TO_WALL_RUN,
            ]

        # register the wall run states
        self.core.plugin_registerState(
            self.STATE_WALL_RUN,[
                self.core.STATE_IDLE,
                self.core.STATE_WALK,
                self.core.STATE_RUN,
                self.core.STATE_SPRINT,
                self.core.STATE_JUMP,
                self.core.STATE_LAND]
                + ["*"] #TODO: implement logic for any plugin states
                + self.core.jump_and_fall_states
                + self.wall_run_states,
            isOnGround=False,
            isFlying=True)

        self.core.plugin_registerState(
            self.STATE_RUN_TO_WALL_RUN,[
                self.core.STATE_IDLE,
                self.core.STATE_RUN,
                self.core.STATE_SPRINT]
                + ["*"] #TODO: implement logic for any plugin states
                + self.core.jump_and_fall_states
                + self.wall_run_states,
            isFlying=True)

        self.core.plugin_registerState(
            self.STATE_SPRINT_TO_WALL_RUN,[
                self.core.STATE_IDLE,
                self.core.STATE_RUN,
                self.core.STATE_SPRINT]
                + ["*"] #TODO: implement logic for any plugin states
                + self.core.jump_and_fall_states
                + self.wall_run_states,
            isFlying=True)


        # just a list containing all the states from which a wall run can be ignited
        self.wall_run_possible_states = self.wall_run_states \
            + self.core.run_states \
            + self.core.sprint_states \
            + self.core.jump_and_fall_states

        # add transition to all states that should be able to transit to the wall run states
        for state in self.wall_run_possible_states:
            self.core.plugin_addStateTransition(state, self.wall_run_states)

        #
        # ANIMATION STATE FUNCTIONS
        #
        self.ease_in_wall_run_up = self.core.createEaseIn(self.WALLRUN_UP)
        self.ease_in_wall_run_l = self.core.createEaseIn(self.WALLRUN_LEFT)
        self.ease_in_wall_run_r = self.core.createEaseIn(self.WALLRUN_RIGHT)

        self.core.enterWallRun = self.enterWallRun
        self.core.enterRunToWallRun = self.enterRunToWallRun
        self.core.exitRunToWallRun = self.exitRunToWallRun
        self.core.enterSprintToWallRun = self.enterSprintToWallRun
        self.core.exitSprintToWallRun = self.exitSprintToWallRun
        self.core.enterJumpToWallRun = self.enterJumpToWallRun
        self.core.exitJumpToWallRun = self.exitJumpToWallRun
        self.core.enterFallToWallRun = self.enterFallToWallRun
        self.core.exitFallToWallRun = self.exitFallToWallRun

        #
        # LOAD ANIMATIONS
        #
        self.updateAnimations(self.core.plugin_isFirstPersonMode())

        #
        # SETUP COLLISION DETECTION
        #
        # Wall check rays to the front, left and right side of the player
        point_a = (0,0,self.core.player_height/2.0)
        point_b = (0, -self.core.wall_run_forward_check_dist, self.core.player_height/2.0)
        self.forward_ray = "wall_run_forward_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.forward_ray, point_a, point_b)

        # Left side collision
        point_b = (self.core.wall_run_sideward_check_dist, 0, self.core.player_height/2.0)
        self.left_ray = "wall_run_left_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.left_ray, point_a, point_b)

        # Right side collision
        point_b = (-self.core.wall_run_sideward_check_dist, 0, self.core.player_height/2.0)
        self.right_ray = "wall_run_right_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.right_ray, point_a, point_b)

        #
        # ACTIVATE PLUGIN
        #
        self.active = True

    def updateAnimations(self, firstPersonMode):
        if firstPersonMode:
            self.core.loadAnims({
                self.WALLRUN_LEFT: self.core.anim_wallrun_left_fp,
                self.WALLRUN_RIGHT: self.core.anim_wallrun_right_fp,
                self.WALLRUN_UP: self.core.anim_wallrun_up_fp,})
        else:
            self.core.loadAnims({
                self.WALLRUN_LEFT: self.core.anim_wallrun_left,
                self.WALLRUN_RIGHT: self.core.anim_wallrun_right,
                self.WALLRUN_UP: self.core.anim_wallrun_up,})
        # "preload" all animations of the character
        self.core.bindAllAnims()

    def action(self, intel_action):
        if not self.core.wall_run_enabled: return
        #
        # WALL COLLISION CHECKS WALL RUN
        #
        char_front_collision_entry = self.core.getFirstCollisionEntryInLine(self.forward_ray)
        char_left_collision_entry = self.core.getFirstCollisionEntryInLine(self.left_ray)
        char_right_collision_entry = self.core.getFirstCollisionEntryInLine(self.right_ray)
        #
        # WALL RUN LOGIC
        #
        checked_fall_time = True
        if self.core.state is self.core.STATE_FALL:
            checked_fall_time = self.core.fall_time > self.core.wall_run_min_fall_time
        if (
            char_front_collision_entry is not None \
            or char_left_collision_entry is not None \
            or char_right_collision_entry is not None \
        ) \
        and intel_action \
        and self.core.state in self.wall_run_possible_states \
        and checked_fall_time \
        and not self.core.do_jump:
            wall_run_possible = False
            wall_normal = None
            #TODO: Maybe make the jumps relative to user input when doing a wall run
            prev_jump_direction = self.core.jump_direction
            if char_front_collision_entry:
                # we have a wall in front of us that we can walk up
                if self.core.hasSurfaceNormal(char_front_collision_entry):
                    wall_normal = self.core.getSurfaceNormal(char_front_collision_entry, render)
                    self.setWallRunDirection(self.WALLRUN_UP)
                    self.core.jump_direction = self.core.wall_run_up_jump_direction
            elif char_left_collision_entry:
                # we have a wall to our left that we can walk along
                if self.core.hasSurfaceNormal(char_left_collision_entry):
                    wall_normal = self.core.getSurfaceNormal(char_left_collision_entry, render)
                    wall_normal.setY(-wall_normal.getY())
                    wall_normal.setX(-wall_normal.getX())
                    self.setWallRunDirection(self.WALLRUN_LEFT)
                    self.core.jump_direction = self.core.wall_run_left_jump_direction

                    # make sure we're always as close to the wall as possible
                    pos = char_left_collision_entry.getSurfacePoint(render)
                    posA = NodePath("WALL-COL-TEMP")
                    posA.setPos(pos)
                    posB = NodePath("CHAR-TEMP")
                    posB.setPos(self.core.mainNode.getPos())
                    diff = posA.getPos() - posB.getPos()
                    posA.removeNode()
                    posB.removeNode()
                    newPos = (-(-diff.length() + self.core.player_radius + 0.2), 0, 0)
                    self.core.updatePlayerPosFix(newPos, self.core.mainNode)
            elif char_right_collision_entry:
                # we have a wall to our right that we can walk along
                if self.core.hasSurfaceNormal(char_right_collision_entry):
                    wall_normal = self.core.getSurfaceNormal(char_right_collision_entry, render)
                    self.setWallRunDirection(self.WALLRUN_RIGHT)
                    self.core.jump_direction = self.core.wall_run_right_jump_direction

                    # make sure we're always as close to the wall as possible
                    pos = char_right_collision_entry.getSurfacePoint(render)
                    posA = NodePath("WALL-COL-TEMP")
                    posA.setPos(pos)
                    posB = NodePath("CHAR-TEMP")
                    posB.setPos(self.core.mainNode.getPos())
                    diff = posA.getPos() - posB.getPos()
                    posA.removeNode()
                    posB.removeNode()
                    newPos = (-diff.length() + self.core.player_radius + 0.2, 0, 0)
                    self.core.updatePlayerPosFix(newPos, self.core.mainNode)

            # set the characters heading if aplicable
            if wall_normal is not None:
                zx = math.atan2(wall_normal.getZ(), wall_normal.getX())*180/math.pi
                zy = math.atan2(wall_normal.getZ(), wall_normal.getY())*180/math.pi
                zx = abs(zx-90)
                zy = abs(zy-90)
                if zy >= self.core.min_wall_angle_for_wall_run and zx >= self.core.min_wall_angle_for_wall_run:
                    if self.wall_run_direction == self.WALLRUN_UP:
                        # face towards the wall
                        h = math.atan2(-wall_normal.getX(), wall_normal.getY())*180/math.pi
                    else:
                        # face along the wall
                        h = math.atan2(wall_normal.getY(), wall_normal.getX())*180/math.pi

                    if self.core.mainNode.getH() != h:
                        tempNP = NodePath("tempCamNP")
                        tempNP.reparentTo(self.core.mainNode)
                        tempNP.setPos(camera.getPos(self.core.mainNode))
                        self.core.updatePlayerHpr((h, 0, 0))
                        self.core.camera_handler.requestReposition(tempNP.getPos(render))
                        tempNP.remove_node()
                    # invalidate other self.core.rotational movements that were set before
                    self.core.rotation = None
                    wall_run_possible = True
            if wall_run_possible:
                self.do_wall_run = True
                self.core.pre_jump_state = self.core.STATE_RUN
                if self.core.state not in [self.STATE_WALL_RUN, self.STATE_RUN_TO_WALL_RUN, self.STATE_SPRINT_TO_WALL_RUN, self.core.STATE_JUMP]:
                    if self.core.state in [self.core.run_states]:
                        self.core.plugin_requestNewState(self.STATE_RUN_TO_WALL_RUN)
                    elif self.core.state in  [self.core.sprint_states]:
                        self.core.plugin_requestNewState(self.STATE_SPRINT_TO_WALL_RUN)
                    else:
                        self.core.plugin_requestNewState(self.STATE_WALL_RUN)
                    self.core.jump_strength = self.core.wall_run_off_jump_strength
            else:
                vec = self.core.plugin_getMoveDirection()
                vec.setZ(0)
                self.core.plugin_setMoveDirection(vec)
                self.core.jump_direction = prev_jump_direction
        else:
            vec = self.core.plugin_getMoveDirection()
            vec.setZ(0)
            self.core.plugin_setMoveDirection(vec)
            self.core.jump_strength = self.core.jump_strength_default
            if self.core.state in self.wall_run_states:
                self.core.plugin_requestNewState(self.core.STATE_RUN)
        return False

    def useStamina(self):
        return False

    def moveRestriction(self):
        if self.do_wall_run and not self.core.wasJumping:
            # if we are runing on a wall add some speed to the Z axis
            # movement of the player
            wr_speed = self.core.wall_run_speed * self.core.current_accleration
            if wr_speed > self.core.max_wall_run_speed:
                wr_speed = self.core.max_wall_run_speed
            #if wr_speed <= 0:
            #    wr_speed = self.core.min_wall_run_speed
            self.core.update_speed.setZ(wr_speed * self.core.dt)
            self.do_wall_run = False

    #
    # FSM EXTENSION HELPER
    #
    def setWallRunDirection(self, direction):
        self.wall_run_direction = direction

    def startWRSeq(self, animFrom, easeOut):
        """Start a wall run sequence dependent on the direction of the
        wall run set in self.wall_run_direction. Also, start the run
        sound effect"""
        base.messenger.send(self.core.audio_play_run_evt)
        if self.wall_run_direction == self.WALLRUN_UP:
            self.core.startCurSeq(animFrom, self.WALLRUN_UP, self.ease_in_wall_run_up, easeOut, self.STATE_WALL_RUN)
        elif self.wall_run_direction == self.WALLRUN_LEFT:
            self.core.startCurSeq(animFrom, self.WALLRUN_LEFT, self.ease_in_wall_run_l, easeOut, self.STATE_WALL_RUN)
        elif self.wall_run_direction == self.WALLRUN_RIGHT:
            self.core.startCurSeq(animFrom, self.WALLRUN_RIGHT, self.ease_in_wall_run_r, easeOut, self.STATE_WALL_RUN)

    #
    # FSM EXTENSION
    #
    def enterWallRun(self):
        self.core.current_animations = [self.wall_run_direction]
        if not self.core.getCurrentAnim() == self.wall_run_direction:
            self.core.loop(self.wall_run_direction)

    def enterRunToWallRun(self):
        self.startWRSeq(self.core.RUN, self.core.ease_out_run)
    def exitRunToWallRun(self):
        self.core.endCurSeq()

    def enterSprintToWallRun(self):
        self.startWRSeq(self.core.SPRINT, self.core.ease_out_sprint)
    def exitSprintToWallRun(self):
        self.core.endCurSeq()

    def enterJumpToWallRun(self):
        self.startWRSeq(self.core.JUMP_START, self.core.ease_out_jump)
    def exitJumpToWallRun(self):
        self.core.endCurSeq()

    def enterFallToWallRun(self):
        self.startWRSeq(self.core.FALL, self.core.ease_out_fall)
    def exitFallToWallRun(self):
        self.core.endCurSeq()
