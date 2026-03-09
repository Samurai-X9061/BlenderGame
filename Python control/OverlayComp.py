import bge
import bpy
from collections import OrderedDict
from math import ceil, floor
from textwrap import wrap

from uplogic.ui import Canvas
from uplogic.ui import RelativeLayout
from uplogic.ui import Layout
from uplogic.ui import Label
from uplogic.ui import LabelButton
from uplogic.ui import Cursor
from uplogic.ui import Image
from uplogic.utils import world_to_screen


class Overlay(bge.types.KX_PythonComponent):
    args = OrderedDict([
        ("Activate", True),
        ("Health Bar", True),
        ("Prompt Bar Height", 1.0)
    ])

    def start(self, args):
        self.active = args["Activate"]
        self.scene = bge.logic.getCurrentScene()
        self.BarColor = bpy.data.materials["Health Bar"].node_tree.nodes["Color Ramp"].inputs[0] 
        self.charcont = self.scene.objects["Character"].components["CharCont"]
        self.maincont = self.scene.objects["Altar"].components["MainCont"]
        self.DispElixer = 0
        self.DispHealth = 800
        self.promptBarSize = args["Prompt Bar Height"]  # 'Y' thickness of the prompt text object at a single line
        self.prompTextMoveC = 0  # No of times the promt text was moved up to accomodate more text
        fontloc = bpy.path.abspath("//Fonts/LilitaOne.ttf")

        self.textsize = bge.render.getWindowHeight()/25

        self.cursor = Cursor(
            size=[40, 40],
            texture='cursShooter.png',
            offset=(-20, -20)
        )
        # Set up layouts for dispPauseNote()
        self.darken = Layout(
            relative={'size': True},
            size=[1, 1],
            bg_color=[0, 0, 0, .4],
            border_color=[1, 1, 1, 0]
            )
        self.frame = RelativeLayout(
            relative={'pos': True, 'size': True},
            pos=[.1, .14],
            size=[.8, .74],
            bg_color=[0, 0, 0, .5],
            border_width=1,
            border_color=[1, 1, 1, 1]
            )
        self.bgrigel = Image(
            relative={'pos': True, 'size': True},
            size=[.43, .74],
            pos=[.3, .14],
            texture="TranspRigel.png"
            )
        self.textBox = Label(
            relative={'pos': True},
            pos=[.15, .85],
            font_size=self.textsize,
            font=fontloc,
            halign='centre',
            valign='top',
            shadow=True,
            text="Note"
            )
        self.exitButton = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.4, 0.04],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='OK'
            )
        self.exitButton.on_click = self.unPauseNote  # run function to set pause an false on click
        self.pauseNote = Canvas()
        self.pauseNote.add_widget(self.darken)
        self.pauseNote.add_widget(self.frame)
        self.pauseNote.add_widget(self.bgrigel)
        self.pauseNote.add_widget(self.textBox)
        self.pauseNote.add_widget(self.exitButton)
        self.unPause = False

        # For the menu...
        self.darken1 = Layout(
            relative={'size': True},
            size=[1, 1],
            bg_color=[0, 0, 0, .4],
            border_color=[1, 1, 1, 0]
            )
        self.logo1 = Image(
            relative={'pos': True, 'size': True},
            size=[.75, .2],
            pos=[.5, .81 ],
            texture="LogoGame.png",
            halign='center'
            )
        self.backgrnd = RelativeLayout(
            relative={'pos': True, 'size': True},
            pos=[.1, .14],
            size=[.8, .71],
            bg_color=[0, 0, 0, .5]
            )
        self.title = Label(
            relative={'pos': True},
            pos=[.475, .82],
            font=fontloc,
            font_size=self.textsize,
            halign='centre',
            valign='top',
            wrap=True,
            shadow=True,
            text="Menu"
            )
        self.resume = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.4, 0.22],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='Resume'
            )
        self.saveExit = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.4, 0.37],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='Save and Exit'
            )
        self.restart = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.4, 0.52],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='New Game'
            )
        self.load = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.4, 0.67],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='Load a Save'
            )

        self.menu = Canvas()
        self.menu.add_widget(self.darken1)
        self.menu.add_widget(self.logo1)
        self.menu.add_widget(self.backgrnd)
        self.menu.add_widget(self.resume)
        self.menu.add_widget(self.saveExit)
        self.menu.add_widget(self.restart)
        self.menu.add_widget(self.load)
        self.menu.add_widget(self.title)
        # save state buttons
        self.backgrnd1 = RelativeLayout(
            relative={'pos': True, 'size': True},
            pos=[.1, .14],
            size=[.8, .71],
            bg_color=[0, 0, 0, .5]
            )
        self.darken2 = Layout(
            relative={'size': True},
            size=[1, 1],
            bg_color=[0, 0, 0, .4],
            border_color=[1, 1, 1, 0]
            )
        self.logo2 = Image(
            relative={'pos': True, 'size': True},
            size=[.75, .2],
            pos=[.5, .81 ],
            texture="LogoGame.png",
            halign='center'
            )
        self.region1 = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.15, 0.2],
            size=[0.3, 0.28],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1]
            )
        self.region2 = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.55, 0.2],
            size=[0.3, 0.28],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1]
            )
        self.region3 = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.15, 0.52],
            size=[0.3, 0.28],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1]
            )
        self.region4 = LabelButton(  
            relative={'pos': True, 'size': True},
            pos=[.55, 0.52],
            size=[0.3, 0.28],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1]
            )
        self.regions = [self.region1, self.region2, self.region3, self.region4]
        self.currSavePage = 0  # The group of slots urrently being displayed (0 = 1st 4 and 1 = next 4) 
        self.nextButton = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.6, .04],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='Next'
            )
        self.backButton = LabelButton(
            relative={'pos': True, 'size': True},
            pos=[0.2, .04],
            size=[0.2, 0.075],
            font_size=self.textsize,
            font=fontloc,
            bg_color=[0, 0, 0, 0.7],
            border_width=1,
            border_color=[1, 1, 1, 1],
            text='Back'
            )
        self.loadGameCanvas = Canvas()
        self.loadGameCanvas.add_widget(self.darken2)
        self.loadGameCanvas.add_widget(self.logo2)
        self.loadGameCanvas.add_widget(self.backgrnd1)
        self.loadGameCanvas.add_widget(self.nextButton)
        self.loadGameCanvas.add_widget(self.backButton)
        for i in self.regions:
            self.loadGameCanvas.add_widget(i)

        self.loadGameCanvas.show = False
        self.pauseNote.show = False
        self.menu.show = False

        self.saveCount = 0  # No of saves to load from
        self.pauseState = 0

    #  to setup the logic of the pause screens
    def cursorCh(self, type: bool):  # type =True is selection false is shooter
        if type:
            self.cursor.texture = 'cursNorm.png'
            self.cursor.offset = (-5,0)
        else:
            self.cursor.texture = 'cursShooter.png'
            self.cursor.offset = (-20, -20)

    def loadSaveClickHandler(self, widget):
        for i in self.regions:
            if widget is i:
                index = self.regions.index(i)
        selected = self.currSavePage*4 + index
        selected = self.maincont.getSavesList()[selected][0]
        self.maincont.reLoadSave(selected)

    def loadGameScreen(self, widget):
        saves = self.maincont.getSavesList()
        self.saveCount = len(saves)  # get saves list and display on buttons
        nof_Entries = self.saveCount - self.currSavePage*4
        for i in range(0, nof_Entries):  # display existing ones
            self.regions[i].text = "{}, {}\nHealth: {} Time: {}\nKills={}, Deaths={}, Keys={}".format(*saves[self.currSavePage*4+i])
        if nof_Entries < 4:  # make the free buttons blank
            for i in range(nof_Entries, 4):
                self.regions[i].text = ""
        self.menu.show = False
        self.loadGameCanvas.show = True

    def nextPageSaves(self, widget): 
        if widget is self.nextButton: # dir 1 is forward and 0 back
            dir = True
        else: dir = False
        if dir and (self.saveCount - 4*self.currSavePage) > 4:  # if there are more the 4 entries left (there is something left for the next page)
            self.currSavePage += 1
            self.loadGameScreen(None)
        elif dir is False:  # Go to prev page
            if self.currSavePage != 0:
                self.currSavePage -= 1
                self.loadGameScreen(None)
            else:  # Go to the main menu back in back is pressed with the first page open
                self.menu.show = True
                self.loadGameCanvas.show = False

    def exitMenu(self, widget):  # To exit the menu view
        self.pauseState = 0
        self.maincont.object["Pause"] = False
        self.menu.show = False
        self.cursorCh(False)

    def unPauseNote(self, widget):
        self.unPause = True

    def dispPauseNote(self, note: str=None, endNote=False):
        if self.pauseState != 2:
            self.maincont.object["Pause"] = True
            self.pauseState = 2
            self.unPause = False
            self.pauseNote.show = True
            self.cursorCh(True)
            note = ' '.join(note.split())
            lines = wrap(note, 75)
            self.textBox.text = ''
            for i in lines:
                self.textBox.text += str(i) + '\n'
        elif self.pauseState == 2:
            if self.unPause:
                self.pauseNote.show = False
                self.cursorCh(False)
                if endNote:
                    bge.logic.endGame()
                else:
                    self.pauseState = 0
                    self.maincont.object["Pause"] = False

    def pauseScreen(self):
        if self.pauseState == 2:
            self.dispPauseNote()
        elif self.pauseState == 0 and bge.logic.keyboard.inputs[bge.events.TABKEY].active:
            self.pauseState = 1
            self.maincont.object["Pause"] = True
            self.menu.show = True
            self.cursorCh(True)

    def restartGame(self, widget):
        self.maincont.endGame("Restart")

    def savexit(self, widget):
        self.maincont.endGame("SaveExit")

    # Initialise variables dependent on other functions or components
    def initialize(self):
        self.DispElixer = self.charcont.Elixer
        self.DispHealth = self.charcont.Health
        # Initialize bars
        self.object.children["Heart"].children["HealthBar"].localScale.x = self.DispHealth/self.charcont.MaxHealth*0.87 + 0.13
        self.object.children["Heart"].children["ElixerTxt"]["Text"] = str(self.DispElixer)+"/200"
        self.object.children["Heart"].children["ElixerBar"].localScale.x = self.DispElixer/200
        self.object.children["Heart"].children["Hypercharge"].localScale.x = 0
        self.BarColor.default_value = self.DispHealth/800

        self.resume.on_click = self.exitMenu
        self.saveExit.on_click = self.savexit
        self.restart.on_click = self.restartGame
        if self.maincont.autosv:
            self.load.on_click = self.loadGameScreen
            self.nextButton.on_click = self.nextPageSaves
            self.backButton.on_click = self.nextPageSaves
        for button in self.regions:
            button.on_click = self.loadSaveClickHandler

    def healthControl(self):
        currHealth = self.charcont.Health
        shield = self.charcont.Shield
        self.object.children["Heart"].children["Shield"].localScale.x = shield/200
        if self.DispHealth != currHealth:
            if self.DispHealth > currHealth:
                self.DispHealth += floor((currHealth - self.DispHealth)/75)
            elif self.DispHealth < currHealth:
                self.DispHealth += ceil((currHealth - self.DispHealth)/75)
            self.BarColor.default_value = self.DispHealth/800
            # self.object.children["Heart"].children["HealthTxt"]["Text"] = self.DispHealth
            self.object.children["Heart"].children["HealthBar"].localScale.x = self.DispHealth/self.charcont.MaxHealth*0.87 + 0.13

    def elixerControl(self):
        currElixer = self.charcont.Elixer
        if self.DispElixer != currElixer:
            if self.DispElixer > currElixer:
                self.DispElixer += floor((currElixer - self.DispElixer)/50)
            elif self.DispElixer < currElixer:
                self.DispElixer += ceil((currElixer - self.DispElixer)/50)
            self.object.children["Heart"].children["ElixerTxt"]["Text"] = str(self.DispElixer)+"/200"
            self.object.children["Heart"].children["ElixerBar"].localScale.x = self.DispElixer/200
        hyper = self.charcont.hyperTime/8  # Divide by total time = 8sec
        if hyper:
            self.object.children["Heart"].children["Hypercharge"].localScale.x = hyper

    def statBar(self):
        self.object.children["StatBar"].children["Kills"]["Text"] = str(self.maincont.object["KillC"])
        self.object.children["StatBar"].children["Deaths"]["Text"] = str(self.maincont.deathC)
        self.object.children["StatBar"].children["KeyD"]["Text"] = str(len(self.maincont.depositedKeys)) + "/8"
        self.object.children["Timer"]["Text"] = self.maincont.timeElapsed

    def showPrompt(self, prompt: str):
        ''' Shows a prompt on given text in the bottom right text object '''
        promptObj = self.object.children["Prompt"]
        promptObj["Text"] = ''
        lines = wrap(prompt, 30)
        promptObj.localPosition.y -= self.promptBarSize*self.prompTextMoveC
        self.prompTextMoveC = len(lines)-1
        for i in range(0, len(lines)):  # Displays all lines 
            promptObj["Text"] += (str(lines[i]) + '\n')
            if i < self.prompTextMoveC:  # this is not the last line
                promptObj.localPosition.y += self.promptBarSize

    def update(self):
        if self.active:
            self.healthControl()
            self.elixerControl()
            self.statBar()
            self.pauseScreen()
