##"entity.py" library ---VERSION 0.87---
## - For managing basically any non-map object within Tank Battalion Online (Exception: bricks) -
##Copyright (C) 2025  Lincoln V.
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

import time #very important for pacing entity movement (e.g. rotation)
import _thread #for allocate_lock() stuff; Each object has a lock in it.
import pygame #for transforming tiles
import random
import math
import GFX #for fire in gas tank / explosive tip bullet
import netcode #for data filtering in enter_data() in all entities

path = ""

class Powerup(): #for collectible items within the map
    def __init__(self, image, powerup_type, location=[0.0, 0.0]):
        # - Needed for external functions -
        self.type = "Powerup" #define what this class is
        self.lock = _thread.allocate_lock()

        # - Enter_data() data format -
        self.DATA_FMT = ["<class 'str'>", ["<class 'float'>","<class 'float'>"], "<class 'int'>"]
        
        # - Positional stuff -
        self.map_location = location #where are we on the map?

        # - Reference constants -
        self.POWERUP_CT = 6

        #the effects of grabbing a certain powerup
        self.powerup_effects = [
            ]
        for x in range(0,self.POWERUP_CT): #add the powerup effects
            self.powerup_effects.append("powerups[" + str(x) + "] = True")

            
        self.powerup_effects.append("shells[0] += 6") #+X hollow shells
        self.powerup_effects.append("shells[1] += 4") #+X regular shells
        self.powerup_effects.append("shells[2] += 2") #+X explosive shells
        self.powerup_effects.append("shells[3] += 2") #+X disk shells

        # - Visual stuff -
        self.image = image

        # - Timing -
        self.spawn_time = time.time() #this value never changes; used for managing image_vfx.
        self.DESPAWN_TIME = 7.5 #seconds till despawn

        # - Which type of powerup is this? -
        self.powerup_number = powerup_type

        # - Should this powerup be deleted? -
        self.despawn = False

    def clock(self): #call this function each time the computation loop runs in a game.
        if(time.time() - self.spawn_time >= self.DESPAWN_TIME): #time to despawn since nobody wanted this powerup?
            self.despawn = True

    def return_collision(self, TILE_SIZE): #returns the powerup's collision coordinates as map/tile coordinates
        # - Calculate the powerup's map coordinates for collision -
        screen_coordinates = self.map_location[:] #x1 and y1 collision coordinates
        # - Add x2 and y2 collision coordinates -
        screen_coordinates.append(0)
        screen_coordinates.append(0)
        screen_coordinates[2] = screen_coordinates[0] + 1
        screen_coordinates[3] = screen_coordinates[1] + 1
        # - Return our coordinates -
        return screen_coordinates

    def use(self,tank): #call this when a tank has touched the powerup. The effects of the powerup will be instantly applied, and the powerup will disappear.
        if(self.powerup_number < self.POWERUP_CT): #we used a powerup, and didn't get an item?
            tank.finish_powerup(self.powerup_number)
            tank.powerups_used[self.powerup_number] -= 1 #we used one less powerup.
        exec("tank." + self.powerup_effects[self.powerup_number])
        self.despawn = True

    #draws the powerup/item onscreen, keeping in mind the player's position within the arena.
    def draw(self, screen, screen_scale, arena_offset, TILE_SIZE):
        # - Calculate the bullet's onscreen coordinates -
        screen_coordinates = [self.map_location[0] * TILE_SIZE * screen_scale[0], self.map_location[1] * TILE_SIZE * screen_scale[1]]
        #offset the coordinates because of our arena offset.
        screen_coordinates[0] -= arena_offset[0] * TILE_SIZE * screen_scale[0]
        screen_coordinates[1] -= arena_offset[1] * TILE_SIZE * screen_scale[1]
        #draw the powerup/item onscreen
        if(screen_coordinates[0] > -TILE_SIZE * screen_scale[0] and screen_coordinates[0] < screen.get_width()): #only draw if it's actually going to be onscreen
            if(screen_coordinates[1] > -TILE_SIZE * screen_scale[1] and screen_coordinates[1] < screen.get_height()):
                screen.blit(pygame.transform.scale(self.image,[int(TILE_SIZE * screen_scale[0]), int(TILE_SIZE * screen_scale[1])]), [int(screen_coordinates[0]), int(screen_coordinates[1])])

    #draws a yellow pixel on the minimap at the location of a powerup.
    def draw_minimap(self, minimap_surf):
        minimap_surf.set_at([int(round(self.map_location[0],0)),int(round(self.map_location[1],0))],[255,255,0])

    def return_data(self, precision=2, clear_flags=None): #gathers data so this can be sent over netcode (certain attributes do not need to be sent)
        return [
            self.type,
            [float(round(self.map_location[0],precision)),float(round(self.map_location[1],precision))],
            self.powerup_number
            ]

    def enter_data(self, data): #enters data from Powerup.return_data() IF the data is valid (to prevent server crashes)
        if(netcode.data_verify(data, self.DATA_FMT)):
            self.map_location[0] = data[1][0]
            self.map_location[1] = data[1][1]
            self.powerup_number = data[2]
        else:
            print("[ENTITY] Powerup failed to enter data! Data: " + str(data))

class Bullet(): #specs_multiplier format: [ damage buff/nerf, penetration buff/nerf ]
    def __init__(self, image, team_name, shell_type, direction, specs_multiplier, tank):
        # - Needed for external functions -
        self.type = "Bullet" #define what this class is
        self.lock = _thread.allocate_lock()

        # - Enter_data() data format (there's two possible formats) -
        self.DATA_FMT = [
            ["<class 'str'>", ["<class 'float'>","<class 'float'>"], "<class 'float'>", "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>", "<class 'str'>", "<class 'int'>",
             "<class 'list'>", "<class 'str'>", "<class 'float'>"],
            ["<class 'str'>", ["<class 'float'>","<class 'float'>"], "<class 'float'>", "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>", "<class 'str'>", "<class 'int'>",
             "<class 'list'>", "<class 'NoneType'>", "<class 'float'>"],
            ["<class 'str'>", ["<class 'float'>","<class 'float'>"], "<class 'int'>", "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>", "<class 'str'>", "<class 'int'>",
             "<class 'list'>", "<class 'str'>", "<class 'float'>"],
            ["<class 'str'>", ["<class 'float'>","<class 'float'>"], "<class 'int'>", "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>", "<class 'str'>", "<class 'int'>",
             "<class 'list'>", "<class 'NoneType'>", "<class 'float'>"]
            ]

        # - Who shot this bullet? We need to increment the damage counter for that tank when we hit a target -
        self.tank_origin = tank
        
        # - Positional stuff -
        self.map_location = [0.0, 0.0] #where are we on the map?
        self.direction = direction

        # - Reference constants -
        self.SHELL_NUM_TO_NAME = ["hollow", "regular", "explosive", "disk"]
        self.shell_specs = [ #Format: [damage, penetration]
            [8, 8], #hollow
            [12, 12], #regular
            [20, 7], #explosive
            [18, 14] #disk
            ]
        self.shell_vfx_reference = [
            None,
            "directional blit",
            None,
            "rotation"
            ]
        self.shell_collision_offset = [
            4,
            7,
            3,
            3
            ]
        self.shell_explosion_colors = [
            [ [100,100,100], [150,150,150] ],
            [ [100,100,100], [150,150,150], [200,200,200] ],
            [ [255,0,0],[255,255,0],[100,100,0] ],
            [ [100,100,0],[255,255,0],[50,50,0],[150,150,0] ]
            ]

        # - Bullet specs -
        self.shell_type = shell_type #4 types: 'hollow', 'regular', 'explosive', 'disk'.
        self.damage =  self.shell_specs[self.shell_type][0] * specs_multiplier[0] #how much damage did I do...?
        self.penetration = self.shell_specs[self.shell_type][1] * specs_multiplier[1] #how fast do I move?
        self.fire_inflict = specs_multiplier[2] #do we set enemy engine on fire??
        if(self.shell_type == 2): #explosive round?
            self.fire_inflict = 10
        #20x20 dimensions; How much smaller than 1 tile should the bullet's collision box be?
        self.COLLISION_OFFSET = self.shell_collision_offset[self.shell_type]
        self.team = team_name #this way friendly fire can be turned off since we know which team shot the bullet.
        self.destroyed = False #this flag is necessary for handling damage encounters

        # - Visual stuff -
        self.image = image
        self.shell_vfx = self.shell_vfx_reference[self.shell_type]
        self.rotation_speed = 2 #RPM; used for disk shells.
        self.explosion_colors = self.shell_explosion_colors[self.shell_type]

        # - Timing -
        self.old_time = time.time()
        self.time_difference = time.time() - self.old_time
        self.spawn_time = time.time() #this value never changes; used for managing image_vfx.

    def __str__(self):
        return ("Bullet damage: " + str(self.damage) + "\n" +
              "Penetration: " + str(self.penetration) + "\n" +
              "Shell type: " + self.SHELL_NUM_TO_NAME[self.shell_type] + "\n" +
              "Collision offset: " + str(self.COLLISION_OFFSET) + "\n" +
              "End of report.")

    def clock(self, particles, framecounter): #call this function each time the computation loop runs in a game.
        self.time_difference = time.time() - self.old_time
        self.old_time = time.time()

        # - Handle drawing fire on the tank + damage numbers from fire -
        if(self.fire_inflict > 1.025 and str(type(particles)) == "<class 'list'>"): #Are we going to set fire to someone's engine?? Add particles!
            GFX.create_fire(particles,self.map_location,framecounter)
        elif(self.fire_inflict > 1.025): #this is for if we are using a GFX_Manager() object instead of a Particle() list.
            particles.create_fire(self.map_location)

    def move(self): #move the bullet, how simple.
        speed = (self.penetration / 4.75) #calculate the bullet's speed in tiles/second based on its penetration
        if(self.direction == 0): #we're moving up
            self.map_location[1] -= speed * self.time_difference
        elif(self.direction == 180): #we're moving down
            self.map_location[1] += speed * self.time_difference
        elif(self.direction == 270): #right
            self.map_location[0] += speed * self.time_difference
        elif(self.direction == 90): #left
            self.map_location[0] -= speed * self.time_difference

    def return_collision(self, TILE_SIZE): #returns the bullet's collision coordinates as map/tile coordinates
        # - Calculate the bullet's map coordinates for collision -
        screen_coordinates = self.map_location[:] #x1 and y1 collision coordinates
        # - Add x2 and y2 collision coordinates -
        screen_coordinates.append(0)
        screen_coordinates.append(0)
        screen_coordinates[2] = screen_coordinates[0] + 1
        screen_coordinates[3] = screen_coordinates[1] + 1
        # - Take into account the collision offset needed for each bullet type -
        screen_coordinates[0] += (self.shell_collision_offset[self.shell_type] / TILE_SIZE) / 2
        screen_coordinates[1] += (self.shell_collision_offset[self.shell_type] / TILE_SIZE) / 2
        screen_coordinates[2] -= (self.shell_collision_offset[self.shell_type] / TILE_SIZE) / 2
        screen_coordinates[3] -= (self.shell_collision_offset[self.shell_type] / TILE_SIZE) / 2
        # - Return our final coordinates -
        return screen_coordinates

    #draws the bullet onscreen, keeping in mind the player's position within the arena.
    def draw(self, screen, screen_scale, arena_offset, TILE_SIZE):
        # - Calculate the bullet's onscreen coordinates -
        screen_coordinates = [self.map_location[0] * TILE_SIZE * screen_scale[0], self.map_location[1] * TILE_SIZE * screen_scale[1]]
        #offset the coordinates because of our arena offset.
        screen_coordinates[0] -= arena_offset[0] * TILE_SIZE * screen_scale[0]
        screen_coordinates[1] -= arena_offset[1] * TILE_SIZE * screen_scale[1]
        if(screen_coordinates[0] > -TILE_SIZE * screen_scale[0] and screen_coordinates[0] < screen.get_width()): #only draw if it's actually going to be onscreen
            if(screen_coordinates[1] > -TILE_SIZE * screen_scale[1] and screen_coordinates[1] < screen.get_height()):
                if(self.shell_vfx == 'rotation'): #we need the bullet continuously rotating as it moves.
                    #degrees; how many the image needs to be rotated
                    rotation = self.rotation_speed * 360 * (time.time() - self.spawn_time)
                    rotated_image = pygame.transform.rotate(self.image, rotation % 360) #rotate the image
                    # - Find the scale between rotated_image and self.image -
                    image_scale = [rotated_image.get_width() / self.image.get_width(), rotated_image.get_height() / self.image.get_height()]
                    # - Find the difference in pixels between rotated_image and self.image -
                    image_difference = [(rotated_image.get_width() - self.image.get_width()) / 2.0, (rotated_image.get_height() - self.image.get_height()) / 2.0]
                    # - Scale "rotated_image" -
                    scaled_image = pygame.transform.scale(rotated_image, [int(TILE_SIZE * image_scale[0] * screen_scale[0]), int(TILE_SIZE * image_scale[1] * screen_scale[1])])
                    # - Draw it onscreen, taking into account the extra pixels created by rotating the image -
                    screen.blit(scaled_image, [int(screen_coordinates[0] - image_difference[0] * screen_scale[0]), int(screen_coordinates[1] - image_difference[1] * screen_scale[1])])
                elif(self.shell_vfx == 'directional blit'): #we need to rotate the bullet image based on which direction it points
                    #we don't need to account for extra pixels because we're doing right-angle rotation
                    rotated_image = pygame.transform.rotate(self.image, self.direction)
                    screen.blit(pygame.transform.scale(rotated_image, [int(TILE_SIZE * screen_scale[0]), int(TILE_SIZE * screen_scale[1])]), [int(screen_coordinates[0]), int(screen_coordinates[1])])
                else: #NO vfx? Simple! Just blit the image onscreen! (with scaling, of course)
                    screen.blit(pygame.transform.scale(self.image,[int(TILE_SIZE * screen_scale[0]), int(TILE_SIZE * screen_scale[1])]), [int(screen_coordinates[0]), int(screen_coordinates[1])])

    #draws a pixel on the minimap at the location of a bullet. Color varies based on which team shot it and whose team the client player is on.
    def draw_minimap(self, minimap_surf, home_team, useless_parameter=True): #useless_paramter is there so that I can use the same draw command for Tank() and Bullet() objects.
        if(home_team != self.team): #an enemy shot this bullet? Color = orange.
            minimap_surf.set_at([int(round(self.map_location[0],0)),int(round(self.map_location[1],0))],[255,125,0])
        else: #friendly fire? Color = blue.
            minimap_surf.set_at([int(round(self.map_location[0],0)),int(round(self.map_location[1],0))],[0,0,255])

    def return_data(self, precision=2, clear_flags=None): #returns bullet data to be sent over netcode
        if(self.destroyed == True): #compress our True/False flags into 1/0s to reduce netcode transmissions
            destroyed = 1
        else:
            destroyed = 0
        return [
            self.type,
            [float(round(self.map_location[0],precision)),float(round(self.map_location[1],precision))],
            self.direction,
            self.shell_type,
            float(round(self.damage,precision)),
            float(round(self.penetration,precision)),
            float(round(self.fire_inflict,precision)),
            self.team,
            destroyed,
            self.explosion_colors,
            self.shell_vfx,
            float(round(time.time() - self.spawn_time,precision)) #this is needed for proper disk shell rotation.
            ]

    def enter_data(self, data): #enters data into the Bullet() object from Bullet.return_data()
        verified = False
        for x in self.DATA_FMT:
            if(netcode.data_verify(data, x)):
                verified = True
                break
        if(verified):
            self.map_location[0] = data[1][0]
            self.map_location[1] = data[1][1]
            self.direction = data[2]
            self.shell_type = data[3]
            self.damage = data[4]
            self.penetration = data[5]
            self.fire_inflict = data[6]
            self.team = data[7]
            if(data[8] == 1):
                self.destroyed = True
            else:
                self.destroyed = False
            self.explosion_colors = data[9]
            self.shell_vfx = data[10]
            self.spawn_time = time.time() - data[11]
        else:
            print("[ENTITY] Bullet failed to enter data! Data: " + str(data))

class Brick():
    def __init__(self, HP, armor):
        self.type = "Tank" #I know, this isn't a tank, but it makes the damage system handle bricks the way I want it to...
        self.HP = HP #setting armor and HP, pretty streightforward
        self.armor = armor
        self.team = None #bricks don't have a team - what would bricks look like if they did?!?
        self.fire = 0 #what would happen if a brick had fire in its gas tank?????? :P

class Tank():
    def __init__(self, images='pygame.image.load()...', names=["tank name","team name"], skip_image_load=False, team_num=0, team_ct=2):
        # - Needed for external functions -
        self.type = "Tank" #define what this class is
        self.lock = _thread.allocate_lock()

        # - Enter_data() data format -
        self.DATA_FMT = [
            ["<class 'str'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'float'>", "<class 'str'>", "<class 'str'>", "<class 'int'>",
             "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             ["<class 'float'>", "<class 'float'>"], "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'int'>", "<class 'int'>", "<class 'float'>", "<class 'int'>",
             "<class 'int'>", ["<class 'int'>", "<class 'int'>", "<class 'int'>", "<class 'int'>"], "<class 'list'>", "<class 'float'>",
             "<class 'NoneType'>", "<class 'int'>", "<class 'int'>"],

            ["<class 'str'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'float'>", "<class 'str'>", "<class 'str'>", "<class 'int'>",
             "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             ["<class 'float'>", "<class 'float'>"], "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'int'>", "<class 'int'>", "<class 'float'>", "<class 'int'>",
             "<class 'int'>", ["<class 'int'>", "<class 'int'>", "<class 'int'>", "<class 'int'>"], "<class 'list'>", "<class 'float'>",
             "<class 'str'>", "<class 'int'>", "<class 'int'>"],

            ["<class 'str'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'float'>", "<class 'str'>", "<class 'str'>", "<class 'int'>",
             "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             ["<class 'float'>", "<class 'float'>"], "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'int'>", "<class 'int'>", "<class 'float'>", "<class 'int'>",
             "<class 'NoneType'>", ["<class 'int'>", "<class 'int'>", "<class 'int'>", "<class 'int'>"], "<class 'list'>", "<class 'float'>",
             "<class 'NoneType'>", "<class 'int'>", "<class 'int'>"],

            ["<class 'str'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'float'>", "<class 'str'>", "<class 'str'>", "<class 'int'>",
             "<class 'int'>", "<class 'float'>", "<class 'float'>", "<class 'float'>",
             ["<class 'float'>", "<class 'float'>"], "<class 'float'>", "<class 'float'>", "<class 'float'>",
             "<class 'int'>", "<class 'int'>", "<class 'float'>", "<class 'int'>",
             "<class 'NoneType'>", ["<class 'int'>", "<class 'int'>", "<class 'int'>", "<class 'int'>"], "<class 'list'>", "<class 'float'>",
             "<class 'str'>", "<class 'int'>", "<class 'int'>"]
            ]
        
        self.POWERUP_DATA_FMT = ["<class 'float'>", "<class 'str'>", "<class 'NoneType'>", "<class 'bool'>"] #powerups need a separate data format filter since they have too many data format combinations to include in self.DATA_FMT
        
        # - Tank specs -
        self.speed = 1.00 #how many tiles can be crossed in a second? How many turns can be made in 1/2 second?
        self.damage_multiplier = 1.00 #if this is above 1, the tank can shoot more than normal damage output
        self.penetration_multiplier = 1.00 #if this is above 1, the tank can shoot more than normal penetration.
        self.RPM = 6.00 #bullets tank can shoot in a minute (Rounds Per Minute)
        self.direction = 0 #tank always starts facing upwards.
        self.HP = 100.0 #tank health points
        self.armor = 20.0 #tank armor points (helps deflect shots from damaging main health points
        self.current_shell = 0 #which shell do we have currently selected to load into our gun? (0=hollow, 1=regular, 2=explosive, 3=disk)
        self.team = names[1]
        self.team_num = team_num #this flag isn't used in this class itself, but I might migrate to using it more to speed up checking which team a player is on
        self.name = names[0] #this tank player has a name!!! Mind blowing.
        self.destroyed = False #well, this one's pretty self explanatory.
        #this flag simply tells the computer whether we need to spawn a location at this tank.
        self.explosion_done = True #Once done, you need to set this flag to True

        #bookmarks; for creating health bars and such.
        self.start_HP = self.HP
        self.start_armor = self.armor
        #More bookmarks, but these are for keeping track of how many shells, powerups the tank has used. Basically, this is currency/money stuff.
        self.shells_used = [
            0,
            0,
            0,
            0
            ]
        self.powerups_used = [
            0,
            0,
            0,
            0,
            0,
            0
            ]
        self.total_damage = 0
        self.kills = 0
        #this variable must be managed outside this tank; There's no way for me to tell when your bullet simply hit a wall from inside entity.py.
        self.missed_shots = 0
        # - This is needed for account.py's upgrade details system -
        self.account_stats = [[self.damage_multiplier,self.penetration_multiplier],[self.RPM],[self.armor],[self.speed]]

        # - Tank specs based on timing -
        #seconds left of fuel fire; updated when hit, set to seconds remaining,
        #then slowly decremented by time_difference each time clock() runs.
        self.fire = 0
        self.fire_inflict = 1 #when this isn't 1, we can inflict fire on people if our shells hit.
        self.fire_cause = None #this becomes a pointer to a tank object when the tank is on fire. This is needed so that we can increment that tank's total damage counter.
        self.last_shot = time.time() #when did our tank fire last? (governs when we may shoot again, based on RPM)
        self.damage_second = 0 #this is how much damage gets done to our tank each second.
        self.last_damage_second = time.time()
        self.spotted = [] #this is a list of which teams have spotted this tank for a certain period of time. This is ONLY used by a server, and is NOT sent to the clients.
        for x in range(0,team_ct):
            self.spotted.append(time.time())
        self.client_spotted = time.time() #this records the last time this tank object has had enter_data() called. It is used to detect whether a tank has been spotted by a client's team recently.
        self.MAX_SPOTTED = 2.5 #seconds; If (time.time() - self.client_spotted) is greater than MAX_SPOTTED, this tank is considered to *not* have been spotted.

        # - Set this flag to True if you are a client and want to shoot! -
        self.shot_pending = False
        # - Set this flag to a number if you want to use a powerup!
        self.powerup_request = None
        # - Set this flag to a string to request the server to spawn a message in the form of a powerup! -
        self.message_request = None #None = no message
        # - I can censor messages server-side! -
        self.MESSAGE_WHITELIST = ["yes","no","maybe","understood",
                    "1","2","3","4","5","6",
                    "up","left","down","right",
                    "attack","retreat","reform",
                    ]

        # - Powerup timing constants -
        self.POWERUP_COOLDOWN = 15.0 #seconds
        self.POWERUP_DURATION = 15.0 #seconds

        # - Equipment installed within the tank (Format: [# of hollow, regular#, explosive#, disk#]) -
        self.shells = [30, 25, 15, 15]
        #List of powerups in index order: Improved Fuel, Fire Extinguisher, Dangerous Loading, Explosive Tip,
        #Amped Gun, Extra Armor
        #List format: Number in quotes = powerup being used right now, "number" seconds left of powerup;
        #Number without quotes = Powerup cooldown occuring right now.
        #None: No powerup available in this slot.
        #True: Powerup ready for use!
        self.powerups = [True, True, True, True, True, True]
        #Powerup effects
        self.powerup_effects = [ # ***Numbers in quotes do not get restored to their default value after the powerup has been used***
            [["self.speed", 1.35]], #Improved Fuel: +35% speed.
            [["self.fire", "0"], ["self.speed", 0.9]], #Fuel Fire Suppressant: Extinguishes fire in gas tank. -10% speed
            [["self.RPM", 1.50], ["self.HP", "0.90"]], #Dangerous Loading: +50% RPM, -10% HP per use
            [["self.damage_multiplier", 1.25], ["self.penetration_multiplier", 0.95], ["self.RPM", 0.95], ["self.fire_inflict",20]], #Explosive Tip: +25% Damage/shot, -5% Penetration, -5% Loading Speed, Inflicts fire in enemy's fuel tank.
            [["self.penetration_multiplier", 1.25], ["self.HP", "0.90"]], #Amped Gun: +25% Penetration, -10% HP per use
            [["self.armor", 1.50], ["self.speed", 0.5]] #Extra Armor: -50% speed, -50% damage intake (+50% Armor)
            ]

        # - Tank positioning -
        self.map_location = [0.0, 0.0] #where are we in the map? (20x20 tile coordinates)
        self.screen_location = [0.0, 0.0] #where are we on the screen? (screen scale coordinates)
        self.overall_location = [0.0, 0.0]
        self.goal_rotation = 0 #how many degrees do we need to rotate if we're not facing the direction we want?
        self.old_direction = self.direction #where *were* we when we started rotating?
        self.last_motion = [0.0, 0.0] #the last movement we made from the last move() call
        self.last_unmove_motion = [0.0, 0.0, False] #the last movement unmove() made, followed by whether it is worth continuing to move in the direction we last moved (self.last_motion).

        # - Timing stuff -
        self.old_time = time.time() #time variable
        self.time_difference = 0 #how long between each call of "clock()"?
        self.last_message = time.time() #when did the player send a message last?
        self.MESSAGE_COOLDOWN = 1.5 #seconds; How long does the player have to wait in between each message he sends?
        self.unmove_timer = time.time() #this helps us with timing WHEN we should activate different kinds of centering to make tanks move as smoothly as possible through the arena
        self.PARALLEL_CENTERING_TIMER = 0.125 #this is linked to unmove_timer (see above). This is the WHEN value in seconds.

        # - Rotation threshold constant - how close to desired direction must be achieved? -
        self.ROTATION_THRESHOLD = 10

        # - When you turn a corner and just turn too early...this will help you move around the corner anyways. How much imprecision (in blocks) is the player allowed to make turns? -
        self.POS_CORRECTION_MAX_THRESHOLD = 0.25 #if we're more than X blocks off, the player doesn't deserve positioning correction.
        self.POS_CORRECTION_MIN_THRESHOLD = 0.025 #if we're less than X blocks off, we don't need to bother with positioning correction.

        # - Visual stuff -
        self.spotted_images = "dummy image"
        if(str(type(images)) != "<class 'str'>"): #sometimes I use a string as an image IF I don't want to continually be loading images from disk when using Tank() objects server-side. When I do, I use "str" classes instead.
            self.spotted_images = images
            self.unspotted_image = pygame.Surface([self.spotted_images[0].get_width(), self.spotted_images[0].get_height()])
            self.unspotted_image.set_colorkey([0,0,0])
            self.unspotted_image.blit(self.spotted_images[0],[0,0])
            for x in range(0,self.spotted_images[0].get_width()): #use grey dithering to dim the self.spotted_image to generate self.unspotted_image
                for y in range(0,self.spotted_images[0].get_width()):
                    if(y % 2 == 0):
                        if(x % 2 == 0):
                            if(self.spotted_images[0].get_at([x,y])[3] != 0):
                                self.unspotted_image.set_at([x,y],[125,125,125])
                            else:
                                self.unspotted_image.set_at([x,y],[0,0,0]) #make sure our unspotted_image also has alpha channel where it is needed
                    else:
                        if(x % 2 != 0):
                            if(self.spotted_images[0].get_at([x,y])[3] != 0):
                                self.unspotted_image.set_at([x,y],[75,75,75])
                            else:
                                self.unspotted_image.set_at([x,y],[0,0,0]) #make sure our unspotted_image also has alpha channel where it is needed
        else:
            self.unspotted_image = self.spotted_images[0]
        self.image_ct = 0
        self.shuffle_timer = time.time()
        self.SHUFFLE_SPEED = 0.175 #smaller number makes the tread animations shuffle more quickly. Frame time = self.SHUFFLE_SPEED / self.speed
                    

        # - Bullet images -
        global path
        if(not skip_image_load):
            self.shell_images = [
                pygame.image.load(path + "../../pix/ammunition/hollow_shell.png"),
                pygame.image.load(path + "../../pix/ammunition/regular_shell.png"),
                pygame.image.load(path + "../../pix/ammunition/explosive_shell.png"),
                pygame.image.load(path + "../../pix/ammunition/disk_shell.png")
                ]
        else: #load dummy image placeholders instead of wasting disk usage on loading images
            self.shell_images = [
                "di",
                "di",
                "di",
                "di"
                ]

    def __str__(self):
        return ("Armor: " + str(self.armor) + "\n" + "HP: " + str(self.HP) + "\n" +
              "Current Direction (specific): " + str(self.direction) + "\n" +
              "Rounded Direction: " + str(self.old_direction) + "\n" +
              "Map position: " + str(self.map_location) + "\n" +
              "Screen position: " + str(self.screen_location) + "\n" +
              "Seconds till next shot loaded: " + str((60 / self.RPM) - (time.time() - self.last_shot)) + "\n" +
              "Next shot type: " + str(self.current_shell) + "\n" +
              "Shells in tank: " + str(self.shells[0]) + " hollow shells left \n" +
              "\t " + str(self.shells[1]) + " regular shells left \n" +
              "\t " + str(self.shells[2]) + " explosive shells left \n" +
              "\t " + str(self.shells[3]) + " disk shells left \n" +
              "Powerup Cooldown state: " + str(self.powerups) + "\n" +
              "Tank Damage/Penetration multipliers: " + str(self.damage_multiplier) + " , " + str(self.penetration_multiplier) + "\n" +
              "Tank speed/RPM: " + str(self.speed) + " , " + str(self.RPM) + "\n" +
              "Tank armor/HP: " + str(self.armor) + " , " + str(self.HP) + "\n" +
              "Tank Team: " + self.team + "\n" +
              "End of report.")

    # - Allows changing images mid-game -
    def load_image(self, images):
        if(self.image_ct > len(images) - 1): #avoid IndexErrors...
            self.image_ct = 0
        self.spotted_images = images
        self.unspotted_image = pygame.Surface([self.spotted_images[0].get_width(), self.spotted_images[0].get_height()])
        self.unspotted_image.set_colorkey([0,0,0])
        self.unspotted_image.blit(self.spotted_images[0],[0,0])
        for x in range(0,self.spotted_images[0].get_width()): #use grey dithering to dim the self.spotted_image to generate self.unspotted_image
            for y in range(0,self.spotted_images[0].get_width()):
                if(y % 2 == 0):
                    if(x % 2 == 0):
                        if(self.spotted_images[0].get_at([x,y])[3] != 0):
                            self.unspotted_image.set_at([x,y],[125,125,125])
                        else:
                            self.unspotted_image.set_at([x,y],[0,0,0]) #make alpha show where it's supposed to (our colorkey's black)
                else:
                    if(x % 2 != 0):
                        if(self.spotted_images[0].get_at([x,y])[3] != 0):
                            self.unspotted_image.set_at([x,y],[75,75,75])
                        else:
                            self.unspotted_image.set_at([x,y],[0,0,0]) #make alpha show where it's supposed to (our colorkey's black)

    # - This is needed for account.py's upgrade details system -
    def update_acct_stats(self):
        self.account_stats = [[self.damage_multiplier,self.penetration_multiplier],[self.RPM],[self.armor],[self.speed]]

    # - Sets map_location, overall_location properly from the location input and screen_location -
    def goto(self, location, TILE_SIZE=20, screen_scale=[1,1]):
        screen_offset = [ #calculate the screen offset in blocks
            self.screen_location[0] / screen_scale[0] / TILE_SIZE,
            self.screen_location[1] / screen_scale[1] / TILE_SIZE
            ]
        self.overall_location[0] = location[0] #now we set overall_location to location[]
        self.overall_location[1] = location[1]
        self.map_location[0] = location[0] - screen_offset[0] #now we set map_location.
        self.map_location[1] = location[1] - screen_offset[1]

    #takes values in degrees; Changes them so that they are not negative, or larger than 359.9(bar).
    def no_360_or_negative(self,direction):
        #we MAY NOT have a negative direction value, or one over 360.
        while (direction >= 360 or direction < 0):
            if(direction >= 360): #decrement self.direction by 360 then
                direction -= 360
            elif(direction < 0): #self.direction is less than 0?
                direction += 360
        return direction

    #takes values in degrees; Changes them so that they are always negative, and never smaller than than -359.9(bar).
    def no_360_or_positive(self,direction):
        #we MAY NOT have a positive direction value, or one over 360.
        while (direction <= -360 or direction > 0):
            if(direction <= -360): #increment self.direction by 360 then
                direction += 360
            elif(direction > 0): #self.direction is greater than 0?
                direction -= 360
        return direction

    #takes values in degrees; Changes them so that they are not smaller than -359.9(bar), or larger than 359.9(bar).
    def no_360(self,direction):
        #we MAY NOT have a negative direction value, or one over 360.
        while (direction >= 360 or direction <= -360):
            if(direction >= 360): #decrement self.direction by 360 then
                direction -= 360
            elif(direction <= -360): #self.direction is less than 0?
                direction += 360
        return direction

    def offset_360(self,direction): #offsets direction by +/-360 so that abs(direction) < 360.
        if(direction >= 0): #start by offseting direction by +/-360
            direction -= 360
        else:
            direction += 360
        # - Check if our variable is at exactly 360 (set it back to 0 then) -
        if(abs(direction) == 360): #positive/negative doesn't matter here
            direction = 0
        #finished!
        return direction

    def clock(self, TILE_SIZE=20, screen_scale=[1, 1],particles=[],current_frame=0,gfx=None,server=True): #call this function each time the computation loop runs in a game.
        self.time_difference = time.time() - self.old_time #set time_difference
        self.old_time = time.time() #reset old_time
        # - Update our overall position so that the server knows where we are -
        self.overall_location[0] = self.map_location[0] + (self.screen_location[0] / screen_scale[0]) / TILE_SIZE
        self.overall_location[1] = self.map_location[1] + (self.screen_location[1] / screen_scale[1]) / TILE_SIZE
        # - Check if we have been destroyed -
        if(self.HP < 0 and self.destroyed == False):
            # - If we already have fire in gas tank/engine, AND we're below 0HP, we need to make sure we increment the kill counter! -
            if(self.fire > 0 and server == True):
                self.fire_cause.kills += 1 #this crashes the client
            self.destroyed = True
            self.explosion_done = False
            self.speed = 3.75 #make sure we can spectate in a speedy manner
        # - Manage various time-based values in the tank; (fire, powerups) -
        if(self.fire > 0): #we need to slowly decrement our fire counter if we're on fire; we can't be burning forever!
            self.fire -= self.time_difference
            self.HP -= self.time_difference * 2.0 #fire can't be friendly!
            self.damage_second += self.time_difference * 2.0 #add our damage to our per-second damage counter
        if(self.fire < 0.025): #self.fire is very close to 0, or below it???
            self.fire = 0 #just set fire to streight 0 then.
        if(self.fire_inflict > 0): #are we able to inflict somebody else with fire right now?
            self.fire_inflict -= self.time_difference
        if(self.fire_inflict < 1.025): #this is 1.025 instead of 0.025 because fire_inflict has a value of 1 by default.
            self.fire_inflict = 1
        return_damage = False
        if(time.time() - self.last_damage_second >= 1): #check if we need to return our damage from fire in engine
            self.last_damage_second = time.time()
            return_damage = True
            if(round(self.damage_second, 0) > 0): #draw a damage number if we're taking more than 0 damage
                particles.append((GFX.Particle(self.overall_location, [self.overall_location[0], self.overall_location[1] - 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(round(self.damage_second, 0))))))

        # - Handle drawing fire on the tank + damage numbers from fire -
        if(self.fire > 0.025 and gfx != None): #fire in engine?? Add particles!
            gfx.create_fire(self.overall_location)
        elif(self.fire > 0.025):
            GFX.create_fire(particles,self.overall_location,current_frame)
                    
        # - Manage powerup cooldowns, both when in use, and when cooling down before next use -
        if(server):
            for x in range(0,len(self.powerups)):
                if(self.powerups[x] != True):
                    if(self.powerups[x] != None and str(type(self.powerups[x])) == "<class 'float'>"): #this is a cooldown period.
                        self.powerups[x] -= self.time_difference
                    elif(self.powerups[x] != None and str(type(self.powerups[x])) == "<class 'str'>"): #this is a usage time period.
                        self.powerups[x] = str(float(self.powerups[x]) - self.time_difference)
                    if(self.powerups[x] != None):
                        if(float(str(self.powerups[x])) < 0.025): #our powerup timer is basically at 0?
                            if(str(type(self.powerups[x])) == "<class 'float'>"): #our powerup cooldown is finished, and we can use our powerup again?
                                self.powerups[x] = True #make sure the computer knows that this powerup is ready for use!
                            elif(str(type(self.powerups[x])) == "<class 'str'>"): #our powerup timer is finished...now we have to wait for it to cool down...
                                self.powerups[x] = self.POWERUP_COOLDOWN #blehhhh. Who wants to wait 30 seconds before we can go 15% faster? Unplayable.
                                #Next, we have to "undo" the buff we gave our tank...
                                for b in range(0,len(self.powerup_effects[x])):
                                    #we only need to restore values which are stored as float values.
                                    if(str(type(self.powerup_effects[x][b][1])) == "<class 'float'>"):
                                       exec(self.powerup_effects[x][b][0] + " /= " + str(self.powerup_effects[x][b][1]))

        # - Return the damage done to this tank via fire -
        if(return_damage): #changing fire_cause crashes the client since it doesn't ever point to an object
            if(self.damage_second > 0.5):
                if(server == True):
                    self.fire_cause.total_damage += self.damage_second #increment that bad tank's damage counter who set fire to our gas tank/engine!
                damage_second = round(self.damage_second, 0) #we need to reset damage_second
                self.damage_second = 0
                return damage_second
            else:
                return None
        else:
            return None

    def reload_time(self): #returns the reload time left of the tank
        time_left = (60 / self.RPM) - (time.time() - self.last_shot)
        if(time_left <= 0): #we have a shell ready?
            return True
        else:
            return time_left

    #if the cooldown is finished, use a powerup! (this function is designed to be used in a client-server architecture, so it'll have to be used strangely to get it working on a local game)
    def use_powerup(self,powerup_number, server=True):
        if(server):
            if(self.powerup_request != None and self.powerup_request >= 0 and self.powerup_request < len(self.powerups)): #make sure that the client gave us a proper request...
                if(self.powerups[self.powerup_request] == True): #the cooldown is done, and the powerup is ready for use?
                    self.powerups_used[self.powerup_request] += 1 #we used this powerup again. Let's bump our counter for how many times we've used this!
                    self.powerups[self.powerup_request] = str(self.POWERUP_DURATION) #now our timer is counting! Use the powerup!
                    #Apply the buffs the powerup provides
                    for x in range(0,len(self.powerup_effects[self.powerup_request])):
                        #apply a buff/nerf to the variable in [x][0], multiplying the variable by [x][1]
                        exec(self.powerup_effects[self.powerup_request][x][0] + " *= " + str(self.powerup_effects[self.powerup_request][x][1]))
                    self.powerup_request = None
        else:
            self.powerup_request = powerup_number

    def finish_powerup(self,powerup_number): #un-applies the effects from a powerup
        if(str(type(self.powerups[powerup_number])) == "<class 'str'>"): #The powerup is currently in use?
            #Set the powerup to cooldown
            self.powerups[powerup_number] = self.POWERUP_COOLDOWN
            #Apply the de-buffs from the powerup
            for x in range(0,len(self.powerup_effects[powerup_number])):
                #apply a buff/nerf to the variable in [x][0], multiplying the variable by [x][1] ONLY if the [x][1] number is NOT in quotes
                if(str(type(self.powerup_effects[powerup_number][x][1])) != "<class 'str'>"):
                    exec(self.powerup_effects[powerup_number][x][0] + " /= " + str(self.powerup_effects[powerup_number][x][1]))

    def use_shell(self,shell_number): #changes which shell you're gonna shoot
        if(self.current_shell >= 0 and self.current_shell < len(self.shells)):
            if(self.current_shell != shell_number): #we only need to switch shells if we aren't already using the requested shell.
                self.current_shell = shell_number #change which shell we'll be shooting
                if((time.time() - self.last_shot) > (60.0 / self.RPM)): #if you are finished reloading...
                    self.last_shot = time.time() - (60 / self.RPM) + 2 #2.0 second cooldown before you can switch shells and shoot
                #else you just finish reloading like usual, and shoot once that is done.

    #attempts to move the tank in a direction;
    #If the tank is not already facing the direction, this function will rotate the tank over (rotate_period) seconds.
    def move(self, direction, TILE_SIZE, screen_scale=[1,1]):
        # - Find what direction we *were* moving in last (not pointing, moving) -
        was_moving_dir = -1
        if(self.last_motion[0] != 0):
            if(self.last_motion[0] > 0):
                was_moving_dir = 270
            else:
                was_moving_dir = 90
        elif(self.last_motion[1] != 0):
            if(self.last_motion[1] > 0):
                was_moving_dir = 180
            else:
                was_moving_dir = 0
        if(self.time_difference != 0):
            align_speed = self.speed * (1 / self.time_difference / 90) #if we aren't hitting 90+ FPS (chosen arbitrarily), we're NOT re-aligning ourselves at our normal speed. We'll clip into a wall (used for corner correction)!
        else:
            align_speed = self.speed
        #we MAY NOT have a negative direction value, or one over 360.
        self.direction = self.no_360_or_negative(self.direction)
        direction = self.no_360_or_negative(round(direction, 1)) #sine and cos functions are VERY INACCURATE, so rounding helps get rid of weird decimals (e.g. 90.000000000000001)
        #first we check if we are facing the direction we want. If so, we don't need to wait to rotate our tank.
        if(direction == self.old_direction): #we're already facing the direction we want?
            self.goal_rotation = 0 #set this back to 0 so that we don't feel like we need to rotate...
            self.direction = self.old_direction #in case self.direction was on an offset
            # - Now we need to actually move the tank -
            if(was_moving_dir != direction or self.last_unmove_motion[2] == False):
                self.last_unmove_motion[2] = False #clear our unmove flag for wall collision
                self.map_location[1] += -round(math.sin(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference #round() HAS to be here; otherwise sin(math.pi) != 0...and that causes problems.
                self.map_location[0] += round(math.cos(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference
                self.last_motion[1] = -round(math.sin(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference
                self.last_motion[0] = round(math.cos(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference
            # - Check if we just *barely* didn't make it around a corner, and let the player make the corner if so. Also check if we can center ourselves in the axis we're moving -
            elif(direction == was_moving_dir and self.last_unmove_motion[2] == True):
                self.shuffle_timer = time.time() #because we weren't able to move, we shouldn't animate the treads.
                # - Update our overall position so that it matches map_location -
                #if we've been in an unmove() state for at least N seconds, we can probably center ourselves on our movement axis without incurring screen shake due to perpendicular centering.
                if(time.time() - self.unmove_timer > self.PARALLEL_CENTERING_TIMER):
                    self.overall_location[0] = self.map_location[0] + (self.screen_location[0] / screen_scale[0]) / TILE_SIZE
                    self.overall_location[1] = self.map_location[1] + (self.screen_location[1] / screen_scale[1]) / TILE_SIZE
                    if(round(abs(math.cos(math.radians(direction) + math.pi/2)), 3) == 1.0): #we should center ourselves horizontally (sometimes at low FPS we don't touch the block we're driving into due to unmove. This fixes that)
                        self.overall_location[0] = float(round(self.overall_location[0], 0))
                    elif(round(abs(math.sin(math.radians(direction) + math.pi/2)), 3) == 1.0): #we should center ourselves vertically (sometimes at low FPS we don't touch the block we're driving into due to unmove. This fixes that)
                        self.overall_location[1] = float(round(self.overall_location[1], 0))
                    self.goto(self.overall_location, TILE_SIZE, screen_scale) #this HAS to be run to sync overall_location[] and map_location[] after the above 4 lines of code
                # - Handle perpendicular centering -
                if(abs(self.overall_location[1] - round(self.overall_location[1],0)) < self.POS_CORRECTION_MAX_THRESHOLD): #positioning precision must be within 0.2 blocks for this correction to take effect
                    if(abs(self.overall_location[1] - round(self.overall_location[1],0)) > self.POS_CORRECTION_MIN_THRESHOLD): #we don't have to be PERFECTLY precise tho...
                        if(self.last_motion[0] != 0): #movement was in the X axis, so we need to center ourselves on the Y axis
                            self.last_unmove_motion[2] = False #clear our unmove flag for wall collision
                            if(self.overall_location[1] - round(self.overall_location[1],0) > 0):
                                #decrease our Y position to get to the closest integer Y value
                                self.map_location[1] -= align_speed * self.time_difference
                            else:
                                #increase our Y position to get to the closest integer Y value
                                self.map_location[1] += align_speed * self.time_difference
                if(abs(self.overall_location[0] - round(self.overall_location[0],0)) < self.POS_CORRECTION_MAX_THRESHOLD): #we're centering ourselves by moving in the X axis
                    if(abs(self.overall_location[0] - round(self.overall_location[0],0)) > self.POS_CORRECTION_MIN_THRESHOLD):
                        # - Now we try and ensure that we slowly center ourselves on the square we are *mostly* on, so that we can make the corner anyways...even if we hit a wall -
                        if(self.last_motion[1] != 0): #movement is in the Y axis, so we need to center ourselves on the X axis
                            self.last_unmove_motion[2] = False #clear our unmove flag for wall collision
                            if(self.overall_location[0] - round(self.overall_location[0],0) > 0):
                                #decrease X pos to get to nearest integer X pos
                                self.map_location[0] -= align_speed * self.time_difference
                            else:
                                #increase X pos to get to nearest integer X pos
                                self.map_location[0] += align_speed * self.time_difference
        elif(direction == self.no_360_or_negative(self.old_direction + 180)): #are we reversing?
            self.goal_rotation = 0 #set this back to 0 so that we don't feel like we need to rotate...
            self.direction = self.old_direction
            # - Now we need to actually move the tank -
            if(was_moving_dir != direction or self.last_unmove_motion[2] == False):
                self.last_unmove_motion[2] = False #clear our unmove flag for wall collision
                self.map_location[1] += -round(math.sin(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference #round() HAS to be here; otherwise sin(math.pi) != 0...and that causes problems.
                self.map_location[0] += round(math.cos(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference
                self.last_motion[1] = -round(math.sin(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference
                self.last_motion[0] = round(math.cos(math.radians(direction) + math.pi/2), 3) * self.speed * self.time_difference
            # - Check if we just *barely* didn't make it around a corner, and let the player make the corner if so. Also try to center ourselves in the axis of our motion -
            elif(direction == was_moving_dir and self.last_unmove_motion[2] == True):
                self.shuffle_timer = time.time() #because we weren't able to move, we shouldn't animate the treads.
                # - Update our overall position so that it matches map_location -
                #if we've been in an unmove() state for at least N seconds, we can probably center ourselves on our movement axis without incurring screen shake due to perpendicular centering.
                if(time.time() - self.unmove_timer > self.PARALLEL_CENTERING_TIMER):
                    self.overall_location[0] = self.map_location[0] + (self.screen_location[0] / screen_scale[0]) / TILE_SIZE
                    self.overall_location[1] = self.map_location[1] + (self.screen_location[1] / screen_scale[1]) / TILE_SIZE
                    if(round(abs(math.cos(math.radians(direction) + math.pi/2)), 3) == 1.0): #we should center ourselves horizontally (sometimes at low FPS we don't touch the block we're driving into due to unmove. This fixes that)
                        self.overall_location[0] = float(round(self.overall_location[0], 0))
                    elif(round(abs(math.sin(math.radians(direction) + math.pi/2)), 3) == 1.0): #we should center ourselves vertically (sometimes at low FPS we don't touch the block we're driving into due to unmove. This fixes that)
                        self.overall_location[1] = float(round(self.overall_location[1], 0))
                    self.goto(self.overall_location, TILE_SIZE, screen_scale) #this HAS to be run to sync overall_location[] and map_location[] after the above 4 lines of code
                # - Handle perpendicular centering -
                if(abs(self.overall_location[1] - round(self.overall_location[1],0)) < self.POS_CORRECTION_MAX_THRESHOLD): #positioning precision must be within 0.2 blocks for this correction to take effect
                    if(abs(self.overall_location[1] - round(self.overall_location[1],0)) > self.POS_CORRECTION_MIN_THRESHOLD): #we don't have to be PERFECTLY precise tho...
                        if(self.last_motion[0] != 0): #movement was in the X axis, so we need to center ourselves on the Y axis
                            self.last_unmove_motion[2] = False #clear our unmove flag for wall collision
                            if(self.overall_location[1] - round(self.overall_location[1],0) > 0):
                                #decrease our Y position to get to the closest integer Y value
                                self.map_location[1] -= align_speed * self.time_difference
                            else:
                                #increase our Y position to get to the closest integer Y value
                                self.map_location[1] += align_speed * self.time_difference
                if(abs(self.overall_location[0] - round(self.overall_location[0],0)) < self.POS_CORRECTION_MAX_THRESHOLD): #we're centering ourselves by moving in the X axis
                    if(abs(self.overall_location[0] - round(self.overall_location[0],0)) > self.POS_CORRECTION_MIN_THRESHOLD):
                        # - Now we try and ensure that we slowly center ourselves on the square we are *mostly* on, so that we can make the corner anyways...even if we hit a wall -
                        if(self.last_motion[1] != 0): #movement is in the Y axis, so we need to center ourselves on the X axis
                            self.last_unmove_motion[2] = False #clear our unmove flag for wall collision
                            if(self.overall_location[0] - round(self.overall_location[0],0) > 0):
                                #decrease X pos to get to nearest integer X pos
                                self.map_location[0] -= align_speed * self.time_difference
                            else:
                                #increase X pos to get to nearest integer X pos
                                self.map_location[0] += align_speed * self.time_difference
        else: #we're gonna have to spend 0.5/self.speed seconds to rotate our tank 90 degrees...
            #only set goal_rotation if it hasn't been set yet...or if we need a new one.
            if(self.goal_rotation == 0 or self.no_360_or_negative(self.old_direction + self.goal_rotation) != self.no_360_or_negative(direction)):
                #how far do we have to rotate? Rotating left/right may create a rotation difference...
                possible_goal_rotation = self.no_360(direction - self.direction)
                other_goal_rotation = self.offset_360(possible_goal_rotation)
                if(abs(possible_goal_rotation) < abs(other_goal_rotation)):
                    self.goal_rotation = possible_goal_rotation
                else:
                    self.goal_rotation = other_goal_rotation
                self.old_direction = self.direction #bookmark our current rotation direction
            old_self_direction = self.direction #this old self.direction state is needed to calculate when we've reached the endpoint of our rotation.
            # - Start rotating (90 degrees is considered "1" rotation, so if you try a 180 turn, it will take twice as long)
            #   - The goal_rotation/abs(goal_rotation) term is in there to get the SIGN from goal_rotation so that we turn the right way...
            if(self.goal_rotation != 0): #Calling move() more than once per frame (e.g. two simultaneous keypresses) causes some issues...like sometimes goal_rotation can be 0...ZeroDivisionError HERE WE GO!!!
                self.direction += 90.0 * self.goal_rotation/abs(self.goal_rotation) * self.time_difference * self.speed * 2
            # - Check if we are within a certain threshold of our desired rotation value...
            #   ...If we are, we just set self.direction to that value
            if(self.goal_rotation > 0): #we're spinning to the left
                if(self.old_direction + self.goal_rotation < self.direction and self.old_direction + self.goal_rotation > old_self_direction): #we're always adding (goal_rotation > 0) so we don't need any special no_360 functions...
                    self.direction = direction
                    self.goal_rotation = 0
                    self.old_direction = direction
            else: #we're spinning to the right
                if(self.no_360_or_negative(self.old_direction + self.goal_rotation) > self.direction and self.no_360_or_negative(self.old_direction + self.goal_rotation) < old_self_direction):
                    self.direction = direction
                    self.goal_rotation = 0
                    self.old_direction = direction
                # - This statement is SPECIFICALLY for the 0 case...where 1 > 0 > 359...so I essentially check that the 1 (self.direction) is greater than the 0 (old_direction + goal_rotation) and that the 0 is greater than...
                #   ...the 359 (old_self_direction). Then I also check that our destination is close enough to 0 that we have a high chance we WON'T get there using the normal IF statment above for finishing a rotation.
                elif(self.no_360_or_negative(self.old_direction + self.goal_rotation) < self.direction and self.no_360_or_negative(self.old_direction + self.goal_rotation) > old_self_direction and abs(self.no_360(self.old_direction + self.goal_rotation)) <= 90.0 * 0.575 * self.time_difference * self.speed * 2):
                    self.direction = direction
                    self.goal_rotation = 0
                    self.old_direction = direction
        # - Update our tread animations here -
        if(time.time() - self.shuffle_timer > self.SHUFFLE_SPEED / self.speed): #time to update?
            self.shuffle_timer = time.time()
            if(self.image_ct >= len(self.spotted_images) - 1):
                self.image_ct = 0
            else:
                self.image_ct += 1

    def unmove(self): #reverts the last movement made by move().
        self.shuffle_timer = time.time() #because we weren't able to move, we shouldn't animate the treads.
        if(self.time_difference != 0):
            align_speed = self.speed * (1 / self.time_difference / 90) #if we aren't hitting 90+ FPS (chosen arbitrarily), we're NOT re-aligning ourselves at our normal speed. We'll clip into a wall!
        else:
            align_speed = self.speed
        if(self.last_unmove_motion[2] == False):
            self.map_location[1] -= self.last_motion[1]
            self.map_location[0] -= self.last_motion[0]
            self.last_unmove_motion[0] = -self.last_motion[0]
            self.last_unmove_motion[1] = -self.last_motion[1]
            self.last_unmove_motion[2] = True #now we may not move in self.last_unmove_motion until we try moving a different direction first.
            self.unmove_timer = time.time() #this helps us with timing WHEN we should activate different kinds of centering to make tanks move as smoothly as possible through the arena
        else: #we need to compensate for the fact that we may have pushed ourselves back into another wall...
            self.map_location[0] -= self.last_unmove_motion[0] * (1 / self.time_difference / 90)
            self.map_location[1] -= self.last_unmove_motion[1] * (1 / self.time_difference / 90)
        # - Check if we just *barely* didn't make it around a corner, and let the player make the corner if so -
        if(abs(self.overall_location[1] - round(self.overall_location[1],0)) < self.POS_CORRECTION_MAX_THRESHOLD): #positioning precision must be within 0.2 blocks for this correction to take effect
            if(abs(self.overall_location[0] - round(self.overall_location[0],0)) < self.POS_CORRECTION_MAX_THRESHOLD):
                if(abs(self.overall_location[1] - round(self.overall_location[1],0)) > self.POS_CORRECTION_MIN_THRESHOLD): #we don't have to be PERFECTLY precise tho...
                    if(abs(self.overall_location[0] - round(self.overall_location[0],0)) > self.POS_CORRECTION_MIN_THRESHOLD):
                        # - Now we try and ensure that we slowly center ourselves on the square we are *mostly* on, so that we can make the corner anyways...even if we hit a wall -
                        if(self.last_motion[1] != 0): #movement is in the Y axis, so we need to center ourselves on the X axis
                            if(self.overall_location[0] - round(self.overall_location[0],0) > 0):
                                #decrease X pos to get to nearest integer X pos
                                self.map_location[0] -= align_speed * self.time_difference
                            else:
                                #increase X pos to get to nearest integer X pos
                                self.map_location[0] += align_speed * self.time_difference
                        else: #movement was in the X axis, so we need to center ourselves on the Y axis
                            if(self.overall_location[1] - round(self.overall_location[1],0) > 0):
                                #decrease our Y position to get to the closest integer Y value
                                self.map_location[1] -= align_speed * self.time_difference
                            else:
                                #increase our Y position to get to the closest integer Y value
                                self.map_location[1] += align_speed * self.time_difference

    # - Makes sure player movement is not restricted due to the "unmove" flag being set -
    def clear_unmove_flag(self):
        self.last_unmove_motion[2] = False

    def draw(self, screen, screen_scale, TILE_SIZE, third_person_coords=None, client_only=True): #draw a tank onscreen
        # - Calculate the tank's onscreen coordinates -
        screen_coordinates = [self.map_location[0] * screen_scale[0] * TILE_SIZE + self.screen_location[0], self.map_location[1] * screen_scale[1] * TILE_SIZE + self.screen_location[1]]
        if(third_person_coords == None):
            screen_coordinates[0] -= self.map_location[0] * screen_scale[0] * TILE_SIZE #offset the coordinates because of our arena offset.
            screen_coordinates[1] -= self.map_location[1] * screen_scale[1] * TILE_SIZE
        else: #we're not the controller of this tank?
            screen_coordinates[0] -= third_person_coords[0] * screen_scale[0] * TILE_SIZE
            screen_coordinates[1] -= third_person_coords[1] * screen_scale[1] * TILE_SIZE
        # - Find whether we want the spotted or unspotted image; If we are a COMPLETELY client-run engine, we may not want the unspotted image at all. -
        if(not client_only and time.time() - self.client_spotted > self.MAX_SPOTTED and self.destroyed == False): #we haven't received updates on this tank object for a while? We should use the unspotted image (if we're not dead).
            image_choice = self.unspotted_image
        else: #use spotted image (if we're dead, or spotted recently, or in client mode)
            image_choice = self.spotted_images[self.image_ct]
        # - Rotate the tank image, scale it, and paste it onscreen -
        if(screen_coordinates[0] > -TILE_SIZE * screen_scale[0] and screen_coordinates[0] < screen.get_width()): #only draw if it's actually going to be onscreen
            if(screen_coordinates[1] > -TILE_SIZE * screen_scale[1] and screen_coordinates[1] < screen.get_height()):
                rotated_image = pygame.transform.rotate(image_choice, self.direction) #optional: switch self.direction to old_direction
                scaled_image = pygame.transform.scale(rotated_image, [int(TILE_SIZE * screen_scale[0]), int(TILE_SIZE * screen_scale[1])])
                screen.blit(scaled_image, [int(screen_coordinates[0]), int(screen_coordinates[1])])

    #draws a red pixel on the minimap at the location of an enemy who isn't dead, and a green pixel on the minimap at the location of an ally who is alive.
    def draw_minimap(self, minimap_surf, home_team, client_only=True):
        if(self.destroyed == False): #there's no point in putting a dead tank on the minimap...
            # - Find whether we want the spotted or unspotted color; If we are a COMPLETELY client-run engine, we may not want the unspotted color at all. -
            if(not client_only and time.time() - self.client_spotted > self.MAX_SPOTTED): #we haven't received updates on this tank object for a while? We should use the unspotted image.
                color_choice = [
                    [127,0,0],
                    [0,127,0]
                    ]
            else: #use spotted color
                color_choice = [
                    [255,0,0],
                    [0,255,0]
                    ]
            if(home_team != self.team): #this tank is NOT on our team
                minimap_surf.set_at([int(round(self.overall_location[0],0)),int(round(self.overall_location[1],0))],color_choice[0])
            else: #it must be then...
                minimap_surf.set_at([int(round(self.overall_location[0],0)),int(round(self.overall_location[1],0))],color_choice[1])

    def return_collision(self, TILE_SIZE, collision_offset): #returns the tank's collision coordinates in tile coordinates
        # - Calculate the tank's onscreen coordinates -
        screen_coordinates = self.overall_location[:]
        screen_coordinates.append(0)
        screen_coordinates.append(0)
        # - Add the x2 and y2 coordinates -
        screen_coordinates[2] = screen_coordinates[0] + 1
        screen_coordinates[3] = screen_coordinates[1] + 1
        # - Take into account our collision offset -
        screen_coordinates[0] += (collision_offset / TILE_SIZE) / 2
        screen_coordinates[1] += (collision_offset / TILE_SIZE) / 2
        screen_coordinates[2] -= (collision_offset / TILE_SIZE) / 2
        screen_coordinates[3] -= (collision_offset / TILE_SIZE) / 2
        # - Return our collision box -
        return screen_coordinates

    def shoot(self, TILE_SIZE, server=None): #this spawns a bullet directly in front of the tank, and continues the bullet in the direction the tank is facing.
        if(server == None or server == True): #we're either not using this as a server, or we are the server (have permission to shoot bullets)?
            if(server == True and self.shot_pending == True or server == None): #shoot!
                self.shot_pending = False #clear the shot_pending flag
                if((time.time() - self.last_shot) > (60.0 / self.RPM)): #has our loading mechanism finished loading a shell into the gun?
                    if(self.shells[self.current_shell] > 0 and self.destroyed == False): #do we still have shells left? And, are we destroyed? No, if we want to shoot.
                        self.shells[self.current_shell] -= 1 #we shot a shell, so we should have one less in our tank, right?
                        self.shells_used[self.current_shell] += 1 #we shot a shell, so we should bump our shot shells counter by one.
                        self.last_shot = time.time() #we shot a shell, so now we need to wait before we can shoot another one...
                        #Create a bullet object!
                        new_bullet = Bullet(self.shell_images[self.current_shell], self.team, self.current_shell, self.old_direction, [self.damage_multiplier, self.penetration_multiplier, self.fire_inflict],self)
                        #Find out EXACTLY where we are in the map.
                        map_position = self.overall_location[:]
                        #Increment map_position by 0.75 in whichever direction we are facing.
                        if(self.old_direction == 0): #up?
                            map_position[1] -= 0.75
                        elif(self.old_direction == 90): #left?
                            map_position[0] -= 0.75
                        elif(self.old_direction == 180): #down?
                            map_position[1] += 0.75
                        elif(self.old_direction == 270): #right?
                            map_position[0] += 0.75
                        # - Set the bullet's position to our calculated coordinates -
                        new_bullet.map_location = map_position
                        # - Make sure that this player gets spotted temporarily for shooting -
                        for x in range(0,len(self.spotted)):
                            self.spotted[x] = time.time() + 0.75 #spotted for 0.75 seconds
                        # - Return "new_bullet" -
                        return new_bullet
        elif(server == False): #we're a client, so we need to set self.shot_pending to True.
            self.shot_pending = True
        return None #you can't shoot yet...

    def message(self, message, particles, server=True): #lets a player send a message to EVERYONE by spawning a word particle
        if(server): #this is what happens server-side
            if(self.message_request != None and time.time() - self.last_message > self.MESSAGE_COOLDOWN): #we got a message from the client and the client is allowed to speak?
                self.last_message = time.time() #reset the time counter for message cooldown
                if(self.message_request in self.MESSAGE_WHITELIST): #we only make the message public IF it passes our censoring!!
                    message_particle = GFX.Particle([self.overall_location[0] - (len(self.message_request) * 0.25),self.overall_location[1]], [self.overall_location[0] + random.randint(-2,2), self.overall_location[1] + random.randint(-2,2)], 0.65, 0.15, [random.randint(150,255),random.randint(150,255),random.randint(150,255)], [50,50,50], time.time(), time.time() + 5.0, self.message_request)
                    particles.append(message_particle) #add the new message particle to our particles list
                    # - Now this player gets spotted for speaking -
                    for x in range(0,len(self.spotted)):
                        self.spotted[x] = time.time() + 0.75
                self.message_request = None #clear the message_request flag
        else: #this is what happens client-side
            self.message_request = message #set the message_request flag

    def return_data(self, precision=2, clear_flags=True): #returns tank data to be sent over netcode
        if(self.destroyed): #Convert True/False flags to 1/0s to save netcode transmissions
            destroyed = 1
        else:
            destroyed = 0
        if(self.explosion_done):
            explosion_done = 1
        else:
            explosion_done = 0
        if(self.shot_pending):
            shot_pending = 1
        else:
            shot_pending = 0
        #Compressing the powerups list takes a bit more work since it holds values which can be a Boolean, a Float, or a String.
        powerups = [] #No modification is needed on the client-side to convert the values sent through netcode to Tank() class compatible data.
        for x in range(0,len(self.powerups)):
            if(str(type(self.powerups[x])) == "<class 'float'>"):
                powerups.append(float(round(self.powerups[x],precision)))
            elif(str(type(self.powerups[x])) == "<class 'str'>"):
                powerups.append(str(float(round(eval(self.powerups[x]),precision))))
            else:
                powerups.append(self.powerups[x])
        return_list = [
            self.type,                                                                              #"<class 'str'>"
            float(round(self.speed,precision)),                                                     #"<class 'float'>"
            float(round(self.direction,precision)),                                                 #"<class 'float'>"
            float(round(self.HP,precision)),                                                        #"<class 'float'>" ---
            float(round(self.armor,precision)),                                                     #"<class 'float'>"
            self.team,                                                                              #"<class 'str'>"
            self.name,                                                                              #"<class 'str'>"
            destroyed,                                                                              #"<class 'int'>" ---
            explosion_done,                                                                         #"<class 'int'>"
            float(round(self.start_HP,precision)),                                                  #"<class 'float'>"
            float(round(self.start_armor,precision)),                                               #"<class 'float'>"
            float(round(self.fire,precision)),                                                      #"<class 'float'>" ---
            [float(round(self.overall_location[0],precision)),float(round(self.overall_location[1],precision))],  #["<class 'float'>", "<class 'float'>"]
            float(round(self.goal_rotation,precision)),                                             #"<class 'float'>"
            float(round(self.old_direction,precision)),                                             #"<class 'float'>"
            float(round(time.time() - self.last_shot,precision)), #seconds ago last shot happened   #"<class 'float'>" ---
            shot_pending, #does the CLIENT want to shoot? (sorry servers, you can't do that)        #"<class 'int'>"
            self.current_shell, #which shell does the client want to shoot?                         #"<class 'int'>"
            float(round(self.total_damage,precision)),                                              #"<class 'float'>"
            self.kills,                                                                             #"<class 'int'>" ---
            self.powerup_request,                                                                   #"<class 'int'>" / "<class 'NoneType'>"
            self.shells,                                                                            #["<class 'int'>", "<class 'int'>", "<class 'int'>", "<class 'int'>"]
            powerups,                                                                               #List of 6 elements: Can be "<class 'bool'>","<class 'NoneType'>","<class 'str'>", or "<class 'float'>"; Has to be verified separately.
            float(round(self.RPM,precision)),                                                       #"<class 'float'>" ---
            self.message_request,                                                                   #"<class 'NoneType'>" / "<class 'str'>"
            self.team_num,                                                                          #"<class 'int'>"
            self.image_ct                                                                           #"<class 'int'>"
            ]
        if(clear_flags):
            self.powerup_request = None #clear the powerup_request flag
            self.shot_pending = False #clear the shot_pending flag after we grab our data; This is just a good place to do it...
            self.message_request = None #clear the message_request flag
        return return_list

    def enter_data(self, data, TILE_SIZE=20, screen_scale=[1,1], server=False): #enters the data from Tank.return_data()
        verified = False
        for x in self.DATA_FMT:
            if(netcode.data_verify(data, x)):
                verified = True
                break
        if(verified):
            for x in data[22]: #check if our powerup list contains valid data
                verified = False
                for scan in range(0,len(self.POWERUP_DATA_FMT)):
                    if(netcode.data_verify(x, self.POWERUP_DATA_FMT[scan])):
                        verified = True
                        break
                if(not verified): #an item failed the verification?
                    break #we'll exit; verified will equal False, so no data will be entered.
        if(verified):
            if(not server):
                self.speed = data[1]
            self.direction = data[2]
            if(not server):
                self.HP = data[3]
                self.armor = data[4]
                self.team = data[5]
                self.name = data[6]
                if(data[7] == 1):
                    self.destroyed = True
                else:
                    self.destroyed = False
                if(data[8] == 1):
                    self.explosion_done = True
                else:
                    self.explosion_done = False
                self.start_HP = data[9]
                self.start_armor = data[10]
                self.fire = data[11]
            self.overall_location[0] = data[12][0]
            self.overall_location[1] = data[12][1]
            self.goto(data[12], TILE_SIZE, screen_scale) #set our screen/map_location accordingly
            self.goal_rotation = data[13]
            self.old_direction = data[14]
            if(not server):
                self.last_shot = time.time() - data[15]
            if(server): #yes, this only happens if the enter_data is from the server.
                if(data[16] == 1):
                    self.shot_pending = True
                else:
                    self.shot_pending = False
                self.use_shell(data[17]) #make sure that cooldown gets measured properly...
            if(not server):
                self.total_damage = data[18]
                self.kills = data[19]
            if(server):
                self.powerup_request = data[20]
                self.use_powerup(data[20], server)
            if(not server):
                self.shells = data[21]
                self.powerups = data[22]
                self.RPM = data[23]
            if(server):
                self.message_request = data[24]
            if(not server):
                self.team_num = data[25]
            # - If NOT server, then we need to reset self.client_spotted so that the client knows that this tank object HAS been spotted -
            if(not server):
                self.client_spotted = time.time()
            self.image_ct = data[26] % len(self.spotted_images) #since clients and servers might not have the same number of tank movement frames, this will prevent IndexErrors from occurring.
        else:
            print("[ENTITY] Tank failed to enter data! Data: " + str(data))

class Bot(): #AI player which can fill a player queue if there is not enough players.
    def __init__(self,team_number=0,player_number=0,player_rating=0.85):
        # - Bot identity constants -
        self.team_number = team_number #basically, this is a numerical way of keeping track of teams (useful in analyse_game() )
        self.player_number = player_number #numerical index of this bot player within the server's list of tank entities.
        self.rating = player_rating #controls how hard the bot plays (higher number = harder bot)

        # - AI variables -
        self.destination = None #where the bot is trying to get to (usually an enemy's base, or a flanking position, etc.)
        self.tactic = None #how should this bot organize its positional strategy?
        #which direction to move? The bot needs something concrete to follow along to, rather than constantly changing its mind about where to turn.
        self.direction = random.randint(0,3) * 90 #this only gets set when the bot is moving towards its destination.
        self.last_directions = [self.direction, self.direction + 90 * [1, -1][random.randint(0,1)]] #We always try to move in one of these directions, or continue moving in self.direction. ALWAYS. (unless no wall)
        self.current_position = [0,0]
        self.destination_time = None #how long has this bot been trying to reach its destination?
        self.goal_base = None #what base is the bot trying to attack?
        self.available_directions = [] #this bookmark is useful for allowing the bot to change directions at times when it would typically continue in its current direction.
        self.last_compute_frame = time.time()
        self.player_aggro = None #these variables change based on whether the bot is trying to attack something
        self.bullet_aggro = None
        self.tactic_num = 0 #this bookmarks which tactic the bot is currently trying...Step 1 = Attack from left/right/center, Step 2 = Move to enemy base, Step 3 = Move to center, Step 4 = wander with teammates?

        #- This threshold is to help calculate pathfinding routines. It has nothing to do with actual pathfinding,
        #   - but it helps with pathfinding destination calculations -
        self.PATHFIND_OVERSHOOT = 0.05
        self.DESTINATION_TIME_LIMIT = 45.0 #seconds
        #this is a threshold (in blocks) which allows bots to be within (pathfind_error) blocks of their destination for it to be considered completed.
        self.PATHFIND_ERROR = 1.05
        self.bot_vision = 5 #how far (in blocks) the bot can see
        self.DECISION_PRIORITY = ["bullet","player"] #first index is first priority, second index is second priority of focus, etc.
        self.CENTER_THRESHOLD = 0.15 #how close to the center of a block the bot may be to simply set his position to center.
        self.OPPOSITE_DIRECTIONS = [[90,270],[0,180]]
        self.FORCED_MOVE_TIME = 1.5
        self.LR_ANGLE = 30 #this angle determines how far left/right the bots will venture when attempting a side attack.
        self.AGGRO_DIR_THRESH = 1.00 #when bots are at or beyond this rating, they WILL point towards any entity they are aggroed onto. Otherwise, they may point 180 degrees away sometimes.
        self.DEFAULT_SIGHT_DISTANCE = 10 #how far (in blocks) do bots get to see? Multiply by self.rating to get the sight distance bots get.

        # - Powerup selection constants -
        self.ARMOR_BOOST_THRESHOLD = 20 * math.sqrt(player_rating) #threshold at which the bot still decides that using armor boost is worth it.
        self.POWERUP_AGGRESSION_LIST = [4,2,3] #list of powerups (in order) that a bot uses when its armor starts getting depleted...
        self.HP_DEPENDANT_POWERUPS = [2,3,4] #list of powerups which affect HP
        self.BULLET_DISTANCE_THRESHOLD = 3.0 #maximum number of blocks away a bullet can be to make the AI use powerups to counter the bullet

    # - Checks if we have reached our destination, and chooses a new destination if so -
    def choose_destination(self,players,arena,blocks):
        new_destination = False
        # - Start by checking if we have a destination, then check whether we've reached our destination if we have one -
        if(self.destination != None):
            # - Check if we've reached our destination
            if(players[self.player_number].overall_location[1] > self.destination[1] - self.PATHFIND_ERROR and players[self.player_number].overall_location[1] < self.destination[1] + self.PATHFIND_ERROR):
                if(players[self.player_number].overall_location[0] > self.destination[0] - self.PATHFIND_ERROR and players[self.player_number].overall_location[0] < self.destination[0] + self.PATHFIND_ERROR):
                    new_destination = True
        else:
            new_destination = True
        if(new_destination or time.time() - self.destination_time > self.DESTINATION_TIME_LIMIT): # - We need to choose a new destination! -
            self.destination_time = time.time() #reset self.destination_time
            # - First resort option: Go for a flank/central approach. Do some tactics! -
            #Step 1 = Attack from left/right/center, Step 2 = Move to enemy base, Step 3 = Move to center, Step 4 = wander with teammates?
            if(self.tactic_num == 0):
                self.tactic_num += 1
                # - Are we moving left, right, or center?
                direction = ["left","right","center"][random.randint(0,2)]
                #how we calculate left/right: Get the angle from the bot to the arena center, and change the angle left/right.
                if(direction == "left"):
                    opposite = players[self.player_number].overall_location[0] - len(arena.arena[0]) / 2
                    Y_dimension = players[self.player_number].overall_location[1] - len(arena.arena) / 2
                    hypotenuse = math.sqrt(opposite * opposite + Y_dimension * Y_dimension)
                    if(hypotenuse != 0):
                        new_direction = math.degrees(math.asin(opposite/hypotenuse))
                    else:
                        new_direction = 45 * random.randint(0,7) #we're EXACTLY @ center, so...just pick a random direction, I guess...
                    if(opposite > 0):
                        if(Y_dimension > 0): #Quadrant I
                            pass
                        else: #Quadrant IV
                            new_direction = 360 - new_direction
                    else:
                        if(Y_dimension > 0): #Quadrant II
                            new_direction = 180 - new_direction
                        else: #Quadrant III
                            new_direction = 180 + new_direction
                    new_direction -= self.LR_ANGLE #direction + 30 degrees left
                    self.destination = [
                        math.cos(math.radians(new_direction)) * hypotenuse,
                        math.sin(math.radians(new_direction)) * hypotenuse,
                        ]
                elif(direction == "right"):
                    opposite = players[self.player_number].overall_location[0] - len(arena.arena[0]) / 2
                    Y_dimension = players[self.player_number].overall_location[1] - len(arena.arena) / 2
                    hypotenuse = math.sqrt(opposite * opposite + Y_dimension * Y_dimension)
                    if(hypotenuse != 0):
                        new_direction = math.degrees(math.asin(opposite/hypotenuse))
                    else:
                        new_direction = 45 * random.randint(0,7) #we're EXACTLY @ center, so...just pick a random direction, I guess...
                    if(opposite > 0):
                        if(Y_dimension > 0): #Quadrant I
                            pass
                        else: #Quadrant IV
                            new_direction = 360 - new_direction
                    else:
                        if(Y_dimension > 0): #Quadrant II
                            new_direction = 180 - new_direction
                        else: #Quadrant III
                            new_direction = 180 + new_direction
                    new_direction += self.LR_ANGLE #direction + 30 degrees right
                    self.destination = [
                        math.cos(math.radians(new_direction)) * hypotenuse,
                        math.sin(math.radians(new_direction)) * hypotenuse,
                        ]
                elif(direction == "center"): #...this one's easy.
                    self.destination = [int(len(arena.arena[0]) / 2), int(len(arena.arena) / 2)]
            elif(self.tactic_num == 1): #now we head to an enemy base.
                self.tactic_num += 1
                base_num = random.randint(0,len(arena.flag_locations)) #pick a random flag to attack
                if(base_num == self.team_number): #make sure we don't attack our own base...lol
                    if(base_num + 1 < len(arena.flag_locations)):
                        base_num += 1
                    else:
                        base_num -= 1
            elif(self.tactic_num == 2): #now we head to the center.
                self.tactic_num += 1
                self.destination = [int(len(arena.arena[0]) / 2), int(len(arena.arena) / 2)]
            elif(self.tactic_num >= 3 and self.tactic_num % 16 <= 7): #Follow teammates
                self.tactic_num += 1
                new_destination = [0,0]
                new_destination_ct = 0 #get the avg. location of all players on our team which are alive
                for x in range(0,len(players)):
                    if(players[x].destroyed != True and players[x].team == players[self.player_number].team and x != self.player_number):
                        new_destination[0] += players[x].overall_location[0]
                        new_destination[1] += players[x].overall_location[1]
                        new_destination_ct += 1
                if(new_destination_ct == 0):
                    #RANDOM LOCATIONS because no players to follow =( (we shrink the amount of positions available because there is a wall on the edge of the map)
                    new_destination = [1 + random.randint(0,len(arena.arena[0]) - 1 - 2), 1 + random.randint(0,len(arena.arena[1]) - 1 - 2)]
                else: #follow the leader...
                    new_destination[0] /= new_destination_ct
                    new_destination[1] /= new_destination_ct
                self.destination = new_destination
            else: #go to a random location!
                self.tactic_num += 1
                new_destination = [1 + random.randint(0,len(arena.arena[0]) - 1 - 2), 1 + random.randint(0,len(arena.arena[1]) - 1 - 2)]
                self.destination = new_destination
            # - Now, we have to check if our destination is ontop of a block. If it is, we have to shift our destination until it isn't -
            is_on_block = False
            self.destination[0] = int(round(self.destination[0],0)) #we have to truncate the floating part of our destination variable to use it as an arena index.
            self.destination[1] = int(round(self.destination[1],0))
            if(self.destination[1] > len(arena.arena) - 1 or self.destination[1] < 0 or self.destination[0] > len(arena.arena[0]) - 1 or self.destination[0] < 0 or arena.arena[self.destination[1]][self.destination[0]] in blocks): #if this is true, our destination is ontop of a block (unreachable)
                is_on_block = True
            if(is_on_block): #now we have to shift self.destination around until we get a tile where it isn't on a block...
                directions = [
                    [1,0],
                    [0,1],
                    [-1,0],
                    [0,-1]
                    ]
                position = self.destination[:]
                size = 0 #how wide the circle is that we are using to check for a new destination point
                while is_on_block == True:
                    size += 2
                    for z in range(0,4):
                        for length in range(0,size): #size is radius...so we need to double that for diameter
                            # - Update the new potential self.destination point -
                            position[0] += directions[z][0]
                            position[1] += directions[z][1]
                            # - Check if the new self.destination point is NOT ontop of any blocks -
                            is_on_block = False #reset is_on_block
                            if(position[1] > len(arena.arena) - 1 or position[1] < 0 or position[0] > len(arena.arena[0]) - 1 or position[0] < 0 or arena.arena[position[1]][position[0]] in blocks):
                                is_on_block = True
                            elif(not is_on_block): #we found a valid destination???
                                break
                        if(not is_on_block):
                            break
                    position[0] -= 1
                    position[1] -= 1
                    if(not is_on_block):
                        break
                self.destination[0] = position[0] #actually ASSIGN the new destination I found to our destination variable (I forgot to do this for over a year of using this code LOL)
                self.destination[1] = position[1]

    def start_pos(self,players,arena,screen_scale): #ez way to get the bot to start on the flag's site.
        players[self.player_number].goto(arena.flag_locations[self.team_number][:], arena.TILE_SIZE, screen_scale)

    def self_center(self,players,TILE_SIZE,screen_scale): #center the bot player over 1 arena tile
        if(abs(players[self.player_number].overall_location[0] - round(players[self.player_number].overall_location[0],0)) > self.CENTER_THRESHOLD):
            centered = False
            #we're not centered on the X axis!
            off_center = players[self.player_number].overall_location[0] - round(players[self.player_number].overall_location[0],0)
            if(off_center > 0): #we're too far right!
                direction = 90 #left
            else:
                direction = 270 #right
            players[self.player_number].move(direction, TILE_SIZE, screen_scale)
        elif(abs(players[self.player_number].overall_location[1] - round(players[self.player_number].overall_location[1],0)) > self.CENTER_THRESHOLD):
            centered = False
            #we're not centered on the Y axis!
            off_center = players[self.player_number].overall_location[1] - round(players[self.player_number].overall_location[1],0)
            if(off_center > 0): #we need to move up
                direction = 0 #up
            else:
                direction = 180 #down
            players[self.player_number].move(direction, TILE_SIZE, screen_scale)
        else: #we're CLOSE ENOUGH to centered. Let's teleport the rest of the way there...
            centered = True
            players[self.player_number].goto([round(players[self.player_number].overall_location[0],0), round(players[self.player_number].overall_location[1],0)],TILE_SIZE,screen_scale)
        return centered

    #takes values in degrees; Changes them so that they are not negative, or larger than 359.9(bar).
    def no_360_or_negative(self,direction):
        #we MAY NOT have a negative direction value, or one over 360.
        while (direction >= 360 or direction < 0):
            if(direction >= 360): #decrement self.direction by 360 then
                direction -= 360
            elif(direction < 0): #self.direction is less than 0?
                direction += 360
        return direction

    def find_directions(self,players,arena,collideable_tiles,TILE_SIZE,offset=1): #finds which direction the bot can move in.
        #We can go any direction where there is not a block in our way.
        total_directions = [0, 180, 90, 270]
        available_directions = [0, 90, 180, 270]
        # - We'll assume the bot is directly ontop of a square. This way we can just check the ones adjacent and find out which ones are open -
        rounded_direction = [
            int(round(players[self.player_number].overall_location[0],0)),
            int(round(players[self.player_number].overall_location[1],0))
            ]
        newpos = [0,0]
        # - To check each direction, we'll use the expression: sin(math.radians(available_directions[x]) + math.pi/2) -
        for x in range(0,len(total_directions)):
            newpos = [0,0]
            newpos[0] = math.cos(math.radians(total_directions[x]) + math.pi/2) + rounded_direction[0]
            newpos[1] = -math.sin(math.radians(total_directions[x]) + math.pi/2) + rounded_direction[1]
            newpos[0] = int(round(newpos[0],0)) #rounding MUST come first; otherwise a 3.99999 will turn into 3...and then the wrong arena tile will be checked =(
            newpos[1] = int(round(newpos[1],0))
            if(newpos[0] < 0 or newpos[1] < 0 or newpos[0] > len(arena.arena[0]) - 1 or newpos[1] > len(arena.arena) - 1):
                available_directions.remove(total_directions[x])
            elif(arena.arena[newpos[1]][newpos[0]] in collideable_tiles):
                available_directions.remove(total_directions[x])
        return available_directions

    def entity_alligned(self,players,entity,TILE_SIZE): #tries to get within direct line of sight vertically or horizontally with an enemy.
        if(entity.type == "Tank"):
            entitypos = entity.overall_location[:]
        elif(entity.type == "Bullet"):
            entitypos = entity.map_location[:]
        position_difference = [ #calculate the positional difference between the bot and the entity
                               entitypos[0] - players[self.player_number].overall_location[0],
                               entitypos[1] - players[self.player_number].overall_location[1]
                               ]
        # - Check if we are within 0.75 blocks of the enemy on either the X or Y axis -
        if(position_difference[0] < 0.75 or position_difference[1] < 0.75): #we're alligned...Now we need to be pointing in the right direction.
            if(abs(position_difference[1]) > abs(position_difference[0])): #we need to make sure we're pointing the direction of the larger number.
                if(position_difference[1] > 0): #down
                    if(players[self.player_number].direction == 180): #180 is down in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
                else: #up
                    if(players[self.player_number].direction == 0): #0 is up in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
            else:
                if(position_difference[0] > 0): #right
                    if(players[self.player_number].direction == 270): #270 is right in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
                else: #left
                    if(players[self.player_number].direction == 90): #90 is left in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
            return True
        else:
            return False

    #points the bot's tank in the specified direction + moves in that direction if auto_move == True
    def point_in_direction(self,direction,players,TILE_SIZE,screen_scale,auto_move=False):
        if(players[self.player_number].old_direction != direction): #we're NOT already pointing in the right direction?
            #are we 90 degrees off? If so, we can just move towards the right direction.
            if(players[self.player_number].old_direction == self.no_360_or_negative(direction + 90) or players[self.player_number].old_direction == self.no_360_or_negative(direction - 90)):
                players[self.player_number].move(direction,TILE_SIZE,screen_scale)
            else: #we're 180 degrees - aka, backwards. We need to rotate 90 degrees before we can point in the right direction to avoid reversing.
                players[self.player_number].move(self.no_360_or_negative(direction + 90),TILE_SIZE,screen_scale)
            return False
        else: #let our bot program know we're pointing in the right direction!
            if(auto_move):
                players[self.player_number].move(direction,TILE_SIZE,screen_scale)
            return True

    #checks for entities within the bot's line of sight. Returns either the first one seen, or None.
    def check_visible_entities(self,players,entities,arena,collideable_tiles,TILE_SIZE):
        seen = None
        for x in range(0,len(entities)):
            if(entities[x].team == players[self.player_number].team): #entities on our own team don't count!
                continue
            elif(entities[x].destroyed == True): #we don't check for destroyed entities.
                continue
            elif(seen == None):
                seen = check_visible(arena, [players[self.player_number], entities[x]], collideable_tiles, int(math.ceil(self.DEFAULT_SIGHT_DISTANCE * self.rating)), proximity=False)
                if(seen == True): #if we spotted this player, we need to set seen to its index in the entities[] list
                    seen = x
                    break
                else:
                    seen = None
        return seen

    #Teleports the bot this Bot() object controls to the nearest integer coordinate/tile. This helps pathfinding work better since it doesn't need to deal with players with decimal tile coordinates.
    def tp_center(self, players):
        players[self.player_number].overall_location[0] = int(round(players[self.player_number].overall_location[0],0))
        players[self.player_number].overall_location[1] = int(round(players[self.player_number].overall_location[1],0))

    #Tries to move in one of a few given directions. Input a list of preferred directions, starting with highest priority.
    def directional_move(self,players,available_directions,preferred_directions,TILE_SIZE,screen_scale,arena,collideable_tiles,screen=None):
        # - Needed debug info -
        #screen_scale = arena.get_scale([15,15],screen)
        #player_offset = players[0].map_location[:]
        # - Set our bot's location to an integer value -
        self.tp_center(players)
        # - A few of these checks have to pass the self.last_turn_location check: Basically, has the bot already made a turn on this square last? -
        rounded_position = [round(players[self.player_number].overall_location[0],0),round(players[self.player_number].overall_location[1],0)]
        wall = False #do we have a wall between us and our destination??
        # - Negative 1st: Find whether there is a SINGLE wall between us and our destination -
        position_difference = [self.destination[0] - rounded_position[0], self.destination[1] - rounded_position[1]]
        if(position_difference[0] == 0): #catch any 0div errors, when X difference = 0 (vertical)
            progression = position_difference[1] #move position_difference[1] without moving right/left
            trace = rounded_position[1]
            for x in range(0,int(abs(progression))):
                # - Now we check if we hit a block (we only have to check THE block because this script rounds) -
                # - This is debug -
                #pygame.draw.rect(screen,[255,255,255],[(rounded_position[0] - player_offset[0]) * TILE_SIZE * screen_scale[0],(trace - player_offset[1]) * TILE_SIZE * screen_scale[1],TILE_SIZE * screen_scale[0],TILE_SIZE * screen_scale[1]],5)
                if(trace < 0 or rounded_position[0] < 0 or rounded_position[0] > len(arena.arena[0]) - 1 or trace > len(arena.arena) - 1 or arena.arena[int(trace)][int(rounded_position[0])] in collideable_tiles): #wall?
                    wall = True
                    break #we found a wall; that's all that matters
                if(progression > 0):
                    trace += 1
                else:
                    trace -= 1
        else:
            progression = position_difference[1] / abs(position_difference[0])
            if(position_difference[0] > 0):
                direction = 1
            else:
                direction = -1
            #Now we trace our position to our destination, and see whether we encounter ANY blocks along the way -
            x_trace = rounded_position[0]
            y_trace = rounded_position[1]
            for x in range(0,abs(int(position_difference[0])) + 1): #trace a direct line from us to our destination
                for y in range(0,int(progression) + 1):
                    # - This is debug -
                    #pygame.draw.rect(screen,[255,255,255],[(x_trace - player_offset[0]) * TILE_SIZE * screen_scale[0],(y_trace - player_offset[1]) * TILE_SIZE * screen_scale[1],TILE_SIZE * screen_scale[0],TILE_SIZE * screen_scale[1]],5)
                    if(x_trace < 0 or y_trace < 0 or x_trace > len(arena.arena[0]) - 1 or y_trace > len(arena.arena) - 1 or arena.arena[int(y_trace)][int(x_trace)] in collideable_tiles): #wall?
                        wall = True
                        break #we found a wall; that's all that matters
                    if(progression > 0):
                        y_trace += 1
                    else:
                        y_trace -= 1
                y_trace = round(progression * x + rounded_position[1],0)
                x_trace += direction
                if(wall): #finishing this computation would just waste CPU time since we've already found the boolean flag we're looking for
                    break
        # - Setup -
        successful_move = False
        player_direction = self.direction
        #data sanity check: we need self.last_directions[0:2] to NOT have opposite directions in them. Otherwise, bots will just run back and forth without ever navigating anywhere useful...
        if(self.last_directions[0] == self.no_360_or_negative(self.last_directions[1] + 180)):
            #print("Sanity Check Triggered") #debug
            index_change = random.randint(0,1)
            #we need to modify index index_change so that it isn't the opposite of index (index_change + 1) % 2
            self.last_directions[index_change] += [90, -90][random.randint(0,1)]
            self.last_directions[index_change] = self.no_360_or_negative(self.last_directions[index_change])
        # - First: Check if we can just keep moving in the direction we are currently moving in -
        if(successful_move == False and player_direction in available_directions and (player_direction in preferred_directions or (wall and player_direction in self.last_directions))):
            successful_move = True
            #print("Streight ahead") #debug
        # - Second: Check if we can move in either of our self.last_directions IF wall -
        if(successful_move == False and wall):
            for x in range(0,len(available_directions)):
                if((available_directions[x] == self.last_directions[0] and self.no_360_or_negative(180 + available_directions[x]) != self.direction) or (available_directions[x] == self.last_directions[1] and self.no_360_or_negative(180 + available_directions[x]) != self.direction)):
                    self.last_directions.insert(0,self.direction)
                    self.last_directions.pop(2) #was 1, but should be 2 (this way we cycle through the directions we've traveled last)
                    self.direction = available_directions[x]
                    self.last_turn_location = rounded_position[:]
                    successful_move = True
                    break
        # - Third: If no wall, we need to try move towards our destination -
        if(successful_move == False and not wall):
            for x in range(0,len(available_directions)):
                if(available_directions[x] in preferred_directions and self.no_360_or_negative(180 + available_directions[x]) != self.direction):
                    self.last_directions.insert(0,self.direction)
                    self.last_directions.pop(2)
                    self.direction = available_directions[x]
                    self.last_turn_location = rounded_position[:]
                    successful_move = True
                    break
        # - Fourth: Regardless of wall, we need to try and move in one of our self.last_directions -
        if(successful_move == False):
            for x in range(0,len(available_directions)):
                if(available_directions[x] == self.last_directions[0] and self.no_360_or_negative(180 + available_directions[x]) != self.direction or available_directions[x] == self.last_directions[1] and self.no_360_or_negative(180 + available_directions[x]) != self.direction):
                    self.last_directions.insert(0,self.direction)
                    self.last_directions.pop(2)
                    self.direction = available_directions[x]
                    self.last_turn_location = rounded_position[:]
                    successful_move = True
                    break
        # - Fifth: Just pick a random available direction -
        #if we haven't found a direction by now...well I give up. Usually this occurs when we're cornered.
        if(successful_move == False and len(available_directions) > 0):
            self.last_directions.insert(0,self.direction)
            self.last_directions.pop(2)
            start_num = random.randint(0,len(available_directions) - 1) #this is the direction we will *try* to go in. However, if this is opposite the direction we are currently going, we will do ANYTHING to go another way.
            for getnum in range(0,len(available_directions)):
                if(self.no_360_or_negative(available_directions[start_num] + 180) == self.direction): #this is opposite to the direction we are currently moving? If we can, we're gonna pick another way.
                    if(len(available_directions) > 1): #there is another way?
                        start_num += 1 #pick it!
                        if(start_num > len(available_directions) - 1):
                            start_num = 0
                        pass #we'll take it! Otherwise, this loop will end automatically and start_num will point to the index of the only direction available.
                else: #this direction is fine? We'll take it!
                    #print("Got wanted direction!", end="") #debug (if this is uncommented, uncomment the print statement below containing "RNG" to see how many times bots get the RNG outcomes they want.
                    break
            self.direction = available_directions[start_num]
            if(self.direction != players[self.player_number].old_direction):
                self.last_turn_location = rounded_position[:] #reset our turn location variable
            #print("RNG") #debug for when the bot resorts to an RNG roll
        players[self.player_number].move(self.direction,TILE_SIZE,screen_scale)

    def track_location(self,players,arena,TILE_SIZE,screen_scale,collideable_tiles,tank_collision_offset,screen): #tries to reach self.destination.
        # - Check: Which directions CAN we move in? -
        available_directions = self.find_directions(players,arena,collideable_tiles,TILE_SIZE,tank_collision_offset)
        # - Check: Which directions do we WANT to move in? -
        goal_directions = []
        if(players[self.player_number].overall_location[0] > self.destination[0] + self.PATHFIND_ERROR / 4): #are we to the right of our destination?
            goal_directions.append(90)
        elif(players[self.player_number].overall_location[0] < self.destination[0] - self.PATHFIND_ERROR / 4): #we're to the left.
            goal_directions.append(270)
        if(players[self.player_number].overall_location[1] > self.destination[1] + self.PATHFIND_ERROR / 4): #are we below our destination?
            goal_directions.append(0)
        elif(players[self.player_number].overall_location[1] < self.destination[1] - self.PATHFIND_ERROR / 4): #we're above our destination.
            goal_directions.append(180)
        #print("Goal: " + str(goal_directions) + " Available: " + str(available_directions)) #debug
        self.directional_move(players,available_directions,goal_directions,TILE_SIZE,screen_scale,arena,collideable_tiles,screen)

    def find_shell(self,players): #simple script which decides which shell the AI is going to shoot
        #We need to make sure we are using shells which we can shoot! We shouldn't waste time trying to shoot a shell which we don't own!
        player_HP = (players[self.player_number].HP / players[self.player_number].start_HP) / self.rating
        if(player_HP > 1.0): #due to the division by self.rating, I need to check if player_HP is above 1.0 to make sure the bot functions as expected.
            player_HP = 1.0
        if(player_HP == 0): #since we divide by player_HP a lot, we NEED to make sure this value ISN'T zero.
            player_HP = 0.01 #the bot's already dead...but just to ensure that no zerodiv errors occur, we'll override the value.
        if(int(1 / player_HP) > len(players[self.player_number].shells) - 1): #are we trying to shoot a shell which doesn't exist?
            #fix that!
            player_HP = 1 / len(players[self.player_number].shells) #this line prevents index errors when using arguments such as list[int(1 / player_HP) - 1].
        if(player_HP <= 0): #we can't have a negative HP value for this to work!
            player_HP = 1 / len(players[self.player_number].shells)
        if(players[self.player_number].shells[int(1 / player_HP) - 1] > 0): #we have some of this shell left?
            players[self.player_number].use_shell(int(1 / player_HP) - 1)
        else: #we don't have any of this shell left, AND we have shells left?
            # - Check if we have shells left -
            shells = 0
            for x in players[self.player_number].shells:
                shells += x
            if(x > 0): #we have shells left! It's actually worth checking for which shell to use!
                if(int(1 / player_HP) >= len(players[self.player_number].shells)): #we are trying to use the most powerful shell, but we don't have it?
                    index = int(1 / player_HP) - 1 #we're going to check if we have any less powerful shells, and use our most powerful shell available of the remaining selection.
                    while True:
                        if(players[self.player_number].shells[index] > 0):
                            players[self.player_number].use_shell(index)
                            break
                        else:
                            index -= 1
                            if(index < 0):
                                break #just keep using the shells we are right now
                else: #we need to try use the next most powerful shell.
                    index = int(1 / player_HP) - 1
                    while True:
                        if(players[self.player_number].shells[index] > 0):
                            players[self.player_number].use_shell(index)
                            break
                        else:
                            index += 1
                            if(index > len(players[self.player_number].shells) - 1):
                                index = 0 #We've been looking for more powerful shells; What if there are less powerful ones available?
                                
    def use_powerups(self,players,bullets,player_aggro,bullet_aggro): #this function decides which powerups (and when) the bot is going to use them
        player_HP = players[self.player_number].HP / players[self.player_number].start_HP
        if(player_aggro != None): #we're fighting another player?
            if(players[self.player_number].armor != 0):
                armor_percentage = (players[self.player_number].armor / players[self.player_number].start_armor)
            else:
                armor_percentage = 0.001 #this CAN NOT equal zero because it will lead to zerodiv errors otherwise
            powerup = int(1 / armor_percentage * self.rating) - 1 #we can't be using powerups like crazy!
            if(powerup > len(self.POWERUP_AGGRESSION_LIST) - 1): #if we lost most of our armor...we're going random!
                powerup = random.randint(0,len(self.POWERUP_AGGRESSION_LIST) - 1)
            elif(powerup < 0):
                powerup = 0
            #Now that we've chosen a powerup from self.POWERUP_AGGRESSION_LIST, we need to check to see if it's worth using it...
            if(self.POWERUP_AGGRESSION_LIST[powerup] in self.HP_DEPENDANT_POWERUPS):
                if(player_HP > 0.5): #we have more than half of our HP left?
                    players[self.player_number].use_powerup(self.POWERUP_AGGRESSION_LIST[powerup],False)
            else: #this powerup won't negatively affect HP. Let's use it!
                players[self.player_number].use_powerup(self.POWERUP_AGGRESSION_LIST[powerup],False)
        if(bullet_aggro != None): #we're trying to shoot a bullet?
            #if the bullet is getting close, and we have enough armor, we're going to use armor boost to counter the shot.
            #Also, we can use a speed boost to make ourselves move faster to shoot the bullet.
            position_difference = [
                               bullets[bullet_aggro].map_location[0] - players[self.player_number].overall_location[0],
                               bullets[bullet_aggro].map_location[1] - players[self.player_number].overall_location[1]
                               ]
            distance = pow(pow(abs(position_difference[0]),2) + pow(abs(position_difference[1]),2),0.5) #find the distance between us and the bullet
            if(distance < self.BULLET_DISTANCE_THRESHOLD): #we're too close to the bullet???
                players[self.player_number].use_powerup(0,False) #+35% speed
                if(players[self.player_number].armor > self.ARMOR_BOOST_THRESHOLD): #we have enough armor to make the armor boost worthwhile, and the bullet is really close?
                    players[self.player_number].use_powerup(5,False) #+50% armor
        #we have fire in engine? We're going to go a little more aggressive with powerups, and we're also going to extinguish that if we have no bullets coming our way.
        if(players[self.player_number].fire != 0):
            if(player_aggro): #we're going hyper-aggressive!
                if(player_HP > 0.5): #we have more than 50HP left?
                    players[self.player_number].use_powerup(2,False) #Dangerous loading (RPM boost)
                    players[self.player_number].use_powerup(3,False) #Explosive tip (fire in engine, +25% damage?)
                    players[self.player_number].use_powerup(4,False) #More penetration (I forgot what this powerup was technically called)
            if(not bullet_aggro): #we're only going to extinguish fire if we don't have a bullet coming our way.
                players[self.player_number].use_powerup(1,False) #Fire extinguisher (no fire in gas tank, -10% speed)
                players[self.player_number].use_powerup(0,False) #Improved Fuel (+35% speed) Used to counter fire extinguisher's -10% speed.

    #analyses the current game state, and creates 2 decisions based on this:
    # - A) Which direction to move, or not to move at all
    # - B) Whether to shoot or not
    def analyse_game(self,players,bullets,arena,TILE_SIZE,collideable_tiles,screen_scale=[1,1],tank_collision_offset=3,screen=None):
        #For finding player locations: [round(players[x].overall_location[0],0), round(players[x].overall_location[1],0)]
        #For finding bullet locations: [round(bullets[x].map_location[0],0), round(bullets[x].map_location[1],0)]
        #For finding arena base locations: arena.flag_locations[x]
        # - Check whether we *somehow* gliched our way outside the map boundaries (this can happen due to lag) -
        if(players[self.player_number].overall_location[0] < 0 or players[self.player_number].overall_location[0] >= len(arena.arena[0])):
            players[self.player_number].HP = -1.0
            players[self.player_number].armor = 0.0
        elif(players[self.player_number].overall_location[1] < 0 or players[self.player_number].overall_location[1] >= len(arena.arena)):
            players[self.player_number].HP = -1.0
            players[self.player_number].armor = 0.0
        if(players[self.player_number].destroyed): #we're DEAD? We don't need to do any computations anymore...
            return None
        potential_bullet = None
        move = False
        centering = False #this flag is important; It tells us whether to move at the bottom of analyse_game() or not.
        if(time.time() - self.last_compute_frame > self.FORCED_MOVE_TIME): #we need to move again?
            # - We need to center ourselves. Once we're centered, we can reset last_compute_frame -
            centered = self.self_center(players,TILE_SIZE,screen_scale)
            players[self.player_number].clear_unmove_flag()
            centering = True
            if(centered): #we've centered ourselves?
                # - Now we can set move to True, and reset last_compute_frame -
                self.last_compute_frame = time.time()
                move = True
                centering = False
        elif(self.current_position[0] + 1 <= players[self.player_number].overall_location[0] or self.current_position[0] - 1 >= players[self.player_number].overall_location[0]):
            move = True
            # - Set self.current_position to our new location -
            self.current_position[0] = round(players[self.player_number].overall_location[0],0)
        elif(self.current_position[1] + 1 <= players[self.player_number].overall_location[1] or self.current_position[1] - 1 >= players[self.player_number].overall_location[1]):
            move = True
            # - Set self.current_position to our new location -
            self.current_position[1] = round(players[self.player_number].overall_location[1],0)
        if(move): # - We only need to check for destinations and movement corrections each time we move one block -
            # - Reset self.last_compute_frame -
            self.last_compute_frame = time.time()
            self.choose_destination(players,arena,collideable_tiles) #check whether we need to find a new destination
            # - The bot needs to check if any bullets are heading its way, and if it can respond in time -
            # - Check on the X and Y axis until a wall/brick is reached to see if we have found a bullet -
            self.bullet_aggro = self.check_visible_entities(players,bullets,arena,collideable_tiles,TILE_SIZE) #bullets MUST be checked each frame because they can be deleted
            # - Now, the bot gets to check if it sees any enemies nearby -
            self.player_aggro = self.check_visible_entities(players,players,arena,collideable_tiles,TILE_SIZE)
            # - Check if we should use any powerups -
            self.use_powerups(players,bullets,self.player_aggro,self.bullet_aggro) #are we using our powerups at all?
            # - Next, the bot has to make decisions: Should I move? Should I shoot? Where should I move? -
            # So the bot knows a few things now: player_aggro is None if there are no players in sight, or the index of the tank the bot is focused on.
            # - bullet_aggro is None if there are no bullets in sight, and otherwise equals the index of the bullet the bot is focused on.
            # - The bot will always have a "destination" to reach, which can be worked toward if there is no aggros active.
            #Now, regardless of what we do (provided it doesn't involve our destination), we need to center ourselves in a block.
            if(self.player_aggro != None or self.bullet_aggro != None):
                self.find_shell(players) #we need to make sure we're using the right type of shells
                if(self.player_aggro != None): #we just have a player in focus? (this IF statement comes first, because damaging players is more important than destroying bullets)
                    self.destination = [round(players[self.player_aggro].overall_location[0],0),round(players[self.player_aggro].overall_location[1],0)] #try and find the player if we lose sight of him
                    self.destination_time = time.time()
                    tracked = self.entity_alligned(players,players[self.player_aggro],TILE_SIZE)
                    if(tracked == True): #we're in line?
                        potential_bullet = players[self.player_number].shoot(TILE_SIZE)
                elif(self.bullet_aggro != None): #we just have a bullet in focus?
                    tracked = self.entity_alligned(players,bullets[self.bullet_aggro],TILE_SIZE)
                    if(tracked == True): #we're in line?
                        potential_bullet = players[self.player_number].shoot(TILE_SIZE)
            # - Continuing towards our destination...which might be a bullet which we need to shoot! -
            self.track_location(players,arena,TILE_SIZE,screen_scale,collideable_tiles,tank_collision_offset,screen)
        elif(not centering): #just keep moving the same direction we have been to reduce CPU load
            #we only keep moving the direction we are IF we're not aggroed onto something.
            if(self.bullet_aggro == None and self.player_aggro == None or self.rating < self.AGGRO_DIR_THRESH):
                players[self.player_number].move(self.direction, TILE_SIZE, screen_scale)
            else: #if we ARE aggroed onto something, we NEED to be pointing the direction of it, NOT the other way.
                self.point_in_direction(self.direction,players,TILE_SIZE,screen_scale,auto_move=True)
        return potential_bullet
                
#The following function accepts two entity objects as a list.
#The function assumes that the two entities have already collided with each other.
#It checks whether the encounter is bullet-bullet, tank-bullet, tank-tank, as well as checking if both entities...
#...are from the same team. (no friendly fire allowed, that's for games where griefing is welcomed)
#Based on what the encounter is, this function also damages both entities appropriately.
def handle_damage(Entities): #Entities format: [ Entity 1, Entity 2 ]
    # - What's a tank game without crispy damage numbers?? -
    damage_numbers = [None, None] #Index 1 is Entity1, Index 2 is Entity 2
    # - Check if both entities are A) from the same team, or B) are both tanks (can't do damage to each other) -
    if(Entities[0].team == Entities[1].team or (Entities[0].type == "Tank" and Entities[1].type == "Tank")): #same team name?
        return None #In this case, no damage is done, and the damage handler just exits.
    else: #so we have either 2 bullets, or a tank and a bullet...
        #if entity1 can do damage, entity1.damage * (entity1.penetration / entity2.armor)
        if(Entities[0].type == "Tank"): #we know that Entities[1].type == "Bullet" then.
            if(Entities[1].fire_inflict > 1): #uh-oh. Did we get inflicted with "fire in gas tank"?
                Entities[0].fire_cause = Entities[1].tank_origin
                Entities[0].fire = Entities[1].fire_inflict
            if(Entities[0].armor > 0.0025):
                damage_numbers[0] = Entities[1].damage * (Entities[1].penetration / Entities[0].armor) #calculate the damage numbers
                if(damage_numbers[0] < 0): #negative damage? (this can happen in rare frame-perfect cases)
                    damage_numbers[0] = 0
                else:
                    Entities[0].armor -= Entities[1].damage * (Entities[1].penetration / Entities[0].armor)
                    if(Entities[0].armor < 0): #we lost so much armor that we're negative???
                        damage_numbers[0] += Entities[0].armor
                        Entities[0].armor = 0.0001 #now our armor is gone.
            else:
                Entities[0].HP -= Entities[1].damage
                damage_numbers[0] = Entities[1].damage
            Entities[1].tank_origin.total_damage += damage_numbers[0] #update the tank's damage numbers who shot the bullet
            if(Entities[0].HP <= 0): #we're dead? The player who killed us needs his kill counter bumped by one.
                Entities[1].tank_origin.kills += 1 #***Entities[1].tank_origin.clock() must be run after this occurs to prevent double-kill registering***
            Entities[1].destroyed = True #the bullet is done after it hits a tank.
        elif(Entities[1].type == "Tank"): #we know that Entities[0].type == "Bullet" then.
            if(Entities[0].fire_inflict > 1): #uh-oh. Did we get inflicted with "fire in gas tank"?
                Entities[1].fire_cause = Entities[0].tank_origin
                Entities[1].fire = Entities[0].fire_inflict
            if(Entities[1].armor > 0.0025):
                damage_numbers[1] = Entities[0].damage * (Entities[0].penetration / Entities[1].armor) #calculate the damage numbers
                if(damage_numbers[1] < 0): #negative damage? (this can happen in rare frame-perfect cases)
                    damage_numbers[1] = 0
                else:
                    Entities[1].armor -= Entities[0].damage * (Entities[0].penetration / Entities[1].armor)
                    if(Entities[1].armor < 0):
                        damage_numbers[1] += Entities[1].armor
                        Entities[1].armor = 0.0001 #now our armor is gone.
            else:
                Entities[1].HP -= Entities[0].damage
                damage_numbers[1] = Entities[0].damage
            Entities[0].tank_origin.total_damage += damage_numbers[1] #update the tank's damage numbers who shot the bullet
            if(Entities[1].HP <= 0): #we're dead? The player who killed us needs his kill counter bumped by one.
                Entities[0].tank_origin.kills += 1 #***Entities[0].tank_origin.clock() must be run after this occurs to prevent double-kill registering***
            Entities[0].destroyed = True #the bullet is done after it hits a tank.
        elif(Entities[0].type == "Bullet" and Entities[1].type == "Bullet"):
            # - There is a rare case in which one entity has 0 penetration and gets shot. This results in a 0div error, and is fixed right here -
            if(Entities[0].penetration == 0 or Entities[1].penetration == 0):
                return None
            Entity1HP = Entities[1].damage
            Entity1Armor = Entities[1].penetration
            # - Damage Entity1 first -
            damage_numbers[1] = Entities[0].damage * (Entities[0].penetration / Entities[1].penetration)
            if(damage_numbers[1] < 0): #this bullet did negative damage? (this can happen in rare frame-perfect cases)
                damage_numbers[1] = 0
            else:
                Entity1Armor -= Entities[0].damage * (Entities[0].penetration / Entities[1].penetration)
                if(Entity1Armor <= 0): #this bullet lost all its penetration (momentum, armor, whatever you want to call it)
                    damage_numbers[1] += Entity1Armor #correct this damage number so that it isn't greater than the other bullet's penetration value.
                    Entities[1].destroyed = True #the bullet lost all momentum (penetration), so its useless.
            # - Damage Entity0 second -
            damage_numbers[0] = Entities[1].damage * (Entities[1].penetration / Entities[0].penetration)
            if(damage_numbers[0] < 0): #this bullet did negative damage? (this can happen in rare frame-perfect cases)
                damage_numbers[0] = 0
            else:
                Entities[0].penetration -= Entities[1].damage * (Entities[1].penetration / Entities[0].penetration)
                if(Entities[0].penetration <= 0): #If we lose momentum, the bullet's dead.
                    damage_numbers[0] += Entities[0].penetration #correct this damage number so that it isn't over the greater than bullet's penetration value.
                    Entities[0].destroyed = True #the bullet lost all momentum (penetration), so its useless.
            # - Overwrite old Entity1 values with Entity1Armor and Entity1HP -
            Entities[1].penetration = Entity1Armor
            Entities[1].damage = Entity1HP
        return damage_numbers #return our damage numbers.

def check_collision(Entity1, Entity2, TILE_SIZE, tank_collision_offset=1):
    # - Start by getting onscreen collision coordinates -
    if(Entity1.type == "Tank"):
        entity1_collision = Entity1.return_collision(TILE_SIZE, tank_collision_offset)
    elif(Entity1.type == "Bullet" or Entity1.type == "Powerup"):
        entity1_collision = Entity1.return_collision(TILE_SIZE)
    if(Entity2.type == "Tank"):
        entity2_collision = Entity2.return_collision(TILE_SIZE, tank_collision_offset)
    elif(Entity2.type == "Bullet" or Entity1.type == "Powerup"):
        entity2_collision = Entity2.return_collision(TILE_SIZE)
    # - Now we check if each entity is A) touching each other, and if so B) which side each entity is colliding on -
    collided = False
    if(entity1_collision[2] > entity2_collision[0]): #checking if the X coordinates of the entities collide
        if(entity1_collision[0] < entity2_collision[2]): #checking if the X coordinates of the entities collide
            if(entity1_collision[1] < entity2_collision[3]): #checking if the Y coordinates of the entities collide
                if(entity1_collision[3] > entity2_collision[1]): #checking if the Y coordinates of the entities collide
                    collided = True #collision happened!
    if(collided == True): #now we need to check which side we collided on.
        side = "center"
        # - Entity2 is touching Entity1's left side? -
        if(entity1_collision[0] + 0.1 > entity2_collision[2]):
            side = "left"
        # - Entity2 is touching Entity1's right side? -
        elif(entity1_collision[2] - 0.1 < entity2_collision[0]):
            side = "right"
        # - Entity2 is touching Entity1's top side? -
        elif(entity1_collision[1] + 0.1 > entity2_collision[3]):
            side = "up"
        # - Entity2 is touching Entity1's bottom side? (that sounded weird...) -
        elif(entity1_collision[3] - 0.1 < entity2_collision[1]):
            side = "down"
        return [collided, side]
    else:
        return [collided, None]

POWERUP_SPAWN_TIME = 20.0 #X seconds between each powerup spawn
last_powerup_spawn = time.time() - 7.5 #when did we last spawn powerups?
POWERUP_CT = 10 #how many different powerups can we spawn on the map?
# - This list HAS to add up to 100; giving more ###s to a specific powerup type gives it a higher probability. Numbers are in % -
POWERUP_PROB = [6, 6, 6, 6, 6, 6,
                16, 16, 16, 16] #I intentionally biased the powerup probability towards ammunition; It is very easy to run out of ammo in larger battles, so it is very important to give the team a good supply.
def spawn_powerups(arena,powerups,images): #spawns powerups every POWERUP_SPAWN_TIME
    global POWERUP_SPAWN_TIME #we need a few global variables defined right above this function.
    global last_powerup_spawn
    global POWERUP_CT
    global POWERUP_PROB
    if(time.time() - last_powerup_spawn >= POWERUP_SPAWN_TIME): #time to spawn a powerup?
        last_powerup_spawn = time.time() #reset our powerup spawn timer
        # - Randomly pick a powerup for ALL bases to receive simultaneously; I want the matches to be even, meaning each base gets the same resources -
        new_powerup_prob = random.randint(0,100)
        powerup_num = 0 #this is the index of the powerup we're going to choose
        for x in range(0,len(POWERUP_PROB)):
            if(x == len(POWERUP_PROB) - 1): #This powerup HAS to be the one selected, since there are no more alternatives.
                powerup_num = x
                break
            else: #check if this is the powerup we should spawn
                lowsum = 0
                highsum = 0
                for getlowsum in range(0,x):
                    lowsum += POWERUP_PROB[getlowsum]
                for gethighsum in range(0,x + 1):
                    highsum += POWERUP_PROB[gethighsum]
                if(new_powerup_prob >= lowsum and new_powerup_prob <= highsum): #the random number fell in the range of the probability of the powerup we're looking at right now?
                    powerup_num = x
                    break
                
        for x in range(0,len(arena.flag_locations)): #spawn the powerup we picked at all base locations
            powerups.append(Powerup(images[powerup_num], powerup_num, arena.flag_locations[x]))

# - Checks if the two entities in entities[] are able to spot one another -
def check_visible(arena,entities,collideable_tiles,vision=5, proximity=True):
    seen = False
    # - First we have to grab locations for both entities -
    locations = []
    for x in range(0,2):
        if(entities[x].type == "Bullet" or entities[x].type == "Powerup"): #use .map_location[] then
            locations.append([entities[x].map_location[0], entities[x].map_location[1]])
        else: #use .overall_location[] then
            locations.append([entities[x].overall_location[0], entities[x].overall_location[1]])
    rounded_locations = [
        [int(round(locations[0][0], 0)), int(round(locations[0][1], 0))],
        [int(round(locations[1][0], 0)), int(round(locations[1][1], 0))]
        ]
    # - Rearrange rounded_locations so the smaller number always comes first (it doesn't matter if we swap X/Y coordinates with one entity to another in this case) -
    if(rounded_locations[0][0] > rounded_locations[1][0]):
        tmp = rounded_locations[0][0]
        rounded_locations[0][0] = rounded_locations[1][0]
        rounded_locations[1][0] = tmp
    if(rounded_locations[0][1] > rounded_locations[1][1]):
        tmp = rounded_locations[0][1]
        rounded_locations[0][1] = rounded_locations[1][1]
        rounded_locations[1][1] = tmp
    # - Now we check for alignment in an axis, and check if there are blocks in between the two entities -
    if(rounded_locations[0][0] == rounded_locations[1][0] and abs(rounded_locations[0][1] - rounded_locations[1][1]) <= vision): #alignment in the X axis + players are within sight distance of each other
        seen = True
        for y in range(rounded_locations[0][1], rounded_locations[1][1] + 1):
            if(y < len(arena.arena) and rounded_locations[0][0] < len(arena.arena[0]) and y >= 0 and rounded_locations[0][0] >= 0): #no index errors?
                if(arena.arena[y][rounded_locations[0][0]] in collideable_tiles):
                    seen = False
                    break #we can't see anything on this axis.
    if(seen == False and rounded_locations[0][1] == rounded_locations[1][1] and abs(rounded_locations[0][0] - rounded_locations[1][0]) <= vision): #alignment in the Y axis + players are within sight distance of each other
        seen = True
        for x in range(rounded_locations[0][0], rounded_locations[1][0] + 1):
            if(x < len(arena.arena[0]) and rounded_locations[0][1] < len(arena.arena) and x >= 0 and rounded_locations[0][1] >= 0): #no index errors?
                if(arena.arena[rounded_locations[0][1]][x] in collideable_tiles):
                    seen = False
                    break #we can't see anything on this axis.
    if(seen == False and proximity == True): #Check if someone got proximity spotted (vision / 2 distance)
        uncombined_distance = [
            locations[0][0] - locations[1][0],
            locations[0][1] - locations[1][1]
            ]
        distance = math.sqrt(pow(abs(uncombined_distance[0]),2) + pow(abs(uncombined_distance[1]),2))
        if(distance < vision / 2):
            seen = True 
    return seen

### - Small demo to test the entity system -
##tank = Tank([pygame.image.load("../../pix/tanks/P1U1.png"),pygame.image.load("../../pix/tanks/P1U2.png")], names=["tank name","team name"])
##
### - ...Okay, this turned into a bigger demo than I thought, but it works SO WELL!!! -
##keypresses = []
##
##directions = [ #0, 90, 180, 270
##    1073741906,
##    1073741904,
##    1073741905,
##    1073741903
##    ]
##
###hollow to disk shells
##shells_keypresses = [
##    pygame.K_a,
##    pygame.K_s,
##    pygame.K_d,
##    pygame.K_f
##    ]
##
###all 6 powerups
##powerup_keypresses = [
##    pygame.K_1,
##    pygame.K_2,
##    pygame.K_3,
##    pygame.K_4,
##    pygame.K_5,
##    pygame.K_6
##    ]
##
##screen = pygame.display.set_mode([640,480])
##minimap = pygame.Surface([150,150])
##tank.screen_location = [screen.get_width() / 2 - 10, screen.get_height() / 2 - 10]
##tank.RPM = 120.0
##
##bullets = [] #list of bullet objects
##
##running = True
##framecounter = 0
##while running:
##    #update the framecounter
##    framecounter += 1
##    if(framecounter > 65535):
##        framecounter = 0
##        
##    #update the display
##    screen.fill([0,0,0])
##    minimap.fill([0,0,0])
##    tank.draw(screen, [1.00, 1.00], 20)
##    tank.draw_minimap(minimap, tank.team)
##    tank.clock()
##    
##    #manage bullets
##    for x in range(0,len(bullets)):
##        bullets[x].clock([],framecounter)
##        bullets[x].move()
##        bullets[x].draw(screen, [1.00, 1.00], tank.map_location, 20)
##        bullets[x].draw_minimap(minimap, tank.team)
##        #check if the bullets are offscreen
##        bullet_collision = bullets[x].return_collision(20)
##        if(bullet_collision[2] < 0 or bullet_collision[0] > screen.get_width()):
##            del(bullets[x])
##            break
##        elif(bullet_collision[3] < 0 or bullet_collision[1] > screen.get_height()):
##            del(bullets[x])
##            break #if we tried to loop through all bullets now, we'd get an index error!
##        elif(bullets[x].destroyed == True):
##            del(bullets[x])
##            break
##    screen.blit(minimap, [0,0])
##    pygame.display.flip()
##
##    #manage collision between bullets
##    for x in range(0,len(bullets)):
##        for y in range(0,len(bullets)):
##            if(x == y): #no checking collision against the same bullet allowed
##                continue
##            bullet_collision = check_collision(bullets[x], bullets[y], 20)
##            if(bullet_collision[0] == True): #the bullets collided??
##                outcome = handle_damage([bullets[x],bullets[y]])
##                if(outcome != None):
##                    print(outcome[1]) #print out damage numbers
##
##    #manage collision between bullets and tanks
##    for x in range(0,len(bullets)):
##        bullet_collision = check_collision(tank, bullets[y], 20)
##        if(bullet_collision[0] == True): #bullet hit tank?
##            outcome = handle_damage([tank,bullets[y]])
##            if(outcome != None):
##                print(outcome[1]) #print damage numbers
##
##    for event in pygame.event.get():
##        if(event.type == pygame.QUIT):
##            running = False
##        elif(event.type == pygame.KEYDOWN):
##            keypresses.append(event.key)
##        elif(event.type == pygame.KEYUP):
##            del(keypresses[keypresses.index(event.key)])
##
##    if(len(keypresses) > 0): #we're trying to move?
##        try:
##            tank.move(directions.index(keypresses[0]) * 90, 20, [1,1])
##        except: #the keypress was not one of the arrow keys?
##            pass
##        try:
##            tank.use_shell(shells_keypresses.index(keypresses[0]))
##        except: #the keypress was not one of shells?
##            pass
##        try:
##            tank.use_powerup(powerup_keypresses.index(keypresses[0]))
##        except:
##            pass
##        if(pygame.K_SPACE in keypresses):
##            bullet = tank.shoot(20)
##            if(bullet != None): #no more than 1 bullet onscreen at once
##                bullets.append(bullet) #add a bullet object to the list
##
##pygame.quit()
##
### - Quick demo to test out the new goto() function for Tank() objects -
##tank = Tank("image", ["team","playername"])
##tank.screen_location = [80,80]
##
##tank.goto([4,4], TILE_SIZE=20, screen_scale=[0.5,0.5])
##
##print(tank.overall_location, tank.map_location, tank.screen_location)
