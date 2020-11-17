#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# PYTHON IMPORTS
#
import math
import sys

#
# PANDA3D ENGINE IMPORTS
#
from panda3d.core import Vec3, Point3

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


#
# MOVE FUNCTIONS
#
class Mover:
    """This is the main mover class.

    It is responsible for handling player input and acting according to
    the input.
    This class handles anything that isn't physics and collision related
    but glues together most of those other classes and is responsible for
    requesting most of the animation states and calling the physics
    update methods"""

    def __init__(self):
        # the actual accleration the character is at
        self.current_accleration = 0.0
        self.current_max_accleration = 0.0
        self.was_jumping = False
        self.fall_time = 0.0
        self.last_platform_position = None
        self.last_platform_rotation = None
        self.update_speed = Point3()
        self.plugin_setMoveDirection(Vec3(0, 0, 0))
        self.cur_jump_press_time = 0.0
        # amount of stamina the player has left
        self.stamina = self.getConfig("max_stamina")
        self.stamina_was_empty = False

        self.jump_direction = Vec3(0, 0, 0)

    def startControl(self):
        """Start the control module"""
        taskMgr.add(self.move, "task_movement", priority=-15)

    def stopControl(self):
        """Stops the controller class"""
        taskMgr.remove("task_movement")

    def pauseControl(self):
        """Stops the controls from being usable by the gamer"""
        self.stopControl()
        if self.state in self.on_ground_states:
            self.current_accleration = 0.0
            self.current_max_accleration = 0.0

    def resetAfterJump(self):
        self.is_airborn = False
        self.fall_time = 0.0
        self.cur_jump_press_time = 0.0
        self.is_first_jump = True
        if self.state in self.on_ground_states:
            self.land()
        if self.was_jumping:
            self.was_jumping = False
            if self.move_key_pressed:
                self.current_accleration = self.pre_jump_accleration * self.getConfig("jump_accleration_multiplier")
            else:
                self.current_accleration = 0.0
        self.setConfig("jump_strength", self.getConfig("jump_strength_default"))
        self.jump_direction = Vec3(0, 0, 0)

    def move(self, task):
        """The main task for updating the players position according
        to the keys pressed by the user"""
        if self.state in self.ignore_input_states:
            return task.cont

        # make sure the collisions are up to date
        self.updatePhysics()

        # reset some variables which should be fresh with every frame
        self.dt = globalClock.getDt()
        self.current_max_accleration = self.getConfig("max_accleration_run")
        self.rotation = None
        self.is_moving = self.current_accleration > 0
        self.is_airborn = False
        self.update_speed = Point3()
        self.plugin_setMoveDirection(Vec3(0, 0, 0))
        # this variables can be used to determine if the input device
        # specific input is given for the specific action

        self.plugin_requestNewState(None)

        self.do_sprint = False
        self.do_walk = False
        self.do_center_cam = False
        self.do_jump = False
        self.do_intel_action = False
        self.do_pull_up = False
        for plugin in self.inputPlugins:
            if plugin.active:
                plugin.centerGamepadAxes()
                self.do_sprint = self.do_sprint or plugin.getSprintState()
                self.do_walk = self.do_walk or plugin.getWalkState()
                self.do_center_cam = self.do_center_cam or plugin.getCenterCamState()
                self.do_jump = self.do_jump or plugin.getJumpState()
                self.do_intel_action = self.do_intel_action or plugin.getIntelActionState()
                self.do_pull_up = self.do_pull_up or plugin.getAction1State()

        #
        # CHECK IF PLAYER IS STILL AIRBORN
        #
        if self.state not in self.on_ground_states \
        and self.state not in self.flying_states:
            # We are not on the ground and hence can't move
            self.is_airborn = True
            if self.state in self.jump_and_fall_states:
                self.fall_time += self.dt
            # check if the player let go the jump key or the max jump
            # time has been reached
            if self.fall_time > self.getConfig("start_fall_time") \
            and self.state != self.STATE_FALL \
            and self.cur_jump_press_time > self.getConfig("max_jump_press_time"):
                self.plugin_requestNewState(self.STATE_FALL)
            self.cur_jump_press_time += self.dt
        else:
            # we probably landed somewhere
            self.resetAfterJump()

        #
        # PLAYER MOVEMENT
        #
        self.calcMoveDirection()

        if self.was_jumping:
            # make sure the character is forced to jump for at least
            # a given minimum of jump time
            self.do_jump = self.do_jump or self.cur_jump_press_time <= self.getConfig("min_jump_press_time")

        # check if any key to move the character has been pressed.
        # Do this by checking if the movement Vec has been set.
        self.move_key_pressed = self.plugin_getMoveDirection() != Vec3()

        #
        # Stamina check
        #
        self.can_use_sprint = self.stamina > 0
        if self.stamina_was_empty and self.stamina <= self.getConfig("min_stamina"):
            self.can_use_sprint = False

        if self.is_airborn:
            if self.current_accleration > 0:
                # we are in the air, so deacclerate
                self.current_accleration -= (self.getConfig("deaccleration") * self.getConfig("jump_airborn_deaccleration_multiplier")) * self.dt
                if self.current_accleration < 0:
                    self.current_accleration = 0
                # calculate the players heading
            if not self.do_center_cam \
            and self.move_key_pressed \
            and not self.getConfig("first_pserson_mode"):
                angle = math.atan2(self.plugin_getMoveDirection().getX(), self.plugin_getMoveDirection().getY())
                self.rotation = angle * (180.0 / math.pi)
        elif self.move_key_pressed:
            self.is_moving = True
            if not self.do_center_cam \
            and not self.getConfig("first_pserson_mode"):
                # calculate the players heading
                angle = math.atan2(self.plugin_getMoveDirection().getX(), self.plugin_getMoveDirection().getY())
                self.rotation = angle * (180.0 / math.pi)

            # set the players accleration
            if self.do_sprint and self.can_use_sprint:
                # sprint
                accleration = self.getConfig("accleration_sprint")
                self.current_max_accleration = self.getConfig("max_accleration_sprint")
            elif self.do_walk:
                # walk
                # set accleration
                accleration = self.getConfig("accleration_walk")
                self.current_max_accleration = self.getConfig("max_accleration_walk")
            else:
                # run
                accleration = self.getConfig("accleration_run")
            accleration *= self.plugin_getMoveDirection().length()
            # acclerate until we reached the maximum speed
            if self.current_accleration < self.current_max_accleration:
                self.current_accleration += accleration * self.dt
                if self.current_accleration > self.current_max_accleration:
                    self.current_accleration = self.current_max_accleration
            elif self.current_accleration > self.current_max_accleration:
                self.current_accleration -= self.getConfig("deaccleration") * self.dt
                if self.current_accleration < self.current_max_accleration:
                    self.current_accleration = self.current_max_accleration
        elif self.current_accleration > 0:
            # Use a "move to idle" animation
            if self.state == self.STATE_WALK:
                self.plugin_requestNewState(self.STATE_WALK_TO_IDLE)
            elif self.state == self.STATE_RUN:
                self.plugin_requestNewState(self.STATE_RUN_TO_IDLE)
            elif self.state == self.STATE_SPRINT:
                self.plugin_requestNewState(self.STATE_SPRINT_TO_IDLE)
            # deacclerate until we stopped completely again
            self.current_accleration -= self.getConfig("deaccleration") * self.dt
            if self.current_accleration < 0:
                self.current_accleration = 0

        #
        # PLAYER STATES
        #
        if self.is_airborn:
            pass
        elif self.do_sprint and self.can_use_sprint and self.move_key_pressed and self.is_moving:
            # SPRINTING
            # set animation
            if self.state == self.STATE_IDLE:
                self.plugin_requestNewState(self.STATE_IDLE_TO_SPRINT)
            elif self.state == self.STATE_RUN:
                self.plugin_requestNewState(self.STATE_RUN_TO_SPRINT)
            elif self.state == self.STATE_RUN_TO_IDLE:
                self.plugin_requestNewState(self.STATE_RUN_TO_SPRINT)
            elif self.state == self.STATE_SPRINT_TO_IDLE:
                self.plugin_requestNewState(self.STATE_SPRINT)
            elif self.state == self.STATE_WALK_TO_IDLE or self.state == self.STATE_WALK:
                self.plugin_requestNewState(self.STATE_WALK_TO_RUN)
        elif self.do_walk and self.move_key_pressed and self.is_moving:
            # WALKING
            # set animation
            if self.state == self.STATE_IDLE:
                self.plugin_requestNewState(self.STATE_IDLE_TO_WALK)
            elif self.state == self.STATE_RUN:
                self.plugin_requestNewState(self.STATE_RUN_TO_WALK)
            elif self.state == self.STATE_WALK_TO_IDLE:
                self.plugin_requestNewState(self.STATE_WALK)
            elif self.state == self.STATE_RUN_TO_IDLE:
                self.plugin_requestNewState(self.STATE_WALK)
            elif self.state == self.STATE_SPRINT or self.state == self.STATE_SPRINT_TO_IDLE:
                self.plugin_requestNewState(self.STATE_SPRINT_TO_RUN)
        elif self.is_moving and self.move_key_pressed:
            # RUNNING
            # no modifier key pressed, so simply run
            # set animation
            if self.state == self.STATE_IDLE:
                self.plugin_requestNewState(self.STATE_IDLE_TO_RUN)
            elif self.state == self.STATE_WALK:
                self.plugin_requestNewState(self.STATE_WALK_TO_RUN)
            elif self.state == self.STATE_WALK_TO_IDLE:
                self.plugin_requestNewState(self.STATE_RUN)
            elif self.state == self.STATE_RUN_TO_IDLE:
                self.plugin_requestNewState(self.STATE_RUN)
            elif self.state == self.STATE_SPRINT:
                self.plugin_requestNewState(self.STATE_SPRINT_TO_RUN)

        if self.is_airborn:
            pass
        elif self.current_accleration <= 0:
            # Make sure we change to an idle animation if we don't move
            if self.state == self.STATE_WALK:
                self.plugin_requestNewState(self.STATE_WALK_TO_IDLE)
            elif self.state == self.STATE_RUN:
                self.plugin_requestNewState(self.STATE_RUN_TO_IDLE)
            elif self.state == self.STATE_SPRINT:
                self.plugin_requestNewState(self.STATE_SPRINT_TO_IDLE)
            elif self.state != self.STATE_IDLE and self.state != self.STATE_LAND:
                self.plugin_requestNewState(self.STATE_IDLE)
        else:
            # set the speed of the currently playing animation to fit
            # the characters current movement speed
            self.setCurrentAnimsPlayRate(self.current_accleration/self.current_max_accleration)

        #
        # CALL ALL PLUGINS HERE
        #
        skip = False
        for key in sorted(self.controlPlugins):
            plugins = self.controlPlugins[key]
            for plugin in plugins:
                if plugin.active:
                    if plugin.action(self.do_intel_action):
                        skip = True
                        break
            if skip:
                break

        #
        # PLAYER POSITION UPDATE
        #

        #
        # CALCULATE PLATFORM SPEED
        #
        platform_speed = Vec3(0,0,0)
        platform_rotation = 0.0
        if self.getActivePlatform() is not None:
            platformPositionAbsolute = self.getActivePlatform().getPos()
            # Character on moving platform
            if self.last_platform_position is None:
                self.last_platform_position = platformPositionAbsolute
            platform_speed = platformPositionAbsolute - self.last_platform_position
            self.last_platform_position = platformPositionAbsolute

            if self.getConfig("respect_platform_rotation"):
                if self.last_platform_rotation is None:
                    self.last_platform_rotation = self.getActivePlatform().getH()
                platform_rotation = self.getActivePlatform().getH() - self.last_platform_rotation
                self.last_platform_rotation = self.getActivePlatform().getH()

        #
        # INITIATE JUMPING
        #
        if self.do_jump \
        and self.getConfig("jump_enabled") \
        and self.fall_time <= self.getConfig("jump_allow_after_fall_time"): #\
            if self.STATE_JUMP in self.defaultTransitions[self.state]:
                self.was_jumping = True
                self.is_airborn = True
                self.pre_jump_state = self.state
                self.pre_jump_accleration = self.current_accleration
                self.plugin_requestNewState(self.STATE_JUMP)
                self.cur_jump_press_time += self.dt
            if self.cur_jump_press_time <= self.getConfig("max_jump_press_time"):
                forward_speed = self.getConfig("speed") * self.current_accleration
                if self.is_first_jump == False:
                    # As we set the power of the forward force the first
                    # time and shouldn't speed up in mid air, we set the
                    # forward speed to 0
                    forward_speed = 0.0
                else:
                    # make sure the first jump is not affected by previous
                    # physical forces
                    self.land()
                self.is_first_jump = False
                if self.getConfig("platform_movement_affects_jump"):
                    #TODO: Check if we need to store the platform speed separately. We might reset the platform speed
                    #      every frame currently.
                    self.doJump(forward_speed, self.jump_direction, platform_speed / self.dt)
                else:
                    # Why did I had to put this here? self.land kinda breaks jump functionality
                    #self.land()
                    self.doJump(forward_speed, self.jump_direction)

        #
        # CALCULATE MOVEMENT SPEED
        #
        if self.is_airborn and self.state not in self.flying_states:
            # character is jumping/falling/flying
            if self.move_key_pressed:
                # move the player while he's airborn. As the current_acceleration
                # can be 0, we check which speed is higher and move the player accordingly
                self.current_speed = max(
                    self.getConfig("speed_airborn") * self.dt,
                    self.getConfig("speed") * self.current_accleration * self.dt)
                self.update_speed = Point3(0, -self.current_speed, 0)
            else:
                # No movement key was pressed, so move the player according
                # to previous speed
                self.current_speed = self.getConfig("speed") * self.current_accleration * self.dt
                self.update_speed = Point3(0, -self.current_speed, 0)
        elif self.state not in self.flying_states:
            # normal walking/running
            self.current_speed = self.getConfig("speed") * self.current_accleration * self.dt
            self.update_speed = Point3(0, -self.current_speed, 0)
        elif self.state in self.flying_states:
            self.current_speed = Point3()
            self.update_speed = Point3()
            self.current_accleration = 0.0
        if self.getConfig("first_pserson_mode"):
            # as we don't rotate the character in first person mode, move
            # him in the direction of the movement vector
            self.update_speed = self.plugin_getMoveDirection() * self.update_speed.getY()

        # check if we actually use stamina
        # 1. Player must be in a sprint state
        use_stamina = self.state in self.sprint_states
        # 2. Player must not be in the air/hanging/flying/...
        use_stamina = use_stamina and not self.is_airborn
        # 3. Player must be sprinting
        use_stamina = use_stamina and self.do_sprint
        # 4. Player must be able to use sprint
        use_stamina = use_stamina and self.can_use_sprint
        # 5. Player must be moving
        use_stamina = use_stamina and self.is_moving

        for key in sorted(self.controlPlugins):
            plugins = self.controlPlugins[key]
            for plugin in plugins:
                if plugin.active:
                    use_stamina = use_stamina or plugin.useStamina()

        if use_stamina:
            self.stamina -= self.getConfig("stamina_usage_per_second") * self.dt
            if self.stamina <= 0:
                self.stamina_was_empty = True
        elif self.stamina < self.getConfig("max_stamina"):
            regain_stamina = self.dt * self.getConfig("stamina_recover_per_second_run")
            if self.state in self.walk_states:
                regain_stamina = self.dt * self.getConfig("stamina_recover_per_second_walk")
            elif self.state is self.STATE_IDLE or self.STATE_FALL:
                regain_stamina = self.dt * self.getConfig("stamina_recover_per_second_idle")

            self.stamina += regain_stamina
            if self.stamina > self.getConfig("max_stamina"):
                self.stamina = self.getConfig("max_stamina")
            if self.stamina >= self.getConfig("min_stamina"):
                self.stamina_was_empty = False

        #
        # CHECK FOR PLUGINS MOVEMENT RESTRICTIONS
        #
        skip = False
        for key in sorted(self.controlPlugins):
            plugins = self.controlPlugins[key]
            for plugin in plugins:
                if plugin.active:
                    if plugin.moveRestriction():
                        skip = True
                        break
            if skip:
                break

        #
        # UPDATE IN THE PHYSICS CLASS
        #
        self.updatePlayerPos(self.update_speed, self.rotation)

        #
        # MOVE PLAYER WITH MOVING PLATFORM
        #
        # respect moving platforms
        if self.getActivePlatform() is not None and not self.state in self.jump_and_fall_states:
            # now update the player position according to the platform
            if self.state in self.flying_states:
                self.updatePlayerPosFloating(platform_speed)
            else:
                self.updatePlayerPosFloatingFlyign(platform_speed)

            # check for the platforms self.rotation
            if self.getConfig("respect_platform_rotation"):
                self.updatePlayerHprFloating(platform_rotation, self.getActivePlatform())
        else:
            self.last_platform_position = None
            self.last_platform_rotation = None

        #
        # REQUEST THE NEW FSM STATE
        #
        self.enterNewState()

        return task.cont
