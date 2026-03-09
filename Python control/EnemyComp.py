import bge
import random
from time import time
from mathutils import Vector
from collections import OrderedDict


class EnemyAI(bge.types.KX_PythonComponent):
    args = OrderedDict([
        ("Activate", True),
        ("Health", 700),
        ("Chase Distance", 100.0),
        ("Attack Range", 1.0),
        ("Max Speed", 20.0)
    ])

    def start(self, args):
        self.active = args["Activate"]
        self.object["Health"] = args["Health"]
        self.object["Enemy"] = "Golem"
        self.lookRange = args["Chase Distance"]
        self.attackRange = args["Attack Range"]
        self.maxSpeed = args["Max Speed"]
        self.character = self.object.scene.objects["Character"]
        self.spawnpoint = self.object.scene.objects[self.object["SpawnP"]]
        self.CharCont = self.character.components["CharCont"]
        self.Altar = self.object.scene.objects["Altar"] 
        self.maincomp = self.Altar.components["MainCont"]
        self.arm = self.object.children[0]
        self.walk_point_set = False
        self.walk_point = [0, 0, 0]
        self.lastWalkPoint = Vector([0, 0, 0])
        self.__lastattacked = time()
        self.__dead = False
        self.pathFinder = self.object.scene.objects['Pathfinding']
        self.lastFrameTime = time()
        self.object.visible = False

    def pathfind(self, target):

        if (Vector(target) - self.lastWalkPoint).length > 1.0:  # Create the path
            self.pathFinder['Requests'].append((self.object, self.object.worldPosition, target))
            self.object["waiting"] = True

        elif 'path' in self.object and 'waiting' not in self.object and len(self.object['path']) > 0:  # Move the golem in the path
            if (self.object['path'][-1][0] - self.lastWalkPoint).length < 8:
                goal = self.object['path'][0][0].copy()
                goal += self.object['path'][0][1]
                up = self.object['path'][0][1]

                local2 = self.object.worldTransform.inverted() @ goal
                deltaTimeFac = 15*(time() - self.lastFrameTime)
                self.lastFrameTime = time()
                if local2.length > .125:
                    v2 = (goal - self.object.worldPosition)
                    if v2.length > .5:
                        if local2.x > 0 and abs(local2.y) < local2.x:
                            self.object.worldPosition += v2.normalized() * deltaTimeFac
                        if local2.x>0:
                            self.object.alignAxisToVect(-(self.object.worldPosition-goal).normalized(), 0, deltaTimeFac)
                            self.object.alignAxisToVect(up, 2, 1)
                        else:
                            if local.y < -.01:
                                self.object.applyRotation((0, 0, -deltaTimeFac/5), 1)
                            else:
                                self.object.applyRotation((0, 0, deltaTimeFac/5), 1)
                    else:
                        self.object.worldPosition = goal
                        self.object['path'].pop(0)
                else:
                    self.object.worldPosition = goal
                    self.object['path'].pop(0)
            else:
                local = self.object.worldTransform.inverted() @ self.lastWalkPoint
                if local.length > 3 and bge.logic.getRandomFloat() > .5:
                    del self.object['path']

    def search_walk_point(self):
        # Calculate random point in range
        random_x = self.spawnpoint.worldPosition.x + random.uniform(-self.lookRange, self.lookRange)
        random_y = self.spawnpoint.worldPosition.y + random.uniform(-self.lookRange, self.lookRange)
        self.walk_point = Vector([random_x, random_y, self.maincomp.findZheight(random_x, random_y)])
        self.walk_point_set = True

    def Patrolling(self):
        if not self.walk_point_set:
            self.search_walk_point()

        else:
            self.pathfind(self.walk_point)

        distance_to_walk_point = (self.object.worldPosition - self.walk_point).length

        # Walkpoint reached
        if distance_to_walk_point < 2.0:
            self.walk_point_set = False

    def healthTest(self):
        if self.object["Health"] <= 0:
            self.Altar["KillC"] += 1
            # Play death anim
            if not self.__dead:
                self.arm.playAction("Die", 1, 70, 4)
                self.__dead = True
            elif not self.arm.isPlayingAction():
                elixer = self.maincomp.addObject("Elixer", self.object)
                elixer["Save"] = True
                elixer["Elixer"] = 15
                elixer["Original"] = "Elixer"
                self.object.endObject()

    def __facePlayer(self):
        vec = self.object.getVectTo(self.character)
        self.object.alignAxisToVect(vec,0,.1)

    def update(self):
        self.healthTest()
        if not self.__dead:
            # Distance to the target
            distance = self.object.getDistanceTo(self.character)

            # If inside the lookRadius
            if distance <= self.lookRange:
                # Move towards the target
                self.pathfind(self.character.worldPosition)

                # If within attacking distance
                if distance <= self.attackRange:
                    self.object.localLinearVelocity.x *= 0.1
                    self.__facePlayer()
                    if (time() - self.__lastattacked) >= 4:
                        self.CharCont.damage(5, True, True)
                        self.arm.playAction("Attack2", 1, 50, 4)
                        self.__lastattacked = time()
            else:
                self.Patrolling()


