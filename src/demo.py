#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    loadPrcFileData,
    Vec3,
    Point3,
    DirectionalLight,
    VBase4,
    AmbientLight,
    CollisionTraverser,
    CollisionPlane,
    CollisionBox,
    CollisionNode,
    Plane,
    BitMask32,

    # For building Bullet collision geometry
    Geom,
    GeomTriangles,
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter)
from panda3d.bullet import (
    BulletWorld,
    BulletDebugNode,
    BulletPlaneShape,
    BulletRigidBodyNode,
    BulletGhostNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
    BulletHelper)
from panda3d.physics import ForceNode, LinearVectorForce
from direct.interval.IntervalGlobal import Sequence, Wait

# The necessary import to run the Extended Character Controller
from player.PlayerController import PlayerController

# only necessary to check whether bullet or the internal physics engine
# should be used
from player.Config import USEBULLET, USEINTERNAL

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""

# setup Logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    filename="./demo.log",
    datefmt="%d-%m-%Y %H:%M:%S",
    filemode="w")


loadPrcFileData("","""
show-frame-rate-meter #t
model-path $MAIN_DIR/testmodel
cursor-hidden 1
on-screen-debug-enabled #f
want-pstats #f
want-tk #f
fullscreen #t
win-size 1920 1080
""")

class Main(ShowBase):
    def __init__(self):
        """initialise and start the Game"""
        ShowBase.__init__(self)

        self.accept("escape", exit)
        self.accept("gamepad-start", exit)
        self.accept("f1", self.toggleDebug)
        self.accept("r", self.resetPlayer)
        self.accept("p", self.togglePause)
        self.accept("f2", self.toggleCamera)
        self.accept("f3", self.toggleOSD)
        # automatically pause if the player is idling for to long
        self.accept("playerIdling", self.pause)
        #def printsomething():
        #    print "something"
        #self.accept("gamepad1-action_a", printsomething)
        self.disableMouse()

        base.win.movePointer(0, base.win.getXSize() // 2, base.win.getYSize() // 2)

        self.useBullet = USEBULLET
        self.useInternal = USEINTERNAL
        self.debugactive = True

        # Comment this line out if the demo runs slow on your system
        render.setShaderAuto(True)

        #
        # SIMPLE LEVEL SETUP
        #
        if self.useInternal:
            self.level = loader.loadModel("../data/level/level")
        else:
            self.level = loader.loadModel("../data/level/level")
        self.level.reparentTo(render)
        #
        # Lights
        #
        alight = AmbientLight("Ambient")
        alight.setColor(VBase4(0.5, 0.5, 0.5, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
        sun = DirectionalLight("Sun")
        sun.setColor(VBase4(1.5, 1.5, 1.0, 1))
        sunnp = render.attachNewNode(sun)
        sunnp.setHpr(10, -60, 0)
        render.setLight(sunnp)
        #
        # LEVEL SETUP END
        #

        #
        # SIMPLE PHYSICS SETUP
        #
        #
        # BULLET
        #
        if self.useBullet:
            self.world = BulletWorld()
            self.world.setGravity(Vec3(0, 0, -9.81))

            shape = BulletPlaneShape(Vec3(0, 0, 1), 1)
            node = BulletRigidBodyNode("Ground")
            node.addShape(shape)
            node.setIntoCollideMask(BitMask32.allOn())
            np = render.attachNewNode(node)
            np.setPos(0, 0, -4)
            self.world.attachRigidBody(node)

            self.levelSolids = BulletHelper.fromCollisionSolids(self.level, True)
            for bodyNP in self.levelSolids:
                bodyNP.reparentTo(self.level)
                bodyNP.node().setDebugEnabled(False)
                if isinstance(bodyNP.node(), BulletRigidBodyNode):
                    bodyNP.node().setMass(0.0)
                    self.world.attachRigidBody(bodyNP.node())
                elif isinstance(bodyNP.node(), BulletGhostNode):
                    self.world.attachGhost(bodyNP.node())

            # show the debug geometry for bullet collisions
            self.debugactive = True
            debugNode = BulletDebugNode("Debug")
            debugNode.showWireframe(True)
            debugNode.showConstraints(True)
            debugNode.showBoundingBoxes(False)
            debugNode.showNormals(True)
            debugNP = render.attachNewNode(debugNode)
            debugNP.show()

            self.world.setDebugNode(debugNode)
            self.__taskName = "task_physicsUpdater_Bullet"
            taskMgr.add(self.updatePhysicsBullet, self.__taskName, priority=-20)
        #
        # INTERNAL
        #
        if self.useInternal:
            # enable physics
            base.enableParticles()
            base.cTrav = CollisionTraverser("base collision traverser")
            base.cTrav.setRespectPrevTransform(True)
            # setup default gravity
            gravityFN = ForceNode("world-forces")
            gravityFNP = render.attachNewNode(gravityFN)
            gravityForce = LinearVectorForce(0, 0, -9.81)  # gravity acceleration
            gravityFN.addForce(gravityForce)
            base.physicsMgr.addLinearForce(gravityForce)

            # Ground Plane
            plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, -4)))
            self.ground = render.attachNewNode(CollisionNode("Ground"))
            self.ground.node().addSolid(plane)
            self.ground.show()

            # Add moving platforms
            self.platformIntervals = []
            self.platforms = []
            self.addFloatingPlatform(0, 8.0, self.level.find("**/PlatformPos.000").getPos(), self.level.find("**/PlatformPos.001").getPos())
            self.addFloatingPlatform(1, 8.0, self.level.find("**/PlatformPos.002").getPos(), self.level.find("**/PlatformPos.003").getPos())
            self.addFloatingPlatform(2, 8.0, self.level.find("**/PlatformPos.004").getPos(), self.level.find("**/PlatformPos.005").getPos())
            self.addFloatingPlatform(3, 8.0, self.level.find("**/PlatformPos.006").getPos(), self.level.find("**/PlatformPos.007").getPos())
            # add a rotating platform that doesn't has a node in the level file
            self.addFloatingPlatform(4, 10.0, (0, -15, 0), (0, -15, 0), 0, (360, 0, 0))

            # start the intervals
            for ival in self.platformIntervals:
                ival.loop()

            # Intangible blocks (as used for example for collectible or event spheres)
            self.moveThroughBoxes = render.attachNewNode(CollisionNode("Ghosts"))
            box = CollisionBox((0, 0, 0.5), 1, 1, 1)
            box.setTangible(False)
            self.moveThroughBoxes.node().addSolid(box)
            # should only collide with the event sphere of the character
            self.moveThroughBoxes.node().setFromCollideMask(BitMask32.allOff())
            self.moveThroughBoxes.node().setIntoCollideMask(BitMask32(0x80))  # 1000 0000
            self.moveThroughBoxes.show()

            # Set the world
            self.world = base.cTrav

        #
        # PHYSICS SETUP END
        #

        #
        # DEBUGGING
        #
        # NOTE: To add output to the OSD, see debugOSDUpdater below
        #       also make sure to set on-screen-debug-enabled to #t in
        #       the loadPrcFileData call given in the upper part of
        #       this file
        from direct.showbase.OnScreenDebug import OnScreenDebug
        self.osd = OnScreenDebug()
        self.osd.enabled = True
        self.osd.append("Debug OSD\n")
        self.osd.append("Keys:\n")
        self.osd.append("escape        - Quit\n")
        self.osd.append("gamepad start - Quit\n")
        self.osd.append("F1            - Toggle Debug Mode\n")
        self.osd.append("F2            - Toggle Camera Mode\n")
        self.osd.append("R             - Reset Player\n")
        self.osd.append("P             - Toggle Pause\n")
        self.osd.load()
        self.osd.render()
        taskMgr.add(self.debugOSDUpdater, "update OSD")

        #
        # THE CHARACTER
        #
        self.p = PlayerController(self.world)
        self.p.startPlayer()
        # find the start position for the character
        startpos = self.level.find("**/StartPos").getPos()
        if USEBULLET:
            # Due to the setup and limitation of bullets collision shape
            # placement, we need to shift the character up by half its
            # height.
            startpos.setZ(startpos.getZ() + self.p.player_height/2.0)
        self.p.setStartPos(startpos)
        self.p.setStartHpr(self.level.find("**/StartPos").getHpr())

        self.pause = False

        self.p.camera_handler.centerCamera()

        # This function should be called whenever the player isn't
        # needed anymore like at an application quit method.
        #self.p.stopPlayer()

    def toggleDebug(self):
        """dis- and enable the collision debug visualization"""
        if not self.debugactive:
            if self.useBullet:
                # activate phyiscs debugging
                self.debugNP.show()
            if self.useInternal:
                self.moveThroughBoxes.show()
                self.p.charCollisions.show()
                self.p.shadowRay.show()
                self.p.charFutureCollisions.show()
                self.p.eventCollider.show()
                for rayID, ray in self.p.raylist.items():
                    ray.ray_np.show()
            self.debugactive = True
        else:
            if self.useBullet:
                # deactivate phyiscs debugging
                self.debugNP.hide()
            if self.useInternal:
                self.moveThroughBoxes.hide()
                self.p.charCollisions.hide()
                self.p.shadowRay.hide()
                self.p.charFutureCollisions.hide()
                self.p.eventCollider.hide()
                for rayID, ray in self.p.raylist.items():
                    ray.ray_np.hide()
            self.debugactive = False

    def resetPlayer(self):
        """This function simply resets the player to the start position
        and centers the camera behind him."""
        self.p.setStartPos(self.level.find("**/StartPos").getPos())
        self.p.setStartHpr(self.level.find("**/StartPos").getHpr())
        self.p.camera_handler.centerCamera()

    def pause(self):
        print("PAUSE")
        if not self.pause:
            self.togglePause()

    def togglePause(self):
        """This function shows how the app can pause and resume the
        player"""
        if self.pause:
            # to respect window size changes we reset the necessary variables
            self.p.win_width_half = base.win.getXSize() // 2
            self.p.win_height_half = base.win.getYSize() // 2

            self.p.resumePlayer()
        else:
            self.p.pausePlayer()
        self.pause = not self.pause

    def toggleCamera(self):
        """This function shows how the app can toggle the camera system
        between first and third person mode"""
        if self.p.first_pserson_mode:
            self.p.changeCameraSystem("thirdperson")
        else:
            self.p.changeCameraSystem("firstperson")

    def toggleOSD(self):
        self.osd.enabled = not self.osd.enabled
        if self.osd.onScreenText:
            if self.osd.enabled:
                self.osd.onScreenText.show()
            else:
                self.osd.onScreenText.hide()

    def debugOSDUpdater(self, task):
        """Update the OSD with constantly changing values"""
        # use self.osd.add("key", value) to add a data pair which will
        # be updated every frame
        #self.osd.add("Rotation", str(self.platforms[4].getH()))
        #self.osd.add("Speed", str(self.p.update_speed))


        #
        # GAMEPAD DEBUGGING
        #
        #gamepads = self.p.gamepad.gamepads


        #from panda3d.core import ButtonHandle
        #self.osd.add("0 - GAMEPAD:", gamepads[0].name)
        #self.osd.add("TEST STATE:", str(ButtonHandle("action_a")))
        #self.osd.add("HANDLE INDEX:", str(ButtonHandle("action_a").get_index()) + " " + str(gamepads[1].get_button_map(6).get_index()))
        #self.osd.add("STATE BY HANDLE:", str(gamepads[0].findButton(ButtonHandle("action_b")).state))
        #self.osd.add("MAP at 6:", str(gamepads[1].get_button_map(6)))
        #self.osd.add("MY MAP:", str(self.p.gamepad.deviceMap["sprint"]))
        #self.osd.add("BUTTON STATE 6:", str(gamepads[0].get_button(6).state))
        self.osd.add("stamina", "{:0.2f}".format(self.p.stamina))
        self.osd.add("velocity", "{X:0.4f}/{Y:0.4f}/{Z:0.4f}".format(
            X=self.p.actorNode.getPhysicsObject().getVelocity().getX(),
            Y=self.p.actorNode.getPhysicsObject().getVelocity().getY(),
            Z=self.p.actorNode.getPhysicsObject().getVelocity().getZ()))
        if taskMgr.hasTaskNamed(self.p.idle_to_pause_task_name):
            pause_task = taskMgr.getTasksNamed(self.p.idle_to_pause_task_name)[0]
            self.osd.add("pause in", "{:0.0f}".format(-pause_task.time))
        self.osd.add("state", "{}".format(self.p.state))
        self.osd.add("move vec", "{}".format(self.p.plugin_getMoveDirection()))

        self.osd.render()
        return task.cont

    def updatePhysicsBullet(self, task):
        """This task will handle the actualisation of
        the physic calculations each frame for the
        Bullet engine"""
        dt = globalClock.getDt()
        self.world.doPhysics(dt, 10, 1.0/180.0)
        return task.cont

    def addFloatingPlatform(self, platformID, time, platformStartPos, platformEndPos, platformStartHpr=0, platformEndHpr=0):
        # load and place the platform
        floatingPlatform = loader.loadModel("../data/level/FloatingPlatform")
        floatingPlatform.setName(floatingPlatform.getName()+str(platformID))
        floatingPlatform.setPos(platformStartPos)
        floatingPlatform.setH(platformStartHpr)
        # rename the collision object so we can determine on which platform the character landed
        fpSub = floatingPlatform.find("**/FloatingPlatform")
        fpSub.setName(fpSub.getName()+str(platformID))
        floatingPlatform.reparentTo(self.level)

        # create the platforms movement using an interval sequence
        platformIval = Sequence(
            floatingPlatform.posInterval(time, platformEndPos, name="Platform%dTo"%platformID),
            Wait(3.0),
            floatingPlatform.posInterval(time, platformStartPos, name="Platform%dFrom"%platformID),
            Wait(3.0),
            name="platform-move-interval-%d"%platformID)

        platformHprInterval = None
        if platformEndHpr != 0:
            platformHprInterval = Sequence(
                floatingPlatform.hprInterval(time, platformEndHpr, name="Platform%dRotate"%platformID),
                name="platform-hpr-interval-%d"%platformID)

        # store the platform and its interval
        self.platforms.append(floatingPlatform)
        self.platformIntervals.append(platformIval)
        if platformHprInterval is not None:
            self.platformIntervals.append(platformHprInterval)

APP = Main()
APP.run()
