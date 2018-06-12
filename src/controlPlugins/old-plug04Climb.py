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

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

def initClimb(self):
    #
    # Rays to detect if there is a climbable area nearby
    #

    # Wall check rays to the front of the player
    point_a = (0,0,self.player_height/2.0)1
    point_b = (0, -self.wall_run_forward_check_dist, self.player_height/2.0)
    self.climb_detect_ray = "climb_detect_ray"
    self.registerRayCheck(self.climb_detect_ray, point_a, point_b, self.mainNode)

    # Add a ray checking if there is a climbable spot to the left
    point_a = (self.player_radius, 0, self.player_height/2.0)
    point_b = (self.player_radius, -self.ledge_forward_check_dist, self.player_height/2.0)
    self.climb_detect_ray_l = "climb_detect_ray_l"
    self.registerRayCheck(self.climb_detect_ray_l, point_a, point_b, self.mainNode)

    # Add a ray checking if there is a climbable spot to the right
    point_a = (-self.player_radius, 0, self.player_height/2.0)
    point_b = (-self.player_radius, -self.ledge_forward_check_dist, self.player_height/2.0)
    self.climb_detect_ray_r = "climb_detect_ray_r"
    self.registerRayCheck(self.climb_detect_ray_r, point_a, point_b, self.mainNode)


    #
    # Rays to detect if the player is within the climbable area
    #

    # Add a ray checking if there is a climbable spot to the top
    point_a = (0, 0, self.climb_top_check_dist)
    point_b = (0, -self.ledge_forward_check_dist, self.climb_top_check_dist)
    self.in_climb_detect_ray_t = "in_climb_detect_ray_t"
    self.registerRayCheck(self.in_climb_detect_ray_t, point_a, point_b, self.mainNode)

    # Add a ray checking if there is a climbable spot to the left
    point_a = (self.player_radius, 0, self.player_height/2.0)
    point_b = (self.player_radius, -self.ledge_forward_check_dist, self.player_height/2.0)
    self.in_climb_detect_ray_l = "in_climb_detect_ray_l"
    self.registerRayCheck(self.in_climb_detect_ray_l, point_a, point_b, self.mainNode)

    # Add a ray checking if there is a climbable spot to the right
    point_a = (-self.player_radius, 0, self.player_height/2.0)
    point_b = (-self.player_radius, -self.ledge_forward_check_dist, self.player_height/2.0)
    self.in_climb_detect_ray_r = "in_climb_detect_ray_r"
    self.registerRayCheck(self.in_climb_detect_ray_r, point_a, point_b, self.mainNode)

def climb(self):
    #
    # CLIMB LOGIC
    #
    if not is_climbing and not self.do_intel_action:
        # we don't have to do anything here
        return

    if self.do_let_go:
        # let go from ledge grab
        self.toggleFlyMode(False)
        return

    self.intel_action.remove(self.INTEL_ACTION_CLIMB)

    # this variable can be used to check if the player can move left/right
    # when climbing
    self.climb_grab_can_move = False
    # Wall checks to the front, left and right side of the player
    climb_collision_front_entry = self.getFirstCollisionEntryInLine(self.climb_detect_ray_f)
    climb_collision_left_entry = self.getFirstCollisionEntryInLine(self.climb_detect_ray_l)
    climb_collision_right_entry = self.getFirstCollisionEntryInLine(self.climb_detect_ray_r)

    climb_collision_top = self.getFirstCollisionEntryInLine(self.in_climb_detect_ray_t)
    climb_collision_left = self.getFirstCollisionEntryInLine(self.in_climb_detect_ray_l)
    climb_collision_right = self.getFirstCollisionEntryInLine(self.in_climb_detect_ray_r)



    if climb_collision_front_entry or climb_collision_left_entry or climb_collision_right_entry:
        # there is a climbable area near us
        self.isAirborn = True
        self.toggleFlyMode(True)
        self.rotation = None
        self.intel_action.append(self.INTEL_ACTION_CLIMB)
        wall_normal = None
        if climb_collision_front_entry:
            # we have a wall in front of us that we can walk up
            if self.hasSurfaceNormal(climb_collision_front_entry):
                wall_normal = self.getSurfaceNormal(climb_collision_front_entry, render)
        elif climb_collision_left_entry:
            # we have a wall to our left that we can walk along
            if self.hasSurfaceNormal(climb_collision_left_entry):
                wall_normal = self.getSurfaceNormal(climb_collision_left_entry, render)
                wall_normal.setY(-wall_normal.getY())
                wall_normal.setX(-wall_normal.getX())
        elif climb_collision_right_entry:
            # we have a wall to our left that we can walk along
            if self.hasSurfaceNormal(climb_collision_right_entry):
                wall_normal = self.getSurfaceNormal(climb_collision_right_entry, render)

        if wall_normal is not None:
            # set the characters heading
            zx = math.atan2(wall_normal.getZ(), wall_normal.getX())*180/math.pi
            zy = math.atan2(wall_normal.getZ(), wall_normal.getY())*180/math.pi
            zx = abs(zx-90)
            zy = abs(zy-90)
            # face towards the wall
            h = math.atan2(-wall_normal.getX(), wall_normal.getY())*180/math.pi
            self.updatePlayerHpr((h, 0, 0))

        # TODO: does this need to be in the restriction method?
        if self.do_move_forward:
            # climb up
            self.update_speed.setZ(climb_speed * self.dt)
        elif self.do_move_backward:
            # climb down
            self.update_speed.setZ(-climb_speed * self.dt)
        elif self.do_move_right:
            # climb right
            self.update_speed.setX(-climb_speed * self.dt)
        elif self.do_move_left:
            # climb left
            self.update_speed.setX(climb_speed * self.dt)





    if self.state in self.ledge_grab_states \
    and (self.do_let_go \
    or self.do_jump \
    or (ledge_collision is None \
    and self.state != self.STATE_LEDGE_GRAB_UP)):
        self.rotation = None
        self.request_state = self.STATE_FALL
        self.isAirborn = True
        if self.INTEL_ACTION_WALL_RUN in self.intel_action:
            self.intel_action.remove(self.INTEL_ACTION_WALL_RUN)
        self.intel_action.append(self.INTEL_ACTION_LEDGE_GRAB)
        if self.do_let_go:
            # let go from ledge grab
            self.toggleFlyMode(False)
        elif self.do_jump \
        and ledge_collision is not None:
            # we want to pull up
            pos = None
            if self.hasSurfacePoint(ledge_collision):
                pos = self.getSurfacePoint(ledge_collision, render)
            elif self.hasContactPos(ledge_collision):
                pos = self.getContactPos(ledge_collision, render)
            has_enough_space = self.checkFutureCharSpace(pos)
            if pos is not None and has_enough_space:
                # we want to pull up on a ledge
                self.request_state = self.STATE_LEDGE_GRAB_UP
                self.updatePlayerPosFix(pos)
                #self.isAirborn = False
            elif has_enough_space:
                # we have no wall or place to pull up to, so simply
                # let go from ledge and fall down
                self.toggleFlyMode(False)
            else:
                self.request_state = None
    elif self.state in self.ledge_grab_states \
    and (self.do_move_left \
    or self.do_move_right):
        if self.INTEL_ACTION_WALL_RUN in self.intel_action:
            self.intel_action.remove(self.INTEL_ACTION_WALL_RUN)
        self.intel_action.append(self.INTEL_ACTION_LEDGE_GRAB)
        self.rotation = None
        ledge_move_collision = None
        direction = None
        if self.do_move_left:
            ledge_move_collision = self.getFirstCollisionEntryInLine(self.ledge_detect_ray_l)
            direction = "left"
        else:
            ledge_move_collision = self.getFirstCollisionEntryInLine(self.ledge_detect_ray_r)
            direction = "right"
        self.request_state = None
        if ledge_move_collision is not None:
            self.ledge_grab_can_move = True
            self.setCurrentAnimsPlayRate(1.0)
            if direction == "left":
                if self.state != self.STATE_LEDGE_GRAB_LEFT:
                    self.request_state = self.STATE_LEDGE_GRAB_LEFT
            elif direction == "right":
                if self.state != self.STATE_LEDGE_GRAB_RIGHT:
                    self.request_state = self.STATE_LEDGE_GRAB_RIGHT
        elif self.state != self.STATE_LEDGE_GRAB:
            self.request_state = self.STATE_LEDGE_GRAB

        if char_front_collision_entry is not None \
        and self.hasSurfaceNormal(char_front_collision_entry):
            wall_normal = self.getSurfaceNormal(char_front_collision_entry, render)

            # set the characters heading
            zx = math.atan2(wall_normal.getZ(), wall_normal.getX())*180/math.pi
            zy = math.atan2(wall_normal.getZ(), wall_normal.getY())*180/math.pi
            zx = abs(zx-90)
            zy = abs(zy-90)
            # face towards the wall
            h = math.atan2(-wall_normal.getX(), wall_normal.getY())*180/math.pi
            self.updatePlayerHpr((h, 0, 0))
    elif self.state in self.ledge_grab_states \
    and ledge_collision is not None:
        # stay in ledge grab mode
        self.isAirborn = True
        self.rotation = None
        self.toggleFlyMode(True)
        if self.INTEL_ACTION_WALL_RUN in self.intel_action:
            self.intel_action.remove(self.INTEL_ACTION_WALL_RUN)
        self.intel_action.append(self.INTEL_ACTION_LEDGE_GRAB)
        if self.state != self.STATE_LEDGE_GRAB:
            self.request_state = self.STATE_LEDGE_GRAB
        else:
            self.request_state = None

        if char_front_collision_entry is not None \
        and self.hasSurfaceNormal(char_front_collision_entry):
            wall_normal = self.getSurfaceNormal(char_front_collision_entry, render)

            # set the characters heading
            zx = math.atan2(wall_normal.getZ(), wall_normal.getX())*180/math.pi
            zy = math.atan2(wall_normal.getZ(), wall_normal.getY())*180/math.pi
            zx = abs(zx-90)
            zy = abs(zy-90)
            # face towards the wall
            h = math.atan2(-wall_normal.getX(), wall_normal.getY())*180/math.pi
            if self.mainNode.getH() > h+25.0 or self.mainNode.getH() < h-25.0:
                self.updatePlayerHpr((h, 0, 0))

        if char_front_collision is not None:
            # make sure we're always as close to the wall as possible
            posA = NodePath("WALL-COL-TEMP")
            posA.setPos(char_front_collision)
            posB = NodePath("CHAR-TEMP")
            posB.setPos(self.mainNode.getPos())
            diff = posA.getPos() - posB.getPos()
            posA.removeNode()
            posB.removeNode()
            newPos = (0, -diff.length() + self.player_radius + 0.2, 0)
            self.updatePlayerPosFix(newPos, self.mainNode)
    elif ledge_collision is not None \
    and self.do_intel_action \
    and self.state != self.STATE_LEDGE_GRAB \
    and self.state in self.ledge_grab_possible_states:
        # initiate a ledge grab if certain conditions are met
        ledge_normal = None
        if self.hasSurfaceNormal(ledge_collision):
            ledge_normal = self.getSurfaceNormal(ledge_collision, render)
        if ledge_normal is not None:
            if ledge_normal.getZ() > 0:
                self.isAirborn = True
                self.rotation = None
                self.toggleFlyMode(True)
                if self.INTEL_ACTION_WALL_RUN in self.intel_action:
                    self.intel_action.remove(self.INTEL_ACTION_WALL_RUN)
                self.intel_action.append(self.INTEL_ACTION_LEDGE_GRAB)

                z = Point3()
                if self.hasSurfacePoint(ledge_collision):
                    z = self.getSurfacePoint(ledge_collision, render).getZ()
                elif self.hasContactPos(ledge_collision):
                    z = self.getContactPos(ledge_collision, render).getZ()

                newPos = char_front_collision
                if newPos is None:
                    newPos = self.getSurfacePoint(ledge_collision, render)
                if newPos is not None:
                    newPos.setZ(z - self.ledge_z_pos + self.getBaseZOffset())
                    self.updatePlayerPosFix(newPos)

                self.updatePlayerPosFix(self.player_radius+0.01, self.mainNode)
                if self.state != self.STATE_LEDGE_GRAB:
                    self.request_state = self.STATE_LEDGE_GRAB
                else:
                    self.request_state = None

def climbMoveRestriction(self):
    if self.INTEL_ACTION_CLIMB in self.intel_action \
    and self.climb_can_move \
    and self.state != self.STATE_LEDGE_GRAB_UP:
        # in ledge grab mode we can only move left and right but not
        # rotate the player
        climb_speed = self.ledge_grab_sidward_move_speed
        if self.do_move_left:
            self.update_speed.setX(climb_speed * self.dt)
        elif self.do_move_right:
            self.update_speed.setX(-climb_speed * self.dt)
