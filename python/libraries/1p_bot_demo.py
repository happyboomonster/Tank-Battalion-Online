##"1p_bot_demo.py" demo ---VERSION 0.09---
## - One-player offline version of TBO with no store and configurable settings (see the variables listed below throughout the game script before the game loop) -
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

import pygame, arena, entity, GFX, time, random, HUD, menu, sys, account, battle_client as battle, font
sys.path.insert(0, "../maps")
import import_arena

#pygame stuff
pygame.init()
screen = pygame.display.set_mode([640, 480], pygame.RESIZABLE) # | pygame.SCALED) #uncomment for a large performance boost at the expense of horrible graphics.
p1_screen = pygame.Surface([screen.get_width(), screen.get_height()])
screens = [p1_screen]

#tank images
T1 = [pygame.image.load("../../pix/tanks/P1U1.png"),pygame.image.load("../../pix/tanks/P1U2.png")]
T2 = [pygame.image.load("../../pix/tanks/P2U1.png"),pygame.image.load("../../pix/tanks/P2U2.png")]
T3 = [pygame.image.load("../../pix/tanks/P3U1.png"),pygame.image.load("../../pix/tanks/P3U2.png")]
T4 = [pygame.image.load("../../pix/tanks/P4U1.png"),pygame.image.load("../../pix/tanks/P4U2.png")]

#list of all blocks we cannot run through
blocks = [15,16,17,18,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]

#our arena map we will be drawing
my_map = [[30,25,25,25,25,25,25,25,25,25,25,27],
          [26,36, 5, 6,10,18,15,18,11,11,37,26],
          [26, 0, 7, 8,10,11, 1, 1,10,10,10,26],
          [26, 1, 7,11,30,21,27,10,10, 5, 6,26],
          [26,18,11,11,23,20,24, 1, 2, 6,18,26],
          [26,15,11, 6,29,22,28, 2, 3, 7,15,26],
          [26, 3, 2, 7, 9, 9, 9, 3, 4, 8, 7,26],
          [26, 1,35, 8,31, 9, 9,30,25,34, 6,26],
          [26, 2, 1,33,35,34, 9,26, 2, 6, 7,26],
          [26, 3, 2, 6,32, 0, 0,32, 3, 4, 1,26],
          [26,39,17, 7, 0, 0, 0, 4, 4,17,38,26],
          [29,25,25,25,25,25,25,25,25,25,25,28]]

#all the tiles we can draw in the arena
path = "./"
my_tiles = [pygame.image.load(path + "../../pix/blocks/original_20x20/ground/asphalt.png"), #0
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/forest-1.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/forest-2.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/forest-1.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/forest-3.png"), #4
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/grass-1.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/grass-2.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/grass-1.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/grass-3.png"), #8
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/dirt.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/cement.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/water-1.png"), #11
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/water-2.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/water-3.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/water-4.png"), #14
            pygame.image.load(path + "../../pix/blocks/original_20x20/ground/water-5.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/brick/brick0h.png"), #16
            pygame.image.load(path + "../../pix/blocks/original_20x20/brick/brick1h.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/brick/brick2h.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/brick/brick3h.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/brick/brick_destroyed.png"), #20
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall.png"), #21
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-top.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-bottom.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-left.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-right.png"), #25
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-double-edge/wall-double-edge-horizontal.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-double-edge/wall-double-edge-vertical.png"), #27
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-top-right.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-bottom-right.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-bottom-left.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-top-left.png"), #31
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-top.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-bottom.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-left.png"),
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-right.png"), #35
            pygame.image.load(path + "../../pix/blocks/original_20x20/wall/wall-island.png"), #36
            pygame.image.load(path + "../../pix/blocks/original_20x20/flags/team-1.png"), #37
            pygame.image.load(path + "../../pix/blocks/original_20x20/flags/team-2.png"), #38
            pygame.image.load(path + "../../pix/blocks/original_20x20/flags/team-3.png"), #39
            pygame.image.load(path + "../../pix/blocks/original_20x20/flags/team-4.png") #40
           ]

#define our list of powerup images
powerup_images = [
    pygame.image.load("../../pix/powerups/fuel.png"),
    pygame.image.load("../../pix/powerups/fire-extinguisher.png"),
    pygame.image.load("../../pix/powerups/dangerous-loading.png"),
    pygame.image.load("../../pix/powerups/explosive-tip.png"),
    pygame.image.load("../../pix/powerups/amped-gun.png"),
    pygame.image.load("../../pix/powerups/makeshift-armor.png"),
    pygame.image.load("../../pix/ammunition/hollow_shell_button.png"),
    pygame.image.load("../../pix/ammunition/regular_shell_button.png"),
    pygame.image.load("../../pix/ammunition/explosive_shell_button.png"),
    pygame.image.load("../../pix/ammunition/disk_shell_button.png")
    ]
    

#define our tile shuffle system
my_shuffle = [[11,12], #water
              [12,13],
              [13,14],
              [14,11],
              [1,2], #forest
              [2,3],
              [3,4],
              [4,1],
              [5,6], #grass
              [6,7],
              [7,8],
              [8,5]]

#define our flag tiles
flag_tiles = [36,37,38,39]

#way in which bricks change to destroyed - listed from least to most destroyed
bricks = [
    15, #0 hits
    16,
    17,
    18, #3 hits
    19 #destroyed
    ]

# - Import an external map -
arena_data = import_arena.return_arena("t4_Arena04")
my_map = arena_data[0]
my_tiles = arena_data[1]
my_shuffle = arena_data[2]
blocks = arena_data[3]
bricks = arena_data[4]
bricks.append(arena_data[5]) #add the destroyed tile to the game
flag_tiles = arena_data[6]

my_arena = arena.Arena(my_map, my_tiles, my_shuffle) #create an arena object
my_arena.stretch = False
visible_arena = [15,15] #what viewport size are we aiming for?
screen_scale = my_arena.get_scale(visible_arena,p1_screen) #define our screen_scale - needed to properly position the players

#create a battle engine
battle_engine = battle.BattleEngine("","",False)

#configure the arena flag locations
my_arena.set_flag_locations(flag_tiles)

#create an HUD system object for P1 + menu handler
hud = HUD.HUD()
hud.default_display_size = [160, 120]
mh = menu.Menuhandler()
mh.default_display_size = [160, 120]

#Set the account rating of all our players and bots
ACCT_RATING = 31.0
#Players Per Team
ppt = 8
#Bot Intelligence Rating
bir = 1.50

#create our tank object
p1_acct = battle_engine.create_account(ACCT_RATING,"Player 1")
p1_acct.specialization = random.randint(-account.upgrade_limit,account.upgrade_limit)
tank = p1_acct.create_tank(T1, "Player Team")
#[hacks] increase the tank's stats
##tank.RPM = 150.0
##tank.shells[0] = 99
##tank.shells[1] = 99
##tank.shells[2] = 99
##tank.shells[3] = 99
##tank.damage_multiplier = 2.5
##tank.penetration_multiplier = 7.5
##tank.speed = 3.0
#set its location onscreen
tank.screen_location = [(p1_screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (p1_screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]
tank.goto(my_arena.flag_locations[0], my_arena.TILE_SIZE, my_arena.get_scale(visible_arena,p1_screen))
#add an HUD bar to the side of p1's screen so that p1 can see his own HP
hud.add_HUD_element("vertical bar",[[0,0],[10,120],[[0,255,0],[0,0,0],[0,0,255]],1.0])
#add a label to p1's HP/armor bar
hud.add_HUD_element("text",[[1,120 / 2],5,[[100,100,100],None,None],"a."])
#add a numerical indicator of p1's HP/armor
hud.add_HUD_element("text",[[1,120 / 2 + 4],3,[[100,100,100],None,None],"100"])
#add some menu elements to p1's screen
mh.create_menu(["","","","","","","","","",""],
               [
                #start by adding our powerup items to the menu
                ["../../pix/powerups/fuel.png",[10,0]],
                ["../../pix/powerups/fire-extinguisher.png",[10,20]],
                ["../../pix/powerups/dangerous-loading.png",[10,40]],
                ["../../pix/powerups/explosive-tip.png",[10,60]],
                ["../../pix/powerups/amped-gun.png",[10,80]],
                ["../../pix/powerups/makeshift-armor.png",[10,100]],
                #add our shells to the menu
                ["../../pix/ammunition/hollow_shell_button.png",[40,0]],
                ["../../pix/ammunition/regular_shell_button.png",[60,0]],
                ["../../pix/ammunition/explosive_shell_button.png",[80,0]],
                ["../../pix/ammunition/disk_shell_button.png",[100,0]]
                ],
               [],buttonindexes=[],name="")
#add numerical indicators of p1's powerup cooldown states (index 4-9)
hud.add_HUD_element("text",[[11,1],9,[[255,0,0],None,None],"cooldown powerup 1"])
hud.add_HUD_element("text",[[11,21],9,[[255,0,0],None,None],"cooldown powerup 2"])
hud.add_HUD_element("text",[[11,41],9,[[255,0,0],None,None],"cooldown powerup 3"])
hud.add_HUD_element("text",[[11,61],9,[[255,0,0],None,None],"cooldown powerup 4"])
hud.add_HUD_element("text",[[11,81],9,[[255,0,0],None,None],"cooldown powerup 5"])
hud.add_HUD_element("text",[[11,101],9,[[255,0,0],None,None],"cooldown powerup 6"])
#add numerical indicators of p1's shell reload times (index 10-13)
hud.add_HUD_element("text",[[41,1],9,[[255,0,0],None,None],"hollow shell"])
hud.add_HUD_element("text",[[61,1],9,[[255,0,0],None,None],"regular shell"])
hud.add_HUD_element("text",[[81,1],9,[[255,0,0],None,None],"explosive shell"])
hud.add_HUD_element("text",[[101,1],9,[[255,0,0],None,None],"disk shell"])
#add numerical indicators of p1's shells left (index 14-17)
hud.add_HUD_element("text",[[41,10],9,[[255,255,0],None,None],"hollow shell"])
hud.add_HUD_element("text",[[61,10],9,[[255,255,0],None,None],"regular shell"])
hud.add_HUD_element("text",[[81,10],9,[[255,255,0],None,None],"explosive shell"])
hud.add_HUD_element("text",[[101,10],9,[[255,255,0],None,None],"disk shell"])

#list of bullet objects
bullets = []

#list of powerup objects
powerups = []

#spawn P2 (bot)...
p2_acct = battle_engine.create_account(ACCT_RATING,"Player 2")
p2_acct.specialization = random.randint(-account.upgrade_limit,account.upgrade_limit)
p2_tank = p2_acct.create_tank(T2, "Bot Team")
#set the tank's map location
p2_tank.goto(my_arena.flag_locations[1], my_arena.TILE_SIZE)

players = [tank, p2_tank]
old_positions = [None]
# - Uncomment the commented list to make the players become bots, and you can passively watch a completely bot-only battle! -
bot_player_managers = [None, entity.Bot(1, 1, bir)] #[entity.Bot(0, 0, bir), entity.Bot(1, 1, bir)]
huds = [hud]

#add some extra bots to the game...LOL
for x in range(0,(ppt - 1) * 2):
    bot_player_managers.append(entity.Bot(x % 2, x + 2, [bir,bir][x % 2])) #create the bot manager
    #create the bot account, and create a bot tank. Append that to the players list...
    bot_acct = battle_engine.create_account(ACCT_RATING,"Bot Player " + str(x))
    bot_acct.specialization = random.randint(-account.upgrade_limit,account.upgrade_limit)
    players.append(bot_acct.create_tank([T1,T2][x % 2], ["Player Team","Bot Team"][x % 2]))
    bot_player_managers[x + 2].start_pos(players,my_arena,my_arena.get_scale(visible_arena,p1_screen))
if(len(flag_tiles) > 2): #third bot team
    for x in range(0,ppt):
        bot_player_managers.append(entity.Bot(2, x + ppt * 2, bir)) #create the bot manager
        #create the bot account, and create a bot tank. Append that to the players list...
        bot_acct = battle_engine.create_account(ACCT_RATING,"Bot Player " + str(x + ppt * 2))
        bot_acct.specialization = random.randint(-account.upgrade_limit,account.upgrade_limit)
        players.append(bot_acct.create_tank(T3, "2nd Bot Team"))
        bot_player_managers[x + ppt * 2].start_pos(players,my_arena,my_arena.get_scale(visible_arena,p1_screen))
if(len(flag_tiles) > 3): #fourth bot team
    for x in range(0,ppt):
        bot_player_managers.append(entity.Bot(3, x + ppt * 3, bir)) #create the bot manager
        #create the bot account, and create a bot tank. Append that to the players list...
        bot_acct = battle_engine.create_account(ACCT_RATING,"Bot Player " + str(x + ppt * 3))
        bot_acct.specialization = random.randint(-account.upgrade_limit,account.upgrade_limit)
        players.append(bot_acct.create_tank(T4, "3nd Bot Team"))
        bot_player_managers[x + ppt * 3].start_pos(players,my_arena,my_arena.get_scale(visible_arena,p1_screen))

player_bar_hud_start = 17
for x in range(0,len(players)): #add the HUD elements for all players to p1's HUD engine
    hud.add_HUD_element("horizontal bar",[[0,-50],[20,5],[[0,255,0],[0,0,0],[0,0,255]],1.0],False)
    hud.add_HUD_element("text",[[0,-50],7,[[255,0,0],False,False],"100 HP"],False)

# - Print out the arena size, and the squares of space available to one player -
free_space = 0
for y in range(0,len(my_arena.arena)):
    for x in range(0,len(my_arena.arena[y])):
        if(my_arena.arena[y][x] not in blocks and my_arena.arena[y][x] not in bricks): #we've found a tile of free space!
            free_space += 1
print("Arena size: " + str(len(my_map[0])) + " x " + str(len(my_map)) + " = " + str(len(my_map[0]) * len(my_map)))
print("Free space: " + str(free_space))
print("1p arena space: " + str(round(len(my_map) * len(my_map[0]) / len(players),1)))
print("1p free space: " + str(round(free_space / len(players),1)))

### - Uncomment this script to turn on MINES game mode! -
##for x in range(0,len(players)):
##    players[x].penetration_multiplier = 0.01
##    players[x].damage_multiplier += 250.0

#this is a list of constants; unscaled mouse positions to click on p2 and p1's powerup items
powerup_positions = [
    [10,0],
    [10,20],
    [10,40],
    [10,60],
    [10,80],
    [10,100]
    ]

#list of GFX particles
particles = []

#Contains the dynamically changing fire color
fire_color = [255,0,0]

#constants; list of keypress IDs for various tank controls
tank_move = [pygame.K_w,
             pygame.K_a,
             pygame.K_s,
             pygame.K_d
             ]
tank_bullets = [pygame.K_1,
                pygame.K_2,
                pygame.K_3,
                pygame.K_4
                ]
tank_shoot = pygame.K_e
tank_powerups = [pygame.K_z,
                 pygame.K_x,
                 pygame.K_c,
                 pygame.K_v,
                 pygame.K_b,
                 pygame.K_n,
                 ]
#P2 control constants
p2_tank_move = [pygame.K_UP,
             pygame.K_LEFT,
             pygame.K_DOWN,
             pygame.K_RIGHT
             ]
p2_tank_bullets = [pygame.K_7,
                pygame.K_8,
                pygame.K_9,
                pygame.K_0
                ]
p2_tank_shoot = pygame.K_SPACE
p2_tank_powerups = [pygame.K_t,
                 pygame.K_y,
                 pygame.K_u,
                 pygame.K_i,
                 pygame.K_o,
                 pygame.K_p,
                 ]

#miscellaneous variables needed within the game loop
running = True
keypresses = [] #holds the list of which keys are pressed at any given time
screen_scale = my_arena.get_scale(visible_arena,p1_screen)
mousepos = [0,0] #where is da mouse onscreen?
fps_clock = pygame.time.Clock() #what's our FPS?
framecounter = 0 #this is a framecounter which is needed for fire GFX
while running:
    # - configure a viewport for the player -
    p1_screen = pygame.Surface([screen.get_width(), screen.get_height()])

    #update our FPS counter
    fps_clock.tick()
    pygame.display.set_caption("FPS: " + str(int(fps_clock.get_fps())))
    framecounter += 1
    if(framecounter > 65535):
        framecounter = 0

    #spawn new powerups if it is time
    entity.spawn_powerups(my_arena,powerups,powerup_images)

    # - Reposition players if we resize (only used for P1 now) -
    if(old_positions[0] != None):
        old_pos = old_positions[0]
        players[0].goto(old_pos,my_arena.TILE_SIZE,screen_scale)
        old_positions[0] = None
        players[0].clear_unmove_flag() #make sure the tank can move; sometimes the one frame when a tank is embedded in a block freezes its motion in one direction.
    
    #event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #we wants out?
            running = False
        elif(event.type == pygame.VIDEORESIZE): #we need to make sure our players stay in the same place they were...
            #set old_positions so we can maintain our current position regardless of window resize...
            old_positions[0] = players[0].overall_location[:]
            screen = pygame.display.set_mode(event.size[:], pygame.RESIZABLE) #resize our window...!
            p1_screen = pygame.Surface([screen.get_width(), screen.get_height()])
        elif(event.type == pygame.KEYDOWN):
            keypresses.append(event.key)
        elif(event.type == pygame.KEYUP):
            keypresses.remove(event.key)
        elif(event.type == pygame.MOUSEMOTION):
            mousepos = event.pos[:]
        elif(event.type == pygame.MOUSEBUTTONDOWN):
            p1_collision = mh.menu_collision([0,0],[p1_screen.get_width(),p1_screen.get_height()],mousepos)
            if(p1_collision[0][1] != None):
                if(p1_collision[0][1] <= 5): #we clicked on a powerup?
                    tank.use_powerup(p1_collision[0][1]) #use powerup
                else: #we clicked on a shell
                    tank.use_shell(p1_collision[0][1] - 6)

    #tank controls handling
    for x in range(0,len(tank_move)):
        if(tank_move[x] in keypresses):
            tank.move(x * 90, my_arena.TILE_SIZE, screen_scale) #move in whatever direction needed
            break #no more than ONE movement per frame; otherwise BAD stuff happens; self.direction gets corrupted with weird values, and you can literally fire stationary bullets...DON'T ASK WHY, I don't care anymore!!
    for x in range(0,len(tank_bullets)): #bet you that changing bullet types more than once per frame also causes issues (I got division errors and all kinds of weird stuff with multiple move() commands on 1 frame)
        if(tank_bullets[x] in keypresses):
            tank.use_shell(x) #change bullets
            break
    for x in range(0,len(tank_powerups)):
        if(tank_powerups[x] in keypresses):
            tank.use_powerup(x, False) #use powerup
            tank.use_powerup(0,True) #update the powerup state for this player (because entity.py is written with server-client architecture in mind)
    if(tank_shoot in keypresses):
        potential_bullet = tank.shoot(my_arena.TILE_SIZE)
        if(potential_bullet != None): #if we were able to shoot, add the bullet object to our bullet object list
            bullets.append(potential_bullet)

    #check if any bullets have hit eachother
    decx = 0
    for x in range(0,len(bullets)):
        decy = 0
        for y in range(0,len(bullets)):
            if(x >= y): #we can't be checking collision against ourself! We also want to avoid double-checking collision.
                continue
            else: #proceed with checking bullet-bullet collision
                collision = entity.check_collision(bullets[x - decx],bullets[y - decy], my_arena.TILE_SIZE)
                if(collision[0] == True): #the bullets hit eachother???
                    damage_outcome = entity.handle_damage([bullets[x - decx],bullets[y - decy]]) #both bullets get damaged then...
                    if(damage_outcome != None): #print out the damage, AND add an explosion effect
                        GFX.create_explosion(particles, [bullets[x - decx].map_location[0] + 0.5,bullets[x - decx].map_location[1] + 0.5], 0.5, [0.1, 0.35], bullets[x - decx].explosion_colors, [[0,0,0],[50,50,50],[100,100,100]], 0.35, 0, None, my_arena.TILE_SIZE)
                        GFX.create_explosion(particles, [bullets[y - decy].map_location[0] + 0.5,bullets[y - decy].map_location[1] + 0.5], 0.5, [0.1, 0.35], bullets[y - decy].explosion_colors, [[0,0,0],[50,50,50],[100,100,100]], 0.35, 0, None, my_arena.TILE_SIZE)
                        #draw damage numbers
                        particles.append(GFX.Particle(bullets[x - decx].map_location, [bullets[x - decx].map_location[0], bullets[x - decx].map_location[1] + 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(damage_outcome[0]))))
                        particles.append(GFX.Particle(bullets[y - decy].map_location, [bullets[y - decy].map_location[0], bullets[y - decy].map_location[1] - 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(damage_outcome[1]))))
                if(bullets[x - decx].destroyed == True): #a bullet broke?
                    del(bullets[x - decx])
                    decx += 1
                    decy += 1
                elif(bullets[y - decy].destroyed == True): #a bullet broke?
                    del(bullets[y - decy])
                    decx += 1
                    decy += 1

    # - Handle on-arena powerups -
    for x in range(0,len(powerups)):
        powerups[x].clock()
        for y in range(0,len(players)):
            if(entity.check_collision(powerups[x],players[y],my_arena.TILE_SIZE)[0]): #player is touching a powerup?
                powerups[x].use(players[y])
        if(powerups[x].despawn == True): #powerup needs to despawn?
            del(powerups[x])
            break

    # - Update P1's menu engine -
    mh.update(p1_screen)

    # - Update P1's HUD, starting with P1's HP/Armor bar -
    if(tank.armor > 0.025):
        color = [0,255,0]
        value = tank.armor / tank.start_armor
        label = "A."
        hud.update_HUD_element_value(2,str(int(tank.armor)))
    else:
        color = [255,0,0]
        value = tank.HP / tank.start_HP
        label = "HP"
        hud.update_HUD_element_value(2,str(int(tank.HP)))
    if(value > 1.0): #we have more armor/HP then we are technically supposed to?
        value = 1.0
        color = [255,255,0] #overdrive color; means we have more than we should...
    hud.update_HUD_element_value(0,value)
    hud.update_HUD_element_color(0,[color,[0,0,0],[0,0,255]])
    hud.update_HUD_element_value(1,label)
    #update P1's HP bar HUD elements
    for x in range(0,len(players)):
        if(x == 0): #we don't need to update HUD elements for P1 and 2
            continue
        if(players[x].armor > 0.025):
            color = [0,255,0]
            value = players[x].armor / players[x].start_armor
            label = str(int(players[x].armor)) + " A."
        else:
            color = [255,0,0]
            value = players[x].HP / players[x].start_HP
            label = str(int(players[x].HP)) + " HP"
        if(value > 1.0): #we have more armor/HP then we are technically supposed to?
            value = 1.0
            color = [255,255,0] #overdrive color; means we have more than we should...
        hud.update_HUD_element(player_bar_hud_start + x * 2,[[(players[x].overall_location[0] - tank.map_location[0]) * my_arena.TILE_SIZE * screen_scale[0],(-0.3 + players[x].overall_location[1] - tank.map_location[1]) * my_arena.TILE_SIZE * screen_scale[1]],[20,5],[color,[0,0,0],[0,0,255]],value])
        hud.update_HUD_element(x * 2 + player_bar_hud_start + 1,[[(players[x].overall_location[0] - tank.map_location[0] + 0.05) * my_arena.TILE_SIZE * screen_scale[0],(-0.25 + players[x].overall_location[1] - tank.map_location[1]) * my_arena.TILE_SIZE * screen_scale[1]],3,[[150,150,150],None,None],label])
    #update P1's powerup cooldown HUD
    for x in range(3,9):
        if(tank.powerups[x - 3] != None and tank.powerups[x - 3] != True):
            if(str(type(tank.powerups[x - 3])) == "<class 'str'>"): #we're currently using the powerup?
                hud.update_HUD_element_value(x,str(int(float(tank.powerups[x - 3]))))
                hud.update_HUD_element_color(x,[[255,255,0],None,None])
            elif(tank.powerups[x - 3] != None): #powerup is on cooldown?
                hud.update_HUD_element_value(x,str(int(float(tank.powerups[x - 3]))))
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
            elif(tank.powerups[x - 3] != None):
                hud.update_HUD_element_value(x,key_to_press)
                hud.update_HUD_element_color(x,[[0,255,0],None,None])
            else: #powerup isn't available!!!
                hud.update_HUD_element_value(x,"x")
                hud.update_HUD_element_color(x,[[255,0,0],None,None])
    #update P1's shell HUD
    for x in range(9,13):
        if(tank.reload_time() != True): #the tank hasn't finished reloading yet?
            if(tank.current_shell == x - 9): #display the reload time left if we're loading this type of shell.
                #Else, just draw the key needed to use the shell type.
                hud.update_HUD_element_value(x,str(int(tank.reload_time())))
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
        hud.update_HUD_element_value(x,str(int(tank.shells[x - 13])))

    #update our tank's collision box
    screen_scale = my_arena.get_scale(visible_arena,p1_screen) #get our display's scale
    players[0].screen_location = [(p1_screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (p1_screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]
    
    #handle a whole bunch of things at once for all tanks
    for x in range(0,len(players)):
        if(players[x].destroyed == True):
            continue
        clocked_damage = players[x].clock(my_arena.TILE_SIZE, screen_scale, particles, framecounter) #handle tank timing stuff

    #Update the particle effects
    decrement = 0
    for x in range(0,len(particles)):
        particles[x + decrement].clock()
        if(particles[x + decrement].timeout == True):
            del(particles[x + decrement])
            decrement -= 1

    for p in range(0,len(players)):
        #handle moving a tank and repositioning the map
        if(players[p].destroyed == True):
            continue
        collided_tiles = my_arena.check_collision([2,2],[int(players[p].overall_location[0]), int(players[p].overall_location[1])],players[p].return_collision(my_arena.TILE_SIZE,3))
        for x in collided_tiles: #iterate through all collision boxes we hit (every tile we're touching)
            if(x[0] in blocks): #we're touching something Not Allowed?
                players[p].unmove()
                break #we only should run this ONCE. Twice could cause wall clipping...

    #check if any tanks are DEAD
    for x in range(0,len(players)):
        if(players[x].explosion_done == False): #this tank died!!
            players[x].explosion_done = True #this tank has had its explosion now.
            #Create a nice big explosion
            GFX.create_explosion(particles, [players[x].overall_location[0] + 0.5,players[x].overall_location[1] + 0.5], 3, [0.1, 1.5], [[255,0,0],[255,255,0],[100,100,0]], [[0,0,0],[50,50,50],[100,100,100]], 1.0, 0, "BOOM", my_arena.TILE_SIZE)
            #set the tank's destroyed flag
            players[x].destroyed = True
            break
    #check if any bullets hit any players
    for b in range(0,len(bullets)):
        #A player got hit?
        for x in range(0,len(players)):
            if(players[x].destroyed): #destroyed players don't count!
                continue
            collide = entity.check_collision(bullets[b], players[x], my_arena.TILE_SIZE)
            if(collide[0] == True): #a bullet hit a tank??
                dn = entity.handle_damage([bullets[b],players[x]]) #damage the tank, the bullet goes poof.
                if(dn != None):
                    GFX.create_explosion(particles, [bullets[b].map_location[0] + 0.5,bullets[b].map_location[1] + 0.5], 0.5, [0.1, 0.35], bullets[b].explosion_colors, [[0,0,0],[50,50,50],[100,100,100]], 0.35, 0, None, my_arena.TILE_SIZE)
                    particles.append(GFX.Particle(bullets[b].map_location, [bullets[b].map_location[0], bullets[b].map_location[1] + 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(dn[1]))))
        if(bullets[b].destroyed == True): #if da bullet be gone, delete it.
            del(bullets[b])
            break

    #handle bullet motion, timing and deletion
    for x in range(0,len(bullets)):
        bullets[x].clock(particles, framecounter) #run the bullet timing function
        bullets[x].move() #move the bullet
        bullet_collision_box = bullets[x].return_collision(my_arena.TILE_SIZE)
        collided_tiles = my_arena.check_collision(visible_arena,bullet_collision_box,bullet_collision_box)
        for b in collided_tiles:
            #if the bullet hit a brick in particular...and NOT a destroyed one!!
            if(b[0] in bricks and b[0] != bricks[len(bricks) - 1]):
                tmp_brick = entity.Brick(6, 15) #HP does not matter, so long as it is above 5, 15 armor.
                damage_outcome = entity.handle_damage([tmp_brick,bullets[x]])
                GFX.create_explosion(particles, [bullets[x].map_location[0] + 0.5,bullets[x].map_location[1] + 0.5], 0.5, [0.1, 0.35], bullets[x].explosion_colors, [[0,0,0],[50,50,50],[100,100,100]], 0.35, 0, None, my_arena.TILE_SIZE)
                #add a damage number
                particles.append(GFX.Particle(bullets[x].map_location, [bullets[x].map_location[0], bullets[x].map_location[1] + 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(damage_outcome[0]))))
                #b[2] is the tile position in the arena (index)
                if(tmp_brick.armor < 2): #the brick took at least 13HP of damage? Destroyed!! (only shell that does this is disk, 20 damage)
                    #brick is destroyed (*was* ID 13)
                    my_arena.modify_tiles([[b[2],bricks[len(bricks) - 1]]])
                    # - Reset the "unmove" flag on ALL tanks; tanks driving up against a brick that is destroyed can't start driving through it otherwise -
                    for find_entities in range(0,len(players)):
                        players[find_entities].clear_unmove_flag()
                elif(tmp_brick.armor < 7): #the brick took ~10HP of damage (a little less to make sure explosive and regular shells damage bricks)
                    #shuffle tiles by 2! (if b[0] <= 13 - 2 then we can increment b[0] by 2, otherwise block is destroyed.)
                    if(b[0] <= bricks[len(bricks) - 1] - 2):
                        my_arena.modify_tiles([[b[2],b[0] + 2]])
                    else: #Destroyed!!
                        my_arena.modify_tiles([[b[2],bricks[len(bricks) - 1]]])
                        # - Reset the "unmove" flag on ALL tanks; tanks driving up against a brick that is destroyed can't start driving through it otherwise -
                        for find_entities in range(0,len(players)):
                            players[find_entities].clear_unmove_flag()
                elif(tmp_brick.armor < 12): #the brick took ~3HP of damage (comment this out if hollow shell brick damage should be disabled).
                    #shuffle brick tile by 1! (if b[0] <= 13 - 1 then increment b[0] by 1, else block is destroyed.)
                    if(b[0] <= bricks[len(bricks) - 1] - 1):
                        my_arena.modify_tiles([[b[2],b[0] + 1]])
                    else: #Destroyed!
                        my_arena.modify_tiles([[b[2],bricks[len(bricks) - 1]]])
                        # - Reset the "unmove" flag on ALL tanks; tanks driving up against a brick that is destroyed can't start driving through it otherwise -
                        for find_entities in range(0,len(players)):
                            players[find_entities].clear_unmove_flag()
            elif(b[0] in blocks): #if the bullet hits a wall, it is most definitely destroyed, and the tank who shot it...gets a bump on his whiff counter.
                bullets[x].tank_origin.missed_shots += 1
                bullets[x].destroyed = True
        if(bullets[x].destroyed == True): #if the bullet is destroyed, delete it
            del(bullets[x])
            break

    #draw everything onscreen (p1 viewport)
    my_arena.draw_arena(visible_arena,players[0].map_location,p1_screen)
    players[0].draw(p1_screen, screen_scale, my_arena.TILE_SIZE)
    for x in range(0,len(bullets)):
        bullets[x].draw(p1_screen, screen_scale, tank.map_location, my_arena.TILE_SIZE)
    for x in range(0,len(powerups)):
        powerups[x].draw(p1_screen, screen_scale, tank.map_location, my_arena.TILE_SIZE)
    for x in range(0,len(players)):
        if(players[x].destroyed == True):
            continue
        if(x == 0):
            continue
        players[x].draw(p1_screen, screen_scale, my_arena.TILE_SIZE, players[0].map_location)
    #draw the particle affects on p1_screen
    for x in range(0,len(particles)):
        particles[x].draw(my_arena.TILE_SIZE, screen_scale, tank.map_location, p1_screen)
    mh.draw_menu([0,0],[p1_screen.get_width(),p1_screen.get_height()],p1_screen,mousepos) #draw P1's menu system
    hud.draw_HUD(p1_screen) #draw P1's HUD
    # - Draw the minimap - #
    minimap_surf = my_arena.draw_minimap(blocks) #draw the arena on the minimap
    for x in range(0,len(particles)):
        particles[x].draw_minimap(minimap_surf)
    for entities in [bullets, powerups, players]:
        for x in entities:
            if(x.type == "Tank" or x.type == "Bullet"):
                x.draw_minimap(minimap_surf, tank.team, True)
            else: #powerup?
                x.draw_minimap(minimap_surf)
    possible_minimap_sizes = [int(p1_screen.get_width() / 3), int(p1_screen.get_height() / 3)]
    scale_qtys = [minimap_surf.get_width() / minimap_surf.get_height(), minimap_surf.get_height() / minimap_surf.get_width()]
    final_minimap_size = [1,1]
    if(possible_minimap_sizes[0] * scale_qtys[1] < possible_minimap_sizes[1]):
        final_minimap_size[0] = possible_minimap_sizes[0]
        final_minimap_size[1] = int(possible_minimap_sizes[0] * scale_qtys[1])
    else:
        final_minimap_size[1] = possible_minimap_sizes[1]
        final_minimap_size[0] = int(possible_minimap_sizes[1] * scale_qtys[0])
    minimap_surf = pygame.transform.scale(minimap_surf, final_minimap_size) #scale the minimap so it retains its size
    p1_screen.blit(minimap_surf, [p1_screen.get_width() - minimap_surf.get_width(), p1_screen.get_height() - minimap_surf.get_height()]) #copy the minimap to the bottom-right corner of the screen

    #run the bot game analysis script for each bot
    if(old_positions[0] == None): #we can't be resizing...if we do and we're running a bots-only game, the 1p bot could explode if he teleports outside the arena for one frame.
        for x in range(0,len(bot_player_managers)):
            if(players[x].destroyed == True):
                continue
            if(bot_player_managers[x] != None):
                potential_bullet = bot_player_managers[x].analyse_game(players,bullets,my_arena,my_arena.TILE_SIZE,blocks,screen_scale,2,p1_screen)
                players[x].use_powerup(0,True) #update the powerup state for this player (because entity.py is written with server-client architecture in mind)
                if(potential_bullet != None):
                    bullets.append(potential_bullet)

    #Update the display
    screen.blit(p1_screen,[0,0])
    pygame.display.flip() #update the display
    p1_screen.fill([0,0,0]) #clear the screen for next frame
    my_arena.shuffle_tiles() #shuffle the arena's water tiles
    
pygame.quit() #exit pygame

p1_acct.return_tank(tank,rebuy=True,bp_to_cash=True,experience=True,verbose=True)
print("\n\n\n")
p2_acct.return_tank(p2_tank,rebuy=True,bp_to_cash=True,experience=True,verbose=True)
print("\n\n\n")

print(p1_acct)
print("\n\n\n")
print(p2_acct)
print("\n\n\n")
