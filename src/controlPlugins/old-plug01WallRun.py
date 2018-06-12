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

def initWallRun(self):
    # Wall check rays to the front, left and right side of the player
    point_a = (0,0,self.player_height/2.0)
    point_b = (0, -self.wall_run_forward_check_dist, self.player_height/2.0)
    self.forward_ray = "wall_run_forward_ray"
    self.registerRayCheck(self.forward_ray, point_a, point_b, self.mainNode)

    # Left side collision
    point_b = (self.wall_run_sideward_check_dist, 0, self.player_height/2.0)
    self.left_ray = "wall_run_left_ray"
    self.registerRayCheck(self.left_ray, point_a, point_b, self.mainNode)

    # Right side collision
    point_b = (-self.wall_run_sideward_check_dist, 0, self.player_height/2.0)
    self.right_ray = "wall_run_right_ray"
    self.registerRayCheck("wall_run_right_ray", point_a, point_b, self.mainNode)

def wallRun(self):
    if not self.wall_run_enabled: return
    #
    # WALL COLLISION CHECKS WALL RUN
    #
    char_front_collision = self.getFirstCollisionInLine(self.forward_ray)
    char_front_collision_entry = self.getFirstCollisionEntryInLine(self.forward_ray)
    char_left_collision_entry = self.getFirstCollisionEntryInLine(self.left_ray)
    char_right_collision_entry = self.getFirstCollisionEntryInLine(self.right_ray)
    #
    # WALL RUN LOGIC
    #
    checked_fall_time = True
    if self.state is self.STATE_FALL:
        checked_fall_time = self.fall_time > self.wall_run_min_fall_time
    if (
        char_front_collision_entry is not None \
        or char_left_collision_entry is not None \
        or char_right_collision_entry is not None \
    ) \
    and self.do_intel_action \
    and self.state in self.wall_run_possible_states \
    and checked_fall_time :
        wall_run_possible = False
        wall_normal = None
        #TODO: Maybe make the jumps relative to user input when doing a wall run
        prev_jump_direction = self.jump_direction
        if char_front_collision_entry:
            # we have a wall in front of us that we can walk up
            if self.hasSurfaceNormal(char_front_collision_entry):
                wall_normal = self.getSurfaceNormal(char_front_collision_entry, render)
                self.setWallRunDirection(self.WALLRUN_UP)
                self.jump_direction = self.wall_run_up_jump_direction
        elif char_left_collision_entry:
            # we have a wall to our left that we can walk along
            if self.hasSurfaceNormal(char_left_collision_entry):
                wall_normal = self.getSurfaceNormal(char_left_collision_entry, render)
                wall_normal.setY(-wall_normal.getY())
                wall_normal.setX(-wall_normal.getX())
                self.setWallRunDirection(self.WALLRUN_LEFT)
                self.jump_direction = self.wall_run_left_jump_direction

                # make sure we're always as close to the wall as possible
                pos = char_left_collision_entry.getSurfacePoint(render)
                posA = NodePath("WALL-COL-TEMP")
                posA.setPos(pos)
                posB = NodePath("CHAR-TEMP")
                posB.setPos(self.mainNode.getPos())
                diff = posA.getPos() - posB.getPos()
                posA.removeNode()
                posB.removeNode()
                newPos = (-(-diff.length() + self.player_radius + 0.2), 0, 0)
                self.updatePlayerPosFix(newPos, self.mainNode)
        elif char_right_collision_entry:
            # we have a wall to our right that we can walk along
            if self.hasSurfaceNormal(char_right_collision_entry):
                wall_normal = self.getSurfaceNormal(char_right_collision_entry, render)
                self.setWallRunDirection(self.WALLRUN_RIGHT)
                self.jump_direction = self.wall_run_right_jump_direction

                # make sure we're always as close to the wall as possible
                pos = char_right_collision_entry.getSurfacePoint(render)
                posA = NodePath("WALL-COL-TEMP")
                posA.setPos(pos)
                posB = NodePath("CHAR-TEMP")
                posB.setPos(self.mainNode.getPos())
                diff = posA.getPos() - posB.getPos()
                posA.removeNode()
                posB.removeNode()
                newPos = (-diff.length() + self.player_radius + 0.2, 0, 0)
                self.updatePlayerPosFix(newPos, self.mainNode)

        # set the characters heading if aplicable
        if wall_normal is not None:
            zx = math.atan2(wall_normal.getZ(), wall_normal.getX())*180/math.pi
            zy = math.atan2(wall_normal.getZ(), wall_normal.getY())*180/math.pi
            zx = abs(zx-90)
            zy = abs(zy-90)
            if zy >= self.min_wall_angle_for_wall_run and zx >= self.min_wall_angle_for_wall_run:
                if self.wall_run_direction == self.WALLRUN_UP:
                    # face towards the wall
                    h = math.atan2(-wall_normal.getX(), wall_normal.getY())*180/math.pi
                else:
                    # face along the wall
                    h = math.atan2(wall_normal.getY(), wall_normal.getX())*180/math.pi

                if self.mainNode.getH() != h:
                    tempNP = NodePath("tempCamNP")
                    tempNP.reparentTo(self.mainNode)
                    tempNP.setPos(camera.getPos(self.mainNode))
                    self.updatePlayerHpr((h, 0, 0))
                    self.camera_handler.requestReposition(tempNP.getPos(render))
                    tempNP.remove_node()
                # invalidate other self.rotational movements that were set before
                self.rotation = None
                wall_run_possible = True
        if wall_run_possible:
            self.intel_action.append(self.INTEL_ACTION_WALL_RUN)
            self.pre_jump_state = self.STATE_RUN
            if self.state not in [self.STATE_WALL_RUN, self.STATE_RUN_TO_WALL_RUN, self.STATE_SPRINT_TO_WALL_RUN, self.STATE_JUMP]:
                if self.state in [self.STATE_RUN, self.STATE_SPRINT_TO_RUN]:
                    self.request_state = self.STATE_RUN_TO_WALL_RUN
                elif self.state in  [self.STATE_RUN_TO_SPRINT, self.STATE_SPRINT]:
                    self.request_state = self.STATE_SPRINT_TO_WALL_RUN
                else:
                    self.request_state = self.STATE_WALL_RUN
                self.jump_strength = self.wall_run_off_jump_strength
        else:
            self.jump_direction = prev_jump_direction
    else:
        self.jump_strength = self.jump_strength_default
        if self.state in self.wall_run_states:
            self.request_state = self.STATE_RUN

def wallRunMoveRestriction(self):
    if self.INTEL_ACTION_WALL_RUN in self.intel_action and not self.wasJumping:
        # if we are runing on a wall add some speed to the Z axis
        # movement of the player
        wr_speed = self.wall_run_speed * self.current_accleration
        if wr_speed > self.max_wall_run_speed:
            wr_speed = self.max_wall_run_speed
        #if wr_speed <= 0:
        #    wr_speed = self.min_wall_run_speed
        self.update_speed.setZ(wr_speed * self.dt)
