##"HUD.py" library ---VERSION 0.07---
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

import font
import pygame
import time

class HUD(): #a sort-of simple class which should allow you to design HUDs which scale to your screen size nicely.
    def __init__(self): #set all dem variables up...
        #HUD elements: "vertical bar" [pos,size,colors,value], "horizontal bar" [pos,size,colors,value],
        #    "text" [pos,size,colors,text], "scrolling text" [pos,[size of text,length of text bar],colors,text,scroll_pos]
        self.HUD_attribs = [] #HUD_attribs format: ["type of HUD element",[data regarding the HUD element],HUD value]
        #simply a list of flags which correspond to each HUD element (True/False). Tells whether the element should be scaled or not.
        self.scaled_HUD_attribs = []
        self.default_display_size = [640,480] #you add HUD elements in this screen resolution, than the program upscales the elements for you.

        #some variables to adjust tick speeds and other stuff
        self.timecounter = time.time() #stores the current time to measure how many times draw_HUD has been called in that time
        self.tick_speed = 8 #how many "ticks" of HUD activity happen per second?
        self.tickcounter = 0

        #This is a variable which simply keeps track of the current scale of our HUD elements.
        self.rectangular_scale = 1.0

    #a (hopefully) easier way to create an HUD element than using append()
    def add_HUD_element(self,element_type,element_data,scaling=True):
        self.HUD_attribs.append([element_type,element_data[:]])
        self.scaled_HUD_attribs.append(scaling)

    #quick function which scales HUD coordinates to whichever scale is smaller, X or Y AND returns an integer version of them.
    def scale_coords(self,coords,screen_scale):
        coords[0] = int(coords[0] * screen_scale[0])
        coords[1] = int(coords[1] * screen_scale[1])
        return coords

    def draw_HUD(self,screen): #draws all the HUD elements we added
        #get the scale of our screen
        screen_scale = [screen.get_width() * 1.0 / self.default_display_size[0], screen.get_height() * 1.0  / self.default_display_size[1]]

        #get our "rectangular" scale - the smaller of the two scales, X or Y.
        if(screen_scale[0] > screen_scale[1]):
            rectangular_scale = screen_scale[1]
        else:
            rectangular_scale = screen_scale[0]
        self.rectangular_scale = rectangular_scale

        #update our HUD tick variables
        if(self.timecounter + (1 / self.tick_speed) < time.time()): #has (1 / tickspeed) seconds elapsed?
            self.timecounter = time.time() #reset the time counter
            self.tickcounter += 1

        #iterate through all HUD elements
        x = 0 #index counter
        for element in self.HUD_attribs:
            if(element[0] == "text"): #print out the text at A) the size and position, SCALED according to screen size.
                #draw a 1px. outline square, then draw the text overtop
                unscaled_position = element[1][0][:] #grab our unscaled coordinates
                if(self.scaled_HUD_attribs[x]): #are we scaling?
                    unscaled_position = self.scale_coords(unscaled_position,screen_scale) #attempt to scale our coordinates
                colors = element[1][2]
                text = element[1][3]
                text_scale = element[1][1] / font.SIZE * rectangular_scale
                text_size = text_scale * font.SIZE
                if(colors[1] != None): #we actually want a background color?
                    pygame.draw.rect(screen,colors[1],[unscaled_position[0],unscaled_position[1],int(text_size * len(list(text))),int(text_scale * font.SIZE)],0) #draw the background color first
                if(colors[2] != None): #we actually want an outline color?
                    pygame.draw.rect(screen,colors[2],[unscaled_position[0],unscaled_position[1],int(text_size * len(list(text))),int(text_scale * font.SIZE)],int(1 * rectangular_scale + 1)) #draw the outline next
                if(colors[0] != None): #we actually want a text color?
                    font.draw_words(text, [unscaled_position[0],unscaled_position[1]], colors[0], text_scale, screen) #draw the actual words next
            elif(element[0] == "scrolling text"):
                text_box_size = element[1][1][1] #the size (in characters) of our scrolling text box
                #draw a 1px. outline square, then draw the text overtop
                unscaled_position = element[1][0][:] #grab our unscaled coordinates
                if(self.scaled_HUD_attribs[x]): #are we scaling?
                    unscaled_position = self.scale_coords(unscaled_position,screen_scale) #attempt to scale our coordinates
                colors = element[1][2]
                text = element[1][3]
                scroll_pos = self.tickcounter % (len(text) + 3) #find out what scroll position our text should be in
                if(len(text) < text_box_size): #we don't need to scroll since we can fit the whole message onscreen?
                    scrolling_text = text
                else: #now we have to scroll
                    scrolling_text = (text + (" " * 3) + text)[scroll_pos:text_box_size + scroll_pos] #complexicated line of code which scrolls the text...
                text_scale = element[1][1][0] / font.SIZE * rectangular_scale
                text_size = text_scale * font.SIZE
                if(colors[1] != None): #we actually want a background color?
                    pygame.draw.rect(screen,colors[1],[unscaled_position[0],unscaled_position[1],int(text_size * text_box_size),int(text_scale * font.SIZE)],0) #draw the background color first
                if(colors[2] != None): #we actually want an outline color?
                    pygame.draw.rect(screen,colors[2],[unscaled_position[0],unscaled_position[1],int(text_size * text_box_size),int(text_scale * font.SIZE)],int(1 * rectangular_scale + 1)) #draw the outline next
                if(colors[0] != None): #we actually want a text color?
                    font.draw_words(scrolling_text, [unscaled_position[0],unscaled_position[1]], colors[0], text_scale, screen) #draw the actual words next
            elif(element[0] == "vertical bar"): #print a vertical loading bar (higher value always goes UP, 100 = max)
                #Format: [pos,size,colors,value]
                #colors[0] = bar color
                #colors[2] = background color
                #colors[1] = bar outline
                size = element[1][1] #grab out our HUD attributes
                unscaled_position = element[1][0][:] #grab our unscaled coordinates
                if(self.scaled_HUD_attribs[x]): #are we scaling?
                    unscaled_position = self.scale_coords(unscaled_position,screen_scale) #attempt to scale our coordinates
                value = element[1][3]
                colors = element[1][2]
                if(colors[1] != None): #we actually want a background color?
                    pygame.draw.rect(screen,colors[1],[unscaled_position[0],unscaled_position[1], int(size[0] * rectangular_scale), int(size[1] * rectangular_scale)],0) #draw the background color first
                if(colors[2] != None): #we actually want an outline color?
                    pygame.draw.rect(screen,colors[2],[unscaled_position[0],unscaled_position[1], int(size[0] * rectangular_scale), int(size[1] * rectangular_scale)],int(1 * rectangular_scale + 1)) #draw the outline next
                pygame.draw.rect(screen,colors[0],[unscaled_position[0] + int(1 * rectangular_scale),unscaled_position[1] + int((size[1] + 1 - size[1] * value) * rectangular_scale),int((size[0] - 2) * rectangular_scale), int((size[1] * value - 2) * rectangular_scale)],0) #draw the bar second-last
            elif(element[0] == "horizontal bar"): #print a horizontal loading bar (higher value is to the right)
                #Format: [pos,size,colors,value]
                #colors[0] = bar color
                #colors[2] = background color
                #colors[1] = bar outline
                size = element[1][1] #grab out our HUD attributes
                unscaled_position = element[1][0][:] #grab our unscaled position coords
                if(self.scaled_HUD_attribs[x]): #are we scaling?
                    unscaled_position = self.scale_coords(unscaled_position,screen_scale) #attempt to scale our coordinates
                value = element[1][3]
                colors = element[1][2]
                if(colors[1] != None): #we actually want a background color?
                    pygame.draw.rect(screen,colors[1],[unscaled_position[0],unscaled_position[1], int(size[0] * rectangular_scale), int(size[1] * rectangular_scale)],0) #draw the background color first
                if(colors[2] != None): #we actually want an outline color?
                    pygame.draw.rect(screen,colors[2],[unscaled_position[0],unscaled_position[1], int(size[0] * rectangular_scale), int(size[1] * rectangular_scale)],int(1 * rectangular_scale + 1)) #draw the outline next
                pygame.draw.rect(screen,colors[0],[unscaled_position[0] + int(1 * rectangular_scale),unscaled_position[1] + int(1 * rectangular_scale),int((size[0] * value - 2) * rectangular_scale), int((size[1] - 2) * rectangular_scale)],0) #draw the bar second-last
            x += 1 #increment our index counter

    def update_HUD_element(self,element_index,element_value): #allows you to change the status of an HUD element.
        self.HUD_attribs[element_index][1] = element_value

    def update_HUD_element_value(self,index,value): #allows you to change the value of an HUD element.
        self.HUD_attribs[index][1][3] = value

    def update_HUD_element_color(self,index,colors): #allows you to change the color of an HUD element.
        self.HUD_attribs[index][1][2] = colors[:]

    def delete_HUD(self,element_index): #deletes a HUD element of your choice
        del(self.HUD_attribs[element_index])

###Example code: Create some HUD elements!
##anhud = HUD()
###add an HUD element which is scrolling text. Outline of white, background of grey, green letters of size 15 px on 640x480 screen.
##anhud.add_HUD_element("scrolling text",[[10,10],[100,6],[[255,255,255],[100,100,100],[0,255,0]],"Demo text which is scrolling"])
###add an HUD element which should be some text; Outline of green, background of blue, letters of white.
##anhud.add_HUD_element("text",[[20,40],50,[[255,255,255],[0,0,255],[0,255,0]],"test text"])
###add an HUD element - vertical bar, outline of red, bar of white, no background.
##anhud.add_HUD_element("vertical bar", [[100,100],[10,50],[[255,255,255],[255,0,0],None],0.0])
###add an HUD element - horizontal bar, outline of red, bar of white, no background.
##anhud.add_HUD_element("horizontal bar", [[150,150],[250,100],[[255,255,255],[255,0,0],None],0.0])
##
##screen = pygame.display.set_mode([640,480],pygame.RESIZABLE)
##pygame.display.set_caption("HUD.py Library Test")
##
##running = True
##countdown = 20
##bar = 0.0
##while running:
##    countdown -= 1 #update a counter variable
##    if(countdown == 0):
##        countdown = 32768
##
##    bar += 0.01 #update our vertical bar
##    if(bar > 100):
##        bar = 0
##        
##    pygame.display.flip() #normal screen blanking and flipping routine
##    screen.fill([0,0,0])
##
##    anhud.update_HUD_element_value(0,"Value: " + str(countdown))
##    anhud.update_HUD_element_value(2,bar / 100)
##    anhud.update_HUD_element_value(3,bar / 100)
##
##    anhud.draw_HUD(screen) #draw our lovely HUD
##
##    for event in pygame.event.get():
##        if(event.type == pygame.QUIT):
##            running = False
##
##pygame.quit()
