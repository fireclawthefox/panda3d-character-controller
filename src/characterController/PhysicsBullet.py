#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# PYTHON IMPORTS
#
import math

#
# PANDA3D ENGINE IMPORTS
#
from panda3d.core import (
    Point3,
    BitMask32,
    NodePath,
    Vec3)
from panda3d.bullet import (
    BulletCapsuleShape,
    BulletRigidBodyNode)

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


#
# PHYSICS FUNCTIONS
#
class Physics:
    class Ray:
        def __init__(self, point_a, point_b, parent):
            self.point_a = point_a
            self.point_b = point_b
            self.parent = parent

    def __init__(self):
        # setup the capsule that surrounds the player
        self.player_capsule = BulletCapsuleShape(self.getConfig("player_radius"), self.getConfig("player_height")/2.0)
        self.base_z_off = self.getConfig("player_height")/2.0

        self.setActivePlatform(None)

        self.event_mask = BitMask32(0x80)  #1000 0000
        self.body_mask = BitMask32(0x70)  #0111 0000
        self.ray_mask = BitMask32(0x0f)  #0000 1111

        self.ignore_step = False

        self.raylist = {}
        point_a = Point3(0, 0, self.getConfig("player_height")/1.8)
        point_b = Point3(0, 0, -self.getConfig("stepheight"))
        self.foot_ray_id = "foot_ray_check"
        self.registerRayCheck(self.foot_ray_id, point_a, point_b, self.main_node)

    def startPhysics(self):
        """Start and set up the remaining physics parts of the character
        Should be called at the character setup and base start method"""
        capsule = BulletRigidBodyNode("Capsule")
        capsule.addShape(self.player_capsule)
        capsule.setKinematic(False)
        capsule.setMass(self.getConfig("player_mass"))
        self.physic_world.attachRigidBody(capsule)
        self.player_capsule_np = NodePath(capsule)
        self.player_capsule_np.setPos(0, 0, self.getConfig("player_height"))
        self.player_capsule_np.setCollideMask(self.body_mask)
        self.reparentTo(self.player_capsule_np)
        self.setZ(-self.getConfig("player_height")/2.0)
        self.player_capsule_np.reparentTo(render)
        self.main_node = self.player_capsule_np

        self.shadow_ray_id = "shadow_ray_check"
        if self.shadow_ray_id not in self.raylist:
            point_a = Point3(0, 0, self.getConfig("player_height")/1.8)
            point_b = self.main_node.getPos()
            point_b.setZ(point_b.getZ() - 10000)
            self.registerRayCheck(self.shadow_ray_id, point_a, point_b, self.main_node)

        #self.should_jump = False
        #self.jump_time = 0.0

        #taskMgr.add(self.updatePhysics, "task_physics", priority=-15)

    def registerRayCheck(self, ray_id, pos_a, pos_b, parent):
        """This function will create a ray segment at the given position
        and attaches it to the given parent node. This has to be done
        for any ray check you want to do in the application."""
        r = self.Ray(pos_a, pos_b, parent)
        # store the ray for later usage
        self.raylist[ray_id] = r

    def stopPhysics(self):
        """Stops the characters physics elements. Should be called at
        character cleanup"""
        #TODO: Cleanup
        self.raylist = None
        #taskMgr.remove("task_physics")
        self.player_capsule_np.removeNode()

    def updatePhysics(self):
        self.main_node.setP(0)
        self.main_node.setR(0)

    def updateRayPositions(self, ray_id, point_a, point_b):
        """This method can be used to update the start and end position
        of the ray with the given ID"""
        self.raylist[ray_id].point_a = point_a
        self.raylist[ray_id].point_b = point_b

    def updatePlayerPos(self, speed, heading, dt, rotation=None, rotate_around_node=None, ignore_step=False):
        """This function should be called to set the players new
        position and heading.
        speed determines the new position of the character.
        heading sets the new direction the player will face as seen from
        the camera and can be None.
        This function will process the stepping and dependend on that
        requests fall and landing states"""
        if heading is not None:
            self.main_node.setH(camera, heading)
            self.main_node.setP(0)
            self.main_node.setR(0)
        self.main_node.setPos(self.main_node, speed)
        self.ignore_step = ignore_step
        if not ignore_step:
            if self.doStep(self.state == self.STATE_IDLE):
                self.main_node.node().setAngularVelocity((0, 0, 0))
                self.main_node.node().setLinearVelocity((0, 0, 0))
                if self.state == self.STATE_JUMP or self.state == self.STATE_FALL:
                    self.request(self.STATE_LAND)
            elif self.state != self.STATE_JUMP \
            and self.state != self.STATE_FALL \
            and self.state != self.STATE_LEDGE_GRAB_UP:
                self.request(self.STATE_FALL)

        if self.getConfig("use_simple_shadow"):
            self.updateCharSimpleShadow()

    def updatePlayerPosFloating(self, speed):
        """This method will update the position of the player respecting
        the global directions rather then the players local direction,
        which is useful for example if the player gets moved by a
        platform he stands on or wind or whatever external force may
        move the player around."""
        newPos = self.main_node.getPos() + speed
        self.main_node.setPos(newPos)

    def updatePlayerPosFix(self, position, relativeTo=None):
        """This method will place the character at the given position."""
        if relativeTo is not None:
            self.main_node.setPos(relativeTo, position)
        else:
            self.main_node.setPos(position)

    def updatePlayerPosFloatingFlyign(self, speed):
        """This method will update the position of the player respecting
        the global directions rather then the players local direction,
        which is useful for example if the player gets moved by a
        platform he stands on or wind or whatever external force may
        move the player around.
        Note: this function will use the not physic related position
        update function and should only be used on flying modes if
        physics are disabled"""
        newPos = self.main_node.getPos() + speed
        self.main_node.setPos(newPos)

    def updatePlayerHpr(self, hpr):
        """Update the HPR value of the main player node"""
        self.main_node.setHpr(hpr)

    def __getHprFloatingNewPos(self, rotation, parent):
        """This function calculates the new position the character will
        get when he will be rotated around the given parent node"""
        center = parent.getPos(render)

        posvec = parent.getPos(render) - self.main_node.getPos(render)
        posvec.setZ(0)
        circle_radius = posvec.length()

        # calculate the current angle of the player to the platform
        xdiff = self.main_node.getX() - parent.getX()
        ydiff = self.main_node.getY() - parent.getY()
        cur_angle_rad = math.atan2(ydiff, xdiff)
        # calculate the amount of radians that we will move the player
        rotation_rad = math.radians(rotation)
        # the new angle to which we will move the player to
        new_angle_rad = cur_angle_rad + rotation_rad

        # calculate the new position in the circle asuming the parent as
        # the center and using the previously calculated circle radius
        # and angle.
        x = parent.getX() + circle_radius * math.cos(new_angle_rad)
        y = parent.getY() + circle_radius * math.sin(new_angle_rad)

        # finally set the new position of the player
        new_pos = self.main_node.getPos()
        new_pos.setX(x)
        new_pos.setY(y)

        return new_pos

    def updatePlayerHprFloating(self, rotation, parent):
        """This method will update the player position according to the
        rotation around the given parent node.
        NOTE: this will currently only work with rotations around the
        Z-Axis"""

        self.main_node.setPos(self.__getHprFloatingNewPos(rotation, parent))
        self.main_node.setH(self.main_node.getH() + rotation)

    def updatePlayerHprFloatingFlying(self, rotation, parent):
        """This method will update the player position according to the
        rotation around the given parent node.
        NOTE: this will currently only work with rotations around the
        Z-Axis"""

        self.main_node.setPos(self.__getHprFloatingNewPos(rotation, parent))
        self.main_node.setH(self.main_node.getH() + rotation)

    def checkCharCollisions(self, args):
        """This method will be called each time a collision occures with
        the characters main collision solids. It will check stepping as
        well as check if the character should fall or just landed
        somewhere."""
        if self.ignore_step:
            pass
        elif self.doStep(self.state == self.STATE_IDLE):
            if self.state == self.STATE_JUMP or self.state == self.STATE_FALL:
                self.main_node.node().setAngularVelocity((0, 0, 0))
                self.main_node.node().setLinearVelocity((0, 0, 0))
                self.request(self.STATE_LAND)
                return
        elif self.state != self.STATE_JUMP and self.state != self.STATE_FALL:
            self.request(self.STATE_FALL)
            return

    def checkFloatingPlatform(self, entry):
        if entry is not None:
            if entry.getName().startswith(self.getConfig("platform_collision_prefix")):
                # we landed on a moving platform
                p = render.find("**/%s"%entry.getName())
                self.setActivePlatform(self.__findPlatformRoot(p))

    def setActivePlatform(self, platform):
        self.active_platform = platform

    def getActivePlatform(self):
        return self.active_platform

    def __findPlatformRoot(self, platform):
        """This method will find the root node of a floating platform
        which then may be used to update the characters position on that
        specific platform. This function will be called recursively."""
        if platform.hasParent():
            if platform.node().getType() == ModelRoot:
                return platform
            return self.__findPlatformRoot(platform.getParent())
        return platform

    def doStep(self, preventSlipping=False):
        """This method will process the characters downward stepping to
        prevent it from floating. It will also check if the character
        landed on a movable platform and set it as active platform.
        This function will return True whenever the character has been
        stepped on the ground and Fals if there was no step"""
        if self.state not in self.ignore_step_states:
            # do the step height check
            char_step_collision = self.getFirstCollisionEntryInLine(self.foot_ray_id)

            # Check if we land on a movable platform
            groundNode = self.getFirstCollisionIntoNodeInLine(self.foot_ray_id)
            if groundNode is not None:
                if groundNode.getName().startswith(self.getConfig("platform_collision_prefix")):
                    # we landed on a moving platform
                    p = render.find("**/%s"%groundNode.getName())
                    self.setActivePlatform(self.__findPlatformRoot(p))
                else:
                    self.setActivePlatform(None)
            else:
                self.setActivePlatform(None)

            # prevent slipping
            if preventSlipping and char_step_collision is not None:
                # get the angle of the part of the ground we currently
                # stand on
                floor_normal = self.getSurfaceNormal(char_step_collision, render)
                zx = math.atan2(floor_normal.getZ(), floor_normal.getX())*180/math.pi
                zy = math.atan2(floor_normal.getZ(), floor_normal.getY())*180/math.pi
                zx = abs(zx-90)
                zy = abs(zy-90)
                # if the angle is within a specific range
                if zy <= self.getConfig("slip_free_angle") and zx <= self.getConfig("slip_free_angle"):
                    # prevent slipping
                    if zy > 0 or zx > 0:
                        self.toggleFlyMode(True)
                    return True
            self.toggleFlyMode(False)

            if char_step_collision is not None:
                if self.hasSurfacePoint(char_step_collision):
                    # place the character on the ground
                    pos = self.getSurfacePoint(char_step_collision, render)
                    self.main_node.setZ(pos.getZ() + self.base_z_off)
                    return True
            return False
        #elif self.anRemoved and self.state not in self.flying_states:
        #    self.toggleFlyMode(False)
        elif self.state in self.ledge_grab_states:
            # Check if we hang on a movable platform
            ledge_node = self.getFirstCollisionIntoNodeInLine(self.ledge_detect_ray)
            if ledge_node is not None:
                if ledge_node.getName().startswith(self.getConfig("platform_collision_prefix")):
                    # we do hang on a moving platform
                    p = render.find("**/%s"%ledge_node.getName())
                    self.setActivePlatform(self.__findPlatformRoot(p))
                else:
                    self.setActivePlatform(None)
            else:
                self.setActivePlatform(None)
            return True
        self.setActivePlatform(None)
        return False

    def toggleFlyMode(self, flyActive):
        """Dis- and Enable the physic effects on the character to give
        him the possibility to fly."""
        #TODO: Bullet specific code
        #if flyActive:
        #    if not self.anRemoved:
        #        self.anRemoved = True
        #        self.actorNode.getPhysicsObject().setVelocity(0,0,0)
        #        base.physicsMgr.removePhysicalNode(self.actorNode)
        #else:
        #    if self.anRemoved:
        #        self.anRemoved = False
        #        base.physicsMgr.attachPhysicalNode(self.actorNode)
        pass

    def hasSurfacePoint(self, entry):
        return entry.hasHit()

    def getSurfacePoint(self, entry, np):
        return entry.getHitPos()

    def hasSurfaceNormal(self, entry):
        return entry.hasHit()

    def getSurfaceNormal(self, entry, np):
        return entry.getHitNormal()

    def getFirstCollisionEntryInLine(self, ray_id):
        """A simple raycast check which will return the collision entry
        of the first collision point as seen from the previously
        registred ray with the given ID"""
        result = self.physic_world.rayTestClosest(
            self.raylist[ray_id].point_a,
            self.raylist[ray_id].point_b,
            self.ray_mask)
        if result.hasHit():
            return result
        return None

    def getFirstCollisionIntoNodeInLine(self, ray_id):
        """A simple raycast check which will return the into node of the
        first collision point as seen from the previously registred ray
        with the given ID"""
        entry = self.getFirstCollisionEntryInLine(ray_id)
        if entry is None: return None
        node = None
        node = entry.getNode()
        return node

    def getFirstCollisionInLine(self, ray_id):
        """A simple raycast check which will return the first collision
        point as seen from the previously registred ray with the given
        ID"""
        entry = self.getFirstCollisionEntryInLine(ray_id)
        if entry is None: return None
        pos = entry.getHitPos()
        return pos

    def checkFutureCharSpace(self, new_position):
        """Check if there is enough space at the new position to place
        the character on. If so, this function will return True
        otherwise it will return False"""
        if new_position is None: return False
        #self.charFutureCollisions.setPos(new_position)
        #self.futureCTrav.traverse(render)
        #if self.charFutureCollisionsQueue.getNumEntries() > 0:
        #    return False
        #else:
        #    return True
        return True

    def getbase_z_offset(self):
        return self.base_z_off

    def updateCharSimpleShadow(self):
        """This function will update the simple shadow image below the
        character. It will synch it's position with the player as well
        as calculate it's size when the player is further away from the
        shadow/ground"""
        self.raylist[self.shadow_ray_id].point_a = self.main_node.getPos()
        pos = self.getFirstCollisionInLine(self.shadow_ray_id)
        if pos is not None:
            self.shadow.setPos(pos.getX(), pos.getY(), pos.getZ() + 0.05)
            z_a = pos.getZ()
            z_b = self.main_node.getZ()
            dist = z_b - z_a
            # check if we should scale the shadow below the character
            if dist <= 0:
                self.shadow.setScale(self.getConfig("max_shadow_scale"))
            else:
                # calculate the shadows scale from its current distance
                # to the player
                scale = self.getConfig("shadow_min_scale_dist") - dist / self.getConfig("shadow_scale_factor")
                if scale < self.getConfig("min_shadow_scale"):
                    scale = self.getConfig("min_shadow_scale")
                elif scale > self.getConfig("max_shadow_scale"):
                    scale = self.getConfig("max_shadow_scale")
                self.shadow.setScale(scale)

    def processJumping(self, dt):
        self.jump_time += dt
        self.player_capsule_np.setZ(
            self.player_capsule_np,
            self.getConfig("jump_strength") * self.jump_time)
        if self.jump_time > 0.5:
            self.should_jump = False
            self.jump_time = 0.0
        #if self.__currentPos.z >= self.jumpMaxHeight:
        #    self.__fall()

    def doJump(self, forwardSpeed, extraSpeedVec=Vec3()):
        """This will let the actor node jump forward on the local y-axis
        with the upward speed given in jumpForce and forward given in speed.
        Note, if the actorNode shouldn't slide after landing call the
        physics.land function with the same actorNode"""
        # as we leave the ground set the active platform, if any, to None
        self.setActivePlatform(None)
        jumpVec = Vec3(0, -forwardSpeed/self.current_max_accleration*self.getConfig("jump_forward_force_mult"), 1)
        jumpVec *= self.getConfig("jump_strength")

        # rotate the extraSpeedVector to face the same direction the main_node vector
        charVec = self.main_node.getRelativeVector(render, extraSpeedVec)
        charVec.normalize()
        rotatedExtraSpeedVec = charVec * extraSpeedVec.length()

        jumpVec += rotatedExtraSpeedVec
        #self.player_capsule_np.node().applyCentralImpulse(jumpVec)
        self.player_capsule_np.node().applyCentralForce(jumpVec)
