#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# PANDA3D ENGINE IMPORTS
#
from direct.interval.LerpInterval import LerpFunc
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait

import logging

__author__ = "Fireclaw the Fox"
__license__ = """
Simplified BSD (BSD 2-Clause) License.
See License.txt or http://opensource.org/licenses/BSD-2-Clause for more info
"""


#
# ANIMATION FSM HANDLER
#
class Animator:
    """
    This class is responsible for playing animations and easing between
    them. It also throws the events usable for playing some audio.
    """
    def __init__(self):
        self.current_animations = []
        self.pre_jump_state = self.STATE_IDLE
        self.pre_pause_anim = self.IDLE
        self.pre_pause_frame = 0
        self.current_seq = None
        self.pause_from_idle_task = None

        self.skip_play_rate_changes = [self.IDLE]

        self.ease_in_idle = self.createEaseIn(self.IDLE)
        self.ease_out_idle = self.createEaseOut(self.IDLE)

        self.ease_in_walk = self.createEaseIn(self.WALK)
        self.ease_out_walk = self.createEaseOut(self.WALK)

        self.ease_in_run = self.createEaseIn(self.RUN)
        self.ease_out_run = self.createEaseOut(self.RUN)

        self.ease_in_sprint = self.createEaseIn(self.SPRINT)
        self.ease_out_sprint = self.createEaseOut(self.SPRINT)

        self.ease_out_jump = self.createEaseOut(self.JUMP_START)
        self.ease_out_fall = self.createEaseOut(self.FALL)
        self.ease_out_land = self.createEaseOut(self.JUMP_LAND)

    def createEaseIn(self, anim):
        return LerpFunc(
            self.__easeAnimation,
            fromData=0,
            toData=1,
            blendType="easeIn",
            extraArgs=[anim])

    def createEaseOut(self, anim):
        return LerpFunc(
            self.__easeAnimation,
            fromData=1,
            toData=0,
            blendType="easeOut",
            extraArgs=[anim])

    def pauseAnimator(self):
        self.pre_pause_anim = self.getCurrentAnim()
        self.pre_pause_frame = self.getCurrentFrame(self.pre_pause_anim)
        if self.current_seq:
            self.current_seq.pause()
        # stop the current running animation
        self.stop()

    def resumeAnimator(self):
        if self.pre_pause_frame is None: self.pre_pause_frame = 0
        if self.pre_pause_anim is None: self.pre_pause_anim = self.IDLE
        self.pose(self.pre_pause_anim, self.pre_pause_frame)
        self.loop(self.pre_pause_anim, restart = False)
        if self.current_seq:
            if self.current_seq.getState() != Sequence.SFinal:
                self.current_seq.resume()

    def cleanup(self):
        if self.pause_from_idle_task is not None:
            taskMgr.remove(self.pause_from_idle_task)

    def __easeAnimation(self, t, anim):
        self.setControlEffect(anim, t)

    def setCurrentAnimsPlayRate(self, rate):
        """Set the play rate of the current playing animations to rate"""
        for anim in self.current_animations:
            if anim in self.skip_play_rate_changes:
                continue
            self.setPlayRate(rate, anim)
            base.messenger.send(self.getConfig("audio_set_walk_playrate_evt"), [rate])

    def tryRequest(self, state):
        if self.state != self.STATE_JUMP and not self.isInTransition():
            if not self.state == state:
                try:
                    self.request(state)
                except:
                    logging.exception("======== EXCEPTION! ========")
                    logging.exception("requested invalid state {} while in {}".format(state, self.state))

    def startCurSeq(self, animFrom, animTo, easeIn, easeOut, finalState):
        if self.current_seq != None:
            self.current_seq.finish()
        self.current_seq = Sequence(
            Func(self.enableBlend),
            Func(self.loop, animTo),
            Parallel(
                easeOut,
                easeIn),
            Func(self.stop, animFrom),
            Func(self.disableBlend),
            Func(self.tryRequest, finalState))
        self.current_seq.start()

    def endCurSeq(self):
        if self.current_seq is not None:
            self.current_seq.finish()
            self.current_seq = None

    #
    # FSM PART START
    #
    #
    # NORMAL MOVEMENT STATES
    #
    def enterIdle(self):
        base.messenger.send(self.getConfig("audio_stop_walk_evt"))
        self.current_animations = [self.IDLE]
        if not self.getCurrentAnim() == self.IDLE:
            self.loop(self.IDLE)

        self.pause_from_idle_task = taskMgr.doMethodLater(
            self.getConfig("idle_to_pause_time"),
            base.messenger.send,
            self.getConfig("idle_to_pause_task_name"),
            extraArgs=[self.getConfig("idle_to_pause_event_name")])

    def exitIdle(self):
        taskMgr.remove(self.pause_from_idle_task)

    def enterWalk(self):
        self.current_animations = [self.WALK]
        if not self.getCurrentAnim() == self.WALK:
            self.loop(self.WALK)

    def enterRun(self):
        self.current_animations = [self.RUN]
        if not self.getCurrentAnim() == self.RUN:
            self.loop(self.RUN)

    def enterSprint(self):
        self.current_animations = [self.SPRINT]
        if not self.getCurrentAnim() == self.SPRINT:
            self.loop(self.SPRINT)

    def enterIdleToWalk(self):
        base.messenger.send(self.getConfig("audio_play_walk_evt"))
        self.current_animations = [self.IDLE, self.WALK]
        self.ease_out_idle.duration = self.getConfig("enter_walk_duration")
        self.ease_in_walk.duration = self.getConfig("enter_walk_duration")
        self.startCurSeq(self.IDLE, self.WALK, self.ease_in_walk, self.ease_out_idle, self.STATE_WALK)
    def exitIdleToWalk(self):
        self.stop(self.IDLE)
        self.endCurSeq()

    def enterIdleToRun(self):
        base.messenger.send(self.getConfig("audio_play_run_evt"))
        self.current_animations = [self.IDLE, self.RUN]
        self.ease_out_idle.duration = self.getConfig("enter_run_duration")
        self.ease_in_run.duration = self.getConfig("enter_run_duration")
        self.startCurSeq(self.IDLE, self.RUN, self.ease_in_run, self.ease_out_idle, self.STATE_RUN)
    def exitIdleToRun(self):
        self.stop(self.IDLE)
        self.endCurSeq()

    def enterIdleToSprint(self):
        base.messenger.send(self.getConfig("audio_play_sprint_evt"))
        self.current_animations = [self.IDLE, self.SPRINT]
        self.ease_out_idle.duration = self.getConfig("enter_sprint_duration")
        self.ease_in_sprint.duration = self.getConfig("enter_sprint_duration")
        self.startCurSeq(self.IDLE, self.SPRINT, self.ease_in_sprint, self.ease_out_idle, self.STATE_SPRINT)
    def exitIdleToSprint(self):
        self.stop(self.IDLE)
        self.endCurSeq()

    def enterWalkToIdle(self):
        base.messenger.send(self.getConfig("audio_play_walk_evt"))
        self.current_animations = [self.WALK, self.IDLE]
        self.ease_out_walk.duration = self.current_accleration/self.current_max_accleration
        self.ease_in_idle.duration = self.current_accleration/self.current_max_accleration
        self.startCurSeq(self.WALK, self.IDLE, self.ease_in_idle, self.ease_out_walk, self.STATE_IDLE)
    def exitWalkToIdle(self):
        self.stop(self.WALK)
        self.endCurSeq()

    def enterWalkToRun(self):
        base.messenger.send(self.getConfig("audio_play_run_evt"))
        self.current_animations = [self.WALK, self.RUN]
        self.ease_in_run.duration = self.getConfig("enter_run_duration")
        self.ease_out_walk.duration = self.getConfig("enter_run_duration")
        self.startCurSeq(self.WALK, self.RUN, self.ease_in_run, self.ease_out_walk, self.STATE_RUN)
    def exitWalkToRun(self):
        self.stop(self.WALK)
        self.endCurSeq()

    def enterRunToIdle(self):
        self.current_animations = [self.RUN, self.IDLE]
        self.ease_out_run.duration = self.current_accleration/self.current_max_accleration
        self.ease_in_idle.duration = self.current_accleration/self.current_max_accleration
        self.startCurSeq(self.RUN, self.IDLE, self.ease_in_idle, self.ease_out_run, self.STATE_IDLE)
    def exitRunToIdle(self):
        self.stop(self.RUN)
        self.endCurSeq()

    def enterRunToWalk(self):
        base.messenger.send(self.getConfig("audio_play_walk_evt"))
        self.current_animations = [self.RUN, self.WALK]
        self.ease_in_walk.duration = self.getConfig("enter_walk_duration")
        self.ease_out_run.duration = self.getConfig("enter_walk_duration")
        self.startCurSeq(self.RUN, self.WALK, self.ease_in_walk, self.ease_out_run, self.STATE_WALK)
    def exitRunToWalk(self):
        self.stop(self.RUN)
        self.endCurSeq()

    def enterRunToSprint(self):
        base.messenger.send(self.getConfig("audio_play_sprint_evt"))
        self.current_animations = [self.RUN, self.SPRINT]
        self.ease_in_sprint.duration = self.getConfig("enter_sprint_duration")
        self.ease_out_run.duration = self.getConfig("enter_sprint_duration")
        self.startCurSeq(self.RUN, self.SPRINT, self.ease_in_sprint, self.ease_out_run, self.STATE_SPRINT)
    def exitRunToSprint(self):
        self.stop(self.RUN)
        self.endCurSeq()

    def enterSprintToIdle(self):
        self.current_animations = [self.SPRINT, self.IDLE]
        self.ease_out_sprint.duration = self.current_accleration/self.current_max_accleration
        self.ease_in_idle.duration = self.current_accleration/self.current_max_accleration
        self.startCurSeq(self.SPRINT, self.IDLE, self.ease_in_idle, self.ease_out_sprint, self.STATE_IDLE)
    def exitSprintToIdle(self):
        self.stop(self.SPRINT)
        self.endCurSeq()

    def enterSprintToRun(self):
        base.messenger.send(self.getConfig("audio_play_run_evt"))
        self.current_animations = [self.WALK, self.RUN]
        self.ease_in_run.duration = self.getConfig("enter_run_duration")
        self.ease_out_sprint.duration = self.getConfig("enter_run_duration")
        self.startCurSeq(self.SPRINT, self.RUN, self.ease_in_run, self.ease_out_sprint, self.STATE_RUN)
    def exitSprintToRun(self):
        self.stop(self.SPRINT)
        self.endCurSeq()

    def enterJump(self):
        base.messenger.send(self.getConfig("audio_stop_walk_evt"))
        base.messenger.send(self.getConfig("audio_play_jump_evt"))
        self.current_animations = [self.JUMP_START]
        if not self.getCurrentAnim() == self.JUMP_START:
            self.current_seq = Sequence(
                self.actorInterval(self.JUMP_START, False),
                Func(self.tryRequest, self.STATE_FALL))
            self.current_seq.start()
    def exitJump(self):
        self.endCurSeq()

    def enterFall(self):
        base.messenger.send(self.getConfig("audio_stop_walk_evt"))
        base.messenger.send(self.getConfig("audio_play_fall_evt"))
        if self.getCurrentAnim() != self.FALL and self.getCurrentAnim() != self.JUMP_START:
            self.loop(self.FALL)

    def enterLand(self):
        base.messenger.send(self.getConfig("audio_play_land_evt"))
        self.current_animations = [self.JUMP_LAND]
        next_state = self.STATE_IDLE
        if self.pre_jump_state == self.STATE_RUN \
        or self.pre_jump_state == self.STATE_IDLE_TO_RUN \
        or self.pre_jump_state == self.STATE_WALK_TO_RUN:
            self.LandToRun()
        elif self.pre_jump_state == self.STATE_WALK \
        or self.pre_jump_state == self.STATE_IDLE_TO_WALK \
        or self.pre_jump_state == self.STATE_RUN_TO_WALK:
            self.LandToWalk()
        else:
            self.current_seq = Sequence(
                self.actorInterval(self.JUMP_LAND, False),
                Func(self.tryRequest, self.STATE_IDLE))
            self.current_seq.start()
    def exitLand(self):
        self.ease_in_walk.duration = self.getConfig("enter_walk_duration")
        self.ease_in_run.duration = self.getConfig("enter_run_duration")
        self.endCurSeq()

    def LandToWalk(self):
        base.messenger.send(self.getConfig("audio_play_walk_evt"))
        self.current_animations = [self.JUMP_LAND, self.WALK]
        self.ease_out_land.duration = 0.5
        self.ease_in_walk.duration = 0.5
        self.startCurSeq(self.JUMP_LAND, self.WALK, self.ease_in_walk, self.ease_out_land, self.STATE_WALK)

    def LandToRun(self):
        base.messenger.send(self.getConfig("audio_play_run_evt"))
        self.current_animations = [self.JUMP_LAND, self.RUN]
        self.ease_out_land.duration = 0.25
        self.ease_in_run.duration = 0.25
        self.startCurSeq(self.JUMP_LAND, self.RUN, self.ease_in_run, self.ease_out_land, self.STATE_RUN)

    def LandToSprint(self):
        base.messenger.send(self.getConfig("audio_play_sprint_evt"))
        self.current_animations = [self.JUMP_LAND, self.SPRINT]
        self.ease_out_land.duration = 0.25
        self.ease_in_sprint.duration = 0.25
        self.startCurSeq(self.JUMP_LAND, self.SPRINT, self.ease_in_sprint, self.ease_out_land, self.STATE_SPRINT)
