#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This Plugin implements the logic for the player to not run head first
into a wall. Instead slow down and don't move forward if a wall is in
front of him"""

#
# PYTHON IMPORTS
#
import math

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

def initWallCollisionAvoidance(self):
    # Wall check rays to the front, left and right side of the player
    point_a = (0, 0, self.player_height/2.0)
    point_b = (0, -self.forward_check_distance, self.player_height/2.0)
    self.wall_avoidance_ray = "wall_avoidance_ray"
    self.registerRayCheck(self.wall_avoidance_ray, point_a, point_b, self.mainNode)

def wallCollisionAvoidance(self):
    #
    # FRONT WALL COLLISION AVOIDANCE
    #
    # Forward facing wall checks to not run head first into a wall
    # calculate the distance to a collision within the forward check distance
    char_front_collision = self.getFirstCollisionInLine(self.wall_avoidance_ray)
    # check this only if we are not interested in a wall trick
    if char_front_collision is not None \
    and self.INTEL_ACTION_WALL_RUN not in self.intel_action \
    and self.INTEL_ACTION_LEDGE_GRAB not in self.intel_action:
        if not self.isAirborn:
            colvec = char_front_collision - self.mainNode.getPos()
            colvec.setZ(0)
            coldist = colvec.length()
            doStateCheck = True
            if self.first_pserson_mode \
            and (self.do_move_backward\
            or self.do_move_left \
            or self.do_move_right):
              doStateCheck = False
            elif coldist <= self.forward_stop_distance:
                # we have a wall in front of us, hence we can't move forward
                self.current_accleration = 0
            elif self.move_key_pressed:
                self.current_accleration -= self.deaccleration * self.dt
                if self.current_accleration <= 0:
                    self.current_accleration = self.forward_min_speed_to_stop
                    if self.state == self.STATE_IDLE:
                        self.request_state = self.STATE_IDLE_TO_WALK
                doStateCheck = False
            if self.request_state != self.STATE_JUMP and doStateCheck:
                if self.state == self.STATE_WALK:
                    self.request_state = self.STATE_WALK_TO_IDLE
                elif self.state == self.STATE_RUN:
                    self.request_state = self.STATE_RUN_TO_IDLE
                elif self.state == self.STATE_SPRINT:
                    self.request_state = self.STATE_SPRINT_TO_IDLE
                else:
                    if self.STATE_IDLE in self.defaultTransitions[self.state]:
                        self.request_state = self.STATE_IDLE
                    else:
                        self.request_state = None
    else:
        self.movementVec.setZ(0)
