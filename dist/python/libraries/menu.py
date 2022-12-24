##"menu.py" library ---VERSION 0.14---
##Copyright (C) 2022  Lincoln V.
##
##This program is free software: you can redistribute it and/or modify
##it under the terms of the GNU General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##This program is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pygame
import font
import math

keys = [
    [pygame.K_a,"a"],
    [pygame.K_b,"b"],
    [pygame.K_c,"c"],
    [pygame.K_d,"d"],
    [pygame.K_e,"e"],
    [pygame.K_f,"f"],
    [pygame.K_g,"g"],
    [pygame.K_h,"h"],
    [pygame.K_i,"i"],
    [pygame.K_j,"j"],
    [pygame.K_k,"k"],
    [pygame.K_l,"l"],
    [pygame.K_m,"m"],
    [pygame.K_n,"n"],
    [pygame.K_o,"o"],
    [pygame.K_p,"p"],
    [pygame.K_q,"q"],
    [pygame.K_r,"r"],
    [pygame.K_s,"s"],
    [pygame.K_t,"t"],
    [pygame.K_u,"u"],
    [pygame.K_v,"v"],
    [pygame.K_w,"w"],
    [pygame.K_x,"x"],
    [pygame.K_y,"y"],
    [pygame.K_z,"z"],
    [pygame.K_0,"0"],
    [pygame.K_1,"1"],
    [pygame.K_2,"2"],
    [pygame.K_3,"3"],
    [pygame.K_4,"4"],
    [pygame.K_5,"5"],
    [pygame.K_6,"6"],
    [pygame.K_7,"7"],
    [pygame.K_8,"8"],
    [pygame.K_9,"9"],
    [pygame.K_MINUS,"-"],
    [pygame.K_PLUS,"+"],
    [pygame.K_PERIOD,"."]
    ]

class Menu():
    def __init__(self):
        global keys
        
        #GENERAL STUFF:
        self.menuscale = 1
        
        #OPTIONS STUFF:
        self.options = [] #the name of each option
        self.optionstype = [] #the way you change the options - On-Off, multichoice (simply put a list with a bunch of strings in it for options), numerical (put a list with a max and minimum number)
        self.optionsetting = [] #the setting each option is set to in STR format
        self.optionstate = []
        self.optionsoffset = 0 #option offset variable

        #BUTTONS STUFF:
        self.buttons = [] #image of each button (since these don't have "settings" such as boolean values etc. we don't need any other things here...) FORMAT: [button,pos]
        self.buttonscale = [1,1] #x and y scale for button positioning

        #Key input constants:
        self.keys = keys

    def addoption(self,optionname,optiontype): #adds an option to the variables made in __init__()
        #provided we're not adding an image, append some stuff to our options and optionstype lists
        if(optiontype == "On-Off" or str(type(optiontype[0])) == "<class 'int'>"):
            self.options.append(optionname) #append the name of our option to the self.options list
            self.optionstype.append(optiontype) #append the type of our option to the self.optionstype list
        else:
            try: #let's try address this as a button...
                pygame.image.load(optiontype[0]) #if this test works, we have a button, not multiple-choice
            except Exception as e: #It didn't work??? It must be multiple-choice then.
                self.options.append(optionname) #append the name of our option to the self.options list
                self.optionstype.append(optiontype) #append the type of our option to the self.optionstype list
        #set up the "self.optionsetting" and "self.optionstate" lists
        if(optiontype == "On-Off"): #this is an On-Off setting?
            self.optionsetting.append("On")
            self.optionstate.append("On")
        elif(str(type(optiontype[0])) == "<class 'int'>"): #this is a "max-min" setting?
            self.optionsetting.append(str(optiontype[0]))
            self.optionstate.append(optiontype[0])
        else: #this is an image (button) OR a multiple-choice option?
            try: #let's try address this as a button...
                asurface = pygame.image.load(optiontype[0]) #if this test works, we have a button, not multiple-choice
                self.buttons.append([asurface,optiontype[1]]) #adds a button to the menu (parameter 1 is a PATH to an image, not a Surface() object)
            except Exception as e: #It didn't work??? It must be multiple-choice then.
                self.optionsetting.append(str(optiontype[0])) #this is a multiple-choice option?
                self.optionstate.append(0) #we always start on the first item of a list of multiple-choice options

    def checkoptionsoffset(self): #make sure our "self.optionsoffset" isn't 0, nor greater than len(self.options) - 2
        if(self.optionsoffset < 0):
            self.optionsoffset = 0
        elif(self.optionsoffset > len(self.options) - 2):
            self.optionsoffset = len(self.options) - 2

    def checkoffsetbuttons(self,coords,dimensions,cursorpos): #check if we clicked the down or up buttons to change the self.optionsoffset variable
        up = [coords[0] + (dimensions[0] / 2.0) - (font.SIZE * self.menuscale / 2.0),coords[1],coords[0] + (dimensions[0] / 2.0) + (font.SIZE * self.menuscale / 2.0),coords[1] + (font.SIZE * self.menuscale)]
        down = [coords[0] + (dimensions[0] / 2.0) - (font.SIZE * self.menuscale / 2.0),coords[1] + dimensions[1] - (self.menuscale * font.SIZE),coords[0] + (dimensions[0] / 2.0) + (font.SIZE * self.menuscale / 2.0),coords[1] + dimensions[1]]
        if(up[0] < cursorpos[0] and up[2] > cursorpos[0]): #our cursorpos is within the collision box on the X axis?
            if(up[1] < cursorpos[1] and up[3] > cursorpos[1]): #our cursorpos is within the collision box on the Y axis?
                self.optionsoffset -= 1
        if(down[0] < cursorpos[0] and down[2] > cursorpos[0]): #our cursorpos is within the collision box on the X axis?
            if(down[1] < cursorpos[1] and down[3] > cursorpos[1]): #our cursorpos is within the collision box on the Y axis?
                self.optionsoffset += 1

    def drawhighlight(self,coords,dimensions,cursorpos,screen,stretch=True): #highlights any selected option
        returnedoption = None #a variable we use to return any OPTION we pressed 
        self.checkoptionsoffset() #make sure our "self.optionsoffset" isn't 0, nor greater than len(self.options) - 2
        collision = self.getmenucollision(coords,dimensions,stretch) #get our collision boxes
        optionscollision = collision[0]
        buttoncollision = collision[1]
        for x in range(0,len(optionscollision)): #check them all against cursorpos
            xoffset = x + self.optionsoffset #make sure we take into account our "offset" of options
            acollisionbox = optionscollision[x][1]
            if(acollisionbox[0] < cursorpos[0] and acollisionbox[2] > cursorpos[0]): #our cursorpos is within the collision box on the X axis?
                if(acollisionbox[1] < cursorpos[1] and acollisionbox[3] > cursorpos[1]): #our cursorpos is within the collision box on the Y axis?
                    #draw the highlight in here...
                    pygame.draw.line(screen,[0,255,0],[0,int(acollisionbox[1] - 1)],[screen.get_width(),int(acollisionbox[1] - 1)],1)
                    pygame.draw.line(screen,[0,255,0],[0,int(acollisionbox[3] - 1)],[screen.get_width(),int(acollisionbox[3] - 1)],1)
                    break
        returnedbutton = None #variable used to keep track of button presses
        for x in range(0,len(buttoncollision)): #check our button collision boxes
            acollisionbox = buttoncollision[x]
            if(acollisionbox[0] < cursorpos[0] and acollisionbox[2] > cursorpos[0]): #our cursorpos is within the collision box on the X axis?
                if(acollisionbox[1] < cursorpos[1] and acollisionbox[3] > cursorpos[1]): #our cursorpos is within the collision box on the Y axis?
                    pygame.draw.rect(screen,[0,255,0],[int(acollisionbox[0]),int(acollisionbox[1]),int(acollisionbox[2] - acollisionbox[0]),int(acollisionbox[3] - acollisionbox[1])],1)
                    break

    def drawmenu(self,coords,dimensions,screen,stretch=True): #dimensions are a list with an X and Y value in it, in pixels Offset: is a variable which displays a different set of options
        #draw all the options first
        #make sure our "self.optionsoffset" isn't 0, nor greater than len(self.options) - 2
        self.checkoptionsoffset()
        for x in range(0,len(self.options)): #draw all the options names that will fit on our dimensions[1]
            if(x * (font.SIZE * self.menuscale) > dimensions[1] - (font.SIZE * self.menuscale * 3)): #we've drawn all we can onscreen?
                break
            elif((x + self.optionsoffset) > (len(self.options) - 1)): #we're at the end of the list?
                break
            font.draw_words(self.options[x + self.optionsoffset],[coords[0],coords[1] + (font.SIZE * self.menuscale) + (font.SIZE * self.menuscale) * x],[0,0,255],self.menuscale,screen)
        for x in range(0,len(self.optionsetting)): #draw the state of all the options
            if(x * (font.SIZE * self.menuscale) > dimensions[1] - (font.SIZE * self.menuscale * 3)): #we've drawn all we can onscreen?
                break
            elif(x + self.optionsoffset > len(self.optionsetting) - 1): #we're at the end of the list?
                break
            font.draw_words(self.optionsetting[x + self.optionsoffset],[coords[0] + dimensions[0] - len(list(self.optionsetting[x + self.optionsoffset])) * (font.SIZE * self.menuscale),coords[1] + (font.SIZE * self.menuscale) + (font.SIZE * self.menuscale) * x],[255,0,0],self.menuscale,screen)
        #draw the up and down arrows ONLY if there's enough options in a menu
        if(len(self.options) * font.SIZE * self.menuscale > dimensions[1] - (font.SIZE * self.menuscale * 2.0) and len(self.options) > 0):
            font.draw_words("^",[coords[0] + (dimensions[0] / 2.0) - (font.SIZE * self.menuscale / 2),coords[1]],[0,255,0],self.menuscale,screen)
            font.draw_words(">",[coords[0] + (dimensions[0] / 2.0) - (font.SIZE * self.menuscale / 2),coords[1] + dimensions[1] - (font.SIZE * self.menuscale)],[0,255,0],self.menuscale,screen)
        #draw all the buttons now
        if(stretch == True): #does we wants to stretch our assets all out of scale?
            for x in range(0,len(self.buttons)):
                pos = [int(self.buttons[x][1][0] * self.buttonscale[0]), int(self.buttons[x][1][1] * self.buttonscale[1])]
                tmpsurface = pygame.transform.scale(self.buttons[x][0],[int(self.buttons[x][0].get_width()  * self.buttonscale[0]),int(self.buttons[x][0].get_height() * self.buttonscale[1])])
                screen.blit(tmpsurface,pos)
        else:
            if(self.buttonscale[0] > self.buttonscale[1]): #are we scaling things farther in the X or Y axis?
                usedscale = self.buttonscale[1]
                #offset = [(dimensions[0] / 2.0) - (dimensions[0] / self.buttonscale[0] * usedscale / 2.0),0]
            else:
                usedscale = self.buttonscale[0]
                #offset = [0,(dimensions[1] / 2.0) - (dimensions[1] / self.buttonscale[1] * usedscale / 2.0)]
            for x in range(0,len(self.buttons)):
                #pos = [(self.buttons[x][1][0] * usedscale) + offset[0], (self.buttons[x][1][1] * usedscale) + offset[1]]
                pos = [int(self.buttons[x][1][0] * self.buttonscale[0]), int(self.buttons[x][1][1] * self.buttonscale[1])]
                tmpsurface = pygame.transform.scale(self.buttons[x][0],[int(self.buttons[x][0].get_width()  * usedscale),int(self.buttons[x][0].get_height() * usedscale)])
                screen.blit(tmpsurface,pos)

    def getmenucollision(self,coords,dimensions,stretch=True): #returns the collision for our menu as this format: [OptionIndex, collisionbox]
        optionscollision = []
        self.checkoptionsoffset() #make sure our "self.optionsoffset" isn't 0, nor greater than len(self.options) - 2
        for x in range(0,len(self.optionstype)): #draw all the options names that will fit on our dimensions[1]
            if(x * (font.SIZE * self.menuscale) >= dimensions[1] - (font.SIZE * self.menuscale * 3)): #we've drawn all we can onscreen?
                break
            elif(x + self.optionsoffset > len(self.options) - 1): #we're at the end of the list?
                break
            optionscollision.append([x + self.optionsoffset, [coords[0],coords[1] + (font.SIZE * self.menuscale) + x * (font.SIZE * self.menuscale),coords[0] + dimensions[0],coords[1] + (font.SIZE * self.menuscale * 2) + x * (font.SIZE * self.menuscale)]]) #add a collision box to the list
        buttonscollision = []
        if(stretch == True): #we wants to stretch our buttons?
            for x in range(0,len(self.buttons)): #gather the button collision for this menu as well
                pos = self.buttons[x][1]
                buttonsize = [self.buttons[x][0].get_width(), self.buttons[x][0].get_height()]
                buttonscollision.append([pos[0] * self.buttonscale[0], pos[1] * self.buttonscale[1], (pos[0] + buttonsize[0]) * self.buttonscale[0], (pos[1] + buttonsize[1]) * self.buttonscale[1]])
        else:
            if(self.buttonscale[0] > self.buttonscale[1]): #are we scaling things farther in the X or Y axis?
                usedscale = self.buttonscale[1]
                #offset = [(dimensions[0] / 2.0) - (dimensions[0] / self.buttonscale[0] * usedscale / 2.0),0]
            else:
                usedscale = self.buttonscale[0]
                #offset = [0,(dimensions[1] / 2.0) - (dimensions[1] / self.buttonscale[1] * usedscale / 2.0)]
            for x in range(0,len(self.buttons)):
                pos = [self.buttons[x][1][0], self.buttons[x][1][1]]
                buttonsize = [self.buttons[x][0].get_width(), self.buttons[x][0].get_height()]
                #buttonscollision.append([(pos[0] * usedscale) + offset[0], (pos[1] * usedscale) + offset[1], ((pos[0] + buttonsize[0]) * usedscale) + offset[0], ((pos[1] + buttonsize[1]) * usedscale) + offset[1]])
                buttonscollision.append([(pos[0] * self.buttonscale[0]), (pos[1] * self.buttonscale[1]), (pos[0] * self.buttonscale[0]) + (buttonsize[0] * usedscale), (pos[1] * self.buttonscale[1]) + (buttonsize[1] * usedscale)])
        return [optionscollision, buttonscollision]

    def menucollision(self,coords,dimensions,cursorpos,stretch=True,inc=None,change_menu=True): #checks collision of menu items against cursorpos (inc = False-decrement if possible, inc=True-increment)
        returnedoption = None #a variable we use to return any OPTION we pressed
        if(change_menu):
            self.checkoffsetbuttons(coords,dimensions,cursorpos)
        self.checkoptionsoffset() #make sure our "self.optionsoffset" isn't 0, nor greater than len(self.options) - 2
        collision = self.getmenucollision(coords,dimensions,stretch) #get our collision boxes
        optionscollision = collision[0]
        buttoncollision = collision[1]
        for x in range(0,len(optionscollision)): #check them all against cursorpos
            xoffset = x + self.optionsoffset #make sure we take into account our "offset" of options
            acollisionbox = optionscollision[x][1]
            if(acollisionbox[0] < cursorpos[0] and acollisionbox[2] > cursorpos[0]): #our cursorpos is within the collision box on the X axis?
                if(acollisionbox[1] < cursorpos[1] and acollisionbox[3] > cursorpos[1]): #our cursorpos is within the collision box on the Y axis?
                    if(change_menu):
                        if(self.optionstype[xoffset] == "On-Off"): #change the options value in "self.optionsetting"
                            #we're dealing with a binary option?
                            if(self.optionstate[xoffset] == "On"):
                                self.optionstate[xoffset] = "Off" #keep track of both the state of the setting, and make sure we know what we're gonna render onscreen to tell the user we registered their input
                            else:
                                self.optionstate[xoffset] = "On"
                            self.optionsetting[xoffset] = self.optionstate[xoffset]
                        elif(str(type(self.optionstype[xoffset][0])) == "<class 'int'>"): #we're looking at a "max-min" setting?
                            if(inc == True or inc == None): #if we're either A)incrementing this value or B) doing standard stuff, do the following. ELSE...
                                if(self.optionstate[xoffset] >= self.optionstype[xoffset][1]):
                                    self.optionstate[xoffset] = self.optionstype[xoffset][0] #restore the "min" value of our variable here
                                else:
                                    self.optionstate[xoffset] += 1 #otherwise increment it by one...
                            else:
                                if(self.optionstate[xoffset] <= self.optionstype[xoffset][0]):
                                    self.optionstate[xoffset] = self.optionstype[xoffset][1] #restore the "max" value of our variable here
                                else:
                                    self.optionstate[xoffset] -= 1 #otherwise decrement it by one...
                            self.optionsetting[xoffset] = str(self.optionstate[xoffset])
                        else: #we're looking at a multiple-option setting?
                            if(inc == True or inc == None):
                                if(self.optionstate[xoffset] >= len(self.optionstype[xoffset]) - 1):
                                    self.optionstate[xoffset] = 0 #we were at the last state of our option? if so, reset it back to 0
                                else:
                                    self.optionstate[xoffset] += 1 #move to the next available option
                            else:
                                if(self.optionstate[xoffset] <= 0): #we're already at the first index of our list of options?
                                    self.optionstate[xoffset] = len(self.optionstype[xoffset]) - 1 #we were at the last state of our option? if so, reset it back to [MAX]
                                else:
                                    self.optionstate[xoffset] -= 1 #move to the previous available option
                            self.optionsetting[xoffset] = str(self.optionstype[xoffset][self.optionstate[xoffset]])
                            
                    returnedoption = optionscollision[x][0] #return the index of the option we collided with
                    break
        returnedbutton = None #variable used to keep track of button presses
        for x in range(0,len(buttoncollision)): #check our button collision boxes
            acollisionbox = buttoncollision[x]
            if(acollisionbox[0] < cursorpos[0] and acollisionbox[2] > cursorpos[0]): #our cursorpos is within the collision box on the X axis?
                if(acollisionbox[1] < cursorpos[1] and acollisionbox[3] > cursorpos[1]): #our cursorpos is within the collision box on the Y axis?
                    returnedbutton = x #we found the index of our pressed button!
                    break
        return [returnedoption, returnedbutton]

    def load_settings(self,settings,label): #loads settings values into [label] setting. settings list format: [[optionsetting,optionstate]]
        for x in range(0,len(label)): #iterate through all the settings
            for b in range(0,len(self.options)): #find if "label[x]" == "self.options[b]"
                if(label[x] == self.options[b]): #then we load the setting values into this index!
                    self.optionsetting[b] == settings[x][0] #option in str format
                    self.optionstate[b] == settings[x][1] #actual option index/whatever state
                    break #and then exit the "for b..." loop

    def reconfigure_setting(self,optiontype,optionsetting,optionstate,label): #you can change the settings TYPE of an option, but not its name.
        for x in range(0,len(self.options)):
            if(self.options[x] == label): #we found the option we want to reconfigure?
                self.optionstype[x] = optiontype[:] #availiable options
                self.optionstate[x] = optionstate #index
                self.optionsetting[x] = optionsetting #str
                break #exit this function!

    def grab_settings(self,settings): #give a list of the names of settings you want.
        #The function will output a list of the same length, with the settings' value in their respective places.
        for x in range(0,len(settings)):
            for b in range(0,len(self.options)):
                if(settings[x] == self.options[b]): #we found a name match?
                    settings[x] = [self.optionsetting[b],self.optionstate[b]] #insert the value into the list
                    break
                if(len(self.options) == (b + 1)): #we didn't find the value?
                    settings[x] = None #make sure the caller of this function knows there's NO SETTING called {settings[x]}
                    break
        return settings[:]

def draw_message(message,width_pixels,width_char): #draws a message on a surface in the form of a paragraph.
    #width_pixels is in pixels, and width_char is in characters.
    font_scale = (width_pixels / font.SIZE) / width_char
    screen = pygame.Surface([width_pixels,font.SIZE * font_scale * math.ceil(len(message) / width_char)])
    word_pos = [0,0]
    word = ""
    x_offset = 0
    for x in range(0,len(message)):
        y_increment = int((x + x_offset) / width_char)
        x_increment = (((x + x_offset) / width_char) - int((x + x_offset) / width_char)) * width_char
        if(message[x] == " " or x == len(message) - 1): #we're going to draw the word!
            if(x == len(message) - 1): #we need to add the last character to our message word then...
               word += message[x]
            # - Check: Is the word going to end up off the edge of our border if we draw it on the current line? -
            if(word_pos[0] + (len(word) * font.SIZE * font_scale) > width_pixels):
                # - Move the word onto the next line -
                x_offset += width_char - x_increment
                # - Recalculate word_pos -
                word_pos[1] += font.SIZE * font_scale
                word_pos[0] = 0
                # - Recreate our screen, since it needs to be resized to account for this change -
                new_screen = pygame.Surface([width_pixels,screen.get_height() + font.SIZE * font_scale])
                new_screen.blit(screen,[0,0])
                screen = new_screen
            font.draw_words(word,word_pos,[0,0,255],font_scale,screen)
            word = "" #reset our word variable
        else: #we aren't finished getting the next word...
            if(word == ""):
                word_pos[1] = y_increment * font_scale * font.SIZE
                word_pos[0] = x_increment * font_scale * font.SIZE
            word += message[x]
    # - Draw a green border around the text -
    if(x_offset > 0): #if we had to offset X at all, we may need to remove one line due to spacing
        # - To make sure a black border is not copied over as well (from the edge of the surface not being used),
        #   I need to resize the surface by 1 line of text (but this only happens sometimes).
        new_screen = pygame.Surface([screen.get_width(),font.SIZE * font_scale * math.ceil((len(message) + x_offset) / width_char) + 1])
        new_screen.blit(screen,[0,0])
        screen = new_screen #whew...that was a lot of work
        #   (if you have to move to a new line early but end up only utilizing the same amount of lines
        pygame.draw.rect(screen,[0,255,0],[0,0,screen.get_width(),font.SIZE * font_scale * math.ceil((len(message) + x_offset) / width_char) - 1],1)
    else:
        pygame.draw.rect(screen,[0,255,0],[0,0,screen.get_width(),font.SIZE * font_scale * math.ceil((len(message) + x_offset) / width_char) - 1],1)
    # - Return the message surface -
    return screen  

def get_input(screen,header="",flags=pygame.RESIZABLE): #makes a basic text input UI with a header of your choice
    global keys
    text = "" #this is what we've entered into the UI
    scale = 1.0 #the scale of our text as we draw it
    header_scale = 1.0 #this is the header scale; it is needed because...well...I hate headers which go off the edge of a screen.
    running = True
    while running:
        screensize = [screen.get_width(),screen.get_height()]
        if(scale * font.SIZE * len(list(text)) > screensize[0] - screensize[0] / 5): #we wrote so much text it is over the sides of the screen???
            scale -= 0.1
        elif(scale * font.SIZE * len(list(text)) < screensize[0] - screensize[0] / 3 and scale * font.SIZE < screensize[1] - screensize[1] / 3): #we haven't wrote much text obviously...it's not even filling our screen or even close!!!
            scale += 0.1
        # - Manage the header scale -
        if(header_scale * font.SIZE * len(list(header)) > screensize[0] - screensize[0] / 5): #the header is too big for the screen? Shrink it!
            header_scale -= 0.025
        elif(header_scale * font.SIZE * len(list(header)) < screensize[0] - screensize[0] / 3 and len(list(header)) > 0): #the header is too small? Grow it!!!
            header_scale += 0.025
        #clear our screen...
        screen.fill([0,0,0])
        #draw a green square around our text we're writing
        pygame.draw.rect(screen,[0,255,0],[int(screensize[0] / 2.0 - len(list(text)) * scale * font.SIZE / 2.0) - int(font.SIZE * scale / 10),int(screensize[1] / 2.0 - scale * font.SIZE / 2.0) - int(font.SIZE * scale / 10),int(screensize[0] / 2.0 + len(list(text)) * scale * font.SIZE / 2.0) - int(screensize[0] / 2.0 - len(list(text)) * scale * font.SIZE / 2.0) + int(font.SIZE * scale / 10),int(screensize[1] / 2.0 + scale * font.SIZE / 2.0) - int(screensize[1] / 2.0 - scale * font.SIZE / 2.0) + int(font.SIZE * scale / 10)],1)
        #draw our text
        font.draw_words(text,[int(screensize[0] / 2.0  - len(list(text)) * scale * font.SIZE / 2.0),int(screensize[1] / 2.0 - scale * font.SIZE / 2.0)],[0,0,255],scale,screen)
        font.draw_words(header,[int(screensize[0] / 2.0 - len(list(header)) * header_scale * font.SIZE / 2.0),0],[255,255,0],header_scale,screen)
        #flip the display
        pygame.display.flip()

        for event in pygame.event.get(): #check if somebody wanted to type something...
            if(event.type == pygame.QUIT): #we wanted to exit the text box?
                return None
            elif(event.type == pygame.VIDEORESIZE):
                screen = pygame.display.set_mode(event.size, flags)
            elif(event.type == pygame.KEYDOWN):
                if(event.key == pygame.K_RETURN): #they pressed enter!!!
                    running = False #exit the loop
                elif(event.key == pygame.K_BACKSPACE): #uhoh, we have to delete something!
                    if(len(list(text)) > 0): #we're not trying to delete nothing?
                        text = text[:len(list(text)) - 1] #run the backspace then!
                else: #they probably pressed something we can add to the string!
                    for x in range(0,len(keys)): #iterate through our list of possible keypresses
                        if(keys[x][0] == event.key): #we found THE key?
                            text += keys[x][1]
                            break #exit this mad loop!
    return text #return the input we got

class Menuhandler():
    def __init__(self):
        self.menus = []
        self.menunames = []
        self.menu_scale = 1.0
        self.buttonscale = [1.0,1.0]
        self.current_menu = 0 #the index of the menu we are currently using in the menus[] list
        self.stretch = False
        self.default_display_size = [640,480] #used to calculate menu scale

    def create_menu(self,options,optionstype,indexes,buttonindexes=[],name=""): #indexes is a list of lists of two numbers each. (I know it should be indices)
        #the first number is the index of the button pressed. The second number is the index of the child menu to enter.
        self.menus.append([Menu(),indexes,buttonindexes]) #add a new menu to the list
        self.menunames.append(name) #add the name of the menu to the list
        for x in range(0,len(optionstype)): #add the new menu's options to the list
            self.menus[len(self.menus) - 1][0].addoption(options[x],optionstype[x])

    def delete_menu(self, menu_num): #deletes a menu at the specified index
        del(self.menus[menu_num])
        del(self.menunames[menu_num])

    def grab_settings(self,settings):
        return self.menus[self.current_menu][0].grab_settings(settings)

    def load_settings(self,settings,label):
        self.menus[self.current_menu][0].load_settings(settings,label)

    def reconfigure_setting(self,optiontype,optionsetting,optionstate,label):
        self.menus[self.current_menu][0].reconfigure_setting(optiontype,optionsetting,optionstate,label)

    def update(self,screen):
        self.menu_scale = screen.get_width() / self.default_display_size[0]
        self.buttonscale = [screen.get_width() / self.default_display_size[0],
                            screen.get_height() / self.default_display_size[1]
                            ]

    def menu_collision(self,coords,dimensions,cursorpos,inc=None,change_menu=True):
        self.menus[self.current_menu][0].menuscale = self.menu_scale #make sure we sync our menu_scale with the one in the menu here
        self.menus[self.current_menu][0].buttonscale = self.buttonscale #make sure we sync our buttonscale with the one in the menu here
        namespace = self.menu_scale * font.SIZE #calculate the space needed to write the name of our game at the top of the screen
        pressed = self.menus[self.current_menu][0].menucollision([coords[0],coords[1] + int(namespace)],[dimensions[0],dimensions[1] - int(namespace)],cursorpos,self.stretch,inc,change_menu)
        wascurrentmenu = self.current_menu
        if(change_menu):
            if(pressed[0] != None): #we pressed a button - did we press THE button which changes our menu?
                for x in range(0,len(self.menus[self.current_menu][1])): #check if any of the buttons we pressed should move us to a different menu?
                    if(self.menus[self.current_menu][1][x][0] == pressed[0]): #we pressed THE button?????
                        self.current_menu = self.menus[self.current_menu][1][x][1] #change the menu we're drawing
                        break #exit this checking loop!
            if(pressed[1] != None): #we pressed an ACTUAL button - did we press THE button which changes our menu?
                for x in range(0,len(self.menus[self.current_menu][2])):
                    if(self.menus[self.current_menu][2][x][0] == pressed[1]): #we pressed THE button?????
                        self.current_menu = self.menus[self.current_menu][2][x][1] #change the menu we're drawing
                        break #exit this checking loop!
        return [pressed, wascurrentmenu] #return the button we pressed + the menu we're in, for if we want to do something with it somewhere else...

    def draw_menu(self,coords,dimensions,screen,mousepos): #draw the menu we're currently selecting, and its title/name
        namespace = self.menu_scale * font.SIZE #calculate the space needed to write the name of our game at the top of the screen
        #draw the menu's name
        font.draw_words(self.menunames[self.current_menu],[coords[0] + (dimensions[0] / 2.0) - (len(list(self.menunames[self.current_menu])) * font.SIZE * self.menu_scale / 2.0),coords[1]],[255,255,0],self.menu_scale,screen)
        self.menus[self.current_menu][0].menuscale = self.menu_scale #make sure we sync our menu_scale with the one in the menu here
        self.menus[self.current_menu][0].buttonscale = self.buttonscale #make sure we sync our buttonscale with the one in the menu here
        self.menus[self.current_menu][0].drawmenu([coords[0],coords[1] + int(namespace)],[dimensions[0],dimensions[1] - int(namespace)],screen,self.stretch)
        self.menus[self.current_menu][0].drawhighlight([coords[0],coords[1] + int(namespace)],[dimensions[0],dimensions[1] - int(namespace)],mousepos,screen,self.stretch)

###basic menu test
##mh = Menuhandler()
##mh.create_menu(["Option a","This is a test option"],
##               [[0,3],["a","b","c"]],
##               [],
##               [],
##               "Test Menu")
##
##screen = pygame.display.set_mode([640,480],pygame.RESIZABLE)
##
##mousepos = [0,0]
##
##running = True
##while running:
##    mh.update(screen)
##    for event in pygame.event.get():
##        if(event.type == pygame.QUIT):
##            running = False
##        elif(event.type == pygame.MOUSEBUTTONDOWN):
##            mh.menu_collision([0,0],[screen.get_width(),screen.get_height()],event.pos)
##        elif(event.type == pygame.MOUSEMOTION):
##            mousepos = event.pos[:]
##
##    screen.fill([0,0,0]) #fill the screen with black for a background
##    mh.draw_menu([0,0],[screen.get_width(),screen.get_height()],screen,mousepos) #draw the menu buttons along with the titles for the menu
##
##    #update the display
##    pygame.display.flip()
##
##pygame.quit()

### - Paragraph draw demo -
##screen = pygame.display.set_mode([300,900])
##screen.blit(draw_message("this is a really long error message becasue I don't know what to do about this junk" \
##             ,screen.get_width(),12),[0,0])
##pygame.display.flip()
