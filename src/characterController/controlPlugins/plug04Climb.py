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
from panda3d.core import Point3F, NodePath

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

        self.request_idle = False

        self.respect_steps = False

        self.can_move_vertical = False
        self.can_move_horizontal = False

        # climb directions
        self.left = False
        self.right = False
        self.up = False
        self.down = False

        self.climb_area_entry_top = None
        self.climb_area_entry = None

        #
        # SETUP STATES
        #
        # a list of all climb states
        self.climb_states = [
            self.STATE_CLIMB,
            self.STATE_CLIMB_EXIT_UP,
            self.STATE_CLIMB_VERT,
            self.STATE_CLIMB_HOR,
            self.STATE_CLIMB_DIAG_UL_BR,
            self.STATE_CLIMB_DIAG_BL_UR,
            ]

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
            self.STATE_CLIMB_EXIT_UP,
            ["*"],
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
        # map enter functions
        self.core.enterClimb = self.enterClimb
        self.core.enterClimbExitUp = self.enterClimbExitUp
        self.core.enterClimbVertical = self.enterClimbVertical
        self.core.enterClimbHorizontal = self.enterClimbHorizontal
        self.core.enterClimbDiagonal_ul_br = self.enterClimbDiagonal_ul_br
        self.core.enterClimbDiagonal_bl_ur = self.enterClimbDiagonal_bl_ur

        # map exit functions
        self.core.exitClimb = self.exitClimb

        #
        # LOAD ANIMATIONS
        #
        #TODO: make animations
        self.updateAnimations(self.core.plugin_isFirstPersonMode())

        #
        # SETUP COLLISION DETECTION
        #
        self.accept("plugin-character-in-collision", self.check_climbing)
        self.accept("plugin-character-out-collision", self.check_climbing)

        # Ray check center to get the climbable entry
        point_a = (0,0,0)
        point_b = (0, -self.core.getConfig("climb_forward_check_dist"), 0)
        self.center_ray = "climb_center_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.center_ray, point_a, point_b)

        # set up collision rays to check if the player would leave the climbable area
        # Ray check above the character
        point_a = (0,0,self.core.getConfig("player_height"))
        point_b = (0, -self.core.getConfig("climb_forward_check_dist"), self.core.getConfig("player_height"))
        self.top_ray = "climb_top_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.top_ray, point_a, point_b)

        # Add a ray checking where the player will stand after climbing up
        point_a = (0, -self.core.getConfig("climb_forward_exit_up_dist"), self.core.getConfig("climb_top_check_dist"))
        point_b = (0, -self.core.getConfig("climb_forward_exit_up_dist"), self.core.getConfig("climb_bottom_check_dist"))
        self.climb_exit_up_pos_ray = "ledge_grab_ledge_pull_up_pos_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.climb_exit_up_pos_ray, point_a, point_b)

        # Ray check below the character
        point_a = (0,0,0)
        point_b = (0, -self.core.getConfig("climb_forward_check_dist"), 0)
        self.bottom_ray = "climb_bottom_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.bottom_ray, point_a, point_b)

        # Ray check left to the character
        point_a = (self.core.getConfig("player_radius"),0,self.core.getConfig("player_height")/2.0)
        point_b = (self.core.getConfig("player_radius"), -self.core.getConfig("climb_forward_check_dist"), self.core.getConfig("player_height")/2.0)
        self.left_ray = "climb_left_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.left_ray, point_a, point_b)

        # Ray check right the character
        point_a = (-self.core.getConfig("player_radius"),0,self.core.getConfig("player_height")/2.0)
        point_b = (-self.core.getConfig("player_radius"), -self.core.getConfig("climb_forward_check_dist"), self.core.getConfig("player_height")/2.0)
        self.right_ray = "climb_right_ray-{}".format(self.pluginID)
        self.core.plugin_registerCharacterRayCheck(self.right_ray, point_a, point_b)

        #
        # ACTIVATE PLUGIN
        #
        self.active = True

    def updateAnimations(self, firstPersonMode):
        if firstPersonMode:
            self.core.loadAnims({
                self.ANIM_IDLE: self.core.getConfig("anim_climb_fp"),
                self.ANIM_UP: self.core.getConfig("anim_climb_up_fp"),
                self.ANIM_DOWN: self.core.getConfig("anim_climb_down_fp"),
                self.ANIM_LEFT: self.core.getConfig("anim_climb_left_fp"),
                self.ANIM_RIGHT: self.core.getConfig("anim_climb_right_fp"),
                self.ANIM_UP_LEFT: self.core.getConfig("anim_climb_left_up_fp"),
                self.ANIM_DOWN_LEFT: self.core.getConfig("anim_climb_left_down_fp"),
                self.ANIM_UP_RIGHT: self.core.getConfig("anim_climb_right_up_fp"),
                self.ANIM_DOWN_RIGHT: self.core.getConfig("anim_climb_right_down_fp"),
                self.ANIM_EXIT_UP: self.core.getConfig("anim_climb_exit_up_fp"),})
        else:
            self.core.loadAnims({
                self.ANIM_IDLE: self.core.getConfig("anim_climb"),
                self.ANIM_UP: self.core.getConfig("anim_climb_up"),
                self.ANIM_DOWN: self.core.getConfig("anim_climb_down"),
                self.ANIM_LEFT: self.core.getConfig("anim_climb_left"),
                self.ANIM_RIGHT: self.core.getConfig("anim_climb_right"),
                self.ANIM_UP_LEFT: self.core.getConfig("anim_climb_left_up"),
                self.ANIM_DOWN_LEFT: self.core.getConfig("anim_climb_left_down"),
                self.ANIM_UP_RIGHT: self.core.getConfig("anim_climb_right_up"),
                self.ANIM_DOWN_RIGHT: self.core.getConfig("anim_climb_right_down"),
                self.ANIM_EXIT_UP: self.core.getConfig("anim_climb_exit_up"),})
        # "preload" all animations of the character
        self.core.bindAllAnims()

    def action(self, intel_action):
        # check if we want to request to transition to the idle animation
        if self.request_idle:
            # check for the climb exit up animation state
            ac = self.core.getAnimControl(self.ANIM_EXIT_UP)
            if ac.isPlaying():
                # as long as it's playing we won't transition anywhere
                # and do as we're still in normal ledge grab mode
                self.core.plugin_requestNewState(None)
                return True
            else:
                # the climb up is done, now we can transit to the idle
                # state to continue with normal execution of the character
                # controller
                self.core.plugin_requestNewState(self.core.STATE_IDLE)
                self.request_idle = False
                return False

        # check if there is a climbable area in front of us. Use the
        # center ray for this check
        entry = self.core.getFirstCollisionEntryInLine(self.center_ray)
        if entry is not None:
            self.check_climbing(entry)
        else:
            # let go from climb object
            self.stopClimb()
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
            self.stopClimb()
            self.core.toggleFlyMode(False)
            return False

        self.do_climb = True

        self.faceWall(self.climb_area_entry)
        self.attachToWall(self.climb_area_entry)
        self.setInitialPosition(self.climb_area_entry)
        self.core.rotation = None
        self.core.toggleFlyMode(True)

        #
        # CLIMB LOGIC
        #

        # left, right, up, down
        self.left = self.right = self.up = self.down = False

        direction = self.core.plugin_getMoveDirection()

        if direction is not None:
            #
            # CLIMB MOVE ANY DIRECTION
            #
            self.core.plugin_requestNewState(None)
            if self.can_move_horizontal:
                #
                # MOVE HORIZONTAL
                #
                if direction.getX() < -0.3:
                    #
                    # CHECK CLIMB LEFT
                    #
                    # do we have a collision entry to the left of us
                    entry_left = self.core.getFirstCollisionEntryInLine(self.left_ray)
                    if entry_left is not None \
                    and "climbable" in entry_left.getIntoNodePath().getNetTag("Type").lower():
                        self.left = True
                if direction.getX() > 0.3:
                    #
                    # CHECK CLIMB RIGHT
                    #
                    # do we have a collision entry to the right of us
                    entry_right = self.core.getFirstCollisionEntryInLine(self.right_ray)
                    if entry_right is not None \
                    and "climbable" in entry_right.getIntoNodePath().getNetTag("Type").lower():
                        self.right = True

            request_climb_exit_up = False
            if self.can_move_vertical:
                #
                # MOVE VERTICAL
                #
                fp_mult = 1
                if self.core.plugin_isFirstPersonMode():
                    fp_mult = -1

                if direction.getY()*fp_mult < -0.3:
                    #
                    # CHECK CLIMB UP
                    #
                    entry_top = self.core.getFirstCollisionEntryInLine(self.top_ray)
                    if entry_top is not None \
                    and "climbable" in entry_top.getIntoNodePath().getNetTag("Type").lower():
                        self.up = True
                    elif entry_top is None:
                        climb_exit_up_collision = self.core.getFirstCollisionEntryInLine(self.climb_exit_up_pos_ray)
                        if climb_exit_up_collision is not None:
                            #
                            # EXIT CLIMB UP
                            #
                            # first get the position where the player should be standing
                            # in the end
                            pos = None
                            if self.core.hasSurfacePoint(climb_exit_up_collision):
                                pos = self.core.getSurfacePoint(climb_exit_up_collision, render)
                            elif self.core.hasContactPos(climb_exit_up_collision):
                                pos = self.core.getContactPos(climb_exit_up_collision, render)

                            self.core.clearFirstCollisionEntryOfRay(self.climb_exit_up_pos_ray)

                            # check weather the player would actually have enough
                            # space to stand there and only continue if so
                            has_enough_space = self.core.checkFutureCharSpace(pos)
                            if pos is not None and has_enough_space:
                                # we want to climb out on the top end of the
                                # area
                                request_climb_exit_up = True
                                pos.setZ(pos.getZ() + 0.05)
                                self.core.updatePlayerPosFix(pos)
                if direction.getY()*fp_mult > 0.3:
                    #
                    # CHECK CLIMB DOWN
                    #
                    entry_bottom = self.core.getFirstCollisionEntryInLine(self.bottom_ray)
                    if entry_bottom is not None \
                    and "climbable" in entry_bottom.getIntoNodePath().getNetTag("Type").lower():
                        self.down = True

            # check which direction we are moving
            if request_climb_exit_up:
                self.core.plugin_requestNewState(self.STATE_CLIMB_EXIT_UP)
            elif (self.left or self.right) and not (self.up or self.down):
                self.core.plugin_requestNewState(self.STATE_CLIMB_VERT)
            elif not (self.left or self.right) and (self.up or self.down):
                self.core.plugin_requestNewState(self.STATE_CLIMB_HOR)
            elif (self.left and self.up) or (self.right and self.down):
                self.core.plugin_requestNewState(self.STATE_CLIMB_DIAG_UL_BR)
            elif (self.left and self.down) or (self.right and self.up):
                self.core.plugin_requestNewState(self.STATE_CLIMB_DIAG_BL_UR)
            elif self.core.state != self.STATE_CLIMB:
                self.core.plugin_requestNewState(self.STATE_CLIMB)
            if (self.core.do_sprint and self.core.can_use_sprint) and self.core.state is not self.STATE_CLIMB and not request_climb_exit_up:
                self.core.plugin_setCurrentAnimationPlayRate(self.core.getConfig("climb_sprint_multiplier"))
            else:
                self.core.plugin_setCurrentAnimationPlayRate(1.0)
        else:
            #
            # CLIMB IDLING
            #
            if self.core.state != self.STATE_CLIMB:
                self.core.plugin_requestNewState(self.STATE_CLIMB)
            else:
                self.core.plugin_requestNewState(None)

        if self.respect_steps:
            self.snapToStepps(entry)

        # skip plugins following this one
        return True

    def stopClimb(self):
        self.do_climb = False
        self.can_climb = False
        self.climb_area_entry = None
        if self.core.state in self.climb_states:
            self.core.plugin_requestNewState(self.core.STATE_FALL)

    def useStamina(self):
        # this plugin doesn't use stamina
        return self.core.do_sprint and self.core.can_use_sprint

    def moveRestriction(self):
        if self.do_climb:
            # in climb mode we can, if at all, only move left and right
            # but not rotate the player
            climb_speed = self.core.getConfig("climb_sidward_move_speed")
            if self.core.do_sprint and self.core.can_use_sprint:
                climb_speed *= self.core.getConfig("climb_sprint_multiplier")
            if self.left:
                self.core.update_speed.setX(climb_speed * self.core.dt)
            elif self.right:
                self.core.update_speed.setX(-climb_speed * self.core.dt)

            climb_speed = self.core.getConfig("climb_vertical_move_speed")
            if self.core.do_sprint and self.core.can_use_sprint:
                climb_speed *= self.core.getConfig("climb_sprint_multiplier")
            if self.up:
                self.core.update_speed.setZ(climb_speed * self.core.dt)
            elif self.down:
                self.core.update_speed.setZ(-climb_speed * self.core.dt)

            self.core.update_speed.setY(0)
        return self.do_climb

    #
    # CLIMB HELPER FUNCTIONS
    #
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
        elif self.core.state in self.climb_states:
            self.stopClimb()

    def faceWall(self, entry):
        """This function will rotate the player to face towards the
        face normal of the given collision entry"""
        if entry is not None \
        and self.core.hasSurfaceNormal(entry):
            entry_normal = self.core.getSurfaceNormal(entry, render)

            # face towards the wall
            h = math.atan2(-entry_normal.getX(), entry_normal.getY())*180/math.pi

            # Fit the players pitch to the skew of the area
            #TODO: This doesn't really work yet.
            #if self.climb_area_entry_top is not None\
            #and self.core.hasSurfaceNormal(self.climb_area_entry_top):
            #    top_entry_normal = self.core.getSurfaceNormal(self.climb_area_entry_top, render)
            #    entry_normal = top_entry_normal
            #p = math.atan2(-entry_normal.getX(), entry_normal.getZ())*180/math.pi
            #p -= 90
            #p = -p

            #p = 0

            if self.core.main_node.getH() != h:
                #self.core.updatePlayerHpr((h, p, 0))
                self.core.updatePlayerHpr((h, 0, 0))
            # invalidate other self.core.rotational movements that were set before
            self.core.rotation = None

    def setInitialPosition(self, entry):
        if self.core.state in self.climb_states: return
        self.snapToStepps(entry)

    def snapToStepps(self, entry):
        if entry is not None \
        and self.core.hasSurfacePoint(entry):
            entry_np = entry.getIntoNodePath()
            if "true" in entry_np.getNetTag("Stepped").lower():
                playerPoint = self.core.plugin_getPos()

                # check if we are closer to the next uper or lower position
                points = list(entry.getInto().getPoints())
                points.sort(key=lambda p:p.z)
                lowest = points[0].z
                highest = points[-1].z
                stepList = []
                curStepPos = lowest
                while(curStepPos < highest-self.core.getConfig("climb_step_height")):
                    curStepPos += self.core.getConfig("climb_step_height")
                    stepList.append(Point3F(playerPoint.x, playerPoint.y, curStepPos))
                stepList.sort(key=lambda p:(p - playerPoint).length_squared())
                self.core.updatePlayerPosFix(stepList[0])

    def attachToWall(self, entry):
        """This function will place the player at the position of the
        given collision entry"""
        if entry is not None \
        and self.core.hasSurfacePoint(entry):
            point = self.core.getSurfacePoint(entry, render)
            climbPos = NodePath("CLIMB-COL-TEMP")
            climbPos.setHpr(self.core.plugin_getHpr())
            if point is None and entry is not None:
                # This can happen if we hang on a concave ledge shape (e.g. Floating platforms)
                if self.core.hasSurfacePoint(entry):
                    climbPos.setPos(self.core.getSurfacePoint(entry, render))
                elif self.core.hasContactPos(entry):
                    climbPos.setPos(self.core.getContactPos(entry, render))
            elif point is not None:
                climbPos.setPos(point)
            else:
                # we have no positions to work with!
                return

            climbPos.setPos(climbPos, (self.core.plugin_getPos(climbPos).getX(), self.core.getConfig("player_radius") + 0.05, self.core.plugin_getPos(climbPos).getZ()))
            self.core.updatePlayerPosFix(climbPos.getPos())

    #
    # FSM EXTENSION
    #
    def enterClimb(self):
        self.core.current_animations = [self.ANIM_IDLE]
        self.core.loop(self.ANIM_IDLE)
        self.respect_steps = True

    def exitClimb(self):
        self.respect_steps = False

    def enterClimbExitUp(self):
        self.core.current_animations = [self.ANIM_EXIT_UP]
        if not self.core.getCurrentAnim() == self.ANIM_EXIT_UP:
            self.request_idle = True
            self.core.play(self.ANIM_EXIT_UP)

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
