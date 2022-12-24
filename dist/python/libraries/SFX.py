##"SFX.py" library ---VERSION 0.04---
## - For creating basic audio effects with volume-based positional sound -
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

import math
import pygame
import time
import _thread

pygame.init()
pygame.mixer.init()

# - How quickly does sound decrease through distance? -
SOUND_DISPERSION = 0.075 #Xe2% volume lost per block

# - We need ID numbers to keep track of all the sounds -
ID_NUM = 0
ID_NUM_MAX = 65535

class Sound(): # - A sound playing class which takes into account position to make the sound's volume change -
    def __init__(self, sound, pos, volume, sound_id=None):
        if(sound_id == None): #sound_id would only be None on the client
            self.ID = 0
        else: #this happens on a server
            global ID_NUM
            self.ID = ID_NUM
            if(ID_NUM > ID_NUM_MAX):
                ID_NUM = 0
            else:
                ID_NUM += 1
        self.sound_id = sound_id
        self.sound = sound #this is a pygame.Sound() object.
        self.initial_volume = volume #between 0 and 1
        self.pos = pos #this is the position on the map in which the sound occurred.
        self.playing = False
        self.track_length = self.sound.get_length() #seconds
        self.track_start = time.time()

    def play(self, player_pos, server=False): #This function starts the sound playing
        # - Make sure the sound is actually playing -
        if(self.playing == False):
            if(not server): #the sound only HAS to play if this is NOT the server ROFL
                self.sound.play()
            self.playing = True
            self.track_start = time.time()
            self.clock(player_pos)

    def clock(self, player_pos): #This function ensures that the sound is played correctly. It should be called frequently.
        if(self.playing):
            # - Calculate what volume it should be played at -
            x = abs(abs(player_pos[0]) - abs(self.pos[0]))
            y = abs(abs(player_pos[1]) - abs(self.pos[1]))
            distance = math.sqrt(pow(x,2) + pow(y,2))
            volume = self.initial_volume - SOUND_DISPERSION * distance
            if(volume > 1): #make sure that any extremes (greater than 1, smaller than 0) do not occur.
                volume = 1
            elif(volume < 0):
                volume = 0
            self.sound.set_volume(volume)

            # - Check if the sound is still playing -
            if(time.time() - self.track_start >= self.track_length):
                self.playing = False #the sound itself will end of its own accord.

            # - Return the volume this sound was set to -
            return volume
        return 0 #no volume if we're not playing!

    def return_data(self, server=False):
        return [
            self.initial_volume,
            self.pos,
            self.track_length,
            time.time() - self.track_start,
            self.sound_id,
            self.ID
            ]
    
    #The actual pygame.mixer.Sound() object will have to be loaded ONCE only upon the creation of this object.
    # - Use SFX_Manager to handle that in netcode.
    def enter_data(self, data):
        self.initial_volume = data[0]
        self.pos = data[1][:]
        self.track_length = data[2]
        self.track_start = time.time() - data[3]
        self.sound_id = data[4]
        self.ID = data[5]

class Music(): # - A basic music player which can queue tracks and play them in order -
    def __init__(self):
        self.volume = 1.0
        self.music_file = None
        self.music_queue = []

    def play_track(self, track_file=None):
        if(track_file != None): #custom choice
            self.music_file = track_file
        else: #load from queue
            self.music_file = self.music_queue.pop(0)
        pygame.mixer.music.stop() #stop the old music
        pygame.mixer.music.load(self.music_file)
        pygame.mixer.music.play() #start the new stuff

    def queue_track(self, track_file):
        self.music_queue.append(track_file)

    def transition_track(self, track_file): #fades out the current track, and starts a new one.
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.queue(track_file)

    def clock(self): #this should be run frequently, e.g. a few times a second at least? Put it in the main game loop/pygame thread if it is threaded.
        end = pygame.mixer.music.get_busy() #NOTE: Music should not be paused under any circumstances! Doing so would goof this line up!
        if(end != True or self.music_file == None): #the track ended? Let's see if we can fill the soundspace with something new...
            if(len(self.music_queue) > 0): #we have a new track waiting?
                self.play_track() #load it from the queue!
            else: #return False to let us know that there's no audio!
                return False
        return True #there's still audio playing...all's well...FOR NOW

    def set_volume(self, volume):
        self.volume = volume
        pygame.mixer.music.set_volume(volume)

class SFX_Manager(): # - A manager for keeping track of multiple Sound() objects at once and transmitting sound states over netcode -
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.sounds = [] #holds the paths of all the sounds we've loaded
        self.sound_instances = [] #holds all the Sound() instances of all the self.sounds[] we're playing at the moment
        self.sound_volume = 1.0
        self.server = False #this mutes SFX_Manager so that the server isn't spitting off sound from everyone at once

    def add_sound(self, sound_file): #Load a sound into SFX_Manager()
        self.sounds.append(sound_file)

    def play_sound(self, sound_number, pos, player_pos): #Start up a new instance of a sound you added to the SFX_Manager.
        sound_file = pygame.mixer.Sound(self.sounds[sound_number])
        self.sound_instances.append(Sound(sound_file,pos,self.sound_volume,sound_number))
        self.sound_instances[len(self.sound_instances) - 1].play(player_pos, server=self.server)

    def clock(self, player_pos): #Run this every frame/several times a second at least in order to get a proper sound experience.
        decrement = 0
        for x in range(0,len(self.sound_instances)):
            self.sound_instances[x - decrement].clock(player_pos)
            if(self.sound_instances[x - decrement].playing == False):
                del(self.sound_instances[x - decrement])
                decrement += 1

    def return_data(self,player_pos=[0,0]): #player_pos is to make sure we only transmit audible sounds.
        instance_data = []
        for x in range(0,len(self.sound_instances)):
            if(self.sound_instances[x].clock(player_pos) > 0):
                instance_data.append(self.sound_instances[x].return_data())
        return [
            instance_data
            ]

    #this should under NO circumstances need to be used on the server, so sounds will automatically start as a part of this function.
    def enter_data(self, data, player_pos):
        global ID_NUM, ID_NUM_MAX
        # - We check if any sounds are greater than (or equal to) the current value of ID_NUM,
        # - OR if ID_NUM is within 90% of its full value, in which case any values greater than ID_NUM
        # - AND values which are within 10% of ID_NUM's minimum value will qualify for adding.
        # - Then, any values which we do not already have in self.sound_instances[] will be placed there promptly.
        for x in range(0,len(data[0])):
            identification = data[0][x][5]
            if(ID_NUM > ID_NUM_MAX * 0.9): #almost at the wrap-around point?
                if(identification > ID_NUM or identification < ID_NUM_MAX * 0.1):
                    add = True
                    for b in self.sound_instances:
                        if(b.ID == identification):
                            add = False
                            break
                    if(add):
                        # - Set up the sound object -
                        sound_file = pygame.mixer.Sound(self.sounds[data[0][x][4]])
                        identification = Sound(sound_file, [0,0], 1.0)
                        identification.enter_data(data[0][x])
                        identification.initial_volume *= self.sound_volume #account for the client's sound volume
                        # - Add it to our SFX_Manager() -
                        self.sound_instances.append(identification)
                        self.sound_instances[len(self.sound_instances) - 1].play(player_pos)
                        ID_NUM = self.sound_instances[len(self.sound_instances) - 1].ID
                        #print("Added sound: " + str([identification.ID, identification.sound_id])) #debug I used to make sure the sounds were getting through
            elif(identification >= ID_NUM):
                add = True
                for b in self.sound_instances:
                    if(b.ID == identification):
                        add = False
                        break
                if(add):
                    # - Set up the sound object -
                    sound_file = pygame.mixer.Sound(self.sounds[data[0][x][4]])
                    identification = Sound(sound_file, [0,0], 1.0)
                    identification.enter_data(data[0][x])
                    identification.initial_volume *= self.sound_volume #account for the client's sound volume
                    # - Add it to SFX_Manager() -
                    self.sound_instances.append(identification)
                    self.sound_instances[len(self.sound_instances) - 1].play(player_pos)
                    ID_NUM = self.sound_instances[len(self.sound_instances) - 1].ID
                    #print("Added sound: " + str([identification.ID, identification.sound_id])) #debug I used to make sure the sounds were getting through

### - Quick test of the Music() class -
##music_handler = Music()
##while True:
##    queue_tracks = music_handler.clock()
##    if(not queue_tracks):
##        music_handler.queue_track("../../sfx/music/ingame/Oasis-CK4.ogg")
##        music_handler.queue_track("../../sfx/music/ingame/Vegetables-CK4.ogg")
##    pygame.time.delay(5000)
##    music_handler.transition_track("../../sfx/music/ingame/Tank Force March.mp3")

### - Quick test for the Sound() class -
##import random
##sounds = []
##sound = pygame.mixer.Sound("../../sfx/gunshot_01.ogg")
##while True:
##    location = [random.randint(0,30), random.randint(0,30)]
##    print(location)
##    sounds.append(Sound(sound, location, 1.0, sound_id=None))
##    sounds[len(sounds) - 1].play([15,15])
##    for x in sounds:
##        x.clock([15,15]) #player is at the middle of the screen
##    for x in range(0,len(sounds)): #delete non-playing sounds
##        if(sounds[x].playing == False):
##            del(sounds[x])
##            break
##    pygame.time.delay(650)

### - Longer, more annoying test for the SFX_Manager() class -
##import random
##sfx = SFX_Manager()
##sfx.add_sound("../../sfx/gunshot_01.ogg")
##sfx.add_sound("../../sfx/driving.ogg")
##while True:
##    decision_sound = random.randint(0,30)
##    if(decision_sound > 24):
##        decision_sound = 1
##    else:
##        decision_sound = 0
##    sfx.play_sound(decision_sound, [random.randint(0,30),random.randint(0,30)], [15,15])
##    sfx.clock([15,15])
##    pygame.time.delay(540)

### - EVEN longer, more annoying test for the SFX_Manager() class's netcode features -
###     - To use, manually copy server data from server to client, and the client outputs the server-generated audio
###     - Server script is down below
##import random
##sfx_server = SFX_Manager()
##sfx_server.server = True
##sfx_server.add_sound("../../sfx/gunshot_01.ogg")
##sfx_server.add_sound("../../sfx/driving.ogg")
##while True:
##    decision_sound = random.randint(0,30)
##    if(decision_sound > 22):
##        decision_sound = 1
##    else:
##        decision_sound = 0
##    sfx_server.play_sound(decision_sound, [random.randint(0,30),random.randint(0,30)], [15,15])
##    sfx_server.clock([15,15])
##    server_data = sfx_server.return_data()
##    print(server_data)
##    input("Continue...")

### - Client script (part of the same demo above) -
##sfx = SFX_Manager()
##sfx.add_sound("../../sfx/gunshot_01.ogg")
##sfx.add_sound("../../sfx/driving.ogg")
##while True:
##    server_data = eval(input("Get server data: "))
##    sfx.enter_data(server_data,[15,15])
##    sfx.clock([15,15])
