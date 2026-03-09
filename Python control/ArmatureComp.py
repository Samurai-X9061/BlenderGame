import bge, bpy
from mathutils import Vector
from math import pi
from collections import OrderedDict

def clamp(x, a, b):
    return min(max(a, x), b)

class Animator(bge.types.KX_PythonComponent):
    """Attach this component to the armature of your character. It's important
    that the armature is parented with an capsule object with physics type equals
    to Character.
        This component will automatically align the armature to the move direction
    of your character, runs the right animations accordding to whether the character is walking or 
    sprinting or sliding and if the character is on air or not."""

    args = OrderedDict([
        ("Activate", True),
        
        
        ("Align To Move Direction", True),
        ("Align Smooth", 0.5),

        ("Idle Animation", bpy.types.Action), 
        ("Idle Frame Start-End", Vector([0, 10])),

        ("Walk Animation", bpy.types.Action),
        ("Walk Frame Start-End", Vector([0, 10])),

        ("Run Animation", bpy.types.Action),
        ("Run Frame Start-End", Vector([0, 10])),

        ("Slide Animation", bpy.types.Action),
        ("Slide Frame Start-End", Vector([0, 10])),

        ("Swim Animation", bpy.types.Action),
        ("Swim Frame Start-End", Vector([0, 10])),

        ("Jump Animation", bpy.types.Action),
        ("Jump Frame Start-End", Vector([0, 10])),
        ("Jump Mid-point Frame", 0),
        
        ("Jump Walk Animation", bpy.types.Action),
        ("Jump Walk Frame Start-End", Vector([0, 10])),
        ("Jump Walk Mid-point Frame", 0),
        
        ("Jump Run Animation", bpy.types.Action),
        ("Jump Run Frame Start-End", Vector([0, 10])),
        ("Jump Run Mid-point Frame", 0),
        ])

    def start(self, args):
        """Start Function"""
        self.active = args["Activate"]

        self.__lastPosition = self.object.worldPosition.copy()
        self.__moveDirection = None
        self.__alignMoveDir = args["Align To Move Direction"]
        self.alignSmooth = 1 - clamp( args["Align Smooth"], 0, 1)

        try:
            self.__animIdle = [args["Idle Animation"].name, args["Idle Frame Start-End"]]
            self.__animWalk = [args["Walk Animation"].name, args["Walk Frame Start-End"]]
            self.__animRun = [args["Run Animation"].name, args["Run Frame Start-End"]]
            self.__animSlide = [args["Slide Animation"].name, args["Slide Frame Start-End"]]
            self.__animSwim = [args["Swim Animation"].name, args["Swim Frame Start-End"]]
            if args["Jump Mid-point Frame"] == 0:
                midpIdle = int((args["Jump Frame Start-End"][0]+args["Jump Frame Start-End"][1])/2)
            else:
                midpIdle = args["Jump Mid-point Frame"]
        
            if args["Jump Walk Mid-point Frame"] == 0:
                midpWalk = int((args["Jump Walk Frame Start-End"][0]+args["Jump Walk Frame Start-End"][1])/2)
            else:
                midpWalk = args["Jump Walk Mid-point Frame"]
        
            if args["Jump Run Mid-point Frame"] == 0:
                midpRun = int((args["Jump Run Frame Start-End"][0]+args["Jump Run Frame Start-End"][1])/2)
            else:
                midpRun = args["Jump Run Mid-point Frame"]
            
            self.__animJumpUp  = [args["Jump Animation"].name, Vector([args["Jump Frame Start-End"][0],midpIdle])]
            self.__animJumpDown = [args["Jump Animation"].name, Vector([midpIdle, args["Jump Frame Start-End"][1]])]
        
            self.__animWalkJumpUp  = [args["Jump Walk Animation"].name, Vector([args["Jump Walk Frame Start-End"][0],midpWalk])]
            self.__animWalkJumpDown = [args["Jump Walk Animation"].name, Vector([midpWalk, args["Jump Walk Frame Start-End"][1]])]
        
            self.__animRunJumpUp  = [args["Jump Run Animation"].name, Vector([args["Jump Run Frame Start-End"][0],midpRun])]
            self.__animRunJumpDown = [args["Jump Run Animation"].name, Vector([midpRun, args["Jump Run Frame Start-End"][1]])]
        except:
            pass
        
        self.JumpStateUp = False  # So that jump animation is only played once 
        self.JumpStateDown = False

        self.Char = self.object.parent
        
        self.CharComp = self.Char.components["CharCont"] #Get the Main Character movement Component
        
        

        

    def __updateMoveDirection(self):
        """Updates the move direction"""
        self.__moveDirection = self.object.worldPosition - self.__lastPosition
        self.__lastPosition = self.object.worldPosition.copy()

    def __animate(self, animData, blend=4, spd = 1.0):
        """Runs an animation"""
        self.object.playAction(animData[0], animData[1][0], animData[1][1], blendin=blend, speed = spd )

    def __handleGroundAnimations(self):
        """Handles animations on ground (Walk, Run, Slide, Idle)."""
        self.JumpStateUp = False  # is not jumping 
        self.JumpStateDown = False
        if self.CharComp.onWater:  # while swimimg only walking and onWater is true
            if self.CharComp.isWalking:
                self.__animate(self.__animSwim)
        else:  # wgile on solid ground onWater is False
            if self.CharComp.isWalking:
                self.__animate(self.__animWalk)
            elif self.CharComp.isRunning:
                self.__animate(self.__animRun)
            elif self.CharComp.isSliding:
                self.__animate(self.__animSlide)
            else:
                self.__animate(self.__animIdle)

    def __handleAirAnimations(self):
        """Handles animations on air (Jump)."""

        if self.__moveDirection[2] > 0 and not self.JumpStateUp:
            self.JumpStateUp = True  # is moving upwards
            if self.CharComp.isWalking:
                self.__animate(self.__animWalkJumpUp, 5)
            elif self.CharComp.isRunning:
                self.__animate(self.__animRunJumpUp, 5)
            else:
                self.__animate(self.__animJumpUp,5)
        
        elif not self.JumpStateDown:
            self.JumpStateDown = True  # is moving downwards
            if self.CharComp.isWalking:
                self.__animate(self.__animWalkJumpDown, 5)
            elif self.CharComp.isRunning:
                self.__animate(self.__animRunJumpDown, 5)
            else:
                self.__animate(self.__animJumpDown, 5)

    def alignToMoveDirection(self):
        """Align the armature to the move direction"""

        length = self.__moveDirection.length
        if length >= 0.:
            # First checks if the move direction is the opposite of the current
            # direction. If so, applies a small rotation just to avoid a weird
            # delay that alignAxisToVect has in this case.
            vec = self.object.worldOrientation @ Vector([0,1,0])
            try:
                if vec.angle(self.__moveDirection) >= pi-0.01:
                    self.object.applyRotation([0,0,0.01], False)
            except:
                pass

            length = clamp(length*20, 0, 1) * self.alignSmooth
            self.object.alignAxisToVect(self.__moveDirection, 1, length)
            self.object.alignAxisToVect([0,0,1], 2, 1)

    def update(self):
        """Update Function"""

        self.__updateMoveDirection()

    
        if self.active:
            if self.__alignMoveDir:
                self.alignToMoveDirection()
            
            if self.CharComp.onGround():
                self.__handleGroundAnimations()
            else:
                self.__handleAirAnimations()