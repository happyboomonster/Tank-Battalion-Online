##"battle_client.py" library ---VERSION 0.74---
## - Handles client stuff (battles, main game loops, lobby stuff, and game setup) -
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

#Python external libraries:
import _thread, socket, pygame, time, sys, os, random, math, pickle
#set up external directories
sys.path.insert(0, "../maps")
#My own proprietary libraries (I just realized that there's a lot of them):
import account, menu, HUD, netcode, font, arena, GFX, SFX, import_arena, entity, arena as arena_lib, controller, pygame_multithread, battle_server
# - Netcode.py sets its default socket timeout to 5 seconds. However, we MUST take longer than the server does, so I will increase it to 7.5 seconds -
netcode.DEFAULT_TIMEOUT = 7.5 #seconds

# - This is a global which tells us the path to find the directory battle_client is stored in -
path = ""

def init(path_str=""):
    global path
    path = path_str
    entity.path = path_str
    import_arena.path = path_str
    battle_server.init(path)

class BattleEngine():
    def __init__(self,IP,PORT,autostart=True):
        global path
        
        # - What is our netcode buffersize? This is very important to ensure that netcode actually gets through, and should not be changed. -
        self.buffersize = 10

        # - List of all music files for lobby, queue, and ingame -
        self.music_files = [
            [ #lobby (automatically populated with any music in the sfx/music/lobby folder)
                ],
            [ #queue (automatically populated with any music in the sfx/music/queue folder)
                ],
            [ #ingame (automatically populated with any music in the sfx/music/ingame folder)
                ]
            ]
        lobby_music = os.listdir(path + "../../sfx/music/lobby/") #locate all available music in the designated folders
        queue_music = os.listdir(path + "../../sfx/music/queue/")
        ingame_music = os.listdir(path + "../../sfx/music/ingame/")
        for x in lobby_music: #add located music files to the self.music_files list
            self.music_files[0].append( path + "../../sfx/music/lobby/" + x )
        for x in queue_music:
            self.music_files[1].append( path + "../../sfx/music/queue/" + x )
        for x in ingame_music:
            self.music_files[2].append( path + "../../sfx/music/ingame/" + x )

        # - Screen constants -
        self.PYGAME_FLAGS = pygame.RESIZABLE
        self.min_screen_size = [75,75]

        # - Needed to check whether we are still connected to the server -
        self.lobby_connected = 0

        # - Default key configuration settings -
        self.controls = controller.Controls(4 + 6 + 4 + 1 + 1 + 1 + 1,"kb") #4: shells - 6: powerups - 4: movement - 1: shoot  - 1: ESC key - 1: Crosshair modifier - 1: Push-To-Talk (combine with other buttons to make a message onscreen as a particle)
        self.controls.buttons = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_t]
        self.controls.init_default_buttons([pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_t])


        # - Create a backup controller object in case we mess up our default controller (and it's in JS mode) -
        self.controls_backup = controller.Controls(4 + 6 + 4 + 1 + 1 + 1 + 1,"kb") #4: shells - 6: powerups - 4: movement - 1: shoot  - 1: ESC key - 1: Crosshair modifier - 1: Push-To-Talk (combine with other buttons to make a message onscreen as a particle)
        self.controls_backup.buttons = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_t]

        # - Packet formats (what we recieve from the server) -
        self.LOBBY_PACKETS = [["<class 'bool'>", "<class 'list'>", "<class 'list'>"],
                              ["<class 'NoneType'>", "<class 'list'>", "<class 'list'>"],
                              ["<class 'bool'>", "<class 'list'>", "<class 'NoneType'>"],
                              ["<class 'NoneType'>", "<class 'list'>", "<class 'NoneType'>"],
                              ["<class 'bool'>", "<class 'str'>", "<class 'list'>", "<class 'NoneType'>"]]
        self.MATCH_PACKET = ["<class 'bool'>", "<class 'list'>", "<class 'int'>"] #[in_battle(True/False), viewing_players data list, player_count]
        self.GAME_PACKETS = [ #the last sublists of the game_packet do not get transmitted every packet...and the data isn't a consistent type either =(
            ["<class 'str'>", "...", "...", "...", "...", "...", "...", "..."],
            ["<class 'str'>", "...", "...", "...", "...", "...", "..."],
            ["<class 'str'>", "...", "...", "...", "...", "..."],
            ["<class 'str'>", "...", "...", "...", "..."],
            ["<class 'str'>", "...", "...", "..."],
            ["<class 'str'>", "...", "..."],
            ["<class 'str'>", "..."],
            ["<class 'str'>"]
            ]

        # - Constants for properly displaying player rating in matchmaking -
        self.battle_types = ["Unrated Battle","Experience Battle"]
        self.rated_battles = [False, True] #simply tells which battles count rating and which ones don't.

        # - Lobby stuff -
        self.request = [None]
        self.response = []
        self.request_lock = _thread.allocate_lock()
        self.response_lock = _thread.allocate_lock()
        #This time value is to keep track of whether we have a request pending. True=complete, False=fail, int=waiting for server response.
        # - It controls whether clicking will be registered -
        self.request_pending = True
        self.request_pending_lock = _thread.allocate_lock()
        #This flag is for keeping track of whether or not we are waiting to get into the battle queue...
        self.waiting_for_queue = False
        self.waiting_for_queue_lock = _thread.allocate_lock()
        # - For displaying special stuff, such as end-game results -
        self.special_window = None
        self.special_window_lock = _thread.allocate_lock()
        # - This list keeps track of our settings, and tries to send them to the server to be saved -
        self.settings_data = [None]
        
        # - Create a dummy account object we can use to easily display our stats in the lobby using enter_data() -
        self.acct = account.Account("name","pwd")
        self.acct_lock = _thread.allocate_lock()

        # - Global Game-round necessary stuff -
        self.running = True #when this goes False, the whole GAME is going down...
        self.running_lock = _thread.allocate_lock()
        self.music = SFX.Music() #this is our music controller (handled client-side)
        self.sfx = SFX.SFX_Manager() #this is our SFX controller (handled mostly server-side)
        self.sfx.add_sound(path + "../../sfx/gunshot_01.wav")
        self.sfx.add_sound(path + "../../sfx/driving.wav")
        self.sfx.add_sound(path + "../../sfx/thump.wav")
        self.sfx.add_sound(path + "../../sfx/explosion_large.wav")
        self.sfx.add_sound(path + "../../sfx/crack.wav")
        self.GUNSHOT = 0 #constants which correspond to SFX_Manager() sounds
        self.DRIVING = 1
        self.THUMP = 2
        self.EXPLOSION = 3
        self.CRACK = 4

        # - Create a mapping list which converts the specialization number into meaningful words -
        self.specialization_offset = 6
        self.specialization_mapper = [
            "SuperHeavy",
            "Insanely Heavy",
            "Heavy",
            "Medium-Heavy",
            "A Touch of Heavy",
            "Semi-Useless Heavy",
            "Medium",
            "Basically Medium",
            "Slightly Light",
            "Medium-Light",
            "Light",
            "Insanely Light",
            "SuperLight"]

        # - Import tank images (these should NOT have .convert() run on them, since we still need to manipulate them before blitting) -
        self.team_images = [[pygame.image.load(path + "../../pix/tanks/P1U1.png"),pygame.image.load(path + "../../pix/tanks/P1U2.png")],
                            [pygame.image.load(path + "../../pix/tanks/P2U1.png"),pygame.image.load(path + "../../pix/tanks/P2U2.png")],
                            [pygame.image.load(path + "../../pix/tanks/P3U1.png"),pygame.image.load(path + "../../pix/tanks/P3U2.png")],
                            [pygame.image.load(path + "../../pix/tanks/P4U1.png"),pygame.image.load(path + "../../pix/tanks/P4U2.png")]
                            ]

        # - Matchmaker constants -
        self.EXP_WEIGHT = 0.00005 #this defines the overall power of a player (more EXP = more experienced player = more strategic = more dangerous)
        self.UPGRADE_WEIGHTS = [2.1/6, 1.77/6, 1.71/6, 1.125/6] #this defines the overall power of a player (more upgrades = more powerful tank) [gun, rpm, armor, engine]
        self.CASH_WEIGHT = 0.000001 #this defines the overall power of a player (more cash = more disk shells the player can buy = more dangerous)
        self.SHELLS_WEIGHT = [1.17 / account.max_shells[0], 1.75 / account.max_shells[1], #hollow shells are 1.17 because I raised their D/P from 7/7 to 8/8.
                              2.625 / account.max_shells[2], 2.625 / account.max_shells[3]] #this defines the overall power of a player (more shells = more dangerous)
        self.POWERUP_WEIGHT = 1.24 #this defines the overall power of a player (more powerups = more dangerous)
        self.SPECIALIZATION_WEIGHT = 0.025 #this defines the overall power of a player (more specialized = potentially more dangerous...?)
        # - All calculated ratings are divided by this number so that our numbers are within a certain range (I like between 0 and 30 roughly) -
        self.MMCEF = 0
        self.MMCEF += self.POWERUP_WEIGHT * len(account.Account().powerups) #powerups
        self.MMCEF += self.SHELLS_WEIGHT[0] * account.max_shells[0] + self.SHELLS_WEIGHT[1] * account.max_shells[1] + \
                      self.SHELLS_WEIGHT[2] * account.max_shells[2] + self.SHELLS_WEIGHT[3] * account.max_shells[3]
        self.MMCEF += self.UPGRADE_WEIGHTS[0] * account.upgrade_limit + self.UPGRADE_WEIGHTS[1] * account.upgrade_limit + \
                      self.UPGRADE_WEIGHTS[2] * account.upgrade_limit + self.UPGRADE_WEIGHTS[3] * account.upgrade_limit
        self.MMCEF += self.SPECIALIZATION_WEIGHT * account.upgrade_limit
        self.MMCEF = self.MMCEF / 30 #get MMCEF so that any rating can be divided by it to bring all ratings closer to X, where X is the value after the division sign in this assignment expression.
        # - This value MUST be larger than a single rating value (e.g. the rating of owning 1 disk shell).
        #   - If a match gets past this imbalance, bots get created to help out a bit.
        self.IMBALANCE_LIMIT = 1.35 / self.MMCEF
        
        # - Battle constants -
        self.EXPLOSION_TIMER = 1.0 #seconds; how long between each explosion when game over occurs?
        self.WORDS_QTY = 15 #how many words to spawn in each self.EXPLOSION_TIMER interval?
        # - How long does the server's compute thread of a battle last AFTER game over has occurred? -
        self.BATTLE_TIMER = 30.0 #seconds

        # - Offline Play Constants -
        self.CASH_MULTIPLIER = 1000.0 #this value influences the amount of cash/EXP each player can have and the precision with which the leader can select everyone's cash/EXP amount
        self.MAX_OFFLINE_CASH = 50 #int value; this * self.CASH_MULTIPLIER = the amount of cash each player starts with in offline mode
        self.MAX_OFFLINE_EXP = 50 #int value; this * self.CASH_MULTIPLIER = the amount of experience each player starts with in offline mode
        self.MAX_OFFLINE_PLAYERS = 25 #int value; this controls the maximum number of players we can have in an offline battle
        self.MAX_OFFLINE_BOTS = 25 #int value; this controls the *approximate* maximum number of players we can have in an offline battle

        # - Autostart -
        if(autostart):
            # - Display stuff / game graphics stuff -
            self.screen = pygame.display.set_mode([320,240], self.PYGAME_FLAGS)

            # - Start the login script -
            self.login(IP,PORT)

    def login(self,IP=None,PORT=None):
        login_menu = menu.Menuhandler()
        login_menu.create_menu(["login","create account","play offline","exit"],[["",""],["",""],["",""],["",""]],[],[],"Tank Battalion Online Login")

        # - Key configuration -
        directions = [10,11,12,13]
        shoot = 14

        clock = pygame.time.Clock()

        cursorpos = [0,0]

        # - Set the window caption -
        pygame.display.set_caption("Tank Battalion Online Login")

        # - We may not shoot that fast (clicking) -
        shoot_cooldown = time.time()

        # - Wait until the player clicks da button -
        running = True
        login = True
        while running:
            keys = self.controls.get_input()
            event_pack = controller.get_keys()
            running = not event_pack[0]
            if(running == False): #we CLICKED the X?
                login = None #we're not logging in OR signing in!
            if(event_pack[1] != None): #we requested a window resize?
                resize_dimensions = list(event_pack[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)

            # - Move cursor based on keypresses (WASD+E) -
            for x in keys:
                if(x in directions):
                     cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * login_menu.menu_scale
                     cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * login_menu.menu_scale

            # - Check for mouse movement or mouse click -
            for x in event_pack[2]:
                if(x.type == pygame.MOUSEMOTION):
                    cursorpos[0] = x.pos[0]
                    cursorpos[1] = x.pos[1]
                elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                    keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                elif(x.type == pygame.MOUSEBUTTONUP):
                    if(shoot in keys):
                        keys.remove(shoot)
                
            if(shoot in keys and time.time() - shoot_cooldown > 0.35): #click?
                shoot_cooldown = time.time() #reset our shooting cooldown
                self.sfx.play_sound(self.GUNSHOT, [0,0],[0,0]) #play the gunshot sound effect
                clicked_button = login_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                if(clicked_button[0][0] != None):
                    if(clicked_button[0][0] == 0): #login
                        login = True
                        running = False
                    elif(clicked_button[0][0] == 1): #create new account
                        login = False
                        running = False
                    elif(clicked_button[0][0] == 2): #play offline
                        login = "offline"
                        running = False
                    elif(clicked_button[0][0] == 3): #exit
                        login = None
                        running = False

            login_menu.update(self.screen) #update the menu scale

            # - Make sure our cursor stays onscreen -
            if(cursorpos[0] < 0): #no negative locations allowed!
                cursorpos[0] += self.screen.get_width()
            if(cursorpos[1] < 0):
                cursorpos[1] += self.screen.get_height()
            if(cursorpos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                cursorpos[0] -= self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()

            fps = clock.get_fps() #fps stuff
            clock.tick()

            self.screen.fill([0,0,0]) #draw everything
            login_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)
            # - Draw GPL notice and attribution for music -
            surf = menu.draw_message("Tank Battalion Online - Copyright 2024 Lincoln V. This program is free software. You can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY, even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. A copy of the GNU General Public License is distributed with this program in the base directory.",
                                     int(self.screen.get_width() * 0.95),14 * login_menu.menu_scale)
            self.screen.blit(surf, [int(self.screen.get_width() * 0.025), int(self.screen.get_height() / 3)])
            # - Draw crosshair -
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * login_menu.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * login_menu.menu_scale)],int(3 * login_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * login_menu.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * login_menu.menu_scale)],int(3 * login_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * login_menu.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * login_menu.menu_scale),cursorpos[1]],int(3 * login_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * login_menu.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * login_menu.menu_scale),cursorpos[1]],int(3 * login_menu.menu_scale))
            pygame.display.flip()

        controller.empty_keys()

        valid = False
        second_iter = False #This is used to tell whether we need to re-enter the port and IP when we fail to connect to the server.
        string_username = "Please enter your username" #I need this in order to give an error message if you enter IP or username/password wrong.
        string_IP = "Please enter the server IP"
        string_port = "Please enter the server port number"
        if(login == None or str(type(login)) == "<class 'str'>"): #we wanted to exit, not try log in? Or we wanted to play offline?
            valid = True #this will entirely bypass the login script
        while not valid:
            address_valid = False # - Grab the server's port and IP address from the client user -
            while not address_valid and address_valid != None:
                if(IP == None or second_iter): #It's hard to tell whether the IP is a valid one, so I just expect people to type it in right.
                    IP = menu.get_input(self.screen,string_IP)
                    string_IP = "IP Address may have been incorrect. Please re-enter the server IP"
                if(PORT == None or second_iter): #...But I can check whether someone typed in a valid port number...
                    PORT = menu.get_input(self.screen,string_port)
                    string_port = "Server port may have been incorrect. Please re-enter the server port number"
                    try:
                        PORT = int(PORT)
                    except: #we didn't give a number?
                        PORT = None #Psyche! Try again...
                if(PORT != None and IP != None): #We entered "valid" data?
                    address_valid = True
                else:
                    # - Someone probably clicked X to make the input windows return None -
                    address_valid = None
            if(address_valid != None): #we only try to log in IF someone did not X out any windows...
                # - Next we grab login data -
                login_username_input = menu.get_input(self.screen,string_username)
                string_username = "Username/Password/IP Address/Port incorrect. Please re-enter username"
                if(login_username_input == None): #player clicked X?
                    return None #finish the function; quit the application
                login_password_input = menu.get_input(self.screen,"Please enter your password")
                if(login_username_input == None or login_password_input == None): #player clicked X?
                    return None #finish the function; quit the application
                else: #...annnnd see if we can connect.
                    valid = self.connect_server(IP,PORT,login_username_input,login_password_input,login)
                second_iter = True #This is used to tell whether we need to re-enter the port and IP when we fail to connect to the server.
            else: #exit this loop...
                break
        if(str(type(login)) == "<class 'str'>"): #we wanted to play offline!!
            self.offline_play() #this function is at the BOTTOM of battle_client so that it's not in the way...

    def connect_server(self,IP,PORT,username,password,login):
        #create a connection to the server
        connection = True
        self.Cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a python Socket object for our Client/game
        try:
            self.Cs.connect((IP, int(PORT))) #try to establish a socket connection with the server
            netcode.configure_socket(self.Cs) #configure our socket settings so it's ready for netcode.py commands
        except:
            print("    [ERROR] Couldn't connect to server!")
            connection = False

        if(connection):
            #try send our username and password
            netcode.send_data(self.Cs, self.buffersize, [username, password, login])

            #Now, we wait 0.5 seconds and check whether the server closed the socket. If the server did, we got the wrong password/username.
            #If not, we probably got it right and we can continue!
            if(self.Cs._closed):
                print("Server connection failed!")
                connection = False
            else:
                #we're connected!...
                print("Connection to " + IP + " Successful!")
                self.Cs.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                connection = True
                self.lobby_frontend()
        return connection

    def lobby_client(self): #this is the backend for the lobby - netcode.
        with self.request_lock:
            self.request = [None]
        # - Set self.request_pending to ON so that players do not try to enter queue immediately (it won't work initially...) -
        self.request_pending = time.time()
        
        while self.running:
            if(self.request == [False]):
                while (self.request == [False]): #we get stuck in this loop until self.request != [False] - This way we can keep this thread running without needing to halt it...
                    time.sleep(0.2)
                # - Set the request_pending flag to true -
                self.request_pending = time.time()
                #clear the socket once we're out of our hibernation routine...
                netcode.clear_socket(self.Cs)

            with self.waiting_for_queue_lock:
                if(self.waiting_for_queue != True):
                    with self.request_lock:
                        netcode.send_data(self.Cs, self.buffersize, self.request) #we're gonna ask the server for something?
                        self.request = [None] #reset our request after we've sent it off
                else:
                    continue

            with self.response_lock: #recieve data
                self.response = netcode.recieve_data(self.Cs, self.buffersize) #did the server manage whatever we asked?

            if(self.response[3]): #make sure the other thread knows whether we're still connected
                self.lobby_connected = 0
            else:
                self.lobby_connected += 1

            for x in range(0,len(self.response[2])):
                print(self.response[2][x])

            # - This is a check to make sure the data the server sent us is valid and worth parsing (avoids crashes) -
            valid = False
            for x in self.LOBBY_PACKETS:
                valid = netcode.data_verify(self.response[0], x)
                if(valid): #if ONE of our lobby_packet types verify, then we go ahead with processing the packet. Else, we skip it.
                    break

            if(valid):
                with self.acct_lock:
                    #print(self.response[0]) #good debug info for transmission stuff
                    self.acct.enter_data(self.response[0][len(self.response[0]) - 2])

                with self.request_pending_lock: #if we are waiting for a server response, let's check and see if the server was successful.
                    if(self.request_pending != False and self.request_pending != True): #we are waiting for something (type of request_pending = "int")?
                        if(self.response[0][0] != None):
                            self.request_pending = self.response[0][0]
                        if(self.request_pending == True and str(type(self.waiting_for_queue)) == "<class 'float'>" and time.time() - self.waiting_for_queue < netcode.DEFAULT_TIMEOUT): #entering battle queue was successful?
                            self.request = [False]

                with self.special_window_lock: #update the special window IF it needs updating
                    if(self.response[0][len(self.response[0]) - 1] != None and self.response[0][len(self.response[0]) - 1] != self.special_window):
                        if(self.special_window != None):
                            for x in range(0,len(self.special_window)):
                                del(self.special_window[0])
                        else:
                            self.special_window = []
                        for x in range(0,len(self.response[0][len(self.response[0]) - 1])):
                            self.special_window.append(self.response[0][len(self.response[0]) - 1][x])
                    elif(self.response[0][len(self.response[0]) - 1] == None):
                        self.special_window = None
            else: #check if we're getting matchmaking packets. If we are, we start up the matchmaking routine by changing self.request, self.response...to make the lobby_frontend() go into queue.
                if(netcode.data_verify(self.response, self.MATCH_PACKET)):
                    self.request_pending = True #just toss us into whatever queue we were supposed to enter...

            if(self.lobby_connected > 4): #5 lost packets in a row?
                break #exit if we're not connected to the server

        self.Cs.close() #close our socket connection and delete it so the server will save our data
        del(self.Cs)

    def lobby_frontend(self, ph=None, socket=None, running=None, thread_num=None, threads_running=None): #this is the GUI for the lobby. ph is short for PygameHandler(), which is a class which is used with this game in offline mode to accomodate n-thread splitscreen.
        # - IF we're using a PygameHandler(), we need to get our screen object from it ASAP. While we do that, we'd better get our socket as well so that the netcode side of the lobby can function -
        if(ph != None):
            self.Cs = socket
            self.thread_num = thread_num
            self.screen = ph.get_surface(self.thread_num)
            self.sfx.server = True #change the SFX_Manager() so that it doesn't try to play sounds. It only queues them so that the main PygameHandler() thread can play them.

        _thread.start_new_thread(self.lobby_client,()) #start up the netcode for the lobby!!
        
        lobby_menu = menu.Menuhandler() #create a menu handler
        lobby_menu.default_display_size[0] += 275 #make the scale for menu text slightly smaller so I have more room for displaying text
        # - Create the various lobby menus -
        main_menu_setting_vectors = [[1,1],[0,6]]
        if(ph == None):
            main_menu_setting_vectors.append([2,7])
        lobby_menu.create_menu(["Battle","Store","Settings","Exit"],[["",""],["",""],["",""],["",""]],main_menu_setting_vectors,[],"Tank Battalion Online Lobby")
        lobby_menu.create_menu(["Purchase Mode","Shells","Upgrades","Specialization","Powerups","Back"],[["buy","refund"],["",""],["",""],["",""],["",""],["",""]],[[5,0],[1,2],[2,3],[3,4],[4,5]],[],"Tank Battalion Online Store")
        lobby_menu.create_menu(["^ Available","Hollow","Regular","Explosive","Disk","Back"],[["",""],["0","0"],["0","0"],["0","0"],["0","0"],["",""]],[[5,1]],[],"Tank Battalion Online Store - Shells")
        lobby_menu.create_menu(["^ Available","Gun","Loading Mechanism","Armor","Engine","Back"],[["",""],["0","0"],["0","0"],["0","0"],["0","0"],["",""]],[[5,1]],[],"Tank Battalion Online Store - Upgrades")
        lobby_menu.create_menu(["EXP Available","Current Specialization","Specialize Light","Specialize Heavy","Back"],[["",""],["0","0"],["",""],["",""],["",""]],[[4,1]],[],"Tank Battalion Online Store - Specialization")
        lobby_menu.create_menu(["^ Available","Improved Fuel +35% Speed","Fire Extinguisher -10% Speed","Dangerous Loading +50% RPM -10% HP","Explosive Tip +25%/-5% D/P, -5% RPM",
                                "Amped Gun +25% PN. -10% HP","Extra Armor +50% Armor -50% Speed","Back"],[["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],[[7,1]],[],"Tank Battalion Online Store - Powerups")
        lobby_menu.create_menu(["Back","Battle Type","Battle"],[["",""],["Unrated Battle","Experience Battle"],["",""]],[[0,0]],[],"Tank Battalion Online Battle Menu") #this line will need to be changed based on what battle modes are available.
        lobby_menu.create_menu(["Back","","Key config","Deadzone","KB/JS","Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1","Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6","Up","Left","Down","Right","Shoot","Escape Battle","Cursor Modifier","PTT Key","","GFX Quality","Music Volume","SFX Volume","Skip Back One Track","Skip Forward One Track"],[["",""],["",""],["",""],[1,9],["Keyboard","Joystick"],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],[1,30],[0,10],[0,10],["",""],["",""]],[[0,0]],[],"Tank Battalion Online Settings")

        # - Define what action clicking a specific button will perform -
        purchase_mode = "buy"
        button_actions = [
            [[None],[None],[None],[None]],
            [[None],[None],[None],[None],[None],[None]],
            [[None],["buy","shell",0],["buy","shell",1],["buy","shell",2],["buy","shell",3],[None]],
            [[None],["buy","upgrade",0],["buy","upgrade",1],["buy","upgrade",2],["buy","upgrade",3],[None]],
            [[None],[None],["buy","specialize",1],["buy","specialize",-1],[None]],
            [[None],["buy","powerup",0],["buy","powerup",1],["buy","powerup",2],["buy","powerup",3],["buy","powerup",4],["buy","powerup",5],[None]],
            [[None],[None],["battle","Battle Type"]],
            [[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None]],
            ]

        # - Create a special second menu with a menu depth of 1 (no sub menus) for special stuff like end-game results -
        special_menu = menu.Menuhandler()
        special_menu.default_display_size[0] += 150

        # - Last index of key configuration stuff -
        last_keyconfig = 22

        # - Brief desctiption of what every button does in the game -
        damage_numbers = entity.Bullet(None, "", 0, 0, [1,1,1,1,1], None)
        damage_numbers = damage_numbers.shell_specs[:]
        button_descriptions = [
            ["Enter a battle mode. Remember to purchase shells before entering battle   -","Purchase items for battle   -","Change your settings   -","Are you sure you want to leave..."],
            ["Choose whether you are planning to refund or purchase items   -","","","Please note, you can not change your tank specialization status without selling your shells first   -","",""],
            ["^ can be earned in battles. You will also be gifted maximum hollow shells every 24 hrs, which can be sold to get money   -","Hollow shell - Deals " + str(damage_numbers[0][0]) + " damage at " + str(damage_numbers[0][1]) + " penetration   -",
                 "Regular shell - Deals " + str(damage_numbers[1][0]) + " damage at " + str(damage_numbers[1][1]) + " penetration   -",
                 "Explosive shell - Deals " + str(damage_numbers[2][0]) + " damage at " + str(damage_numbers[2][1]) + " penetration   -",
                 "Disk shell - Deals " + str(damage_numbers[3][0]) + " damage at " + str(damage_numbers[3][1]) + " penetration   -",""],
            ["^ can be earned in battles. You will also be gifted maximum hollow shells every 24 hrs, which can be sold to get money   -","Increases damage multiplier and penetration multiplier   -","Increases tank firing rate   -","Increases tank armor   -","Increases tank speed   -",""],
            ["EXP can be earned by playing experience battles   -","This is the current state of your tank   -","Makes your tank faster, increases firing rate and bullet penetration, but decreases bullet damage and tank armor   -","Makes your tank slower, decreases firing rate and bullet penetration, but increases bullet damage and tank armor significantly   -",""],
            ["^ can be earned in battles. You will also be gifted maximum hollow shells every 24 hrs, which can be sold to get money   -","","Extinguishes fire in your tank   -","Increases firing rate at the expense of losing some health points   -","Marginally decreases firing rate and bullet penetration while significantly increasing bullet damage. This powerup also inflicts fire on any tank which is shot while active   -","Increases bullet penetration at the expense of losing some health points   -","This powerup behaves strangely. It multiplies the amount of armor your tank has upon activation by 1.5, and then divides the amount of armor your tank has upon deactivation by 1.5   -",""],
            ["Back to the lobby menu   -","Change the type of battle you want to enter   -","Enter the battle queue   -"],
            ["","","","","Are you going to play on a joystick or a keyboard   -","","","","","","","","","","","","","","","","","","","","Graphical Effects Quality   -","","","Do you like the music track you are listening to...","Do you like the music track you are listening to..."]
            ]
        if(ph != None): #correct some of the button descriptions for offline gameplay
            button_descriptions[0][2] = "Settings can not be changed in local multiplayer mode here   -"
            button_descriptions[0][3] = "Beware, clicking this button will make you enter battle rather than exit the game unless everyone clicks exit   -"
            button_descriptions[0][0] = "Enter battle when you are ready. Remember to purchase shells first   -"
            button_descriptions[2][0] = "Additional ^ can be earned in battles if Keep Battle Revenue is set to True   -"
            button_descriptions[3][0] = "Additional ^ can be earned in battles if Keep Battle Revenue is set to True   -"
            button_descriptions[4][0] = "Additional EXP can only be earned if you are playing Experience Battles with Keep Battle Revenue set to True   -"
            button_descriptions[5][0] = "Additional ^ can be earned in battles if Keep Battle Revenue is set to True   -"

        # - Create an HUD to display the descriptions of menu items -
        hud = HUD.HUD()
        hud.tick_speed = 6
        hud.default_display_size = [320,240]
        hud.add_HUD_element("scrolling text",[[0,220],[20,16],[[255,255,255],[100,100,100],[0,255,0]],"Demo text which is scrolling"])

        # - Reference index of the names of lobby_menu index 3 (upgrades) so that I can change their values -
        upgrade_names = ["Gun","Loading Mechanism","Armor","Engine"]
        # - Reference index of the names of lobby_menu index 2 (shells) so that I can change their values -
        shell_names = ["Hollow","Regular","Explosive","Disk"]
        # - Reference index of the names of lobby_menu index 5 (powerups) so that I can change their values -
        powerup_names = ["Improved Fuel +35% Speed","Fire Extinguisher -10% Speed","Dangerous Loading +50% RPM -10% HP","Explosive Tip +25%/-5% D/P, -5% RPM",
                        "Amped Gun +25% PN. -10% HP","Extra Armor +50% Armor -50% Speed"]
        # - Reference names for key configurations -
        key_configuration_names = [
            "Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1","Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6","Up","Left","Down","Right","Shoot","Escape Battle","Cursor Modifier","PTT Key"
            ]

        cursorpos = [0,0] #where is our cursor?

        # - Key configuration -
        directions = [10,11,12,13]
        shoot = 14

        # - This flag is to make sure that we don't get the red X the first thing we get into the lobby -
        first_entry = True

        if(ph == None):
            pygame.display.set_caption("Tank Battalion Online Lobby") #this will need to be disabled for 2/3 player modes, because otherwise this will not be stable...

        # - Timing stuff for keypress/cursor management and shooting -
        debounce = time.time()
        fps = 30

        # - Special window backup to see if we need to update special_menu -
        special_window_backup = []

        #get da fps
        clock = pygame.time.Clock()

        # - Start the MUSIC! (unless we're using a PygameHandler() -
        if(ph == None):
            if(len(self.music_files[0]) > 0):
                music_track = random.randint(0,len(self.music_files[0]) - 1) #which track do we start with...?
            music_timer = time.time() #we wait until 2.25x netcode.DEFAULT_TIMEOUT. THEN we start the music...

        while self.running:
            # - Obtain our screen surface for this frame IF we're using a PygameHandler() -
            if(ph != None):
                self.screen = ph.get_surface(self.thread_num)
            
            # - Update our menu's scale -
            lobby_menu.update(self.screen)

            # - Check if time.time() - request_pending is greater than our maximum ping allowance (2 seconds? I'm gonna reference the constant in netcode.py) -
            with self.request_pending_lock:
                if(self.request_pending != True and self.request_pending != False and time.time() - self.request_pending > netcode.DEFAULT_TIMEOUT):
                    self.request_pending = False
                     
            if(self.special_window == None): #this stuff only needs to happen if we're not currently utilizing the special menu.
                # - Update bullet damage strings -
                phrase1 = "^ can be earned in battles. You will also be gifted maximum hollow shells every 24 hrs   -"
                if(ph != None):
                    phrase1 = "Additional ^ can be earned in battles if Keep Battle Revenue is set to True   -"
                button_descriptions[2] = [phrase1,"Hollow shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[0][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[0][1])) + " penetration   -",
                     "Regular shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[1][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[1][1])) + " penetration   -",
                     "Explosive shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[2][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[2][1])) + " penetration   -",
                     "Disk shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[3][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[3][1])) + " penetration   -",""]
                
                # - If we're in the battle menu, make sure the battle command is configured properly -
                if(lobby_menu.current_menu == 6): #we're in the battle selection screen?
                    battle_settings = lobby_menu.grab_settings(["Battle Type"])
                    button_actions[6][2] = ["battle",battle_settings[0][0]]

                # - Update purchase_mode if we are in menu index 1 (the menu which can control purchase_mode) -
                if(lobby_menu.current_menu == 1):
                    settings = lobby_menu.grab_settings(["Purchase Mode"])
                    purchase_mode = settings[0][0]

                # - Update the function that button_actions performs IF we are in the menu which can control purchase_mode (menu index 1) -
                if(lobby_menu.current_menu == 1):
                    for x in range(0,len(button_actions)):
                        for y in range(0,len(button_actions[x])):
                            if(button_actions[x][y] != [None]):
                                if(button_actions[x][y][0] in ["buy","refund"]):
                                    button_actions[x][y][0] = purchase_mode

                # - Update the price and state of our tank's powerups + ^ counter -
                if(lobby_menu.current_menu == 5):
                    opt_str = str(round(self.acct.cash,2)) + "^" #update ^ counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"^ Available")
                    for x in range(0,len(self.acct.powerups)): #update powerups
                        owned = 0
                        if(self.acct.powerups[x] == True):
                            owned = 1
                        if(purchase_mode == "buy"):
                            opt_str = "Owned - " + str(owned) + "/1, " + "Cost - " + str(round(self.acct.purchase("powerup",x,True)[0],2)) + "^"
                        else:
                            opt_str = "Owned - " + str(owned) + "/1, " + "Refund amt - " + str(round(self.acct.refund("powerup",x,True)[0],2)) + "^"
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,powerup_names[x])

                # - I know that the controls, sound volume, SFX, and GFX get updated below...but they also need to be updated HERE because you don't start the client in menu #7 (this doesn't need to happen in split-screen mode tho) -
                if(self.acct.settings != [None] and ph == None):
                    # - Music volume (self.acct.settings[0]) -
                    self.music.set_volume(int(self.acct.settings[0]) / 10)
                    # - SFX volume (self.acct.settings[1]) -
                    self.sfx.sound_volume = int(self.acct.settings[1]) / 10
                    # - GFX quality (self.acct.settings[2]) -
                    GFX.gfx_quality = int(self.acct.settings[2]) / 20
                    self.WORDS_QTY = int(int(self.acct.settings[2]) / 2)
                    self.controls.enter_data(self.acct.settings[3]) #controls

                # - Update our key configuration menu (again, this doesn't need to happen in split-screen mode) -
                if(lobby_menu.current_menu == 7 and ph == None):
                    # - Load the lobby_menu with settings sent from the server, which then get transferred to all the variables they need to influence below -
                    if(self.acct.settings != [None]):
                        lobby_menu.reconfigure_setting([0,10],self.acct.settings[0],int(self.acct.settings[0]),"Music Volume")
                        lobby_menu.reconfigure_setting([0,10],self.acct.settings[1],int(self.acct.settings[1]),"SFX Volume")
                        lobby_menu.reconfigure_setting([1,30],self.acct.settings[2],int(self.acct.settings[2]),"GFX Quality")
                        self.controls.enter_data(self.acct.settings[3])
                        lobby_menu.reconfigure_setting([1,9],str(int(controller.DEADZONE * 10)),int(controller.DEADZONE * 10),"Deadzone")
                        if(self.controls.kb_ctrl == "kb"):
                            lobby_menu.reconfigure_setting(["Keyboard","Joystick"], "Keyboard", 0, "KB/JS")
                        else:
                            lobby_menu.reconfigure_setting(["Keyboard","Joystick"], "Joystick", 1, "KB/JS")
                    
                    # - Get the deadzone value for when we're playing with a joystick -
                    controller.DEADZONE = int(lobby_menu.grab_settings(["Deadzone"])[0][0]) / 10
                    # - Find out whether we're planning on using a keyboard or joystick -
                    keyboard_joystick = lobby_menu.grab_settings(["KB/JS"])[0][0] #get the string format
                    if(keyboard_joystick == "Joystick"):
                        success = self.controls.joystick_request(js_num=0) #we ALWAYS use JS 0 for this game since it is only 1-player
                        if(not success): #if we can't switch to joystick, make sure it doesn't let us.
                            lobby_menu.reconfigure_setting(["Keyboard","Joystick"],"Keyboard",0,"KB/JS")
                    else:
                        self.controls.kb_ctrl = "kb"
                    # - Update what the menu shows we have configured our keys as -
                    if(self.controls.kb_ctrl == "kb"): #this works for keyboards only
                        for x in range(0,len(self.controls.buttons)):
                            opt_str = "."
                            for b in range(0,len(menu.keys)):
                                if(menu.keys[b][0] == self.controls.buttons[x]):
                                    opt_str = menu.keys[b][1]
                                    break
                            lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,key_configuration_names[x])
                    else: #this works for joysticks only
                        for x in range(0,len(self.controls.buttons)):
                            opt_str = "Button " + str(self.controls.buttons[x])
                            lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,key_configuration_names[x])
                    GFX.gfx_quality = int(lobby_menu.grab_settings(["GFX Quality"])[0][0]) / 20
                    self.WORDS_QTY = int(int(lobby_menu.grab_settings(["GFX Quality"])[0][0]) / 2)
                    self.music.set_volume(int(lobby_menu.grab_settings(["Music Volume"])[0][0]) / 10)
                    self.sfx.sound_volume = int(lobby_menu.grab_settings(["SFX Volume"])[0][0]) / 10

                # - Update the value of specialization in menu 4, index 0 + EXP counter -
                if(lobby_menu.current_menu == 4):
                    opt_str = str(round(self.acct.experience,2)) + " EXP" #EXP counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"EXP Available")
                    opt_str = self.specialization_mapper[self.acct.specialization + self.specialization_offset] #specialization settings
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Current Specialization")
                    # - Update the costs for specializing heavy/light -
                    light = str(round(self.acct.purchase("specialize",1,True)[0],2)) + " EXP"
                    heavy = str(round(self.acct.purchase("specialize",-1,True)[0],2)) + " EXP"
                    lobby_menu.reconfigure_setting([light,light],light,0,"Specialize Light")
                    lobby_menu.reconfigure_setting([heavy,heavy],heavy,0,"Specialize Heavy")

                # - Update the value of tank upgrades + ^ counter -
                if(lobby_menu.current_menu == 3):
                    opt_str = str(round(self.acct.cash,2)) + " ^" #configure the cash counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"^ Available")
                    for x in range(0,len(self.acct.upgrades)): #configure the upgrades counter
                        if(purchase_mode == "buy"):
                            opt_str = "Owned - " + str(self.acct.upgrades[x]) + "/" + str(account.upgrade_limit) + ", " + self.acct.purchase("upgrade",x,True)[1] + ", Cost - " + str(round(self.acct.purchase("upgrade",x,True)[0],2)) + "^"
                        else:
                            opt_str = "Owned - " + str(self.acct.upgrades[x]) + "/" + str(account.upgrade_limit) + ", " + self.acct.refund("upgrade",x,True)[1] + ", Refund amt - " + str(round(self.acct.refund("upgrade",x,True)[0],2)) + "^"
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,upgrade_names[x])

                # - Update the value of shells + ^ counter -
                if(lobby_menu.current_menu == 2):
                    opt_str = str(round(self.acct.cash,2)) + " ^" #configure the cash counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"^ Available")
                    for x in range(0,len(self.acct.shells)): #configure the shells counter
                        if(purchase_mode == "buy"):
                            opt_str = "Owned - " + str(self.acct.shells[x]) + "/" + str(account.max_shells[x]) + ", " + self.acct.purchase("shell",x,True)[1] + ", Cost - " + str(round(self.acct.purchase("shell",x,True)[0],2)) + "^"
                        else:
                            opt_str = "Owned - " + str(self.acct.shells[x]) + "/" + str(account.max_shells[x]) + ", " + self.acct.refund("shell",x,True)[1] + ", Refund amt - " + str(round(self.acct.refund("shell",x,True)[0],2)) + "^"
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,shell_names[x])
            else: #we need to configure our special window/menu...which is always just a set of strings, with no settings you can change lol
                if(self.special_window != special_window_backup):
                    special_window_backup = self.special_window[:]
                    with self.special_window_lock:
                        special_menu = menu.Menuhandler() #wipe out the old special_menu instance, and create a new one which has no menus created
                        special_menu.default_display_size[0] += 150
                        options_settings = []
                        for x in range(0,len(self.special_window) - 1):
                            options_settings.append(["",""])
                        special_menu.create_menu(self.special_window[:len(self.special_window) - 1],options_settings,[],[],self.special_window[len(self.special_window) - 1])
                special_menu.update(self.screen)

            # - Update our Music() manager, and check if we need to queue more tracks (this MAY NOT happen in split-screen mode, since this thread would hang then) -
            if(ph == None):
                if(time.time() - music_timer > netcode.DEFAULT_TIMEOUT * 2.25 and len(self.music_files[0]) > 0): #wait until we hear from the server whether we want music on or not before starting it.
                    queue = not self.music.clock() #returns False if we need to queue more tracks
                    if(queue): #queue a new random track
                        music_track += 1
                        if(music_track > len(self.music_files[0]) - 1):
                            music_track = 0
                        self.music.queue_track(self.music_files[0][music_track])

            # - Make sure our cursor stays onscreen -
            if(cursorpos[0] < 0): #no negative locations allowed!
                cursorpos[0] += self.screen.get_width()
            if(cursorpos[1] < 0):
                cursorpos[1] += self.screen.get_height()
            if(cursorpos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                cursorpos[0] -= self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()

            # - Check if we have clicked any buttons -
            if(ph == None): #There are two ways of getting input: The first is WITHOUT the PygameHandler(), which we will be using for single-player online play. The second is WITH the PygameHandler(), which is for split-screen play only.
                event_pack = controller.get_keys()
                with self.running_lock:
                    self.running = not event_pack[0]
                if(event_pack[1] != None): #we requested a window resize?
                    resize_dimensions = list(event_pack[1])
                    if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                        resize_dimensions[0] = self.min_screen_size[0]
                    if(resize_dimensions[1] < self.min_screen_size[1]):
                        resize_dimensions[1] = self.min_screen_size[1]
                    self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)
                keys = self.controls.get_input()
                # - Check if we need to engage our backup controller -
                if(self.controls.kb_ctrl == "ctrl"): #we're using a joystick? We may need to help out the player a bit so that he can still use the lobby while configuring his controller.
                    backup_keys = self.controls_backup.get_input()
                    for x in backup_keys:
                        keys.append(x)
            else: #We're using the PygameHandler() to get input
                keys = ph.get_input(thread_num)
                with self.running_lock:
                    self.running = running[0]
            
            # - Move the cursor based on the keys we've pressed -
            for x in directions:
                if(x in keys):
                    cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * lobby_menu.menu_scale
                    cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * lobby_menu.menu_scale

            # - Check if the mouse moved @ all, or if the player clicked -
            if(ph == None):
                for x in event_pack[2]: #check for mouse movement or mouse click
                    if(x.type == pygame.MOUSEMOTION):
                        cursorpos[0] = x.pos[0]
                        cursorpos[1] = x.pos[1]
                    elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                        keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                    elif(x.type == pygame.MOUSEBUTTONUP):
                        if(shoot in keys):
                            keys.remove(shoot)

            if(shoot in keys and time.time() - debounce > 0.2 and str(type(self.request_pending)) != "<class 'float'>"): #shoot? And we're not still connecting to server?
                debounce = time.time()
                self.sfx.play_sound(self.GUNSHOT, [0,0],[0,0]) #play the gunshot sound effect
                if(self.special_window == None):
                    clicked_button = lobby_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height() - font.SIZE * 3 * lobby_menu.menu_scale],cursorpos)
                    if(clicked_button[0][0] != None):
                        with self.request_lock: #I know there's a bit of a duplicate statement down below for settings storage, but this handles everything ELSE...buy, sell, enter battle...
                            self.request = button_actions[clicked_button[1]][clicked_button[0][0]]
                        with self.request_pending_lock:
                            if(self.request != [None]):
                                self.request_pending = time.time()
                        # - Check if the button we pressed was in menu # 7 (key config). This check is bypassed if we are using a PygameHandler(), since our controls *should* have been already configured -
                        if(ph == None and lobby_menu.current_menu == 7 and clicked_button[1] == 7 and clicked_button[0][0] - 5 >= 0 and clicked_button[0][0] <= last_keyconfig): #we didn't change into this menu?? We were already here when we clicked?
                            config = True
                            pygame.display.set_caption("Configure key number " + str(clicked_button[0][0] - 4))
                            pygame.time.delay(250) #delay 250ms to ensure that we don't configure our shoot button as whatever this button is going to be
                            controller.get_keys() #empty the event queue
                            controller.empty_keys() #empty the key list
                            while config: #wait until the client configures the key
                                config = not controller.get_keys()[0]
                                if(config):
                                    config = not self.controls.configure_key(clicked_button[0][0] - 5) #did we get a successful configuration?
                                # - Draw the "press a key to configure the button" words onscreen
                                self.screen.fill([0,0,0])
                                word_scale = (self.screen.get_width() / (len("Press any key...") * font.SIZE))
                                font.draw_words("Press any key...", [(self.screen.get_width() / 2 - len("Press any key...") * font.SIZE * word_scale * 0.5),10], [0,0,255], word_scale, self.screen)
                                pygame.display.flip()
                            pygame.time.delay(250) #250ms
                            controller.get_keys() #empty the event queue
                            controller.empty_keys() #empty the key list, and delay a small amount...
                        # - Check if the player requested using a joystick. If the player did, we need to get that handled BEFORE our controller data is sent to the server in the self.settings[] list -
                        if(ph == None and lobby_menu.current_menu == 7 and clicked_button[0][0] == 4):
                            # - Find out whether we're planning on using a keyboard or joystick -
                            keyboard_joystick = lobby_menu.grab_settings(["KB/JS"])[0][0] #get the string format
                            if(keyboard_joystick == "Joystick"):
                                success = self.controls.joystick_request(js_num=0) #we ALWAYS use JS 0 for this game since it is only 1-player
                                if(not success): #if we can't switch to joystick, make sure it doesn't let us.
                                    lobby_menu.reconfigure_setting(["Keyboard","Joystick"],"Keyboard",0,"KB/JS")
                            else:
                                self.controls.kb_ctrl = "kb"
                        # - Check if the player requested a different music track (music is not handled by the client thread in split-screen mode, so these buttons do not respond in this mode) -
                        if(ph == None and lobby_menu.current_menu == 7 and clicked_button[1] == 7):
                            if(clicked_button[0][0] == 27 and len(self.music_files[0]) > 0): #skip back a track
                                music_track -= 1
                                if(music_track < 0):
                                    music_track = len(self.music_files[0]) - 1
                                self.music.transition_track(self.music_files[0][music_track])
                            if(clicked_button[0][0] == 28 and len(self.music_files[0]) > 0): #skip forward a track
                                music_track += 1
                                if(music_track > len(self.music_files[0]) - 1):
                                    music_track = 0
                                self.music.transition_track(self.music_files[0][music_track])
                        # - Check if the player clicked Exit -
                        if(lobby_menu.current_menu == 0 and clicked_button[1] == 0 and clicked_button[0][0] == 3): #time to go?
                            with self.running_lock:
                                self.running = False
                        # - Check if the player clicked battle & we're using split-screen mode; This will result in this client script ending so that the main thread can start a match with our account data -
                        if(clicked_button[1] == 0 and clicked_button[0][0] == 0 and ph != None):
                            threads_running[thread_num] = None #False = exit game; True = still in menu; None = battle?
                            break #exit this thread
                        # - Send our settings to the server so they are saved between play sessions (this is not needed in split-screen mode since settings are not saved on a "server") -
                        if(ph == None and lobby_menu.current_menu == 7 and clicked_button[1] == 7): #we need to be IN the settings menu before a click makes a settings save worthwhile.
                            # - We save some of our settings to a list * only if* we've changed any settings...this way, the server can save them for us -
                            self.settings_data = []
                            #order: [music volume, SFX volume, GFX quality, control data]
                            self.settings_data.append(lobby_menu.grab_settings(["Music Volume"])[0][0])
                            self.settings_data.append(lobby_menu.grab_settings(["SFX Volume"])[0][0])
                            self.settings_data.append(lobby_menu.grab_settings(["GFX Quality"])[0][0])
                            # - Get our most up-to-date DEADZONE value from the menu since if we don't save it here, the server will overwrite it next time it sends us our saved settings -
                            controller.DEADZONE = int(lobby_menu.grab_settings(["Deadzone"])[0][0]) / 10
                            self.settings_data.append(self.controls.return_data()) #we also save our control scheme
                            # - Now we request to have that data saved -
                            with self.request_lock:
                                #the number in the middle of this list MUST be there for the server to accept this packet; it is there to distinguish this packet type from an ingame packet.
                                self.request = ["settings",1,self.settings_data[:]]
                            with self.request_pending_lock:
                                if(self.request != [None]):
                                    self.request_pending = time.time()
                        
                else: #if the first button is clicked in the special window, we need to exit the special window by sending an exit packet to the server.
                    clicked_button = special_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height() - font.SIZE * 3 * lobby_menu.menu_scale],cursorpos)
                    if(clicked_button[0][0] == 0): #button 0 was clicked? Send a signal to the _netcode thread to exit this dumb window.
                        with self.request_lock:
                            self.request = ["sw_close",""] #the empty string here is to get the server to receive this packet, as [<str>,<str>] is a valid lobby data packet format for the server.

            if(self.request[0] == "battle"): #part of making sure the server acknowledges we're in the player queue...
                with self.waiting_for_queue_lock:
                    self.waiting_for_queue = time.time()

            if(str(type(self.waiting_for_queue)) == "<class 'float'>" and time.time() - self.waiting_for_queue < netcode.DEFAULT_TIMEOUT and self.request_pending == True): #make sure the server acknowledges that we're in the player queue
                with self.request_lock:
                    self.request = [False]
                with self.waiting_for_queue_lock:
                    self.waiting_for_queue = True
                self.battle_queue(battle_settings[0][0])
                if(ph == None): #this can only happen if we're in single player mode. I haven't implemented an equivalent function in the PygameHandler() class for threads to utilize.
                    controller.empty_keys()
                self.waiting_for_queue = False
                with self.request_lock:
                    self.request[0] = None #clear the halt on the packets thread for the lobby client.
                first_entry = True #this is so we don't get the red X when we leave the battle queue/leave a battle.
                if(ph == None and len(self.music_files[0]) > 0): #NO music in multi-player mode!
                    self.music.transition_track(self.music_files[0][random.randint(0,len(self.music_files[0]) - 1)]) #start the music up again...
            elif(str(type(self.waiting_for_queue)) == "<class 'float'>" and time.time() - self.waiting_for_queue < netcode.DEFAULT_TIMEOUT and self.request_pending == False): #We didn't make it?
                with self.request_lock:
                    self.request[0] = None
                with self.waiting_for_queue_lock:
                    self.waiting_for_queue = False

            # - Reconfigure the HUD -
            if(self.special_window == None):
                hovered_button = lobby_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height() - font.SIZE * 3 * lobby_menu.menu_scale],cursorpos,None,False)
                if(hovered_button[0][0] != None):
                    hud.update_HUD_element_value(0,button_descriptions[lobby_menu.current_menu][hovered_button[0][0]])
                else: #here we should display our tank's current stats.
                    dummy_tank = self.acct.create_tank("img", "team_name",[0,0,0,0],True)
                    armor = round(dummy_tank.armor,2)
                    speed = round(dummy_tank.speed,2)
                    damage = round(dummy_tank.damage_multiplier,2)
                    penetration = round(dummy_tank.penetration_multiplier,2)
                    RPM = round(dummy_tank.RPM,2)
                    hud.update_HUD_element_value(0,"Tank stats - " + str(armor) + " Armor, " + str(speed) + " Speed, " + str(damage) + " Damage multiplier, " + str(penetration) + " Penetration multiplier, " + str(RPM) + " RPM   -")

            # - Make sure that our crosshair does not become a red X when we enter the lobby -
            if(first_entry == True and self.request_pending == False):
                self.request_pending = True
                first_entry = False

            # - Update our SFX_Manager() -
            if(ph != None): #we need to send our SFX data to the PygameHandler() for it to be played.
                ph.add_sounds(thread_num, self.sfx.return_data())
            self.sfx.clock([0,0])
                
            #draw everything
            if(ph != None): #wait until the PygameHandler() has drawn our previous frame so that we don't end up with a half-drawn frame onscreen
                while not ph.surface_flipped(thread_num):
                    pass
            self.screen.fill([0,0,0]) #draw our menu stuff onscreen
            if(self.special_window == None):
                if(self.request_pending != True and self.request_pending != False): #draw the menu, but do not highlight options since we are awaiting a response from the server.
                    lobby_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height() - font.SIZE * 3 * lobby_menu.menu_scale],self.screen,[0,0])
                else: #draw the menu as normal
                    lobby_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height() - font.SIZE * 3 * lobby_menu.menu_scale],self.screen,cursorpos)
            else: #draw special_menu
                try:
                    with self.special_window_lock:
                        special_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height() - font.SIZE * 3 * lobby_menu.menu_scale],self.screen,cursorpos)
                except Exception as e: #we got an error from some sort of threading issue?
                    print("An exception occurred during special_menu.draw_menu: " + str(e) + " - Nonfatal")
            #draw our cursor onscreen (it's a crosshair LOL...I should add a gunshot effect for when you click on the screen...)
            # - Change: Crosshair is only when a request is not pending...and is ALWAYS a crosshair when in special_menu.
            if(self.request_pending == True):
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * lobby_menu.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * lobby_menu.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * lobby_menu.menu_scale),cursorpos[1]],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * lobby_menu.menu_scale),cursorpos[1]],int(3 * lobby_menu.menu_scale))
            elif(str(type(self.request_pending)) == "<class 'float'>"): #make the words "loading..." follow your mouse pointer around lol.
                font.draw_words("Loading...", [cursorpos[0] - font.SIZE * lobby_menu.menu_scale * len("Loading...") / 2, cursorpos[1] - font.SIZE * lobby_menu.menu_scale / 2.0], [255,255,255], lobby_menu.menu_scale, self.screen)
            elif(self.request_pending == False): #draw an X instead of a + crosshair.
                pygame.draw.line(self.screen,[255,0,0],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1] - int(8 * lobby_menu.menu_scale)],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1] + int(8 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,0,0],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1] + int(8 * lobby_menu.menu_scale)],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1] - int(8 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
            #draw the HUD
            hud.draw_HUD(self.screen)
            #update the display: There are different ways needed depending on whether a PygameHandler() is being used.
            if(ph == None):
                pygame.display.flip() #update the display
            else:
                ph.surface_flip(thread_num)

            if(self.lobby_connected > 4): #5 lost packets in a row?
                break #exit if we're not connected to the server

            #get da FPS
            clock.tick(900)
            fps = clock.get_fps()
            if(ph == None): #NO caption setting if there's multiple client threads running @ once!
                pygame.display.set_caption("Tank Battalion Online Lobby - FPS: " + str(int(fps)))

        if(self.lobby_connected > 4 and ph == None): #Did we disconnect/get kicked from the server? (this menu doesn't need to be here in offline mode)
            # - Reconfigure lobby_menu -
            lobby_menu = menu.Menuhandler()
            lobby_menu.create_menu(["Exit"],[["",""]],[],[],"Disconnected")
            running = True
            font_size = 10
            cursorpos = [0,0]
            while running:
                # - Check if we have clicked any buttons -
                event_pack = controller.get_keys()
                running = not event_pack[0]
                if(event_pack[1] != None): #we requested a window resize?
                    resize_dimensions = list(event_pack[1])
                    if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                        resize_dimensions[0] = self.min_screen_size[0]
                    if(resize_dimensions[1] < self.min_screen_size[1]):
                        resize_dimensions[1] = self.min_screen_size[1]
                    self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)
                keys = self.controls.get_input()
                for x in directions:
                    if(x in keys):
                        cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * lobby_menu.menu_scale
                        cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * lobby_menu.menu_scale

                # - Check for mouse movement or mouse click -
                for x in event_pack[2]:
                    if(x.type == pygame.MOUSEMOTION):
                        cursorpos[0] = x.pos[0]
                        cursorpos[1] = x.pos[1]
                    elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                        keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                    elif(x.type == pygame.MOUSEBUTTONUP):
                        if(shoot in keys):
                            keys.remove(shoot)

                # - Check if we clicked exit -
                if(shoot in keys): #shoot?
                    if(self.special_window == None):
                        clicked_button = lobby_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                        if(clicked_button[0][0] != None):
                            # - We clicked exit! Time to leave... -
                            running = False

                # - Update the menu -
                lobby_menu.update(self.screen)

                # - Grab the message we are trying to blit onto the screen -
                message = menu.draw_message("An error occurred. Most likely, you entered bad account credentials, tried to log into an account which is currently logged in, or tried to create an account with a name which either starts with bot or has already been used. However, there is a chance that the server is down, in which case please try again in a few minutes.",int(self.screen.get_width() * 0.95),font_size)
                if(message.get_height() > self.screen.get_height() - lobby_menu.menu_scale * font.SIZE * 3):
                    font_size -= 1
                    message = pygame.transform.scale(message,[message.get_width(), self.screen.get_height() - lobby_menu.menu_scale * font.SIZE * 3])
                elif(message.get_height() < self.screen.get_height() - lobby_menu.menu_scale * font.SIZE * 14):
                    font_size += 1

                # - Draw everything onscreen -
                self.screen.fill([0,0,0]) #fill the screen black
                # - Draw the menu onscreen -
                lobby_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)
                # - Draw the error message onscreen -
                self.screen.blit(message,[int(self.screen.get_width() / 2 - message.get_width() / 2),font.SIZE * lobby_menu.menu_scale * 3])
                # - Draw the cursor onscreen -
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * lobby_menu.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * lobby_menu.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * lobby_menu.menu_scale),cursorpos[1]],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * lobby_menu.menu_scale),cursorpos[1]],int(3 * lobby_menu.menu_scale))
                # - Update the display -
                pygame.display.flip() #update the display

                # - Make sure our cursor stays onscreen -
                if(cursorpos[0] < 0): #no negative locations allowed!
                    cursorpos[0] += self.screen.get_width()
                if(cursorpos[1] < 0):
                    cursorpos[1] += self.screen.get_height()
                if(cursorpos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                    cursorpos[0] -= self.screen.get_width()
                if(cursorpos[1] > self.screen.get_height()):
                    cursorpos[1] -= self.screen.get_height()

                # - Manage FPS -
                clock.tick(900)
                fps = clock.get_fps()
                pygame.display.set_caption("Disconnnected! FPS: " + str(int(fps)))

        if(ph == None): #pygame does NOT need to be quit if we're using a PygameHandler().
            pygame.quit() #quit pygame when we're out of here...
        else:
            self.screen = ph.get_surface(self.thread_num)
            self.screen.fill([0,0,0])
            ph.surface_flip(thread_num)
            if(threads_running[thread_num] != None):
                threads_running[thread_num] = False #let the main thread know we've exited the game.

    def battle_queue(self, battle_queue_str): #this handles the socket connection + the pygame stuff in the same thread. Lowers the FPS while in queue, but that's OK.
        #create a menu object for player queue stuff
        queue_menu = menu.Menuhandler()
        queue_menu.create_menu(["Back to Lobby","Up","Player 1","Player 2","Player 3","Player 4","Player 5","Down","","Skip Back One Track","Skip Forward One Track"],
                               [["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],
                               [[2,1],[3,1],[4,1],[5,1],[6,1]],[],"TBO " + battle_queue_str + " Matchmaking Queue")
        queue_menu.create_menu(["Name","",
                                "Shells", "Hollow","Regular","Explosive","Disk","",
                                "Powerups","Improved Fuel","Fire Extinguisher","Dangerous Loading","Explosive Tip","Amped Gun","Extra Armor","",
                                "Upgrades","Gun","Loading Mechanism","Armor","Engine","",
                                "Specialization","",
                                "Back to Queue"],
                               [["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],
                               [[24,0]],[],"TBO " + battle_queue_str + " Player Data")

        # - Helpful constant lists which make updating the Player Data menu easier -
        shell_names = ["Hollow","Regular","Explosive","Disk"]
        powerup_names = ["Improved Fuel","Fire Extinguisher","Dangerous Loading","Explosive Tip","Amped Gun","Extra Armor"]
        upgrade_names = ["Gun","Loading Mechanism","Armor","Engine"]

        # - Because we handle packets and display stuff in the same thread, I need to let this loop run a certain amount of time before waiting for a packet.
        #   - If I do not, I will get between 2 and 6 FPS due to the server's packet delay.
        PACKET_TIME = 0.25 #Change this value like this: PACKET_TIME = current_ping * 0.25 + PACKET_TIME * 0.75
        last_packet = time.time()
        send_packet = True

        # - Constant; Tells how many players we can view at once -
        VIEW_CT = 5

        # - Records which player's data we are currently interested in viewing -
        selected_player = 0

        #where is our cursor onscreen?
        cursorpos = [0,0]

        #what does da fps be?
        clock = pygame.time.Clock()

        # - Keeps track of what index of players we're looking at in player_queue (server side) -
        player_view_index = 0

        # - How many players are in queue? -
        total_players = 1 #we know that we are at least in queue...

        # - List of players we are currently viewing: Basically a list of data from account.Account().return_data() -
        viewing_players = []
        for x in range(0,VIEW_CT):
            viewing_players.append(account.Account().return_data())

        # - This flag is for if we wanted to exit the match queue -
        exit_queue = False

        # - FPS counter -
        fps = 30

        # - Key configuration -
        directions = [10,11,12,13]
        shoot = 14

        # - Shooting debouncing -
        shoot_timeout = time.time()

        # - Start the music! -
        if(len(self.music_files[1]) > 0):
            music_track = random.randint(0,len(self.music_files[1]) - 1)
            self.music.transition_track(self.music_files[1][music_track]) #start the music up again...

        #...queueing is taking a long time, eh?
        queueing = True
        while queueing and self.running:
            if(send_packet): #only if the server is waiting for a packet...
                # - Handle socket packet exchanges (we send first) -
                if(not exit_queue):
                    netcode.send_data(self.Cs, self.buffersize, [VIEW_CT,player_view_index]) #Send format: [VIEW_CT, player_view_index] OR [False] to leave matchmaker
                else: #we want to exit the battle queue?? We need to send an exit message and hope that the server recognizes it after we've left...
                    netcode.send_data(self.Cs, self.buffersize, [False])
                    queueing = False
                # - Clear the send_packet flag -
                send_packet = False

            if(time.time() - last_packet >= PACKET_TIME): #time to recieve a packet?
                data_pack = netcode.recieve_data(self.Cs, self.buffersize)
                data = data_pack[0] #Format: [in_battle(True/False), viewing_players data list, player_count]

                # - Update our PACKET_TIME "constant" (really not a constant at all) -
                seconds_ping = ((data_pack[1] / 1000) + PACKET_TIME) * 0.85 #make sure our ping is always a little lower than it should be to reduce frame decreses too much
                PACKET_TIME = 0.75 * PACKET_TIME + seconds_ping * 0.25

                # - Check if the data is worth grabbing -
                if(netcode.data_verify(data, self.MATCH_PACKET)):
                    # - Update our viewing_players list -
                    queueing = data[0]
                    viewing_players = data[1]
                    total_players = data[2]
                else: #are we supposed to be IN a match??
                    for x in range(0,len(self.GAME_PACKETS)):
                        verify = netcode.data_verify(data, self.GAME_PACKETS[x])
                        if(verify == True): #We only need ONE of the GAME_PACKETS data formats to qualify this packet as a GAME_PACKET.
                            break
                    if(verify):
                        queueing = False #we move onto getting INTO our match then...hopefully the setup sequences work properly =)

                # - Make sure we respond with a packet -
                send_packet = True

                # - Set our last_packet timer -
                last_packet = time.time()

            # - Update our Music() manager, and check if we need to queue more tracks -
            queue = not self.music.clock() #returns False if we need to queue more tracks
            if(queue and len(self.music_files[1]) > 0): #queue a new random track
                music_track += 1
                if(music_track >= len(self.music_files[1])):
                    music_track = 0
                self.music.queue_track(self.music_files[1][music_track])

            # - Make sure our cursor stays onscreen -
            if(cursorpos[0] < 0): #no negative locations allowed!
                cursorpos[0] += self.screen.get_width()
            if(cursorpos[1] < 0):
                cursorpos[1] += self.screen.get_height()
            if(cursorpos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                cursorpos[0] -= self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()
            
            # - Check if we have clicked any buttons -
            event_pack = controller.get_keys()
            with self.running_lock:
                self.running = not event_pack[0]
            if(event_pack[1] != None): #we requested a window resize?
                resize_dimensions = list(event_pack[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)
            keys = self.controls.get_input()
            for x in directions:
                if(x in keys):
                    cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * queue_menu.menu_scale
                    cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * queue_menu.menu_scale

            # - Check for mouse motion or mouse click -
            for x in event_pack[2]:
                if(x.type == pygame.MOUSEMOTION):
                    cursorpos[0] = x.pos[0]
                    cursorpos[1] = x.pos[1]
                elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                    keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                elif(x.type == pygame.MOUSEBUTTONUP):
                    if(shoot in keys):
                        keys.remove(shoot)

            if(shoot in keys and str(type(self.request_pending)) == "<class 'bool'>" and time.time() - shoot_timeout > 0.20): #we shot?
                shoot_timeout = time.time()
                self.sfx.play_sound(self.GUNSHOT, [0,0],[0,0]) #play the gunshot sound effect
                clicked_button = queue_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                if(clicked_button[0][0] != None): #a button was clicked?
                    if(queue_menu.current_menu == 0):
                        if(clicked_button[0][0] == 1): #view players farther up
                            if(player_view_index > 0):
                                player_view_index -= 1
                        elif(clicked_button[0][0] == 7): #view players farther down
                            player_view_index += 1
                        elif(clicked_button[0][0] == 0): #return to lobby??
                            exit_queue = True
                        elif(clicked_button[0][0] == 9 and len(self.music_files[1]) > 0): #skip 1 track backward?
                            music_track -= 1
                            if(music_track < 0):
                                music_track = len(self.music_files[1]) - 1
                            self.music.transition_track(self.music_files[1][music_track])
                        elif(clicked_button[0][0] == 10 and len(self.music_files[1]) > 0): #skip 1 track forward?
                            music_track += 1
                            if(music_track >= len(self.music_files[1])):
                                music_track = 0
                            self.music.transition_track(self.music_files[1][music_track])
                    elif(queue_menu.current_menu == 1): #we're in the Player Data menu? We need to check which player we clicked on to get to this menu.
                        if(clicked_button[0][0] > 1 and clicked_button[0][0] < 7 and clicked_button[1] == 0): #we clicked on a player to view its data?
                            selected_player = clicked_button[0][0] - 2 #record which player we wanted to view.

            # - Update "Up" and "Down" settings so that we know which range of players we're looking at -
            if(queue_menu.current_menu == 0):
                opt_str = str(player_view_index + 1) + "/" + str(total_players)
                queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Up")
                opt_str = str(player_view_index + 5) + "/" + str(total_players)
                queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Down")

                # - Update "Player X" settings so that we know what players are in queue -
                for x in range(0,VIEW_CT):
                    if(x < len(viewing_players)):
                        tmp_acct = account.Account()
                        tmp_acct.enter_data(viewing_players[x])
                        #this long incomprehensible argument (last parameter up ahead) tells the ratings manager whether we want to include experience as part of a player's rating.
                        rating = self.return_rating(tmp_acct, self.rated_battles[self.battle_types.index(battle_queue_str)])
                        opt_str = tmp_acct.name + " Rating: " + str(round(rating,2))
                    else:
                        opt_str = ""
                    queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Player " + str(x + 1))
            # - Update the Player Data menu so that we get the stats of the player we're looking at -
            elif(queue_menu.current_menu == 1):
                if(selected_player < len(viewing_players)): #Do we have player data from the server to fill the menu with?
                    tmp_acct = account.Account()
                    tmp_acct.enter_data(viewing_players[selected_player])
                    #Name
                    opt_str = tmp_acct.name
                    queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Name")
                    #Shells
                    for x in range(0,len(shell_names)):
                        opt_str = str(tmp_acct.shells[x]) + "/" + str(account.max_shells[x])
                        queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,shell_names[x])
                    #Powerups
                    for x in range(0,len(powerup_names)):
                        if(tmp_acct.powerups[x] == None): #we don't have it
                            opt_str = "0"
                        else:
                            opt_str = "1"
                        queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,powerup_names[x])
                    #Upgrades
                    for x in range(0,len(upgrade_names)):
                        opt_str = str(tmp_acct.upgrades[x]) + "/" + str(account.upgrade_limit)
                        queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,upgrade_names[x])
                    #Specialization
                    opt_str = self.specialization_mapper[tmp_acct.specialization + self.specialization_offset]
                    queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Specialization")
                else: #we have no data to fill the Player Data menu with; We should blank everything.
                    opt_str = "Unknown"
                    #Name
                    queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Name")
                    #Shells
                    for x in range(0,len(shell_names)):
                        queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,shell_names[x])
                    #Powerups
                    for x in range(0,len(powerup_names)):
                        queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,powerup_names[x])
                    #Upgrades
                    for x in range(0,len(upgrade_names)):
                        queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,upgrade_names[x])
                    #Specialization
                    queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Specialization")

            # - Update our SFX_Manager() -
            self.sfx.clock([0,0])

            #update queue_menu's scaling
            queue_menu.update(self.screen)

            #start drawing the screen
            self.screen.fill([0,0,0])

            #draw the menu onscreen
            queue_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)

            #draw the cursor onscreen
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * queue_menu.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * queue_menu.menu_scale)],int(3 * queue_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * queue_menu.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * queue_menu.menu_scale)],int(3 * queue_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * queue_menu.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * queue_menu.menu_scale),cursorpos[1]],int(3 * queue_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * queue_menu.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * queue_menu.menu_scale),cursorpos[1]],int(3 * queue_menu.menu_scale))

            pygame.display.flip() #update the display...
            clock.tick(900)
            fps = clock.get_fps()
            pygame.display.set_caption("Tank Battalion Online Battle Queue - FPS: " + str(int(fps)))

        if(not queueing and not exit_queue): #we got into a match? start the battle client script(s)!
            self.battle_client()
        elif(exit_queue): #leaving the matchmaking queue?
            pass #we will automatically exit back to the main menu when this happens.

    def battle_client(self, ph=None, Cs=None, thread_num=None, thread_running=None, external_running=None):
        global path
        # - Get our screen surface and client socket (if we don't have one, which can happen in split-screen mode) -
        if(ph != None):
            self.Cs = Cs
            self.screen = ph.get_surface(thread_num)
        # - Menu stuff -
        battle_menu = menu.Menuhandler()
        battle_menu.default_display_size = [160, 120]
        battle_menu.create_menu(["","","","","","","","","",""],
                       [
                        #start by adding our powerup items to the menu
                        [path + "../../pix/powerups/fuel.png",[10,0]],
                        [path + "../../pix/powerups/fire-extinguisher.png",[10,20]],
                        [path + "../../pix/powerups/dangerous-loading.png",[10,40]],
                        [path + "../../pix/powerups/explosive-tip.png",[10,60]],
                        [path + "../../pix/powerups/amped-gun.png",[10,80]],
                        [path + "../../pix/powerups/makeshift-armor.png",[10,100]],
                        #add our shells to the menu
                        [path + "../../pix/ammunition/hollow_shell_button.png",[40,0]],
                        [path + "../../pix/ammunition/regular_shell_button.png",[60,0]],
                        [path + "../../pix/ammunition/explosive_shell_button.png",[80,0]],
                        [path + "../../pix/ammunition/disk_shell_button.png",[100,0]]
                        ],
                       [],buttonindexes=[],name="")
        battle_menu.create_menu(["Continue","Leave Match","","Music Volume","SFX Volume","","Skip Back One Track","Skip Forward One Track"], [["",""],["",""],["",""],[0,10],[0,10],["",""],["",""],["",""]], [[0,0]], buttonindexes=[], name="Ingame Options")
        # - Update our SFX and music volume in Menu 1 so that it doesn't mute as soon as use press ESC_KEY -
        battle_menu.current_menu = 1
        battle_menu.reconfigure_setting([0,10], str(int(round(pygame.mixer.music.get_volume() * 10))), int(round(pygame.mixer.music.get_volume() * 10)), "Music Volume")
        if(ph == None):
            input_volume = self.sfx.sound_volume
        else:
            input_volume = ph.get_volume(thread_num)
        battle_menu.reconfigure_setting([0,10], str(int(round(self.sfx.sound_volume * 10))), int(round(self.sfx.sound_volume * 10)), "SFX Volume")
        battle_menu.current_menu = 0

        # - HUD stuff -
        hud = HUD.HUD()
        hud.default_display_size = [160, 120]
        #add an HUD bar to the side of the screen for HP
        hud.add_HUD_element("vertical bar",[[0,0],[10, 120],[[0,255,0],[0,0,0],[0,0,255]],1.0])
        #add a label to the HP/armor bar
        hud.add_HUD_element("text",[[1, 60],5,[[100,100,100],None,None],"a."])
        #add a numerical indicator to the player's HP/armor
        hud.add_HUD_element("text",[[1,60 + 4],3,[[100,100,100],None,None],"100"])
        #add numerical indicators of the player's powerup cooldown states (index 4-9)
        hud.add_HUD_element("text",[[11,1],9,[[255,0,0],None,None],"cooldown powerup 1"])
        hud.add_HUD_element("text",[[11,21],9,[[255,0,0],None,None],"cooldown powerup 2"])
        hud.add_HUD_element("text",[[11,41],9,[[255,0,0],None,None],"cooldown powerup 3"])
        hud.add_HUD_element("text",[[11,61],9,[[255,0,0],None,None],"cooldown powerup 4"])
        hud.add_HUD_element("text",[[11,81],9,[[255,0,0],None,None],"cooldown powerup 5"])
        hud.add_HUD_element("text",[[11,101],9,[[255,0,0],None,None],"cooldown powerup 6"])
        #add numerical indicators of the player's shell reload times (index 10-13)
        hud.add_HUD_element("text",[[41,1],9,[[255,0,0],None,None],"hollow shell"])
        hud.add_HUD_element("text",[[61,1],9,[[255,0,0],None,None],"regular shell"])
        hud.add_HUD_element("text",[[81,1],9,[[255,0,0],None,None],"explosive shell"])
        hud.add_HUD_element("text",[[101,1],9,[[255,0,0],None,None],"disk shell"])
        #add numerical indicators of player's shells left (index 14-17)
        hud.add_HUD_element("text",[[41,10],9,[[255,255,0],None,None],"hollow shell"])
        hud.add_HUD_element("text",[[61,10],9,[[255,255,0],None,None],"regular shell"])
        hud.add_HUD_element("text",[[81,10],9,[[255,255,0],None,None],"explosive shell"])
        hud.add_HUD_element("text",[[101,10],9,[[255,255,0],None,None],"disk shell"])

        # - Constants regarding the index of battle_menu elements -
        SHELL_START = 6 #index 6-9 are shells
        POWERUP_START = 0 #index 0-5 are powerups
        BAR_START = 17 #index 17 is where HUD HP bars begin...

        # - Key configuration stuff -
        tank_bullets = [0,1,2,3] #[pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        tank_powerups = [4,5,6,7,8,9] #[pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n]
        directions = [10,11,12,13] #[pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_a]
        shoot = 14
        ESC_KEY = 15 #this brings you to the second menu, which lets you continue the match or leave it.
        CURSOR_MOD = 16
        PTT_KEY = 17 #PTT + Dpad = lets you direct people - "up/down/left/right"
        # - Note about KEY_TALK: The server does have a copy of this list and will only let through phrases which it has in its list -
        KEY_TALK = ["yes","no","maybe","understood", #shell keys
                    "1","2","3","4","5","6", #powerup keys
                    "up","left","down","right", #dpad/directions
                    "attack", #shoot
                    "retreat", #ESC_KEY
                    "reform", #cursor_mod key
                    None #PTT key
                    ]
        keys = [] #list of keys pressed
        
        # - Entity/player stuff -
        player_account = account.Account() #your account stats (they get set up properly within battle_client_netcode())
        player_tank = entity.Tank([pygame.image.load(path + "../../pix/tanks/P1U1.png"),pygame.image.load(path + "../../pix/tanks/P1U2.png")], ["tmp team name","tmp player name"]) #your player tank
        entities = [] #list of other players, powerups, bullets
        entities_lock = _thread.allocate_lock()

        # - Arena stuff -
        arena = arena_lib.Arena([[0,0],[0,0]], [pygame.image.load(path + "../../pix/blocks/original_20x20/ground/asphalt.png")], [])
        arena.stretch = False
        arena.TILE_SIZE = 20 #This needs to be set to the tile size of the TANK sprite being used for all players. The arena's tile size will change once the arena is loaded in the netcode thread.
        # - The viewport size of our screen -
        tile_viewport = [15,15]
        # - Our screen scale -
        screen_scale = arena.get_scale(tile_viewport, self.screen)
        # - Set our player's position onscreen -
        player_tank.screen_location = [
            self.screen.get_width() / 2 - (arena.TILE_SIZE / 2) * screen_scale[0],
            self.screen.get_height() / 2 - (arena.TILE_SIZE / 2) * screen_scale[1],
            ]
        # - The blocks we cannot run through (this gets populated once setup occurs within the netcode script) -
        blocks = []

        # - Game setup -
        particles_lock = _thread.allocate_lock()
        particles = [] #list of particle effects (explosions, fire, etc.)
        gfx_particles_lock = _thread.allocate_lock()
        gfx_particles = []
        gfx = GFX.GFX_Manager()
        framecounter = 0 #this makes sense...frame counter for particle stuff I wanna say?
        time_remaining = [500] #this is in seconds; the server needs to send this value to the client, but the client does need a starting value well above 0 to give time for the server to sync the player's timer.

        # - Gameloop setup -
        clock = pygame.time.Clock() #gotta see that cap FPS - or is it a FPS cap???
        # - The next two variables are only needed until I have proper key configuration implemented -
        mousepos = [0,0] #where is our cursor located?
        running = [True] #HAS to be a list so that the value is shared between the _netcode() thread and this thread...bad things happen otherwise.
        explosion_timer = time.time() #this is for checking when the last "game over" explosion happened
        #counts how many explosions occurred. Using this, we can detect approximately how many seconds game over has been and exit the match at an appropriate time.
        explosion_counter = 0
        fps = 30 #an fps counter is needed for moving the cursor around at a reasonable rate
        framecounter = [0]
        shot_cooldown = time.time() #this is so that we don't end up clicking 250 times a second on our volume control...imagine!

        # - These flags are for netcode operation which also involves the client frontend -
        game_end = False #this flag helps me end the game smoothly.
        sync = [False] #this flag prevents us from moving when the server syncs us.
        eliminated = [] #this only gets filled with data once it is game over.
        netcode_performance = [10.0, 100.0] #carries data about game performance: [PPS, ping]
        cps_performance = [100.0] #carries data about game performance: [CPS]

        pending_position = None #this flag gets set to your player position when you resize your screen to avoid teleportation from screen resize.

        # - Start the music (except in split-screen mode - music is handled by the PygameHandler then)! -
        if(ph == None):
            if(len(self.music_files[2]) > 0):
                music_track = random.randint(0,len(self.music_files[2]) - 1)
                self.music.transition_track(self.music_files[2][music_track]) #start the music up again...
        else: #if we are using a PygameHandler(), we need to ensure that we don't try playing any SFX either in the threads inside this BattleEngine() instance.
            self.sfx.server = True

        #start up the netcode        
        _thread.start_new_thread(self.battle_client_netcode,(player_tank, player_account, entities, entities_lock, particles, particles_lock, arena, blocks, screen_scale, running, sync, game_end, eliminated, hud, gfx, time_remaining, netcode_performance, ph, thread_num))
        #start up a thread solely for computations
        _thread.start_new_thread(self.battle_client_compute,(player_tank, running, arena, gfx_particles, gfx_particles_lock, battle_menu, gfx, framecounter, hud, mousepos, cps_performance, ph, thread_num))

        # - This bookmarks the size of our screen at the beginning of a frame. It can be used to help keep the player's onscreen position constant when resizing the game window.
        #   This method is only used when we are using a PygameHandler(), as there is a cleaner way to do this with the pygame.VIDEORESIZE flag.
        if(ph != None):
            previous_screensize = [self.screen.get_width(), self.screen.get_height()]

        # - Now we use this thread to draw graphics, and do keypress detection etc. -
        while running[0]:
            # - This is a simple method of using speedhax; The game WILL detect anyone using it, and you WILL teleport back to where you were -
            #player_tank.speed = 4.5 #4.5 speed is WAAAY faster than normal
            
            # - Update our framecounter -
            framecounter[0] += 1
            if(framecounter[0] > 65535):
                framecounter[0] = 0

            # - Get our screen surface (if we don't have one, which can happen in split-screen mode) -
            if(ph != None):
                self.screen = ph.get_surface(thread_num)

            # - Update our Music() manager, and check if we need to queue more tracks (only for online mode) -
            if(ph == None):
                queue = not self.music.clock() #returns False if we need to queue more tracks
                if(queue and len(self.music_files[2]) > 0): #queue a new random track
                    music_track += 1
                    if(music_track >= len(self.music_files[2])):
                        music_track = 0
                    self.music.queue_track(self.music_files[2][music_track])

            # - Check if we asked to close the game in split-screen mode -
            if(ph != None and running[0] == True):
                running[0] = external_running[0]

            # - If we're dead, we may as well be able to move quickly so we can see what is happening in-game -
            if(player_tank.destroyed == True):
                player_tank.speed = 3.75

            # - Run the pygame event loop, update the keys pressed, and check whether we need a window resize (the first and third one only happens in online mode) -
            if(ph == None): #there are two ways of getting input: via pygame, or the PygameHandler(). For online mode, pygame is used. For offline split-screen mode, the P.H. is used.
                event_pack = controller.get_keys()
                running[0] = not event_pack[0]
                if(event_pack[1] != None): #we requested a window resize?
                    pending_position = player_tank.overall_location[:]
                    resize_dimensions = list(event_pack[1])
                    if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                        resize_dimensions[0] = self.min_screen_size[0]
                    if(resize_dimensions[1] < self.min_screen_size[1]):
                        resize_dimensions[1] = self.min_screen_size[1]
                    self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)
                keys = self.controls.get_input()
                # - Check for mouse movement or mouse click -
                for x in event_pack[2]:
                    if(x.type == pygame.MOUSEMOTION):
                        mousepos[0] = x.pos[0]
                        mousepos[1] = x.pos[1]
                    elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                        keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                        keys.append(CURSOR_MOD)
                    elif(x.type == pygame.MOUSEBUTTONUP):
                        if(shoot in keys):
                            keys.remove(shoot)
                        if(CURSOR_MOD in keys):
                            keys.remove(CURSOR_MOD)
            else: #PygameHandler() needs to get input
                keys = ph.get_input(thread_num)
                if([self.screen.get_width(), self.screen.get_height()] != previous_screensize): #check whether we need to change our tank's coordinates to account for a screen resize
                    pending_position = player_tank.overall_location[:]
                    previous_screensize = [self.screen.get_width(), self.screen.get_height()]

            # - Handle the ESC key -
            if(ESC_KEY in keys and not PTT_KEY in keys): #menu # 1 then...
                battle_menu.current_menu = 1

            # - Make sure that our menu scales properly when we are in menu 1 instead of 0 -
            if(battle_menu.current_menu == 1):
                battle_menu.default_display_size = [320,240]
            else: #our game menu coordinates are in 160x120 res...
                battle_menu.default_display_size = [160,120]

            # - Handle keypresses -
            if(not sync[0]):
                if(not PTT_KEY in keys):
                    for x in directions:
                        if(x in keys and not CURSOR_MOD in keys):
                            with player_tank.lock:
                                player_tank.move(directions.index(x) * 90, arena.TILE_SIZE, screen_scale)
                        elif(x in keys and CURSOR_MOD in keys):
                            mousepos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 80 * battle_menu.menu_scale
                            mousepos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 80 * battle_menu.menu_scale
                    if(shoot in keys and not CURSOR_MOD in keys):
                        with player_tank.lock:
                            player_tank.shoot(arena.TILE_SIZE, server=False)
                    elif(shoot in keys and CURSOR_MOD in keys and time.time() - shot_cooldown > 0.2): #we're shooting a menu item? ...Here we go...menu collision...
                        shot_cooldown = time.time()
                        collide = battle_menu.menu_collision([0,0],[self.screen.get_width(), self.screen.get_height()],mousepos,inc=None)
                        if(battle_menu.current_menu == 0 and collide[0][1] != None): #menu index 0?
                            if(collide[0][1] >= POWERUP_START and collide[0][1] <= SHELL_START - 1): #use powerup?
                                player_tank.use_powerup(collide[0][1] - POWERUP_START, False)
                            elif(collide[0][1] >= SHELL_START and collide[0][1] <= SHELL_START + 3): #use shell?
                                player_tank.use_shell(collide[0][1] - SHELL_START)
                        elif(battle_menu.current_menu == 1 and collide[0][0] != None): #we clicked a button in the second menu (hit ESC to access)
                            if(collide[0][0] == 1): #disconnect?
                                running[0] = False #just make sure we're leaving - this tells the netcode thread that we're leaving, and quits us back to the lobby.
                            elif(collide[0][0] == 6 and ph == None and len(self.music_files[2]) > 0): #skip back one music track (this can only happen with NO PygameHandler() since the PygameHandler() does music for us)
                                music_track -= 1
                                if(music_track < 0):
                                    music_track = len(self.music_files[2]) - 1
                                self.music.transition_track(self.music_files[2][music_track])
                            elif(collide[0][0] == 7 and ph == None and len(self.music_files[2]) > 0): #skip forward one track (this can only happen with NO PygameHandler() since the PygameHandler() does music for us)
                                music_track += 1
                                if(music_track >= len(self.music_files[2])):
                                    music_track = 0
                                self.music.transition_track(self.music_files[2][music_track])
                    # - Check for powerup usage -
                    for x in tank_powerups:
                        if(x in keys):
                            player_tank.use_powerup(tank_powerups.index(x), False)
                    # - Check for shell changing -
                    for x in tank_bullets:
                        if(x in keys):
                            player_tank.use_shell(tank_bullets.index(x))
                else: #we're trying to speak, are we??
                    for x in keys:
                        speak_word = None #find out what on earth we said
                        if(x != PTT_KEY):
                            speak_word = KEY_TALK[x]
                            break
                    if(speak_word != None):
                        player_tank.message(speak_word, "dummy particles", server=False) #send the message!

            # - Handle updating various objects (this MUST go before collision detection happens) -
            arena.shuffle_tiles() #update the arena object's tile shuffling system
            with entities_lock:
                with player_tank.lock: #update some of our various timing variables for reload time, etc.
                    player_tank.clock(arena.TILE_SIZE, screen_scale, particles, framecounter[0], None, False)

            # - Update screen_scale -
            new_scale = arena.get_scale(tile_viewport, self.screen)
            screen_scale[0] = new_scale[0]
            screen_scale[1] = new_scale[1]

            # - Handle tank collision (just our tank, nobody else's) -
            with player_tank.lock:
                player_tank.screen_location = [ #get the position set up properly for starts...
                    (self.screen.get_width() / 2) - (arena.TILE_SIZE * screen_scale[0] / 2),
                    (self.screen.get_height() / 2) - (arena.TILE_SIZE * screen_scale[1] / 2),
                    ]
            collision = player_tank.return_collision(arena.TILE_SIZE, 3) #collision offset of 3 pixels to make map navigation easier
            tile_collision = arena.check_collision(tile_viewport, player_tank.overall_location[:], collision)
            # - Comment out EVERYTHING inside the "with player_tank..." statement including the with statement to implement locationhax; You can walk through walls. However, my Anti-Cheat WILL detect you and TP you off the walls! -
            with player_tank.lock:
                for x in tile_collision:
                    if(x[0] in blocks and player_tank.destroyed != True): #block collision isn't necessary if the player is dead...they may as well be free to spectate
                        player_tank.unmove()
                        break

            # - Check if we need to reposition to avoid teleportation upon window resize -
            if(pending_position != None):
                player_tank.goto(pending_position[:], TILE_SIZE=arena.TILE_SIZE, screen_scale=screen_scale)
                pending_position = None

            # - Check if it is time to leave (self.BATTLE_TIMER * 0.65 seconds after game over) -
            #   - NOTE: This might need to be here to avoid the server deleting the player data server-side,
            #       and crashing the client during the results screen.
            if(explosion_counter * self.EXPLOSION_TIMER > self.BATTLE_TIMER * 0.65): #time to exit battle?
                running[0] = False

            # - Set up an explosion system IF the game is over -
            msg = None #if this does not equal None, we create explosions. If it equals None, then the game's not over yet.
            #This is set to -2 because of the IF statement down below which checks if this gets equal
            destroyed_counter = -2 #to len(eliminated) - 1. If that happens, I assume the game is finished.
            self_eliminated = False
            for x in eliminated:
                if(x[0] == player_tank.team and x[1] != False): #our team got eliminated?
                    msg = ["game over","defeat","L","oig"][random.randint(0,3)]
                elif(x[1] != False):
                    if(destroyed_counter < 0): #this is the first team we've seen get eliminated?
                        destroyed_counter = 1
                    else: #just increment the counter...
                        destroyed_counter += 1
                if(x[0] == player_tank.team):
                    if(x[1] == False):
                        self_eliminated = False
                    else:
                        self_eliminated = True
            if(destroyed_counter >= len(eliminated) - 1 and self_eliminated == False): #we won?
                msg = ["W","victory"][random.randint(0,1)]
            if(time_remaining[0] <= 0): #We ran out of time (teams alive get 1st place, teams already dead get worse places. You can consider yourself to have won...or lost...I'd say a draw)?
                msg = ["draw","tie"][random.randint(0,1)]

            #create an explosion every X seconds + a bunch of word particles
            if(time.time() - explosion_timer > self.EXPLOSION_TIMER and msg != None):
                explosion_timer = time.time() #reset the explosion timer...
                explosion_counter += 1
                with particles_lock:
                    GFX.create_explosion(particles, [random.randint(0,len(arena.arena[0])), random.randint(0,len(arena.arena))], random.randint(2,6), [0.05, random.randint(1,3)], [[255,0,0],[255,255,0]],[[0,0,0],[100,100,100],[50,50,50]], 0.85, 0, msg, arena.TILE_SIZE)
                    # - Create a burst of word particles to help us understand the fact that the game's over -
                    for x in range(0,self.WORDS_QTY): #create 10 words in this interval of self.EXPLOSION_TIMER time
                        time_offset = (self.EXPLOSION_TIMER / (x + 1))
                        start_map_pos = [random.randint(0,len(arena.arena[0])), random.randint(0,len(arena.arena))]
                        finish_map_pos = [start_map_pos[0] + random.randint(-1,1), start_map_pos[1] + random.randint(-1,1)]
                        start_size = random.randint(1,200) / 100
                        finish_size = random.randint(1,200) / 100
                        start_color = [random.randint(0,255),random.randint(0,255),random.randint(0,255)]
                        finish_color = [random.randint(0,255),random.randint(0,255),random.randint(0,255)]
                        time_start = time.time() + time_offset
                        time_finish = time.time() + self.EXPLOSION_TIMER + time_offset
                        form = msg #text
                        particles.append(GFX.Particle(start_map_pos, finish_map_pos, start_size, finish_size, start_color, finish_color, time_start, time_finish, form))

            # - Draw everything -
            if(ph != None): #wait until the PygameHandler has flipped our display if we're in split-screen mode to prevent screen tearing
                while not ph.surface_flipped(thread_num):
                    pass
            self.screen.fill([0,0,0]) #start with black...every good game starts with a black screen.
            arena.draw_arena(tile_viewport, player_tank.map_location[:], self.screen) #draw the arena
            player_tank.draw(self.screen, screen_scale, arena.TILE_SIZE) #draw the player tank
            with entities_lock: #draw all other entities
                # - For bullets and powerups: draw(self, screen, screen_scale, arena_offset, TILE_SIZE)
                # - For tanks: draw(self, screen, screen_scale, TILE_SIZE, third_person_coords=None, client_only=True)
                bar = 0
                for x in entities:
                    if(x.type != "Tank"): #Bullet/powerup
                        x.draw(self.screen, screen_scale, player_tank.map_location[:], arena.TILE_SIZE)
                    else: #tank
                        x.draw(self.screen, screen_scale, arena.TILE_SIZE, player_tank.map_location[:], False)
                        # - Update their HUD HP bar at the same time IF the tank isn't ourselves -
                        try:
                            if(x.name != player_tank.name or x.team != player_tank.team):
                                if(x.armor > 0.025):
                                    color = [0,255,0]
                                    value = x.armor / x.start_armor
                                    label = str(int(x.armor)) + " A."
                                else:
                                    color = [255,0,0]
                                    value = x.HP / x.start_HP
                                    label = str(int(x.HP)) + " HP"
                                if(value > 1.0): #we have more armor/HP then we are technically supposed to?
                                    value = 1.0
                                    color = [255,255,0] #overdrive color; means we have more than we should...
                                hud.update_HUD_element(BAR_START + bar * 3,[[(x.overall_location[0] - player_tank.map_location[0]) * arena.TILE_SIZE * screen_scale[0],(-0.35 + x.overall_location[1] - player_tank.map_location[1]) * arena.TILE_SIZE * screen_scale[1]],[20,5],[color,[0,0,0],[0,0,255]],value])
                                hud.update_HUD_element(bar * 3 + BAR_START + 1,[[(x.overall_location[0] - player_tank.map_location[0] + 0.05) * arena.TILE_SIZE * screen_scale[0],(-0.275 + x.overall_location[1] - player_tank.map_location[1]) * arena.TILE_SIZE * screen_scale[1]],3,[[150,150,150],None,None],label])
                                # - The font is size 7 for this. x_offset is a value which should always equal half of the name's length in pixels -
                                x_offset = len(x.name) * 7 * hud.rectangular_scale * 0.25
                                hud.update_HUD_element(bar * 3 + BAR_START + 2,[[(0.5 + x.overall_location[0] - player_tank.map_location[0]) * arena.TILE_SIZE * screen_scale[0] - x_offset,(0.125 + x.overall_location[1] - player_tank.map_location[1]) * arena.TILE_SIZE * screen_scale[1]],3,[[150,150,150],None,None],x.name])
                            else:
                                hud.update_HUD_element(BAR_START + bar * 3,[[-1000,-1000],[20,5],[color,[0,0,0],[0,0,255]],value])
                                hud.update_HUD_element(bar * 3 + BAR_START + 1,[[-1000,-1000],3,[[150,150,150],None,None],label])
                                # - The font is size 7 for this. x_offset is a value which should always equal half of the name's length in pixels -
                                x_offset = len(x.name) * 7 * hud.rectangular_scale * 0.25
                                hud.update_HUD_element(bar * 3 + BAR_START + 2,[[-1000,-1000],3,[[150,150,150],None,None],x.name])
                        except Exception as e:
                            print("Exception occurred at battle_client(): " + str(e) + " - Nonfatal")
                        bar += 1 #increment the HP bar counter
            # - Draw all particle effects and delete old particles -
            with particles_lock:
                # - Delete any particles() which are finished their job (this has to happen first to avoid invalid color arguments from bad timing) -
                decrement = 0
                for x in range(0,len(particles)):
                    if(particles[x - decrement].timeout == True):
                        del(particles[x - decrement])
                        decrement += 1
            for x in particles: # - Draw the remaining particles -
                x.clock()
                x.draw(arena.TILE_SIZE, screen_scale, player_tank.map_location[:], self.screen)
            # - Delete any gfx_particles() which are finished their job (this has to happen first to avoid invalid color arguments from bad timing) -
            decrement = 0
            with gfx_particles_lock:
                for x in range(0,len(gfx_particles)):
                    if(gfx_particles[x - decrement].timeout == True):
                        del(gfx_particles[x - decrement])
                        decrement += 1
            for x in gfx_particles: # - Draw the remaining particles -
                x.clock()
                x.draw(arena.TILE_SIZE, screen_scale, player_tank.map_location[:], self.screen)
            # - Draw time remaining in game -
            zero_filler = (5 - len(str(round(time_remaining[0],1)))) * "0"
            str_time = str(round(time_remaining[0],1))
            if(str_time[0] == "-"):
                str_time = str_time[0] + zero_filler + str_time[1:]
            else:
                str_time = zero_filler + str_time
            time_text = "Time - " + str_time + "s" #time_remaining is a variable which NEEDS to be sent from the server...
            font.draw_words(time_text, [int(self.screen.get_width() / 2 - 0.5 * battle_menu.menu_scale * font.SIZE * len(time_text) / 2),self.screen.get_height() - int(font.SIZE * 0.5 * battle_menu.menu_scale)], [255,255,0], battle_menu.menu_scale * 0.5, self.screen)
            # - Draw the minimap -
            minimap_surf = arena.draw_minimap(blocks) #draw the arena on the minimap
            for x in range(0,len(gfx_particles)): #draw the positions of all GFX particles on the minimap
                gfx_particles[x].draw_minimap(minimap_surf)
            with particles_lock:
                for x in range(0,len(particles)):
                    particles[x].draw_minimap(minimap_surf)
            if(ph == None):
                self.sfx.draw_minimap(minimap_surf) #draw the positions of all SFX objects on the minimap
            else:
                ph.draw_minimap(thread_num, minimap_surf)
            with entities_lock: #draw all entity positions on the minimap
                for x in entities:
                    if(x.type == "Tank" or x.type == "Bullet"):
                        x.draw_minimap(minimap_surf, player_tank.team, False)
                    else: #powerup?
                        x.draw_minimap(minimap_surf)
            minimap_room = int((self.screen.get_width() - battle_menu.menu_scale * 0.5 * font.SIZE * len(time_text)) / 2)
            possible_minimap_sizes = [int(minimap_room * 0.95), int(self.screen.get_height() / 3)]
            scale_qtys = [minimap_surf.get_width() / minimap_surf.get_height(), minimap_surf.get_height() / minimap_surf.get_width()]
            final_minimap_size = [1,1]
            if(possible_minimap_sizes[0] * scale_qtys[1] < possible_minimap_sizes[1]):
                final_minimap_size[0] = possible_minimap_sizes[0]
                final_minimap_size[1] = int(possible_minimap_sizes[0] * scale_qtys[1])
            else:
                final_minimap_size[1] = possible_minimap_sizes[1]
                final_minimap_size[0] = int(possible_minimap_sizes[1] * scale_qtys[0])
            minimap_surf = pygame.transform.scale(minimap_surf, final_minimap_size) #scale the minimap so it retains its size
            self.screen.blit(minimap_surf, [self.screen.get_width() - minimap_surf.get_width(), self.screen.get_height() - minimap_surf.get_height()]) #copy the minimap to the bottom-right corner of the screen
            # - Draw the menu -
            if(battle_menu.current_menu == 1): #give the menu a black background; It's almost unreadable otherwise.
                self.screen.fill([0,0,0])
            battle_menu.draw_menu([0,0],[self.screen.get_width(), self.screen.get_height()],self.screen,mousepos)
            if(battle_menu.current_menu == 0): #we only draw the HUD if we're playing, not if we're in the ingame settings menu.
                hud.draw_HUD(self.screen)
            #draw the cursor onscreen
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0],mousepos[1] - int(8 * battle_menu.menu_scale)],[mousepos[0],mousepos[1] - int(4 * battle_menu.menu_scale)],int(3 * battle_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0],mousepos[1] + int(8 * battle_menu.menu_scale)],[mousepos[0],mousepos[1] + int(4 * battle_menu.menu_scale)],int(3 * battle_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0] + int(8 * battle_menu.menu_scale),mousepos[1]],[mousepos[0] + int(4 * battle_menu.menu_scale),mousepos[1]],int(3 * battle_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0] - int(8 * battle_menu.menu_scale),mousepos[1]],[mousepos[0] - int(4 * battle_menu.menu_scale),mousepos[1]],int(3 * battle_menu.menu_scale))

            # - Update the display (which has to be done different ways depending on whether we use a PygameHandler() or not) -
            if(ph == None):
                pygame.display.flip()
            else:
                ph.surface_flip(thread_num)

            # - Handle FPS display -
            clock.tick(750)
            fps = clock.get_fps()
            if(ph == None):
                pygame.display.set_caption("Tank Battalion Online - FPS: " + str(int(fps)) + " - CPS: " + str(cps_performance[0]) + " - PPS: " + str(netcode_performance[0]) + " - Ping: " + str(netcode_performance[1]) + " ms")
            else: #make sure the main thread can see our FPS
                ph.update_fps(thread_num)
        if(ph != None):
            while not ph.surface_flipped(thread_num): #blacken our display to show the thread ended
                pass
            self.screen = ph.get_surface(thread_num)
            self.screen.fill([0,0,0])
            ph.surface_flip(thread_num)
            thread_running[thread_num] = False #let the main thread know we're done

    def battle_client_compute(self, player_tank, running, arena, gfx_particles, gfx_particles_lock, battle_menu, gfx, framecounter, hud, mousepos, cps_performance, ph=None, thread_num=None):
        # - Lists of all the pygame IDs of our keybinds. These lists are then used to display the correct key on the player's HUD required to take a certain action -
        if(ph == None):
            tank_bullets_pygame_keys = self.controls.buttons[0:4] #[pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
            tank_powerups_pygame_keys = self.controls.buttons[4:10] #[pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n]
        else:
            tank_bullets_pygame_keys = ph.get_controls(thread_num)[0:4]
            tank_powerups_pygame_keys = ph.get_controls(thread_num)[4:10]
        
        # - For recording performance statistics -
        clock = pygame.time.Clock()
        
        while running[0]:
            # - Make sure our cursor stays onscreen -
            if(mousepos[0] < 0): #no negative locations allowed!
                mousepos[0] += self.screen.get_width()
            if(mousepos[1] < 0):
                mousepos[1] += self.screen.get_height()
            if(mousepos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                mousepos[0] -= self.screen.get_width()
            if(mousepos[1] > self.screen.get_height()):
                mousepos[1] -= self.screen.get_height()

            # - Update audio volume -
            if(battle_menu.current_menu == 1):
                self.music.set_volume(int(battle_menu.grab_settings(["Music Volume"])[0][0]) / 10)
                self.sfx.sound_volume = int(battle_menu.grab_settings(["SFX Volume"])[0][0]) / 10
                if(ph != None):
                    ph.set_volume(thread_num, int(battle_menu.grab_settings(["SFX Volume"])[0][0]) / 10)

            # - Update P1's HUD, starting with P1's HP/Armor bar and the menu update command -
            battle_menu.update(self.screen)
            if(player_tank.armor > 0.025):
                color = [0,255,0]
                value = player_tank.armor / player_tank.start_armor
                label = "A."
                hud.update_HUD_element_value(2,str(int(player_tank.armor)))
            else:
                color = [255,0,0]
                value = player_tank.HP / player_tank.start_HP
                label = "HP"
                hud.update_HUD_element_value(2,str(int(player_tank.HP)))
            if(value > 1.0): #we have more armor/HP then we are technically supposed to?
                value = 1.0
                color = [255,255,0] #overdrive color; means we have more than we should...
            hud.update_HUD_element_value(0,value)
            hud.update_HUD_element_color(0,[color,[0,0,0],[0,0,255]])
            hud.update_HUD_element_value(1,label)
            #Update P1's powerup cooldown HUD
            for x in range(3,9):
                if(player_tank.powerups[x - 3] != None and player_tank.powerups[x - 3] != True):
                    if(str(type(player_tank.powerups[x - 3])) == "<class 'str'>"): #we're currently using the powerup?
                        hud.update_HUD_element_value(x,str(int(float(player_tank.powerups[x - 3]))))
                        hud.update_HUD_element_color(x,[[255,255,0],None,None])
                    elif(player_tank.powerups[x - 3] != None): #powerup is on cooldown?
                        hud.update_HUD_element_value(x,str(int(float(player_tank.powerups[x - 3]))))
                        hud.update_HUD_element_color(x,[[255,0,0],None,None])
                else: #powerup is ready?
                    key_to_press = None  #check to see if we can display the key to use the powerup...
                    for key in range(0,len(menu.keys)):
                        if(self.controls.kb_ctrl == "kb"): #we only look for a letter if we're using a keyboard.
                            if(tank_powerups_pygame_keys[x - 3] == menu.keys[key][0]):
                                key_to_press = menu.keys[key][1]
                                break
                        else: #this is a joystick?
                            key_to_press = str(x - 3) #just give the button number
                    if(key_to_press == None and player_tank.powerups[x - 3] != None):
                        hud.update_HUD_element_value(x,"")
                        hud.update_HUD_element_color(x,[[0,255,0],None,None])
                    elif(player_tank.powerups[x - 3] != None):
                        hud.update_HUD_element_value(x,key_to_press)
                        hud.update_HUD_element_color(x,[[0,255,0],None,None])
                    else: #powerup isn't available!!!
                        hud.update_HUD_element_value(x,"x")
                        hud.update_HUD_element_color(x,[[255,0,0],None,None])
            #Update P1's shell HUD
            for x in range(9,13):
                if(player_tank.reload_time() != True): #the tank hasn't finished reloading yet?
                    if(player_tank.current_shell == x - 9): #display the reload time left if we're loading this type of shell.
                        #Else, just draw the key needed to use the shell type.
                        hud.update_HUD_element_value(x,str(int(player_tank.reload_time())))
                        hud.update_HUD_element_color(x,[[255,0,0],None,None])
                        continue
                #the tank has a shell ready, or we're not loading this type of shell?
                key_to_press = None  #check to see if we can display the key to use the shell...
                for key in range(0,len(menu.keys)):
                    if(tank_bullets_pygame_keys[x - 9] == menu.keys[key][0]):
                        key_to_press = menu.keys[key][1]
                        break
                if(key_to_press != None):
                    hud.update_HUD_element_value(x,key_to_press)
                else:
                    hud.update_HUD_element_value(x,"")
                hud.update_HUD_element_color(x,[[0,255,0],None,None])
            for x in range(13,17):
                hud.update_HUD_element_value(x,str(int(player_tank.shells[x - 13])))

            # - Copy the GFX_Manager particles into the particles[] list -
            with gfx.lock:
                with gfx_particles_lock:
                    gfx.draw(gfx_particles, framecounter[0], arena.TILE_SIZE)
                gfx.purge() #delete old particles

            # - Update our SFX_Manager() -
            if(ph == None):
                with self.sfx.lock:
                    self.sfx.clock(player_tank.overall_location[:])
            else: #this is the SFX_Manager() clock equivalent which needs to happen when using a PygameHandler().
                ph.set_player_pos(thread_num, player_tank.overall_location[:])
            
            # - Get CPS and send them to the main thread -
            clock.tick(750)
            cps_performance[0] = round(clock.get_fps(),1)
    
    def battle_client_netcode(self, player_tank, player_account, entities, entities_lock, particles, particles_lock, arena, blocks, screen_scale, running, sync, game_end, eliminated, hud, gfx, time_remaining, netcode_performance, ph=None, thread_num=None): #netcode and background processes for battle_client().
        setup = True #do we still need to set up the game?
        packets = True #are we going to stop exchanging packets yet?
        clock = pygame.time.Clock() #I like to see my PPS
        SFX.ID_NUM = 0 #Reset our SFX sound counter, so that we don't lose any sounds at the beginning of the battle
        old_tile_data = None #we compare this with new tile data we get from the server to see if we need to clear our tank's unmove() flag when a brick is destroyed.

        #define our list of powerup images
        powerup_images = [
            pygame.image.load(path + "../../pix/powerups/fuel.png").convert(),
            pygame.image.load(path + "../../pix/powerups/fire-extinguisher.png").convert(),
            pygame.image.load(path + "../../pix/powerups/dangerous-loading.png").convert(),
            pygame.image.load(path + "../../pix/powerups/explosive-tip.png").convert(),
            pygame.image.load(path + "../../pix/powerups/amped-gun.png").convert(),
            pygame.image.load(path + "../../pix/powerups/makeshift-armor.png").convert(),
            pygame.image.load(path + "../../pix/ammunition/hollow_shell_button.png").convert(),
            pygame.image.load(path + "../../pix/ammunition/regular_shell_button.png").convert(),
            pygame.image.load(path + "../../pix/ammunition/explosive_shell_button.png").convert(),
            pygame.image.load(path + "../../pix/ammunition/disk_shell_button.png").convert()
            ]
        
        while packets:
            #Recieve data from the server
            #Recieve packet description: All packets start with a "prefix", a small string describing what the packet does and the format corresponding to it.
            # - Type A) Setup packet. Very long packet, used to setup the client's game state. (Not entity related stuff; Account data, arena data, etc.)
            #       Format: ["setup", account.return_data(), map_name]
            # - Type B) Sync packet. Shorter packet, usually used to change the client's player state. In the case that a sync packet has to be used, the client MUST send back the exact same data next packet. Only used with AC enabled.
            #       Format: ["sync", server_entity.return_data()]
            # - Type C) Normal packet. Sends player data such as where entities are onscreen, the cooldown of your consumables, and your reload time.
            #       Format: ["packet",[entity1, entity2, entity3...]]
            # - Type D) Ending packet. Sends a simple message to the client letting the client know that the game is finished.
            #       Format: ["end", [entity1, entity2, entity3...], elimination_order]
            #time_receive = time.time() #Timing debug info
            data_pack = netcode.recieve_data(self.Cs, self.buffersize)
            data = data_pack[0]
            netcode_performance[1] = data_pack[1] #get ping
            for x in data_pack[2]: #print out all packet receive errors
                print(x)
            #time_receive = time.time() - time_receive #Timing debug info
            #print(len(str(data))) #Prints the size in bytes of the received data packet

            #time_compute = time.time() #Timing debug info
            for x in range(0,len(self.GAME_PACKETS)):
                verify = netcode.data_verify(data, self.GAME_PACKETS[x])
                if(verify == True): #we only need this data to pass ONE of the self.GAME_PACKETS data formats.
                    break
            if(data != None and verify == True): #...only try this if we get some valid data...otherwise bad things might happen lol
                if(data[0] == "setup"): #set up the game!
                    # - Set up the player -
                    player_account.enter_data(data[1]) #gotta make sure we have our account + tank set up properly
                    with player_tank.lock:
                        #team name will get set on a sync packet. The server will have to send one right after setup occurs.
                        player_tank_new = player_account.create_tank(self.team_images[0], "team name here...")
                        player_tank.enter_data(player_tank_new.return_data(), arena.TILE_SIZE, screen_scale, server=False) #this has to be run twice, once as client, once as server to enter all the data necessary.
                        player_tank.enter_data(player_tank_new.return_data(), arena.TILE_SIZE, screen_scale, server=True) # - The server version only inputs certain pieces of data, as does the client. Doing both enters all the data.
                    # - Set up the arena -
                    with arena.lock:
                        arena_name = data[2] #the server sent us the name of the arena we're playing on
                        # - Get our arena data from the name the server sent us...
                        #   (and DON'T convert the images to faster formats BECAUSE we need to scale them before blitting them. Converting NOW would introduce image corruption into the final arena we draw onscreen)
                        arena_data = import_arena.return_arena(arena_name, False)
                        arena.arena = arena_data[0] #input the arena data into our arena object
                        arena.tiles = arena_data[1]
                        #arena.TILE_SIZE = arena.tiles[0].get_width() #I don't think this actually ends up being necessary...
                        for x in range(0,len(arena.scaled_tiles)):
                            del(arena.scaled_tiles[0])
                        for x in range(0,len(arena_data[1])):
                            newsurf = pygame.Surface([arena_data[1][x].get_width(), arena_data[1][x].get_height()])
                            newsurf.blit(arena_data[1][x], [0,0])
                            arena.scaled_tiles.append(newsurf)
                        #I had this here...but it shouldn't be. We SHOULDN'T populate scaled_tiles[] with the same data as arena.tiles[]; it would lead to both the unscaled and scaled versions pointing to the same data.
                        #arena.scaled_tiles = arena_data[1]
                        arena.shuffle_patterns = arena_data[2]
                        for x in arena_data[3]:
                            blocks.append(x)
                        # - Now we update our arena tile scale -
                        arena.last_screen_size = [-1,-1] #changing this value WILL make the game update the scale.
                        arena.clear_flag_locations() #make sure we know where our flags are; this make it so the minimap knows what to mark as grey (a flag).
                        arena.set_flag_locations(arena_data[6])
                    # - Set up the HUD a bit (HP bars for all players other than ourselves) & add enough tank entities for all players -
                    for x in range(0,len(data[3])):
                        hud.add_HUD_element("horizontal bar",[[0,-100],[20,5],[[0,255,0],[0,0,0],[0,0,255]],1.0],False)
                        hud.add_HUD_element("text",[[0,-100],7,[[255,0,0],False,False],"100 HP"],False)
                        hud.add_HUD_element("text",[[0,-100],7,[[255,0,0],False,False],"Player Name"],False)
                    # - Set up all players -
                    with entities_lock:
                        for x in range(0,len(entities)): #clear the entities list
                            del(entities[x])
                        for x in range(0,len(data[3])): #Index 4 is every player's data in the match.
                            new_tank = entity.Tank("image will be fixed", ["Tank name which will be inserted when we enter_data()","Team name which will be fixed when we enter_data()"])
                            new_tank.enter_data(data[3][x], TILE_SIZE=arena.TILE_SIZE, screen_scale=[1,1], server=False) #fixes everything but the image, which we can do by checking if the player is on our team. if not, the image is p2's tank.
                            # - Fix the image -
                            new_tank.load_image(self.team_images[new_tank.team_num])
                            entities.append(new_tank)
                    setup = False
                elif(data[0] == "sync"): #we're moving a bit funny, and the server doesn't like it...we can't move for a bit here =(
                    sync[0] = True #turn on our sync flag (auugh! we can't move all of a sudden!)
                    with player_tank.lock:
                        player_tank.enter_data(data[1], arena.TILE_SIZE, screen_scale) #reset our tank's position a bit...
                    print("Synced to location: " + str(player_tank.overall_location))
                elif(data[0] == "packet"): #normal data packet
                    with entities_lock:
                        decrement = 0
                        for x in range(0,len(entities)):
                            if(entities[x - decrement].type != "Tank"):
                                del(entities[x - decrement]) #delete all of the entities list (except tanks) without removing our pointer to the list
                                decrement += 1
                        for x in range(0,len(data[1])):
                            if(data[1][x][0] == "Powerup"): #we need to create a powerup object and insert attributes into it
                                entities.append(entity.Powerup("image will be fixed", 0, [0,0]))
                                entities[len(entities) - 1].enter_data(data[1][x]) #fix most of my phony data entries
                                entities[len(entities) - 1].image = powerup_images[entities[len(entities) - 1].powerup_number] #fix the powerup image, which won't be fixed by my enter_data() command
                            elif(data[1][x][0] == "Bullet"): #we need to create a bullet object and insert attributes into it
                                entities.append(entity.Bullet("image will be fixed", "team name will be fixed", 0, 0, [1,1,1], "dummy tank object which won't be fixed"))
                                entities[len(entities) - 1].enter_data(data[1][x]) #fix most of the bad data entries I made above
                                entities[len(entities) - 1].image = player_tank.shell_images[entities[len(entities) - 1].shell_type] #fix the bullet's image
                            elif(data[1][x][0] == "Tank"): #we need to create a tank object and insert attributes into it
                                new_tank_data = entity.Tank("image will be fixed", ["Tank name which will be inserted when we enter_data()","Team name which will be fixed when we enter_data()"])
                                new_tank_data.enter_data(data[1][x]) #fixes everything but the image, which we can do by checking if the player is on our team. if not, the image is p2's tank.
                                for find in range(0,len(entities)): #check where this tank is...
                                    if(entities[find].type == "Tank" and new_tank_data.name == entities[find].name and new_tank_data.team_num == entities[find].team_num):
                                        entities[find].enter_data(data[1][x])
                                        break
                    # - Update our particle list -
                    if(data[2] != None): #the server is sending particles this packet?
                        with particles_lock:
                            for x in range(0,len(particles)):
                                del(particles[0])
                            for x in data[2]:
                                tmp_particle = GFX.Particle([0,0], [0,0], 1, 1, [0,0,0], [0,0,0], 1, 2, form=0) #create a blank particle
                                tmp_particle.enter_data(x) #enter some attribute data into the particle
                                particles.append(tmp_particle) #add it to the particles list so it can be drawn
                    if(data[3] != None): #we got GFX_Manager particle data too?
                        with gfx.lock:
                            gfx.enter_data(data[3])
                    if(data[4] != None): #the server is sending block updates this packet?
                        arena.modify_tiles(data[4]) #update our tiles...
                        if(data[4] != old_tile_data): #we need to clear our unmove() flag?
                            old_tile_data = data[4][:]
                            player_tank.clear_unmove_flag() #this function doesn't need to be under any sort of .lock() because it simply changes a flag under the hood from True to False.
                    # - Update eliminated list -
                    if(len(eliminated) != len(data[5])): #make sure eliminated is the right length
                        if(len(eliminated) > len(data[5])):
                            for x in range(0,len(eliminated) - len(data[5])):
                                del(eliminated[len(eliminated) - 1])
                        else:
                            for x in range(0,len(data[5]) - len(eliminated)):
                                eliminated.append(["",False])
                    for x in range(0,len(data[5])): #this is the order teams were eliminated in.
                        eliminated[x][0] = data[5][x][0]
                        eliminated[x][1] = data[5][x][1]
                    # - Update SFX_Manager() -
                    if(ph == None):
                        with self.sfx.lock:
                            self.sfx.enter_data(data[6], player_tank.overall_location[:])
                    else: #if we're using a PygameHandler(), we just copy the data we got from the server and enter it into the PygameHandler()'s SFX_Manager() instead of ours.
                        ph.add_sounds(thread_num, data[6])
                    # - Update time_remaining -
                    time_remaining[0] = data[7]
                elif(data[0] == "end"): #game over?
                    # - Update eliminated list -
                    if(len(eliminated) != len(data[2])): #make sure eliminated is the right length
                        if(len(eliminated) > len(data[2])):
                            for x in range(0,len(eliminated) - len(data[2])):
                                del(eliminated[len(eliminated) - 1])
                        else:
                            for x in range(0,len(data[2]) - len(eliminated)):
                                eliminated.append(["",False])
                    for x in range(0,len(data[2])): #this is the order teams were eliminated in.
                        eliminated[x][0] = data[2][x][0]
                        eliminated[x][1] = data[2][x][1]
                    game_end = True
                    with entities_lock:
                        decrement = 0
                        for x in range(0,len(entities)):
                            if(entities[x - decrement].type != "Tank"):
                                del(entities[x - decrement]) #delete all of the entities list (except tanks) without removing our pointer to the list
                                decrement += 1
                        for x in range(0,len(data[1])):
                            if(data[1][x][0] == "Powerup"): #we need to create a powerup object and insert attributes into it
                                entities.append(entity.Powerup("image will be fixed", 0, [0,0]))
                                entities[len(entities) - 1].enter_data(data[1][x]) #fix most of my phony data entries
                                entities[len(entities) - 1].image = powerup_images[entities[len(entities) - 1].powerup_number] #fix the powerup image, which won't be fixed by my enter_data() command
                            elif(data[1][x][0] == "Bullet"): #we need to create a bullet object and insert attributes into it
                                entities.append(entity.Bullet("image will be fixed", "team name will be fixed", 0, 0, [1,1,1], "dummy tank object which won't be fixed"))
                                entities[len(entities) - 1].enter_data(data[1][x]) #fix most of the bad data entries I made above
                                entities[len(entities) - 1].image = player_tank.shell_images[entities[len(entities) - 1].shell_type] #fix the bullet's image
                            elif(data[1][x][0] == "Tank"): #we need to create a tank object and insert attributes into it
                                new_tank_data = entity.Tank("image will be fixed", ["Tank name which will be inserted when we enter_data()","Team name which will be fixed when we enter_data()"])
                                new_tank_data.enter_data(data[1][x]) #fixes everything but the image, which we can do by checking if the player is on our team. if not, the image is p2's tank.
                                for find in range(0,len(entities)): #check where this tank is...
                                    if(entities[find].type == "Tank" and new_tank_data.name == entities[find].name and new_tank_data.team_num == entities[find].team_num):
                                        entities[find].enter_data(data[1][x])
                                        break
                    # - Update time_remaining -
                    time_remaining[0] = data[3]

            # - Copy a small amount of data from the entities list into our player_tank object -
            for x in range(0,len(entities)): #find which tank is us...
                if(entities[x].type == "Tank" and entities[x].name == player_tank.name and entities[x].team == player_tank.team): #we found us?
                    with player_tank.lock: #this basically syncs some basic attributes about ourselves so that we know our own tank's current state...
                        player_tank.last_shot = entities[x].last_shot
                        player_tank.HP = entities[x].HP
                        player_tank.armor = entities[x].armor
                        player_tank.speed = entities[x].speed
                        player_tank.RPM = entities[x].RPM
                        player_tank.last_shot = entities[x].last_shot
                        for y in range(0,len(entities[x].shells)):
                            player_tank.shells[y] = entities[x].shells[y]
                        for y in range(0,len(entities[x].powerups)):
                            player_tank.powerups[y] = entities[x].powerups[y]
                        player_tank.team_num = entities[x].team_num #fix OUR image + our team_num, since it WILL be wrong.
                        player_tank.spotted_images = self.team_images[player_tank.team_num]
                    break
            #time_compute = time.time() - time_compute #Timing debug info

            # - Send our data back to the server -
            #   Format:
            #   - Normal packet:["packet",Tank.return_data()]
            #   - Leave match: ["end",Tank.return_data()]
            #   - Still need to setup (packet lost): ["setup"]
            #time_send = time.time() #Timing debug info
            if(running[0] == True):
                if(setup):
                    netcode.send_data(self.Cs, self.buffersize, ["setup"])
                else:
                    netcode.send_data(self.Cs, self.buffersize, ["packet",player_tank.return_data()])
            else: #if we're not in the game anymore, just start sending lobby packets. The server will find out what we're doing and accomodate us.
                packets = False
            sync[0] = False #disable the sync after we send our data to the server
            #time_send = time.time() - time_send #Timing debug info

            #print("Receive time: " + str(round(time_receive,4)) + "; Compute time: " + str(round(time_compute,4)) + "; Send time: " + str(round(time_send,4)) + ".") #Timing debug info

            clock.tick(800) #tick our clock; it won't hit close to 800PPS obviously, but I just want to see my PPS without hitting an infinity value if something goes wrong...
            netcode_performance[0] = round(clock.get_fps(),1)

    def return_rating(self, player_account, rating=False): #creates a numerical rating number for a player.
        player_stat = 0 #temporary variable which I use to calculate a player's numerical rating
        if(rating): #this is for rated/ranked battles only.
            player_stat += self.EXP_WEIGHT * player_account.experience #add player exp to predicted performance
        player_stat += self.CASH_WEIGHT * player_account.cash #add player cash to predicted performance
        # - Find the player's individual upgrade levels, and add player rating from them -
        for b in range(0,len(player_account.upgrades)):
            player_stat += self.UPGRADE_WEIGHTS[b] * player_account.upgrades[b]
        # - Add the player's number of shells of each type to the player's predicted performance -
        for x in range(0,len(player_account.shells)):
            player_stat += player_account.shells[x] * self.SHELLS_WEIGHT[x]
        # - Add the player's powerups to the player's predicted performance -
        for x in range(0,len(player_account.powerups)):
            if(player_account.powerups[x] == True):
                player_stat += self.POWERUP_WEIGHT
        # - Add the player's specialization number to the player's predicted performance -
        player_stat += self.SPECIALIZATION_WEIGHT * abs(player_account.specialization)
        return player_stat / self.MMCEF

    def create_account(self,rating,player_name="Bot Player"): #creates an account with upgrades which correspond roughly to the rating value you input.
        bot_account = account.Account(player_name,"pwd",True) #create a bot account
        # - This variable makes sure that this while loop does not run forever -
        run_ct = 0
        while (self.return_rating(bot_account) < rating and run_ct < 30) or (self.return_rating(bot_account) > rating + self.IMBALANCE_LIMIT and run_ct < 30):
            run_ct += 1 #increment our runtime counter (keeps us from running these loops infinitely)
            int_runct = 0 #each of these smaller loops can also encounter issues where they can't finish without a finite timeout.
            while self.return_rating(bot_account) < rating and int_runct < 10:
                bot_account.bot_purchase()
                int_runct += 1
            int_runct = 0 #each of these smaller loops can also encounter issues where they can't finish without a finite timeout.
            while self.return_rating(bot_account) > rating + self.IMBALANCE_LIMIT and int_runct < 10:
                bot_account.bot_refund()
                int_runct += 1
        return bot_account

    # - This function is where OFFLINE PvPvBot play BEGINS -
    def offline_play(self):
        # - Basic gameplay setup values -
        #   player_ct, bot_ct, bot difficulty (/ 2 = bot difficulty), money_start (^ amt), 
        #   exp_start (* self.CASH_MULTIPLIER = exp amt), keep_money, GFX Quality, battle type ("Regular"/"Experience"),
        #   music volume, SFX volume
        player_setup = [1, 8, 5, 250.0, 2, True, 8, "Regular", 3, 10]
        # - Controls: up, down, left, right, shoot, PTT, powerups 1-6, shells 1-4, cursor modifier
        controls = [] #[player 1 Controls() object, player 2 Controls() object, player 3 Controls() object...] - DEADZONE is stored as a global variable inside of controller.py, so I don't need to store it here.
        map_choice = [0] #maps are arranged by index number. I have to keep this value in a list to allow a function to change this value when passed through as a parameter.

        # - Load our saved settings into the above variables -
        try:
            #raise IndexError #uncomment this line, run the program, and close it normally to save new default settings without starting with the old ones.
            afile = open(path + "saves/offline_player_data.pkl","rb+")
            loaded_content = pickle.load(afile)
            player_setup = loaded_content[0]
            control_data = loaded_content[1]
            for x in range(0,len(control_data)):
                controls.append(controller.Controls(18,"kb"))
                controls[x].enter_data(control_data[x])
            map_choice = loaded_content[2]
            print("Succeeded in loading offline play preferences!")
        except Exception as e:
            print("An exception occurred: " + str(e))
            print("Failed to load offline play preferences. Continuing with defaults...")

        # - This value holds any data regarding all player performance screens for at the end of a battle -
        special_window_return = None

        # - This will *become* a list once Menu D is entered. It will hold all player accounts and their current state -
        account_list = None
        
        # - Idea: The following happens IN SEQUENCE:
        #   - Menu A:
        #       The leader chooses the number of players in the match, along with the number of bots.
        #       The leader chooses bot difficulty (bot rating)
        #       The leader chooses how much ^ each player gets to spend (including bots), and whether players keep what they have @ the end of a round/players get new $$ @ the end of a round.
        #       GFX quality is also chosen at this time by the leader so that the leader can prevent naughty guests from lagging his computer to death =) LOL
        initial_entry = True #this variable is used to tell whether the game needs to give player $$$ or not
        exit_loop = False #essentially the reverse of most programs' "running" variable; this also can have the value "back" for going back one menu.
        while not exit_loop:
            exit_loop = self.offline_menu_a(player_setup)
            #   - Menu B:
            #       The leader must help all players configure their controls (controllers/keyboards)
            while not exit_loop:
                if(not exit_loop):
                    exit_loop = self.offline_menu_b(controls, player_setup)
                    if(exit_loop == "back"): #we need to go back to menu A
                        exit_loop = False
                        break
                #   - Menu C:
                #       The leader chooses the map (which governs the number of teams in the match)
                while not exit_loop:
                    self.music.fadeout_track() #make sure no music starts until Menu D...and no music carries over from ingame...
                    if(not exit_loop):
                        exit_loop = self.offline_menu_c(map_choice, player_setup)
                        if(exit_loop == "back"):
                            exit_loop = False
                            break #we need to get back to menu B
                    #   - Menu D:
                    #       The screen splits into N number of screens, where N is the number of players the leader chose.
                    #       Each player gets to buy what he chooses with his money within a time limit (maybe 2 min 50 sec?) and refunds are 100% value refunds, unlike in online mode.
                    #       When all players have finished buying what they want OR time has run out, all players are matched into a game with the matchmaker from battle_server.
                    #       The bots will all buy as much as they can with the money they have in their accounts (this can happen almost anywhere, doesn't have to be in sequence).
                        if(not exit_loop):
                            data_pack = self.offline_menu_d(controls, player_setup, initial_entry, account_list, special_window_return)
                            exit_loop = data_pack[0]
                            account_list = data_pack[1]
                            initial_entry = False
                    #   GAME START!
                        if(not exit_loop):
                            data_pack = self.offline_game_start(controls, map_choice, player_setup, account_list)
                            exit_loop = data_pack[0]
                            #we still have account_list[] from Menu D. Combining account_list[] data with special_window_return[] data will allow us to find what battle outcome screen belongs to which player.
                            special_window_return = data_pack[1]

        # - Save our current game settings -
        try:
            control_data = []
            for x in range(0,len(controls)):
                control_data.append(controls[x].return_data())
            afile = open(path + "saves/offline_player_data.pkl","wb+")
            obj = [player_setup, control_data, map_choice]
            pickle.dump(obj,afile)
            afile.flush()
            afile.close()
            print("Succeeded in saving offline play preferences!")
        except Exception as e:
            print("An exception occurred: " + str(e))
            print("Failed to save offline play preferences. Exiting...")

    # - Beginning player setup menu for offline play -
    def offline_menu_a(self, setup_data):
        # - Setup Menu A -
        menua = menu.Menuhandler()
        menua.create_menu(["Player Count","Bot Count","","Bot Difficulty","","^ Per Player x" + str(int(self.CASH_MULTIPLIER)),"Additional ^ Per Player x" + str(int(self.CASH_MULTIPLIER / 10)),"EXP Per Player x" + str(int(self.CASH_MULTIPLIER)),"Keep Battle Revenue","","GFX Quality","","Battle Type","","Music Volume","SFX Volume","","Continue","","Exit"],
                       [[1,self.MAX_OFFLINE_PLAYERS],[0,self.MAX_OFFLINE_BOTS],["",""],[1,20],["",""],[0,self.MAX_OFFLINE_CASH],[0,9],[0,self.MAX_OFFLINE_EXP],["True","False"],["",""],[1,30],["",""],["Regular","Experience"],["",""],[0,10],[0,10],["",""],["",""],["",""],["",""]],
                       [],buttonindexes=[],name="TBO Offline Mode Player Setup")

        # - Load old setup_data values into the menu -
        menua.reconfigure_setting([1,self.MAX_OFFLINE_PLAYERS], str(setup_data[0]), setup_data[0], "Player Count")
        menua.reconfigure_setting([0,self.MAX_OFFLINE_BOTS], str(setup_data[1]), setup_data[1], "Bot Count")
        menua.reconfigure_setting([1,20], str(setup_data[2]), setup_data[2], "Bot Difficulty")
        menua.reconfigure_setting([0,self.MAX_OFFLINE_CASH], str(int(setup_data[3] / self.CASH_MULTIPLIER)), int(setup_data[3] / self.CASH_MULTIPLIER), "^ Per Player x" + str(int(self.CASH_MULTIPLIER)))
        menua.reconfigure_setting([0,9], str(int((setup_data[3] - self.CASH_MULTIPLIER * int(setup_data[3] / self.CASH_MULTIPLIER)) / (self.CASH_MULTIPLIER / 10))), int((setup_data[3] - self.CASH_MULTIPLIER * int(setup_data[3] / self.CASH_MULTIPLIER)) / (self.CASH_MULTIPLIER / 10)), "Additional ^ Per Player x" + str(int(self.CASH_MULTIPLIER / 10)))
        menua.reconfigure_setting([0,self.MAX_OFFLINE_EXP], str(setup_data[4]), setup_data[4], "EXP Per Player x" + str(int(self.CASH_MULTIPLIER)))
        menua.reconfigure_setting(["True","False"], str(setup_data[5]), ["True","False"].index(str(setup_data[5])), "Keep Battle Revenue")
        menua.reconfigure_setting([1,30], str(setup_data[6]), setup_data[6], "GFX Quality")
        menua.reconfigure_setting(["Regular","Experience"], setup_data[7], ["Regular","Experience"].index(setup_data[7]), "Battle Type")
        menua.reconfigure_setting([0,10], str(setup_data[8]), setup_data[8], "Music Volume")
        menua.reconfigure_setting([0,10], str(setup_data[9]), setup_data[9], "SFX Volume")

        # - Key configuration -
        directions = [10,11,12,13]
        shoot = 14
        shoot_timeout = time.time()
        keys = []
        fps = 30 #needed to control cursor speed

        running = True
        exit_loop = True #this flag tells whether we exited this loop to leave TBO or to continue to Offline Menu B.
        clock = pygame.time.Clock()
        cursorpos = [1,0]
        while running:
            # - Pygame event loop stuff -
            keys = self.controls.get_input()
            event_pack = controller.get_keys()
            running = not event_pack[0]
            if(event_pack[1] != None): #we requested a window resize?
                resize_dimensions = list(event_pack[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)

            # - Update the menu -
            menua.update(self.screen)

            # - Move the cursor -
            for x in keys:
                if(x in directions):
                     cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * menua.menu_scale
                     cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * menua.menu_scale

            # - Check for mouse movement or mouse click -
            for x in event_pack[2]:
                if(x.type == pygame.MOUSEMOTION):
                    cursorpos[0] = x.pos[0]
                    cursorpos[1] = x.pos[1]
                elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                    keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                elif(x.type == pygame.MOUSEBUTTONUP):
                    if(shoot in keys):
                        keys.remove(shoot)

            # - Handle clicking on menu objects -
            if(shoot in keys and time.time() - shoot_timeout > 0.25): #we shot at something (clicked on it)?
                shoot_timeout = time.time() #reset our shot timeout variable
                self.sfx.play_sound(self.GUNSHOT, [0,0],[0,0]) #play the gunshot sound effect
                clicked_button = menua.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                if(clicked_button[0][0] != None):
                    if(clicked_button[0][0] == 17): #continue to next menu
                        running = False
                        exit_loop = False
                    if(clicked_button[0][0] == 19): #exit
                        running = False
            
            # - Keep the cursor from moving offscreen -
            if(cursorpos[0] > self.screen.get_width()):
                cursorpos[0] -= self.screen.get_width()
            elif(cursorpos[0] < 0):
                cursorpos[0] += self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()
            elif(cursorpos[1] < 0):
                cursorpos[1] += self.screen.get_height()

            # - Update the values in setup_data[] to reflect our settings we just chose -
            grabbed_settings = menua.grab_settings(["Player Count","Bot Count","Bot Difficulty","^ Per Player x" + str(int(self.CASH_MULTIPLIER)),"Additional ^ Per Player x" + str(int(self.CASH_MULTIPLIER / 10)),"EXP Per Player x" + str(int(self.CASH_MULTIPLIER)),"Keep Battle Revenue","GFX Quality","Battle Type","Music Volume","SFX Volume"])
            setup_data[0] = grabbed_settings[0][1]
            setup_data[1] = grabbed_settings[1][1]
            setup_data[2] = grabbed_settings[2][1]
            setup_data[3] = int(grabbed_settings[3][1] * self.CASH_MULTIPLIER) + grabbed_settings[4][1] * int(self.CASH_MULTIPLIER / 10)
            setup_data[4] = grabbed_settings[5][1]
            setup_data[5] = eval(grabbed_settings[6][0])
            setup_data[6] = grabbed_settings[7][1]
            setup_data[7] = grabbed_settings[8][0]
            setup_data[8] = grabbed_settings[9][1]
            setup_data[9] = grabbed_settings[10][1]

            # - Set our music volume based on setup_data[8] -
            pygame.mixer.music.set_volume(setup_data[8] / 10)

            # - Set our SFX volume based on setup_data[9] -
            self.sfx.sound_volume = setup_data[9] / 10

            # - Draw everything and update the window border -
            self.screen.fill([0,0,0]) #clear screen
            menua.draw_menu([0,0],[self.screen.get_width(), self.screen.get_height()],self.screen,cursorpos) #draw menu
            # - Draw the cursor -
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * menua.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * menua.menu_scale)],int(3 * menua.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * menua.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * menua.menu_scale)],int(3 * menua.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * menua.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * menua.menu_scale),cursorpos[1]],int(3 * menua.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * menua.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * menua.menu_scale),cursorpos[1]],int(3 * menua.menu_scale))
            # - Update the screen and window border -
            pygame.display.flip()
            fps = clock.get_fps()
            pygame.display.set_caption("Tank Battalion Online - Offline Mode Setup - FPS: " + str(round(fps,1)))
            clock.tick(750)

        return exit_loop #this is True if we want to close TBO, and False if we want to continue playing in offline mode.

    # - Control configuration -
    def offline_menu_b(self, controls, setup_data):
        # - Setup Menu B -
        menub = menu.Menuhandler()
        # - The beginning menu needs to be configured carefully, since the number of buttons needed to configure each player will vary based on the number of players we chose in Menu A -
        button_names = ["","Back","","Continue","","Exit"]
        button_options = [["",""],["",""],["",""],["",""]]
        button_indexes = []
        for x in range(0,setup_data[0]):
            button_options.append(["",""])
            button_names.insert(0, "Player " + str(setup_data[0] - 1 - x) + " Controls") #I want player 1 to be player 0. I like index numbers, not counting numbers.
            button_indexes.append([x,x + 1])
        menub.create_menu(button_names, button_options, button_indexes, buttonindexes=[], name="TBO Offline Mode Controls Setup")
        # - Create control configuration menus for all players -
        key_config_names = ["Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1","Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6","Up","Left","Down","Right","Shoot","Escape Battle","Cursor Modifier","PTT Key"]
        for x in range(0,setup_data[0]):
            menub.create_menu(["Deadzone","KB/JS","JS Num","Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1","Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6","Up","Left","Down","Right","Shoot","Escape Battle","Cursor Modifier","PTT Key","","Back"],
                              [[1,9],["Keyboard","Joystick"],["0","0"],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],
                              [[22,0]], [], "TBO Offline Mode Player " + str(x) + " Controls Setup")
        # - Make sure that the controls[] list is long enough to accomodate as many players as we're adding -
        if(len(controls) < setup_data[0]):
            for x in range(0,setup_data[0] - len(controls)):
                controls.append(controller.Controls(18,"kb"))

        # - Load the correct values into each menu (menub.reconfigure_setting(SettingType, str, int, "Name")) -
        for x in range(0,setup_data[0]):
            menub.current_menu = x + 1
            menub.reconfigure_setting([1,9], str(int(controller.DEADZONE * 10)), int(controller.DEADZONE * 10), "Deadzone") #set the deadzone for each controller
            menub.reconfigure_setting(["Keyboard","Joystick"], ["Keyboard","Joystick"][["kb","ctrl"].index(controls[x].kb_ctrl)], ["kb","ctrl"].index(controls[x].kb_ctrl), "KB/JS") #set whether each controller is a keyboard or joystick
            for button in range(0,len(key_config_names)):
                if(controls[x].kb_ctrl == "kb"): #we need letters
                    key_str = "."
                    for b in range(0,len(menu.keys)):
                        if(menu.keys[b][0] == controls[x].buttons[button]):
                            key_str = menu.keys[b][1]
                else: #just print button numbers
                    key_str = "Button " + str(controls[x].buttons[button])
                menub.reconfigure_setting([key_str,key_str], key_str, 0, key_config_names[button])
        menub.current_menu = 0 #set our menu # back to 0 again so we start at the main key configuration menu

        # - Key configuration -
        directions = [10,11,12,13]
        shoot = 14
        shoot_timeout = time.time()
        keys = []
        fps = 30 #needed to control cursor speed

        # - Gameloop related variables -
        cursorpos = [1,0]
        clock = pygame.time.Clock()
        exit_loop = True
        running = True
        while running:
            # - Pygame event loop stuff -
            keys = self.controls.get_input()
            event_pack = controller.get_keys()
            running = not event_pack[0]
            if(event_pack[1] != None): #we requested a window resize?
                resize_dimensions = list(event_pack[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)

            # - Move the cursor -
            for x in keys:
                if(x in directions):
                     cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * menub.menu_scale
                     cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * menub.menu_scale

            # - Check for mouse movement or mouse click -
            for x in event_pack[2]:
                if(x.type == pygame.MOUSEMOTION):
                    cursorpos[0] = x.pos[0]
                    cursorpos[1] = x.pos[1]
                elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                    keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                elif(x.type == pygame.MOUSEBUTTONUP):
                    if(shoot in keys):
                        keys.remove(shoot)

            # - Handle clicking on menu objects -
            if(shoot in keys and time.time() - shoot_timeout > 0.25): #we shot at something (clicked on it)?
                shoot_timeout = time.time() #reset our shot timeout variable
                self.sfx.play_sound(self.GUNSHOT, [0,0],[0,0]) #play the gunshot sound effect
                clicked_button = menub.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                if(clicked_button[0][0] != None):
                    if(menub.current_menu == 0):
                        if(clicked_button[0][0] == 5 + setup_data[0]): #exit?
                            running = False
                        elif(clicked_button[0][0] == 3 + setup_data[0]): #continue to Menu C?
                            running = False
                            exit_loop = False
                        elif(clicked_button[0][0] == 1 + setup_data[0]): #go back one menu (B)?
                            running = False
                            exit_loop = "back"
                    elif(clicked_button[1] != 0): #we clicked on *something* in a key configuration menu (NOT menu 0)
                        selected_player = menub.current_menu - 1 #find which player we are configuring controls for
                        #KB/JS button (index 3)
                        if(clicked_button[0][0] == 1):
                            if(menub.grab_settings(["KB/JS"])[0][1] == 0): #keyboard?
                                controls[selected_player].kb_ctrl = "kb"
                            else: #joystick?
                                if(controls[selected_player].joystick_request(js_num=int(menub.grab_settings(["JS Num"])[0][0]))): #success?
                                    pass #we don't have to do anything actually...
                                else: #failed to get the JS we asked for. We need to revert the menu setting to "Keyboard"
                                    menub.reconfigure_setting(["Keyboard","Joystick"], "Keyboard", 0, "KB/JS")
                        #JS Num button (index 4)
                        elif(clicked_button[0][0] == 2):
                            # - Increase the JS num selected -
                            js_num = int(menub.grab_settings(["JS Num"])[0][0]) + 1
                            if(js_num >= self.MAX_OFFLINE_PLAYERS):
                                js_num = 0
                            menub.reconfigure_setting([str(js_num),str(js_num)], str(js_num), 0, "JS Num")
                            # - Check whether we need to DECREASE it since it's not available -
                            if(controls[selected_player].kb_ctrl == "kb"): #if we're using a keyboard, it doesn't matter if we change this setting.
                                pass #we don't need to do anything here...
                            else: #we need to check whether this JS is available since it's obvious we're planning on using the JS number we're asking for.
                                if(controls[selected_player].joystick_request(js_num=int(menub.grab_settings(["JS Num"])[0][0]))): #we got it!
                                    pass #we don't need to do anything here...
                                else: #failed to get the JS num, so decrease the JS num to return it to its original value.
                                    js_num = int(menub.grab_settings(["JS Num"])[0][0]) - 1
                                    if(js_num > self.MAX_OFFLINE_PLAYERS):
                                        js_num = 0
                                    menub.reconfigure_setting([str(js_num),str(js_num)], str(js_num), 0, "JS Num")
                                    menub.reconfigure_setting(["Keyboard","Joystick"], "Keyboard", 0, "KB/JS")
                        # - Actual key needs to be configured? -
                        elif(clicked_button[0][0] >= 3 and clicked_button[0][0] <= 20):
                            pygame.time.delay(250) #delay slightly, and empty all keys pressed during that time so that they don't count as key configuration keypresses.
                            controller.get_keys()
                            controller.empty_keys()
                            # - NOW we check what key has been pressed -
                            config = True
                            pygame.display.set_caption("Configure Player " + str(selected_player) + " Key Number " + str(clicked_button[0][0] - 3))
                            while config: #wait until the client configures the key
                                config = not controller.get_keys()[0]
                                if(config):
                                    config = not controls[selected_player].configure_key(clicked_button[0][0] - 3) #did we get a successful configuration?
                                # - Draw the "press a key to configure the button" words onscreen
                                self.screen.fill([0,0,0])
                                word_scale = (self.screen.get_width() / (len("Press any key...") * font.SIZE))
                                font.draw_words("Press any key...", [(self.screen.get_width() / 2 - len("Press any key...") * font.SIZE * word_scale * 0.5),10], [0,0,255], word_scale, self.screen)
                                pygame.display.flip()
                            pygame.time.delay(250) #250ms
                            controller.get_keys() #empty the event queue
                            controller.empty_keys() #empty the key list, and delay a small amount...

            # - Update the menu -
            menub.update(self.screen)
            if(menub.current_menu > 0): #we're in a key configuration menu? We need to update the keys displayed as our controls in the menu.
                selected_player = menub.current_menu - 1
                for button in range(0,len(key_config_names)):
                    if(controls[selected_player].kb_ctrl == "kb"): #we need letters
                        key_str = "."
                        for x in range(0,len(menu.keys)):
                            if(menu.keys[x][0] == controls[selected_player].buttons[button]):
                                key_str = menu.keys[x][1]
                    else: #just print button numbers
                        key_str = "Button " + str(controls[selected_player].buttons[button])
                    menub.reconfigure_setting([key_str,key_str], key_str, 0, key_config_names[button])

            # - Update the controller deadzone value the menu -
            if(menub.current_menu > 0):
                button_settings = menub.grab_settings(["Deadzone"])
                controller.DEADZONE = button_settings[0][1] / 10

            # - Keep the cursor from moving offscreen -
            if(cursorpos[0] > self.screen.get_width()):
                cursorpos[0] -= self.screen.get_width()
            elif(cursorpos[0] < 0):
                cursorpos[0] += self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()
            elif(cursorpos[1] < 0):
                cursorpos[1] += self.screen.get_height()
            
            # - Draw everything -
            self.screen.fill([0,0,0])
            menub.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)
            # - Draw the cursor -
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * menub.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * menub.menu_scale)],int(3 * menub.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * menub.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * menub.menu_scale)],int(3 * menub.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * menub.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * menub.menu_scale),cursorpos[1]],int(3 * menub.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * menub.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * menub.menu_scale),cursorpos[1]],int(3 * menub.menu_scale))
            pygame.display.flip()

            # - Update our FPS & window header -
            fps = clock.get_fps()
            clock.tick(750)
            pygame.display.set_caption("Tank Battalion Online - Offline Mode Setup - FPS: " + str(round(fps,1)))
        
        return exit_loop

    # - Map choice -
    def offline_menu_c(self, map_choice, player_setup):
        # - Menu setup -
        menuc = menu.Menuhandler()
        menuc.create_menu(["Next Map","Previous Map","","Map Number","Map Name","Team Count","","Back","","Continue","","Exit"],
                          [["",""],["",""],["",""],["0","0"],["",""],["2","2"],["",""],["",""],["",""],["",""],["",""],["",""]],
                          [], [], name="TBO Offline Mode Map Setup")

        # - Map draw setup -
        arena_data = import_arena.return_arena_numerical(map_choice[0])
        draw_arena = arena.Arena(arena_data[0][0], arena_data[0][1], [])
        draw_arena.clear_flag_locations()
        draw_arena.set_flag_locations(arena_data[0][6])

        # - Set our menu settings to what has been previously used in the Pickle save file -
        menuc.reconfigure_setting([str(map_choice[0]),str(map_choice[0])], str(map_choice[0]), map_choice[0], "Map Number")
        menuc.reconfigure_setting([arena_data[1],arena_data[1]], arena_data[1], 0, "Map Name")
        menuc.reconfigure_setting([str(len(arena_data[0][6])),str(len(arena_data[0][6]))], str(len(arena_data[0][6])), 0, "Team Count")

        # - Controls stuff -
        clock = pygame.time.Clock()
        fps = 30
        directions = [10,11,12,13]
        shoot = 14
        shoot_timeout = time.time()
        keys = []
        
        exit_loop = True
        running = True
        cursorpos = [0,0]
        while running:
            # - Pygame event loop stuff -
            keys = self.controls.get_input()
            event_pack = controller.get_keys()
            running = not event_pack[0]
            if(event_pack[1] != None): #we requested a window resize?
                resize_dimensions = list(event_pack[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                self.screen = pygame.display.set_mode(resize_dimensions, self.PYGAME_FLAGS)

            # - Move the cursor -
            for x in keys:
                if(x in directions):
                     cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * menuc.menu_scale
                     cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * menuc.menu_scale

            # - Check for mouse movement or mouse click -
            for x in event_pack[2]:
                if(x.type == pygame.MOUSEMOTION):
                    cursorpos[0] = x.pos[0]
                    cursorpos[1] = x.pos[1]
                elif(x.type == pygame.MOUSEBUTTONDOWN and shoot not in keys):
                    keys.append(shoot) #we're going to insert shoot into keys...this is a quick way to use the same code as pressing E for choosing a menu option with the mouse.
                elif(x.type == pygame.MOUSEBUTTONUP):
                    if(shoot in keys):
                        keys.remove(shoot)

            # - Handle clicking on menu objects -
            if(shoot in keys and time.time() - shoot_timeout > 0.25): #we shot at something (clicked on it)?
                shoot_timeout = time.time() #reset our shot timeout variable
                self.sfx.play_sound(self.GUNSHOT, [0,0],[0,0]) #play the gunshot sound effect
                clicked_button = menuc.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                if(clicked_button[0][0] == 0): #next map?
                    if(map_choice[0] < len(import_arena.arena_libraries) - 1): #we are free to increment our map counter since we won't get an IndexError.
                        map_choice[0] += 1
                        menuc.reconfigure_setting([str(map_choice[0]),str(map_choice[0])], str(map_choice[0]), map_choice[0], "Map Number")
                        arena_data = import_arena.return_arena_numerical(map_choice[0])
                        draw_arena.arena = arena_data[0][0]
                        draw_arena.tiles = arena_data[0][1]
                        draw_arena.clear_flag_locations()
                        draw_arena.set_flag_locations(arena_data[0][6])
                        menuc.reconfigure_setting([arena_data[1],arena_data[1]], arena_data[1], 0, "Map Name")
                        menuc.reconfigure_setting([str(len(arena_data[0][6])),str(len(arena_data[0][6]))], str(len(arena_data[0][6])), 0, "Team Count")
                elif(clicked_button[0][0] == 1): #previous map?
                    if(map_choice[0] <= 0): #we're NOT decreasing our map # if we're already at 0.
                        pass
                    else: #we can decrease it and update the map # displayed as well as the data stored in draw_arena.
                        map_choice[0] -= 1
                        menuc.reconfigure_setting([str(map_choice[0]),str(map_choice[0])], str(map_choice[0]), map_choice[0], "Map Number")
                        arena_data = import_arena.return_arena_numerical(map_choice[0])
                        draw_arena.arena = arena_data[0][0]
                        draw_arena.tiles = arena_data[0][1]
                        draw_arena.clear_flag_locations()
                        draw_arena.set_flag_locations(arena_data[0][6])
                        menuc.reconfigure_setting([arena_data[1],arena_data[1]], arena_data[1], 0, "Map Name")
                        menuc.reconfigure_setting([str(len(arena_data[0][6])),str(len(arena_data[0][6]))], str(len(arena_data[0][6])), 0, "Team Count")
                elif(clicked_button[0][0] == 7): #back to menu B?
                    running = False
                    exit_loop = "back"
                elif(clicked_button[0][0] == 9): #continue?
                    running = False
                    exit_loop = False
                elif(clicked_button[0][0] == 11): #exit?
                    running = False
            
            # - Keep the cursor from moving offscreen -
            if(cursorpos[0] > self.screen.get_width()):
                cursorpos[0] -= self.screen.get_width()
            elif(cursorpos[0] < 0):
                cursorpos[0] += self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()
            elif(cursorpos[1] < 0):
                cursorpos[1] += self.screen.get_height()

            # - Update the menu -
            menuc.update(self.screen)

            # - Draw everything, beginning with the menu -
            self.screen.fill([0,0,0])
            menuc.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)
            # - Draw the map we selected onscreen -
            bricks = []
            for x in arena_data[0][3]:
                bricks.append(x)
            for x in arena_data[0][4]:
                bricks.append(x)
            minimap_surface = draw_arena.draw_minimap(bricks)
            scaling_factor = minimap_surface.get_width() / minimap_surface.get_height() #this is a unit multiplier so that I can match the vertical scale factor to the horizontal scale factor I choose
            hscale = int(self.screen.get_width() / 3)
            if(hscale / scaling_factor > self.screen.get_height() / 3): #is our image going to be too tall if we use hscale as a vertical scaling factor?
                hscale = int(self.screen.get_height() / 3 * scaling_factor) #make sure it isn't so that the player can see the WHOLE map preview, not just the top three quarters.
            surf_size = [hscale, int(hscale * (1/scaling_factor))] #choose a horizontal scale factor and make the vertical match it
            minimap_surface = pygame.transform.scale(minimap_surface, surf_size) #use the scale factor to scale up the minimap
            pygame.draw.rect(minimap_surface, [255,255,255], [0,0,minimap_surface.get_width(),minimap_surface.get_height()], math.ceil(2 * menuc.menu_scale))
            centered_pos = [int(self.screen.get_width() / 2), int(self.screen.get_height() * 0.75)] #find the center of our screen
            centered_pos[0] -= int(minimap_surface.get_width() / 2) #take into account the dimensions of the minimap surface
            centered_pos[1] -= int(minimap_surface.get_height() / 2)
            self.screen.blit(minimap_surface, centered_pos) #copy the scaled minimap to the screen so that it is centered
            # - Draw the cursor -
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * menuc.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * menuc.menu_scale)],int(3 * menuc.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * menuc.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * menuc.menu_scale)],int(3 * menuc.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * menuc.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * menuc.menu_scale),cursorpos[1]],int(3 * menuc.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * menuc.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * menuc.menu_scale),cursorpos[1]],int(3 * menuc.menu_scale))
            pygame.display.flip()

            # - Update the clock and the display border -
            clock.tick(750)
            fps = clock.get_fps()
            pygame.display.set_caption("Tank Battalion Online - Offline Mode Setup - FPS: " + str(round(fps,1)))
        
        return exit_loop

    # - Store -
    def offline_menu_d(self, controls, player_setup, initial_entry=False, player_accts=None, special_window_return=None):
        # - We need to spawn player_ct number of accounts, load them with money_start * self.CASH_MULTIPLIER ^, and let them buy what they want with it in the store.
        #   This requires the use of a special library I have made which allows threads OTHER than the main thread to utilize pygame function calls.
        internal_display_size = [math.floor(self.screen.get_width() / math.ceil(math.sqrt(player_setup[0]))), math.floor(self.screen.get_height() / math.ceil(math.sqrt(player_setup[0])))]
        sound_names = [str(path + "../../sfx/gunshot_01.wav"), str(path + "../../sfx/driving.wav"), str(path + "../../sfx/thump.wav"), str(path + "../../sfx/explosion_large.wav"), str(path + "../../sfx/crack.wav")]
        ph = pygame_multithread.PygameHandler(player_setup[0], [self.screen.get_width(), self.screen.get_height()], internal_display_size, sound_names, 18)
        ph.update_surface_sizes()
        ph.update_surface_positions()

        # - Enter all controls into the PygameHandler so it can handle all our inputs for us -
        for x in range(0,player_setup[0]):
            ph.update_controller(x, controls[x].return_data())

        # - All threads need to be able to see this value...to keep it updated for all threads if I pass it through as a parameter, it needs to be in a list -
        running = [True]

        # - This tells us which threads are still running (one flag for each thread) -
        thread_running = []
        for x in range(0,player_setup[0]):
            thread_running.append(True)

        # - Generate all our player accounts with the correct amount of cash -
        if(initial_entry):
            player_accts = []
            for x in range(0,player_setup[0]):
                player_accts.append(account.Account("Player " + str(x), "Player " + str(x)))
        elif(len(player_accts) < player_setup[0]): #a player *could* have changed player count...then we'd have to add new accounts.
            for x in range(len(player_accts), player_setup[0]):
                player_accts.append(account.Account("Player " + str(x), "Player " + str(x)))
                #Make sure they start with some $$$ and EXP
                player_accts[len(player_accts) - 1].cash = float(player_setup[3])
                player_accts[len(player_accts) - 1].experience = player_setup[4] * self.CASH_MULTIPLIER
        for x in range(0,player_setup[0]):
            if(initial_entry or not player_setup[5]): #Either if we want FIXED cash for ALL rounds OR we're doing our FIRST round, we need to set all account cash to a certain amount.
                player_accts[x].cash = float(player_setup[3])
                player_accts[x].experience = player_setup[4] * self.CASH_MULTIPLIER
                player_accts[x].shells = [0,0,0,0]
                player_accts[x].powerups = [None, None, None, None, None, None]
                player_accts[x].upgrades = [0,0,0,0]
                player_accts[x].specialization = 0

        # - Start all our threads running -
        server_engine = battle_server.BattleEngine(False)
        battle_clients = []
        dummy_socks = []
        server_socks = []
        for x in range(0,player_setup[0]):
            dummy_socks.append(netcode.DummySocket())
            server_socks.append(netcode.DummySocket())
            server_socks[x].settimeout(5.0) #make sure the server socket timeouts are 5s rather than 7.5s (client timeout)
            dummy_socks[x].connect(server_socks[x])
            server_socks[x].connect(dummy_socks[x])
            battle_clients.append(BattleEngine("dummy IP", 50613472, autostart=False))
            battle_clients[x].sfx.sound_volume = player_setup[9] / 10
            _thread.start_new_thread(battle_clients[x].lobby_frontend, (ph, dummy_socks[x], running, x, thread_running))
            # - Find which special_window from special_window_return[] corresponds to this player -
            special_window_player = None
            if(special_window_return != None): #there are special windows?
                for find_window in range(0,len(special_window_return)):
                    if(special_window_return[find_window][0] == player_accts[x].name and special_window_return[find_window][1] == player_accts[x].password):
                        special_window_player = special_window_return[find_window][2]
            _thread.start_new_thread(server_engine.lobby_server, ([player_accts[x], server_socks[x]], special_window_player, running))

        # - Start some music! -
        if(len(self.music_files[0]) > 0):
            music_track = random.randint(0,len(self.music_files[0]) - 1)
            self.music.transition_track(self.music_files[0][music_track])

        # - Make sure that sound effects can actually be played and heard -
        ph.reset_idnum()

        # - Main loop! -
        fps_clock = pygame.time.Clock()
        exit_loop = False
        while running[0]:
            # - Pygame event handler stuff -
            window_data = ph.clock()
            running[0] = not window_data[0]
            exit_loop = not running[0]
            if(window_data[1] != None): #resize?
                resize_dimensions = list(window_data[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                ph.screen = pygame.display.set_mode(resize_dimensions, pygame.RESIZABLE)
                ph.update_surface_sizes()
                ph.update_surface_positions()

            # - Check if we should stop playing because the threads have all stopped -
            if(running[0]):
                still_run = False
                none_found = False
                for x in range(0,len(thread_running)):
                    still_run = thread_running[x]
                    if(still_run):
                        break
                    elif(still_run == None): #if none_found == True, we know that we need to enter battle, not exit the game.
                        none_found = True
                if(not still_run and none_found == True): #all players are ready for battle or left the game? We're gonna start!
                    #   (and the people who clicked exit...well they're gonna be dragged back into the game anyways since we saved their account data)
                    running[0] = False #exit_loop will still be False when we leave this loop, so we'll be able to tell whether we want to leave the game or if we want to enter battle.
                else:
                    running[0] = still_run
                    exit_loop = not running[0]

            # - Update our music system -
            queue = not self.music.clock() #returns False if we need to queue more tracks
            if(queue and len(self.music_files[0]) > 0): #queue a new random track
                music_track += 1
                if(music_track > len(self.music_files[0]) - 1):
                    music_track = 0
                self.music.queue_track(self.music_files[0][music_track])

            # - Update the display -
            ph.draw()
            fps_clock.tick(750)
            pygame.display.set_caption("Tank Battalion Online - Offline Mode Store - FPS: " + str(round(fps_clock.get_fps(),1)))

        pygame.time.delay(5000 + 250 * player_setup[0]) #I have a nice long wait in here for wayward processes to finish up their final loop iterations before I end this function.
        return [exit_loop, player_accts]

    # - Game start function -
    def offline_game_start(self, controls, map_choice, player_setup, accounts):
        # - We need to spawn player_ct number of accounts, load them with money_start * self.CASH_MULTIPLIER ^, and let them buy what they want with it in the store.
        #   This requires the use of a special library I have made which allows threads OTHER than the main thread to utilize pygame function calls.
        internal_display_size = [math.floor(self.screen.get_width() / math.ceil(math.sqrt(player_setup[0]))), math.floor(self.screen.get_height() / math.ceil(math.sqrt(player_setup[0])))]
        sound_names = [str(path + "../../sfx/gunshot_01.wav"), str(path + "../../sfx/driving.wav"), str(path + "../../sfx/thump.wav"), str(path + "../../sfx/explosion_large.wav"), str(path + "../../sfx/crack.wav")]
        ph = pygame_multithread.PygameHandler(player_setup[0], [self.screen.get_width(), self.screen.get_height()], internal_display_size, sound_names, 18)
        ph.update_surface_sizes()
        ph.update_surface_positions()

        # - Enter all controls into the PygameHandler so it can handle all our inputs for us -
        for x in range(0,player_setup[0]):
            ph.update_controller(x, controls[x].return_data())

        # - Set our GFX value correctly -
        GFX.gfx_quality = player_setup[6] / 20 #this ranges from 1/20 to 1.5 (enough to lag a powerful PC)

        # - All threads need to be able to see this value...to keep it updated for all threads if I pass it through as a parameter, it needs to be in a list -
        running = [True]

        # - This tells us which threads are still running (one flag for each thread) -
        thread_running = []
        for x in range(0,player_setup[0]):
            thread_running.append(True)

        # - Get some sockets set up, along with a server engine and a list of all players -
        server_engine = battle_server.BattleEngine(False)
        server_engine.offline = True
        battle_clients = []
        players = [] #this is a list of [account, client socket] objects which the matchmaker uses.
        dummy_socks = [] #this is a list of all client sockets.
        server_socks = []
        for x in range(0,player_setup[0]):
            dummy_socks.append(netcode.DummySocket())
            server_socks.append(netcode.DummySocket())
            server_socks[x].settimeout(5.0) #make sure the server socket timeouts are 5s rather than 7.5s (client timeout)
            dummy_socks[x].connect(server_socks[x])
            server_socks[x].connect(dummy_socks[x])
            battle_clients.append(BattleEngine("dummy IP", 50613472, autostart=False))
            battle_clients[x].sfx.sound_volume = player_setup[9] / 10
            players.append([accounts[x], server_socks[x]])

        # - Make a match now -
        server_engine.ac_enable = False
        server_engine.MIN_URGENCY = 0.00001
        server_engine.MIN_WAIT_ADD_URGENCY = 0.000011
        chosen_map = import_arena.return_arena_numerical(map_choice[0])
        team_ct = len(chosen_map[0][6])
        # - Engine call: matchmake(player_queue, odd_allowed=False, rating=False, urgency=1.0, target_bot_ct=None, forced_team_ct=None) -
        #   player_queue is a list: [ [account, client socket], [account, client socket] ... ]
        server_engine.RULES = ["bot_rating[0] >= self.IMBALANCE_LIMIT"]
        server_engine.PLAYER_RULES = []
        print("[MATCH] Attempting to make a match...")
        match = server_engine.matchmake(players, odd_allowed=True, rating=player_setup[5], urgency=0.00001, target_bot_ct=player_setup[1], forced_team_ct=team_ct, target_bot_rating=player_setup[2] / 2)

        # - Start all client/server threads, beginning with the ALL the server's threads -
        print("[THREAD] Starting all threads, beginning with the server...")
        special_window_return = [] #this holds the special_window values we need to pass to all clients once they get back into the store
        _thread.start_new_thread(server_engine.battle_type_functions[["Regular","Experience"].index(player_setup[7])], (match, chosen_map[1], special_window_return, running)) #[type]_battle_server(players, forced_map=None)
        # - Start all client threads (each one of these threads branches out into a total of 3...so for a 3-player game, there's 9 threads just for client stuff lol -
        for x in range(0,player_setup[0]):
            _thread.start_new_thread(battle_clients[x].battle_client, (ph, dummy_socks[x], x, thread_running, running))

        print("[MATCH] Game start!")

        # - Start some music! -
        if(len(self.music_files[2]) > 0):
            music_track = random.randint(0,len(self.music_files[2]) - 1)
            self.music.transition_track(self.music_files[2][music_track])

        # - Make sure that sound effects can actually be played and heard -
        ph.reset_idnum()

        # - Main loop! -
        fps_clock = pygame.time.Clock()
        exit_loop = False
        while running[0]:
            # - Pygame event handler stuff -
            window_data = ph.clock()
            running[0] = not window_data[0]
            if(not running[0]): #if we clicked the X, we probably don't want to keep playing...we're LEAVING.
                exit_loop = True
            if(window_data[1] != None): #resize?
                resize_dimensions = list(window_data[1])
                if(resize_dimensions[0] < self.min_screen_size[0]): #make sure that we don't resize beyond the minimum screen size allowed (this can cause errors if we don't do this)
                    resize_dimensions[0] = self.min_screen_size[0]
                if(resize_dimensions[1] < self.min_screen_size[1]):
                    resize_dimensions[1] = self.min_screen_size[1]
                ph.screen = pygame.display.set_mode(resize_dimensions, pygame.RESIZABLE)
                ph.update_surface_sizes()
                ph.update_surface_positions()

            # - Check if we should stop playing because the threads have all stopped -
            if(running[0]):
                if(True in thread_running):
                    pass
                else:
                    running[0] = False

            # - Update our music system -
            queue = not self.music.clock() #returns False if we need to queue more tracks
            if(queue and len(self.music_files[2]) > 0): #queue a new random track
                music_track += 1
                if(music_track > len(self.music_files[2]) - 1):
                    music_track = 0
                self.music.queue_track(self.music_files[2][music_track])

            # - Update the display -
            ph.draw()
            fps_clock.tick(750)
            pygame.display.set_caption("Tank Battalion Online - Offline Mode Ingame - FPS: " + str(round(ph.get_avg_fps(),1)))

        # - If we formally disconnect all sockets, the various game threads will end significantly sooner -
        for x in range(0,len(dummy_socks)):
            dummy_socks[x].disconnect()
        pygame.time.delay(5000 + 250 * (player_setup[0] + player_setup[1])) #we need to delay here so that any wayward processes which need to modify special_window_return[] are able to before this thread ends
        return [exit_loop, special_window_return]

### - Test -
##engine = BattleEngine(None,5031)
##pygame.quit() #exit pygame
