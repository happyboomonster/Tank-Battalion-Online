##"GFX.py" library ---VERSION 0.15---
## - REQUIRES: "font.py" library
## - For creating basic graphical effects (usually based on particles) in the same scale as your screen in a game -
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

import time
import pygame
import font
import random
import _thread

# - This function prevents colors from being outside their max/min values due to timing errors -
def colorsafe(color):
    for x in range(0,len(color)):
        if(color[x] > 255):
            color[x] = 255
        elif(color[x] < 0):
            color[x] = 0
    return color

class Particle(): #a square onscreen which can A) change size, B) change color, and C) change position over time.
    def __init__(self, start_map_pos, finish_map_pos, start_size, finish_size, start_color, finish_color, time_start, time_finish, form=2):
        self.pos = start_map_pos[:] #position attributes
        self.destination = [start_map_pos[:], finish_map_pos[:]]
        self.delta_position = [ #find the amount we need to move over...well, the amount of time specified.
                self.destination[1][0] - self.destination[0][0],
                self.destination[1][1] - self.destination[0][1]
                ]
        
        self.size = start_size #size attributes
        self.goal_size = [start_size, finish_size]
        self.delta_size = self.goal_size[1] - self.goal_size[0]

        self.color = start_color[:] #color attributes
        self.goal_color = [start_color[:], finish_color[:]]
        self.delta_color = [
            finish_color[0] - start_color[0],
            finish_color[1] - start_color[1],
            finish_color[2] - start_color[2],
            ]

        self.start_time = time_start #timing attributes
        self.finish_time = time_finish
        self.total_time = self.finish_time - self.start_time

        self.form = form #form attribute

        self.active = False #this becomes true once the particle actually needs to be drawn onscreen.
        self.timeout = False #this becomes true once the particle is finished its job (providing a temporary effect onscreen)

        self.last_clock = time.time() #this tells us roughly how long it has been since the particle's state has been updated.

    def clock(self): #update the particle's position, color, size, etc.
        # - First: Figure out how much time has passed since the last call of clock() -
        time_passed = time.time() - self.last_clock
        self.last_clock = time.time()
        # - Check: Should the particle become active (needs timing handling, drawing onscreen) -
        if(self.active == False): #no?
            if(self.start_time < time.time()): #the particle SHOULD be active now?
                self.active = True
        else: #we need to handle the particle...
            # - First: Check how much time we have left -
            time_left = self.finish_time - time.time()
            if(time_left <= 0): #check whether the particle's time is out
                self.timeout = True
            else:
                # - First: Create our timing ration based on time_passed and self.total_time -
                time_ratio = (time_passed / self.total_time)
                # - First: Update the particle's position -
                self.calculated_move = [ #how far do we need to shift over our particle's position?
                    self.delta_position[0] * time_ratio,
                    self.delta_position[1] * time_ratio
                    ]
                self.pos[0] += self.calculated_move[0]
                self.pos[1] += self.calculated_move[1]
                # - Secondly: Update the particle's size -
                self.calculated_size =  self.delta_size * time_ratio
                self.size += self.calculated_size
                # - Thirdly: Update the particle's color (the hardest part of updating a particle) -
                self.calculated_color = [
                    self.delta_color[0] * time_ratio,
                    self.delta_color[1] * time_ratio,
                    self.delta_color[2] * time_ratio
                    ]
                self.color[0] += self.calculated_color[0]
                self.color[1] += self.calculated_color[1]
                self.color[2] += self.calculated_color[2]

    def draw(self, TILE_SIZE, screen_scale, offset, screen): #draw the particle onscreen, accounting for a map offset
        # - First, we check that our color is valid... -
        self.color = colorsafe(self.color)
        # - NOW we can draw the particle -
        if(self.form == 1):
            pygame.draw.rect(screen, self.color, [self.pos[0] * TILE_SIZE * screen_scale[0] - offset[0] * TILE_SIZE * screen_scale[0], self.pos[1] * TILE_SIZE * screen_scale[1] - offset[1] * TILE_SIZE * screen_scale[1], self.size * TILE_SIZE * screen_scale[0], self.size * TILE_SIZE * screen_scale[1]],0)
        elif(self.form == 2): #circles will always remain square, even when they should be scaled as rectangular. Scaled by the X axis.
            pygame.draw.circle(screen, self.color, [self.pos[0] * TILE_SIZE * screen_scale[0] - offset[0] * TILE_SIZE * screen_scale[0], self.pos[1] * TILE_SIZE * screen_scale[1] - offset[1] * TILE_SIZE * screen_scale[1]], self.size * TILE_SIZE * screen_scale[0])
        else: #we want to draw text?
            font.draw_words(self.form, [self.pos[0] * TILE_SIZE * screen_scale[0] - offset[0] * TILE_SIZE * screen_scale[0], self.pos[1] * TILE_SIZE * screen_scale[1] - offset[1] * TILE_SIZE * screen_scale[1]], self.color, self.size * screen_scale[0] / font.SIZE * TILE_SIZE, screen)

    def return_data(self,precision=2): #returns data for netcode transmission
        return [self.pos, #position attributes
            [[round(self.destination[0][0],precision), round(self.destination[0][1],precision)],[round(self.destination[1][0],precision), round(self.destination[1][1],precision)]],
            [round(self.delta_position[0],precision), round(self.delta_position[1],precision)], #find the amount we need to move over...well, the amount of time specified.
            
            round(self.size,precision), #size attributes
            [round(self.goal_size[0],precision),round(self.goal_size[1],precision)],
            round(self.delta_size,precision),

            [round(self.color[0],precision), round(self.color[1],precision), round(self.color[2],precision)], #color attributes
            [[round(self.goal_color[0][0],precision), round(self.goal_color[0][1],precision), round(self.goal_color[0][2],precision)],[round(self.goal_color[1][0],precision), round(self.goal_color[1][1],precision), round(self.goal_color[1][2],precision)]],
            [round(self.delta_color[0],precision), round(self.delta_color[1],precision), round(self.delta_color[2],precision)],

            round(time.time() - self.start_time,precision), #timing attributes
            round(time.time() - self.finish_time,precision),
            round(self.total_time,precision),

            self.form, #form attribute

            self.active, #this becomes true once the particle actually needs to be drawn onscreen.
            self.timeout, #this becomes true once the particle is finished its job (providing a temporary effect onscreen)

            round(time.time() - self.last_clock,precision) #this tells us roughly how long it has been since the particle's state has been updated.
                ]

    def enter_data(self, data): #enters data from netcode
        self.pos = data[0] #position attributes
        self.destination = data[1]
        self.delta_position = data[2] #find the amount we need to move over...well, the amount of time specified.
        
        self.size = data[3] #size attributes
        self.goal_size = data[4]
        self.delta_size = data[5]

        self.color = data[6] #color attributes
        self.goal_color = data[7]
        self.delta_color = data[8]

        self.start_time = time.time() - data[9] #timing attributes
        self.finish_time = time.time() - data[10]
        self.total_time = data[11]

        self.form = data[12] #form attribute

        self.active = data[13] #this becomes true once the particle actually needs to be drawn onscreen.
        self.timeout = data[14] #this becomes true once the particle is finished its job (providing a temporary effect onscreen)
        self.last_clock = time.time() - data[15]

class GFX_Manager(): # - A class which helps transmit a large amount of particles over netcode without overloading transmission protocols -
    def __init__(self):
        # - Particle tracking variables -
        self.last_id = 0
        self.max_id = 1000 #max of 1000 explosions/fires happening at once

        # - Constants -
        self.TIMEOUT = 0.075 #seconds...This way fire doesn't lag people's PCs to death...because the only way to update the position for fire is to spawn new fire and wait for the old fire to despawn.

        # - Particle list (Format: [ ["explosion/fire",ID#,parameters,start_time], ["explosion/fire",ID#,parameters,start_time]... ] ) -
        self.particle_effects = []

        # - lock for threading -
        self.lock = _thread.allocate_lock()

    def create_explosion(self, position, explosion_radius, particle_sizes, start_colors, end_colors, duration, time_offset, optional_words): #creates an explosion...
        self.last_id += 1
        params = [position, explosion_radius, particle_sizes, start_colors, end_colors, duration, time_offset, optional_words]
        self.particle_effects.append(["explosion", self.last_id, params, time.time()])

    def create_fire(self, location): #start something on fire!
        self.last_id += 1
        self.particle_effects.append(["fire", self.last_id, location, time.time()])

    def purge(self): #deletes old particles
        decrement = 0
        for x in range(0,len(self.particle_effects)):
            if(time.time() - self.particle_effects[x - decrement][3] > self.TIMEOUT):
                del(self.particle_effects[x - decrement])
                decrement += 1

    def draw(self, particles, current_frame, TILE_SIZE): #adds the particles to the player's particles list to be drawn and deletes only the explosions after they have been drawn
        decrement = 0
        for x in range(0,len(self.particle_effects)):
            if(self.particle_effects[x - decrement][0] == "explosion"): #an explosion occurred?
                position = self.particle_effects[x - decrement][2][0]
                explosion_radius = self.particle_effects[x - decrement][2][1]
                particle_sizes = self.particle_effects[x - decrement][2][2]
                start_colors = self.particle_effects[x - decrement][2][3]
                end_colors = self.particle_effects[x - decrement][2][4]
                duration = self.particle_effects[x - decrement][2][5]
                time_offset = self.particle_effects[x - decrement][2][6]
                optional_words = self.particle_effects[x - decrement][2][7]
                create_explosion(particles, position, explosion_radius, particle_sizes, start_colors, end_colors, duration, time_offset, optional_words, TILE_SIZE)
                del(self.particle_effects[x - decrement])
                decrement += 1
            elif(self.particle_effects[x - decrement][0] == "fire"): #fire? - Format: ["fire",ID#,[X,Y],time.time()]
                create_fire(particles,self.particle_effects[x - decrement][2],current_frame)

    def enter_data(self, data): #Copies the data from data[] IF we haven't already copied that data into our GFX manager
        # - Start by deleting all fire effects -
        decrement = 0
        for x in range(0,len(self.particle_effects)):
            if(self.particle_effects[x - decrement][0] == "fire"):
                del(self.particle_effects[x - decrement])
                decrement += 1
        for x in data: #add the new effects into self.particle_effects
            if(x[1] > self.last_id or self.last_id == 1000 and x[1] < self.last_id): #this is a new effect?
                self.last_id = x[1] #make sure we don't add the effect again...
                self.particle_effects.append([x[0], x[1], x[2], time.time() - x[3]])

    def return_data(self,precision=2):
        data = [] #get the data from self.particle_effects
        for x in self.particle_effects:
            data.append([x[0], x[1], x[2], round(time.time() - x[3])])
        return data

gfx_quality = 1.0

#pretty self explanatory. Give the function the parameters it needs, and it makes a big explosion.
def create_explosion(particles, position, explosion_radius, particle_sizes, start_colors, end_colors, duration, time_offset=0, optional_words=None, TILE_SIZE=1): #creates an explosion with varying color, choosable size and position.
    global gfx_quality
    for x in range(0,int(pow(explosion_radius * TILE_SIZE, 2) * gfx_quality)): #create a bunch of square particles next
        random.shuffle(start_colors) #shuffle our color options
        random.shuffle(end_colors)
        random_start_color = start_colors[0] #pick a random color for both ending and starting our effect based on the choices we allow in our parameters above
        random_end_color = end_colors[0]
        #add the finished particle to our collecive list
        particles.append(Particle([position[0], position[1]], [position[0] + random.randint(-explosion_radius * 100, explosion_radius * 100) / 100, position[1] + random.randint(-explosion_radius * 100, explosion_radius * 100) / 100], particle_sizes[0], particle_sizes[1], random_start_color[:], random_end_color[:], time.time() + time_offset, time.time() + duration + time_offset, 1))
    for x in range(0,5): #create a bunch of circle particles for start
        random.shuffle(start_colors) #shuffle our color options
        random.shuffle(end_colors)
        random_start_color = start_colors[0] #pick a random color for both ending and starting our effect based on the choices we allow in our parameters above
        random_end_color = end_colors[0]
        #add the finished particle to our collecive list
        particles.append(Particle([position[0], position[1]], [position[0] + random.randint(-explosion_radius * 100, explosion_radius * 100) / 100, position[1] + random.randint(-explosion_radius * 100, explosion_radius * 100) / 100], particle_sizes[0] / 2, particle_sizes[1] / 2, random_start_color[:], random_end_color[:], time.time() + time_offset + (duration / (x + 1) / 2), time.time() + duration + time_offset + (duration / (x + 1) / 2), 2))
    if(optional_words != None):
        for x in range(0,int(explosion_radius * TILE_SIZE / 5)): #create a bunch of word particles
            random.shuffle(start_colors) #shuffle our color options
            random.shuffle(end_colors)
            random_start_color = start_colors[0] #pick a random color for both ending and starting our effect based on the choices we allow in our parameters above
            random_end_color = end_colors[0]
            #add the finished particle to our collecive list
            particles.append(Particle([position[0], position[1]], [position[0] + random.randint(-explosion_radius * 100, explosion_radius * 100) / 100, position[1] + random.randint(-explosion_radius * 100, explosion_radius * 100) / 100], particle_sizes[0], particle_sizes[1], random_start_color[:], random_end_color[:], time.time() + time_offset, time.time() + duration + time_offset, optional_words))

last_fire_frame = 0 #helps keep track of how much fire to draw
last_frame_time = 0
last_fire_time = time.time()
fire_draw_interval = 0.05
fire_color = [255,0,0]
fire_color_change = 2
MAX_FIRE_FRAME = 5 #maximum of 5 particles created per frame

def create_fire(particles,location,current_frame): #run this every frame you want the fire to last for. Creates a cartoonish fire from top view.
    global last_fire_frame
    global last_fire_time
    global fire_draw_interval
    global fire_color
    global fire_color_change
    global last_frame_time
    global gfx_quality
    if(current_frame == last_fire_frame or time.time() - last_fire_time >= fire_draw_interval / gfx_quality):
        if(current_frame != last_fire_frame): #we need to set a timing value if we JUST started a new frame.
            last_frame_time = round((time.time() - last_fire_time) / fire_draw_interval,0)
        last_fire_frame = current_frame #update the frame bookmark
        #add the GFX particles to the particles list
        for x in range(0,int(last_frame_time * gfx_quality)): #make sure we account for missed frames and lag
            if(x > MAX_FIRE_FRAME): #we need to account for missed frames, that's true, but we also don't want to re-lag the machine to death...
                break
            particles.append(Particle([location[0] + 0.5, location[1] + 0.5], [location[0] + 0.5 + random.randint(-5,5) / 10, location[1] + 0.5 + random.randint(-5,5) / 10], 0.1, 0.05, fire_color[:], [50,50,50], time.time(), time.time() + 1, random.randint(1,2)))
        # - Update fire_color -
        #First: We start by changing R by fire_color_change
        fire_color[0] += random.randint(-int(fire_color_change * round((time.time() - last_fire_time) / fire_draw_interval,0)),int(fire_color_change * round((time.time() - last_fire_time) / fire_draw_interval,0)))
        if(fire_color[0] >= 255): #can't pass 255! Pygame doesn't like it if I do that...
            fire_color[0] = 255
        elif(fire_color[0] < 0):
            fire_color[0] = 0
        #Next: We can change G upwards IF it is below R by 25%. Else, we're gonna have to change that one down.
        G_RNG = [-fire_color_change,fire_color_change]
        fire_color[1] += random.randint(int(G_RNG[0] * round((time.time() - last_fire_time) / fire_draw_interval,0)),int(G_RNG[1] * round((time.time() - last_fire_time) / fire_draw_interval,0)))
        if(fire_color[1] > fire_color[0] * 0.50 or fire_color[1] >= 255):
            G_RNG[1] = -1
            fire_color[1] = 255 #can't pass 255! Pygame doesn't like it if I do that...
        if(fire_color[1] < 0):
            fire_color[1] = 0
        #Next: We can change B upwards IF it is below B by 25%. Else, we're gonna have to change that one down.
        B_RNG = [-fire_color_change,fire_color_change]
        fire_color[2] += random.randint(int(B_RNG[0] * round((time.time() - last_fire_time) / fire_draw_interval,0)),int(B_RNG[1] * round((time.time() - last_fire_time) / fire_draw_interval,0)))
        if(fire_color[2] > fire_color[1] * 0.50 or fire_color[2] >= 255):
            B_RNG[1] = -1
            fire_color[2] = 255 #can't pass 255! Pygame doesn't like it if I do that...
        elif(fire_color[2] < 0):
            fire_color[2] = 0
        last_fire_time = time.time() #update the timing counter

###short demo test for the Particle() class
##screen = pygame.display.set_mode([640,480])
##
##particles = []
##
##running = True
##while running:
##    for event in pygame.event.get(): #event loop
##        if(event.type == pygame.QUIT):
##            running = False
##
##    if(round(time.time() % 0.1, 2) == 0): #randomly create a bunch of particles, 10 in a second
##        particles.append(Particle([random.randint(0,32),random.randint(0,24)], [random.randint(0,32),random.randint(0,24)], random.randint(1,5), random.randint(1,5), [random.randint(0,255),random.randint(0,255),random.randint(0,255)], [0,0,0], time.time(), time.time() + 5, "words"))
##
##    if(round(time.time() % 0.1, 3) == 0): #create an explosion on occasion
##        create_explosion(particles, [random.randint(0,32), random.randint(0,24)], random.randint(2,10), [0.1, random.randint(1,3)], [[255,0,0],[255,255,0]],[[0,0,0],[100,100,100],[50,50,50]], 0.80, 0, "boom")
##
##    decrement = 0
##    for x in range(0,len(particles)): #update the particle states and draw them onscreen
##        particles[x + decrement].clock()
##        particles[x + decrement].draw(1, [20, 20], [0, 0], screen)
##        if(particles[x + decrement].timeout == True):
##            del(particles[x + decrement])
##            decrement -= 1
##
##    pygame.display.flip() #update the screen and clear it for next frame
##    screen.fill([0,0,0])
##
##pygame.quit()

        
###short demo test for the GFX_Manager class
##screen = pygame.display.set_mode([640,480])
##
##particles = []
##gfx = GFX_Manager()
##client_gfx = GFX_Manager()
##
##fire_pos = [0,0]
##
##current_frame = 0
##
##running = True
##while running:
##    # - Manage the framecounter -
##    current_frame += 1
##    if(current_frame > 65535):
##        current_frame = 0
##    
##    for event in pygame.event.get(): #event loop
##        if(event.type == pygame.QUIT):
##            running = False
##
##    #***This code down below would happen on the server***
##    if(round(time.time() % 0.0025, 2) == 0): #randomly create a bunch of particles, 10 in a second
##        fire_pos[0] += random.randint(-1,1) / 20
##        fire_pos[1] += random.randint(-1,1) / 20
##        fire_pos[0] = abs(fire_pos[0])
##        fire_pos[1] = abs(fire_pos[1])
##        if(fire_pos[0] > screen.get_width()):
##            fire_pos[0] = screen.get_width()
##        if(fire_pos[1] > screen.get_height()):
##            fire_pos[1] = screen.get_height()
##        gfx.create_fire(fire_pos[:])
##
##    if(round(time.time() % 0.2, 3) == 0): #create an explosion on occasion
##        gfx.create_explosion([random.randint(0,32), random.randint(0,24)], random.randint(3,8), [0.1, random.randint(2,5)], [[255,0,0],[255,255,0]],[[0,0,0],[100,100,100],[50,50,50]], 0.80, 0, "boom")
##
##    gfx.purge() #delete old particle entries
##
##    gfx_data = gfx.return_data()
##
##    #***This code would happen on the client***
##    client_gfx.enter_data(gfx_data)
##    client_gfx.draw(particles, current_frame, 1)
##
##    # - Update the particles -
##    decrement = 0
##    for x in range(0,len(particles)): #update the particle states and draw them onscreen
##        particles[x + decrement].clock()
##        particles[x + decrement].draw(1, [20, 20], [0, 0], screen)
##        if(particles[x + decrement].timeout == True):
##            del(particles[x + decrement])
##            decrement -= 1
##
##    pygame.display.flip() #update the screen and clear it for next frame
##    screen.fill([0,0,0])
##
##pygame.quit()
