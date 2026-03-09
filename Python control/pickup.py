import bge


def main():

    cont = bge.logic.getCurrentController()
    own = cont.owner
    charcont = own.scene.objects["Character"].components["CharCont"]
    maincomp = own.scene.objects["Altar"].components["MainCont"]

    sens = cont.sensors['Near']
    key = cont.sensors["Key"]

    if sens.positive:
        for i in sens.hitObjectList:
            if charcont.Elixer + i["Elixer"] <=200:
                charcont.Elixer += i["Elixer"]
                i.endObject()
            elif charcont.Elixer <=200:
                charcont.Elixer = 200
                i.endObject()
    if key.positive:
        for i in key.hitObjectList:
            charcont.keysHolding.append(maincomp.keys[i["Key"]])
            i.endObject


main()
