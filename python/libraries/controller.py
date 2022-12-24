##"controller.py" library ---VERSION 0.09---
## - use this library to easily make a game compatible with both controllers and keyboards!
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

#init pygame.joystick
pygame.init()
pygame.joystick.init()

#a list which holds all the keycodes of pressed keys at any given time
keycodes = []

#everyone knows what this does...
DEADZONE = 0.30

#give a joystick object, outputs all IDs of buttons pressed
def check_joystick_buttons(joystick): #returns a list with the numbers of all pressed buttons
    buttons = [] #temporary list of all pressed js buttons
    for buttonnum in range(0,joystick.get_numbuttons()): #iterate through all the #s of joystick buttons
        if(joystick.get_button(buttonnum)):
            buttons.append(buttonnum + joystick.get_numhats() * 4 + joystick.get_numaxes() * 2) #if this X button is pressed, append the # to the list
    return buttons

#give a joystick object, returns IDs of Dpad buttons pressed
def check_joystick_dpads(joystick):
    buttons = []
    for hatnum in range(0,joystick.get_numhats()):
        hat_data = list(joystick.get_hat(hatnum))
        if(hat_data[0] != 0): #we're pressing a button on the X axis?
            if(hat_data[0] == -1):
                buttons.append((joystick.get_numaxes() * 2) + 2 + (hatnum*4)) #left
            else:
                buttons.append((joystick.get_numaxes() * 2) + 3 + (hatnum*4)) #right
        if(hat_data[1] != 0): #we pressed a button on the Dpad on the Y axis?
            if(hat_data[1] == -1):
                buttons.append((joystick.get_numaxes() * 2) + 1 + (hatnum*4)) #down
            else:
                buttons.append((joystick.get_numaxes() * 2) + 0 + (hatnum*4)) #up
    return buttons

#give a joystick object, outputs all axis values in order of ID number as a list.
def check_joystick_axes(joystick):
    global DEADZONE
    axes = [] #temporary list of joystick axes values
    num_axes = joystick.get_numaxes() #get the number of js analog axes
    for x in range(0,num_axes): #append a # to our list for each analog axis on the controller
        axes.append(0)
    for x in range(0,num_axes): #set all our axes values to what pygame is reading from the controller
        axes[x] = joystick.get_axis(x)
    # - Now we convert our axis values to button presses -
    axis_buttons = []
    for x in range(0,len(axes)):
        if(abs(axes[x]) > DEADZONE):
            if(axes[x] > DEADZONE):
                axis_buttons.append(x * 2 + 1)
            else: #-1 value
                axis_buttons.append(x * 2)
    return axis_buttons

def empty_keys(): #empties keycodes of keypresses
    global keycodes
    for x in keycodes:
        keycodes.pop(0)

#checks pygame's event loop for keypress events, and appends them to the keycode list. Also removes old keycodes.
def get_keys(): #this should be run once per frame/compute tick in a game's code for optimal performance.
    global keycodes
    wants_quit = False #quick boolean value which tells us whether it's time to quit
    resize = None
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #if someone clicks the "X", we're going to return "True" from this function.
            wants_quit = True
        if(event.type == pygame.KEYDOWN): #do we need to add a key to our list of keycodes?
            if(event.key not in keycodes): #if the keycode isn't already in the keycodes list, append it.
                keycodes.append(event.key)
        elif(event.type == pygame.KEYUP): #if we released a key, we need to remove the keycode from our list of keypresses.
            if(event.key in keycodes): #make sure we're not deleting a keycode which isn't there!
                del(keycodes[keycodes.index(event.key)])
        elif(event.type == pygame.VIDEORESIZE):
            resize = event.size[:]
    return [wants_quit, resize] #return whether we want to quit

class Controls():
    def __init__(self, buttons_ct=8, kb_ctrl="kb", js_num=0):
        self.buttons = [] #this is a list of all our buttons, which holds the corresponding keycode/button code number.
        for x in range(0,buttons_ct): #add key/buttoncode 0 to all our buttons at the moment
            self.buttons.append(0)
        self.kb_ctrl = kb_ctrl #make sure we set a variable telling us if we're using a "kb" (keyboard) or controller "ctrl"
        self.js_num = js_num #which joystick are we using, if any?
        self.js_ct = pygame.joystick.get_count() #update our joystick count
        if(self.js_num < self.js_ct):
            self.joystick = pygame.joystick.Joystick(self.js_num) #set up a joystick object on our joystick ID IF we are using joysticks
            self.joystick.init()

    def joystick_request(self, js_num=0):
        self.js_ct = pygame.joystick.get_count() #update our joystick count
        if(self.js_num < self.js_ct):
            self.kb_ctrl = "ctrl"
            if(self.js_num != js_num): #if we need to reconfigure our JS...
                self.js_num = js_num
                self.joystick = pygame.joystick.Joystick(self.js_num) #set up a joystick object on our joystick ID IF we are using joysticks
                self.joystick.init()
                pygame.time.delay(500)
            return True
        self.kb_ctrl = "kb"
        return False #couldn't get the joystick we wanted

    def get_input(self): #keyboard_input is a list of keycodes of all the keys which are being pressed down.
        global keycodes #we need to read from this list of pressed keys to see what has been pressed
        self.js_ct = pygame.joystick.get_count() #update our joystick count
        buttons_pressed = [] #a list which contains the button numbers which are pressed
        keyboard_input = keycodes #we need to find out what keys have been pressed...
        if(self.kb_ctrl == "kb"): #we're getting input from a keyboard
            for x in range(0,len(self.buttons)): #check if any of our buttons keycodes matches any from keyboard_input
                if(self.buttons[x] in keyboard_input): #did one of our keycodes match a keyboard press?
                    buttons_pressed.append(x) #make sure we add this button to buttons_pressed
        elif(self.kb_ctrl == "ctrl"): #we're getting input from a controller
            js_buttons = check_joystick_buttons(self.joystick)
            js_dpads = check_joystick_dpads(self.joystick) #get buttons from our Dpads
            js_axes = check_joystick_axes(self.joystick) #get virtual button input from analog axes
            # - Add the Dpad and js_axes buttons into our main buttons list -
            for x in js_dpads:
                js_buttons.append(x)
            for x in js_axes:
                js_buttons.append(x)
            # - Check if any buttons in js_buttons matched our configuration setup -
            for x in range(0,len(js_buttons)):
                if(js_buttons[x] in self.buttons): #have we found that a pressed button was part of our JS button configuration?
                    buttons_pressed.append(self.buttons.index(js_buttons[x])) #add the button ID to the list!
        return buttons_pressed #return the list of all the buttons which were pressed

    #configures a key of your choice by checking if any keys were pressed. If they were, the key gets automatically mapped to the key self.buttons[key_num] and True is returned. If no key is pressed, False is returned.
    def configure_key(self, key_num):
        global keycodes
        self.js_ct = pygame.joystick.get_count() #update our joystick count
        if(keycodes != [] and self.kb_ctrl == "kb"): #we pressed a key?
            self.buttons[key_num] = keycodes[0] #the first key pressed gets configuration priority.
            return True
        elif(self.kb_ctrl == "ctrl"): #joystick?
            js_buttons = check_joystick_buttons(self.joystick)
            js_dpads = check_joystick_dpads(self.joystick)
            js_axes = check_joystick_axes(self.joystick) #get virtual button input from analog axes
            # - Add the Dpad and js_axes buttons into our main buttons list -
            for x in js_dpads:
                js_buttons.append(x)
            for x in js_axes:
                js_buttons.append(x)
            if(js_buttons != []):
                self.buttons[key_num] = js_buttons[0]
                return True
        return False

### - Brief demo program of how to use this library effectively -
##screen = pygame.display.set_mode([200,200])
##player_1_controls = Controls(8, "ctrl") #joystick/controller player
##for x in range(0,8): #configure all controls
##    print("Configure button " + str(x))
##    while not player_1_controls.configure_key(x):
##        get_keys()
##    pygame.time.delay(350)
##    get_keys()
##while True:
##    get_keys() #grab all keys pressed
##    print(player_1_controls.get_input())
##
##    pygame.time.delay(500) #I don't want to kill IDLE from printing too much...LOL
##    pygame.display.flip()
