##"entity.py" library ---VERSION 0.69---
## - For managing basically any non-map object within Tank Battalion Online (Exception: bricks) -
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

import time #very important for pacing entity movement (e.g. rotation)
import _thread #for allocate_lock() stuff; Each object has a lock in it.
import pygame #for transforming tiles
import random
import math
import GFX #for fire in gas tank / explosive tip bullet

path = ""

class Powerup(): #for collectible items within the map
    def __init__(self, image, powerup_type, location=[0.0, 0.0]):
        # - Needed for external functions -
        self.type = "Powerup" #define what this class is
        self.lock = _thread.allocate_lock()
        
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
        self.powerup_effects.append("shells[3] += 1") #+X disk shells

        # - Visual stuff -
        self.image = image

        # - Timing -
        self.spawn_time = time.time() #this value never changes; used for managing image_vfx.
        self.DESPAWN_TIME = 20.0 #seconds till despawn

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
        screen.blit(pygame.transform.scale(self.image,[int(TILE_SIZE * screen_scale[0]), int(TILE_SIZE * screen_scale[1])]), [int(screen_coordinates[0]), int(screen_coordinates[1])])

    def return_data(self, precision=2, clear_flags=None): #gathers data so this can be sent over netcode (certain attributes do not need to be sent)
        return [
            self.type,
            self.map_location,
            self.powerup_number
            ]

    def enter_data(self, data): #enters data from Powerup.return_data()
        self.map_location[0] = data[1][0]
        self.map_location[1] = data[1][1]
        self.powerup_number = data[2]

class Bullet(): #specs_multiplier format: [ damage buff/nerf, penetration buff/nerf ]
    def __init__(self, image, team_name, shell_type, direction, specs_multiplier, tank):
        # - Needed for external functions -
        self.type = "Bullet" #define what this class is
        self.lock = _thread.allocate_lock()

        # - Who shot this bullet? We need to increment the damage counter for that tank when we hit a target -
        self.tank_origin = tank
        
        # - Positional stuff -
        self.map_location = [0.0, 0.0] #where are we on the map?
        self.direction = direction

        # - Reference constants -
        self.SHELL_NUM_TO_NAME = ["hollow", "regular", "explosive", "disk"]
        self.shell_specs = [ #Format: [damage, penetration]
            [7, 7], #hollow
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

    def return_data(self, precision=2, clear_flags=None): #returns bullet data to be sent over netcode
        return [
            self.type,
            self.map_location,
            self.direction,
            self.shell_type,
            round(self.damage,precision),
            round(self.penetration,precision),
            round(self.fire_inflict,precision),
            self.team,
            self.destroyed,
            self.explosion_colors,
            self.shell_vfx,
            round(time.time() - self.spawn_time,precision) #this is needed for proper disk shell rotation.
            ]

    def enter_data(self, data): #enters data into the Bullet() object from Bullet.return_data()
        self.map_location[0] = data[1][0]
        self.map_location[1] = data[1][1]
        self.direction = data[2]
        self.shell_type = data[3]
        self.damage = data[4]
        self.penetration = data[5]
        self.fire_inflict = data[6]
        self.team = data[7]
        self.destroyed = data[8]
        self.explosion_colors = data[9]
        self.shell_vfx = data[10]
        self.spawn_time = time.time() - data[11]

class Brick():
    def __init__(self, HP, armor):
        self.type = "Tank" #I know, this isn't a tank, but it makes the damage system handle bricks the way I want it to...
        self.HP = HP #setting armor and HP, pretty streightforward
        self.armor = armor
        self.team = None #bricks don't have a team - what would bricks look like if they did?!?
        self.fire = 0 #what would happen if a brick had fire in its gas tank?????? :P

class Tank():
    def __init__(self, image='pygame.image.load()...', names=["tank name","team name"], skip_image_load=False, team_num=0, team_ct=2):
        # - Needed for external functions -
        self.type = "Tank" #define what this class is
        self.lock = _thread.allocate_lock()
        
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
        self.spotted = [] #this is a list of which teams have spotted this tank for a certain period of time.
        for x in range(0,team_ct):
            self.spotted.append(time.time())

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
        #List of powerups in index order: Improved Fuel, Fuel Fire Suppressant, Dangerous Loading, Explosive Tip,
        #Amped Gun, Makeshift Armor
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

        # - Timing stuff -
        self.old_time = time.time() #time variable
        self.time_difference = 0 #how long between each call of "clock()"?
        self.last_message = time.time() #when did the player send a message last?
        self.MESSAGE_COOLDOWN = 1.5 #seconds; How long does the player have to wait in between each message he sends?

        # - Rotation threshold constant - how close to desired direction must be achieved? -
        self.ROTATION_THRESHOLD = 10

        # - Visual stuff -
        self.image = image

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

    # - This is needed for account.py's upgrade details system -
    def update_acct_stats(self):
        self.account_stats = [[self.damage_multiplier,self.penetration_multiplier],[self.RPM],[self.armor],[self.speed]]

    # - Sets map_location, overall_location properly from the location input and screen_location -
    def goto(self,location, TILE_SIZE=20, screen_scale=[1,1]):
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
            if(self.fire > 0):
                self.fire_cause.kills += 1
            self.destroyed = True
            self.explosion_done = False
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
        if(return_damage):
            if(self.damage_second > 0.5):
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
    def move(self, direction, TILE_SIZE):
        #we MAY NOT have a negative direction value, or one over 360.
        self.direction = self.no_360_or_negative(self.direction)
        #first we check if we are facing the direction we want. If so, we don't need to wait to rotate our tank.
        if(direction == self.old_direction): #we're already facing the direction we want?
            self.goal_rotation = 0 #set this back to 0 so that we don't feel like we need to rotate...
            self.direction = self.old_direction #in case self.direction was on an offset
            # - now we need to actually move the tank -
            if(direction == 0): #we're moving up
                self.map_location[1] -= self.speed * self.time_difference
                self.last_motion[1] = -self.speed * self.time_difference
                self.last_motion[0] = 0.0
            elif(direction == 180): #we're moving down
                self.map_location[1] += self.speed * self.time_difference
                self.last_motion[1] = self.speed * self.time_difference
                self.last_motion[0] = 0.0
            elif(direction == 270): #right
                self.map_location[0] += self.speed * self.time_difference
                self.last_motion[0] = self.speed * self.time_difference
                self.last_motion[1] = 0.0
            elif(direction == 90): #left
                self.map_location[0] -= self.speed * self.time_difference
                self.last_motion[0] = -self.speed * self.time_difference
                self.last_motion[1] = 0.0
        elif(direction == self.no_360_or_negative(self.old_direction + 180)): #are we reversing?
            self.goal_rotation = 0 #set this back to 0 so that we don't feel like we need to rotate...
            self.direction = self.old_direction
            # - now we need to actually move the tank -
            if(direction == 0): #we're moving up
                self.map_location[1] -= self.speed * self.time_difference
                self.last_motion[1] = -self.speed * self.time_difference
                self.last_motion[0] = 0.0
            elif(direction == 180): #we're moving down
                self.map_location[1] += self.speed * self.time_difference
                self.last_motion[1] = self.speed * self.time_difference
                self.last_motion[0] = 0.0
            elif(direction == 270): #right
                self.map_location[0] += self.speed * self.time_difference
                self.last_motion[0] = self.speed * self.time_difference
                self.last_motion[1] = 0.0
            elif(direction == 90): #left
                self.map_location[0] -= self.speed * self.time_difference
                self.last_motion[0] = -self.speed * self.time_difference
                self.last_motion[1] = 0.0
        else: #we're gonna have to spend self.speed/2.0 seconds to rotate our tank...
            if(self.goal_rotation == 0): #only set goal_rotation if it hasn't been set yet...
                #how far do we have to rotate? Rotating left/right may create a rotation difference...
                possible_goal_rotation = self.no_360(direction - self.direction)
                other_goal_rotation = self.offset_360(possible_goal_rotation)
                if(abs(possible_goal_rotation) < abs(other_goal_rotation)):
                    self.goal_rotation = possible_goal_rotation
                else:
                    self.goal_rotation = other_goal_rotation
                self.old_direction = self.direction #bookmark our current rotation direction
            old_self_direction = self.direction #this old self.direction state is needed to calculate when we've reached the endpoint of our rotation.
            self.direction += self.goal_rotation * self.time_difference * self.speed * 2 #start rotating!
            # - Check if we are within a certain threshold of our desired rotation value...
            #If we are, we just set self.direction to that value -
            if(self.direction + self.ROTATION_THRESHOLD > direction and self.direction - self.ROTATION_THRESHOLD < direction):
                self.direction = direction
                self.goal_rotation = 0
                self.old_direction = self.direction
            elif(old_self_direction < (self.goal_rotation + self.old_direction) and self.direction > (self.goal_rotation + self.old_direction) and self.goal_rotation > 0):
                self.direction = direction
                self.goal_rotation = 0
                self.old_direction = self.direction
            elif(old_self_direction > (self.goal_rotation + self.old_direction) and self.direction < (self.goal_rotation + self.old_direction) and self.goal_rotation < 0):
                self.direction = direction
                self.goal_rotation = 0
                self.old_direction = self.direction

    def unmove(self): #reverts the last movement made by move().
        self.map_location[1] -= self.last_motion[1]
        self.map_location[0] -= self.last_motion[0]
        self.overall_location[1] -= self.last_motion[1]
        self.overall_location[0] -= self.last_motion[0]

    def draw(self, screen, screen_scale, TILE_SIZE, third_person_coords=None): #draw a tank onscreen
        # - Calculate the tank's onscreen coordinates -
        screen_coordinates = [self.map_location[0] * screen_scale[0] * TILE_SIZE + self.screen_location[0], self.map_location[1] * screen_scale[1] * TILE_SIZE + self.screen_location[1]]
        if(third_person_coords == None):
            screen_coordinates[0] -= self.map_location[0] * screen_scale[0] * TILE_SIZE #offset the coordinates because of our arena offset.
            screen_coordinates[1] -= self.map_location[1] * screen_scale[1] * TILE_SIZE
        else: #we're not the controller of this tank?
            screen_coordinates[0] -= third_person_coords[0] * screen_scale[0] * TILE_SIZE
            screen_coordinates[1] -= third_person_coords[1] * screen_scale[1] * TILE_SIZE
        # - Rotate the tank image, scale it, and paste it onscreen -
        rotated_image = pygame.transform.rotate(self.image, self.direction) #optional: switch self.direction to old_direction
        scaled_image = pygame.transform.scale(rotated_image, [int(TILE_SIZE * screen_scale[0]), int(TILE_SIZE * screen_scale[1])])
        screen.blit(scaled_image, [int(screen_coordinates[0]), int(screen_coordinates[1])])

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
        return_list = [
            self.type,
            round(self.speed,precision),
            round(self.direction,precision),
            round(self.HP,precision),
            round(self.armor,precision),
            self.team,
            self.name,
            self.destroyed,
            self.explosion_done,
            round(self.start_HP,precision),
            round(self.start_armor,precision),
            round(self.fire,precision),
            self.overall_location[:],
            round(self.goal_rotation,precision),
            round(self.old_direction,precision),
            round(time.time() - self.last_shot,precision), #seconds ago last shot happened
            self.shot_pending, #does the CLIENT want to shoot? (sorry servers, you can't do that)
            self.current_shell, #which shell does the client want to shoot?
            round(self.total_damage,precision),
            self.kills,
            self.powerup_request,
            self.shells,
            self.powerups,
            round(self.RPM,precision),
            self.message_request,
            self.team_num
            ]
        if(clear_flags):
            self.powerup_request = None #clear the powerup_request flag
            self.shot_pending = False #clear the shot_pending flag after we grab our data; This is just a good place to do it...
            self.message_request = None #clear the message_request flag
        return return_list

    def enter_data(self, data, TILE_SIZE=20, screen_scale=[1,1], server=False): #enters the data from Tank.return_data()
        if(not server):
            self.speed = data[1]
        self.direction = data[2]
        if(not server):
            self.HP = data[3]
            self.armor = data[4]
            self.team = data[5]
            self.name = data[6]
            self.destroyed = data[7]
            self.explosion_done = data[8]
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
            self.shot_pending = data[16]
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
        self.last_directions = [self.direction, self.direction + 90,0] #Important: Index 2 is a counter. Based on what it is, we modify either index 0 or index 1 when we change direction. we always try to move in this direction, or continue moving in self.direction. ALWAYS. (unless no wall)
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
        self.PATHFIND_ERROR = 0.25
        self.bot_vision = 5 #how far (in blocks) the bot can see
        self.DECISION_PRIORITY = ["bullet","player"] #first index is first priority, second index is second priority of focus, etc.
        self.CENTER_THRESHOLD = 0.15 #how close to the center of a block the bot may be to simply set his position to center.
        self.OPPOSITE_DIRECTIONS = [[90,270],[0,180]]
        self.FORCED_MOVE_TIME = 1.5
        self.LR_ANGLE = 30 #this angle determines how far left/right the bots will venture when attempting a side attack.

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
                    new_direction = math.degrees(math.asin(opposite/hypotenuse))
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
                    new_direction = math.degrees(math.asin(opposite/hypotenuse))
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
            else: #LAST RESORT OPTION!! Follow teammates/random locations
                new_destination = [0,0]
                new_destination_ct = 0 #get the avg. location of all players on our team which are alive
                for x in range(0,len(players)):
                    if(players[x].destroyed != True and players[x].team == players[self.player_number].team and x != self.player_number):
                        new_destination[0] += players[x].overall_location[0]
                        new_destination[1] += players[x].overall_location[1]
                        new_destination_ct += 1
                if(new_destination_ct == 0):
                    #RANDOM LOCATIONS because no players to follow =(
                    new_destination = [random.randint(0,len(arena.arena[0])), random.randint(0,len(arena.arena))]
                else: #follow the leader...
                    new_destination[0] /= new_destination_ct
                    new_destination[1] /= new_destination_ct
                self.destination = new_destination
            # - Now, we have to check if our destination is ontop of a block. If it is, we have to shift our destination until it isn't -
            is_on_block = False
            dummy_tank = Tank(image='', names=["dt","tn"], skip_image_load=True)
            dummy_tank.overall_location = self.destination[:]
            dummy_collision = arena.check_collision([1,1], dummy_tank.overall_location[:], dummy_tank.return_collision(arena.TILE_SIZE,1))
            for dummy_tile in dummy_collision:
                if(dummy_tile[0] in blocks):
                    # - Uhoh...now we know that our destination IS on a block! -
                    is_on_block = True
            if(is_on_block): #now we have to shift self.destination around until we get a tile where it isn't on a block...
                directions = [
                    [1,0],
                    [0,-1],
                    [-1,0],
                    [0,1]
                    ]
                position = self.destination[:]
                size = 0 #how wide the circle is that we are using to check for a new destination point
                while is_on_block == True:
                    size += 2
                    for z in range(0,4):
                        for length in range(0,size):
                            # - Update the new potential self.destination point -
                            position[0] += directions[z][0]
                            position[1] += directions[z][1]
                            # - Check if the new self.destination point is NOT ontop of any blocks -
                            dummy_tank.overall_location = position[:]
                            dummy_collision = arena.check_collision([1,1], dummy_tank.overall_location[:], dummy_tank.return_collision(arena.TILE_SIZE,1))
                            is_on_block = False #we start by assuming we're not on a block...
                            for dummy_tile in dummy_collision:
                                if(dummy_tile[0] in blocks):
                                    # - Uhoh...now we know that our destination IS on a block! -
                                    is_on_block = True
                            if(not is_on_block): #we found a valid destination???
                                # - We still need to check if this destination is *outside* the map. If it is, we're not ever going to get there -
                                if(position[0] >= len(arena.arena[0]) or position[0] <= 0 or position[1] <= 0 or position[1] >= len(arena.arena)):
                                    is_on_block = True #this is not a valid position
                                else: #this is a valid position
                                    self.destination = position[:]
                                    break
                        if(not is_on_block):
                            break
                    position[0] -= 1
                    position[1] += 1
                    if(not is_on_block):
                        break

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
            players[self.player_number].move(direction, TILE_SIZE)
        elif(abs(players[self.player_number].overall_location[1] - round(players[self.player_number].overall_location[1],0)) > self.CENTER_THRESHOLD):
            centered = False
            #we're not centered on the Y axis!
            off_center = players[self.player_number].overall_location[1] - round(players[self.player_number].overall_location[1],0)
            if(off_center > 0): #we need to move up
                direction = 0 #up
            else:
                direction = 180 #down
            players[self.player_number].move(direction, TILE_SIZE)
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
        available_directions = [0,180,90,270]
        visible_tiles = [2,2]
        # - How much further are we trying to go in each direction? -
        #   - We move a dummy tank this amount from our current position to tell if we can move...
        increment = offset / TILE_SIZE * 1.025
        #first, we're checking if we can move left.
        dummy_tank = Tank(image='', names=["dt","tn"], skip_image_load=True)
        dummy_tank.map_location[0] = players[self.player_number].overall_location[0] - increment #round(players[self.player_number].overall_location[0],0) - 1
        dummy_tank.map_location[1] = players[self.player_number].overall_location[1] #round(players[self.player_number].overall_location[1],0)
        dummy_tank.clock(TILE_SIZE)
        tile_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
        dummy_collision = arena.check_collision(visible_tiles, tile_offset, dummy_tank.return_collision(TILE_SIZE,offset))
        for dummy_tile in dummy_collision:
            if(dummy_tile[0] in collideable_tiles):
                available_directions.remove(90)
                break
        #next, we're checking if we can move right.
        dummy_tank = Tank(image='', names=["dt","tn"], skip_image_load=True)
        dummy_tank.map_location[0] = players[self.player_number].overall_location[0] + increment #round(players[self.player_number].overall_location[0],0) + 1
        dummy_tank.map_location[1] = players[self.player_number].overall_location[1] #round(players[self.player_number].overall_location[1],0)
        dummy_tank.clock(TILE_SIZE)
        tile_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
        dummy_collision = arena.check_collision(visible_tiles, tile_offset, dummy_tank.return_collision(TILE_SIZE,offset))
        for dummy_tile in dummy_collision:
            if(dummy_tile[0] in collideable_tiles):
                available_directions.remove(270)
                break
        #Now we're checking if we can move up.
        dummy_tank = Tank(image='', names=["dt","tn"], skip_image_load=True)
        dummy_tank.map_location[0] = players[self.player_number].overall_location[0] #round(players[self.player_number].overall_location[0],0)
        dummy_tank.map_location[1] = players[self.player_number].overall_location[1] - increment #round(players[self.player_number].overall_location[1],0) - 1
        dummy_tank.clock(TILE_SIZE)
        tile_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
        dummy_collision = arena.check_collision(visible_tiles, tile_offset, dummy_tank.return_collision(TILE_SIZE,offset))
        for dummy_tile in dummy_collision:
            if(dummy_tile[0] in collideable_tiles):
                available_directions.remove(0)
                break
        #first, we're checking if we can move down.
        dummy_tank = Tank(image='', names=["dt","tn"], skip_image_load=True)
        dummy_tank.map_location[0] = players[self.player_number].overall_location[0] #round(players[self.player_number].overall_location[0],0)
        dummy_tank.map_location[1] = players[self.player_number].overall_location[1] + increment #round(players[self.player_number].overall_location[1],0) + 1
        dummy_tank.clock(TILE_SIZE)
        tile_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
        dummy_collision = arena.check_collision(visible_tiles, tile_offset, dummy_tank.return_collision(TILE_SIZE,offset))
        for dummy_tile in dummy_collision:
            if(dummy_tile[0] in collideable_tiles):
                available_directions.remove(180)
                break
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
                    if(players[self.player_number].direction == 0): #180 is down in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
            else:
                if(position_difference[0] > 0): #right
                    if(players[self.player_number].direction == 270): #180 is down in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
                else: #left
                    if(players[self.player_number].direction == 90): #180 is down in my entity engine (I know, you're all annoyed at me).
                        return True
                    else:
                        return False
            return True
        else:
            return False

    #points the bot's tank in the specified direction + moves in that direction if auto_move == True
    def point_in_direction(self,direction,players,TILE_SIZE,auto_move=False):
        if(players[self.player_number].old_direction != direction): #we're NOT already pointing in the right direction?
            #are we 90 degrees off? If so, we can just move towards the right direction.
            if(players[self.player_number].old_direction == self.no_360_or_negative(direction + 90) or players[self.player_number].old_direction == self.no_360_or_negative(direction - 90)):
                players[self.player_number].move(direction,TILE_SIZE)
            else: #we're 180 degrees - aka, backwards. We need to rotate 90 degrees before we can point in the right direction to avoid reversing.
                players[self.player_number].move(self.no_360_or_negative(direction + 90),TILE_SIZE)
            return False
        else: #let our bot program know we're pointing in the right direction!
            if(auto_move):
                players[self.player_number].move(direction,TILE_SIZE)
            return True

    #checks for entities within the bot's line of sight. Returns either the first one seen, or None.
    def check_visible_entities(self,players,entities,arena,collideable_tiles,TILE_SIZE):
        seen = None
        visible_tiles = [2,2] #for checking arena collision
        for x in range(0,len(entities)):
            if(entities[x].team == players[self.player_number].team): #entities on our own team don't count!
                continue
            if(entities[x].destroyed == True): #we don't check for destroyed entities.
                continue
            # - Check on the X and Y axis until a wall/brick is reached to see if we have found an entity -
            dummy_tank = Tank(image='img', names=["dt","tn"], skip_image_load=True)
            dummy_tank.map_location = [round(players[self.player_number].overall_location[0],0),round(players[self.player_number].overall_location[1],0)]
            dummy_tank.clock(TILE_SIZE)
            wall = False #this becomes true if we try looking through a wall.
            for check_x in range(0,self.bot_vision + 1): #the bot can only see this far in each direction
                #check if we are trying to look through a wall...
                arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
                collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
                for tile in collided_tiles:
                    if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                        wall = True
                        break #exit the collision loop
                if(wall):
                    break
                dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another enemy.
                if(check_collision(dummy_tank, entities[x], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                    seen = x
                    break
                dummy_tank.map_location[0] -= 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            if(seen == None): #check the other way on the X axis
                dummy_tank.map_location = [round(players[self.player_number].overall_location[0],0),round(players[self.player_number].overall_location[1],0)]
                dummy_tank.clock(TILE_SIZE)
                wall = False #this becomes true if we try looking through a wall.
                for check_x in range(0,self.bot_vision): #the bot can only see this far in each direction
                    #check if we are trying to look through a wall...
                    arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
                    collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
                    for tile in collided_tiles:
                        if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                            wall = True
                            break #exit the collision loop
                    if(wall):
                        break
                    dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another enemy.
                    if(check_collision(dummy_tank, entities[x], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                        seen = x
                        break
                    dummy_tank.map_location[0] += 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            if(seen == None):
                wall = False
                dummy_tank.map_location = [round(players[self.player_number].overall_location[0],0),round(players[self.player_number].overall_location[1],0)]
                dummy_tank.clock(TILE_SIZE)
                for check_y in range(0,self.bot_vision + 1):
                    #check if we are trying to look through a wall...
                    arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
                    collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
                    for tile in collided_tiles:
                        if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                            wall = True
                            break #exit the collision loop
                    if(wall):
                        break
                    dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another entity.
                    if(check_collision(dummy_tank, entities[x], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                        seen = x
                        break
                    dummy_tank.map_location[1] -= 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            if(seen == None):
                wall = False
                dummy_tank.map_location = [round(players[self.player_number].overall_location[0],0),round(players[self.player_number].overall_location[1],0)]
                dummy_tank.clock(TILE_SIZE)
                for check_y in range(0, self.bot_vision):
                    #check if we are trying to look through a wall...
                    arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
                    collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
                    for tile in collided_tiles:
                        if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                            wall = True
                            break #exit the collision loop
                    if(wall):
                        break
                    dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another entity.
                    if(check_collision(dummy_tank, entities[x], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                        seen = x
                        break
                    dummy_tank.map_location[1] += 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            else: #if the bot has found an entity, it needs to shoot it, not get distracted by another one!
                break
        return seen

    #Tries to move in one of a few given directions. Input a list of preferred directions, starting with highest priority.
    def directional_move(self,players,available_directions,preferred_directions,TILE_SIZE,arena,collideable_tiles,screen=None):
        # - Needed debug info -
        #screen_scale = arena.get_scale([10,10],screen)
        #player_offset = players[0].map_location[:]
        # - A few of these checks have to pass the self.last_turn_location check: Basically, has the bot already made a turn on this square last? -
        rounded_position = [round(players[self.player_number].overall_location[0],0),round(players[self.player_number].overall_location[1],0)]
        wall = False #do we have a wall between us and our destination??
        # - Negative 1st: Find whether there is a SINGLE wall between us and our destination -
        position_difference = [self.destination[0] - rounded_position[0], self.destination[1] - rounded_position[1]]
        dummy_tank = Tank("img",["dt","tn"],True) #create a tank with no images
        if(position_difference[0] == 0): #catch any 0div errors, when X difference = 0 (vertical)
            progression = position_difference[1] #move position_difference[1] without moving right/left
            trace = rounded_position[1]
            for x in range(0,int(abs(progression))):
                # - Now we check if we hit a block (we only have to check THE block because this script rounds) -
                dummy_tank.overall_location = [rounded_position[0], trace]
                # - This is debug -
                #pygame.draw.rect(screen,[255,255,255],[(dummy_tank.overall_location[0] - player_offset[0]) * TILE_SIZE * screen_scale[0],(dummy_tank.overall_location[1] - player_offset[1]) * TILE_SIZE * screen_scale[1],TILE_SIZE * screen_scale[0],TILE_SIZE * screen_scale[1]],5)
                # - Continuing... -
                collision = arena.check_collision([1,1], dummy_tank.overall_location[:], dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
                for x in collision:
                    if(x[0] in collideable_tiles):
                        wall = True
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
                    # - Now we check if we hit a block (we only have to check THE block because this script rounds) -
                    dummy_tank.overall_location = [x_trace, y_trace]
                    # - This is debug -
                    #pygame.draw.rect(screen,[255,255,255],[(dummy_tank.overall_location[0] - player_offset[0]) * TILE_SIZE * screen_scale[0],(dummy_tank.overall_location[1] - player_offset[1]) * TILE_SIZE * screen_scale[1],TILE_SIZE * screen_scale[0],TILE_SIZE * screen_scale[1]],5)
                    # - Continuing... -
                    collision = arena.check_collision([1,1], dummy_tank.overall_location[:], dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
                    for b in collision:
                        if(b[0] in collideable_tiles):
                            wall = True
                    if(progression > 0):
                        y_trace += 1
                    else:
                        y_trace -= 1
                y_trace = round(progression * x + rounded_position[1],0)
                x_trace += direction
        # - Setup -
        successful_move = False
        player_direction = self.direction
        # - First: Check if we can just keep moving in the direction we are currently moving in -
        if(successful_move == False and player_direction in available_directions and (player_direction in preferred_directions or (wall and (player_direction == self.last_directions[0] or player_direction == self.last_directions[1])))):
            successful_move = True
            #print("Streight ahead") #debug
        # - Second: Check if we can move in either of our self.last_directions IF wall -
        if(successful_move == False and wall):
            for x in range(0,len(available_directions)):
                if(available_directions[x] == self.last_directions[0] and self.no_360_or_negative(180 + available_directions[x]) != self.direction or available_directions[x] == self.last_directions[1] and self.no_360_or_negative(180 + available_directions[x]) != self.direction):
                    self.last_directions.insert(0,self.direction)
                    self.last_directions.pop(1)
                    self.direction = available_directions[x]
                    self.last_turn_location = rounded_position[:]
                    successful_move = True
                    break
        # - Third: If no wall, we need to try move towards our destination -
        if(successful_move == False and not wall):
            for x in range(0,len(available_directions)):
                if(available_directions[x] in preferred_directions and self.no_360_or_negative(180 + available_directions[x]) != self.direction):
                    self.last_directions.insert(0,self.direction)
                    self.last_directions.pop(1)
                    self.direction = available_directions[x]
                    self.last_turn_location = rounded_position[:]
                    successful_move = True
                    break
        # - Fourth: Regardless of wall, we need to try and move in one of our self.last_directions -
        if(successful_move == False):
            for x in range(0,len(available_directions)):
                if(available_directions[x] == self.last_directions[0] and self.no_360_or_negative(180 + available_directions[x]) != self.direction or available_directions[x] == self.last_directions[1] and self.no_360_or_negative(180 + available_directions[x]) != self.direction):
                    self.last_directions.insert(0,self.direction)
                    self.last_directions.pop(1)
                    self.direction = available_directions[x]
                    self.last_turn_location = rounded_position[:]
                    successful_move = True
                    break
        # - Fifth: Just pick a random available direction -
        #if we haven't found a direction by now...well I give up. Usually this occurs when we're cornered.
        if(successful_move == False and len(available_directions) > 0):
            self.last_directions[self.last_directions[2] % 2] = self.direction
            self.last_directions[2] += 1 #change the modifier factor in self.last_directions
            if(self.last_directions[2] >= 2):
                self.last_directions[2] = 0
            self.direction = available_directions[random.randint(0,len(available_directions) - 1)]
            if(self.direction != players[self.player_number].old_direction):
                self.last_turn_location = rounded_position[:] #reset our turn location variable
            #print("RNG") #debug for when the bot resorts to an RNG roll
        players[self.player_number].move(self.direction,TILE_SIZE)

    def track_location(self,players,arena,TILE_SIZE,collideable_tiles,tank_collision_offset,screen): #tries to reach self.destination.
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
        self.directional_move(players,available_directions,goal_directions,TILE_SIZE,arena,collideable_tiles,screen)

    def find_shell(self,players): #simple script which decides which shell the AI is going to shoot
        #We need to make sure we are using shells which we can shoot! We shouldn't waste time trying to shoot a shell which we don't own!
        player_HP = (players[self.player_number].HP / players[self.player_number].start_HP) / self.rating
        if(player_HP > 1.0): #due to the division by self.rating, I need to check if player_HP is above 1.0 to make sure the bot functions as expected.
            player_HP = 1.0
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
            powerup = int(1 / (players[self.player_number].armor / players[self.player_number].start_armor) * self.rating) - 1 #we can't be using powerups like crazy!
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
        potential_bullet = None
        move = False
        centering = False #this flag is important; It tells us whether to move at the bottom of analyse_game() or not.
        if(time.time() - self.last_compute_frame > self.FORCED_MOVE_TIME): #we need to move again?
            # - We need to center ourselves. Once we're centered, we can reset last_compute_frame -
            centered = self.self_center(players,TILE_SIZE,screen_scale)
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
            #if(time.time() - self.last_entity_check > self.LAST_ENTITY_CHECK_TIME):
                #self.last_entity_check = time.time() #reset our cooldown timer - This is here to promote higher performance levels
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
            self.track_location(players,arena,TILE_SIZE,collideable_tiles,tank_collision_offset,screen)
        elif(not centering): #just keep moving the same direction we have been to reduce CPU load
            players[self.player_number].move(self.direction, TILE_SIZE)
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
                Entities[0].fire = Entities[1].fire_inflict
                Entities[0].fire_cause = Entities[1].tank_origin
            if(Entities[0].armor > 0.0025):
                damage_numbers[0] = Entities[1].damage * (Entities[1].penetration / Entities[0].armor) #calculate the damage numbers
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
                Entities[1].fire = Entities[0].fire_inflict
                Entities[1].fire_cause = Entities[0].tank_origin
            if(Entities[1].armor > 0.0025):
                damage_numbers[1] = Entities[0].damage * (Entities[0].penetration / Entities[1].armor) #calculate the damage numbers
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
            Entity1HP = Entities[1].damage
            Entity1Armor = Entities[1].penetration
            # - Damage Entity1 first -
            damage_numbers[1] = Entities[0].damage * (Entities[0].penetration / Entity1Armor)
            Entity1Armor -= Entities[0].damage * (Entities[0].penetration / Entity1Armor)
            if(Entity1Armor <= 0): #this bullet lost all its penetration (momentum, armor, whatever you want to call it)
                damage_numbers[1] += Entity1Armor #correct this damage number so that it isn't greater than the other bullet's penetration value.
                Entities[1].destroyed = True #the bullet lost all momentum (penetration), so its useless.
            # - Damage Entity0 second -
            damage_numbers[0] = Entities[1].damage * (Entities[1].penetration / Entities[0].penetration)
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

POWERUP_SPAWN_TIME = 45.0 #X seconds between each powerup spawn
last_powerup_spawn = time.time() - POWERUP_SPAWN_TIME / 1.5 #when did we last spawn powerups?
POWERUP_CT = 10 #how many different powerups can we spawn on the map?
def spawn_powerups(arena,powerups,images): #spawns powerups every POWERUP_SPAWN_TIME
    global POWERUP_SPAWN_TIME #we need a few global variables defined right above this function.
    global last_powerup_spawn
    global POWERUP_CT
    if(time.time() - last_powerup_spawn >= POWERUP_SPAWN_TIME): #time to spawn a powerup?
        last_powerup_spawn = time.time() #reset our powerup spawn timer
        for x in range(0,len(arena.flag_locations)):
            powerups.append(Powerup(images[x], random.randint(0,POWERUP_CT - 1), arena.flag_locations[x]))

# - Checks if the two entities in entities[] are able to spot one another -
def check_visible(arena,entities,collideable_tiles,vision=5):
    TILE_SIZE = arena.TILE_SIZE
    seen = False
    visible_tiles = [2,2] #for checking arena collision
    # - Check on the X and Y axis until a wall/brick is reached to see if we have found an entity -
    dummy_tank = Tank(image='img', names=["dt","tn"], skip_image_load=True)
    dummy_tank.map_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
    dummy_tank.overall_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
    dummy_tank.clock(TILE_SIZE)
    wall = False #this becomes true if we try looking through a wall.
    for check_x in range(0,vision + 1): #the bot can only see this far in each direction
        #check if we are trying to look through a wall...
        arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
        collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
        for tile in collided_tiles:
            if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                wall = True
                break #exit the collision loop
        if(wall):
            break
        dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another enemy.
        if(check_collision(dummy_tank, entities[1], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
            seen = True
            break
        dummy_tank.map_location[0] -= 1 #keep updating the dummy tank's position and check if an entity has collided with it.
        dummy_tank.overall_location[0] -= 1
    if(seen == False): #check the other way on the X axis
        dummy_tank.map_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
        dummy_tank.overall_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
        dummy_tank.clock(TILE_SIZE)
        wall = False #this becomes true if we try looking through a wall.
        for check_x in range(0,vision): #the bot can only see this far in each direction
            #check if we are trying to look through a wall...
            arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
            collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
            for tile in collided_tiles:
                if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                    wall = True
                    break #exit the collision loop
            if(wall):
                break
            dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another enemy.
            if(check_collision(dummy_tank, entities[1], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                seen = True
                break
            dummy_tank.map_location[0] += 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            dummy_tank.overall_location[0] += 1
    if(seen == False):
        wall = False
        dummy_tank.map_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
        dummy_tank.overall_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
        dummy_tank.clock(TILE_SIZE)
        for check_y in range(0,vision + 1):
            #check if we are trying to look through a wall...
            arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
            collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
            for tile in collided_tiles:
                if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                    wall = True
                    break #exit the collision loop
            if(wall):
                break
            dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another entity.
            if(check_collision(dummy_tank, entities[1], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                seen = True
                break
            dummy_tank.map_location[1] -= 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            dummy_tank.overall_location[1] -= 1
    if(seen == False):
        wall = False
        dummy_tank.map_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
        dummy_tank.overall_location = [round(entities[0].overall_location[0],0),round(entities[0].overall_location[1],0)]
        dummy_tank.clock(TILE_SIZE)
        for check_y in range(0,vision):
            #check if we are trying to look through a wall...
            arena_offset = [int(dummy_tank.overall_location[0]), int(dummy_tank.overall_location[1])]
            collided_tiles = arena.check_collision(visible_tiles, arena_offset, dummy_tank.return_collision(TILE_SIZE,TILE_SIZE * 0.1))
            for tile in collided_tiles:
                if(tile[0] in collideable_tiles): #we're trying to look through a wall...
                    wall = True
                    break #exit the collision loop
            if(wall):
                break
            dummy_tank.clock(TILE_SIZE) # - If so, we need to try and target him until...he gets out of view, or we get distracted by another entity.
            if(check_collision(dummy_tank, entities[1], TILE_SIZE, TILE_SIZE * 0.15)[0] == True): #we can see another entity who is NOT on our team???
                seen = True
                break
            dummy_tank.map_location[1] += 1 #keep updating the dummy tank's position and check if an entity has collided with it.
            dummy_tank.overall_location[1] += 1
    if(seen == False): #Check if someone got proximity spotted (vision / 2 distance)
        uncombined_distance = [
            entities[0].overall_location[0] - entities[1].overall_location[0],
            entities[0].overall_location[1] - entities[1].overall_location[1]
            ]
        distance = math.sqrt(pow(abs(uncombined_distance[0]),2) + pow(abs(uncombined_distance[1]),2))
        if(distance < vision / 2):
            seen = True 
    return seen

###Small demo to test the entity system
##tank = Tank(pygame.image.load("../../pix/Characters(gub)/p1U.png"), names=["tank name","team name"])
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
##    tank.draw(screen, [1.00, 1.00], 20)
##    tank.clock()
##    
##    #manage bullets
##    for x in range(0,len(bullets)):
##        bullets[x].clock([],framecounter)
##        bullets[x].move()
##        bullets[x].draw(screen, [1.00, 1.00], tank.map_location, 20)
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
##            tank.move(directions.index(keypresses[0]) * 90, 20)
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

### - Quick demo to test out the new goto() function for Tank() objects -
##tank = Tank("image", ["team","playername"])
##tank.screen_location = [80,80]
##
##tank.goto([4,4], TILE_SIZE=20, screen_scale=[0.5,0.5])
##
##print(tank.overall_location, tank.map_location, tank.screen_location)
