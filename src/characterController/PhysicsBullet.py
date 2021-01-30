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
    Vec3,
    NodePath,
    BitMask32,
    ModelRoot,
    TransformState,
    )
from panda3d.bullet import (
    BulletCapsuleShape,
    BulletSphereShape,
    BulletRigidBodyNode,
    BulletGhostNode)

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

        self.char_collision_dict = {}

        self.event_mask = BitMask32(0x80)  #1000 0000
        self.body_mask = BitMask32(0x70)  #0111 0000
        self.ray_mask = BitMask32(0x0f)  #0000 1111

        self.ignore_step = False
        self.customP = False

        self.pre_set_platform = False

        self.landing_force = None

        self.speed = None

        self.setActivePlatform(None)

        self.raylist = {}
        self.ray_ids = []
        self.ignore_ray_cycle = []
        point_a = Point3(0, 0, self.getConfig("player_height")/1.8)
        point_b = Point3(0, 0, -self.getConfig("stepheight_down"))
        self.foot_ray_id = "foot_ray_check"
        self.registerRayCheck(self.foot_ray_id, point_a, point_b, self.main_node, True)

        self.bodyCollisionList = []
        self.eventCollisionList = []

    def startPhysics(self):
        """Start and set up the remaining physics parts of the character
        Should be called at the character setup and base start method"""

        # some calculations for position and size of the characters body collision spheres
        self.characterBodySphereRadius = self.getConfig("player_height") / 4.0
        r = self.characterBodySphereRadius
        # bottom sphere
        zA = r
        # top sphere
        zB = self.getConfig("player_height") - r

        # Main character spheres
        self.charCollisions = BulletRigidBodyNode("charBody")
        self.charCollisions.setKinematic(False)
        self.charCollisions.setMass(1.0)#self.getConfig("player_mass"))
        self.charCollisions.addShape(
            BulletSphereShape(r),
            TransformState.makePos((0,0,zA)))
        self.charCollisions.addShape(
            BulletSphereShape(r),
            TransformState.makePos((0,0,zB)))
        self.main_node = render.attachNewNode(self.charCollisions)
        self.physic_world.attachRigidBody(self.charCollisions)

        self.charCollisions.setIntoCollideMask(self.body_mask)
        self.charCollisions.setCcdMotionThreshold(1e-7)
        self.charCollisions.setCcdSweptSphereRadius(r)

        # Create the big sphere around the caracter which can be used for special events
        self.charEventCollisions = BulletGhostNode(self.getConfig("char_collision_name"))
        self.eventCollider = self.main_node.attachNewNode(self.charEventCollisions)
        self.charEventCollisions.addShape(
            BulletSphereShape(self.getConfig("player_height")/2.0),
            TransformState.makePos((0, 0, self.getConfig("player_height")/2.0)))
        self.charEventCollisions.setIntoCollideMask(self.event_mask)
        self.physic_world.attachGhost(self.charEventCollisions)

        self.accept("charBody-in", self.checkInBodyContact)
        self.accept("charBody-out", self.checkOutBodyContact)
        self.accept("{}-in".format(self.getConfig("char_collision_name")), self.checkCharCollisions)
        self.accept("{}-out".format(self.getConfig("char_collision_name")), self.charOutCollisions)

        '''
        shapeHolder = NodePath("Bullet Shape Holder")
        shapeHolder.setZ(self.getConfig("player_height")/2.0)
        shapeHolder.reparentTo(render)
        self.charFutureCollisions = shapeHolder.attachNewNode(BulletRigidBodyNode("charFutureBody"))
        self.charFutureCollisions.node().addShape(BulletSphereShape(self.getConfig("player_height")/4.0))
        self.charFutureCollisions.node().setIntoCollideMask(self.body_mask)
        '''

        if self.getConfig("use_simple_shadow"):
            self.shadow_ray_id = "shadow_ray_check"
            if self.shadow_ray_id not in self.raylist:
                point_a = Point3(0, 0, self.getConfig("player_height")/1.8)
                point_b = self.main_node.getPos()
                point_b.setZ(point_b.getZ() - 10000)
                self.registerRayCheck(self.shadow_ray_id, point_a, point_b, self.main_node)

        self.reparentTo(self.main_node)

        self.physic_world.setTickCallback(self.tickCallback, False)

    def tickCallback(self, a):
        speed = self.speed
        if speed is not None:
            speed.setX(speed.getX()/(a.timestep/10))
            speed.setY(speed.getY()/(a.timestep/10))
            self.charCollisions.setLinearVelocity(speed)

    def registerRayCheck(self, ray_id, pos_a, pos_b, parent, ignore_ray_cycle=False):
        """This function will create a ray segment at the given position
        and attaches it to the given parent node. This has to be done
        for any ray check you want to do in the application."""
        r = self.Ray(pos_a, pos_b, parent)
        # store the ray for later usage
        self.raylist[ray_id] = r
        if ignore_ray_cycle:
            self.ignore_ray_cycle.append(ray_id)
        if ray_id not in self.ignore_ray_cycle:
            self.ray_ids.append(ray_id)

    def stopPhysics(self):
        """Stops the characters physics elements. Should be called at
        character cleanup"""
        #TODO: Cleanup
        self.char_collision_dict = {}
        self.raylist = None
        self.charCollisions.removeNode()

    def updatePhysics(self):
        """This method must be called every frame to update collision contacts."""

        self.main_node.setP(0)
        self.main_node.setR(0)

        # since bullet doesn't have a way to do it automatically, we have to
        # check collisions and store them on our own to check when we hit
        # something for the first time and whenever we lost a collision contact

        # Check for Body contact
        result = self.physic_world.contactTest(self.charCollisions, True)

        lostContacts = self.bodyCollisionList

        # check the new contacts
        for contact in result.getContacts():
            # check if we already had contact to this
            if contact in self.bodyCollisionList:
                # existing contact
                lostContacts.reomve(contact)
            else:
                # new contact
                self.bodyCollisionList.append(contact)
                base.messenger.send("charBody-in", [contact])

        # remove lost contacts from our list
        for contact in lostContacts:
            self.bodyCollisionList.remove(contact)
            base.messenger.send("charBody-out", [contact])

        '''
        # Check for event sphere contact
        result = self.physic_world.contactTest(self.eventCollider.node(), True)

        lostContacts = self.eventCollisionList

        # check the new contacts
        for contact in result.getContacts():
            # check if we already had contact to this
            if contact in self.eventCollisionList:
                # existing contact
                lostContacts.reomve(contact)
            else:
                # new contact
                self.eventCollisionList.append(contact)
                base.messenger.send("{}-in".format(self.getConfig("char_collision_name")), [contact])

        # remove lost contacts from our list
        for contact in lostContacts:
            self.eventCollisionList.remove(contact)
            base.messenger.send("{}-out".format(self.getConfig("char_collision_name")), [contact])
        '''

    def updateRayPositions(self, ray_id, point_a, point_b):
        """This method can be used to update the start and end position
        of the ray with the given ID"""
        self.raylist[ray_id].point_a = point_a
        self.raylist[ray_id].point_b = point_b

    def updatePlayerPos(self, speed, heading):
        """This function should be called to set the players new
        position and heading.
        speed determines the new position of the character.
        heading sets the new direction the player will face as seen from
        the camera and can be None.
        This function will process the stepping and dependend on that
        requests fall and landing states"""
        dt = globalClock.getDt()
        if heading is not None:
            curH = self.main_node.getH()

            tempNp = NodePath("temp")
            tempNp.setHpr(self.main_node.getHpr())
            tempNp.setH(camera, heading)
            rotation_angle = self.main_node.getHpr(tempNp)
            tempNp.removeNode()
            tempNp = None
            velocity = Vec3(0, 0, 1) * -rotation_angle.getX()
            self.charCollisions.setActive(True, True)
            self.charCollisions.setAngularVelocity(velocity)
        else:
            self.charCollisions.setAngularVelocity(0)

        speed = self.main_node.getRelativeVector(render, speed)
        speed.setX(-speed.getX())
        zVel = self.charCollisions.getLinearVelocity().getZ()
        speed.setZ(speed.getZ() + zVel)

        self.speed = speed
        #self.charCollisions.setLinearVelocity(speed)

        self.updateCharSimpleShadow()

        if self.state not in self.ignore_step_states:
            if self.doStep():
                self.landing_force = self.main_node.node().getLinearVelocity()
                if self.state not in self.on_ground_states:
                    self.charCollisions.setAngularVelocity((0, 0, 0))
                    self.charCollisions.setLinearVelocity((0, 0, 0))
                    self.plugin_requestNewState(self.STATE_LAND)
            elif self.state != self.STATE_JUMP and self.state != self.STATE_FALL:
                self.plugin_requestNewState(self.STATE_FALL)

    def updatePlayerPosFloating(self, speed):
        """This method will update the position of the player respecting
        the global directions rather then the players local direction,
        which is useful for example if the player gets moved by a
        platform he stands on or wind or whatever external force may
        move the player around."""
        preFlyMode = self.charCollisions.getKinematic()
        self.toggleFlyMode(False)
        newPos = self.main_node.getPos() + speed
        self.main_node.setPos(newPos)
        self.updateCharSimpleShadow()
        self.toggleFlyMode(preFlyMode)

    def updatePlayerPosFix(self, position, relativeTo=None):
        """This method will place the character at the given position."""
        preFlyMode = self.charCollisions.getKinematic()
        self.toggleFlyMode(False)
        if relativeTo is not None:
            self.main_node.setPos(relativeTo, position)
        else:
            self.main_node.setPos(position)
        self.updateCharSimpleShadow()
        self.toggleFlyMode(preFlyMode)

    def updatePlayerPosFloatingFlyign(self, speed):
        """This method will update the position of the player respecting
        the global directions rather then the players local direction,
        which is useful for example if the player gets moved by a
        platform he stands on or wind or whatever external force may
        move the player around.
        Note: this function will use the not physic related position
        update function and should only be used on flying modes if
        physics are disabled"""
        # check if we are in fly mode, otherwise we won't let this happen
        if self.charCollisions.getKinematic() == False: return
        newPos = self.main_node.getPos() + speed
        self.main_node.setPos(newPos)
        self.updateCharSimpleShadow()

    def updatePlayerHpr(self, hpr):
        """Update the HPR value of the main player node"""
        if hpr[1] != 0:
            self.customP = True
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
        return
        """This method will update the player position according to the
        rotation around the given parent node.
        NOTE: this will currently only work with rotations around the
        Z-Axis"""

        self.main_node.setPos(self.__getHprFloatingNewPos(rotation, parent))
        self.main_node.setH(self.main_node.getH() + rotation)

    def updatePlayerHprFloatingFlying(self, rotation, parent):
        return
        """This method will update the player position according to the
        rotation around the given parent node.
        NOTE: this will currently only work with rotations around the
        Z-Axis"""

        self.main_node.setPos(self.__getHprFloatingNewPos(rotation, parent))
        self.main_node.setH(self.main_node.getH() + rotation)

    def checkCharCollisions(self, args):
        return
        """This method will be called each time a collision occures with
        the characters main collision solids. It will check stepping as
        well as check if the character should fall or just landed
        somewhere."""
        if self.state in self.ignore_step_states:
            pass
        elif self.doStep():
            if self.state == self.STATE_JUMP or self.state == self.STATE_FALL:
                self.landing_force = self.charCollisions.getLinearVelocity()
                self.plugin_requestNewState(self.STATE_LAND)
        elif self.state != self.STATE_JUMP and self.state != self.STATE_FALL:
            self.plugin_requestNewState(self.STATE_FALL)
        self.enterNewState()
        base.messenger.send("plugin-character-in-collision", [collision])

    def charOutCollisions(self, collision):
        return
        base.messenger.send("plugin-character-out-collision", [collision])

    def checkInBodyContact(self, collision):
        return
        self.char_collision_dict[collision.getNode1().getName()] = collision

    def checkOutBodyContact(self, collision):
        return
        """This method will be called each time the character doesn't
        collide with a previous collided object anymore. It will remove
        the collision from the objects checked when stepping."""
        name = collision.getIntoNode().getName()
        if name in self.char_collision_dict.keys():
            del self.char_collision_dict[name]
        else:
            print("COULDN'T FIND", name)

    def checkFloatingPlatform(self, entry):
        if entry is not None:
            if entry.getName().startswith(self.getConfig("platform_collision_prefix")):
                # we landed on a moving platform
                p = render.find("**/%s"%entry.getName())
                self.setActivePlatform(self.__findPlatformRoot(p))
                self.pre_set_platform = True

    def cleanFloatingPlatform(self):
        if not self.pre_set_platform:
            self.setActivePlatform(None)

    def __findPlatformRoot(self, platform):
        return
        """This method will find the root node of a floating platform
        which then may be used to update the characters position on that
        specific platform. This function will be called recursively."""
        if platform.hasParent():
            if platform.node().getType() == ModelRoot:
                return platform
            return self.__findPlatformRoot(platform.getParent())
        return platform

    def doStep(self):
        """This method will process the characters downward stepping to
        prevent it from floating. It will also check if the character
        landed on a movable platform and set it as active platform.
        This function will return True whenever the character has been
        stepped on the ground and falls if there was no step"""
        if self.state not in self.ignore_step_states:
            # do the step height check
            char_step_collision = self.getFirstCollisionEntryInLine(self.foot_ray_id)

            # Check if we land on a movable platform
            groundNode = self.getFirstCollisionIntoNodeInLine(self.foot_ray_id)

            # we're not interrested in extra character collisions if we have actual foot contact

            shiftZ = 0

            #TODO: Bullet specific changes need to be made from here
            if self.getConfig("do_step_up_check"):
                #
                # In this section we are going to check if the character should
                # move up on stairs. For this we need to gather all collision
                # points that have occured with the characters body collisions
                #
                entries = self.physic_world.contactTest(self.charCollisions, True).getContacts()
                for collision in entries:

                    mpoint = collision.getManifoldPoint()

                    newPos = mpoint.getPositionWorldOnB()
                    #self.placer_b.setPos(newPos)
                    stepHeight = mpoint.getLocalPointB().getZ()
                    if stepHeight >= self.getConfig("stepheight_min_up") and stepHeight <= self.getConfig("stepheight_max_up"):
                        # move up a tiny bit, so we won't stuck in the ground
                        newPos.setZ(newPos.getZ() + 0.2)
                        # also move forward by the given amount so we won't fall off of the step right away
                        #newPos.setY(newPos.getY() - self.getConfig("step_up_forward_distance"))
                        self.main_node.setPos(newPos)
                        return True

            if char_step_collision is None:
                # check for additianal collisions with the char sphere or
                # any other solids that serve as "stand on ground" check
                for key, collision in self.char_collision_dict.items():

                    pos = collision.getManifoldPoint().getLocalPointB()
                    dist = -(collision.getManifoldPoint().getDistance())
                    # sometimes the calculated distance is in the wrong direction
                    if dist < 0: continue
                    shiftZ = dist
                    if dist < self.getConfig("player_height")/100.0:
                        char_step_collision = char_step_collision if char_step_collision is not None else collision
                        groundNode = groundNode if groundNode is not None else collision.getNode1()
                        break
                    else:
                        if dist > self.characterBodySphereRadius:
                            # if the collisions are higher, we
                            # probably collided with the upper
                            # collision sphere of the player
                            dist = self.characterBodySphereRadius

                        dt = globalClock.getDt()
                        moveVec = pos
                        moveVec.setZ(0)
                        moveVec *= -1
                        moveVec *= dt


                        moveVec = self.main_node.getRelativeVector(render, moveVec)
                        moveVec.setX(-moveVec.getX())
                        newPos = self.main_node.getPos() + moveVec
                        self.main_node.setPos(newPos)

                        #self.main_node.setPos(self.main_node, moveVec)
                        self.toggleFlyMode(False)
                        return False

            self.clearFirstCollisionEntryOfRay(self.foot_ray_id)
            self.cleanFloatingPlatform()
            self.pre_set_platform = False
            if groundNode is not None:
                if groundNode.getName().startswith(self.getConfig("platform_collision_prefix")):
                    # we landed on a moving platform
                    p = render.find("**/%s"%groundNode.getName())
                    self.setActivePlatform(self.__findPlatformRoot(p))

            # prevent slipping
            if self.state in self.prevent_slip_states and char_step_collision is not None:
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
                    self.main_node.setFluidZ(pos.getZ() - shiftZ)
                    return True
            return False
        elif self.charCollisions and self.state not in self.flying_states:
            self.toggleFlyMode(False)
        self.setActivePlatform(None)
        return False

    def toggleFlyMode(self, flyActive):
        """Dis- and Enable the physic effects on the character to give
        him the possibility to fly."""
        self.charCollisions.setKinematic(flyActive)

    def hasSurfacePoint(self, entry):
        return entry.hasHit()

    def getSurfacePoint(self, entry, np):
        return entry.getHitPos()

    def hasSurfaceNormal(self, entry):
        return entry.hasHit()

    def getSurfaceNormal(self, entry, np):
        return entry.getHitNormal()

    def getFallForce(self):
        return self.charCollisions.getLinearVelocity().getZ()

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

    def clearFirstCollisionEntryOfRay(self, ray_id):
        """Not necessary for Bullet physics collision system"""
        pass

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
        pos = None
        if entry.hasHit():
            pos = entry.getHitPos()
        return pos

    def checkFutureCharSpace(self, new_position):
        return True
        """Check if there is enough space at the new position to place
        the character on. If so, this function will return True
        otherwise it will return False"""
        if new_position is None: return False
        #TODO: Implement the bullet way
        self.charFutureCollisions.setPos(new_position)
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
        if not self.getConfig("use_simple_shadow"): return
        self.raylist[self.shadow_ray_id].point_a = self.main_node.getPos()
        pos = self.getFirstCollisionInLine(self.shadow_ray_id)
        if pos is not None:
            self.shadow.setPos(pos.getX(), pos.getY(), pos.getZ() + self.getConfig("shadow_z_offset"))
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

    def doJump(self, forwardSpeed, jump_direction=Vec3(0,0,0), extraSpeedVec=Vec3()):
        """This will let the actor node jump forward on the local y-axis
        with the upward speed given in jumpForce and forward given in speed.
        Note, if the actorNode shouldn't slide after landing call the
        physics.land function with the same actorNode"""
        #
        # Reset stuff
        #
        # as we leave the ground set the active platform, if any, to None
        self.setActivePlatform(None)

        # make sure we aren't in fly mode, otherwise we can't jump at all
        self.toggleFlyMode(False)

        #
        # Jump vector calculation
        #
        dt = globalClock.getDt()
        jumpVec = Vec3(
            jump_direction.getX()*dt,
            -((forwardSpeed*self.getConfig("jump_forward_force_mult"))+jump_direction.getY())*dt,
            (self.getConfig("phys_jump_strength")+jump_direction.getZ()))#*dt)
        jumpVec *= self.getConfig("jump_strength")

        #
        # Extra speed calculation
        #
        # rotate the extraSpeedVector to face the same direction the main_node
        # does and add it to the jump vector
        jumpVec += self.main_node.getRelativeVector(render, extraSpeedVec)

        #
        # Push the character
        #
        # now add the actual force to the characters physic node
        #TODO: Which one is correct?
        #self.charCollisions.applyCentralImpulse(jumpVec)
        self.charCollisions.applyCentralForce(jumpVec)

        #
        # Velocity checks
        #
        #TODO: Check for the right function
        vel = self.charCollisions.getLinearVelocity()
        #TODO: This portion can be shared
        velX = vel.getX()
        velY = vel.getY()
        velZ = vel.getZ()

        # Make sure we don't jump/move faster than we are alowed to
        if abs(velX) > self.getConfig("max_jump_force_internal_X") \
        or abs(velY) > self.getConfig("max_jump_force_internal_Y"):
            # we need to make sure X and Y are at the same distance
            # as before otherwise jump direction will be shifted
            if abs(velX) > abs(velY):
                pass
                #TODO: Calculate diff between x and y and subtract/add to respective other
            if velX < 0:
                velX = -self.getConfig("max_jump_force_internal_X")
            else:
                velX = self.getConfig("max_jump_force_internal_X")
        if abs(velY) > self.getConfig("max_jump_force_internal_Y"):
            if velY < 0:
                velY = -self.getConfig("max_jump_force_internal_Y")
            else:
                velY = self.getConfig("max_jump_force_internal_Y")
        if abs(velZ) > self.getConfig("max_jump_force_internal_Z"):
            if velZ < 0:
                velZ = -self.getConfig("max_jump_force_internal_Z")
            else:
                velZ = self.getConfig("max_jump_force_internal_Z")
        #TODO: This portion can be shared END


    def land(self):
        """Reset velocities of the characters physic node"""
        #self.actorNode.getPhysicsObject().setVelocity(0,0,0)
        pass

    def setActivePlatform(self, platform):
        return
        self.active_platform = platform

    def getActivePlatform(self):
        return None
        return self.active_platform
