import bge
import bpy
from collections import OrderedDict
from mathutils import Vector, Euler, bvhtree
from uplogic.nodes.logictree import ULLogicTree
import json
import time
import random


class MainCont(bge.types.KX_PythonComponent):

    args = OrderedDict([
        ("Activate", True),
        ("AutoSave", True),
        ("Overlays", True),
        ("Overlay Collection", bpy.types.Collection),
        ("OverlayCam", bpy.types.Object),
        ("Pond Anim", False),
        ("SaveFrequency(s)", 30),
        ("MaxTimeLimit(s)", 1200),
        ("HealRange", 30.0),
        ("InteractionRange", 2.0),
        ("ElixerSpawnRate", 10)
    ])

    def formatTime(self, data, mode: bool):  
        ''' mode = False is string to time and True is time to string '''
        if mode:
            minutes = int(data//60)
            if minutes < 10:
                minutes = '0' + str(minutes)
            else:
                minutes = str(minutes)
            sec = int(data%60)
            if sec < 10:
                sec = '0' + str(sec)
            else:
                sec = str(sec)
            return (minutes + ':' + sec)
        else:
            return (int(data[0:2])*60 + int(data[3:]))

    def addObject(self, obj, refObj: bge.types.KX_GameObject, save = True):
        if isinstance(obj, bge.types.KX_GameObject):  # by game object
            game_obj = obj.blenderObject.copy()
            name = obj.name
        elif isinstance(obj, str):  #index by string
            game_obj = bpy.data.objects[obj].copy()
            name = obj
        else:  # by blender object
            game_obj = obj.copy()
            name = obj.name
        bpy.data.collections["GameScene"].objects.link(game_obj)# Link to the GameScene collection which contains
        game_obj = self.__scene.convertBlenderObject(game_obj)  # all objects that should be paused when the game is paused
        game_obj.worldPosition = refObj.worldPosition
        game_obj["Original"] = name  # add original property to store the name of the original object 
        if save:
            game_obj["Save"] = True  # for savegame feature
        return game_obj

    def autoSave(self):
        health = self.CharCont.Health
        shield = self.CharCont.Shield
        elixer = self.CharCont.Elixer
        weapon = json.dumps(self.CharCont.Weapon)
        kills = self.object["KillC"]
        deaths = self.deathC

        KeysHolding = []
        for key in self.CharCont.keysHolding:
            KeysHolding.append(key.name)
        KeysHolding = json.dumps(KeysHolding)

        KeysDeposited = []
        for key in self.depositedKeys:
            KeysDeposited.append(key.name)
        KeysDeposited = json.dumps(KeysDeposited)

        ElapsedTime = self.timeElapsed

        curr_time = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
        # Create a dictionary to store
        objectinfo = {"Objects": [], "Spotlist": [], "KeySpots": {}}
        for i in self.spotlist:  # Storing all the unused spots
            objectinfo["Spotlist"].append(i.name)  
        for i in self.keyspots:  # Storing them in KeyName: SpawnPointName format
            objectinfo["KeySpots"][i] = self.keyspots[i].name

        for obj in self.__scene.objects:
            if "Save" in obj:  # property for location save is existing
                props = obj.getPropertyNames()
                prop_list = []
                for prop in props:
                    if prop not in ['NodeTree', 'path', 'waiting']:  # path and waiting is for pathfinding 
                        if isinstance(obj[prop], ULLogicTree):
                            continue
                        if isinstance(obj[prop], Vector):
                            continue
                        prop_set = {}
                        prop_set['name'] = prop
                        prop_set['value'] = obj[prop]
                        prop_list.append(prop_set)
                loc = obj.worldPosition
                rot = obj.worldOrientation.to_euler()
                sca = obj.worldScale

                if obj.mass:  # Dynamic objects
                    lin_vel = obj.worldLinearVelocity
                    ang_vel = obj.worldAngularVelocity

                    objectinfo["Objects"].append(
                        {
                            'name': obj.blenderObject.name,
                            'collection': obj.blenderObject.users_collection[0].name,
                            'visible': obj.visible,
                            'type': 'dynamic',
                            'data': {
                                'worldPosition': {
                                    'x': loc.x,
                                    'y': loc.y,
                                    'z': loc.z
                                },
                                'worldOrientation': {
                                    'x': rot.x,
                                    'y': rot.y,
                                    'z': rot.z
                                },
                                'worldLinearVelocity': {
                                    'x': lin_vel.x,
                                    'y': lin_vel.y,
                                    'z': lin_vel.z
                                },
                                'worldAngularVelocity': {
                                    'x': ang_vel.x,
                                    'y': ang_vel.y,
                                    'z': ang_vel.z
                                },
                                'worldScale': {'x': sca.x, 'y': sca.y, 'z': sca.z},
                                'props': prop_list
                            }
                        }
                    )

                else:  # Static obj
                    objectinfo["Objects"].append(
                        {
                            'name': obj.blenderObject.name,
                            'collection': obj.blenderObject.users_collection[0].name,
                            'visible': obj.visible,
                            'type': 'static',
                            'data': {
                                'worldPosition': {
                                    'x': loc.x,
                                    'y': loc.y,
                                    'z': loc.z
                                },
                                'worldOrientation': {
                                    'x': rot.x,
                                    'y': rot.y,
                                    'z': rot.z
                                },
                                'worldScale': {'x': sca.x, 'y': sca.y, 'z': sca.z},
                                'props': prop_list
                            }
                        }
                    )

        self.globalDict["ID"] = curr_time
        data = (curr_time, health, shield, elixer, weapon, kills, deaths, KeysHolding,
                KeysDeposited, ElapsedTime, json.dumps(objectinfo), self.globalDict["SaveSlot"])
        self.cursor.execute(self.saveStatement.format(*data))  # create query to deposit data
        self.conn.commit()

    def __startGame(self):
        # To place character in correct position
        self.Character.worldOrientation = self.object.worldOrientation
        self.Character.worldPosition = self.object.worldPosition + Vector([0, -1.5, 1])
        self.Overlay.dispPauseNote(self.introNote)
        for i in self.keys:  # Select the 8 spots to place keys
            self.keyspots[i] = self.spotlist.pop(random.randint(0, len(self.spotlist)-1))
            self.keyspots[i]["Active"] = True  # Tested using property sensor to run the enemy spawn script
            self.keyspots[i]["KeyName"] = i # Store data on which key is it
            self.spawnKeys[i] = self.addObject(self.keys[i], self.keyspots[i])
            self.spawnKeys[i].worldPosition += Vector([0,0,1])
            self.spawnKeys[i].visible = True
            self.spawnKeys[i]["NotCollected"] = True  # For adding to spawn keys list on game reload
        for i in self.spotlist:
            i.visible = False
        if self.autosv:
            self.autoSave()

    def __get_game_vec(self, data):
        return Vector((data['x'], data['y'], data['z']))

    def __loadGame(self):
        self.cursor.execute("SELECT * FROM saves WHERE Slot = {0}".format(self.globalDict["SaveSlot"]))
        query = self.cursor.fetchall()[0]  # First tuple returned (it returns a list of tuples)
        self.CharCont.Health = int(query[3])
        self.CharCont.Shield = int(query[4])
        self.CharCont.Elixer = int(query[5])
        self.CharCont.Weapon = json.loads(query[6])
        self.object["KillC"] = int(query[7])
        self.deathC = int(query[8])
        keys = json.loads(query[9])
        for key in keys:
            self.CharCont.keysHolding.append(self.keys[key])
        keys = json.loads(query[10])
        for key in keys:
            self.depositedKeys.append(self.keys[key])
        # Deal with elapsed time
        self.timeElapsed = query[11]
        self.startTime = self.__currtime - self.formatTime(self.timeElapsed, False)

        data = json.loads(query[12])
        nameslist = []  # object names list
        for obj in data["Objects"]:  # Load obj data
            nameslist.append(obj['name'])
            if obj['name'] in self.__scene.objects:  # for original objects
                game_obj = self.__scene.objects[obj['name']]

            else:  # for Cloned objs having the Original property
                for prop in obj["data"]['props']:
                    if prop["name"] == 'Original':
                        original = prop['value']
                        break
                if len(bpy.data.objects[original].children) == 0:  # if obj has no children
                    game_obj = bpy.data.objects[original].copy()
                    game_obj.name = obj['name']  # Creating a new object to load the spawnable
                    bpy.data.collections[obj['collection']].objects.link(game_obj)
                    game_obj = self.__scene.convertBlenderObject(game_obj)
                else:  # use slower function to clone all children too
                    game_obj = self.__scene.addObject(original, self.object)
                    game_obj.blenderObject.name = obj['name']

            game_obj.visible = obj['visible']

            wPos = self.__get_game_vec(obj['data']['worldPosition'])
            wOri = Euler(self.__get_game_vec(obj['data']['worldOrientation']))
            wSca = self.__get_game_vec(obj['data']['worldScale'])

            game_obj.worldPosition = wPos
            game_obj.worldOrientation = wOri.to_matrix()
            game_obj.worldScale = wSca

            if obj['type'] == 'dynamic':  # set Phy data
                linVel = self.__get_game_vec(
                    obj['data']['worldLinearVelocity']
                )
                angVel = self.__get_game_vec(
                    obj['data']['worldAngularVelocity']
                )
                game_obj.worldLinearVelocity = linVel
                game_obj.worldAngularVelocity = angVel

            for prop in obj['data']['props']:  # load properties
                game_obj[prop['name']] = prop['value']

                # Load the list of spawned Keys
                if prop["name"] == "NotCollected":
                    self.spawnKeys[original] = game_obj

        for obj in self.__scene.objects:  # To delete object that dont exist in the save
            if (obj.blenderObject.name not in nameslist) and ("Save" in obj):
                obj.endObject()  # Use blendName for uniqueness
        for i in self.spotlist:
            if i.name not in data["Spotlist"]:
                self.spotlist.remove(i)
        for i in data["KeySpots"]:
            self.keyspots[i] = self.__scene.objects[data["KeySpots"][i]]

        self.__scene.objects["PhysicsMesh"].reinstancePhysicsMesh(evaluated=True)
        self.__scene.objects["Tree Phy"].reinstancePhysicsMesh(evaluated=True)
        self.Overlay.dispPauseNote("Loaded from save of slot {} saved at {}".format(query[0],query[1]))

    def start(self, args):

        self.active = args["Activate"]
        self.globalDict = bge.logic.globalDict
        self.autosv = args["AutoSave"] and self.globalDict["AutoSave"]
        self.saveFreq = args["SaveFrequency(s)"]
        self.__scene = bge.logic.getCurrentScene()
        if self.autosv:
            self.conn = bge.logic.globalDict["Conn"]
            self.cursor = bge.logic.globalDict["Cursor"]
            self.cursor.execute("SELECT Name, Value FROM records WHERE Value is NOT NULL")
            self.reclist = self.cursor.fetchall()

        self.deathC = 0
        self.object["KillC"] = 0  # Can asign to be a property or something
        self.depositedKeys = []
        self.justStarted = True
        self.maxTime = args["MaxTimeLimit(s)"]
        self.timeElapsed = "00:00"
        self.startTime = time.time()  # time the game was started
        self.__currtime = time.time()
        self.pauseTimeTotal = 0  # Total time elapsed in paused state
        self.pauseStartTime = 0  # time at which game was paused
        self.keys = {"Insidious": self.__scene.objects["Insidious"],
                     "Avalanche": self.__scene.objects["Avalanche"],
                     "Amethyst": self.__scene.objects["Amethyst"],
                     "Venom": self.__scene.objects["Venom"],
                     "Raven": self.__scene.objects["Raven"],
                     "Scorch": self.__scene.objects["Scorch"],
                     "Ember": self.__scene.objects["Ember"],
                     "Dartarix": self.__scene.objects["Dartarix"]}  # Dict of keys
        self.keyspots = {}  # Dict of spawn point that have keys placed in them
        self.spotlist = [self.__scene.objects["Point1"],
                         self.__scene.objects["Point2"],
                         self.__scene.objects["Point3"],
                         self.__scene.objects["Point4"],
                         self.__scene.objects["Point5"],
                         self.__scene.objects["Point6"],
                         self.__scene.objects["Point7"],
                         self.__scene.objects["Point8"],
                         self.__scene.objects["Point9"],
                         self.__scene.objects["Point10"],
                         self.__scene.objects["Point11"],
                         self.__scene.objects["Point12"],
                         self.__scene.objects["Point13"],
                         self.__scene.objects["Point14"],
                         self.__scene.objects["Point15"],
                         self.__scene.objects["Point16"]]  # list of spawn point object to spawn keys
        self.spawnKeys = {}  # dict of spawned key objects

        self.healRange = args["HealRange"]  # Range in which the altar heals
        self.interactionRange = args["InteractionRange"]
        self.pondanim = args["Pond Anim"]
        self.__lastHeal = 0.0
        self.__altarView = False
        self.fstate = False
        self.__lastElixer = 0  # last time elixer spawnign was conducted
        self.__elixerSpawnRate = args["ElixerSpawnRate"]
        self.__currtime = time.time()

        self.altarCam = self.__scene.objects["AltarCam"]
        self.Character = self.__scene.objects["Character"]
        self.Character.suspendPhysics()
        self.CharCont = self.Character.components["CharCont"]
        self.gameCam = self.__scene.active_camera
        self.TPVCont = self.gameCam.components["ThirdPersonCamera"]
        self.Animator = self.Character.children["Albedo"].components["Animator"]
        self.ovrlCam = self.object.scene.getGameObjectFromObject(args["OverlayCam"])
        self.ovrlColn = args["Overlay Collection"]
        self.Overlay = self.__scene.objects["OverlayCam"].components["Overlay"]

        self.saveStatement = '''UPDATE Saves
                                SET ID = '{}', 
                                    Health = {},
                                    Shield = {},
                                    Elixer = {},
                                    Weapon = '{}',
                                    Kills = {},
                                    Deaths = {},
                                    KeysHold = '{}',
                                    KeysDep = '{}',
                                    ElapsedT = '{}',
                                    ObjData = '{}'
                                WHERE Slot = {}'''
        self.lastSaved = time.time()

        self.introNote = '''800 years ago a great mage had sealed the evil power\n
                            of the Negacius. Recently the greed of human has lead\n
                            to the unsealing of this evil force which has lead to the\n 
                            destruction of this world and the draining of life force\n of 
                            all living organisms, it is up to you to collect the 8 keys\n of
                            sealing that have been hidden in this secret mountain\n region of 
                            Darzentius and activate the sealing artifact before\n Negacius's 
                            will consumes your life force in 20 minutes.\n Remember each key 
                            is going to be guarded by negacius's beasts and\n the altar only 
                            has enough power to revive you 5 more times\n so be wary of them. 
                            Good Luck'''

    def reLoadSave(self, newSlot):
        if self.autosv:
            self.cursor.execute("UPDATE saves SET Active = False")
            self.cursor.execute("UPDATE saves SET Active = True WHERE Slot = {0}".format(newSlot))
            self.conn.commit()
        bge.logic.restartGame()

    def getSavesList(self):
        if not hasattr(self, "SaveList"):
            self.cursor.execute("SELECT Slot, ID, Health, ElapsedT, Kills, Deaths, KeysDep FROM Saves WHERE Slot != {} ORDER BY Slot".format(bge.logic.globalDict["SaveSlot"]))
            self.SaveList = self.cursor.fetchall()
        return self.SaveList

    def spawnTest(self):
        if self.CharCont.Health == 0:
            for i in self.CharCont.keysHolding:  # Drop all carrying objects
                key = self.addObject(i, self.Character)
                key["Key"] = i.name  # Props to save this obj and consider it a key
            self.CharCont.keysHolding.clear()
            elixer = self.addObject("Elixer", self.Character)
            elixer["Elixer"] = self.CharCont.Elixer
            self.CharCont.Elixer = 0
            self.Character.worldOrientation = self.object.worldOrientation
            self.Character.worldPosition = self.object.worldPosition + Vector([0, -1.5, 1])
            self.CharCont.Health = self.CharCont.MaxHealth
            self.CharCont.Sheild = 200
            self.Overlay.dispPauseNote("You have been slain..\nYou have {}lives left out of 5".format(5-self.deathC))
            self.deathC += 1

            if self.deathC == 5:
                self.endGame("ByDeath")

    def endGame(self, reason: str):
        self.active = False
        if reason == "ByDeath":  # deal with defeat from more than 5 deaths
            if self.autosv:
                self.cursor.execute("DELETE from saves WHERE Slot = {}".format(self.globalDict["SaveSlot"]))
                self.conn.commit()
            self.Overlay.dispPauseNote("You have Run out of chances to Revive and lost the mission", endGame = True)
        elif reason == "Overtime":  # deal with defeat from going above time limit
            if self.autosv:
                self.cursor.execute("DELETE from saves WHERE Slot = {}".format(self.globalDict["SaveSlot"]))
                self.conn.commit()
            self.Overlay.dispPauseNote("Your life force has been consumed and you no longer have the power to continue and hence have lost the mission", 
                                        endGame=True)
        elif reason == "SaveExit":  # deal with save and exit feature
            if self.autosv:
                self.autoSave()
                print("Game saved successfully")
            bge.logic.endGame()
        elif reason == "Restart":
            if self.autoSave:
                self.cursor.execute("UPDATE saves SET Active = False WHERE Slot = {}".format(self.globalDict["SaveSlot"]))
                self.conn.commit()
            bge.logic.restartGame()
        elif reason == "Complete":  # game completed by collecting all 8 keys
            if self.autosv:
                self.cursor.execute("DELETE from saves WHERE Slot = {}".format(self.globalDict["SaveSlot"]))
                self.conn.commit()
                for i in self.reclist:
                    if i[0] == "Time":
                        elpsd = self.formatTime(self.timeElapsed, False)
                        if elpsd < int(i[1]):
                            self.Overlay.showPrompt("You broke the record for finish the game in least time")
                            self.cursor.execute("UPDATE records SET Value = {} WHERE Name = 'Time'".format(str(elpsd)))
                            self.conn.commit()
                        break
            self.Overlay.dispPauseNote("Congratulations... You succesfully have activated the sealing artifact of Negasius and saved the world from destruction", 
                                       endGame=True)

    def nearPointPrompt(self):  # prompt on how near is the nearest key
        lowest = 2000
        for i in self.keyspots:
            dist = int(self.Character.getDistanceTo(self.keyspots[i]))
            if dist < lowest:
                lowest = dist
        self.Overlay.showPrompt("Nearest Key is {}m away       {} keys in hand".format(lowest, len(self.CharCont.keysHolding)))

    def interact(self):
        dist = self.object.getDistanceTo(self.Character)
        if dist < self.healRange:
            if self.pondanim:
                self.__scene.objects["Pond"].playAction("Flow",1 , 480)
            if self.__currtime-self.__lastHeal >= 1:
                self.CharCont.heal(20)
                self.__lastHeal = self.__currtime
            if dist < self.interactionRange:
                fkey = bge.logic.keyboard.inputs[bge.events.FKEY]
                ukey = bge.logic.keyboard.inputs[bge.events.UKEY]
                if fkey.active and not self.__altarView:  # enter altar view with f key
                    self.fstate = True
                    self.__altarView = True
                    self.__scene.active_camera = self.altarCam
                    self.CharCont.active = False
                    self.TPVCont.active = False
                    self.Animator.active = False
                    self.depositedKeys.extend(self.CharCont.keysHolding)
                    self.Overlay.showPrompt("{} keys were deposited".format(len(self.CharCont.keysHolding)))
                    self.CharCont.keysHolding.clear()
                    for i in self.depositedKeys:
                        i.visible = True
                elif not fkey.active and self.fstate:  # f key has been released
                    self.fstate = False
                elif fkey.active and self.__altarView and not self.fstate:  # exit altar view with f key
                    self.__altarView = False
                    self.__scene.active_camera = self.gameCam
                    self.CharCont.active = True
                    self.TPVCont.active = True
                    self.Animator.active = True
                    self.Overlay.showPrompt("")
                elif self.__altarView:  # in altar view
                    if self.CharCont.Elixer >= 150 and self.CharCont.Weapon["Sword"] == 1:
                        if ukey.active:
                            self.CharCont.Elixer -= 150
                            self.CharCont.Weapon["Sword"] = 2
                            # upgrade sword
                        else:
                            self.Overlay.showPrompt("Press U to Upgrade Sword")

                else:  # Not altar view
                    self.Overlay.showPrompt("Press F to interact with the altar")

        else:  # out of heal range
            self.nearPointPrompt()

    def buildbvh(self):
        # Set up BVHTree
        depsgraph = bpy.context.evaluated_depsgraph_get()
        self.terrain = self.__scene.objects["Snow Range"]
        self.bvh = bvhtree.BVHTree.FromObject(self.terrain.blenderObject, depsgraph)

    def findZheight(self, x, y):
        start = self.terrain.worldTransform.inverted() @ Vector([x, y, 500.0])
        rayEnd = self.terrain.worldTransform.inverted() @ Vector([x, y, -100.0])
        angle = (rayEnd-start).normalized()  # get vector that points down
        distance = (start-rayEnd).length
        ray = self.bvh.ray_cast(start, angle, distance)
        if ray[0]:
            print(ray[0])
            return (self.terrain.worldTransform @ ray[0])[2]

    def elixerSpawn(self):
        if self.__currtime - self.__lastElixer >= self.__elixerSpawnRate:
            spot = self.spotlist[random.randrange(0, len(self.spotlist))]
            x = spot.worldPosition.x + random.uniform(-self.healRange, self.healRange)
            y = spot.worldPosition.y + random.uniform(-self.healRange, self.healRange)
            quantity = random.randint(0,5)
            elixer = self.addObject("Elixer", spot)
            elixer.visible = True
            elixer["Elixer"] = quantity
            elixer.worldPosition = Vector([x, y, (self.findZheight(x, y)+1)])
            self.__lastElixer = self.__currtime

    def recordBreaks(self):
        for i in self.reclist:
            if i[0] == "Kills":
                if self.object["KillC"] > int(i[1]):
                    self.Overlay.showPrompt("You broke the record for most kills")
                    self.cursor.execute("UPDATE records SET Value = {} WHERE Name = 'Kills'".format(str(self.object["KillC"])))
                    self.conn.commit()
            elif i[0] == "HalfGame":
                if len(self.depositedKeys) >= 4:
                    t = self.formatTime(self.timeElapsed, False)
                    if t < int(i[1]):
                        self.Overlay.showPrompt("You broke the record for fastest time to get 4 keys")
                        self.cursor.execute("UPDATE records SET Value = {} WHERE Name = 'HalfGame'".format(str(t)))
                        self.conn.commit()

    def timeManager(self):
        self.__currtime = time.time()
        if self.object["Pause"] and self.pauseStartTime == 0:
            self.pauseStartTime = self.__currtime
        elif self.pauseStartTime > 0 and not self.object["Pause"]:
            self.pauseTimeTotal += self.__currtime - self.pauseStartTime
            self.pauseStartTime = 0
        elif not self.object["Pause"]:
            t = self.__currtime - self.startTime - self.pauseTimeTotal
            if t < self.maxTime:
                self.timeElapsed = self.formatTime(t, True)
            else:
                self.endGame("OverTime")

    def update(self):
        if self.active:
            if self.justStarted:
                self.startTime = time.time()
                if not hasattr(self, "bvh"):  # build bvhtree and other init functions
                    self.buildbvh()
                    self.Overlay.initialize()
                    self.__scene.addOverlayCollection(self.ovrlCam, self.ovrlColn)
                if not self.object["Pause"]:
                    if self.autosv and self.globalDict["LoadGame"]:
                        self.object["Pause"] = True
                    else:
                        self.justStarted = False
                        self.__startGame()
                else:
                    self.justStarted = False
                    self.__loadGame()
                    self.lastSaved = time.time()

            self.timeManager()  # To manage all time based vars and features
            if (self.__currtime - self.lastSaved >= self.saveFreq) and self.autosv:  # if the time to save has come again 
                self.lastSaved = self.__currtime
                self.autoSave()
            if not self.object["Pause"]:
                self.__scene.gravity = Vector([0, 0, -9.8])  # set gravity at game start
                self.spawnTest()  # Check if char is dead
                self.interact()  # Interact with altar
                if self.autosv:
                    self.recordBreaks()  # Test for some record breaks
                self.elixerSpawn()  # Spawn elixers
                if len(self.depositedKeys) == 8:  # If u finished the game
                    self.endGame("Complete")
