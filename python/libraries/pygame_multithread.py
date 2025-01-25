##"pygame_multithread.py" library ---VERSION 0.03---
## - This library's purpose is to make it possible to utilize some Pygame function calls from a thread other than the main thread -
##Copyright (C) 2024  Lincoln V.
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

#Import other people's libraries
import pygame, _thread, math, time
#Import my own libraries
import controller, SFX_ph

#NOTE: SFX is imported under a different name so that some internal variables used to keep track of whether a client SFX_Manager() needs to play a sound from a server SFX_Manager()
#   does not conflict since both are used with the PygameHandler() class.

# - This class should be initialized by the main thread and the clock() function should be run regularly by the main thread. Other than that, the other functions can be run by any thread -
class PygameHandler():
    #thread_count is the number of threads which will need to access pygame function calls and draw things on pygame's display window.
    #window_display_size is the size of the window which this function will create.
    #internal_display_size is the size of the surface which each thread will have access to. For good performance (since this library will usually be used for split-screen), this size can be considerably smaller than window_display_size.
    #sound_names is a list of all sound files which any of the threads will use. These files will be imported into SFX_Manager()s from the SFX.py library,
    #   and the threads can use the return_data() function from their own SFX_Manager() class to make the SFX_Manager() class in the main thread play their sound file for them.
    # *** NOTE: This software makes NO PROVISION for playing music in a random thread whatsoever. You will have to account for that in your own programming by placing all pygame.mixer calls in your main thread ***
    def __init__(self, thread_count, window_display_size, internal_display_size, sound_names, button_ct):
        # - *** General setup *** -
        self.threads = thread_count
        pygame.init()

        # - *** Display setup *** -
        self.screen = pygame.display.set_mode(window_display_size, pygame.RESIZABLE)
        self.screen.fill([0,0,0])
        pygame.display.flip()

        # - Generate all the smaller surfaces which each thread will have access to -
        self.update_flag = [] #this holds True/False flags for all surfaces which tell the PygameHandler() whether to update a particular mini-display's output on the main window.
        self.internal_screen = []
        self.screen_pos = [] #this holds the position at which each surface will be drawn onto the pygame window surface. By default, all screens are tiled across the screen starting from the top left and descending to the bottom right.
        for x in range(0,self.threads):
            self.update_flag.append(True)
            self.internal_screen.append(pygame.Surface(internal_display_size))
            self.screen_pos.append([0,0]) #proper screen positioning will be taken care of with the line beneath.
        self.update_surface_positions()

        # - Set up some time counters for all threads so that we can get our average FPS -
        self.timers = []
        for x in range(0,self.threads):
            self.timers.append([0.1, time.time()]) #format: last frametime, time that last frame was rendered at

        # - *** SFX setup *** -
        self.sfx_managers = [] #this is going to get messy...we're using a SFX_Manager() class to manage EACH THREAD's sound effect requests...LOL (I couldn't think of a better way, so... \_=)_/ )
        self.sfx_queues = [] #Basically, a thread can make multiple sound requests before the main thread manages to answer them. I am using a queue system so that no sounds get lost...
        self.player_pos = [] #this controls the volume of all sound effects based on where they are located relative to these positions...
        for x in range(0,self.threads):
            self.sfx_managers.append(SFX_ph.SFX_Manager())
            self.sfx_queues.append([])
            self.player_pos.append([0,0])
            for files in sound_names: #add all sound files we plan on using to the SFX_Manager()
                self.sfx_managers[len(self.sfx_managers) - 1].add_sound(files)

        # - *** Controller setup *** -
        self.controls = []
        self.buttons_pressed = []
        self.buttons_pressed_lock = []
        for x in range(0,self.threads):
            self.buttons_pressed.append([])
            self.buttons_pressed_lock.append(_thread.allocate_lock())
            self.controls.append(controller.Controls(button_ct, "kb")) #all controllers are initialized as a controller with button_ct buttons which take input through the keyboard.

# *** CONTROLLER FUNCTIONS *** #

    # - This is the equivalent function to controller.Controls().get_input(), but this can be called by ANY thread -
    def get_input(self, thread_num):
        with self.buttons_pressed_lock[thread_num]:
            return_value = self.buttons_pressed[thread_num][:]
        return return_value

    # - This returns a list of all buttons mapped to some control input from a controller.Controls() object -
    def get_controls(self, thread_num):
        return self.controls[thread_num].buttons[:]

# *** DISPLAY FUNCTIONS *** #

    # - This function returns the surface assigned to a certain thread. The thread should be able to draw on it once it receives it from this function and the changes should transfer to the surface stored in this class -
    def get_surface(self, thread_num):
        return self.internal_screen[thread_num]

    # - This function allows moving all thread surface positions around. pos[] format: [thread pos 1, thread pos 2, thread pos 3...]. By default, the surfaces are tiled across the screen -
    def update_surface_positions(self, pos=None):
        x = 0
        y = 0
        greatest_surf = 0 #this is used to check how far down a new row of surfaces must be placed to prevent overlap with the surfaces above.
        for b in range(0,self.threads):
            if(pos == None):
                if(greatest_surf < self.internal_screen[b].get_height()): #update which surface on this row is the tallest
                    greatest_surf = self.internal_screen[b].get_height()
                self.screen_pos[b] = [x,y] #actual surface position
                x += self.internal_screen[b].get_width() #update the position of where the next surface will go horizontally
                if(x > self.screen.get_width() - self.internal_screen[b].get_width()): #this would place this thread's surface offscreen? Move it to the next row below.
                    y += greatest_surf
                    greatest_surf = self.internal_screen[b].get_height()
                    x = 0 #reset our X position...
            else: #if the program wants to manually place surfaces...let them!
                self.internal_screen[b] = pos[b][:]

    # - This function allows moving one thread's surface position around -
    def update_surface_position(self, thread_num, pos):
        self.screen_pos[thread_num] = pos[:]

    # - This function allows changing all thread surface sizes. size[] format: [thread 1 size, thread 2 size...] By default, the surfaces are organized so they can be evenly tiled across the screen -
    def update_surface_sizes(self, size=None):
        for x in range(0,self.threads):
            if(size == None): #organize all thread sizes so they can be evenly tiled across the screen
                threads_per_dimension = math.ceil(math.sqrt(self.threads))
                new_size = [int(self.screen.get_width() / threads_per_dimension), int(self.screen.get_height() / threads_per_dimension)]
                self.internal_screen[x] = pygame.Surface(new_size)
            else: #custom user-specified surface size
                self.internal_screen[x] = pygame.Surface(size[x])

    # - Tells the PygameHandler() when a particular thread's surface is completely drawn and ready for blitting onto the main window -
    def surface_flip(self, thread_num):
        self.update_flag[thread_num] = True

    # - Tells whether the PygameHandler() has updated a particular thread's surface yet -
    def surface_flipped(self, thread_num):
        return not self.update_flag[thread_num]

    # - Updates the FPS received from a particular thread -
    def update_fps(self, thread_num):
        self.timers[thread_num][0] = time.time() - self.timers[thread_num][1] #update our frametime
        self.timers[thread_num][1] = time.time() #update when our last frame was drawn

    # - Returns the average FPS from every thread -
    def get_avg_fps(self):
        avg_frametimes = 0
        for x in range(0,self.threads):
            avg_frametimes += self.timers[x][0]
        avg_frametimes /= self.threads #self.threads should NEVER equal 0, so this shouldn't ever raise an error.
        avg_fps = 1 / avg_frametimes
        return avg_fps

# *** SOUND FUNCTIONS *** #

    # - Adds sounds to the sound queue. sound_payload[] is a list which is returned from SFX.SFX_Manager().return_data() -
    def add_sounds(self, thread_num, sound_payload):
        self.sfx_queues[thread_num].append(sound_payload)

    def set_player_pos(self, thread_num, pos):
        self.player_pos[thread_num] = pos[:]

    def draw_minimap(self, thread_num, minimap):
        with self.sfx_managers[thread_num].lock:
            self.sfx_managers[thread_num].draw_minimap(minimap)

    def set_volume(self, thread_num, volume):
        self.sfx_managers[thread_num].sound_volume = volume

    def get_volume(self, thread_num):
        return self.sfx_managers[thread_num].sound_volume

    # - This should be called at the beginning of a game if sounds are not being played for some reason -
    def reset_idnum(self):
        SFX_ph.ID_NUM = 0

# *** MAIN THREAD ONLY FUNCTIONS *** #

    # - This allows you to change what the controls for each thread are configured as by setting control_payload to controller.Controls().return_data() -
    def update_controller(self, thread_num, control_payload):
        self.controls[thread_num].enter_data(control_payload)

    # - This function takes every internal_screen[] surface and blits them to the actual pygame window using the main thread (this function MUST be run with the program's main thread) -
    def draw(self):
        update_rects = []
        for x in range(0,self.threads):
            if(self.update_flag[x] == True): #IF a display update is ready, we'll draw it.
                self.screen.blit(self.internal_screen[x], self.screen_pos[x])
                update_rects.append([
                    self.screen_pos[x][0],
                    self.screen_pos[x][1],
                    self.internal_screen[x].get_width(),
                    self.internal_screen[x].get_height()
                    ])
            self.update_flag[x] = False
        pygame.display.update(update_rects) #only update the portions of the screen containing new frames

    # - Update ALL things needed for the PygameHandler() class to function properly (grab input, play requested sounds, etc.) -
    def clock(self):
        # - Update all sound volumes based on player positions (player positions should be updated by individual threads) -
        for x in range(0,self.threads):
            with self.sfx_managers[x].lock:
                self.sfx_managers[x].clock(self.player_pos[x])
        # - Plays ALL sounds for ALL SFX_Managers() (that's gonna be a lot of sounds...) -
        for x in range(0,self.threads):
            for payload in range(0,len(self.sfx_queues[x])): #play ALL the requested sounds over multiple return_data() calls from the thread's SFX_Manager()
                self.sfx_managers[x].enter_data(self.sfx_queues[x][payload],self.player_pos[x]) #this will play all requested sounds in ONE return_data() call
            self.sfx_queues[x] = [] #clear all the requested sounds since we've played them now
        # - Update the keypresses which controller.py currently sees as "active" -
        window_data = controller.get_keys() #return value/format: [wants_quit, resize]
        # - Update which key numbers are currently pressed by each controller -
        for x in range(0,self.threads):
            with self.buttons_pressed_lock[x]:
                self.buttons_pressed[x] = self.controls[x].get_input()
        return window_data
