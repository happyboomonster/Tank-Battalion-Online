##"battle_server.py" library ---VERSION 0.65---
## - Handles battles (main game loops, matchmaking, lobby stuff, and game setup) for SERVER ONLY -
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

#Python libraries:
import _thread #we need threading systems for handling netcode + CPU threads
import random
import netcode
import socket
import time
import pickle
import pygame
import sys
import math
#set up external directories
sys.path.insert(0, "../maps")
#My own proprietary librares:
import account
import entity
import import_arena
import arena as arena_lib
import GFX #(yes, we're using particles on the server lol)
import SFX #(yes, sound effects too)

# - This is a global which tells us the path to find the directory battle_server is stored in -
path = ""

def init(path_str=""):
    global path
    path = path_str
    entity.path = path_str
    import_arena.path = path_str

class BattleEngine():
    def __init__(self, autostart=True):
        # - Netcode constants -
        self.buffersize = 10

        # - Enable Anti-Cheat? -
        self.ac_enable = True

        # - Are we using the server for a split-screen offline game? This will modify the behaviour of battle_server() slightly -
        self.offline = False

        # - Sound reference constants -
        self.GUNSHOT = 0
        self.DRIVING = 1
        self.THUMP = 2
        self.EXPLOSION = 3
        self.CRACK = 4

        # - Formats for netcode packets (being recieved from the client) -
        #   - Format: [None], OR if we want to buy/return something, ["buy"/"return","item type",###], enter battle ["battle","battle type"]
        self.LOGIN_PACKET = ["<class 'str'>","<class 'str'>","<class 'bool'>"]
        #NOTE: the INT class contained in the last LOBBY_PACKETS packet type is redundant; it is simply there to distinguish it from a GAME_PACKET, which also has an ID of a STR + a LIST.
        self.LOBBY_PACKETS = [
            ["<class 'NoneType'>"],
            ["<class 'str'>", "<class 'str'>", "<class 'int'>"],
            ["<class 'str'>", "<class 'str'>"],
            ["<class 'str'>", "<class 'int'>", "<class 'list'>"]
            ]
        self.MATCH_PACKETS = ["<class 'int'>", "<class 'int'>"] #[VIEW_CT, player_view_index] OR [False] to leave matchmaker (this one doesn't need to be included)
        self.GAME_PACKETS = [
            ["<class 'str'>"],
            ["<class 'str'>","<class 'list'>"]
            ]

        #list of all accounts in the game; These get stored into a pickle dump when the server is shut down, and recovered when the server starts up.
        self.accounts = []
        try:
            self.accounts = self.load_save_data()
        except Exception as e:
            print("An exception occurred while loading save data: " + str(e) + " ...Resuming with standard save file...")
            self.accounts.append(account.Account("testaccta","pwda"))
            self.accounts.append(account.Account("testacctb","pwdb"))
        self.logged_in = [] #list of ["player name","player password] lists to detect who is/isn't logged in
        self.logged_in_lock = _thread.allocate_lock()
        #player_queue: List of queues of [account,socket]s in different game modes.
        # - Format: [[account, socket],[account, socket]],[[account, socket],[account, socket]]
        self.battle_types = ["Unrated Battle","Experience Battle"]
        self.experience_battles = [False, True] #list of which battle types involve player experience
        self.player_queue = []
        for x in range(0,len(self.battle_types)):
            self.player_queue.append([])
        self.player_queue_lock = _thread.allocate_lock()
        self.battle_type_functions = [self.unrated_battle_server,self.ranked_battle_server]

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
        self.IMBALANCE_LIMIT = 1.25 / self.MMCEF #self.POWERUP_WEIGHT
        #How many players (not including bots) can be put into a battle? [min, max]
        self.PLAYER_CT = [1, 25]
        #How many teams can a single battle have? -
        self.TEAM_CT = [2,4]
        # - How long should it take before a minimum player match attempts to take place?
        #   - (These matchmaking delays are really just here to reduce server CPU load now that match restrictions are built into the...
        #   - ...matchmaker)
        self.IMMEDIATE_MATCH = 45 #X/60 minutes = maximum wait time
        # - This isn't really the maximum match time, it's the maximum match time during which all matchmaking rules apply.
        #   - After X number of seconds have passed, the restrictions on matchmaking will begin to slacken to encourage a quick match.
        self.MAXIMUM_MATCH_TIME = 30 #seconds
        # - This constant is used by dividing SCALING_CONSTANT / PlayersInQueue
        self.TIME_SCALING_CONSTANT = self.IMMEDIATE_MATCH * self.PLAYER_CT[0] * 0.7 #how fast should the matchmaker shove players into matches if there are more than minimum players?
        # - This constant defines the minimum player count for an "optimal" match -
        self.OPTIMAL_MATCH_CT = 8 #How many players does the matchmaker *want* in a game? If it is not met, the game will add extra bots to compensate.
        # - At this point, a match WILL be made regardless of whether we have attained self.OPTIMAL_MATCH_CT number of players -
        self.FORCED_MATCH_URGENCY = 0.625
        # - The lower this constant is, the faster the matchmaker will make matches at the expense of being more unbalanced. Values less than 1 and greater than 0 only -
        self.MIN_URGENCY = 0.25
        # - This constant helps determine how much imbalance the matchmaker will allow in a match to get more players into it -
        self.MIN_WAIT_ADD_URGENCY = self.MIN_URGENCY * 1.25
        # - Matchmaker rules -
        #   - Usable variables:
        #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
        #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
        #       - player_counts[] is a list which holds the count of each team's players
        #       - team_ratings[] is a list which holds the rating of each team
        #       - max_team_rating is a variable storing the most powerful team rating
        #       - min_team_rating is a variable storing the least powerful team rating
        #       - max_team_players is a variable storing the most players on a team
        #       - min_team_players is a variable storing the least players on a team
        #       - max_player_rating is a variable storing the most powerful player in the match
        #       - min_player_rating is a variable storing the least powerful player in the match
        #       - bot_rating[] is a list: [rating, team index] It only applies to the weakest bot in the match, since there CAN be multiple.
        #       - player_ratings[] is a list of lists: [ [team 0 players: 0.9, 5.5, 6.2], team 1 players: [5.1, 8.9, 9.1]... ]
        #           - The first player rating is always the weakest player,
        #           - and the last player rating for each team is always the strongest player.
        # - Self.rules is a list of strings which the matchmaker has to evaluate to determine whether the match is fair.
        self.RULES = [ #The rules without urgency implemented in them will remain rigid at all times.
            "max_team_rating * math.sqrt(urgency) < min_team_rating", #all teams must be within sqrt(urgency%) rating differences
            "bot_rating[0] >= self.IMBALANCE_LIMIT", #the bot player MUST have at least the rating required to hold a few shells (otherwise useless bot, because bot has no bullets)
            "min_team_players > max_team_players * urgency" #all teams must have the same amount of players with urgency% error.
            ]

        # - self.PLAYER_RULES is a list of rules which EACH player has to meet to be added to a match -
        #   - Usable variables:
        #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
        #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
        #       - first_player is a variable storing the rating of the first player added to the match.
        #       - player is a list containing this player's data: [rating, [account, socket]]
        self.PLAYER_RULES = [
            "player[0] > first_player * math.sqrt(urgency) and player[0] < first_player * (1/math.sqrt(urgency))"
            ]

        # - Map picker constants -
        self.MAX_SQUARES_PER_PERSON = 7.0 #if all the free space on the map was evenly divided between every player in it, how much space should each player get (at max)?
        self.MIN_SQUARES_PER_PERSON = 6.0 #if all the free space on the map was evenly divided between every player in it, how much space should each player get (at max)?

        # - How long should the compute thread of a battle last AFTER game over has occurred? -
        self.BATTLE_TIMER = 30.0 #seconds

        # - How long do players have to COMPLETE a battle? (remember: battle_time is different from battle_timer [see above]) -
        self.BATTLE_TIME = 6 * 60 #X minutes is adequate?
        self.BATTLE_TIME_PLAYER_COEFFICIENT = 30.0 #How many seconds do we add to a battle for each additional player in it?

        if(autostart):
            # - Set up our networking stuff; This has to be done here since we don't want to make real IP connections when playing in offline mode -
            #the IP/device name of our server
            HOST_NAME = socket.gethostname()
            try: #for some reason (maybe network configuration?) this fails on AWS instances. You have to type in the server IP address manually.
                self.IP = socket.gethostbyname(HOST_NAME + ".local")
            except Exception as e:
                print("[ERROR] Couldn't get server IP!")
                self.IP = input("Please enter the server IP manually: ")

            #create a random port number
            PORT = 5031
            print("Port Number: " + str(PORT) + " IP: " + str(self.IP))
            
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket object
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.s.bind((self.IP, PORT))
            self.s.listen() #wait for connections

            # - Start the matchmaker script and the client connection script -
            _thread.start_new_thread(self.matchmaker_loop,())
            self.connect_players() #begin the connection script

    # - Logs out a player, so their data is saved when they leave the game. This function returns True if the data was saved successfully -
    def logout_player(self, player_data): #player_data format: [account.Account() object, socket object]
        found = False
        try:
            for x in range(0,len(self.accounts)):
                if(self.accounts[x].name == player_data[0].name): #we found the account we need to sync data with?
                    self.accounts[x] = player_data[0]
                    found = True
                    self.save_data()
            if(found == True): #remove the player from the logged_in list
                with self.logged_in_lock:
                    for x in range(0,len(self.logged_in)):
                        if(self.logged_in[x] == [player_data[0].name, player_data[0].password]):
                            del(self.logged_in[x])
                            print("[LOGIN] Successfully deleted login data")
                            break
        except Exception as e:
            print("[SAVE] Failed to save player data - Error message: " + str(e))
            found = False
        return found

    def connect_players(self):
        while True:
            print("[WAIT] Waiting for a connection...")
            try:
                Cs, Caddress = self.s.accept() #connect to a client
            except Exception as e:
                print("[ERROR] Couldn't open a new socket! Assuming older accept() syntax and retrying...")
                Cs, Caddress = self.s.accept(100) #100 failed connects before server stops accepting new clients (needs restart then)
            netcode.configure_socket(Cs) #configure our socket settings so it's ready for netcode.py commands

            # - A bad client could kill the server, so let's save our data before that happens... -
            self.save_data()

            print("[CONNECT] Connected a client - ", end="")

            #get the password and username we entered to log in [name, password]
            client_data = netcode.recieve_data(Cs, self.buffersize)
            logged_in = False
            if(client_data[0] != None and netcode.data_verify(client_data[0], self.LOGIN_PACKET)):
                name = client_data[0][0]
                password = client_data[0][1]
                signin = client_data[0][2]

                print("[CONNECT] Recieved login/create account data - Username: " + str(name) + "; Password: " + str(password) + " - ", end="")

                # - First check if the player's name is equivalent to the name all bots are assigned: "Bot Player" -
                if(name[0:3] != "Bot"): #if the player name starts with "Bot", the player has NO CHANCE of creating a new account/signing in.
                    # - Create the player's acccount if the player does not have an account already -
                    if(signin == False):
                        # - First check if the account NAME (not password) already exists. If it DOESN'T, then the new account gets created -
                        for x in self.accounts: #NOTE: If the account already exists, the server will try to log the player onto it.
                            if(x.name == name):
                                signin = True
                        if(signin == False): #the account hasn't already been created?
                            self.accounts.append(account.Account(name, password))

                    #Next: Get username and password. If they match an account's password and username, we log the user in as that account.
                    for x in range(0,len(self.accounts)):
                        if(name == self.accounts[x].name and password == self.accounts[x].password and (not [self.accounts[x].name, self.accounts[x].password] in self.logged_in)): #someone has NOT already logged in as us?
                            logged_in = True
                            # - Add the player to our "logged in" list
                            with self.logged_in_lock:
                                self.logged_in.append([self.accounts[x].name, self.accounts[x].password])
                            break
            if(logged_in == False): #the person failed to log in because they got the wrong username/password?
                Cs.close() #disconnect the client. They can reconnect to the server and try again if they like.
                print("[CONNECT] Bad login data or player was already logged in with another system")
            else: #we got in successfully? We hand off the next responsibility to the lobby handler. One parameter is needed (player data): [account,socket]
                print("[CONNECT] Good login data")
                _thread.start_new_thread(self.lobby_server, ([self.accounts[x], Cs],) )

    def save_data(self): #saves everyone's data into a pickle file
        #dump all account data
        afile = open("saves/player_data.pkl","wb")
        pickle.dump(self.accounts, afile)
        afile.flush()
        afile.close()

    def load_save_data(self):
        afile = open("saves/player_data.pkl","rb")
        data = pickle.load(afile)
        return data

    #handles player requests while a player is in the lobby still
    def lobby_server(self, player_data, special_window=None, running=None): #player_data format: [account.Account() object, socket object]; Running is a list which allows an external process to halt this thread. Format: [True/False]
        netcode.clear_socket(player_data[1]) #clear the data within the socket to make sure there are no leftover packets from something else...
        in_lobby = True
        disconnect_packets = 0 #counter of packets disconnected
        while in_lobby:
            #we need to wait for a response from our client - data packets are exchanged between client and server every 0.X seconds.
            client_data_pack = netcode.recieve_data(player_data[1], self.buffersize) #Client transmission format: [None], OR if we want to buy/return something, ["buy"/"return","item type",###], enter battle ["battle","battle type"]
            client_data = client_data_pack[0]

            # - Check if the client disconnected -
            if(not client_data_pack[3]):
                disconnect_packets += 1
            else:
                disconnect_packets = 0
            if(disconnect_packets > 3):
                in_lobby = False

            # - Check if running[] says we should exit -
            if(running != None):
                in_lobby = running[0]

            # - Print out any errors that occurred -
            for x in range(0,len(client_data_pack[2])):
                print(client_data_pack[2][x])

            #Perform the client's requested operation
            if(client_data != [None] and client_data != None): #the client actually requested an operation?
                # - We need to verify that the client data is valid -
                valid = False
                for x in self.LOBBY_PACKETS:
                    valid = netcode.data_verify(client_data, x)
                    if(valid):
                        break
                if(valid): #IF the data verification passes, then we process the data we recieved.
                    #print(client_data, player_data[0].name) #debug
                    if(client_data[0] == "buy"): #purchasing an item?
                        reply = [player_data[0].purchase(client_data[1],client_data[2])]
                    elif(client_data[0] == "refund"): #refunding an item?
                        reply = [player_data[0].refund(client_data[1],client_data[2])]
                    elif(client_data[0] == "battle"): #enter into battle!!!
                        with self.player_queue_lock:
                            reply = [False]
                            for x in range(0,len(self.battle_types)): #...just making sure this game mode exists...
                                if(self.battle_types[x] == client_data[1]):
                                    reply = [True, "battle"]
                                    reply.append(player_data[0].return_data())
                                    reply.append(None) #append NO special window data to the list
                                    netcode.send_data(player_data[1], self.buffersize, reply)
                                    self.player_queue[x].append(player_data)
                        in_lobby = False #exit the lobby netcode loop
                    elif(client_data[0] == "sw_close"): #closing the special window?
                        special_window = None #clear our special window...
                    elif(client_data[0] == "settings"): #change our settings?
                        player_data[0].settings = client_data[2][:]
                        reply = [True]
                    else:
                        reply = [None]
                else:
                    reply = [None]
            else:
                reply = [None]

            if((len(reply) > 1 and reply[1] != "battle") or len(reply) < 2): #we're not battling? We can send data like normal...
                #make sure that the player we're connected to knows his ^ balance, tank upgrades, etc.
                reply.append(player_data[0].return_data())

                #append our special window data to the send list
                reply.append(special_window)

                #wait that 0.X seconds before we should send a packet to achieve ~1/0.X PPS at best
                time.sleep(0.125)

                #send back a response based on whether we had to perform any action, and whether we could perform it.
                netcode.send_data(player_data[1], self.buffersize, reply) #Server transmission format: [True] (success), [None] (no operation), [False, "$$$ needed"/"max"]

        # - Make sure that the client receives free hollow shells if they haven't got any for 24+ hrs -
        player_data[0].check_free_stuff()
                
        if(len(reply) > 1 and reply[1] == "battle" and running == None): #entered battle?
            print("[IN QUEUE] Player " + player_data[0].name + " has entered queue in mode: " + str(client_data[1]))
        else: #save the player's data if the player disconnected
            #print out a disconnect message, move the player data back into its place inside self.accounts so that it is saved for later...
            print("[DISCONNECT] " + player_data[0].name + " has disconnected from the server. Saving account data...",end="")
            #Save the account data...
            saved = self.logout_player(player_data)
            if(saved == True):
                print(" Successfully saved data.")
            else:
                print(" Failed to save data! Progress lost.")

    def matchmaker_loop(self):
        matchmaking_time = [] #keeps track of how long it has taken in each mode to create a match
        for x in range(0,len(self.player_queue)):
            matchmaking_time.append(time.time())

        #keeps track of which modes will have a match made on the next packet exchange. This is done to prevent players who newly join the queue from being whisked into a battle before they get a single matchmaking packet.
        making_matches = []
        for x in range(0,len(self.player_queue)): #remember: Player_queue's format is: [ [players from unrated matches], [players from ranked], etc...]
            making_matches.append(False)
        
        while True:
            with self.player_queue_lock:
                for x in range(0,len(self.player_queue)): #perform matchmaking for all game types available
                    first_iter = True
                    # - Check if there are 0 players in queue. If so, our matchmaking time gets reset -
                    if(len(self.player_queue[x]) == 0):
                        matchmaking_time[x] = time.time() #reset matchmaking time
                    while making_matches[x] == True or first_iter: #prevent new players from joining queue while the matchmaker arranges things properly (this could create problems if player ping gets too high)
                        team = None #clear our team queue variable
                        first_iter = False #make sure that the loop above knows that we are no longer on our first iteration next time the condition above gets checked! (...or first_iter)
                        if(making_matches[x] == False): #only check if we need to make a match if we're not already planning on one!
                            if(time.time() - matchmaking_time[x] > self.IMMEDIATE_MATCH and len(self.player_queue[x]) >= self.PLAYER_CT[0]): #time for an immediate match?
                                making_matches[x] = True
                            #Enough time has passed + enough players to warrant a game start?
                            elif(len(self.player_queue[x]) >= self.OPTIMAL_MATCH_CT and time.time() - matchmaking_time[x] > self.TIME_SCALING_CONSTANT / len(self.player_queue[x])):
                                making_matches[x] = True
                        if(making_matches[x] == True):
                            match_urgency = self.MAXIMUM_MATCH_TIME / (time.time() - matchmaking_time[x])
                            if(match_urgency > 1):
                                match_urgency = 1
                            elif(match_urgency < self.MIN_URGENCY):
                                match_urgency = self.MIN_URGENCY
                            #print("[MATCHMAKER] Current urgency: " + str(round(match_urgency,3)))
                            team = self.matchmake(self.player_queue[x], odd_allowed=(not self.experience_battles[x]), rating=self.experience_battles[x], urgency=match_urgency)
                            #did we get a match? Let's send them off to the battlefield, and reset our time counter!
                            #If the match failed, then we just wait a while for the matchmaker to try again...
                            making_matches[x] = False #reset making_matches to its original state
                        # - Did we get a match? -
                        if(team != None):
                            matchmaking_time[x] = time.time() #reset the matchmaking timer
                            _thread.start_new_thread(self.battle_type_functions[x],(team,))
                            team = None #reset team for next time the loop runs!
                        # - Transmit data to all sockets, and recieve data -
                        decrement = 0
                        for y in range(0,len(self.player_queue[x])):
                            #recieve packets (Format: [VIEW_CT, player_view_index]) #note: self.player_queue[x][1] = socket (recieve data)
                            if(self.player_queue[x][y - decrement][1] != "bot"): #this is NOT a bot socket?
                                data_pack = netcode.recieve_data(self.player_queue[x][y - decrement][1], self.buffersize)
                                data = data_pack[0]
                                connected = data_pack[3] #is the client still connected?
                                # - Set up the player_queue[x][y] list, and make sure that we set some fallback stats in case we don't get data from the client -
                                if(len(self.player_queue[x][y - decrement]) < 3):
                                        self.player_queue[x][y - decrement].append(0) #add a 0 to count disconnected packets.
                                #leftovers from the lobby OR a timeout occurred? Send back some base data.
                                VIEW_CT = 5
                                view_index = 0
                                if(connected): #Is this client still connected?
                                    self.player_queue[x][y - decrement][2] = 0 #we're still connected...
                                    if(data == [False]): #client asked to leave??
                                        _thread.start_new_thread(self.lobby_server, (self.player_queue[x][y - decrement],)) #back to the lobby...(extra comma is there to make sure the 2nd function argument is a tuple)
                                        print("[MATCHMAKER] Removed player " + str(self.player_queue[x][y - decrement][0].name) + " from the matchmaking queue")
                                        del(self.player_queue[x][y - decrement])
                                        decrement += 1
                                        continue #we need to move to the next iteration of this loop to avoid errors from executing lines of code below...
                                    else: #we first need to verify our data before we go ahead on using it...
                                        # - Verify our data -
                                        verified = netcode.data_verify(data, self.MATCH_PACKETS)
                                        if(verified):
                                            VIEW_CT = data[0]
                                            view_index = data[1]
                                        else: #if the data is bad AND we're not getting lobby packets...well...we can send back some generic view_ct stuff (set above about 10 lines)
                                            verify = False #check if we're still stuck in the lobby...
                                            for check_packet in self.LOBBY_PACKETS:
                                                if(netcode.data_verify(data, check_packet)):
                                                    verify = True
                                                    break
                                            if(verify): #put the player back in the lobby.
                                                _thread.start_new_thread(self.lobby_server, (self.player_queue[x][y - decrement],)) #back to the lobby...(extra comma is there to make sure the 2nd function argument is a tuple)
                                                print("[MATCHMAKER] Removed player " + str(self.player_queue[x][y - decrement][0].name) + " from the matchmaking queue due to lobby desync")
                                                del(self.player_queue[x][y - decrement])
                                                decrement += 1
                                                continue #we need to move to the next iteration of this loop to avoid errors from executing lines of code below...
                                #Server Send Format: [in_battle(True/False), viewing_players data list, player_count] (send data)
                                view_data = []
                                for b in range(0,VIEW_CT):
                                    if(b + view_index < len(self.player_queue[x])):
                                        view_data.append(self.player_queue[x][b + view_index - decrement][0].return_data())
                                    else:
                                        break
                                netcode.send_data(self.player_queue[x][y - decrement][1], self.buffersize, [True, view_data, len(self.player_queue[x])])
                                if(not connected): #we need to log this player out and remove him from the queue IF they have been disconnected for a few packets in a row.
                                    if(len(self.player_queue[x][y - decrement]) < 3):
                                        self.player_queue[x][y - decrement].append(0) #add a 0 to count disconnected packets.
                                    self.player_queue[x][y - decrement][2] += 1
                                    if(self.player_queue[x][y - decrement][2] > 3): #4 lost packets in a row? disconnect the player.
                                        #self.player_queue[x][y - decrement] is the player that disconnected.
                                        saved = self.logout_player(self.player_queue[x][y - decrement])
                                        if(saved):
                                            print("[MATCHMAKER] Successfully saved player data from user " + str(self.player_queue[x][y - decrement][0].name) + " during matchmaking")
                                        else:
                                            print("[MATCHMAKER] Failed to save player data from user " + str(self.player_queue[x][y - decrement][0].name) + " during matchmaking")
                                        del(self.player_queue[x][y - decrement])
                                        decrement += 1 #make sure we don't get an IndexError...I hate those things!!
            time.sleep(0.15) #~4PPS sounds good to me... (I'm accounting for 100ms ping)

    # - Typical battle with no stakes except losing silver - server side -
    def unrated_battle_server(self, players, forced_map=None, special_window_return=None, external_running=[True]):
        # - Start by setting up the game state: Players in their starting position, no bullets, no powerups spawned on the map -
        #Player Format: [[rating, [account, socket]], [rating, [account, socket]]...]
        #Teams format: [[[[rating, [account, socket]], [rating, [account, socket]]...], rating], [players, rating]...]
        game_objects = []
        game_objects_lock = _thread.allocate_lock()
        # - Which map are we playing on? -
        if(forced_map == None):
            map_name = self.pick_map(players)
            if(map_name == False): #we didn't get a map? (0 players in match)
                print("[BATTLE] NO MAP! Escaping battle routine...")
                return None #exit this battle!
        else:
            map_name = forced_map
        # - How much time should the players (and bots) have to finish the bots? -
        player_ct = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                player_ct += 1
        time_remaining = [self.BATTLE_TIME + self.BATTLE_TIME_PLAYER_COEFFICIENT * player_ct] #this HAS to be a list for it to be shared between threads
        # - This is for holding all particle effects. This lets people know where gunfights are happening easily because everyone gets to see them -
        particles = []
        particles_lock = _thread.allocate_lock()
        # - This is for holding team-specific particle effects. These are for confidential communications by using word particles -
        team_particles = []
        for x in range(0,len(players)): #create a particle effect list for each team
            team_particles.append([])
        team_particles_lock = _thread.allocate_lock()
        # - This list documents which teams have been eliminated -
        eliminated = [] #[team 0, team 1, team 2, etc.] Format: False = not destroyed, 1 = first destroyed, 2 = 2nd destroyed, etc.
        # - Grab our arena data -
        #   Format: [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
        arena_data = import_arena.return_arena(map_name)
        arena = arena_lib.Arena(arena_data[0], arena_data[1], arena_data[2], server=True)
        arena.set_flag_locations(arena_data[6])
        arena_lock = _thread.allocate_lock()
        # - Create a GFX manager to reduce netcode load -
        gfx = GFX.GFX_Manager()
        # - Create a SFX_Manager() so that the client has sound effects occurring at the right times -
        sfx = SFX.SFX_Manager()
        sfx.server = True
        sfx.add_sound(path + "../../sfx/gunshot_01.wav")
        sfx.add_sound(path + "../../sfx/driving.wav")
        sfx.add_sound(path + "../../sfx/thump.wav")
        sfx.add_sound(path + "../../sfx/explosion_large.wav")
        sfx.add_sound(path + "../../sfx/crack.wav")
        # - Set players in the right position -
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                if(player == 0): #add the team bookmark to the eliminated[] list.
                    eliminated.append(["Team " + str(teams), False])
                #print(players[teams][0][player]) #debug info
                game_objects.append(players[teams][0][player][1][0].create_tank("image replacement", "Team " + str(teams), upgrade_offsets=[0,0,0,0], skip_image_load=False, team_num=teams, team_ct=len(players)))
                # - Set the position our player should go to -
                game_objects[len(game_objects) - 1].goto(arena.flag_locations[teams])
        # - Start child threads to handle netcode -
        player_number = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                _thread.start_new_thread(self.battle_server, (game_objects, game_objects_lock, players[teams][0][player][1], player_number, map_name, particles, particles_lock, team_particles, team_particles_lock, arena, eliminated, time_remaining, False, teams, gfx, sfx, special_window_return, external_running))
                player_number += 1
        # - Start this thread to handle most CPU based operations -
        _thread.start_new_thread(self.battle_server_compute, (game_objects, game_objects_lock, map_name, particles, particles_lock, team_particles, team_particles_lock, arena, eliminated, gfx, sfx, time_remaining, False, external_running))

    # - This battle mode allows you to lose experience, which is needed to unlock new tanks -
    def ranked_battle_server(self, players, forced_map=None, special_window_return=None, external_running=[True]):
        # - Start by setting up the game state: Players in their starting position, no bullets, no powerups spawned on the map -
        #Player Format: [[rating, [account, socket]], [rating, [account, socket]]...]
        #Teams format: [[[[rating, [account, socket]], [rating, [account, socket]]...], rating], [players, rating]...]
        game_objects = []
        game_objects_lock = _thread.allocate_lock()
        # - Which map are we playing on? -
        if(forced_map == None):
            map_name = self.pick_map(players)
            if(map_name == False): #we didn't get a map? (0 players in match)
                print("[BATTLE] NO MAP! Escaping battle routine...")
                return None #exit this battle!
        else:
            map_name = forced_map
        # - How much time should the players (and bots) have to finish the bots? -
        player_ct = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                player_ct += 1
        time_remaining = [self.BATTLE_TIME + self.BATTLE_TIME_PLAYER_COEFFICIENT * player_ct] #this HAS to be a list for it to be shared between threads
        # - This is for holding all particle effects. This lets people know where gunfights are happening easily because everyone gets to see them -
        particles = []
        particles_lock = _thread.allocate_lock()
        # - This is for holding team-specific particle effects. These are for confidential communications by using word particles -
        team_particles = []
        for x in range(0,len(players)): #create a particle effect list for each team
            team_particles.append([])
        team_particles_lock = _thread.allocate_lock()
        # - This list documents which teams have been eliminated -
        eliminated = [] #[team 0, team 1, team 2, etc.] Format: False = not destroyed, 1 = first destroyed, 2 = 2nd destroyed, etc.
        # - Grab our arena data -
        #   Format: [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
        arena_data = import_arena.return_arena(map_name)
        arena = arena_lib.Arena(arena_data[0], arena_data[1], arena_data[2], server=True)
        arena.set_flag_locations(arena_data[6])
        arena_lock = _thread.allocate_lock()
        # - Create a GFX manager to reduce netcode load -
        gfx = GFX.GFX_Manager()
        # - Create a SFX_Manager() so that the client has sound effects occurring at the right times -
        sfx = SFX.SFX_Manager()
        sfx.server = True
        sfx.add_sound(path + "../../sfx/gunshot_01.wav")
        sfx.add_sound(path + "../../sfx/driving.wav")
        sfx.add_sound(path + "../../sfx/thump.wav")
        sfx.add_sound(path + "../../sfx/explosion_large.wav")
        sfx.add_sound(path + "../../sfx/crack.wav")
        # - Set players in the right position -
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                if(player == 0): #add the team bookmark to the eliminated[] list.
                    eliminated.append(["Team " + str(teams), False])
                #print(players[teams][0][player])
                game_objects.append(players[teams][0][player][1][0].create_tank("image replacement", "Team " + str(teams), upgrade_offsets=[0,0,0,0], skip_image_load=False, team_num=teams, team_ct=len(players)))
                # - Set the position our player should go to -
                game_objects[len(game_objects) - 1].goto(arena.flag_locations[teams])
        # - Start child threads to handle netcode -
        player_number = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])): #the True at the end is to let all threads know that this battle is for more stakes then just cash!
                _thread.start_new_thread(self.battle_server, (game_objects, game_objects_lock, players[teams][0][player][1], player_number, map_name, particles, particles_lock, team_particles, team_particles_lock, arena, eliminated, time_remaining, True, teams, gfx, sfx, special_window_return, external_running))
                player_number += 1
        # - Start this thread to handle most CPU based operations -
        _thread.start_new_thread(self.battle_server_compute, (game_objects, game_objects_lock, map_name, particles, particles_lock, team_particles, team_particles_lock, arena, eliminated, gfx, sfx, time_remaining, True, external_running))

    # - Handles most of the computation for battles, excluding packet exchanging -
    def battle_server_compute(self, game_objects, game_objects_lock, map_name, particles, particles_lock, team_particles, team_particles_lock, arena, eliminated, gfx, sfx, time_remaining, experience=False, external_running=[True]):
        battle = True #this goes false when the battle is finished.
        TILE_SIZE = 20 #this is a constant which we don't *really* need...
        framecounter = 0 #we need a framecounter for handling particle generation
        # - Grab our arena data -
        #   Format: [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
        arena_data = import_arena.return_arena(map_name)
        #arena = arena_lib.Arena(arena_data[0], arena_data[1], arena_data[2]) #this gets passed through to us from the game setup code.
        # - Set up our collision tile sets -
        blocks = arena_data[3]
        bricks = arena_data[4]
        destroyed_brick = arena_data[5]
        battle_timeout = None
        clock = pygame.time.Clock() #limit the CPU usage just a bit, ok?
        compute_timer = time.time()
        while battle:
            # - Update our framecounter -
            if(framecounter >= 65535):
                framecounter = 0
            else:
                framecounter += 1

            # - Update whether we still need to run this thread (this thread can be killed externally via the external_running parameter -
            if(battle):
                battle = external_running[0]
                if(not battle):
                    print("[BATTLE] Main compute thread ending through external killing of this process...")

            # - Update time_remaining for the battle -
            time_remaining[0] -= time.time() - compute_timer
            compute_timer = time.time()

            # - Update the state of the SFX_Manager() -
            sfx.clock([0,0])

            with particles_lock:
                # - Update all particles in the game -
                for x in particles:
                    x.clock() #keeps all the particles working properly

                # - Delete any particles which are finished their job -
                decrement = 0
                for x in range(0,len(particles)):
                    if(particles[x - decrement].timeout == True):
                        del(particles[x - decrement])
                        decrement += 1

            with team_particles_lock:
                for i in team_particles:
                    # - Update all team-specific particles (for confidential communication purposes) in the game -
                    for x in i:
                        x.clock() #keeps all the particles working properly

                    # - Delete any particles which are finished their job -
                    decrement = 0
                    for x in range(0,len(i)):
                        if(i[x - decrement].timeout == True):
                            del(i[x - decrement])
                            decrement += 1

            decrement = 0 # - Update all the "game_objects" in the game -
            with game_objects_lock:
                # - Attempt to spawn powerups -
                entity.spawn_powerups(arena,game_objects,["","","","","","","","","",""]) #the "" are dummy images...The client will have to populate those spaces with proper images.
                for x in range(0,len(game_objects)):
                    if(game_objects[x - decrement].type == "Tank"): #Are we updating a tank object?
                        if(game_objects[x - decrement].destroyed != True):
                            # - Check if we have spotted any players every 0.25ish seconds -
                            if(framecounter % 7 == 0): #every 28 frames, we check 4 times for spotting players.
                                for y in range(0,len(game_objects)):
                                    if(game_objects[y].type == "Tank" and y != x): #we need to meet some requirements before we try spotting anyone...
                                        if(game_objects[y].team != game_objects[x].team): #Are we trying to spot our own team? Ridiculous.
                                            # - The next set of requirements only pass if the game mode involves experience. If not, players are always spotted -
                                            if(experience):
                                                if(game_objects[y].spotted[game_objects[x].team_num] - time.time() < 0.1): #this player is NOT spotted (or close)?
                                                    # - Let's see if we can spot him! -
                                                    spotted = entity.check_visible(arena,[game_objects[x],game_objects[y]],blocks,vision=5)
                                                    if(spotted): #IF we spotted him, we set his spotted variable so that our whole team knows where he is.
                                                        game_objects[y].spotted[game_objects[x].team_num] = time.time() + 1.5 #X seconds of spotted before he must be in view to continue being spotted.
                                            else: #this is not an experience-based battle?
                                                game_objects[y].spotted[game_objects[x].team_num] = time.time() + 1.5
                            # - Did the client try to shoot? And, were we able to let them shoot? -
                            potential_bullet = game_objects[x - decrement].shoot(20, server=True)
                            if(potential_bullet != None): #if our gunshot was successful, we add the bullet object to our game objects list.
                                game_objects.append(potential_bullet)
                                # - Create a gunshot sound effect -
                                sfx.play_sound(self.GUNSHOT, game_objects[x - decrement].overall_location[:], [0,0])
                            game_objects[x - decrement].clock(TILE_SIZE, [1, 1], particles, framecounter, gfx) #update all tank objects
                            game_objects[x - decrement].message("This is server-side...", team_particles[game_objects[x - decrement].team_num])
                        else: #now we need to check if we exploded the tank yet....
                            if(game_objects[x - decrement].explosion_done == False): #we haven't done the explosion yet?
                                #Create a nice big explosion
                                with gfx.lock:
                                    gfx.create_explosion([game_objects[x - decrement].overall_location[0] + 0.5,game_objects[x - decrement].overall_location[1] + 0.5], 2.25, [0.1, 2.0], [[255,0,0],[255,255,0],[100,100,0]], [[0,0,0],[50,50,50],[100,100,100]], 1.0, 0, "BOOM")
                                # - Set the tank's explosion_done flag to False (I know, it's backwards, but it would break 2p_bot_demo otherwise) -
                                game_objects[x - decrement].explosion_done = True
                                # - Create some SFX -
                                sfx.play_sound(self.EXPLOSION, game_objects[x - decrement].overall_location[:], [0,0]) #the tank just blew up, so it needs to sound like it did...
                    elif(game_objects[x - decrement].type == "Bullet"): #Are we updating a bullet object?
                        if(game_objects[x - decrement].destroyed == True): #Is the bullet destroyed already?
                            del(game_objects[x - decrement])
                            decrement += 1
                            continue
                        game_objects[x - decrement].clock(gfx, framecounter) #clock the bullet
                        game_objects[x - decrement].move() #move the bullet
                        # - Check: Has the bullet hit anything? -
                        bullet_collision = game_objects[x - decrement].return_collision(TILE_SIZE)
                        collided_tiles = arena.check_collision([2,2],game_objects[x - decrement].map_location[:],bullet_collision)
                        # - A brick? -
                        for t in collided_tiles: #Format: [ [block#, collision direction, position], [block#, collision direction, position]... ]
                            if(t[0] in bricks): #we hit a brick?
                                tmp_entity = entity.Brick(6, 15) #all this does is create a blank tank object with 6HP and 15 armor. Good for checking brick damage.
                                damage_numbers = entity.handle_damage([game_objects[x - decrement], tmp_entity])
                                advance = 0
                                if(damage_numbers[1] >= 15): #we dealt 15 damage? Advance 4 spaces lol (4 tiles forwards in the brick destruction sequence)
                                    advance = 4
                                elif(damage_numbers[1] >= 7): #we dealt at least 7 damage? Advance 2 spaces (2 tiles forwards in the brick destruction sequence)
                                    advance = 2
                                elif(damage_numbers[1] >= 3): #we dealt at least 3 damage? 1 tile forward in the brick destruction sequence...
                                    advance = 1
                                # - Handle shuffling the brick tile (t[0] is the tile ID) -
                                tile_index = bricks.index(t[0])
                                if(tile_index + advance < len(bricks)): #we have enough tiles to shuffle the tiles forwards properly?
                                    arena.modify_tiles([[t[2], bricks[tile_index + advance]]])
                                else: #we just put the brick at its "destroyed" state
                                    arena.modify_tiles([[t[2], destroyed_brick]])
                                game_objects[x - decrement].destroyed = True
                                # - Add some particle effects -
                                particles.append(GFX.Particle(game_objects[x - decrement].map_location[:], game_objects[x - decrement].map_location[:], 0.5, 0.3, [175,25,25], [50,50,50], time.time(), time.time() + 1.5, str(round(damage_numbers[1],0))))
                                #Bullet stuff: self.shell_explosion_colors, self.shell_type
                                with gfx.lock:
                                    gfx.create_explosion([game_objects[x - decrement].map_location[0] + 0.5, game_objects[x - decrement].map_location[1] + 0.5], 0.65, [0.025, 0.5], game_objects[x - decrement].shell_explosion_colors[game_objects[x - decrement].shell_type], [[0,0,0],[50,50,50],[100,100,100]], 0.75, 0, None)
                                sfx.play_sound(self.CRACK, game_objects[x - decrement].map_location[:], [0,0]) #play the crack sound when the bullet hits...
                        # - A wall? -
                        if(game_objects[x - decrement].destroyed != True): #the bullet isn't destroyed yet, is it?
                            for t in collided_tiles:
                                if(t[0] in blocks):
                                    #bullet destroyed!
                                    game_objects[x - decrement].destroyed = True
                                    game_objects[x - decrement].tank_origin.missed_shots += 1 #increment the amount of shots this particular tank missed...
                                    sfx.play_sound(self.CRACK, game_objects[x - decrement].map_location[:], [0,0]) #play this sound when the bullet hits...
                                    break
                        # - Tanks? Or another bullet? -
                        if(game_objects[x - decrement].destroyed != True):
                            for y in range(0,len(game_objects)):
                                if(game_objects[y].type == "Tank"):
                                    if(game_objects[y].destroyed != True): #we're not going to waste bullets shooting a dead tank...
                                        collision = entity.check_collision(game_objects[x - decrement], game_objects[y], TILE_SIZE)
                                        if(collision[0]): #The bullet hit a tank?
                                            damage_numbers = entity.handle_damage([game_objects[x - decrement], game_objects[y]])
                                            # - Add some particle effects -
                                            if(damage_numbers != None):
                                                particles.append(GFX.Particle(game_objects[x - decrement].map_location[:], game_objects[x - decrement].map_location[:], 0.5, 0.3, [175,175,25], [50,50,50], time.time(), time.time() + 1.5, str(round(damage_numbers[1],0))))
                                                #Bullet stuff: self.shell_explosion_colors, self.shell_type
                                                with gfx.lock:
                                                    gfx.create_explosion([game_objects[x - decrement].map_location[0] + 0.5, game_objects[x - decrement].map_location[1] + 0.5], 0.65, [0.025, 0.5], game_objects[x - decrement].shell_explosion_colors[game_objects[x - decrement].shell_type], [[0,0,0],[50,50,50],[100,100,100]], 0.75, 0, "bang")
                                                sfx.play_sound(self.THUMP, game_objects[x - decrement].map_location[:], [0,0]) #play the thump sound when the bullet hits...
                                elif(game_objects[y].type == "Bullet"): #collided with a bullet? Don't need to check if it's destroyed, 'cause they don't last the whole match...
                                    collision = entity.check_collision(game_objects[x - decrement], game_objects[y], TILE_SIZE)
                                    if(collision[0]): #The bullet hit another bullet?
                                        damage_numbers = entity.handle_damage([game_objects[x - decrement], game_objects[y]])
                                        # - Add some particle effects -
                                        if(damage_numbers != None):
                                            particles.append(GFX.Particle(game_objects[x - decrement].map_location[:], game_objects[x - decrement].map_location[:], 0.5, 0.3, [200,200,25], [50,50,50], time.time(), time.time() + 1.5, str(round(damage_numbers[1],0))))
                                            particles.append(GFX.Particle(game_objects[y].map_location[:], game_objects[y].map_location[:], 0.5, 0.3, [200,25,25], [50,50,50], time.time(), time.time() + 1.5, str(round(damage_numbers[0],0))))
                                            #Bullet stuff: self.shell_explosion_colors, self.shell_type
                                            with gfx.lock:
                                                gfx.create_explosion([game_objects[x - decrement].map_location[0] + 0.5, game_objects[x - decrement].map_location[1] + 0.5], 0.65, [0.025, 0.5], game_objects[x - decrement].shell_explosion_colors[game_objects[x - decrement].shell_type], [[0,0,0],[50,50,50],[100,100,100]], 0.75, 0, "pow")
                                                gfx.create_explosion([game_objects[y].map_location[0] + 0.5, game_objects[y].map_location[1] + 0.5], 0.65, [0.025, 0.5], game_objects[y].shell_explosion_colors[game_objects[y].shell_type], [[0,0,0],[50,50,50],[100,100,100]], 0.75, 0, "pop")
                                            sfx.play_sound(self.CRACK, game_objects[x - decrement].map_location[:], [0,0]) #play the crack sound when the bullet hits...

                    elif(game_objects[x - decrement].type == "Powerup"): #Are we managing a powerup?
                        # - Check if the powerup has been collected -
                        for y in range(0,len(game_objects)):
                            if(game_objects[y].type == "Tank"): #only tanks can collect powerups
                                if(game_objects[y].destroyed != True): #tanks MAY NOT collect powerups if they're dead
                                    if(entity.check_collision(game_objects[x - decrement], game_objects[y], arena.TILE_SIZE, tank_collision_offset=5)[0]): #the tank got the powerup?
                                        game_objects[x - decrement].use(game_objects[y]) #it will despawn automatically from the code below...
                                        break
                        game_objects[x - decrement].clock() #update the powerup's state
                        if(game_objects[x - decrement].despawn == True): #despawn the powerup?
                            del(game_objects[x - decrement])
                            decrement += 1

                # - Check if any teams were eliminated (this does have to be done with entities_lock, by the way) -
                for teams in range(0,len(eliminated)):
                    if(eliminated[teams][1] != False): #this team already got eliminated? Skip the computation.
                        pass
                    else: #check if the team is eliminated
                        eliminate = True #by default, we're gonna eliminate this team unless proven otherwise.
                        for x in range(0,len(game_objects)): #find if all the tanks in a certain team are dead...(defeat for them lol)
                            if(game_objects[x].type == "Tank"):
                                if(game_objects[x].team == eliminated[teams][0] and game_objects[x].destroyed == True): #the destroyed tank is from the team we're checking?
                                    pass
                                elif(game_objects[x].team == eliminated[teams][0] and game_objects[x].destroyed != True): #this team is still alive!
                                    eliminate = False
                        if(eliminate): #the team is destroyed?
                            # - Find out what teams were destroyed before them -
                            destruction_number = 1
                            for find_destroyed in range(0,len(eliminated)):
                                if(eliminated[find_destroyed][1] >= destruction_number): #we were destroyed after another team?
                                    destruction_number = eliminated[find_destroyed][1] + 1 #make sure we know that we were destroyed after the other team.
                            # - Set our eliminated status to destruction_number, which is the order in which teams were destroyed -
                            eliminated[teams][1] = destruction_number

            # - Limit CPS -
            clock.tick(30)

            # - Purge old GFX items -
            with gfx.lock:
                gfx.purge()

            # - Check if all but one team has been eliminated OR if time is up -
            battle_end_check = 0 #this variable needs to equal len(eliminated) - 1 by the time this loop is finished for the game to end.
            for battle_end in range(0,len(eliminated)):
                if(eliminated[battle_end][1] != False): #this team got eliminated?
                    battle_end_check += 1
            if(battle_timeout != None and time.time() - battle_timeout > self.BATTLE_TIMER): #30 seconds after battle ends? Kill this thread.
                print("[BATTLE] Main compute thread ending through battle timeout...")
                break #exit the loop! We're done here!
            elif(battle_end_check >= len(eliminated) - 1 and battle_timeout == None or time_remaining[0] <= 0 and battle_timeout == None): #battle ends?
                print("[BATTLE] Game over timeout started...")
                battle_timeout = time.time() #start a timer...

    # - Player_data is a list of [account, socket].
    # - This function exchanges packets between client and server, AND stuffs the client's data into the game_objects list. It can also function as a dummy client, with a bot controlling the tank. -
    def battle_server(self, game_objects, game_objects_lock, player_data, player_index, map_name, particles, particles_lock, team_particles, team_particles_lock, arena, eliminated, time_remaining, experience=False, team_num=0, gfx=None, sfx=None, special_window_return=None, external_running=[True]):
        #Send packet description: All packets start with a "prefix", a small string describing what the packet does and the format corresponding to it.
        # - Type A) Setup packet. Very long packet, used to setup the client's game state. (Not entity related stuff; Account data, arena data, etc.)
        #       Format: ["setup", account.return_data(), map_name]
        # - Type B) Sync packet. Shorter packet, usually used to change the client's player state. In the case that a sync packet has to be used, the client MUST send back the exact same data next packet. Only used with AC enabled.
        #       Format: ["sync", server_entity.return_data()]
        # - Type C) Normal packet. Sends player data such as where entities are onscreen, the cooldown of your consumables, and your reload time.
        #       Format: ["packet",[entity1, entity2, entity3...], [list of particle effects], [list of arena tiles which need to be changed/updated]]
        # - Type D) Ending packet. Sends a simple message to the client letting the client know that the game is finished.
        #       Format: ["end"]
        # - Type E) Confirmed End packet. Sends a simple message to the client, simply letting the client know that the server has recieved the client's acknowledge about endgame.
        #       Format: ["end2"]

        # - Grab our arena data -
        #   Format: [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
        arena_data = import_arena.return_arena(map_name)
        #arena = arena_lib.Arena(arena_data[0], arena_data[1], arena_data[2]) #we don't need to set up an arena since we're sharing the one with the compute() thread.
        # - Set up our collision tile sets -
        blocks = arena_data[3]
        bricks = arena_data[4]
        destroyed_brick = arena_data[5]
        
        clock = pygame.time.Clock() #limit PPS to 20

        packet_phase = "init" #defines which type of packet we send - "setup","sync","end","end2","packet","init", OR "bot", which is used to signify that no one actually needs any data sent through this thread...
        if(player_data[1] == "bot"):
            packet_phase = "bot"
            try:
                intelligence_rating = player_data[0].requested_rating
                print("[BOT] Found requested bot rating of: " + str(round(intelligence_rating, 1)))
            except Exception as e:
                print("[BOT] Could not locate a requested rating value. Continuing based on upgrade rating...")
                intelligence_rating = pow(self.return_rating(player_data[0], experience),0.10)
            bot_computer = entity.Bot(team_num,player_index,player_rating=intelligence_rating)
            game_objects[player_index].shells[0] = 999999 #make sure bots NEVER run out of shells (by giving them lots of the worst kind: hollow)
        elif(self.ac_enable == True): #If we're NOT dealing with a bot, we need to set up a speedhax anti-cheat system.
            ac = AntiCheater()

        packet_counter = 0 #this counts packets; I use this to help tell which packets we send packet data through.

        disconnect_packets = 0 #this counts packets we sent during which the client was disconnected.

        # - This variable holds the outcome of the battle. In online mode, it is sent as a parameter to lobby_server to be displayed by the client.
        #   In offline mode, this value is copied to the special_window_return parameter so that an external process can handle displaying this value.
        special_window_str = None
        
        packets = True #are we still exchanging packets?
        #***NOTE: Sometimes this thread will get started to handle a bot client: Player_data format: [self.create_account(potential_match * 0.75),"bot"]***
        while packets:
            # - Send our data to the client -
            if(packet_phase != "bot"): #we're NOT a bot?
                if(packet_phase == "init"): #making sure the client left the matchmaker?
                    packet_data = [False,[account.Account().return_data(),account.Account().return_data()],2]
                    packet_phase = "setup" #make sure we move onto the next stage of client setup
                elif(packet_phase == "setup"): #setting up the client? tanks is needed to tell the client how many HUD HP bars and Tank entities are needed for other players...
                    tanks = []
                    with game_objects_lock: #gather player data
                        for x in game_objects:
                            if(x.type == "Tank"):
                                tanks.append(x.return_data(2,False))
                    packet_data = ["setup" ,player_data[0].return_data(), map_name, tanks]
                elif(packet_phase == "sync"): #client sync?
                    with game_objects_lock:
                        packet_data = ["sync", game_objects[player_index].return_data()]
                elif(packet_phase == "end"): #end of game? Send ALL the player data and nothing else then...
                    with game_objects_lock:
                        game_object_data = [] #gather all entity data into one list (this could be moved into the compute thread later on)
                        for x in range(0,len(game_objects)):
                            game_object_data.append(game_objects[x].return_data(2, False))
                    packet_data = ["end", game_object_data, eliminated, time_remaining[0]] #this way we can see the scoreboard at the end of the game...
                elif(packet_phase == "packet"): #typical data packet
                    with game_objects_lock:
                        game_object_data = [] #gather all entity data into one list (this could be moved into the compute thread later on)
                        for x in range(0,len(game_objects)): #This requires adding a ".spotted" timer to tanks in order to send only spotted tanks to the team.
                            if(game_objects[x].type == "Tank" and game_objects[x].team != game_objects[player_index].team and game_objects[x].spotted[game_objects[player_index].team_num] - time.time() > 0):
                                game_object_data.append(game_objects[x].return_data(2, False))
                            elif(game_objects[x].type != "Tank" or game_objects[x].type == "Tank" and game_objects[x].team == game_objects[player_index].team):
                                game_object_data.append(game_objects[x].return_data(2, False))
                    packet_data = ["packet", game_object_data]
                    # - Send particle data to client every Xnd packet -
                    if(packet_counter % 2 == 0): #it's every second packet?
                        particle_list = []
                        with particles_lock: #gather public particles
                            for x in particles:
                                particle_list.append(x.return_data())
                        with team_particles_lock: #gather private (team-specific) particles
                            for x in team_particles[game_objects[player_index].team_num]:
                                particle_list.append(x.return_data())
                        packet_data.append(particle_list) #send particle data
                        with gfx.lock:
                            packet_data.append(gfx.return_data())
                    else:
                        packet_data.append(None) #not sending particle data this packet.
                        packet_data.append(None)
                    # - Send map data to client every Xnd packet -
                    if(packet_counter % 2 == 0):
                        arena_data = []
                        for y in range(0,len(arena.arena)):
                            for x in range(0,len(arena.arena[0])):
                                if(arena.arena[y][x] in bricks or arena.arena[y][x] == destroyed_brick): #if the block is either a brick or a destroyed brick, we need to send data to the client about the tile's current state.
                                    arena_data.append([[x,y],arena.arena[y][x]]) #this format can be directly input into Arena().modify_tiles().
                        packet_data.append(arena_data)
                    else:
                        packet_data.append(None)
                    # - Send the state of all teams to the client -
                    packet_data.append(eliminated)
                    # - Send sound data to the client -
                    with sfx.lock:
                        sfx_data = sfx.return_data(game_objects[player_index].overall_location[:])
                    packet_data.append(sfx_data)
                    # - Send time_remaining -
                    packet_data.append(time_remaining[0])
                netcode.send_data(player_data[1], self.buffersize, packet_data) #send the battle data

                # - Recieve data from the client -
                # - Format:
                #   - Normal packet:["packet",Tank.return_data()]
                #   - Leave battle: ["end",Tank.return_data()]
                #   - Still need to setup (packet lost): ["setup"]
                data_pack = netcode.recieve_data(player_data[1], self.buffersize)
                data = data_pack[0] #grab our data out of the data payload
                # - Now we check if the client is still connected -
                if(data_pack[3]): #still connected?
                    disconnect_packets = 0 #we are still connected.
                    # - Handle the data we recieved -
                    # - First we check if we're getting leftovers from matchmaking -
                    verify = False
                    for x in range(0,len(self.MATCH_PACKETS)):
                        verify = netcode.data_verify(data, self.MATCH_PACKETS[x])
                        if(verify):
                            break
                    if(verify == True): #we're recieving matchmaking packets?
                        packet_phase = "init" #make sure we resent our init packet
                    else: #now we need to check if we're getting a proper ingame packet
                        # - Check if the packet is valid, starting by seeing if the player left to the lobby -
                        for x in self.LOBBY_PACKETS:
                            verify = netcode.data_verify(data, x)
                            if(verify):
                                break
                        if(verify): # - The player left to the lobby? -
                            print("[BATTLE] Connecting player " + str(player_data[0].name) + " to lobby...")
                            with game_objects_lock:
                                if(packet_phase != "end"): #we only punish the player for leaving if the battle's not over
                                    game_objects[player_index].destroyed = True
                                    player_data[0].cash *= 0.85 #decrease the player's cash by 15%
                                outcome = player_data[0].return_tank(game_objects[player_index],rebuy=True,bp_to_cash=True,experience=experience, verbose=True)
                            special_window_str = self.generate_outcome_menu(outcome, game_objects[player_index], eliminated, "- Battle Complete -")
                            _thread.start_new_thread(self.lobby_server,(player_data, special_window_str))
                            del(player_data)
                            packets = False
                        else: # - The player HAS NOT left to the lobby? -
                            verify = False
                            for x in self.GAME_PACKETS:
                                if(netcode.data_verify(data, x)):
                                    verify = True
                                    break
                            if(verify):
                                # - Handle the packet -
                                if(packet_phase == "sync"): #if we sent a sync packet beforehand, we need to check if the client followed the sync packet before we continue with normal packets.
                                    with game_objects_lock:
                                        compare_data = game_objects[player_index].return_data()
                                    #make sure the comparison is fair...index 15 will never match, so I need to make it match.
                                    #...same with data 16 and 17. Not that they won't always match, but they won't sometimes, and the server can bypass the sync on these variables without consequences.
                                    data[1][1] = compare_data[1] #1, and 3-11 don't HAVE to match, so why make them?
                                    #2 should match
                                    data[1][3] = compare_data[3]
                                    data[1][4] = compare_data[4]
                                    data[1][5] = compare_data[5]
                                    data[1][6] = compare_data[6]
                                    data[1][7] = compare_data[7]
                                    data[1][8] = compare_data[8]
                                    data[1][9] = compare_data[9]
                                    data[1][10] = compare_data[10]
                                    data[1][11] = compare_data[11]
                                    #12-14 should match
                                    data[1][15] = compare_data[15]
                                    data[1][16] = compare_data[16]
                                    data[1][17] = compare_data[17]
                                    data[1][18] = compare_data[18]
                                    data[1][19] = compare_data[19]
                                    data[1][20] = compare_data[20]
                                    data[1][21] = compare_data[21] #21-23 don't HAVE to match, so I won't make them
                                    data[1][22] = compare_data[22]
                                    data[1][23] = compare_data[23]
                                    data[1][24] = compare_data[24]
                                    data[1][25] = compare_data[25] #25 doesn't have to match either
                                    if(compare_data == data[1]): #we got the sync to happen properly?
                                        print("[BATTLE] Sync from player " + player_data[0].name + " successful")
                                        packet_phase = "packet" #if the player does not sync, the server continues to ignore the player's new coordinates.
                                elif(data[0] == "end"): #the client wants to leave now?
                                    with game_objects_lock:
                                        if(packet_phase != "end"): #we only punish the player for leaving if the battle's not over
                                            game_objects[player_index].destroyed = True
                                            player_data[0].cash *= 0.85 #decrease the player's cash by 15%
                                        outcome = player_data[0].return_tank(game_objects[player_index],rebuy=True,bp_to_cash=True,experience=experience, verbose=True)
                                    special_window_str = self.generate_outcome_menu(outcome,  game_objects[player_index], eliminated, "- Battle Complete -")
                                    if(not self.offline):
                                        _thread.start_new_thread(self.lobby_server, (player_data[1], special_window_str)) #back to the lobby...
                                        del(player_data)
                                    print("[BATTLE] Removed player " + str(player_data[0].name) + " from the battle successfully")
                                    packets = False #then it is time to leave...
                                else: #either setup packet stuff or standard packets are coming through...
                                    if(packet_phase == "setup" or data[0] == "setup"):
                                        if(data[0] == "setup"): #we need to resend the setup data if the client didn't get it
                                            packet_phase = "setup"
                                        elif(packet_phase == "setup"): #once we finish setting up the player, we need to sync his state.
                                            packet_phase = "sync"
                                    else: #normal packet - only enter data IF the player is alive by server standards!
                                        with game_objects_lock:
                                            if(game_objects[player_index].destroyed == False):
                                                # - Enter the player data into our game_objects list
                                                game_objects[player_index].enter_data(data[1], server=True) #make sure we only take the attributes a server should...
                            
                else: #client disconnected? Log him out...but we're gonna decrease his $$$ a bit first...
                    disconnect_packets += 1
                    if(disconnect_packets >= 15): #the client really disconnected? (15 lost packets in a row???)
                        with game_objects_lock: #we'll still rebuy stuff for him that he spent in battle, and generate a battle outcome string (this is NEEDED in offline mode)
                            if(packet_phase != "end"): #we only punish the player for leaving if the battle's not over
                                player_data[0].cash *= 0.85 #decrease the player's cash by 15%
                                game_objects[player_index].destroyed = True
                            outcome = player_data[0].return_tank(game_objects[player_index],rebuy=True,bp_to_cash=True,experience=experience, verbose=True)
                        special_window_str = self.generate_outcome_menu(outcome,  game_objects[player_index], eliminated, "- Battle Complete -")
                        if(not self.offline):
                            saved = self.logout_player(player_data) #try to log out the player
                            if(saved):
                                print("[BATTLE] Successfully disconnected/saved player data from user " + str(player_data[0].name) + " during battle")
                            else:
                                print("[BATTLE] Failed to save player data from user " + str(player_data[0].name) + " during battle")
                        else:
                            print("[BATTLE] Disconnected player data from user " + str(player_data[0].name) + " during battle")
                        packets = False #this thread can die now...

            # - This is for offline split-screen mode only: I need a way to end this thread and reward players & bots what they have earned as well. This happens here and is triggered when external_running[0] == False -
            if(not external_running[0]): #the client wants to leave now?
                with game_objects_lock:
                    if(packet_phase != "end"): #we only punish the player for leaving if the battle's not over AND he's not already dead (you can't die twice)
                        game_objects[player_index].destroyed = True
                        player_data[0].cash *= 0.85 #decrease the player's cash by 15%
                    outcome = player_data[0].return_tank(game_objects[player_index],rebuy=True,bp_to_cash=True,experience=experience, verbose=True)
                special_window_str = self.generate_outcome_menu(outcome,  game_objects[player_index], eliminated, "- Battle Complete -")
                print("[BATTLE] Removed player " + str(player_data[0].name) + " from the battle successfully by external ending of this server process")
                packets = False #then it is time to leave...

            # - Check if we should switch packet_phase to "end" (game over). This can happen EITHER if we are eliminated, if we win, OR if we run out of time. -
            win = 0
            for x in eliminated:
                if(x[0] == game_objects[player_index].team and x[1] != False): #our team is destroyed? End flag it is...IF we're NOT a bot!!!
                    if(packet_phase == "bot"):
                        packets = False
                    else: #then we can let the client (not a bot) know it's end time
                        packet_phase = "end"
                    break
                elif(x[1] != False):
                    win += 1
            if(win >= len(eliminated) - 1): #all teams were eliminated BUT ourselves?
                if(packet_phase != "bot"):
                    packet_phase = "end"
                else: #just kill the thread...
                    packets = False
            if(time_remaining[0] <= 0): #we ran out of time?
                if(packet_phase != "bot"):
                    packet_phase = "end"
                else: #just kill the thread...
                    packets = False

            if(packet_phase == "bot"): #this is a bot player's thread? Let's do some bot computing!
                all_blocks = blocks[:] #grab all blocks the bot cannot move through
                for x in bricks:
                    all_blocks.append(x)
                with game_objects_lock:
                    tanks = [] #gather all tanks from game_objects
                    for x in game_objects:
                        if((x.type == "Tank")):
                            tanks.append(x)
                    bullets = [] #gather all bullets from game_objects
                    for x in game_objects:
                        if(x.type == "Bullet" and x.team != game_objects[player_index].team):
                            bullets.append(x)
                    potential_bullet = bot_computer.analyse_game(tanks,bullets,arena,arena.TILE_SIZE,all_blocks,screen_scale=[1,1],tank_collision_offset=2)
                    if(potential_bullet != None): #did the bot shoot?
                        game_objects.append(potential_bullet)
                        # - Create a gunshot sound effect so that this bot actually makes sound -
                        sfx.play_sound(self.GUNSHOT, game_objects[player_index].overall_location[:], [0,0])
            elif(self.ac_enable == True): #ONLY if this player is NOT a bot, we need to do some Anti-Cheat stuff to prevent speedhax...
                all_blocks = blocks[:] #grab all blocks the bot cannot move through
                for x in bricks:
                    all_blocks.append(x)
                with game_objects_lock:
                    cheater = ac.clock(game_objects[player_index], arena, all_blocks)
                    if(cheater): #We did catch this player cheating?
                        return_pos = ac.find_last_uncheat_pos() #Get the last position he was in where he WASN'T using speedhax
                        if(return_pos != None): #If we could get a position, we're gonna use it to force him to return to the last position he was in BEFORE using speedhax
                            #I address each individual value of the position list because otherwise some annoying pointers get lost and the player doesn't receive the right position.
                            game_objects[player_index].goto(return_pos)
                            packet_phase = "sync" #force the client to sync to the position we just decided was the last non-cheating position
                            print("[BATTLE] Player " + str(player_data[0].name) + " has cheated - New position: [" + str(round(game_objects[player_index].overall_location[0],1)) + ", " + str(round(game_objects[player_index].overall_location[1],1)) + "]")
                        
            clock.tick(20) #limit PPS to 20

        # - IF we're trying to get our special_window_str value to somewhere outside of this function...(offline mode) we need to make that possible here -
        if(self.offline):
            special_window_return.append([player_data[0].name, player_data[0].password, special_window_str])

    def generate_outcome_menu(self, rebuy_data, tank, eliminated_order, title): #generates the menu string which needs to be transmitted to the client to form a "special menu/window".
        # - Calculate some statistics about player performance -
        total_shots = 0
        for x in tank.shells_used:
            total_shots += x
        if(total_shots == 0): #make sure we don't get div0 errors when calculating accuracy...
            total_shots += 1
        total_powerups = 0
        for x in tank.powerups_used:
            total_powerups += x
        # - Check if we won, or if we got 2nd, 3rd, 4th...etc. place or a TIE -
        alive_ct = [] #this is used to check if we got a tie between other teams
        for x in eliminated_order:
            if(x[0] == tank.team):
                team_pos = x[1]
            else:
                if(x[1] == False): #bookmark all the OTHER teams which DIDN'T die
                    alive_ct.append(x)
        if(team_pos == False and len(alive_ct) == 0): #we won (weren't destroyed) and no one else was alive?
            team_pos = "Victory"
        elif(team_pos == False and len(alive_ct) > 0): #we weren't destroyed, but others weren't as well? (we ran out of time)
            team_pos = str(len(alive_ct) + 1) + " - way tie"
        else:
            place_english = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th","11th","12th","13th","14th","15th","16th"]
            team_pos = place_english[team_pos] + " place"
        # - Generate the outcome menu -
        return [ #rebuy_data format: [earned, shell_cost, pu_cost, net earnings, net experience]
            "Back",
            "",
            "Battle Outcome - " + team_pos,
            "",
            "Earnings",
            "^ before rebuy - " + str(round(rebuy_data[0],2)) + "^",
            "Shell costs - " + str(round(rebuy_data[1],2)) + "^",
            "Powerup costs - " + str(round(rebuy_data[2],2)) + "^",
            "Net ^ - " + str(round(rebuy_data[3],2)) + "^",
            "Net experience - " + str(round(rebuy_data[4],2)) + " EXP",
            "Hollow shells used - " + str(tank.shells_used[0]),
            "Regular shells used - " + str(tank.shells_used[1]),
            "Explosive shells used - " + str(tank.shells_used[2]),
            "Disk shells used -  " + str(tank.shells_used[3]),
            "Powerups used - " + str(total_powerups),
            "",
            "Performance Stats",
            "Total damage - " + str(round(tank.total_damage,2)),
            "Kills - " + str(tank.kills),
            "Shots fired - " + str(total_shots),
            "Shots missed - " + str(tank.missed_shots),
            "Shooting accuracy - " + str(round(100 * (total_shots - tank.missed_shots) / total_shots, 2)) + "%",
            title
            ]

    def pick_map(self, players): #players is the TEAMs list. [[players, rating],[players, rating]]
        # - Find out exactly how many players we are gonna need to host within one map -
        player_ct = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                player_ct += 1
        # - Find out which maps (if any) can support this amount of players -
        map_counter = 0
        available_maps = []
        while True:
            potential_map = import_arena.return_arena_numerical(map_counter) #get our potential map
            map_counter += 1 #increment our map counter
            
            if(potential_map != None): #this is a valid map; NOW we need to check whether it will host as many players as we want & if it has the correct amount of teams.
                if(len(potential_map[0][6]) == len(players)): #do we have the right number of teams?
                    pass
                else:
                    continue #Next...this map is unsuitable
                # - Get the total area of the map in tiles -
                # - Potential_map[0][0] is the map itself, potential_map[0][1] is the map's tiles, potential_map[1] is the map's name, and potential_map[0][3, 4] give the tiles the player can not run through.
                tiles = 0 #we're going to count...how many tiles of FREE SPACE does this map have?
                blocks = []
                for x in range(0,len(potential_map[0][3])):
                    blocks.append(potential_map[0][3][x])
                for x in range(0,len(potential_map[0][4])):
                    blocks.append(potential_map[0][4][x])
                for y in range(0,len(potential_map[0][0])):
                    for x in range(0,len(potential_map[0][0][y])):
                        if(potential_map[0][0][y][x] in blocks):
                            pass
                        else:
                            tiles += 1
                if(player_ct != 0 and tiles / player_ct >= self.MIN_SQUARES_PER_PERSON and tiles / player_ct <= self.MAX_SQUARES_PER_PERSON): #will it host as many players as we want????????
                    #YES!
                    if(len(potential_map[0][6]) == len(players)): #we have the right amount of bases for the amount of teams we have?
                        #YES!
                        available_maps.append(potential_map[1]) #just append the map's name, nothing else. We can get the map's data later using import_arena.
                elif(player_ct == 0):
                    return False #we need to put an end to a battle with no players...
                else:
                    #NO...
                    pass
            else:
                break
        # - Now that we've found the available maps, we need to choose from them. If there were too many players, a random map is chosen then -
        if(len(available_maps) > 0): #we have maps which can host the amount of players we want?
            battle_map = available_maps[random.randint(0,len(available_maps) - 1)]
        else: #just pick a random map then...but MAKE sure it has the right number of teams!
            map_counter = 0
            while True:
                potential_map = import_arena.return_arena_numerical(map_counter) #get our potential map
                map_counter += 1 #increment our map counter
                
                if(potential_map != None):
                    # - Potential_map[0][0] is the map itself, potential_map[0][1] is the map's tiles, potential_map[1] is the map's name
                    if(len(potential_map[0][6]) == len(players)): #we have the right amount of bases for the amount of teams we have?
                            #YES!
                            available_maps.append(potential_map[1]) #just append the map's name, nothing else. We can get the map's data later using import_arena.
                    else:
                        #NO...
                        pass
                else:
                    break
            battle_map = available_maps[random.randint(0,len(available_maps) - 1)]
        return battle_map #just returns the map name, nothing more.

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

    # - Creates an account with upgrades which correspond roughly to the rating value you input. NOTE: target_bot_rating is for intelligence rating, not normal rating -
    def create_account(self,rating,player_name="Bot Player",target_bot_rating=None):
        bot_account = account.Account(player_name,"pwd",True,target_bot_rating) #create a bot account
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

    #***Player_queue MUST be locked while matchmaking to avoid index errors***
    #player_queue is a list: [ [account, client socket], [account, client socket] ... ]
    def matchmake(self, player_queue, odd_allowed=False, rating=False, urgency=1.0, target_bot_ct=None, forced_team_ct=None, target_bot_rating=None): #creates a match from the player queue
        # - self.PLAYER_RULES is a list of rules which EACH player has to meet to be added to a match -
        #   - Usable variables:
        #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
        #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
        #           - It is defined above as a parameter of matchmake().
        #       - players is a list of all players on the team, in the format [rating, [account, socket]]
        #       - player is a list containing this player's data: [rating, [account, socket]]

        # - How matches are made -
        # 1) Sort players according to strength. Strongest are first, weakest are last.
        # 2) Create matches with every possible number of teams.
        # 3) Add players to the teams as evenly as possible, starting with the strongest player and ending with the weakest player.
        # 4) Use the match where players are balanced as evenly as possible between teams, and discard the others.

        # - Start by seeing if there's enough players for a match! -
        match = []
        # - We always start by adding the first player in the queue to the match, and then seeing how many other players we can add after him -
        if(len(player_queue) > 0): #there HAS to be players in the queue for this to work...
            #print("[MATCH] Phase I begin! Find enough players!") #debug
            potential_players = 1 #this tells us how many players we COULD have in a match (if the matchmaker pays as little regard to balance as possible)
            player_ct = 1
            # - This becomes *very* important for choosing bot difficulty ratings and account ratings, as they will try hit 0.75*avg_player_rating account rating to be competitive -
            avg_player_rating = 0
            avr_ct = 0
            #   - Usable variables for individual player rules:
            #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
            #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
            #       - first_player is a variable storing the rating of the first player added to the match.
            first_player = self.return_rating(player_queue[0][0], rating)
            #       - player is a list containing this player's data: [rating, [account, socket]]
            #           - This will have to be defined within the loop which checks rules.
            for x in range(1,len(player_queue)): #now we check if anyone else can join the match
                add = True
                # - player is a list containing this player's data: [rating, [account, socket]] -
                player = [self.return_rating(player_queue[x][0],rating),player_queue[x]]
                for rule in self.PLAYER_RULES: #this loop determines whether this player can enter THIS match
                    if(eval(rule)):
                        pass
                    else:
                        add = False
                    if(not add):
                        break
                if(add):
                    player_ct += 1
                    # - Also add this player's rating to the average -
                    avg_player_rating = (avg_player_rating * avr_ct + player[0])/(avr_ct + 1)
                    avr_ct += 1
                # - Check whether the player *could* enter this match IF urgency = self.MIN_WAIT_ADD_URGENCY
                #   (used to help the matchmaker whether to make the first available match or wait longer) -
                potential_add = True
                old_urgency = urgency
                urgency = self.MIN_WAIT_ADD_URGENCY
                for rule in self.PLAYER_RULES:
                    if(eval(rule)):
                        pass
                    else:
                        potential_add = False
                    if(not potential_add):
                        break
                if(potential_add):
                    potential_players += 1
                urgency = old_urgency
            # - Was there enough players for a match? ANNND...is there enough to get a GOOD match going if we wait a little longer? -
            if(player_ct >= self.OPTIMAL_MATCH_CT or player_ct >= potential_players and player_ct >= self.PLAYER_CT[0] and urgency <= self.FORCED_MATCH_URGENCY):
                #print("[MATCH] Phase I Complete: Found " + str(player_ct) + " players...Beginning Phase II: Add players to teams.") #debug
                min_teams = self.TEAM_CT[0] #figure out how many teams we can have
                max_teams = player_ct
                if(max_teams > self.TEAM_CT[1]):
                    max_teams = self.TEAM_CT[1]
                if(max_teams < self.TEAM_CT[0]): #this can occur if only 1 player is in queue.
                    max_teams = self.TEAM_CT[0]
                if(forced_team_ct != None): #if this parameter is set to a number, we MUST have that number of teams in this match (used for offline mode)
                    min_teams = forced_team_ct
                    max_teams = forced_team_ct
                matches = []
                for generate_matches in range(min_teams, max_teams + 1): #try generating matches with ANY number of teams possible (1 player per team minimum, 4 teams maximum)
                    # - Start adding players to a new match! -
                    match = []
                    for x in range(0,generate_matches): #prepare a match list with space for teams
                        match.append([[], 0.0]) #match format: match[ team[ players[ [rating,[account,socket]]...], team rating ]
                    # - Add the first player in the queue to our match -
                    match[0][0].append([self.return_rating(player_queue[0][0], rating),player_queue[0]])
                    match[0][1] += self.return_rating(player_queue[0][0], rating)
                    # - Start adding other players into the match by seeing which team has the least rating, and adding the player there -
                    #   - Usable variables for individual player rules:
                    #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
                    #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
                    #       - first_player is a variable storing the rating of the first player added to the match.
                    #       - player is a list containing this player's data: [rating, [account, socket]]
                    #           - It usually has to be defined within the player evaluation loop because it needs to be changed for each player.
                    for x in range(1,len(player_queue)): #we don't need to re-add the first player to the queue, which is why I start at 1.
                        add = True #do we add this player or not??
                        # - player is a list containing this player's data: [rating, [account, socket]] -
                        player = [self.return_rating(player_queue[x][0],rating),player_queue[x]]
                        for rule in self.PLAYER_RULES:
                            if(eval(rule)):
                                pass
                            else:
                                add = False
                            if(not add):
                                break
                        if(add): #we're adding this player to the match!
                            # - Now we need to check: Which team do we add this player to?? -
                            #   - This is done by checking which team is the weakest by rating, and adding the player to that team.
                            least_powerful_team = 0
                            least_powerful_team_rating = match[0][1] #set this to the rating of the first team for now
                            for team in range(0,len(match)):
                                if(match[team][1] < least_powerful_team_rating): #we found a less powerful team?
                                    least_powerful_team_rating = match[team][1] #make sure we remember this team.
                                    least_powerful_team = team
                            match[least_powerful_team][0].append([self.return_rating(player_queue[x][0],rating), player_queue[x]])
                            match[least_powerful_team][1] += self.return_rating(player_queue[x][0],rating)
                    matches.append(match) #add this to a list of *possible* matches
            else: #match failed.
                print("[MATCH] Match failed on account of sub-optimal player count; Urgency=" + str(round(urgency,2)) + "; Player_queue=" + str(len(player_queue)) + "; Player_ct=" + str(player_ct) + ";")
                match = None
        else: #match failed.
            match = None

        # - Now we find which match is the most balanced, and use it to continue -
        if(match != None):
            balance = []
            for x in range(0,len(matches)): #matches[x] = match.
                rating = [] #find the imbalance in a particular potential match
                for team in range(0,len(matches[x])):
                    rating.append(matches[x][team][1])
                diff = 0
                for b in rating:
                    for y in rating:
                        if(abs(b - y) > diff):
                            diff = abs(b - y)
                balance.append(diff)
            # - Find which value in balance[] is smallest, which gives us the index of the match we should proceed with -
            smallest = balance[0]
            ind = 0
            for x in range(0, len(balance)):
                if(balance[x] < smallest):
                    smallest = balance[x]
                    ind = x
            # - Set match to matches[ind], as it is the most balanced -
            match = matches[ind]

        #Player Format: [[rating, [account, socket]], [rating, [account, socket]]...]
        #Teams format: [[[[rating, [account, socket]], [rating, [account, socket]]...], rating], [players, rating]...]

        # - Now we take the match we created, and we check if it is valid, starting by defining what the matchmaking variables will be -
        #   - Matchmaker variables:
        #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
        #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
        #           - This variable is defined as a parameter of this function.
        #       - player_counts[] is a list which holds the count of each team's players
        if(match != None): #we actually got a match?
            player_counts = []
            for teams in match:
                count = 0
                for players in teams[0]:
                    count += 1
                player_counts.append(count)
            #       - team_ratings[] is a list which holds the rating of each team
            team_ratings = []
            for teams in match:
                team_ratings.append(teams[1])
            #       - max_team_rating is a variable storing the most powerful team rating
            max_team_rating = 0
            for most_powerful in team_ratings:
                if(most_powerful > max_team_rating):
                    max_team_rating = most_powerful
            #       - min_team_rating is a variable storing the least powerful team rating
            min_team_rating = team_ratings[0]
            min_team_rating_index = 0 #this is required so that I know which team gets a bot.
            counter = 0
            for least_powerful in team_ratings:
                if(least_powerful < min_team_rating):
                    min_team_rating = least_powerful
                    min_team_rating_index = counter
                counter += 1
            # - BREAK from defining rules temporarily: Now that we have the player ratings of all teams, it is a good time to add bots! -
            #   - The teams other than the strongest always gets a bot to help them out, provided that the bot can be created greater than self.IMBALANCE_LIMIT.
            #   - A bot will be added to the match on all teams with NO real players even if the bot must be of rating LESSER than self.IMBALANCE_LIMIT.
            created_bot = 0 #we record how many bots we add to preserve match integrity so that we can TRY hitting target_bot_ct number of bots.
            for team in range(0,len(match)):
                total_team_players = len(match[team][0])
                if(max_team_rating - match[team][1] > self.IMBALANCE_LIMIT or total_team_players == 0):
                    if(total_team_players == 0 and max_team_rating - match[team][1] < self.IMBALANCE_LIMIT):
                        if(max_team_rating - match[team][1] <= 0): #we WILL NOT create a 0-rating bot.
                            continue
                        planned_rating = self.IMBALANCE_LIMIT
                    else:
                        planned_rating = max_team_rating - match[team][1]
                    # - Index 1 of the bot player data MUST be equal to "bot" to make the bot scripts begin in the game's main loop
                    #   The bot's reported rating is less than the ACTUAL rating so that the bots have an advantage over players through resources, if not in skill -
                    match[team][0].append([planned_rating, [self.create_account(planned_rating * self.IMBALANCE_LIMIT, "Bot BT" + str(team),target_bot_rating),"bot"]]) #get the bot in the game
                    match[team][1] += planned_rating #update the team's rating so that it represents the bot being added to the match
                    player_counts[team] += 1 #update the player_counts list to match the amount of players in each team now
                    created_bot += 1
            # - Now we also just add some bots to each team to make things interesting -
            team_counter = 0
            bot_ct = (self.OPTIMAL_MATCH_CT - player_ct) / len(match) #how many bots do we need per team to make things interesting?
            if(bot_ct < 0): #no quantities of bots below 0 (this can be overridden with the target_bot_ct parameter)
                bot_ct = 0
            bot_ct = int(math.ceil(bot_ct)) #round the number up to the nearest large integer so I can use it for iteration
            # - IF an override is given, we CAN end up in a situation where we want 0 bots. We'll calculate how many bots we should have in the game in THAT case here -
            if(target_bot_ct != None):
                bot_ct = int(math.ceil((target_bot_ct - created_bot) / len(match)))
            # - Find what rating each bot should be based on the average rating of players in this match -
            if(avg_player_rating * 0.95 < self.IMBALANCE_LIMIT): #if the players are gonna be this weak...we're just gonna have to make the bots a bit stronger
                #since avg_player_rating isn't used ANYWHERE else, I can change the value here with NO consequence
                avg_player_rating = self.IMBALANCE_LIMIT / 0.94 #make it so the bots just *barely* make it past self.IMBALANCE_LIMIT checks (minimum bot rating)
            for team in match:
                for add in range(0,bot_ct): #bot intelligence rating is chosen somewhere else...so it will have to be done based on the account rating given here.
                    team[0].append([avg_player_rating * 0.95, [self.create_account(avg_player_rating * 0.95,"Bot T" + str(team_counter) + "P" + str(add),target_bot_rating),"bot"]])
                team_counter += 1
            # - Now that I have added bots to all teams, I have to recalculate several rule variables since the team ratings have changed -
            #       - team_ratings[] is a list which holds the rating of each team
            team_ratings = []
            for teams in match:
                team_ratings.append(teams[1])
            #       - max_team_rating is a variable storing the most powerful team rating
            max_team_rating = 0
            for most_powerful in team_ratings:
                if(most_powerful > max_team_rating):
                    max_team_rating = most_powerful
            #       - min_team_rating is a variable storing the least powerful team rating
            min_team_rating = team_ratings[0]
            min_team_rating_index = 0 #this is required so that I know which team gets a bot.
            counter = 0
            for least_powerful in team_ratings:
                if(least_powerful < min_team_rating):
                    min_team_rating = least_powerful
                    min_team_rating_index = counter
                counter += 1
            # - END RATING VARIABLE RECALCULATIONS -
            #       - max_team_players is a variable storing the most players on a team
            max_team_players = 0
            for most_players in player_counts:
                if(most_players > max_team_players):
                    max_team_players = most_players
            #       - min_team_players is a variable storing the least players on a team
            min_team_players = (self.PLAYER_CT[1] / 2)
            for least_players in player_counts:
                if(least_players < min_team_players):
                    min_team_players = least_players
            #       - max_player_rating is a variable storing the most powerful player in the match
            max_player_rating = 0
            for teams in match:
                for player in teams[0]:
                    if(player[0] > max_player_rating):
                        max_player_rating = player[0]
            #       - min_player_rating is a variable storing the least powerful player in the match
            min_player_rating = pow(10,10) #set this to a rating so high nobody could reasonably achieve it
            for teams in match:
                for player in teams[0]:
                    if(player[0] < min_player_rating):
                        min_player_rating = player[0]
            #       - bot_rating[] is a list: [rating, team index]
            bot_rating = [0.00001, 0] # - Find the bot! There can be multiple, but their names always start with "Bot", and password is "pwd"
            team_index = 0
            found = False
            for teams in match:
                for player in teams[0]:
                    if(found == False):
                        if(player[1][0].name[0:3] == "Bot" and player[1][0].password == "pwd"):
                            bot_rating[0] = player[0]
                            bot_rating[1] = team_index
                            found = True
                    else: #this only applies once we've already found A bot. However, it might not be the lowest rating bot in the match...
                        if(player[1][0].name[0:3] == "Bot" and player[1][0].password == "pwd"):
                            if(player[0] < bot_rating[0]): #this bot's rating IS lower than the one we WERE thinking of?
                                bot_rating[0] = player[0] #well now all eyes are on IT!
                                bot_rating[1] = team_index
                team_index += 1
            if(not found or player_ct == 1): #We don't have a bot in the game? OR, did we INTENTIONALLY add a bot with a low rating because there was only 1 real player in this game?
                bot_rating[0] = self.IMBALANCE_LIMIT #just ensure that the bot rating will pass the requirements
            #       - player_ratings[] is a list of lists: [ [team 0 players: 0.9, 5.5, 6.2], team 1 players: [5.1, 8.9, 9.1]... ]
            #           - The first player rating is always the strongest player,
            #           - and the last player rating for each team is always the weakest player.
            player_ratings = []
            for teams in match:
                player_ratings.append([])
                for player in teams[0]:
                    player_ratings[len(player_ratings) - 1].append(player[0])
            # - Now we evaluate our rules, and if all of them return True, we can continue the match! -
            match_allowed = True
            for x in self.RULES:
                if(eval(x)): #the rule worked?
                    pass
                else: #uhoh, our match won't work!
                    print("[MATCH] Match failed on rule: " + str(x)) #good debug info on why matches won't start
                    match_allowed = False
                    break
        else: #if we didn't even get a match to evaluate, the match DEFINITELY failed.
            match_allowed = False
        # - Did the match succeed? -
        if(match_allowed):
            print("[MATCH] Successful match made; Teams=" + str(len(match)) + "; Players=" + str(player_ct) + ".")
            # - Delete all the players in the match out of the player_queue[] before the match starts -
            for team in match:
                for player in team[0]:
                    # - Now we compare this player to every player in player_queue[] and delete his player_queue[] instance of himself -
                    for queue_instance in range(0,len(player_queue)):
                        if(player_queue[queue_instance][0].name == player[1][0].name and player_queue[queue_instance][0].password == player[1][0].password):
                            del(player_queue[queue_instance]) #get rid of the player_queue[] instance of the player
                            break #exit this loop to prevent index errors
            # - Now we can return the match to the matchmaker, which will start the server code for the battle -
            return match
        else: #...no =(
            return None

# - This class watches ONE Tank() object's movement patterns to see if the tank is using speedhax of any sort. It checks turning speed and movement speed.
#   - It also checks whether the tank is allowed to be in the location it currently is in. If it is outside the maze, it is teleported back to a permitted location - #
class AntiCheater():
    def __init__(self):
        self.POS_RECORD_CT = 32
        self.CHEATING_THRESHOLD = 1/16 #if a player is flagged as cheating for POS_RECORD_CT * CHEATING_THRESHOLD positions, they're in TROUBLE!!
        self.last_positions = [] #this list records POS_RECORD_CT positions of the tank being watched. These are used to detect movement which is faster than should be allowed.
        self.POS_RECORD_INTERVAL = 0.125 #Every X seconds we will record a new position for the tank we're watching.
        self.last_record = time.time()
        self.first_cheat = None #this stores the index of the first position where a player was flagged for cheating.
        self.BEFORE_CHEAT = 8 #when we return the position speedhax cheaters should return to, we're going to return a position BEFORE_CHEAT indexes behind self.first_cheat.
        #How much beyond a player's speed will we permit the tank being watched to go WITHOUT sending a sync() call to make it return to the last NON-CHEATING spot?
        self.AC_THRESH = 1.325 #This is useful for helping people with inconsistent internet connections from always teleporting around.
        self.speed_max = None #Since a tank's speed can change (speed boosts?), we need to know the MAXIMUM speed it is ALLOWED to go recently.
        self.last_speed_update = time.time() #we only need a maximum speed allowance to last until all data samples holding that speed have been emptied from self.last_positions.
        #This value is from Entity.py and needs to be the same as the value in Entity.py. It is used to detect when a player has rounded a corner without turning, which really throws off the Anti-Cheat without knowing this value.
        self.POS_CORRECTION_MAX_THRESHOLD = 0.25
        #This value sets how strict the cheater detection is on when players try to drive through walls. NEVER set it higher than 0.49; The game will malfunction. Higher numbers are more strict.
        self.CLIP_THRESHOLD = 0.40

    def clock(self, tank_object, arena, blocks):
        # - Only check speedhax every 1/POS_RECORD_INTERVAL times per second -
        if(time.time() - self.last_record > self.POS_RECORD_INTERVAL):
            # - Check what our top speed is at MAX, and record it for use when checking for speedhax -
            if(self.speed_max == None or tank_object.speed > self.speed_max):
                self.speed_max = tank_object.speed
                self.last_speed_update = time.time()
            elif(time.time() - self.last_speed_update > self.POS_RECORD_CT / self.POS_RECORD_INTERVAL):
                self.speed_max = tank_object.speed
            # - Update the timer which controls when we record new position data -
            self.last_record = time.time()
            # - Update self.last_positions with new tank position data -
            self.last_positions.append([ tank_object.overall_location[:], time.time() ])
            if(len(self.last_positions) > self.POS_RECORD_CT):
                self.last_positions.pop(0)
            if(len(self.last_positions) < 2): #we might not have enough data to make any good analysis...and division by zero happens with only one data sample.
                return False
            # - Calculate the maximum speed allowed when taking into account self.AC_THRESH -
            max_speed = self.speed_max * self.AC_THRESH
            # - Check each individual position record to the one next to it -
            cheating_ct = [0, 0] #cheating, not cheating
            self.first_cheat = None #this records the index of the first position which indicated cheating
            for x in range(0,len(self.last_positions) - 1):
                dist_x = abs(self.last_positions[x + 1][0][0] - self.last_positions[x][0][0])
                dist_y = abs(self.last_positions[x + 1][0][1] - self.last_positions[x][0][1])
                dist = dist_y + dist_x
                diff_time = self.last_positions[x + 1][1] - self.last_positions[x][1]
                if(dist_y <= self.POS_CORRECTION_MAX_THRESHOLD or dist_x <= self.POS_CORRECTION_MAX_THRESHOLD): #no turning occurred; We only need to check transport speed.
                    speed = dist / diff_time
                    if(speed > max_speed): #We're going too fast?
                        cheating_ct[0] += 1 #CHEATER!!
                        if(self.first_cheat == None):
                            self.first_cheat = x
                    else:
                        cheating_ct[1] += 1 #You're fine...keep playing.
                else: #turning occurred; We need to take into account turning time along with transport speed.
                    remaining_time = diff_time - (0.5 / self.AC_THRESH) / max_speed #time is needed to turn; We take this time needed off of diff_time to see how much extra time there is to actually drive.
                    if(remaining_time > 0):
                        speed = dist / remaining_time
                    else:
                        speed = 0
                    if(speed > max_speed or remaining_time < 0): #if we had no time to move, then we shouldn't have been able to move.
                        cheating_ct[0] += 1 #CHEATER!!!
                        if(self.first_cheat == None):
                            self.first_cheat = x
                    else:
                        cheating_ct[1] += 1 #You're fine...keep playing (and win for me, will you?)
            if(cheating_ct[0] > self.POS_RECORD_CT * self.CHEATING_THRESHOLD): #Was there a LOT of positions which indicated cheating?
                #CHEATER!!!
                return True
            else: #We'll do ONE MORE check...seeing where we moved from the START to the END of self.last_positions and seeing if we OVERALL were going too fast...
                min_xy = [self.last_positions[0][0][0], self.last_positions[0][0][1]]
                max_xy = [self.last_positions[0][0][1], self.last_positions[0][0][1]]
                for x in range(0,len(self.last_positions)):
                    if(self.last_positions[x][0][0] < min_xy[0]):
                        min_xy[0] = self.last_positions[x][0][0]
                    if(self.last_positions[x][0][1] < min_xy[1]):
                        min_xy[1] = self.last_positions[x][0][1]
                    if(self.last_positions[x][0][0] > max_xy[0]):
                        max_xy[0] = self.last_positions[x][0][0]
                    if(self.last_positions[x][0][1] > max_xy[1]):
                        max_xy[1] = self.last_positions[x][0][1]
                # - Take our min/max XY values and use them to determine the amount of distance we traveled -
                dist_x = abs(max_xy[0] - min_xy[0])
                dist_y = abs(max_xy[1] - min_xy[0])
                dist = dist_x + dist_y
                diff_time = self.last_positions[0][1] - self.last_positions[len(self.last_positions) - 1][1]
                if(dist_x <= self.POS_CORRECTION_MAX_THRESHOLD or dist_y <= self.POS_CORRECTION_MAX_THRESHOLD): #turning was not used, so we simply need to watch distance traveled to determine if the player is cheating
                    speed = dist / diff_time
                    if(speed > max_speed): #CHEATER!!!
                        return True
                    else: #Not cheating
                        pass
                else: #the player DID turn, so we need to take this into account when checking for speedhax
                    remaining_time = diff_time - (0.5 / self.AC_THRESH) / max_speed
                    if(remaining_time > 0):
                        speed = dist / remaining_time
                    else:
                        speed = 0
                    if(speed > max_speed): #CHEATER!!!
                        return True
                    else:
                        pass
        # - Also check whether we exited the arena boundaries (position reset if we do?) -
        if(tank_object.overall_location[0] < len(arena.arena[0]) - 1): #this lets us technically clip into the far-right boundary of the arena, but I need to let players do that to accomodate slow machines (which let players clip sometimes).
            if(tank_object.overall_location[0] > 0): #we can also clip into the far-left boundary of the arena...but as soon as we exit it...
                if(tank_object.overall_location[1] > 0): #again, we *can* clip into the top boundary of the arena; As soon as we leave the boundary though, we're in trouble.
                    if(tank_object.overall_location[1] < len(arena.arena) - 1): #again, we *can* clip into the bottom boundary of the arena. As soon as we go beyond it, we'll be TPed back into the game though...
                        pass #not cheating
                    else: #we cheated; we're outside the map
                        if(self.first_cheat == None):
                            self.first_cheat = len(self.last_positions) - 1
                        return True
                else: #we cheated; we're outside the map
                    if(self.first_cheat == None):
                        self.first_cheat = len(self.last_positions) - 1
                    return True
            else: #we cheated; we're outside the map
                if(self.first_cheat == None):
                    self.first_cheat = len(self.last_positions) - 1
                return True
        else: #we cheated; we're outside the map
            if(self.first_cheat == None):
                self.first_cheat = len(self.last_positions) - 1
            return True
        # - Also check if we tried to glitch into a wall -
        rounded_position = [
            int(round(tank_object.overall_location[0],0)),
            int(round(tank_object.overall_location[1],0))
            ]
        # - If these values are BELOW self.CLIP_THRESHOLD, and rounded_position has a block on it, we're (1.0 - self.CLIP_THRESHOLD) * 100% embedded in a block (blatant cheating) -
        round_diff = [abs(rounded_position[0] - tank_object.overall_location[0]), abs(rounded_position[1] - tank_object.overall_location[1])]
        if(rounded_position[0] >= 0 and rounded_position[0] < len(arena.arena[0]) and rounded_position[1] >= 0 and rounded_position[1] < len(arena.arena)):
            if(arena.arena[rounded_position[1]][rounded_position[0]] in blocks):
                if(round_diff[0] <= self.CLIP_THRESHOLD or round_diff[1] <= self.CLIP_THRESHOLD): #WE'RE CHEATING!!!
                    if(self.first_cheat == None):
                        self.first_cheat = len(self.last_positions) - 1
                    return True
        else: #we're not even in the map borders!
            if(self.first_cheat == None):
                self.first_cheat = len(self.last_positions) - 1
            return True
        return False #we're not considered a cheater if we didn't bother checking speedhax and didn't get flagged on locationhax...

    # - Returns the last position which did not indicate cheating. This can be used with the clock() function to help return cheating players to their last Non-Cheating position -
    def find_last_uncheat_pos(self):
        if(self.first_cheat != None): #we've got a position to give!
            if(self.first_cheat >= self.BEFORE_CHEAT):
                pos = self.last_positions[self.first_cheat - self.BEFORE_CHEAT][0]
            else:
                pos = self.last_positions[0][0]
            self.last_positions = [[pos, time.time() - self.POS_RECORD_INTERVAL]] #we clear the last_positions list after getting the position we wanted so that the cheater has the chance to turn off speedhax and be treated as a regular player for the rest of the game.
            return pos
        else: #this player was not flagged for cheating
            return None

### - A quick test which shows the average battle unbalance from my matchmaker -
##engine = BattleEngine(False)
##engine.MIN_URGENCY = 0.0005
##engine.MIN_WAIT_ADD_URGENCY = 0.001
##power_differences = []
##
##urgency = 0.65 #change this value lower (lowest=engine.MIN_URGENCY) to make matches sloppier, or raise it (max=1) to make the match more strict.
##engine.MIN_WAIT_ADD_URGENCY = urgency * 1.5
##
##for x in range(0,500):
##    accounts = []
##    for x in range(0,random.randint(0,50)): #prepare (random # of) random accounts (yes, my matchmaker can handle 0 and 1-player scenarios without crashing!)
##        accounts.append(engine.create_account(random.randint(100,2500) / 100,player_name="name"))
##
##    player_queue = []
##    for x in range(0,len(accounts)):
##        player_queue.append([accounts[x], "client socket"])
##
##    #Although we can matchmake with an odd amount of players, generally odd matches are less balanced then ones with even numbers of players.
##    power_differences.append(engine.matchmake(player_queue, odd_allowed=True, rating=False, urgency=urgency, target_bot_ct=random.randint(0,8)))
##
### - Find the average power difference in matches, as well as how many matches were rejected due to imbalance -
##avg_power_differences = 0
##failed_matches = 0
##for x in range(0,len(power_differences)):
##    if(power_differences[x] != None): #this was an actual match?
##        #find what the imbalance for this match actually was
##        greatest_imbalance = 0.0
##        for y in range(0,len(power_differences[x])):
##            for b in range(0,len(power_differences[x])):
##                if(power_differences[x][y][1] - power_differences[x][b][1] > greatest_imbalance):
##                    greatest_imbalance = power_differences[x][y][1] - power_differences[x][b][1]
##        avg_power_differences += abs(greatest_imbalance)
##    else: #I also want to see how many matches got rejected...
##        failed_matches += 1
##if(len(power_differences) > 0):
##    avg_power_differences /= len(power_differences)
##else:
##    avg_power_differences = 9999.99
##print("\n\n\n")
##print("Average imbalance: " + str(round(avg_power_differences,2)))
##print("Failed match count: " + str(failed_matches) + " Successful match count: " + str(500 - failed_matches))
##print("Percentage of rejected matches: " + str(round(failed_matches / 500 * 100,2)) + "%")
##
##nones = None #see if any matches were made
##for x in range(0,len(power_differences)):
##    if(power_differences[x] != None):
##        nones = True
##        break
##if(nones == True): #if no matches were made, this just erupts into errors...
##    # - Find the outliers (extremes), beginning with the battle most in favor of Team 0 -
##    power = 0
##    imbalance_index = 0
##    for x in range(0,len(power_differences)):
##        if(power_differences[x] != None):
##            #find what the imbalance for this match actually was
##            greatest_imbalance = 0.0
##            for y in range(0,len(power_differences[x])):
##                for b in range(0,len(power_differences[x])):
##                    if(power_differences[x][y][1] - power_differences[x][b][1] > greatest_imbalance):
##                        greatest_imbalance = power_differences[x][y][1] - power_differences[x][b][1]
##            if(power < greatest_imbalance):
##                power = greatest_imbalance
##                imbalance_index = x #needed to print out team specs
##    print("\n\n\n")
##    print("Greatest imbalance: " + str(power))
##    #print out the teams for the specific match in which the inbalance occurred.
##    for team in range(0,len(power_differences[imbalance_index])):
##        print("\n --- *** Team " + str(team) + ": *** ---\n")
##        for x in range(0,len(power_differences[imbalance_index][team][0])): #iterate through team 0's players
##            print("Player " + str(x) + ": ", end="")
##            print(power_differences[imbalance_index][team][0][x][0]) #print out the player's rating
##            print(power_differences[imbalance_index][team][0][x][1][0]) #print out the player's account stats
##            print("\n")
##    print("\n\n\n")
##
##    # - Find the battle which is most in favor of Team 1 -
##    power = pow(10,10)
##    imbalance_index = 0
##    for x in range(0,len(power_differences)):
##        if(power_differences[x] != None):
##            #find what the imbalance for this match actually was
##            greatest_imbalance = 0.0
##            for y in range(0,len(power_differences[x])):
##                for b in range(0,len(power_differences[x])):
##                    if(power_differences[x][y][1] - power_differences[x][b][1] > greatest_imbalance):
##                        greatest_imbalance = power_differences[x][y][1] - power_differences[x][b][1]
##            if(power > greatest_imbalance):
##                power = greatest_imbalance
##                imbalance_index = x #needed to print out team specs
##    print("Least imbalance: " + str(power))
##    #print out the teams for the specific match in which the inbalance occurred.
##    for team in range(0,len(power_differences[imbalance_index])):
##        print("\n --- *** Team " + str(team) + ": *** ---\n")
##        for x in range(0,len(power_differences[imbalance_index][team][0])): #iterate through team 0's players
##            print("Player " + str(x) + ": ", end="")
##            print(power_differences[imbalance_index][team][0][x][0]) #print out the player's rating
##            print(power_differences[imbalance_index][team][0][x][1][0]) #print out the player's account stats
##            print("\n")
##else:
##    print("\n\n[MATCH] All matches failed.")
