import bge, bpy
from collections import OrderedDict
from mathutils import Vector, Matrix
import time

class CharCont(bge.types.KX_PythonComponent):
    """ This Component is to be attached the main Character Capsule object with the armature as 
    its Child object """

    args = OrderedDict([
        ("Activate", True),
        ("Character Health", 800),
        ("Character Height", 2.0),
        ("Walk Speed", 10.0),
        ("Run Speed", 20.0),
        ("Max Jumps", 1),
        ("Jump Force", 4000.0),
        ("Character Slide", True),
        ("Slide Speed", 40.0),
        ("Make Object Invisible", True)
        
    ])

    def start(self, args):
        #Start Function

        self.active = args["Activate"]

        self.Elixer = int(0)
        self.MaxHealth = self.Health = args["Character Health"]
        self.Shield = 200
        self.hyperTime = 0.0  # Time left for hypercharge to end
        self.hyperEnd = 0.0  # End time for hypercharge
        self.multiplier = 1  # Hyper multiplier
        self.Weapon = {"Sword": 1}  # 0-not unlocked 1_onwards-unlocked levels
        self.sword = self.object.children["Albedo"].children["WeaponGuide"]
        self.lastAttacked = 0
        self.keysHolding = []

        self.walkSpeed = args["Walk Speed"]
        self.runSpeed = args["Run Speed"]
        self.isWalking = False
        self.isRunning = False
        self.onWater = False
        self.__shiftkeystatus = False

        self.jumpForce = args["Jump Force"]
        self.charslide = args["Character Slide"]
        self.slideSpeed = args["Slide Speed"]
        self.isSliding = False
        self.__slideStop = 0.0
        self.__height = args["Character Height"]
        self.__lastframeTime = time.time()
        self.__deltaTime = 0.0

        if self.active:
            if args["Make Object Invisible"]:
                self.object.visible = False
            self.sword.children["SwordSmall"].visible = False
            self.sword.children["SwordBig"].visible = False

    def onGround(self, normal=False):
        own = self.object
        end = own.worldPosition + (own.worldOrientation.col[2] * -(self.__height*.5))
        ray = own.rayCast(end,own.worldPosition,0,"",0,0,0)
        if ray[0] and "Pond" in ray[0]:  # to prevent any other actions while swimming
            self.onWater = True  # as the pond or ocean shud have "pond" property
            self.isRunning = False
            self.__shiftkeystatus = False
            self.isSliding = False
        else: self.onWater = False
        if normal:
            return ray
        else:
            return bool(ray[0])

    def servoMotion(self, move: Vector, speed: float):
        #move = motion vector & speed = manVelocity
        ray = self.onGround(True)  # get raycast to land
        self.object["Ray"] = bool(ray[0])
        if self.object["Ray"]:
            localNorm = self.object.worldTransform.inverted().transposed() @ Vector(ray[2])  # make it local space
            dir = localNorm.cross(Vector([1,0,0]))  # cross product gives y vector facing forward based on the land slope
            dir.normalize()
            vel = (move.y*speed)-self.object.localLinearVelocity.y #Calibration for velocity
            force_y = dir*vel*5000*self.__deltaTime

            dir = Vector([0,1,0]).cross(localNorm)  # cross product gives x vector facing right based on the land slope
            dir.normalize()
            vel = (move.x*speed)-self.object.localLinearVelocity.x
            force_x = dir*vel*5000*self.__deltaTime

            self.object.applyForce((force_x + force_y), 1)  # apply force to move the character

    def characterMovement(self):
        #Makes the character walk with W,A,S,D
        #(You can run by holding Left Shift)

        keyboard = bge.logic.keyboard.inputs
        keyRel = bge.logic.KX_INPUT_JUST_RELEASED
        x = 0
        y = 0

        if not self.isSliding:

            if keyboard[bge.events.WKEY].active:   y = 1
            elif keyboard[bge.events.SKEY].active: y = -1
            if keyboard[bge.events.AKEY].active:   x = -1
            elif keyboard[bge.events.DKEY].active: x = 1

            if not(abs(y) or abs(x)):
                self.isWalking = False
            elif not (self.isRunning or self.isSliding):
                self.isWalking = True

            #For character sprinting
            if keyboard[bge.events.LEFTSHIFTKEY].active and (y == 1) and (self.__shiftkeystatus == False):
                self.isRunning = True #shift is pressed when moving forward
            elif (keyRel in keyboard[bge.events.LEFTSHIFTKEY].queue) and (self.__shiftkeystatus == False):
                self.__shiftkeystatus = True #If user has release shift key

            if keyboard[bge.events.LEFTSHIFTKEY].active and (self.__shiftkeystatus == True):
                self.isRunning = False #If shift is pressed again
            if (keyRel in keyboard[bge.events.LEFTSHIFTKEY].queue) and (self.__shiftkeystatus == True):
                self.__shiftkeystatus = False #If shift has been released again


            #Assign move dir and speed depending on whether sprinting or not
            if self.onWater or not self.isRunning:
                vec = Vector([x, y, 0]) 
                speed = self.walkSpeed
            else: 
                vec = Vector([0, 1, 0])
                speed = self.runSpeed

            if vec.length != 0:
                # Normalizing the vector.
                vec.normalize()
            self.servoMotion(vec, speed*self.multiplier)

    def characterJump(self):
        #Makes the Character jump with SPACE.

        keyboard = bge.logic.keyboard.inputs
        keyTAP = bge.logic.KX_INPUT_JUST_ACTIVATED

        if keyTAP in keyboard[bge.events.SPACEKEY].queue:
            self.object.applyForce([0,0,self.jumpForce], 1)

    def slide(self):
        # Makes the character slide when activated by X key
        xkey = bge.logic.keyboard.inputs[bge.events.XKEY]
        if self.charslide:
            if xkey.active and not self.isSliding:
                self.isSliding = True
                self.__slideStop = round(time.time(), 1) + 1
            elif (self.__slideStop - round(time.time(), 1)) <= 0:
                self.isSliding = False

            if self.isSliding:
                self.servoMotion(Vector([0, 1, 0]), self.slideSpeed)

    def damage(self, dmg=0, perDmg=False, permaxHealth=False):
        '''dmg = amount of damage done; perDmg = Whether to infinct 
        damage based on dmg's value or dmg percent of health;
        permaxHeath = If health considered for damage is object max health 
        or present health.'''
        if self.Health>=0:
            if perDmg:
                if permaxHealth:
                    dmg = (self.MaxHealth*dmg/100)
                else:
                    dmg = (self.Health*dmg/100)
            extra = self.Shield - dmg
            if extra > 0:
                self.Shield -= dmg
            else:
                self.Shield = 0
                self.Health += extra

            if self.Health < 0:
                self.Health = 0

    def heal(self, heal=0, perHeal=False, permaxHealth=False):
        '''heal = amount of healing done; perHeal = Whether to heal based 
        on dmg's value or dmg percent of health; permaxHeath = If health 
        considered for healing is object max health  or present health.'''
        if self.Health <= self.MaxHealth:
            if perHeal:
                if permaxHealth:
                    health = self.MaxHealth
                else:
                    health = self.Health
                self.Health += int(health*heal/100)
            else:
                self.Health += heal

            if self.Health > self.MaxHealth:
                self.Health = self.MaxHealth

    def hyperCharge(self):  # The hypercharge function
        vkey = bge.logic.keyboard.inputs[bge.events.VKEY]
        if vkey.active and not (self.hyperTime):
            if self.Elixer >= 50:
                self.hyperEnd = round(time.time(), 2) + 10
                self.hyperTime = 8
                self.heal(20, 1, 1)
                self.Elixer -= 50  # Charge 50 elixer
        elif self.hyperTime:
            self.multiplier = 2
            # increase damage 
            self.hyperTime = self.hyperEnd - round(time.time(), 2)
            if self.hyperTime <= 0:  # Calculate time left and deal with it
                self.hyperTime = 0

        else:
            self.multiplier = 1

    def attack(self):
        if self.Weapon["Sword"] == 1 and self.sword.children["SwordSmall"].visible == False:
            self.sword.children["SwordSmall"].visible = True
            self.sword.children["SwordBig"].visible = False
        elif self.Weapon["Sword"] == 2 and self.sword.children["SwordBig"].visible == False:
            self.sword.children["SwordBig"].visible = True
            self.sword.children["SwordSmall"].visible = False
        lmb = bge.logic.mouse.inputs[bge.events.LEFTMOUSE]
        cooldown = time.time() - self.lastAttacked
        if lmb.active and cooldown >= 1.5:
            self.lastAttacked = time.time()
            self.object.children["Albedo"].playAction("swordslash", 1, 39, layer=1,\
                                         priority=1, layer_weight=0.3, blendin=4)

        if self.object.children["Albedo"].isPlayingAction(1) and cooldown >= 1.5:  # attack animation is running
            if self.Weapon["Sword"] == 1:
                rng = 2
                damage = 100
            elif self.Weapon["Sword"] == 2:
                rng = 4
                damage = 300
            ray_start = self.sword.worldPosition
            ray_end = self.sword.worldPosition + self.sword.worldOrientation.col[2] * rng

            # Perform ray casting to detect hits on the sword
            ray = self.object.rayCast(ray_end, ray_start, 0, "Enemy", 0, 1, 0)

            if ray[0] and (time.time() - ray[0]["LastHit"]) >= 1:
                ray[0]["Health"] -= damage*self.multiplier
                ray[0]["LastHit"] = time.time()

    def update(self):
        # Update Function"""
        if self.active:
            self.__deltaTime = time.time() - self.__lastframeTime
            self.__lastframeTime = time.time()
            self.characterMovement()
            if not self.onWater:  # these actions only work on ground
                self.hyperCharge()
                if not (self.isSliding):
                    self.characterJump()
                if not self.isRunning and self.onGround():
                    self.slide()
                    self.attack()

