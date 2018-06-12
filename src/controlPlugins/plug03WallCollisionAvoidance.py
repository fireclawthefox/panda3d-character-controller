#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This Plugin implements the logic for the player to not run head first
into a wall. Instead slow down and don't move forward if a wall is in
front of him"""

#
# PYTHON IMPORTS
#
import math

#
# PANDA3D ENGINE IMPORTS
#
from panda3d.core import Vec3

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

class Plugin:
    def __init__(self, core, pid):
        self.pluginID = pid
        self.core = core

        # Wall check rays to the front, left and right side of the player
        point_a = (0, 0, self.core.player_height/2.0)
        point_b = (0, -self.core.forward_check_distance, self.core.player_height/2.0)

        self.wall_avoidance_ray = "wall_avoidance_ray"
        self.core.plugin_registerCharacterRayCheck(self.wall_avoidance_ray, point_a, point_b)

        self.active = True

    def action(self, intel_action):
        #
        # FRONT WALL COLLISION AVOIDANCE
        #
        # Forward facing wall checks to not run head first into a wall
        # calculate the distance to a collision within the forward check distance
        char_front_collision = self.core.getFirstCollisionInLine(self.wall_avoidance_ray)
        # check this only if we are not having an active intel action
        if char_front_collision is not None \
        and not intel_action \
        and self.core.state != self.core.STATE_FALL:
            if not self.core.isAirborn:
                colvec = char_front_collision - self.core.plugin_getPos()
                colvec.setZ(0)
                coldist = colvec.length()
                doStateCheck = True
                if self.core.first_pserson_mode \
                and (self.core.plugin_getMoveDirection().getX() > 0 \
                or self.core.plugin_getMoveDirection().getY() != 0):
                  doStateCheck = False
                elif coldist <= self.core.forward_stop_distance:
                    # we have a wall in front of us, hence we can't move forward
                    self.core.current_accleration = 0
                elif self.core.plugin_getMoveDirection() != Vec3():
                    self.core.current_accleration -= self.core.deaccleration * self.core.dt
                    if self.core.current_accleration <= 0:
                        self.core.current_accleration = self.core.forward_min_speed_to_stop
                        if self.core.state == self.core.STATE_IDLE:
                            self.core.plugin_requestNewState(self.core.STATE_IDLE_TO_WALK)
                    doStateCheck = False
                if self.core.plugin_getRequestedNewState() != self.core.STATE_JUMP and doStateCheck:
                    if self.core.state == self.core.STATE_WALK:
                        self.core.plugin_requestNewState(self.core.STATE_WALK_TO_IDLE)
                    elif self.core.state == self.core.STATE_RUN:
                        self.core.plugin_requestNewState(self.core.STATE_RUN_TO_IDLE)
                    elif self.core.state == self.core.STATE_SPRINT:
                        self.core.plugin_requestNewState(self.core.STATE_SPRINT_TO_IDLE)
                    elif self.core.STATE_IDLE in self.core.defaultTransitions[self.core.state]:
                        self.core.plugin_requestNewState(self.core.STATE_IDLE)
                    else:
                        self.core.plugin_requestNewState(None)
        return False

    def useStamina(self):
        return False

    def moveRestriction(self):
        return False
