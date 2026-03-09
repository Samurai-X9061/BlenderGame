import bge
from time import time

# This script is connected to a near sensor which detect "Enemy" property
cont = bge.logic.getCurrentController()
own = cont.owner
near = cont.sensors["Near"]
MainCont = own.scene.objects["Altar"].components["MainCont"]
character = own.scene.objects["Character"]
CharCont = character.components["CharCont"]
ownKey = MainCont.spawnKeys[own["KeyName"]]
own["Save"] = True


def addGolem(count = 1):
    for i in range(0, count):
        golem = own.scene.addObject("GolemEnemy", own)
        golem["Original"] = "GolemEnemy"
        golem["Enemy"] = True
        golem["LastHit"] = 0
        golem["SpawnP"] = own.name
        own["TotalGolemCount"] += 1


dist = own.getDistanceTo(character)
golemCount = len(near.hitObjectList)

if own["TotalGolemCount"] < 7:
    if (golemCount < 3 and dist < 100) and ((time() - own["lastSpawn"]) > 15):
        print("b")
        addGolem(3 - golemCount)
        own["lastSpawn"] = time()

    elif dist < 10 and golemCount < 5:
        print("c")
        addGolem(5 - golemCount)

if dist < 1:
    print("d")
    CharCont.keysHolding.append(MainCont.keys[ownKey])
    MainCont.Overlay.showPrompt("You obtained the {} key".format(ownKey))
    MainCont.spawnKeys[ownKey].endObject()
    del MainCont.keyspots[ownKey]
    own.visible = False
    own["Active"] = False


