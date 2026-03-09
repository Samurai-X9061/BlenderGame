import bge
import bpy
import mysql.connector
import pickle

own = bge.logic.getCurrentController().owner


# set graphics variables
if "Init" not in own:
    own["Init"] = True
    loc = bpy.path.abspath("//Python control/settings.config")
    with open(loc, "rb") as config:
        settings = pickle.load(config)
        bge.logic.globalDict["AutoSave"] = settings["AutoSave"]
        SQL_host = settings["SQL_host"]
        SQL_user = settings["SQL_user"]
        SQL_pwd = settings["SQL_pwd"]
        #bpy.context.scene.eevee.use_bloom = settings["Bloom"]
        bpy.context.scene.eevee.use_raytracing = settings["SSR"]
        bpy.context.scene.eevee.use_shadows = settings["Soft_Shadows"]
        bpy.context.scene.eevee.use_gtao = settings["AO"]
        #bpy.context.scene.eevee.use_motion_blur = settings["MotionBlur"]
        bpy.context.scene.eevee.use_volumetric_lights = settings["Volumetrics"]
        # make code for eevee

    if bge.logic.globalDict["AutoSave"]:
        conn = mysql.connector.connect(user=SQL_user, host=SQL_host, passwd=SQL_pwd)

        bge.logic.globalDict["Conn"] = conn

        if conn.is_connected:
            cursor = conn.cursor(buffered=True)
            bge.logic.globalDict["Cursor"] = cursor

            cursor.execute("SHOW DATABASES")  # Check if DB exist and deal

            if ('horizons_resurfaced',) not in cursor.fetchall():
                cursor.execute("CREATE DATABASE horizons_resurfaced")

            cursor.execute("USE horizons_resurfaced")

            cursor.execute("SHOW TABLES")  # Check if table exists and deal
            tables = cursor.fetchall()
            if ('saves',) not in tables:
                cursor.execute('''CREATE TABLE saves
                    (Slot     tinyint   NOT NULL UNIQUE PRIMARY KEY,
                    ID       char(20)  NOT NULL,
                    Active   bool      DEFAULT True,
                    Health   smallint  DEFAULT 800,
                    Shield   smallint  DEFAULT 200,
                    Elixer   smallint  DEFAULT 0,
                    Weapon   text      ,
                    Kills    smallint  DEFAULT 0,
                    Deaths   tinyint   DEFAULT 0,
                    KeysHold text      ,
                    KeysDep  text      ,
                    ElapsedT varchar(6)DEFAULT "00:00",
                    ObjData  mediumtext
                    )''')

            if ('records',) not in tables:
                cursor.execute('''CREATE TABLE records
                    (Name    varchar(20)  NOT NULL,
                    Value   varchar(10)
                    )''')
            else:
                cursor.execute("SELECT Name FROM records")
                query = cursor.fetchall()
                nameslist = []
                for i in query:
                    nameslist.append(i[0])
                if "Kills" not in nameslist:
                    cursor.execute("INSERT INTO records VALUES('Kills','0')")
                if "HalfGame" not in nameslist:
                    cursor.execute("INSERT INTO records VALUES('HalfGame','1200')")
                if "Time" not in nameslist:
                    cursor.execute("INSERT INTO records VALUES('Time','1200')")

            # Slot selection
            cursor.execute("SELECT Slot FROM saves WHERE Active = True")
            activeSlots = cursor.fetchall()
            if activeSlots == []:  # Make a new game if no active slot
                cursor.execute("SELECT Slot FROM saves")
                slotlist = cursor.fetchall()
                for i in range(0, 25):  # Find free slot
                    if (i,) not in slotlist:
                        currentSlot = i
                        break
                else:  # all slots are filled then delete small game
                    cursor.execute("SELECT Slot FROM saves WHERE ElapsedT = (SELECT min(ElapsedT) FROM saves)")
                    currentSlot = cursor.fetchone()[0]
                    cursor.execute("DELETE FROM saves WHERE Slot = {0}".format(currentSlot))

                cursor.execute("INSERT into saves(Slot, ID, Active) VALUES({0}, 0, True)".format(currentSlot))
                bge.logic.globalDict["LoadGame"] = False

            else:  # Select active slot
                currentSlot = activeSlots[0][0]
                bge.logic.globalDict["LoadGame"] = True

            bge.logic.globalDict["SaveSlot"] = currentSlot

            conn.commit()

        else:
            bge.logic.globalDict["AutoSave"] = False
