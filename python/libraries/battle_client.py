##"battle_client.py" library ---VERSION 0.24---
## - Handles battles (main game loops, lobby stuff, and game setup) for CLIENT ONLY -
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

#Python external libraries:
import _thread, socket, pygame, time, sys, random, math
#set up external directories
sys.path.insert(0, "../maps")
#My own proprietary libraries:
import account, menu, HUD, netcode, font, arena, GFX, import_arena, entity, arena as arena_lib, controller

# - This is a global which tells us the path to find the directory battle_client is stored in -
path = ""

def init(path_str=""):
    global path
    path = path_str
    entity.path = path_str
    import_arena.path = path_str

class BattleEngine():
    def __init__(self,IP,PORT,autostart=True):
        self.buffersize = 10

        # - Default key configuration settings -
        self.controls = controller.Controls(4 + 6 + 4 + 1 + 1 + 1,"kb") #4: shells - 6: powerups - 4: movement - 1: shoot  - 1: ESC key - 1: Crosshair modifier
        self.controls.buttons = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE]

        # - Packet formats (what we recieve from the server) -
        self.LOBBY_PACKETS = [["<class 'bool'>", "<class 'list'>", "..."], ["<class 'NoneType'>", "<class 'list'>", "..."], ["<class 'bool'>", "<class 'str'>", "<class 'list'>", "..."]]
        self.MATCH_PACKET = ["<class 'bool'>", "<class 'list'>", "<class 'int'>"] #[in_battle(True/False), viewing_players data list, player_count]
        self.GAME_PACKET = ["<class 'str'>", "...", "...", "...", "...", "..."] #the last sublists of the game_packet do not get transmitted every packet...and the data isn't a consistent type either =(

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
        
        # - Create a dummy account object we can use to easily display our stats in the lobby using enter_data() -
        self.acct = account.Account("name","pwd")
        self.acct_lock = _thread.allocate_lock()

        # - Global Game-round necessary stuff -
        self.running = True #when this goes False, the whole GAME is going down...
        self.running_lock = _thread.allocate_lock()

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

        # - Matchmaker constants -
        self.EXP_WEIGHT = 0.0005 #this defines the overall power of a player (more EXP = more experienced player = more strategic = more dangerous)
        self.UPGRADE_WEIGHT = 0.5 #this defines the overall power of a player (more upgrades = more powerful tank)
        self.CASH_WEIGHT = 0.0005 #this defines the overall power of a player (more cash = more disk shells the player can buy = more dangerous)
        self.SHELLS_WEIGHT = [0.025, 0.035, 0.05, 0.075] #this defines the overall power of a player (more powerful shells = more dangerous)
        self.POWERUP_WEIGHT = 0.10 / 6 #this defines the overall power of a player (more powerups = more dangerous)
        self.SPECIALIZATION_WEIGHT = 0.025 #this defines the overall power of a player (more specialized = potentially more dangerous...?)
        self.IMBALANCE_LIMIT = 2.50 #the maximum imbalance of rating points a match is allowed to have to be finalized.

        # - Autostart -
        if(autostart):
            # - Display stuff / game graphics stuff -
            self.screen = pygame.display.set_mode([320,240], pygame.RESIZABLE)

            # - Start the login script -
            self.login(IP,PORT)

    def login(self,IP,PORT):
        valid = False
        while not valid:
            login_username_input = menu.get_input(self.screen,"Please enter your username")
            if(login_username_input == None): #player clicked X?
                return None #finish the function; quit the application
            login_password_input = menu.get_input(self.screen,"Please enter your password")
            if(login_username_input == None or login_password_input == None): #player clicked X?
                return None #finish the function; quit the application
            else:
                valid = self.connect_server(IP,PORT,login_username_input,login_password_input)

    def connect_server(self,IP,PORT,username,password):
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
            netcode.send_data(self.Cs, self.buffersize, [username, password])

            #Now, we wait 0.5 seconds and check whether the server closed the socket. If the server did, we got the wrong password/username.
            #If not, we probably got it right and we can continue!
            if(self.Cs._closed):
                print("Server connection failed!")
                connection = False
            else:
                #we're connected!
                print("Connection to " + IP + " Successful!")
                connection = True
                self.lobby_frontend()
        return connection

    def lobby_client(self): #this is the backend for the lobby - netcode.
        with self.request_lock:
            self.request = [None]
        while self.running:
            if(self.request == [False]):
                while (self.request == [False]): #we get stuck in this loop until self.request != [False] - This way we can keep this thread running without needing to halt it...
                    time.sleep(0.2)
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

                with self.special_window_lock: #update the special window
                    if(self.response[0][len(self.response[0]) - 1] != None):
                        if(self.special_window != None):
                            for x in range(0,len(self.special_window)):
                                del(self.special_window[0])
                        else:
                            self.special_window = []
                        for x in range(0,len(self.response[0][len(self.response[0]) - 1])):
                            self.special_window.append(self.response[0][len(self.response[0]) - 1][x])
                    else:
                        self.special_window = None
            else: #check if we're getting matchmaking packets. If we are, we start up the matchmaking routine by changing self.request, self.response...to make the lobby_frontend() go into queue.
                if(netcode.data_verify(self.response, self.MATCH_PACKET)):
                    self.request_pending = True #just toss us into whatever queue we were supposed to enter...

        self.Cs.close() #close our socket connection and delete it so the server will save our data
        del(self.Cs)

    def lobby_frontend(self): #this is the GUI for the lobby.
        _thread.start_new_thread(self.lobby_client,()) #start up the netcode for the lobby!!
        lobby_menu = menu.Menuhandler() #create a menu handler
        # - Create the various lobby menus -
        lobby_menu.create_menu(["Battle","Store","Settings","Exit"],[["",""],["",""],["",""],["",""]],[[1,1],[0,6],[2,7]],[],"Tank Battalion Online Lobby")
        lobby_menu.create_menu(["Purchase Mode","Shells","Upgrades","Specialization","Powerups","Back"],[["buy","refund"],["",""],["",""],["",""],["",""],["",""]],[[5,0],[1,2],[2,3],[3,4],[4,5]],[],"Tank Battalion Online Store")
        lobby_menu.create_menu(["^ Available","Hollow","Regular","Explosive","Disk","Back"],[["",""],["0","0"],["0","0"],["0","0"],["0","0"],["",""]],[[5,1]],[],"Tank Battalion Online Store - Shells")
        lobby_menu.create_menu(["^ Available","Gun - Damage","Loading Mechanism - RPM","Armor","Engine - More Speed","Back"],[["",""],["0","0"],["0","0"],["0","0"],["0","0"],["",""]],[[5,1]],[],"Tank Battalion Online Store - Upgrades")
        lobby_menu.create_menu(["EXP Available","Current Specialization","Specialize Light","Specialize Heavy","Back"],[["",""],["0","0"],["",""],["",""],["",""]],[[4,1]],[],"Tank Battalion Online Store - Specialization")
        lobby_menu.create_menu(["^ Available","Improved Fuel +35% Speed","Fire Extinguisher -10% Speed","Dangerous Loading +50% RPM -10% HP","Explosive Tip +25% DMG. -5% RPM -5% PN.",
                                "Amped Gun +25% PN. -10% HP","Extra Armor +50% Armor -50% Speed","Back"],[["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],[[7,1]],[],"Tank Battalion Online Store - Powerups")
        lobby_menu.create_menu(["Back","Battle Type","Battle"],[["",""],["Unrated Battle","Experience Battle"],["",""]],[[0,0]],[],"Tank Battalion Online Battle Menu") #this line will need to be changed based on what battle modes are available.
        lobby_menu.create_menu(["Back","Key config","Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1","Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6","Up","Left","Down","Right","Shoot","Escape Battle","Cursor Modifier"],[["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],[[0,0]],[],"Tank Battalion Online Settings")

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
            [[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None],[None]],
            ]

        # - Create a special second menu with a menu depth of 1 (no sub menus) for special stuff like end-game results -
        special_menu = menu.Menuhandler()

        # - Brief desctiption of what every button does in the game -
        damage_numbers = entity.Bullet(None, "", 0, 0, [1,1,1,1,1], None)
        damage_numbers = damage_numbers.shell_specs[:]
        button_descriptions = [
            ["Choose a battle mode   -","Purchase items for battle   -","Change your settings   -","Are you sure you want to leave..."],
            ["Choose whether you are planning to refund or purchase items   -","","","","",""],
            ["^ can be earned in battles or purchased.","Hollow shell - Deals " + str(damage_numbers[0][0]) + " damage at " + str(damage_numbers[0][1]) + " penetration",
                 "Regular shell - Deals " + str(damage_numbers[1][0]) + " damage at " + str(damage_numbers[1][1]) + " penetration",
                 "Explosive shell - Deals " + str(damage_numbers[2][0]) + " damage at " + str(damage_numbers[2][1]) + " penetration",
                 "Disk shell - Deals " + str(damage_numbers[3][0]) + " damage at " + str(damage_numbers[3][1]) + " penetration",""],
            ["^ can be earned in battles or purchased.","","","","",""],
            ["EXP can be earned by playing rating battles.","This is the current state of your tank   -","Make your tank faster, shoot with more RPM and penetration but with less damage.","Make your tank slower, decrease RPM and penetration, but increase damage significantly.",""],
            ["^ can be earned in battles or purchased.","","","","","","This powerup acts a little strangely - If you have armor left, that armor gets increased by 50% temporarily. If you have no armor left, you will recieve no benefit from using this powerup, because 0 armor times 1.5 equals 0 armor.",""],
            ["Back to the lobby menu   -","Change the type of battle you want to enter   -","Enter the battle queue   -"],
            ["","","","","","","","","","","","","","","","","","",""]
            ]

        # - Create an HUD to display the descriptions of menu items -
        hud = HUD.HUD()
        hud.tick_speed = 6
        hud.default_display_size = [320,240]
        hud.add_HUD_element("scrolling text",[[0,220],[20,16],[[255,255,255],[100,100,100],[0,255,0]],"Demo text which is scrolling"])

        # - Reference index of the names of lobby_menu index 3 (upgrades) so that I can change their values -
        upgrade_names = ["Gun - Damage","Loading Mechanism - RPM","Armor","Engine - More Speed"]
        # - Reference index of the names of lobby_menu index 2 (shells) so that I can change their values -
        shell_names = ["Hollow","Regular","Explosive","Disk"]
        # - Reference index of the names of lobby_menu index 5 (powerups) so that I can change their values -
        powerup_names = ["Improved Fuel +35% Speed","Fire Extinguisher -10% Speed","Dangerous Loading +50% RPM -10% HP","Explosive Tip +25% DMG. -5% RPM -5% PN.",
                        "Amped Gun +25% PN. -10% HP","Extra Armor +50% Armor -50% Speed"]
        # - Reference names for key configurations -
        key_configuration_names = [
            "Shell 1","Shell 2","Shell 3","Shell 4","Powerup 1","Powerup 2","Powerup 3","Powerup 4","Powerup 5","Powerup 6","Up","Left","Down","Right","Shoot","Escape Battle","Cursor Modifier"
            ]

        cursorpos = [0,0] #where is our cursor?

        # - Key configuration -
        directions = self.controls.buttons[10:14]
        shoot = self.controls.buttons[14]

        #Things that will need to be changed when I add 2/3p split screen online modes:
        # - Multiple players' lobby data being transmitted through one socket (perhaps use a list with all player connections for data?)
        # - pygame.display.set_caption() may only happen in one thread
        # - pygame.display.flip() may only get called by one thread
        # - All threads need to draw to a pygame.Surface() not pygame.display.set_mode() returned object.

        pygame.display.set_caption("Tank Battalion Online Lobby") #this will need to be disabled for 2/3 player modes, because otherwise this will not be stable...

        # - Timing stuff for keypress/cursor management and shooting -
        debounce = time.time()
        fps = 30

        #get da fps
        clock = pygame.time.Clock()

        while self.running:
            if(self.special_window == None): #this stuff only needs to happen if we're not currently utilizing the special menu.
                # - Update bullet damage strings -
                button_descriptions[2] = ["^ can be earned in battles or purchased.","Hollow shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[0][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[0][1])) + " penetration",
                     "Regular shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[1][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[1][1])) + " penetration",
                     "Explosive shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[2][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[2][1])) + " penetration",
                     "Disk shell - Deals " + str(int(self.acct.damage_multiplier * damage_numbers[3][0])) + " damage at " + str(int(self.acct.penetration_multiplier * damage_numbers[3][1])) + " penetration",""]
                
                # - If we're in the battle menu, make sure the battle command is configured properly -
                if(lobby_menu.current_menu == 6): #we're in the battle selection screen?
                    battle_settings = lobby_menu.grab_settings(["Battle Type"])
                    button_actions[6][2] = ["battle",battle_settings[0][0]]
                
                # - Check if time.time() - request_pending is greater than our maximum ping allowance (2 seconds? I'm gonna reference the constant in netcode.py) -
                with self.request_pending_lock:
                    if(self.request_pending != True and self.request_pending != False and time.time() - self.request_pending > netcode.DEFAULT_TIMEOUT):
                        self.request_pending = False

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
                            opt_str = str(owned) + "/1 " + str(round(self.acct.purchase("powerup",x,True),2))
                        else:
                            opt_str = str(owned) + "/1 " + str(round(self.acct.refund("powerup",x,True),2))
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,powerup_names[x])

                # - Update our key configuration menu -
                if(lobby_menu.current_menu == 7):
                    for x in range(0,len(self.controls.buttons)):
                        opt_str = "."
                        for b in range(0,len(menu.keys)):
                            if(menu.keys[b][0] == self.controls.buttons[x]):
                                opt_str = menu.keys[b][1]
                                break
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,key_configuration_names[x])
                    
                #update our menu's scale
                lobby_menu.update(self.screen)

                # - Update the value of specialization in menu 4, index 0 + EXP counter -
                if(lobby_menu.current_menu == 4):
                    opt_str = str(round(self.acct.experience,2)) + " EXP" #EXP counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"EXP Available")
                    opt_str = self.specialization_mapper[self.acct.specialization + self.specialization_offset] #specialization settings
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Current Specialization")
                    # - Update the costs for specializing heavy/light -
                    light = str(self.acct.purchase("specialize",1,True)) + " EXP"
                    heavy = str(self.acct.purchase("specialize",-1,True)) + " EXP"
                    lobby_menu.reconfigure_setting([light,light],light,0,"Specialize Light")
                    lobby_menu.reconfigure_setting([heavy,heavy],heavy,0,"Specialize Heavy")

                # - Update the value of tank upgrades + ^ counter -
                if(lobby_menu.current_menu == 3):
                    opt_str = str(round(self.acct.cash,2)) + " ^" #configure the cash counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"^ Available")
                    for x in range(0,len(self.acct.upgrades)): #configure the upgrades counter
                        if(purchase_mode == "buy"):
                            opt_str = str(self.acct.upgrades[x]) + "/" + str(self.acct.upgrade_limit) + " " + str(round(self.acct.purchase("upgrade",x,True),2)) + "^"
                        else:
                            opt_str = str(self.acct.upgrades[x]) + "/" + str(self.acct.upgrade_limit) + " " + str(round(self.acct.refund("upgrade",x,True),2)) + "^"
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,upgrade_names[x])

                # - Update the value of shells + ^ counter -
                if(lobby_menu.current_menu == 2):
                    opt_str = str(round(self.acct.cash,2)) + " ^" #configure the cash counter
                    lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"^ Available")
                    for x in range(0,len(self.acct.shells)): #configure the shells counter
                        if(purchase_mode == "buy"):
                            opt_str = str(self.acct.shells[x]) + "/" + str(self.acct.max_shells[x]) + " " + str(round(self.acct.purchase("shell",x,True),2)) + "^"
                        else:
                            opt_str = str(self.acct.shells[x]) + "/" + str(self.acct.max_shells[x]) + " " + str(round(self.acct.refund("shell",x,True),2)) + "^"
                        lobby_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,shell_names[x])
            else: #we need to configure our special window/menu...which is always just a set of strings, with no settings you can change lol
                optionsettings = []
                for x in range(0,len(self.special_window) - 1):
                    optionsettings.append(["",""])
                special_menu.create_menu(self.special_window[:len(self.special_window) - 1],optionsettings,[],[],self.special_window[len(self.special_window) - 1])
                special_menu.update(self.screen)

            # - Make sure our cursor stays onscreen -
            cursorpos[0] = abs(cursorpos[0]) #no negative locations allowed!
            cursorpos[1] = abs(cursorpos[1])
            if(cursorpos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                cursorpos[0] -= self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()

            # - Check if we have clicked any buttons -
            with self.running_lock:
                self.running = not controller.get_keys()
            keys = self.controls.get_input()
            for x in directions:
                if(x in keys):
                    cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * lobby_menu.menu_scale
                    cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * lobby_menu.menu_scale

            if(shoot in keys and time.time() - debounce > 0.2): #shoot?
                debounce = time.time()
                if(self.special_window == None):
                    clicked_button = lobby_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                    if(clicked_button[0][0] != None):
                        with self.request_lock:
                            self.request = button_actions[clicked_button[1]][clicked_button[0][0]]
                        with self.request_pending_lock:
                            if(self.request != [None]):
                                self.request_pending = time.time()
                        # - Check if the button we pressed was in menu # 7 (key config) -
                        if(lobby_menu.current_menu == 7 and clicked_button[1] == 7 and clicked_button[0][0] - 2 >= 0): #we didn't change into this menu?? We were already here when we clicked?
                            config = True
                            controller.empty_keys() #empty the key list
                            while config: #wait until the client configures the key
                                controller.get_keys()
                                config = not self.controls.configure_key(clicked_button[0][0] - 2) #did we get a successful configuration?
                                # - Draw the "press a key to configure the button" words onscreen
                                self.screen.fill([0,0,0])
                                font.draw_words("Press a key to set it as the button you chose", [(self.screen.get_width() / 2 - len("Press a key to set it as the button you chose") * 5),10], [0,0,255], 1.0, self.screen)
                                pygame.display.flip()
                        # - Check if the player clicked Exit -
                        if(lobby_menu.current_menu == 0 and clicked_button[1] == 0 and clicked_button[0][0] == 3): #time to go?
                            with self.running_lock:
                                self.running = False
                else: #if the first button is clicked in the special window, we need to exit the special window by sending an exit packet to the server.
                    clicked_button = special_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                    if(clicked_button[0][0] == 0): #button 0 was clicked? Send a signal to the _netcode thread to exit this dumb window.
                        with self.request_lock:
                            self.request = ["sw_close"]

            if(self.request[0] == "battle"): #part of making sure the server acknowledges we're in the player queue...
                with self.waiting_for_queue_lock:
                    self.waiting_for_queue = time.time()

            if(str(type(self.waiting_for_queue)) == "<class 'float'>" and time.time() - self.waiting_for_queue < netcode.DEFAULT_TIMEOUT and self.request_pending == True): #make sure the server acknowledges that we're in the player queue
                with self.request_lock:
                    self.request[0] = False
                with self.waiting_for_queue_lock:
                    self.waiting_for_queue = True
                self.battle_queue(battle_settings[0][0])
                self.waiting_for_queue = False
                with self.request_lock:
                    self.request[0] = None #clear the halt on the packets thread for the lobby client.
            elif(str(type(self.waiting_for_queue)) == "<class 'float'>" and time.time() - self.waiting_for_queue < netcode.DEFAULT_TIMEOUT and self.request_pending == False): #We didn't make it?
                with self.request_lock:
                    self.request[0] = None
                with self.waiting_for_queue_lock:
                    self.waiting_for_queue = False

            # - Reconfigure the HUD -
            if(self.special_window == None):
                hovered_button = lobby_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos,None,False)
                if(hovered_button[0][0] != None):
                    hud.update_HUD_element_value(0,button_descriptions[lobby_menu.current_menu][hovered_button[0][0]])
                else: #here we should display our tank's current stats.
                    dummy_tank = self.acct.create_tank("img", "team_name")
                    armor = round(dummy_tank.armor,2)
                    speed = round(dummy_tank.speed,2)
                    damage = round(dummy_tank.damage_multiplier,2)
                    penetration = round(dummy_tank.penetration_multiplier,2)
                    RPM = round(dummy_tank.RPM,2)
                    hud.update_HUD_element_value(0,"Tank stats - " + str(armor) + " Armor, " + str(speed) + " Speed, " + str(damage) + " Damage multiplier, " + str(penetration) + " Penetration multiplier, " + str(RPM) + " RPM   -")
                
            #draw everything
            self.screen.fill([0,0,0]) #draw our menu stuff onscreen
            if(self.special_window == None):
                if(self.request_pending != True and self.request_pending != False): #draw the menu, but do not highlight options since we are awaiting a response from the server.
                    lobby_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,[0,0])
                else: #draw the menu as normal
                    lobby_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)
            else: #draw special_menu
                special_menu.draw_menu([0,0],[self.screen.get_width(),self.screen.get_height()],self.screen,cursorpos)
            #draw our cursor onscreen (it's a crosshair LOL...I should add a gunshot effect for when you click on the screen...)
            # - Change: Crosshair is only when a request is not pending...and is ALWAYS a crosshair when in special_menu.
            if(self.request_pending == True or self.special_window != None):
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] - int(8 * lobby_menu.menu_scale)],[cursorpos[0],cursorpos[1] - int(4 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0],cursorpos[1] + int(8 * lobby_menu.menu_scale)],[cursorpos[0],cursorpos[1] + int(4 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1]],[cursorpos[0] + int(4 * lobby_menu.menu_scale),cursorpos[1]],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,255,255],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1]],[cursorpos[0] - int(4 * lobby_menu.menu_scale),cursorpos[1]],int(3 * lobby_menu.menu_scale))
            elif(str(type(self.request_pending)) == "<class 'float'>"): #make the words "loading..." follow your mouse pointer around lol.
                font.draw_words("Loading...", [cursorpos[0] - 37.5, cursorpos[1] - 3.75], [255,255,255], 0.75 * lobby_menu.menu_scale, self.screen)
            elif(self.request_pending == False): #draw an X instead of a + crosshair.
                pygame.draw.line(self.screen,[255,0,0],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1] - int(8 * lobby_menu.menu_scale)],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1] + int(8 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
                pygame.draw.line(self.screen,[255,0,0],[cursorpos[0] - int(8 * lobby_menu.menu_scale),cursorpos[1] + int(8 * lobby_menu.menu_scale)],[cursorpos[0] + int(8 * lobby_menu.menu_scale),cursorpos[1] - int(8 * lobby_menu.menu_scale)],int(3 * lobby_menu.menu_scale))
            #draw the HUD
            hud.draw_HUD(self.screen)
            pygame.display.flip() #update the display

            # - Delete our menu in our special menu if we created one -
            if(self.special_window != None): #this can sometimes raise an exception if we're unlucky, so I need to catch it if it happens! I just *really* don't want to have to lock self.special_menu for basically this whole loop =(
                try:
                    special_menu.delete_menu(0)
                except Exception as e:
                    print("An exception occurred during lobby_frontend: " + str(e) + " - Nonfatal") #print the exception that occurred (most likely a IndexError)

            #get da FPS
            clock.tick(900)
            fps = clock.get_fps()
            pygame.display.set_caption("Tank Battalion Online Lobby - FPS: " + str(int(fps)))
            
        pygame.quit() #quit pygame when we're out of here...

    def battle_queue(self, battle_queue_str): #this handles the socket connection + the pygame stuff in the same thread. Lowers the FPS while in queue, but that's OK.
        #create a menu object for player queue stuff
        queue_menu = menu.Menuhandler()
        queue_menu.create_menu(["Back to Lobby","Up","Player 1","Player 2","Player 3","Player 4","Player 5","Down"],[["",""],["",""],["",""],["",""],["",""],["",""],["",""],["",""]],[],[],"TBO " + battle_queue_str + " Matchmaking Queue")

        # - Because we handle packets and display stuff in the same thread, I need to let this loop run a certain amount of time before waiting for a packet.
        #   - If I do not, I will get between 2 and 6 FPS due to the server's packet delay.
        PACKET_TIME = 0.25 #Change this value like this: PACKET_TIME = current_ping * 0.25 + PACKET_TIME * 0.75
        last_packet = time.time()
        send_packet = True

        # - Constant; Tells how many players we can view at once -
        VIEW_CT = 5

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
        directions = self.controls.buttons[10:14]
        shoot = self.controls.buttons[14]

        # - Shooting debouncing -
        shoot_timeout = time.time()

        #...queuing is taking a long time, eh?
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
                elif(netcode.data_verify(data, self.GAME_PACKET)): #are we supposed to be IN a match??
                    queueing = False #we move onto getting INTO our match then...hopefully the setup sequences work properly =)

                # - Make sure we respond with a packet -
                send_packet = True

                # - Set our last_packet timer -
                last_packet = time.time()

            # - Make sure our cursor stays onscreen -
            cursorpos[0] = abs(cursorpos[0]) #no negative locations allowed!
            cursorpos[1] = abs(cursorpos[1])
            if(cursorpos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                cursorpos[0] -= self.screen.get_width()
            if(cursorpos[1] > self.screen.get_height()):
                cursorpos[1] -= self.screen.get_height()
            
            # - Check if we have clicked any buttons -
            with self.running_lock:
                self.running = not controller.get_keys()
            keys = self.controls.get_input()
            for x in directions:
                if(x in keys):
                    cursorpos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * queue_menu.menu_scale
                    cursorpos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 160 * queue_menu.menu_scale

            if(shoot in keys and str(type(self.request_pending)) == "<class 'bool'>" and time.time() - shoot_timeout > 0.20): #we shot?
                shoot_timeout = time.time()
                clicked_button = queue_menu.menu_collision([0,0],[self.screen.get_width(),self.screen.get_height()],cursorpos)
                if(clicked_button[0][0] != None): #a button was clicked?
                    if(clicked_button[0][0] == 1): #view players farther up
                        if(player_view_index > 0):
                            player_view_index -= 1
                    elif(clicked_button[0][0] == 7): #view players farther down
                        player_view_index += 1
                    elif(clicked_button[0][0] == 0): #return to lobby??
                        exit_queue = True

            # - Update "Up" and "Down" settings so that we know which range of players we're looking at -
            opt_str = str(player_view_index) + "/" + str(total_players)
            queue_menu.reconfigure_setting([opt_str,opt_str],opt_str,0,"Up")
            opt_str = str(player_view_index + 4) + "/" + str(total_players)
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

    def battle_client(self):
        global path
        # - Menu stuff -
        battle_menu = menu.Menuhandler()
        battle_menu.default_display_size = [160, 120]
        battle_menu.create_menu(["","","","","","","","","",""],
                       [
                        #start by adding our powerup items to the menu
                        [path + "../../pix/blocks/powerups/fuel.png",[10,0]],
                        [path + "../../pix/blocks/powerups/fire-extinguisher.png",[10,20]],
                        [path + "../../pix/blocks/powerups/dangerous-loading.png",[10,40]],
                        [path + "../../pix/blocks/powerups/explosive-tip.png",[10,60]],
                        [path + "../../pix/blocks/powerups/amped-gun.png",[10,80]],
                        [path + "../../pix/blocks/powerups/makeshift-armor.png",[10,100]],
                        #add our shells to the menu
                        [path + "../../pix/ammunition/hollow_shell_button.png",[40,0]],
                        [path + "../../pix/ammunition/regular_shell_button.png",[60,0]],
                        [path + "../../pix/ammunition/explosive_shell_button.png",[80,0]],
                        [path + "../../pix/ammunition/disk_shell_button.png",[100,0]]
                        ],
                       [],buttonindexes=[],name="")
        battle_menu.create_menu(["Continue","Leave Match"], [["",""],["",""]], [[0,0]], buttonindexes=[], name="Ingame Options")
        SHELL_START = 6 #index 6-9 are shells
        POWERUP_START = 0 #index 0-5 are powerups

        # - HUD stuff -
        hud = HUD.HUD()
        hud_lock = _thread.allocate_lock()
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

        BAR_START = 17 #index 17 is where HUD HP bars begin...

        # - Key configuration stuff -
        tank_bullets = self.controls.buttons[0:4] #[pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        tank_powerups = self.controls.buttons[4:10] #[pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b, pygame.K_n]
        directions = self.controls.buttons[10:14] #[pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_a]
        shoot = self.controls.buttons[14]
        ESC_KEY = self.controls.buttons[15] #this brings you to the second menu, which lets you continue the match or leave it.
        CURSOR_MOD = self.controls.buttons[16]
        
        # - Entity/player stuff -
        player_account = account.Account() #your account stats (they get set up properly within battle_client_netcode())
        player_tank = entity.Tank(pygame.image.load(path + "../../pix/Characters(gub)/p1U.png"), ["tmp team name","tmp player name"]) #your player tank
        entities = [] #list of other players, powerups, bullets
        entities_lock = _thread.allocate_lock()

        # - Arena stuff -
        arena = arena_lib.Arena([[0,0],[0,0]], [pygame.image.load(path + "../../pix/blocks/ground/asphalt.png")], [])
        arena.stretch = False
        # - The viewport size of our screen -
        tile_viewport = [12,12]
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
        particles = [] #list of particle effects (explosions, fire, etc.)
        framecounter = 0 #this makes sense...frame counter for particle stuff I wanna say?
        particles_lock = _thread.allocate_lock()

        # - Gameloop setup -
        clock = pygame.time.Clock() #gotta see that cap FPS - or is it a FPS cap???
        # - The next two variables are only needed until I have proper key configuration implemented -
        keys = [] #list of keys pressed (temporary; when key configuration is implemented, this will change...)
        mousepos = [0,0] #where is our cursor located?
        running = [True] #HAS to be a list so that the value is shared between the _netcode() thread and this thread...bad things happen otherwise.
        explosion_timer = time.time() #this is for checking when the last "game over" explosion happened
        fps = 30 #this is needed for moving the cursor around at a reasonable rate
        
        # - These flags are for netcode operation which also involves the client frontend -
        game_end = False #this flag helps me end the game smoothly.
        sync = False #this flag prevents us from moving when the server syncs us.
        eliminated = [] #this only gets filled with data once it is game over.
        
        _thread.start_new_thread(self.battle_client_netcode,(player_tank, player_account, entities, entities_lock, particles, particles_lock, arena, blocks, screen_scale, running, sync, game_end, eliminated, hud, hud_lock)) #start up the netcode

        # - Now we use this thread to draw graphics, and do keypress detection etc. -
        while running[0]:
            # - Make sure our cursor stays onscreen -
            mousepos[0] = abs(mousepos[0]) #no negative locations allowed!
            mousepos[1] = abs(mousepos[1])
            if(mousepos[0] > self.screen.get_width()): #can't be offscreen by being too big either!
                mousepos[0] -= self.screen.get_width()
            if(mousepos[1] > self.screen.get_height()):
                mousepos[1] -= self.screen.get_height()
            
            running[0] = not controller.get_keys() #handle controller stuff real EZ
            keys = self.controls.get_input()

            # - Increment our framecounter counter -
            if(framecounter >= 65535):
                framecounter = 0
            else:
                framecounter += 1

            # - Hnadle the ESC key -
            if(ESC_KEY in keys): #menu # 1 then...
                battle_menu.current_menu = 1

            # - Handle constant keypresses (for the moment) -
            if(not sync):
                for x in directions:
                    if(x in keys and not CURSOR_MOD in keys):
                        with player_tank.lock:
                            player_tank.move(directions.index(x) * 90, arena.TILE_SIZE)
                    elif(x in keys and CURSOR_MOD in keys):
                        mousepos[1] -= math.sin(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 80 * battle_menu.menu_scale
                        mousepos[0] += math.cos(math.radians(directions.index(x) * 90 + 90)) / (abs(fps) + 1) * 80 * battle_menu.menu_scale
                if(shoot in keys and not CURSOR_MOD in keys):
                    player_tank.shoot(arena.TILE_SIZE, server=False)
                elif(shoot in keys and CURSOR_MOD in keys): #we're shooting a menu item? ...Here we go...menu collision...
                    collide = battle_menu.menu_collision([0,0],[self.screen.get_width(), self.screen.get_height()],mousepos,inc=None)
                    if(battle_menu.current_menu == 0 and collide[0][1] != None): #menu index 0?
                        if(collide[0][1] >= POWERUP_START and collide[0][1] <= SHELL_START - 1): #use powerup?
                            player_tank.use_powerup(collide[0][1] - POWERUP_START, False)
                        elif(collide[0][1] >= SHELL_START and collide[0][1] <= SHELL_START + 3): #use shell?
                            player_tank.use_shell(collide[0][1] - SHELL_START)
                    elif(battle_menu.current_menu == 1 and collide[0][0] != None): #we clicked a button in the second menu (hit ESC to access)
                        if(collide[0][0] == 1): #disconnect?
                            running[0] = False #just make sure we're leaving - this tells the netcode thread that we're leaving, and quits us back to the lobby.
                # - Check for powerup usage -
                for x in tank_powerups:
                    if(x in keys):
                        player_tank.use_powerup(tank_powerups.index(x), False)
                # - Check for shell changing -
                for x in tank_bullets:
                    if(x in keys):
                        player_tank.use_shell(tank_bullets.index(x))


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
            #update P1's powerup cooldown HUD
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
                        if(tank_powerups[x - 3] == menu.keys[key][0]):
                            key_to_press = menu.keys[key][1]
                            break
                    if(key_to_press == None):
                        hud.update_HUD_element_value(x,"")
                        hud.update_HUD_element_color(x,[[0,255,0],None,None])
                    elif(player_tank.powerups[x - 3] != None):
                        hud.update_HUD_element_value(x,key_to_press)
                        hud.update_HUD_element_color(x,[[0,255,0],None,None])
                    else: #powerup isn't available!!!
                        hud.update_HUD_element_value(x,"x")
                        hud.update_HUD_element_color(x,[[255,0,0],None,None])
            #update P1's shell HUD
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
                    if(tank_bullets[x - 9] == menu.keys[key][0]):
                        key_to_press = menu.keys[key][1]
                        break
                if(key_to_press != None):
                    hud.update_HUD_element_value(x,key_to_press)
                else:
                    hud.update_HUD_element_value(x,"")
                hud.update_HUD_element_color(x,[[0,255,0],None,None])
            for x in range(13,17):
                hud.update_HUD_element_value(x,str(int(player_tank.shells[x - 13])))

            # - Handle updating various objects (this MUST go before collision detection happens) -
            arena.shuffle_tiles() #update the arena object's tile shuffling system
            with player_tank.lock: #update some of our various timing variables for reload time, etc.
                player_tank.clock(arena.TILE_SIZE, screen_scale, particles, framecounter)
            screen_scale = arena.get_scale(tile_viewport, self.screen)

            # - Handle tank collision (just our tank, nobody else's) -
            with player_tank.lock:
                player_tank.screen_location = [ #get the position set up properly for starts...
                    (self.screen.get_width() / 2) - (arena.TILE_SIZE * screen_scale[0] / 2),
                    (self.screen.get_height() / 2) - (arena.TILE_SIZE * screen_scale[1] / 2),
                    ]
            collision = player_tank.return_collision(arena.TILE_SIZE, 3) #collision offset of 3 pixels to make map navigation easier
            tile_collision = arena.check_collision(tile_viewport, player_tank.overall_location[:], collision)
            with player_tank.lock:
                for x in tile_collision:
                    if(x[0] in blocks):
                        player_tank.unmove()
                        break

            # - Set up an explosion system IF the game is over -
            if(len(eliminated) != 0): #game over?
                if(time.time() - explosion_timer > 0.50): #create an explosion every X seconds
                    explosion_timer = time.time() #reset the explosion timer...
                    GFX.create_explosion(particles, [random.randint(0,tile_viewport[0]), random.randint(0,tile_viewport[1])], random.randint(2,6), [0.05, random.randint(1,3)], [[255,0,0],[255,255,0]],[[0,0,0],[100,100,100],[50,50,50]], 0.80, 0, "game over", arena.TILE_SIZE)

            # - Draw everything -
            self.screen.fill([0,0,0]) #start with black...every good game starts with a black screen.
            arena.draw_arena(tile_viewport, player_tank.map_location[:], self.screen) #draw the arena
            player_tank.draw(self.screen, screen_scale, arena.TILE_SIZE) #draw the player tank
            with entities_lock: #draw all other entities
                # - For bullets and powerups: draw(self, screen, screen_scale, arena_offset, TILE_SIZE)
                # - For tanks: draw(self, screen, screen_scale, TILE_SIZE, third_person_coords=None)
                bar = 0
                for x in entities:
                    if(x.type != "Tank"): #Bullet/powerup
                        x.draw(self.screen, screen_scale, player_tank.map_location[:], arena.TILE_SIZE)
                    else: #tank
                        x.draw(self.screen, screen_scale, arena.TILE_SIZE, player_tank.map_location[:])
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
                                hud.update_HUD_element(BAR_START + bar * 2,[[(x.overall_location[0] - player_tank.map_location[0]) * arena.TILE_SIZE * screen_scale[0],(-0.35 + x.overall_location[1] - player_tank.map_location[1]) * arena.TILE_SIZE * screen_scale[1]],[20,5],[color,[0,0,0],[0,0,255]],value])
                                hud.update_HUD_element(bar * 2 + BAR_START + 1,[[(x.overall_location[0] - player_tank.map_location[0] + 0.05) * arena.TILE_SIZE * screen_scale[0],(-0.275 + x.overall_location[1] - player_tank.map_location[1]) * arena.TILE_SIZE * screen_scale[1]],3,[[150,150,150],None,None],label])
                        except Exception as e:
                            print("Exception occurred at battle_client(): " + str(e) + " - Nonfatal")
                        bar += 1 #increment the HP bar counter
            # - Draw all particle effects and delete old particles -
            with particles_lock:
                # - Delete any particles which are finished their job (this has to happen first to avoid invalid color arguments from bad timing) -
                decrement = 0
                for x in range(0,len(particles)):
                    if(particles[x - decrement].timeout == True):
                        del(particles[x - decrement])
                        decrement += 1
                
                for x in particles: # - Draw the remaining particles -
                    x.clock()
                    x.draw(arena.TILE_SIZE, screen_scale, player_tank.map_location[:], self.screen)
            # - Draw the menu -
            battle_menu.draw_menu([0,0],[self.screen.get_width(), self.screen.get_height()],self.screen,mousepos)
            hud.draw_HUD(self.screen)
            #draw the cursor onscreen
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0],mousepos[1] - int(8 * battle_menu.menu_scale)],[mousepos[0],mousepos[1] - int(4 * battle_menu.menu_scale)],int(3 * battle_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0],mousepos[1] + int(8 * battle_menu.menu_scale)],[mousepos[0],mousepos[1] + int(4 * battle_menu.menu_scale)],int(3 * battle_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0] + int(8 * battle_menu.menu_scale),mousepos[1]],[mousepos[0] + int(4 * battle_menu.menu_scale),mousepos[1]],int(3 * battle_menu.menu_scale))
            pygame.draw.line(self.screen,[255,255,255],[mousepos[0] - int(8 * battle_menu.menu_scale),mousepos[1]],[mousepos[0] - int(4 * battle_menu.menu_scale),mousepos[1]],int(3 * battle_menu.menu_scale))

            # - Update the display -
            pygame.display.flip()

            # - Handle FPS display -
            clock.tick(900)
            fps = clock.get_fps()
            pygame.display.set_caption("Tank Battalion Online - FPS: " + str(int(fps)))
        
    def battle_client_netcode(self, player_tank, player_account, entities, entities_lock, particles, particles_lock, arena, blocks, screen_scale, running, sync, game_end, eliminated, hud, hud_lock): #netcode and background processes for battle_client().
        setup = True #do we still need to set up the game?
        packets = True #are we going to stop exchanging packets yet?
        clock = pygame.time.Clock() #I like to see my PPS

        #define our list of powerup images
        powerup_images = [
            pygame.image.load(path + "../../pix/blocks/powerups/fuel.png"),
            pygame.image.load(path + "../../pix/blocks/powerups/fire-extinguisher.png"),
            pygame.image.load(path + "../../pix/blocks/powerups/dangerous-loading.png"),
            pygame.image.load(path + "../../pix/blocks/powerups/explosive-tip.png"),
            pygame.image.load(path + "../../pix/blocks/powerups/amped-gun.png"),
            pygame.image.load(path + "../../pix/blocks/powerups/makeshift-armor.png"),
            pygame.image.load(path + "../../pix/ammunition/hollow_shell_button.png"),
            pygame.image.load(path + "../../pix/ammunition/regular_shell_button.png"),
            pygame.image.load(path + "../../pix/ammunition/explosive_shell_button.png"),
            pygame.image.load(path + "../../pix/ammunition/disk_shell_button.png")
            ]

        #define ally and enemy images
        ally_image = pygame.image.load(path + "../../pix/Characters(gub)/p1U.png")
        enemy_image = pygame.image.load(path + "../../pix/Characters(gub)/p2U.png")
        
        while packets:
            #recieve data from the server
            #Recieve packet description: All packets start with a "prefix", a small string describing what the packet does and the format corresponding to it.
            # - Type A) Setup packet. Very long packet, used to setup the client's game state. (Not entity related stuff; Account data, arena data, etc.)
            #       Format: ["setup", account.return_data(), map_name]
            # - Type B) Sync packet. Shorter packet, usually used to change the client's player state. In the case that a sync packet has to be used, the client MUST send back the exact same data next packet. Only used with AC enabled.
            #       Format: ["sync", server_entity.return_data()]
            # - Type C) Normal packet. Sends player data such as where entities are onscreen, the cooldown of your consumables, and your reload time.
            #       Format: ["packet",[entity1, entity2, entity3...]]
            # - Type D) Ending packet. Sends a simple message to the client letting the client know that the game is finished.
            #       Format: ["end", [entity1, entity2, entity3...], elimination_order]
            data_pack = netcode.recieve_data(self.Cs, self.buffersize)
            data = data_pack[0]

            if(data != None and netcode.data_verify(data, self.GAME_PACKET)): #...only try this if we get some valid data...otherwise bad things might happen lol
                if(data[0] == "setup"): #set up the game!
                    # - Set up the player -
                    player_account.enter_data(data[1]) #gotta make sure we have our account + tank set up properly
                    with player_tank.lock:
                        #team name will get set on a sync packet. The server will have to send one right after setup occurs.
                        player_tank_new = player_account.create_tank(pygame.image.load(path + "../../pix/Characters(gub)/p1U.png"), "team name here...")
                        player_tank.enter_data(player_tank_new.return_data(), arena.TILE_SIZE, screen_scale)
                    # - Set up the arena -
                    with arena.lock:
                        arena_name = data[2] #the server sent us the name of the arena we're playing on
                        print(arena_name)
                        arena_data = import_arena.return_arena(arena_name) #get our arena data from the name the server sent us
                        arena.arena = arena_data[0] #input the arena data into our arena object
                        arena.tiles = arena_data[1]
                        arena.shuffle_patterns = arena_data[2]
                        for x in arena_data[3]:
                            blocks.append(x)
                    # - Set up the HUD a bit (HP bars for all players other than ourselves) -
                    for x in range(0,data[3]):
                        hud.add_HUD_element("horizontal bar",[[0,-50],[20,5],[[0,255,0],[0,0,0],[0,0,255]],1.0],False)
                        hud.add_HUD_element("text",[[0,-50],7,[[255,0,0],False,False],"100 HP"],False)
                    setup = False
                elif(data[0] == "sync"): #we're moving a bit funny, and the server doesn't like it...we can't move for a bit here =(
                    with player_tank.lock:
                        player_tank.enter_data(data[1], arena.TILE_SIZE, screen_scale) #reset our tank's position a bit...
                    sync = True #turn on our sync flag (auugh! we can't move all of a sudden!)
                elif(data[0] == "packet"): #normal data packet
                    with entities_lock:
                        for x in range(0,len(entities)):
                            del(entities[0]) #delete all of the entities list without removing our pointer to the list
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
                                entities.append(entity.Tank("image will be fixed", ["Tank name which will be inserted when we enter_data()","Team name which will be fixed when we enter_data()"]))
                                entities[len(entities) - 1].enter_data(data[1][x]) #fixes everything but the image, which we can do by checking if the player is on our team. if not, the image is p2's tank.
                                # - Fix the image -
                                if(entities[len(entities) - 1].team == player_tank.team): #on our team?
                                    entities[len(entities) - 1].image = ally_image #assign p1_tank's image
                                else: #assign p2_tank's image
                                    entities[len(entities) - 1].image = enemy_image
                        # - Update our particle list -
                        if(data[2] != None): #the server is sending particles this packet?
                            with particles_lock:
                                for x in range(0,len(particles)):
                                    del(particles[0])
                                for x in data[2]:
                                    tmp_particle = GFX.Particle([0,0], [0,0], 1, 1, [0,0,0], [0,0,0], 1, 2, form=0) #create a blank particle
                                    tmp_particle.enter_data(x) #enter some attribute data into the particle
                                    particles.append(tmp_particle) #add it to the particles list so it can be drawn
                        if(data[3] != None): #the server is sending block updates this packet?
                            arena.modify_tiles(data[3]) #update our tiles...
                                
                elif(data[0] == "end"): #game over?
                    if(len(eliminated) != len(data[2])): #make sure eliminated is the right length
                        if(len(eliminated) > len(data[2])):
                            for x in range(0,len(eliminated) - len(data[2])):
                                del(eliminated[len(eliminated) - 1])
                        else:
                            for x in range(0,len(data[2]) - len(eliminated)):
                                eliminated.append(["",False])
                    for x in range(0,len(data[2])): #this is the order teams were eliminated in.
                        eliminated[x] = data[2][x]
                    game_end = True
                    with entities_lock: #we still need to update entities...
                        for x in range(0,len(entities)):
                            del(entities[0]) #delete all of the entities list without removing our pointer to the list
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
                                entities.append(entity.Tank("image will be fixed", ["Tank name which will be inserted when we enter_data()","Team name which will be fixed when we enter_data()"]))
                                entities[len(entities) - 1].enter_data(data[1][x]) #fixes everything but the image, which we can do by checking if the player is on our team. if not, the image is p2's tank.
                                # - Fix the image -
                                if(entities[len(entities) - 1].team == player_tank.team): #on our team?
                                    entities[len(entities) - 1].image = ally_image #assign p1_tank's image
                                else: #assign p2_tank's image
                                    entities[len(entities) - 1].image = enemy_image

            # - Copy a small amount of data from the entities list into our player_tank object -
            for x in range(0,len(entities)): #find which tank is us...
                if(entities[x].type == "Tank" and entities[x].name == player_tank.name and entities[x].team == player_tank.team): #we found us?
                    with player_tank.lock: #this basically syncs some basic attributes about ourselves so that we know our own tank's current state...
                        player_tank.last_shot = entities[x].last_shot
                        player_tank.HP = entities[x].HP
                        player_tank.armor = entities[x].armor
                        player_tank.speed = entities[x].speed
                        for y in range(0,len(entities[x].shells)):
                            player_tank.shells[y] = entities[x].shells[y]
                        for y in range(0,len(entities[x].powerups)):
                            player_tank.powerups[y] = entities[x].powerups[y]
                    break

            #send our data back to the server
            # - Format:
            #   - Normal packet:["packet",Tank.return_data()]
            #   - Leave match: ["end",Tank.return_data()]
            #   - Still need to setup (packet lost): ["setup"]
            if(running[0] == True):
                if(setup):
                    netcode.send_data(self.Cs, self.buffersize, ["setup"])
                else:
                    netcode.send_data(self.Cs, self.buffersize, ["packet",player_tank.return_data()])
            else: #if we're not in the game anymore, just start sending lobby packets. The server will find out what we're doing and accomodate us.
                packets = False
            sync = False #disable the sync after we send our data to the server

            clock.tick(800) #tick our clock; it won't hit close to 800PPS obviously, but I just want to see my PPS without hitting an infinity value if something goes wrong...

    def return_rating(self, player_account, rating=False): #creates a numerical rating number for a player.
        player_stat = 0 #temporary variable which I use to calculate a player's numerical rating
        if(rating): #this is for rated/ranked battles only.
            player_stat += self.EXP_WEIGHT * player_account.experience #add player exp to predicted performance
        player_stat += self.CASH_WEIGHT * player_account.cash #add player cash to predicted performance
        # - Find the player's average upgrade level -
        avg_player_upgrade = 0
        for b in range(0,len(player_account.upgrades)):
            avg_player_upgrade += player_account.upgrades[b]
        avg_player_upgrade /= len(player_account.upgrades)
        # - Add the player's average upgrade level to the player's predicted performance -
        player_stat += self.UPGRADE_WEIGHT * avg_player_upgrade
        # - Add the player's number of shells of each type to the player's predicted performance -
        for x in range(0,len(player_account.shells)):
            player_stat += player_account.shells[x] * self.SHELLS_WEIGHT[x]
        # - Add the player's powerups to the player's predicted performance -
        for x in range(0,len(player_account.powerups)):
            if(player_account.powerups[x] == True):
                player_stat += self.POWERUP_WEIGHT
        # - Add the player's specialization number to the player's predicted performance -
        player_stat += self.SPECIALIZATION_WEIGHT * abs(player_account.specialization)
        return player_stat

    def create_account(self,rating,player_name="Bot Player"): #creates an account with upgrades which correspond roughly to the rating value you input.
        bot_account = account.Account(player_name,"pwd",True) #create a bot account
        while self.return_rating(bot_account) < rating:
            bot_account.random_purchase()
        return bot_account

#engine = BattleEngine("192.168.50.47",5031)
#pygame.quit() #exit pygame
