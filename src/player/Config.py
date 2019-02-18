#!/usr/bin/python
# -*- coding: utf-8 -*-

from panda3d.core import KeyboardButton, MouseButton, ButtonHandle, Point3F, Vec3
from panda3d.core import InputDevice

from player.inputPlugins.inputMapping import InputMapping

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


# Deside which physics engine to use
# Panda3D internal engine
USEINTERNAL = True
# Bullet engine
USEBULLET = not USEINTERNAL

#
# PLAYER CONFIGURATIONS
#
class Config:
    """
    This class contains all the configurable variables of the player
    controller module.
    Most of the variables are set to represent a normal modern jump and
    run game feeling. Not to realistic but also not to floaty and should
    fit with characters created with measurements as 1 unit = 1 meter
    """
    def __init__(self):
        #
        # MODEL AND ANIMATION
        #
        # The players model file path
        self.basePath = "../data/actor/"
        self.model = self.basePath + "Fox"
        # Paths of the animation files
        self.anim_idle = self.basePath + "Fox-Idle"
        self.anim_walk = self.basePath + "Fox-Walk"
        self.anim_run = self.basePath + "Fox-Run"
        self.anim_sprint = self.basePath + "Fox-Sprint"
        self.anim_jumpstart = self.basePath + "Fox-Jump"
        self.anim_jumpland = self.basePath + "Fox-Landing"
        self.anim_falling = self.basePath + "Fox-Fall"
        self.anim_crouch_move = self.basePath + "Fox-Run"
        self.anim_crouch_idle = self.basePath + "Fox-Run"
        self.anim_crawl_move = self.basePath + "Fox-Run"
        self.anim_crawl_idle = self.basePath + "Fox-Run"
        self.anim_wallrun_left = self.basePath + "Fox-WallRun_Left"
        self.anim_wallrun_right = self.basePath + "Fox-WallRun_Right"
        self.anim_wallrun_up = self.basePath + "Fox-WallRun_Up"
        self.anim_roll = self.basePath + "Fox-Run"
        self.anim_ledge_grab = self.basePath + "Fox-LedgeGrab"
        self.anim_ledge_grab_up = self.basePath + "Fox-LedgeGrab_Up"
        self.anim_ledge_grab_left = self.basePath + "Fox-LedgeGrab_Left"
        self.anim_ledge_grab_right = self.basePath + "Fox-LedgeGrab_Right"
        self.anim_climb = self.basePath + "Fox-Climb_Idle"
        self.anim_climb_exit_up = self.basePath + "Fox-Climb_Exit_Up"
        self.anim_climb_up = self.basePath + "Fox-Climb_Up"
        self.anim_climb_down = self.basePath + "Fox-Climb_Down"
        self.anim_climb_left = self.basePath + "Fox-Climb_Left"
        self.anim_climb_right = self.basePath + "Fox-Climb_Right"
        self.anim_climb_left_up = self.basePath + "Fox-Climb_Up_Left"
        self.anim_climb_left_down = self.basePath + "Fox-Climb_Down_Left"
        self.anim_climb_right_up = self.basePath + "Fox-Climb_Up_Right"
        self.anim_climb_right_down = self.basePath + "Fox-Climb_Down_Right"

        # Paths of the animation files for first person mode
        self.anim_idle_fp = self.basePath + "Fox-Idle_fp"
        self.anim_walk_fp = self.basePath + "Fox-Walk_fp"
        self.anim_run_fp = self.basePath + "Fox-Run_fp"
        self.anim_sprint_fp = self.basePath + "Fox-Sprint_fp"
        self.anim_jumpstart_fp = self.basePath + "Fox-Jump_fp"
        self.anim_jumpland_fp = self.basePath + "Fox-Landing_fp"
        self.anim_falling_fp = self.basePath + "Fox-Fall_fp"
        self.anim_crouch_move_fp = self.basePath + "Fox-Run_fp"
        self.anim_crouch_idle_fp = self.basePath + "Fox-Run_fp"
        self.anim_crawl_move_fp = self.basePath + "Fox-Run_fp"
        self.anim_crawl_idle_fp = self.basePath + "Fox-Run_fp"
        self.anim_wallrun_left_fp = self.basePath + "Fox-WallRun_Left_fp"
        self.anim_wallrun_right_fp = self.basePath + "Fox-WallRun_Right_fp"
        self.anim_wallrun_up_fp = self.basePath + "Fox-WallRun_Up_fp"
        self.anim_roll_fp = self.basePath + "Fox-Run_fp"
        self.anim_ledge_grab_fp = self.basePath + "Fox-LedgeGrab_fp"
        self.anim_ledge_grab_up_fp = self.basePath + "Fox-LedgeGrab_Up_fp"
        self.anim_ledge_grab_left_fp = self.basePath + "Fox-LedgeGrab_Left_fp"
        self.anim_ledge_grab_right_fp = self.basePath + "Fox-LedgeGrab_Right_fp"
        self.anim_climb_fp = self.basePath + "Fox-Climb_Idle_fp"
        self.anim_climb_exit_up_fp = self.basePath + "Fox-Climb_Exit_Up_fp"
        self.anim_climb_up_fp = self.basePath + "Fox-Climb_Up_fp"
        self.anim_climb_down_fp = self.basePath + "Fox-Climb_Down_fp"
        self.anim_climb_left_fp = self.basePath + "Fox-Climb_Left"
        self.anim_climb_right_fp = self.basePath + "Fox-Climb_Right"
        self.anim_climb_left_up_fp = self.basePath + "Fox-Climb_Up_Left"
        self.anim_climb_left_down_fp = self.basePath + "Fox-Climb_Down_Left"
        self.anim_climb_right_up_fp = self.basePath + "Fox-Climb_Up_Right"
        self.anim_climb_right_down_fp = self.basePath + "Fox-Climb_Down_Right"

        # If the animations only consists of a few frames this should be enabled
        # NOTE: This should always be enabled to smoth the transition within
        #       animations. For example for the accleration of the character
        #       untill it reaches full pace. Otherwise you would get a kind
        #       of stop motion effect in the transitions.
        self.enable_interpolation = True
        # the time in seconds until the game automatically pauses if
        # only the idle animation is played
        self.idle_to_pause_time = 300.0 # 5 minutes should be good
        self.idle_to_pause_task_name = "pause-from-idle"
        self.idle_to_pause_event_name = "playerIdling"

        #
        # AUDIO
        #
        # the following events will be thrown when a sfx should be played or stopped respectively
        self.audio_play_walk_evt = "player-play-walk-sfx"
        self.audio_stop_walk_evt = "player-stop-walk-sfx"
        self.audio_play_run_evt = "player-play-run-sfx"
        self.audio_play_sprint_evt = "player-play-sprint-sfx"
        self.audio_play_jump_evt = "player-play-jump-sfx"
        self.audio_play_land_evt = "player-play-land-sfx"
        self.audio_play_fall_evt = "player-play-fall-sfx"
        self.audio_set_walk_playrate_evt = "player-set-playrate-walk-sfx"

        #
        # FX
        #
        # Use simple shadow will place a shadow image on the ground below the character
        self.use_simple_shadow = True
        self.simple_shadow_image = self.basePath + "Shadow.png"
        # the minimum size of the shadow
        self.min_shadow_scale = 0.15
        # the maximum size of the shadow
        self.max_shadow_scale = 0.5
        # the factor the shadow shrinks when it gets further away
        # NOTE: the higher the scale, the slower the shadow shrinks
        self.shadow_scale_factor = 5.0
        # distance from where on the shadow starts to shrink
        self.shadow_min_scale_dist = 1.0
        # offset of the shadow on the Z-Axis
        self.shadow_z_offset = 0.015

        #
        # CONTROLS
        #
        # append gamepad and other device mappings here
        self.deviceMaps = {
            "Keyboard and Mouse": InputMapping()
        }
        self.deviceMaps["Keyboard and Mouse"].setDefaultMappingKeyboardAndMouse()
        self.usedDevice = None
        self.selectedDevice = "Keyboard and Mouse"
        for device in base.devices.getDevices(InputDevice.DeviceClass.gamepad):
            if device.name == self.selectedDevice:
                self.usedDevice = device
        self.deadzone_x = 0.1
        self.deadzone_y = 0.1

        #
        # CAMERA CONTROL VARIABLES
        #
        # Camera basics
        self.first_pserson_mode = False
        # how close can the camera come until clipping
        self.cam_near_clip_default_firstperson = 0.005
        self.cam_near_clip_default_thirdperson = 0.5
        if self.first_pserson_mode:
            self.cam_near_clip = self.cam_near_clip_default_firstperson
        else:
            self.cam_near_clip = self.cam_near_clip_default_thirdperson
        # how far can the camera see until clipping
        self.cam_far_clip = 5000
        # camera field of view
        self.cam_fov_default_firstperson = 100
        self.cam_fov_default_thirdperson = 70
        if self.first_pserson_mode:
            self.cam_fov = self.cam_fov_default_firstperson
        else:
            self.cam_fov = self.cam_fov_default_thirdperson
        # Mouse camera movement
        # enables the camera control via the mouse
        self.enable_mouse = True
        # invert vertical camera movements when mouse is used
        self.mouse_invert_vertical = False
        self.mouse_invert_horizontal = False
        # invert vertical camera movements when keyboard is used
        self.keyboard_invert_vertical = True
        self.keyboard_invert_horizontal = False
        # screen sizes
        self.win_width_half = base.win.getXSize() // 2
        self.win_height_half = base.win.getYSize() // 2
        # mouse speed
        self.mouse_speed_x_default_firsrperson = 0.1
        self.mouse_speed_y_default_firsrperson = 0.1
        self.mouse_speed_x_default_thirdperson = 80.0
        self.mouse_speed_y_default_thirdperson = 40.0
        if self.first_pserson_mode:
            self.mouse_speed_x = self.mouse_speed_x_default_firsrperson
            self.mouse_speed_y = self.mouse_speed_y_default_firsrperson
        else:
            self.mouse_speed_x = self.mouse_speed_x_default_thirdperson
            self.mouse_speed_y = self.mouse_speed_y_default_thirdperson
        # keyboard speed
        self.keyboard_cam_speed_x_default_firsrperson = 160
        self.keyboard_cam_speed_y_default_firsrperson = 100
        self.keyboard_cam_speed_x_default_thirdperson = 8
        self.keyboard_cam_speed_y_default_thirdperson = 4
        if self.first_pserson_mode:
            self.keyboard_cam_speed_x = self.keyboard_cam_speed_x_default_firsrperson
            self.keyboard_cam_speed_y = self.keyboard_cam_speed_y_default_firsrperson
        else:
            self.keyboard_cam_speed_x = self.keyboard_cam_speed_x_default_thirdperson
            self.keyboard_cam_speed_y = self.keyboard_cam_speed_y_default_thirdperson
        # the next two vars will set the min and max distance the cam can have
        # to the node it is attached to
        self.max_cam_distance = 5.0 #8.0
        self.min_cam_distance = 2.0 #3.0
        # the initial cam distance
        self.cam_distance = (self.max_cam_distance - self.min_cam_distance) / 2.0 + self.min_cam_distance
        # the maximum distance on the Z-Axis to the player
        self.max_cam_height_distance = 4.0
        # the minimum distance on the Z-Axis to the player
        self.min_cam_height_distance = 0.25
        # the average camera height
        self.cam_height_avg = (self.max_cam_height_distance - self.min_cam_height_distance) / 2.0 + self.min_cam_height_distance
        self.cam_height_avg_up = self.cam_height_avg + 0.2
        self.cam_height_avg_down = self.cam_height_avg - 0.2
        # the initial cam height
        self.cam_height = self.cam_height_avg
        # the speed of the cameras justification movement towards
        # the average height
        self.cam_z_justification_speed = 1
        # a floater which hovers over the player and is used as a
        # look at position for the camera
        self.cam_floater_pos = Point3F(0, 0, 1.5)
        # this variable determines the duration in which the camera gets
        # repositioned to a new position which it will need after a
        # collision in the view space between the camera and player
        # occured. The duration is for distances at 1 unit and given in
        # seconds.
        self.cam_reposition_duration = 0.025

        #
        # PHYSICS AND COLLISIONS
        #
        # CHARACTER GENERAL
        # show collision solids
        self.show_collisions = False
        # The physical physic_world which will be responsible for collision checks and
        # physic updates
        # NOTE: This will first be set in the constructor of the controller
        self.physic_world = None
        # the name of the collision solids that surround the character
        self.char_collision_name = "CharacterCollisions"
        # the mass of the character
        # 181 lbs = average weight of a male human
        self.player_mass = 210
        # the heights of the various player states
        # normal height
        self.player_height = 1.863
        # the radius of the players collision shape
        self.player_radius = self.player_height / 4.0
        # crouch height
        self.player_height_crouch = self.player_height / 3.0
        # crawl height
        self.player_height_crawl = self.player_height / 4.0

        #
        # CHARACTER SPEED
        #
        # accleration for the various states
        # these will be multiplied with frame delta time
        self.accleration_walk = 10.0 #2.5
        self.accleration_run = 19.0 #5.0
        self.accleration_sprint = 25.0 #6.0
        # the speed of how fast the player deacclerates
        self.deaccleration = 30.0
        # maximum acclerations at the various states
        self.max_accleration_walk = 5.0
        self.max_accleration_run = 10.0
        self.max_accleration_sprint = 15.0
        # the speed for how fast the player is generally moving
        self.speed = 0.7
        # the movement speed of the character while he is in the air
        self.speed_airborn = 3.4 #0.7
        # transit durations from specific animations. Duration is in
        # seconds
        self.enterSprintDuration = 1.0
        self.enterRunDuration = 0.5 #1.0
        self.enterWalkDuration = 0.5
        # This multiplier is used whenever the character makes a step
        # turn (180 degree direction change)
        self.stepturn_accleration_multiplier = 0.25
        # maximum available stamina
        self.max_stamina = 100.0
        # the minimum amount of stamina that needs to be refilled after
        # all stamina was used.
        self.min_stamina = 50.0
        # how much stamina is drained per second when the player sprints
        # NOTE: set this to 0 to deactivate stamina usage
        self.stamina_usage_per_second = 25.0
        # how much stamina is recovered per second when the player is
        # in the specific state
        self.stamina_recover_per_second_idle = 15.0
        self.stamina_recover_per_second_walk = 10.0
        self.stamina_recover_per_second_run = 5.0

        #
        # CHARACTER STEPPING
        #
        # step height
        self.stepheight = 0.27
        # angle at which the character will not slip
        self.slip_free_angle = 30.0

        #
        # CHARACTER JUMPING AND FALLING
        #
        # the force of a jump
        self.jump_strength_default = 5 if USEINTERNAL else 10
        self.jump_strength = self.jump_strength_default
        self.jump_forward_force_mult = 1.0
        # for internal physics engine, the maximum jump force. This
        # determines how much force and hence how high/far the player
        # can jump
        self.max_jump_force_internal_X = 4.0
        self.max_jump_force_internal_Y = 4.0
        self.max_jump_force_internal_Z = 6.0
        # how long (in sec) is the player able to hold the jump key down
        # to enhance jump strength
        self.max_jump_press_time = 1.10
        # this sets the minimum time that has to be used for a jump
        self.min_jump_press_time = 0.1
        # the force that gets applied to the player every frame while
        # pressing down the jump key
        self.phys_jump_strength = 10
        # this will tell the player if he can or can't jump at all
        self.jump_enabled = True
        # this sets the time for which the player can still jump after
        # falling off of a ledge
        self.jump_allow_after_fall_time = 0.2
        # this value is multiplied with the active accleration and will
        # take affect after landing
        self.jump_accleration_multiplier = 1.0
        # this multiplier gets multiplied to the deaccleration to
        # calculate how fast the player deaclerates when airborn
        self.jump_airborn_deaccleration_multiplier = 0.25
        # the time in seconds after which the animation changes to fall
        # after jump has been activated
        self.start_fall_time = 1.10

        #
        # CHARACTER WALL CHECK
        #
        # this variable sets at which distance the forward wall check should be started
        self.forward_check_distance = 2.0
        # this distance determines how close the player can move to a wall before he stops completely
        self.forward_stop_distance = self.player_radius + 0.15
        # this minimum speed is for the distance between the first forward wall check
        # and the definite stop as set with forward_stop_distance
        self.forward_min_speed_to_stop = 2.0
        # This variable can be set to tell which angle the wall must have
        # to be able to make a wall run at
        self.min_wall_angle_for_wall_run = 75

        #
        # CHARACTER WALLRUN
        #
        self.wall_run_forward_check_dist = 1.25
        self.wall_run_sideward_check_dist = 1.25
        self.wall_run_enabled = True
        self.min_wall_run_speed = 1.5
        self.wall_run_speed = 2.5
        self.max_wall_run_speed = 5
        self.wall_run_forward_speed_multiplier = 2.0
        self.wall_run_off_jump_strength = 5
        self.wall_run_up_jump_direction = Vec3(0, -0.05, 0)
        self.wall_run_forward_jump_direction = Vec3(0, 2, 0)
        self.wall_run_left_jump_direction = Vec3(-2, 0, 0)
        self.wall_run_right_jump_direction = Vec3(2, 0, 0)
        # this determines how long the character had to fall until he
        # can initiate the wall run (prevent jumping up on high walls
        # with the use of wall runs)
        self.wall_run_min_fall_time = 1.5

        #
        # CHARACTER LEDGE GRAB
        #
        # set the highest point the player can grab at 1.5 of its height as
        # it is calculated from its 0 point which is at the characters feet.
        self.ledge_top_check_dist = self.player_height + self.player_height / 3.0
        # the lowest point where the character will grab on a ledge is at its
        # center position.
        self.ledge_bottom_check_dist = self.player_height * 0.5
        # this variable determines how far the ledge can be away to grab
        # on to it
        self.ledge_forward_check_dist = self.player_radius * 1.3
        self.ledge_forward_pull_up_dist = self.player_radius * 1.3
        # this will be the z-position at which the character hangs on
        # the ledge
        self.ledge_z_pos = self.player_height * 1.3
        self.ledge_grab_sidward_move_speed = 2.5

        #
        # CHARACTER AND MOVING PLATFORMS
        #
        # the current movable platform which we stand or hang on
        self.active_platform = None
        self.platform_collision_prefix = "FloatingPlatform"
        # if this is set to True, the character will rotate with the platform
        # this will only affect the characters rotation, not heading and pinch
        self.respect_platform_rotation = True
        # if this is set to True, the jump direction will get affected by the
        # current active platform movement
        self.platform_movement_affects_jump = True

        #
        # CHARACTER CLIMBING
        #
        self.climb_forward_check_dist = 1.25
        self.climb_sidward_move_speed = 0.8
        self.climb_vertical_move_speed = 0.8
        self.climb_step_height = 0.4
        self.climb_forward_exit_up_dist = self.player_radius * 1.3
        self.climb_top_check_dist = self.player_height + self.player_height / 3.0
        self.climb_bottom_check_dist = self.player_height * 0.5
