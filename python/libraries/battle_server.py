##"battle_server.py" library ---VERSION 0.45---
## - Handles battles (main game loops, matchmaking, lobby stuff, and game setup) for SERVER ONLY -
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

class BattleEngine():
    def __init__(self, autostart=True):
        # - Netcode constants -
        self.buffersize = 10

        # - Sound reference constants -
        self.GUNSHOT = 0
        self.DRIVING = 1
        self.THUMP = 2
        self.EXPLOSION = 3
        self.CRACK = 4

        # - Formats for netcode packets (being recieved from the client) -
        #   - Format: [None], OR if we want to buy/return something, ["buy"/"return","item type",###], enter battle ["battle","battle type"]
        self.LOGIN_PACKET = ["<class 'str'>","<class 'str'>","<class 'bool'>"]
        self.LOBBY_PACKETS = [["<class 'NoneType'>"], ["<class 'str'>", "<class 'str'>", "<class 'int'>"], ["<class 'str'>", "<class 'str'>"]]
        self.MATCH_PACKETS = ["<class 'int'>", "<class 'int'>"] #[VIEW_CT, player_view_index] OR [False] to leave matchmaker (this one doesn't need to be included)
        self.GAME_PACKETS = [["<class 'str'>"],["<class 'str'>","<class 'list'>"]]

        #list of all accounts in the game; These get stored into a pickle dump when the server is shut down, and recovered when the server starts up.
        self.accounts = []
        try:
            self.accounts = self.load_save_data()
        except Exception as e:
            print("An exception occurred while loading save data: " + str(e) + " ...Resuming with standard save file...")
            self.accounts.append(account.Account("boomonster","password"))
            self.accounts.append(account.Account("muskoka","badtbo"))
            self.accounts.append(account.Account("i","tyler"))
            self.accounts.append(account.Account("blackfang","m41"))
            self.accounts.append(account.Account("shadow","name11"))
            self.accounts.append(account.Account("gubba","mylittledingus"))
            self.accounts.append(account.Account("yeudler","diycandles"))
            self.accounts.append(account.Account("necroneus","idkwhatpwdshouldbe"))
            self.accounts.append(account.Account("allegheny1606","cabforward"))
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
        
        #the IP/device name of our server
        HOST_NAME = socket.gethostname()
        self.IP = socket.gethostbyname(HOST_NAME)

        #create a random port number
        PORT = 5031
        print("Port Number: " + str(PORT) + " IP: " + str(self.IP))
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket object
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.IP, PORT))
        self.s.listen() #wait for connections

        # - AC Constants -
        self.AC_THRESH = 1.10 #how much can a player break past the AC's allowed constants before being labelled a cheater?

        # - Matchmaker constants -
        self.EXP_WEIGHT = 0.0005 #this defines the overall power of a player (more EXP = more experienced player = more strategic = more dangerous)
        self.UPGRADE_WEIGHT = 1.35 #this defines the overall power of a player (more upgrades = more powerful tank)
        self.CASH_WEIGHT = 0.0 #this defines the overall power of a player (more cash = more disk shells the player can buy = more dangerous)
        self.SHELLS_WEIGHT = [0.025, 0.05, 0.075, 0.15] #this defines the overall power of a player (more powerful shells = more dangerous)
        self.POWERUP_WEIGHT = 4 / 6 #this defines the overall power of a player (more powerups = more dangerous)
        self.SPECIALIZATION_WEIGHT = 1.125 #this defines the overall power of a player (more specialized = potentially more dangerous...?)
        self.IMBALANCE_LIMIT = 1.00 #the maximum imbalance of rating points a match is allowed to have to be finalized.
        #How many players can be put into a battle? [min, max]
        self.PLAYER_CT = [2, 50]
        #How many teams can a single battle have? -
        self.TEAM_CT = [2,4]
        # - How long should it take before a minimum player match attempts to take place?
        #   - (These matchmaking delays are really just here to reduce server CPU load now that match restrictions are built into the...
        #   - ...matchmaker)
        self.IMMEDIATE_MATCH = 20 #X/60 minutes = maximum wait time
        # - This isn't really the maximum match time, it's the maximum match time during which all matchmaking rules apply.
        #   - After X number of seconds have passed, the restrictions on matchmaking will begin to slacken to encourage a quick match.
        self.MAXIMUM_MATCH_TIME = 40 #seconds
        # - This constant is used by dividing SCALING_CONSTANT / PlayersInQueue
        self.TIME_SCALING_CONSTANT = self.IMMEDIATE_MATCH * self.PLAYER_CT[0] * 0.7 #how fast should the matchmaker shove players into matches if there are more than minimum players?
        # - This constant defines the minimum player count for an "optimal" match -
        self.OPTIMAL_MATCH_CT = 16 #16 players on a maximum of 4 teams is really the bare minimum for a *good* battle...
        self.OPTIMAL_TEAM_CT = 4 #X players on each team

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
            #"bot_rating[0] < player_ratings[bot_rating[1]][len(player_ratings[bot_rating[1]]) - 1]", #bot player must be weaker than the strongest player on the team
            #The rule above is redundant because the match will not let players within a certain skill gap enter the match. Even without the bot, the team's players will be at least comparable to the other players without the bot.
            "max_team_rating * math.sqrt(urgency) < min_team_rating", #all teams must be within sqrt(urgency%) rating differences
            "bot_rating[0] >= self.IMBALANCE_LIMIT", #the bot player MUST have at least the rating required to hold a few shells (otherwise useless bot, because bot has no bullets)
            "min_team_players > max_team_players * urgency" #all teams must have the same amount of players with urgency% error.
            #"min_player_rating > max_player_rating * urgency" #all players must be within urgency% as powerful as each other. [DEPRECATED] Now using PLAYER_RULES to account for deprecating this rule.
            #The above rule is useless because a rule in self.PLAYER_RULES basically performs the same task.
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
        self.SQUARES_PER_PERSON = 9 #3x3 per person is a decent space I think.

        # - How long should the compute thread of a battle last AFTER game over has occurred? -
        self.BATTLE_TIMER = 30.0 #seconds

        if(autostart):
            _thread.start_new_thread(self.matchmaker_loop,())
            self.connect_players() #begin the connection script

    # - Logs out a player, so their data is saved when they leave the game. This function returns True if the data was saved successfully -
    def logout_player(self, player_data): #player_data format: [account.Account() object, socket object]
        found = False
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
        return found

    def connect_players(self):
        while True:
            print("[WAIT] Waiting for a connection...")
            Cs, Caddress = self.s.accept() #connect to a client
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

                print("[CONNECT] Recieved login/create account data - Username: " + str(name) + " Password: " + str(password) + " - ", end="")

                # - First check if the player's name is equivalent to the name all bots are assigned: "Bot Player" -
                if(name != "Bot Player"): #if the player name IS "Bot Player", the player has NO CHANCE of creating a new account/signing in.
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
    def lobby_server(self, player_data, special_window=None): #player_data format: [account.Account() object, socket object]
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
                    #print(client_data, player_data[0].name)
                    if(client_data[0] == "buy"): #purchasing an item?
                        reply = [player_data[0].purchase(client_data[1],client_data[2])]
                    elif(client_data[0] == "refund"): #refunding an item?
                        reply = [player_data[0].refund(client_data[1],client_data[2])]
                    elif(client_data[0] == "battle"): #enter into battle!!!
                        with self.player_queue_lock:
                            reply = [False]
                            #netcode.clear_socket(player_data[1]) #clear the socket so that the matchmaker doesn't have to deal with garbage
                            for x in range(0,len(self.battle_types)): #...just making sure this game mode exists...
                                if(self.battle_types[x] == client_data[1]):
                                    self.player_queue[x].append(player_data)
                                    reply = [True, "battle"]
                                    reply.append(player_data[0].return_data())
                                    reply.append(None) #append NO special window data to the list
                                    netcode.send_data(player_data[1], self.buffersize, reply)
                    elif(client_data[0] == "sw_close"): #closing the special window?
                        special_window = None #clear our special window...
                    else:
                        reply = [None]
                else:
                    reply = [None]
            else:
                reply = [None]

            if(len(reply) < 2): #we're not battling? We can send data like normal...
                #make sure that the player we're connected to knows his ^ balance, tank upgrades, etc.
                reply.append(player_data[0].return_data())

                #append our special window data to the send list
                reply.append(special_window)

                #wait that 0.25 seconds before we should send a packet to achieve ~4PPS at best, ~0.5PPS worst before a disconnect occurs (if the timeout constant in netcode.py is 2 seconds)
                time.sleep(0.25)

                #send back a response based on whether we had to perform any action, and whether we could perform it.
                netcode.send_data(player_data[1], self.buffersize, reply) #Server transmission format: [True] (success), [None] (no operation), [False, "$$$ needed"/"max"]

            # - Check if it is time to exit the server's lobby loop -
            if(len(reply) > 1 and reply[1] == "battle"):
                in_lobby = False
        if(len(reply) > 1 and reply[1] == "battle"): #entered battle?
            print("[IN QUEUE] Player " + player_data[0].name + " has entered battle in mode: " + str(client_data[1]))
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
                            elif(match_urgency < 0.5):
                                match_urgency = 0.5
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
    def unrated_battle_server(self, players):
        # - Start by setting up the game state: Players in their starting position, no bullets, no powerups spawned on the map -
        #Player Format: [[rating, [account, socket]], [rating, [account, socket]]...]
        #Teams format: [[[[rating, [account, socket]], [rating, [account, socket]]...], rating], [players, rating]...]
        game_objects = []
        game_objects_lock = _thread.allocate_lock()
        # - Which map are we playing on? -
        map_name = self.pick_map(players)
        if(map_name == False): #we didn't get a map? (0 players in match)
            return None #exit this battle!
        # - This is for holding all particle effects. This lets people know where gunfights are happening easily because everyone gets to see them -
        particles = []
        particles_lock = _thread.allocate_lock()
        # - This list documents which teams have been eliminated -
        eliminated = [] #[team 0, team 1, team 2, etc.] Format: False = not destroyed, 1 = first destroyed, 2 = 2nd destroyed, etc.
        # - Grab our arena data -
        #   Format: [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
        arena_data = import_arena.return_arena(map_name)
        arena = arena_lib.Arena(arena_data[0], arena_data[1], arena_data[2])
        arena.set_flag_locations(arena_data[6])
        arena_lock = _thread.allocate_lock()
        # - Create a GFX manager to reduce netcode load -
        gfx = GFX.GFX_Manager()
        # - Create a SFX_Manager() so that the client has sound effects occurring at the right times -
        sfx = SFX.SFX_Manager()
        sfx.server = True
        sfx.add_sound("../../sfx/gunshot_01.ogg")
        sfx.add_sound("../../sfx/driving.ogg")
        sfx.add_sound("../../sfx/thump.ogg")
        sfx.add_sound("../../sfx/explosion_large.ogg")
        sfx.add_sound("../../sfx/crack.ogg")
        # - Set players in the right position -
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                if(player == 0): #add the team bookmark to the eliminated[] list.
                    eliminated.append(["Team " + str(teams), False])
                #print(players[teams][0][player])
                game_objects.append(players[teams][0][player][1][0].create_tank("image replacement", "Team " + str(teams)))
                # - Set the position our player should go to -
                game_objects[len(game_objects) - 1].goto(arena.flag_locations[teams])
        # - Start child threads to handle netcode -
        player_number = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                _thread.start_new_thread(self.battle_server, (game_objects, game_objects_lock, players[teams][0][player][1], player_number, map_name, particles, particles_lock, arena, eliminated, False, teams, gfx, sfx))
                player_number += 1
        # - Start this thread to handle most CPU based operations -
        _thread.start_new_thread(self.battle_server_compute, (game_objects, game_objects_lock, map_name, particles, particles_lock, arena, eliminated, gfx, sfx))

    # - This battle mode allows you to lose experience, which is needed to unlock new tanks -
    def ranked_battle_server(self, players):
        # - Start by setting up the game state: Players in their starting position, no bullets, no powerups spawned on the map -
        #Player Format: [[rating, [account, socket]], [rating, [account, socket]]...]
        #Teams format: [[[[rating, [account, socket]], [rating, [account, socket]]...], rating], [players, rating]...]
        game_objects = []
        game_objects_lock = _thread.allocate_lock()
        # - Which map are we playing on? -
        map_name = self.pick_map(players)
        if(map_name == False): #we didn't get a map? (0 players in match)
            return None #exit this battle!
        # - This is for holding all particle effects. This lets people know where gunfights are happening easily because everyone gets to see them -
        particles = []
        particles_lock = _thread.allocate_lock()
        # - This list documents which teams have been eliminated -
        eliminated = [] #[team 0, team 1, team 2, etc.] Format: False = not destroyed, 1 = first destroyed, 2 = 2nd destroyed, etc.
        # - Grab our arena data -
        #   Format: [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
        arena_data = import_arena.return_arena(map_name)
        arena = arena_lib.Arena(arena_data[0], arena_data[1], arena_data[2])
        arena.set_flag_locations(arena_data[6])
        arena_lock = _thread.allocate_lock()
        # - Create a GFX manager to reduce netcode load -
        gfx = GFX.GFX_Manager()
        # - Create a SFX_Manager() so that the client has sound effects occurring at the right times -
        sfx = SFX.SFX_Manager()
        sfx.server = True
        sfx.add_sound("../../sfx/gunshot_01.ogg")
        sfx.add_sound("../../sfx/driving.ogg")
        sfx.add_sound("../../sfx/thump.ogg")
        sfx.add_sound("../../sfx/explosion_large.ogg")
        sfx.add_sound("../../sfx/crack.ogg")
        # - Set players in the right position -
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])):
                if(player == 0): #add the team bookmark to the eliminated[] list.
                    eliminated.append(["Team " + str(teams), False])
                #print(players[teams][0][player])
                game_objects.append(players[teams][0][player][1][0].create_tank("image replacement", "Team " + str(teams)))
                # - Set the position our player should go to -
                game_objects[len(game_objects) - 1].goto(arena.flag_locations[teams])
        # - Start child threads to handle netcode -
        player_number = 0
        for teams in range(0,len(players)):
            for player in range(0,len(players[teams][0])): #the True at the end is to let all threads know that this battle is for more stakes then just cash!
                _thread.start_new_thread(self.battle_server, (game_objects, game_objects_lock, players[teams][0][player][1], player_number, map_name, particles, particles_lock, arena, eliminated, True, teams, gfx, sfx))
                player_number += 1
        # - Start this thread to handle most CPU based operations -
        _thread.start_new_thread(self.battle_server_compute, (game_objects, game_objects_lock, map_name, particles, particles_lock, arena, eliminated, gfx, sfx))

    # - Handles most of the computation for battles, excluding packet exchanging -
    def battle_server_compute(self, game_objects, game_objects_lock, map_name, particles, particles_lock, arena, eliminated, gfx, sfx):
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
        while battle:
            # - Update our framecounter -
            if(framecounter >= 65535):
                framecounter = 0
            else:
                framecounter += 1

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

            decrement = 0 # - Update all the "game_objects" in the game -
            with game_objects_lock:
                # - Attempt to spawn powerups -
                entity.spawn_powerups(arena,game_objects,["","","","","","","","","",""]) #the "" are dummy images...The client will have to populate those spaces with proper images.
                for x in range(0,len(game_objects)):
                    if(game_objects[x - decrement].type == "Tank"): #Are we updating a tank object?
                        if(game_objects[x - decrement].destroyed != True):
                            potential_bullet = game_objects[x - decrement].shoot(20, server=True) #did the client try to shoot? And, were we able to let them shoot?
                            if(potential_bullet != None): #if our gunshot was successful, we add the bullet object to our game objects list.
                                game_objects.append(potential_bullet)
                                # - Create a gunshot sound effect -
                                sfx.play_sound(self.GUNSHOT, game_objects[x - decrement].overall_location[:], [0,0])
                            game_objects[x - decrement].clock(TILE_SIZE, [1, 1], particles, framecounter, gfx) #update all tank objects
                            game_objects[x - decrement].message("This is server-side...", particles)
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
                                if(entity.check_collision(game_objects[x - decrement], game_objects[y], arena.TILE_SIZE, tank_collision_offset=5)[0]): #the tank got the powerup?
                                    game_objects[x - decrement].use(game_objects[y]) #it will despawn automatically from the code below...
                                    break
                        game_objects[x - decrement].clock() #update the powerup's state
                        if(game_objects[x - decrement].despawn == True): #despawn the powerup?
                            del(game_objects[x - decrement])
                            decrement += 1

                # - Check if any teams were eliminated -
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

            # - Check if all but one team has been eliminated -
            battle_end_check = 0 #this variable needs to equal len(eliminated) - 1 by the time this loop is finished for the game to end.
            for battle_end in range(0,len(eliminated)):
                if(eliminated[battle_end][1] != False): #this team got eliminated?
                    battle_end_check += 1
            if(battle_timeout != None and time.time() - battle_timeout > self.BATTLE_TIMER): #30 seconds after battle ends? Kill this thread.
                print("[BATTLE] Main compute thread ended...")
                break #exit the loop! We're done here!
            elif(battle_end_check >= len(eliminated) - 1 and battle_timeout == None): #battle ends?
                print("[BATTLE] Game over timeout started...")
                battle_timeout = time.time() #start a timer...

    # - Player_data is a list of [account, socket].
    # - This function exchanges packets between client and server, AND stuffs the client's data into the game_objects list. It can also function as a dummy client, with a bot controlling the tank. -
    def battle_server(self, game_objects, game_objects_lock, player_data, player_index, map_name, particles, particles_lock, arena, eliminated, experience=False, team_num=0, gfx=None, sfx=None):
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
            bot_computer = entity.Bot(team_num,player_index,player_rating=1.15)

        packet_counter = 0 #this counts packets; I use this to help tell which packets we send packet data through.

        disconnect_packets = 0 #this counts packets we sent during which the client was disconnected.
        
        packets = True #are we still exchanging packets?
        #***NOTE: Sometimes this thread will get started to handle a bot client: Player_data format: [self.create_account(potential_match * 0.75),"bot"]***
        while packets:
            # - Send our data to the client -
            if(packet_phase != "bot"): #we're NOT a bot?
                if(packet_phase == "init"): #making sure the client left the matchmaker?
                    packet_data = [False,[account.Account().return_data(),account.Account().return_data()],2]
                    packet_phase = "setup" #make sure we move onto the next stage of client setup
                elif(packet_phase == "setup"): #setting up the client? player_ct is needed to tell the client how many HUD HP bars are needed for other players...
                    player_ct = 0
                    with game_objects_lock: #count players
                        for x in game_objects:
                            if(x.type == "Tank"):
                                player_ct += 1
                    packet_data = ["setup" ,player_data[0].return_data(), map_name, player_ct]
                elif(packet_phase == "sync"): #client sync?
                    packet_data = ["sync", game_objects[player_index].return_data()]
                elif(packet_phase == "end"): #end of game? Send ALL the player data and nothing else then...
                    with game_objects_lock:
                        game_object_data = [] #gather all entity data into one list (this could be moved into the compute thread later on)
                        for x in range(0,len(game_objects)):
                            game_object_data.append(game_objects[x].return_data(2, False))
                    packet_data = ["end", game_object_data, eliminated] #this way we can see the scoreboard at the end of the game...
                elif(packet_phase == "packet"): #typical data packet
                    with game_objects_lock:
                        game_object_data = [] #gather all entity data into one list (this could be moved into the compute thread later on)
                        for x in range(0,len(game_objects)):
                            game_object_data.append(game_objects[x].return_data(2, False))
                    packet_data = ["packet", game_object_data]
                    # - Send particle data to client every Xnd packet -
                    if(packet_counter % 2 == 0): #it's every second packet?
                        with particles_lock:
                            particle_list = []
                            for x in particles:
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
                        if(verify):
                            print("[BATTLE] Connecting player " + str(player_data[0].name) + " to lobby...")
                            with game_objects_lock:
                                if(packet_phase != "end"): #we only punish the player for leaving if the battle's not over AND he's not already dead (you can't die twice)
                                    game_objects[player_index].destroyed = True
                                outcome = player_data[0].return_tank(game_objects[player_index],rebuy=True,bp_to_cash=True,experience=experience, verbose=True)
                            special_window_str = self.generate_outcome_menu(outcome, game_objects[player_index], "- Battle Complete -")
                            _thread.start_new_thread(self.lobby_server,(player_data, special_window_str))
                            del(player_data)
                            packets = False
                        else:
                            verify = False
                            for x in self.GAME_PACKETS:
                                if(netcode.data_verify(data, x)):
                                    verify = True
                                    break
                            if(verify):
                                # - Handle the packet -
                                if(packet_phase == "sync"): #if we sent a sync packet beforehand, we need to check if the client followed the sync packet before we continue with normal packets.
                                    compare_data = game_objects[player_index].return_data()
                                    data[1][15] = compare_data[15] #make sure the comparison is fair...index 15 will never match, so I need to make it match.
                                    data[1][16] = compare_data[16] #...same with data 16 and 17. Not that they won't always match, but they won't sometimes, and the server can bypass the sync on these variables without consequences.
                                    data[1][17] = compare_data[17]
                                    data[1][18] = compare_data[18]
                                    data[1][19] = compare_data[19]
                                    if(compare_data == data[1]): #we got the sync to happen properly?
                                        packet_phase = "packet" #if the player does not sync, the server continues to ignore the player's new coordinates.
                                elif(data[0] == "end"): #the client wants to leave now?
                                    with game_objects_lock:
                                        if(packet_phase != "end"): #we only punish the player for leaving if the battle's not over AND he's not already dead (you can't die twice)
                                            game_objects[player_index].destroyed = True
                                        outcome = player_data[0].return_tank(game_objects[player_index],rebuy=True,bp_to_cash=True,experience=experience, verbose=True)
                                    special_window_str = self.generate_outcome_menu(outcome,  game_objects[player_index], "- Battle Complete -")
                                    _thread.start_new_thread(self.lobby_server, (player_data[1], special_window_str)) #back to the lobby...
                                    print("[BATTLE] Removed player " + str(player_data[1].name) + " from the battle successfully")
                                    del(player_data)
                                    packets = False #then it is time to leave...
                                else: #either setup packet stuff or standard packets are coming through...
                                    if(packet_phase == "setup" or data[0] == "setup"):
                                        if(packet_phase == "setup"): #once we finish setting up the player, we need to sync his state.
                                            packet_phase = "sync"
                                        if(data[0] == "setup"): #we need to resend the setup data
                                            packet_phase = "setup"
                                    else: #normal packet - only enter data IF the player is alive by server standards!
                                        with game_objects_lock:
                                            if(game_objects[player_index].destroyed == False):
                                                # - Enter the player data into our game_objects list
                                                game_objects[player_index].enter_data(data[1], server=True) #make sure we only take the attributes a server should...
                            
                else: #client disconnected? Log him out...but we're gonna decrease his $$$ a bit first...
                    disconnect_packets += 1
                    if(disconnect_packets >= 15): #the client really disconnected? (15 lost packets in a row???)
                        player_data[0].cash *= 0.85 #decrease the player's cash by 15%
                        saved = self.logout_player(player_data) #try to log out the player
                        if(saved):
                            print("[BATTLE] Successfully disconnected/saved player data from user " + str(player_data[0].name) + " during battle")
                        else:
                            print("[BATTLE] Failed to save player data from user " + str(player_data[0].name) + " during battle")
                        packets = False #this thread can die now...

            # - Check if we should switch packet_phase to "end" (game over). This can happen EITHER if we are eliminated, OR if we win. -
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
                    
            clock.tick(20) #limit PPS to 20

    def generate_outcome_menu(self, rebuy_data, tank, title): #generates the menu string which needs to be transmitted to the client to form a "special menu/window".
        # - Calculate some statistics about player performance -
        total_shots = 0
        for x in tank.shells_used:
            total_shots += x
        if(total_shots == 0): #make sure we don't get div0 errors when calculating accuracy...
            total_shots += 1
        total_powerups = 0
        for x in tank.powerups_used:
            total_powerups += x
        # - Generate the outcome menu -
        return [ #rebuy_data format: [earned, shell_cost, pu_cost, net earnings, net experience]
            "Back",
            "",
            "Earnings",
            "^ before rebuy - " + str(round(rebuy_data[0],2)),
            "Shell costs - " + str(round(rebuy_data[1],2)),
            "Powerup costs - " + str(round(rebuy_data[2],2)),
            "Net ^ - " + str(round(rebuy_data[3],2)),
            "Net experience - " + str(round(rebuy_data[4],2)),
            "Hollow shells used - " + str(tank.shells_used[0]),
            "Regular shells used - " + str(tank.shells_used[1]),
            "Explosive shells used - " + str(tank.shells_used[2]),
            "Disk shells used -  " + str(tank.shells_used[3]),
            "Powerups used: " + str(total_powerups),
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
            
            if(potential_map != None): #this is a valid map; NOW we need to check whether it will host as many players as we want.
                # - Get the total area of the map in tiles -
                # - Potential_map[0][0] is the map itself, potential_map[0][1] is the map's tiles, potential_map[1] is the map's name
                tiles = len(potential_map[0][0]) * len(potential_map[0][0][0]) #get the map's area
                if(player_ct != 0 and tiles / player_ct >= self.SQUARES_PER_PERSON): #will it host as many players as we want????????
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
        else: #just pick a random map then...
            battle_map = import_arena.return_arena_numerical(random.randint(0,map_counter - 1))[1]
        return battle_map #just returns the map name, nothing more.

    def return_rating(self, player_account, rating=False): #creates a numerical rating number for a player.
        player_stat = 0 #temporary variable which I use to calculate a player's numerical rating
        if(rating): #this is for rated/ranked battles only.
            player_stat += self.EXP_WEIGHT * player_account.experience #add player exp to predicted performance
        player_stat += self.CASH_WEIGHT * player_account.cash #add player cash to predicted performance
        # - Find the player's individual upgrade levels, and add player rating from them -
        for b in range(0,len(player_account.upgrades)):
            player_stat += pow(self.UPGRADE_WEIGHT, player_account.upgrades[b]) - 1
        # - Add the player's number of shells of each type to the player's predicted performance -
        for x in range(0,len(player_account.shells)):
            player_stat += player_account.shells[x] * self.SHELLS_WEIGHT[x]
        # - Add the player's powerups to the player's predicted performance -
        for x in range(0,len(player_account.powerups)):
            if(player_account.powerups[x] == True):
                player_stat += self.POWERUP_WEIGHT
        # - Add the player's specialization number to the player's predicted performance -
        player_stat += pow(self.SPECIALIZATION_WEIGHT, abs(player_account.specialization)) - 1
        return player_stat

    def create_account(self,rating,player_name="Bot Player"): #creates an account with upgrades which correspond roughly to the rating value you input.
        bot_account = account.Account(player_name,"pwd",True) #create a bot account
        while self.return_rating(bot_account) < rating or self.return_rating(bot_account) > rating + self.IMBALANCE_LIMIT:
            while self.return_rating(bot_account) < rating:
                bot_account.bot_purchase()
            while self.return_rating(bot_account) > rating + self.IMBALANCE_LIMIT:
                bot_account.bot_refund()
        return bot_account

    def return_team_ratings(self, player_queue, odd_allowed=False, rating=False):
        if(len(player_queue) >= self.PLAYER_CT[0]): #we have enough players in queue to start a game?
            if(len(player_queue) >= self.PLAYER_CT[1]): #we have too many players in queue for one game?
                #Create a match with the maximum amount of players allowed in one battle!
                match_players = []
                for x in range(0,self.PLAYER_CT[1]):
                    match_players.append(player_queue.pop(0))
            else: #create a match with an even/odd number of players
                if(odd_allowed):
                    match_player_ct = len(player_queue)
                else:
                    match_player_ct = (int(len(player_queue) / 2.0) * 2)
                match_players = []
                for x in range(0,match_player_ct):
                    match_players.append(player_queue[x])
            # - Now we need to balance the "match_players" into two teams -
            #"match_players_stats" holds numbers: the higher the number, the better the player is predicted to perform.
            match_players_stats = [] #Holds what I will refer to as "numerical rating" or "predicted performance" numbers
            for x in range(0,len(match_players)): #find the numerical rating of each player in this match
                match_players_stats.append([self.return_rating(match_players[x][0],rating), match_players[x]])
            # - Now that we have attempted to predict how powerful a player will be, we need to arrange teams -
            teams = [[[], 0], [[], 0]] #this could be changed in the future to allow 3 or 4 teams...
            while len(match_players_stats) > 0:
                # - find the most powerful player -
                power = [0, 0]
                for x in range(0,len(match_players_stats)):
                    if(match_players_stats[x][0] > power[0]): #this player is more powerful than any others we have checked?
                        power = [match_players_stats[x][0], x]
                powerful_player = match_players_stats[power[1]]
                powerful_player_full = [powerful_player[0], powerful_player[1]]
                del(match_players_stats[power[1]])
                # - Now which team should he go on? Which one is behind in matchmaking points? -
                if(teams[0][1] > teams[1][1]): #then the player goes on team 1.
                    teams[1][0].append(powerful_player_full)
                    teams[1][1] += powerful_player[0] #add the player's numerical rating to the team's overall rating
                else: #the player goes on team 0.
                    teams[0][0].append(powerful_player_full)
                    teams[0][1] += powerful_player[0] #add the player's numerical rating to the team's overall rating
            return abs(teams[0][1] - teams[1][1]) #return the imbalance of points in the matchmaking
        else:
            return None

    #***Player_queue MUST be locked while matchmaking to avoid index errors***
    #player_queue is a list: [ [account, client socket], [account, client socket] ... ]
    def matchmake(self, player_queue, odd_allowed=False, rating=False, urgency=1.0): #creates a match from the player queue
        # - self.PLAYER_RULES is a list of rules which EACH player has to meet to be added to a match -
        #   - Usable variables:
        #       - urgency is a variable which starts at 1, and decreases downwards to 0 (but never ends up below 0.5).
        #           - It is used to promote quick(er) matches when there isn't really enough players in the queue.
        #           - It is defined above as a parameter of matchmake().
        #       - players is a list of all players on the team, in the format [rating, [account, socket]]
        #       - player is a list containing this player's data: [rating, [account, socket]]

        # - How matches are made -
        # 1) Sort players according to strength. Strongest are first, weakest are last.
        # 2) Create a certain amount of teams (between 2 and 4) based on the number of players which could be added to the match.
        # 3) Add players to the teams as evenly as possible, starting with the strongest player and ending with the weakest player

        # - Start by seeing if there's enough players for a match! -
        match = []
        # - We always start by adding the first player in the queue to the match, and then seeing how many other players we can add after him -
        if(len(player_queue) > 0): #there HAS to be players in the queue for this to work...
            #print("[MATCH] Phase I begin! Find enough players!") #debug
            player_ct = 1
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
                for rule in self.PLAYER_RULES:
                    if(eval(rule)):
                        pass
                    else:
                        add = False
                    if(not add):
                        break
                if(add):
                    player_ct += 1
            # - Was there enough players for a match? -
            if(player_ct >= self.PLAYER_CT[0]):
                #print("[MATCH] Phase I Complete: Found " + str(player_ct) + " players...Beginning Phase II: Add players to teams.") #debug
                # - How many teams should we create? -
                team_ct = int(player_ct / self.OPTIMAL_TEAM_CT)
                if(team_ct < self.TEAM_CT[0]): #not enough teams for a battle to start???
                    team_ct = self.TEAM_CT[0] #just head for the bare minimum amount of teams
                # - Start adding players to a new match! -
                match = []
                for x in range(0,team_ct): #prepare a match list with space for teams
                    match.append([[], 0.0])
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
            else: #match failed.
                match = None
        else: #match failed.
            match = None

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
            for team in match:
                if(max_team_rating - team[1] > self.IMBALANCE_LIMIT):
                    # - Index 1 of the bot player data MUST be equal to "bot" to make the bot scripts begin in the game's main loop -
                    team[0].append([max_team_rating - team[1], [self.create_account(max_team_rating - team[1]),"bot"]]) #get the bot in the game
            #       - max_team_players is a variable storing the most players on a team
            max_team_players = 0
            for most_players in player_counts:
                if(most_players > max_team_players):
                    max_team_players = most_players
            #       - min_team_players is a variable storing the least players on a team
            min_team_players = (self.PLAYER_CT[1] * 2)
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
            bot_rating = [0.001, 0] # - Find the bot! There can only be one, and its name is always "Bot Player", and password is "pwd"
            team_index = 0
            found = False
            for teams in match:
                for player in teams[0]:
                    if(found == False):
                        if(player[1][0].name == "Bot Player" and player[1][0].password == "pwd"):
                            bot_rating[0] = player[0]
                            bot_rating[1] = team_index
                            found = True
                            break
                    else: #this only applies once we've already found A bot. However, it might not be the lowest rating bot in the match...
                        if(player[1][0].name == "Bot Player" and player[1][0].password == "pwd"):
                            if(player[0] < bot_rating[0]): #this bot's rating IS lower than the one we WERE thinking of?
                                bot_rating[0] = player[0] #well now all eyes are on IT!
                                bot_rating[1] = team_index
                team_index += 1
            if(not found): #We don't have a bot in the game?
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

    def anti_cheat(self): #checks old_data list and can see if any players are cheating based on that.
        # - AC needs to check 2 things: -
        # 1) Player speed: Is the player moving faster than allowed?
        # 2) Player rotation: Is the player able to change direction faster than it should?
        pass

engine = BattleEngine()

### - A quick test which shows the average battle unbalance from my matchmaker -
##engine = BattleEngine(False)
##power_differences = []
##
##urgency = 0.65 #change this value lower (lowest=0.5) to make matches sloppier, or raise it (max=1) to make the match more strict.
##
##for x in range(0,500):
##    accounts = []
##    for x in range(0,random.randint(8,50)): #prepare (random # of) random accounts
##        accounts.append(account.Account("name", "password"))
##        accounts[len(accounts) - 1].randomize_account()
##
##    player_queue = []
##    for x in range(0,len(accounts)):
##        player_queue.append([accounts[x], "client socket"])
##
##    #Although we can matchmake with an odd amount of players, generally odd matches are less balanced then ones with even numbers of players.
##    power_differences.append(engine.matchmake(player_queue, odd_allowed=True, rating=False, urgency=urgency))
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
##        print("Failed match!")
##avg_power_differences /= len(power_differences)
##print("Average unbalance: " + str(avg_power_differences))
##print("Percentage of rejected matches: " + str(failed_matches / 500 * 100))
##
### - Find the outliers (extremes), beginning with the battle most in favor of Team 0 -
##power = 0
##for x in range(0,len(power_differences)):
##    if(power_differences[x] != None):
##        #find what the imbalance for this match actually was
##        greatest_imbalance = 0.0
##        for y in range(0,len(power_differences[x])):
##            for b in range(0,len(power_differences[x])):
##                if(power_differences[x][y][1] - power_differences[x][b][1] > greatest_imbalance):
##                    greatest_imbalance = power_differences[x][y][1] - power_differences[x][b][1]
##        if(power < greatest_imbalance):
##            power = greatest_imbalance
##            imbalance_index = x #needed to print out team specs
##print("Greatest imbalance: " + str(power))
###print out the teams for the specific match in which the inbalance occurred.
##for team in range(0,len(power_differences[imbalance_index])):
##    print("\n\n\n - Team " + str(team) + ":")
##    for x in range(0,len(power_differences[imbalance_index][team][0])): #iterate through team 0's players
##        print("Player " + str(x) + ": ", end="")
##        print(power_differences[imbalance_index][team][0][x][0]) #print out the player's rating
##        print(power_differences[imbalance_index][team][0][x][1][0]) #print out the player's account stats
##        print("\n")
##print("\n\n\n")
##
### - Find the battle which is most in favor of Team 1 -
##power = pow(10,10)
##for x in range(0,len(power_differences)):
##    if(power_differences[x] != None):
##        #find what the imbalance for this match actually was
##        greatest_imbalance = 0.0
##        for y in range(0,len(power_differences[x])):
##            for b in range(0,len(power_differences[x])):
##                if(power_differences[x][y][1] - power_differences[x][b][1] > greatest_imbalance):
##                    greatest_imbalance = power_differences[x][y][1] - power_differences[x][b][1]
##        if(power > greatest_imbalance):
##            power = greatest_imbalance
##            imbalance_index = x #needed to print out team specs
##print("Least imbalance: " + str(power))
###print out the teams for the specific match in which the inbalance occurred.
##for team in range(0,len(power_differences[imbalance_index])):
##    print("\n\n\n - Team " + str(team) + ":")
##    for x in range(0,len(power_differences[imbalance_index][team][0])): #iterate through team 0's players
##        print("Player " + str(x) + ": ", end="")
##        print(power_differences[imbalance_index][team][0][x][0]) #print out the player's rating
##        print(power_differences[imbalance_index][team][0][x][1][0]) #print out the player's account stats
##        print("\n")
