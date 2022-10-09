##"2p_bot_demo.py" demo ---VERSION 0.02---
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

import pygame, arena, entity, GFX, time, random, HUD, menu, battle_client as battle

#pygame stuff
pygame.init()
screen = pygame.display.set_mode([320, 240], pygame.RESIZABLE) #| pygame.SCALED) #uncomment for a large performance boost at the expense of horrible graphics.
p1_screen = pygame.Surface([screen.get_width() / 2, screen.get_height() / 2])
p2_screen = pygame.Surface([screen.get_width() / 2, screen.get_height() / 2])
screens = [p1_screen, p2_screen]

#tank images
T1U = pygame.image.load("../../pix/Characters(gub)/p1U.png")
T2U = pygame.image.load("../../pix/Characters(gub)/p2U.png")
t_images = [T1U, T2U]

#list of all blocks we cannot run through
blocks = []
for x in range(9,30):
    blocks.append(x)
blocks.remove(13) #destroyed bricks can be driven through!

#our arena map we will be drawing
my_map = [[24,19,19,19,19,19,19,19,19,19,19,21],
          [20, 2, 2, 1, 0, 0, 2, 1, 0, 0, 0,12],
          [20, 4,33,11, 9, 9,27,19,21,32, 3,20],
          [20, 4, 3,11, 4, 4, 3, 3,20, 4, 3,20],
          [20, 6, 7,11, 0,27,28, 9,20, 8, 7,20],
          [20, 0, 2, 7, 0, 0, 2, 5,20, 7, 2,20],
          [20, 4, 3, 6, 5, 6, 3, 6,26, 9, 3,20],
          [20, 4, 3, 3, 4, 7, 9, 7, 4, 9, 3,20],
          [20, 0, 1, 2, 0, 0, 9, 9, 0, 9, 1,20],
          [20, 0,30, 1, 0, 0, 2, 9, 9,31, 2,20],
          [20, 0, 3, 3, 4, 4, 3, 3, 4, 4, 2,20],
          [23,12,19,19,19,19,19,19,19,19,19,22]]

#all the tiles we can draw in the arena
my_tiles = [pygame.image.load("../../pix/blocks/ground/asphalt.png"), #0
            pygame.image.load("../../pix/blocks/ground/forest.png"),
            pygame.image.load("../../pix/blocks/ground/grass.png"),
            pygame.image.load("../../pix/blocks/ground/dirt.png"),
            pygame.image.load("../../pix/blocks/ground/cement.png"),
            pygame.image.load("../../pix/blocks/ground/water-1.png"), #5
            pygame.image.load("../../pix/blocks/ground/water-2.png"),
            pygame.image.load("../../pix/blocks/ground/water-3.png"),
            pygame.image.load("../../pix/blocks/ground/water-4.png"), #8
            pygame.image.load("../../pix/blocks/brick/brick0h.png"), #9
            pygame.image.load("../../pix/blocks/brick/brick1h.png"),
            pygame.image.load("../../pix/blocks/brick/brick2h.png"),
            pygame.image.load("../../pix/blocks/brick/brick3h.png"),
            pygame.image.load("../../pix/blocks/brick/brick_destroyed.png"), #13
            pygame.image.load("../../pix/blocks/wall/wall.png"), #14
            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-top.png"),
            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-bottom.png"),
            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-left.png"),
            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-right.png"), #18
            pygame.image.load("../../pix/blocks/wall/wall-double-edge/wall-double-edge-horizontal.png"),
            pygame.image.load("../../pix/blocks/wall/wall-double-edge/wall-double-edge-vertical.png"), #20
            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-top-right.png"),
            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-bottom-right.png"),
            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-bottom-left.png"),
            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-top-left.png"), #24
            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-top.png"),
            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-bottom.png"),
            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-left.png"),
            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-right.png"), #28
            pygame.image.load("../../pix/blocks/wall/wall-island.png"), #29
            pygame.image.load("../../pix/fortresses/team-blue.png"), #30
            pygame.image.load("../../pix/fortresses/team-green.png"), #31
            pygame.image.load("../../pix/fortresses/team-red.png"), #32
            pygame.image.load("../../pix/fortresses/team-yellow.png") #33
            ]

#define our list of powerup images
powerup_images = [
    pygame.image.load("../../pix/blocks/powerups/fuel.png"),
    pygame.image.load("../../pix/blocks/powerups/fire-extinguisher.png"),
    pygame.image.load("../../pix/blocks/powerups/dangerous-loading.png"),
    pygame.image.load("../../pix/blocks/powerups/explosive-tip.png"),
    pygame.image.load("../../pix/blocks/powerups/amped-gun.png"),
    pygame.image.load("../../pix/blocks/powerups/makeshift-armor.png"),
    pygame.image.load("../../pix/ammunition/hollow_shell_button.png"),
    pygame.image.load("../../pix/ammunition/regular_shell_button.png"),
    pygame.image.load("../../pix/ammunition/explosive_shell_button.png"),
    pygame.image.load("../../pix/ammunition/disk_shell_button.png")
    ]
    

#define our tile shuffle system
my_shuffle = [[5,6],
              [6,7],
              [7,8],
              [8,5]]

my_arena = arena.Arena(my_map, my_tiles, my_shuffle) #create an arena object
my_arena.stretch = False

#create a battle engine
battle_engine = battle.BattleEngine("","",False)

#configure the arena flag locations
my_arena.set_flag_locations([30,31,32,33])

#create an HUD system object for P1 + menu handler
hud = HUD.HUD()
hud.default_display_size = [p1_screen.get_width(), p1_screen.get_height()]
mh = menu.Menuhandler()
mh.default_display_size = [p1_screen.get_width(), p1_screen.get_height()]

#create an HUD system object for P2 + menu handler
p2_hud = HUD.HUD()
p2_hud.default_display_size = [p2_screen.get_width(), p2_screen.get_height()]
p2_mh = menu.Menuhandler()
p2_mh.default_display_size = [p2_screen.get_width(), p2_screen.get_height()]

#create our tank object
#tank = entity.Tank(T1U, "Player Team")
p1_acct = battle_engine.create_account(5.1,"Player 1")
tank = p1_acct.create_tank(T1U, "Player Team")
#increase the tank's RPM
#tank.RPM = 25.0
#tank.damage_multiplier = 9
#tank.penetration_multiplier = 5.0
#tank.speed = 1.25
#set its location onscreen
tank.screen_location = [screen.get_width() / 4, screen.get_height() / 4]
tank.map_location = [-1.5, 0]
#add an HUD bar to the side of p1's screen so that p1 can see his own HP
hud.add_HUD_element("vertical bar",[[0,0],[10,p1_screen.get_height()],[[0,255,0],[0,0,0],[0,0,255]],1.0])
#add a label to p1's HP/armor bar
hud.add_HUD_element("text",[[1,p1_screen.get_height() / 2],5,[[100,100,100],None,None],"a."])
#add a numerical indicator of p1's HP/armor
hud.add_HUD_element("text",[[1,p1_screen.get_height() / 2 + 4],3,[[100,100,100],None,None],"100"])
#add some menu elements to p1's screen
mh.create_menu(["","","","","","","","","",""],
               [
                #start by adding our powerup items to the menu
                ["../../pix/blocks/powerups/fuel.png",[10,0]],
                ["../../pix/blocks/powerups/fire-extinguisher.png",[10,20]],
                ["../../pix/blocks/powerups/dangerous-loading.png",[10,40]],
                ["../../pix/blocks/powerups/explosive-tip.png",[10,60]],
                ["../../pix/blocks/powerups/amped-gun.png",[10,80]],
                ["../../pix/blocks/powerups/makeshift-armor.png",[10,100]],
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

#spawn P2...
#p2_tank = entity.Tank(T1U, "Player Team")
p2_acct = battle_engine.create_account(5.1,"Player 2")
p2_tank = p2_acct.create_tank(T1U, "Player Team")
#p2_tank.destroyed = True
#increase the tank's RPM
#p2_tank.RPM = 25.0
#p2_tank.damage_multiplier = 9
#p2_tank.penetration_multiplier = 5.0
#p2_tank.speed = 1
#set the tank's map location
p2_tank.map_location = [0, 3.5]
#set the tank's screen location
p2_tank.screen_location = [screen.get_width() / 4, screen.get_height() / 4]
#add an HUD bar to the side of p2's screen so that p2 can see his own HP
p2_hud.add_HUD_element("vertical bar",[[0,0],[10,p2_screen.get_height()],[[0,255,0],[0,0,0],[0,0,255]],1.0])
#add a label to p2's HP/armor bar
p2_hud.add_HUD_element("text",[[1,p2_screen.get_height() / 2],5,[[100,100,100],None,None],"a."])
#add a numerical indicator of p2's HP/armor
p2_hud.add_HUD_element("text",[[1,p2_screen.get_height() / 2 + 4],3,[[100,100,100],None,None],"100"])
#add some menu elements to p2's screen
p2_mh.create_menu(["","","","","","","","","",""],
               [
                #start by adding our powerup items to the menu
                ["../../pix/blocks/powerups/fuel.png",[10,0]],
                ["../../pix/blocks/powerups/fire-extinguisher.png",[10,20]],
                ["../../pix/blocks/powerups/dangerous-loading.png",[10,40]],
                ["../../pix/blocks/powerups/explosive-tip.png",[10,60]],
                ["../../pix/blocks/powerups/amped-gun.png",[10,80]],
                ["../../pix/blocks/powerups/makeshift-armor.png",[10,100]],
                #add our shells to the menu (index 6-9)
                ["../../pix/ammunition/hollow_shell_button.png",[40,0]],
                ["../../pix/ammunition/regular_shell_button.png",[60,0]],
                ["../../pix/ammunition/explosive_shell_button.png",[80,0]],
                ["../../pix/ammunition/disk_shell_button.png",[100,0]]
                ],
               [],buttonindexes=[],name="")
#add numerical indicators of p2's powerup cooldown states (index 3-8)
p2_hud.add_HUD_element("text",[[11,1],9,[[255,0,0],None,None],"cooldown powerup 1"])
p2_hud.add_HUD_element("text",[[11,21],9,[[255,0,0],None,None],"cooldown powerup 2"])
p2_hud.add_HUD_element("text",[[11,41],9,[[255,0,0],None,None],"cooldown powerup 3"])
p2_hud.add_HUD_element("text",[[11,61],9,[[255,0,0],None,None],"cooldown powerup 4"])
p2_hud.add_HUD_element("text",[[11,81],9,[[255,0,0],None,None],"cooldown powerup 5"])
p2_hud.add_HUD_element("text",[[11,101],9,[[255,0,0],None,None],"cooldown powerup 6"])
#add numerical indicators of p2's shell reload times (index 9-12)
p2_hud.add_HUD_element("text",[[41,1],9,[[255,0,0],None,None],"hollow shell"])
p2_hud.add_HUD_element("text",[[61,1],9,[[255,0,0],None,None],"regular shell"])
p2_hud.add_HUD_element("text",[[81,1],9,[[255,0,0],None,None],"explosive shell"])
p2_hud.add_HUD_element("text",[[101,1],9,[[255,0,0],None,None],"disk shell"])
#add numerical indicators of p2's shells left (index 13-16)
p2_hud.add_HUD_element("text",[[41,10],9,[[255,255,0],None,None],"hollow shell"])
p2_hud.add_HUD_element("text",[[61,10],9,[[255,255,0],None,None],"regular shell"])
p2_hud.add_HUD_element("text",[[81,10],9,[[255,255,0],None,None],"explosive shell"])
p2_hud.add_HUD_element("text",[[101,10],9,[[255,255,0],None,None],"disk shell"])

players = [tank, p2_tank]
bot_player_managers = [None, None]
huds = [hud, p2_hud]

#add some extra bots to the game...LOL
for x in range(0,2):
    bot_player_managers.append(entity.Bot(2, x + 2, 1.15)) #create the bot manager
    #create the bot account, and create a bot tank. Append that to the players list...
    players.append(battle_engine.create_account(5.1,"Bot Player " + str(x)).create_tank(T2U, "Bot Team"))
    bot_player_managers[x + 2].start_pos(players,my_arena)

player_bar_hud_start = 17
for x in range(0,len(players)): #add the HUD elements for all players to p1's and p2's HUD engines
    p2_hud.add_HUD_element("horizontal bar",[[0,-50],[20,5],[[0,255,0],[0,0,0],[0,0,255]],1.0],False)
    p2_hud.add_HUD_element("text",[[0,-50],7,[[255,0,0],False,False],"100 HP"],False)

    hud.add_HUD_element("horizontal bar",[[0,-50],[20,5],[[0,255,0],[0,0,0],[0,0,255]],1.0],False)
    hud.add_HUD_element("text",[[0,-50],7,[[255,0,0],False,False],"100 HP"],False)

#this is a list of constants; unscaled mouse positions to click on p2 and p1's powerup items
powerup_positions = [
    [10,0],
    [10,20],
    [10,40],
    [10,60],
    [10,80],
    [10,100]
    ]

#way in which bricks change to destroyed - listed from least to most destroyed
bricks = [
    9, #0 hits
    10,
    11,
    12, #3 hits
    13 #destroyed
    ]

visible_arena = [8,8]

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
    # - configure two viewports for each player -
    p1_screen = pygame.Surface([screen.get_width() / 2, screen.get_height() / 2])
    p2_screen = pygame.Surface([screen.get_width() / 2, screen.get_height() / 2])

    #update our FPS counter
    fps_clock.tick()
    pygame.display.set_caption("FPS: " + str(int(fps_clock.get_fps())))
    framecounter += 1
    if(framecounter > 65535):
        framecounter = 0

    #spawn new powerups if it is time
    entity.spawn_powerups(my_arena,powerups,powerup_images)
    
    #event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #we wants out?
            running = False
        elif(event.type == pygame.KEYDOWN):
            keypresses.append(event.key)
        elif(event.type == pygame.KEYUP):
            keypresses.remove(event.key)
        elif(event.type == pygame.MOUSEMOTION):
            mousepos = event.pos[:]
        elif(event.type == pygame.MOUSEBUTTONDOWN):
            p1_collision = mh.menu_collision([0,0],[p1_screen.get_width(),p1_screen.get_height()],mousepos)
            p2_collision = mh.menu_collision([0,0],[p2_screen.get_width(),p2_screen.get_height()],[mousepos[0] - p1_screen.get_width(),mousepos[1] - p1_screen.get_height()])
            if(p1_collision[0][1] != None):
                if(p1_collision[0][1] <= 5): #we clicked on a powerup?
                    tank.use_powerup(p1_collision[0][1]) #use powerup
                else: #we clicked on a shell
                    tank.use_shell(p1_collision[0][1] - 6)
            if(p2_collision[0][1] != None):
                if(p2_collision[0][1] <= 5): #we clicked on a powerup?
                    p2_tank.use_powerup(p2_collision[0][1]) #use powerup
                else: #we clicked on a shell.
                    p2_tank.use_shell(p2_collision[0][1] - 6)

    #tank controls handling
    for x in range(0,len(tank_move)):
        if(tank_move[x] in keypresses):
            tank.move(x * 90, my_arena.TILE_SIZE) #move in whatever direction needed
    for x in range(0,len(tank_bullets)):
        if(tank_bullets[x] in keypresses):
            tank.use_shell(x) #change bullets
    for x in range(0,len(tank_powerups)):
        if(tank_powerups[x] in keypresses):
            tank.use_powerup(x) #use powerup
    if(tank_shoot in keypresses):
        potential_bullet = tank.shoot(my_arena.TILE_SIZE)
        if(potential_bullet != None): #if we were able to shoot, add the bullet object to our bullet object list
            bullets.append(potential_bullet)
    #P2 control handling
    for x in range(0,len(p2_tank_move)):
        if(p2_tank_move[x] in keypresses):
            p2_tank.move(x * 90, my_arena.TILE_SIZE) #move in whatever direction needed
    for x in range(0,len(p2_tank_bullets)):
        if(p2_tank_bullets[x] in keypresses):
            p2_tank.use_shell(x) #change bullets
    for x in range(0,len(p2_tank_powerups)):
        if(p2_tank_powerups[x] in keypresses):
            p2_tank.use_powerup(x) #use powerup
    if(p2_tank_shoot in keypresses):
        potential_bullet = p2_tank.shoot(my_arena.TILE_SIZE)
        if(potential_bullet != None): #if we were able to shoot, add the bullet object to our bullet object list
            bullets.append(potential_bullet)

    #run the bot game analysis script for each bot
    for x in range(0,len(bot_player_managers)):
        if(players[x].destroyed == True):
            continue
        if(bot_player_managers[x] != None):
            potential_bullet = bot_player_managers[x].analyse_game(players,bullets,my_arena,my_arena.TILE_SIZE,blocks)
            if(potential_bullet != None):
                bullets.append(potential_bullet)

    #check if any bullets have hit eachother
    exit_loop = False
    for x in range(0,len(bullets)):
        if(exit_loop): #useful for exiting nested loops like this
            break
        for y in range(0,len(bullets)):
            if(x == y): #we can't be checking collision against ourself!
                continue
            else: #proceed with checking bullet-bullet collision
                collision = entity.check_collision(bullets[x],bullets[y], my_arena.TILE_SIZE)
                if(collision[0] == True): #the bullets hit eachother???
                    damage_outcome = entity.handle_damage([bullets[x],bullets[y]]) #both bullets get damaged then...
                    if(damage_outcome != None): #print out the damage, AND add an explosion effect
                        GFX.create_explosion(particles, [bullets[x].map_location[0] + 0.5,bullets[x].map_location[1] + 0.5], 0.5, [0.1, 0.35], bullets[x].explosion_colors, [[0,0,0],[50,50,50],[100,100,100]], 0.35, 0, None, my_arena.TILE_SIZE)
                        GFX.create_explosion(particles, [bullets[y].map_location[0] + 0.5,bullets[y].map_location[1] + 0.5], 0.5, [0.1, 0.35], bullets[y].explosion_colors, [[0,0,0],[50,50,50],[100,100,100]], 0.35, 0, None, my_arena.TILE_SIZE)
                        #draw damage numbers
                        particles.append(GFX.Particle(bullets[x].map_location, [bullets[x].map_location[0], bullets[x].map_location[1] + 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(damage_outcome[0]))))
                        particles.append(GFX.Particle(bullets[y].map_location, [bullets[y].map_location[0], bullets[y].map_location[1] - 1], 1, 0.75, [200,200,0], [50,50,50], time.time(), time.time() + 2.5, str(int(damage_outcome[1]))))
                if(bullets[x].destroyed == True): #a bullet broke?
                    del(bullets[x])
                    exit_loop = True
                    break
                elif(bullets[y].destroyed == True): #a bullet broke?
                    del(bullets[y])
                    exit_loop = True
                    break

    # - Handle on-arena powerups -
    for x in range(0,len(powerups)):
        powerups[x].clock()
        for y in range(0,len(players)):
            if(entity.check_collision(powerups[x],players[y],my_arena.TILE_SIZE)[0]): #player is touching a powerup?
                powerups[x].use(players[y])
        if(powerups[x].despawn == True): #powerup needs to despawn?
            del(powerups[x])
            break

    # - Update P1 and 2's menu engine -
    mh.update(p1_screen)
    p2_mh.update(p2_screen)

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

    # - Update P2's HUD -
    if(p2_tank.armor > 0.025):
        color = [0,255,0]
        value = p2_tank.armor / p2_tank.start_armor
        label = "A."
        p2_hud.update_HUD_element_value(2,str(int(p2_tank.armor)))
    else:
        color = [255,0,0]
        value = p2_tank.HP / p2_tank.start_HP
        label = "HP"
        p2_hud.update_HUD_element_value(2,str(int(p2_tank.HP)))
    if(value > 1.0): #we have more armor/HP then we are technically supposed to?
        value = 1.0
        color = [255,255,0] #overdrive color; means we have more than we should...
    p2_hud.update_HUD_element_value(0,value)
    p2_hud.update_HUD_element_color(0,[color,[0,0,0],[0,0,255]])
    p2_hud.update_HUD_element_value(1,label)
    #update P2's HP bar HUD elements
    for x in range(0,len(players)):
        if(x == 1): #we're not updating our own HUD here...
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
        p2_hud.update_HUD_element(x * 2 + player_bar_hud_start,[[(players[x].overall_location[0] - p2_tank.map_location[0]) * my_arena.TILE_SIZE * screen_scale[0],(-0.3 + players[x].overall_location[1] - p2_tank.map_location[1]) * my_arena.TILE_SIZE * screen_scale[1]],[20,5],[color,[0,0,0],[0,0,255]],value])
        p2_hud.update_HUD_element(x * 2 + player_bar_hud_start + 1,[[(players[x].overall_location[0] - p2_tank.map_location[0] + 0.05) * my_arena.TILE_SIZE * screen_scale[0],(-0.25 + players[x].overall_location[1] - p2_tank.map_location[1]) * my_arena.TILE_SIZE * screen_scale[1]],3,[[150,150,150],None,None],label])

    #update P2's powerup cooldown HUD
    for x in range(3,9):
        if(p2_tank.powerups[x - 3] != None and p2_tank.powerups[x - 3] != True):
            if(str(type(p2_tank.powerups[x - 3])) == "<class 'str'>"): #we're currently using the powerup?
                p2_hud.update_HUD_element_value(x,str(int(float(p2_tank.powerups[x - 3]))))
                p2_hud.update_HUD_element_color(x,[[255,255,0],None,None])
            else: #powerup is on cooldown?
                p2_hud.update_HUD_element_value(x,str(int(float(p2_tank.powerups[x - 3]))))
                p2_hud.update_HUD_element_color(x,[[255,0,0],None,None])
        else: #powerup is ready?
            key_to_press = None  #check to see if we can display the key to use the powerup...
            for key in range(0,len(menu.keys)):
                if(p2_tank_powerups[x - 3] == menu.keys[key][0]):
                    key_to_press = menu.keys[key][1]
                    break
            if(key_to_press == None):
                p2_hud.update_HUD_element_value(x,"")
                p2_hud.update_HUD_element_color(x,[[0,255,0],None,None])
            elif(p2_tank.powerups[x - 3] != None):
                p2_hud.update_HUD_element_value(x,key_to_press)
                p2_hud.update_HUD_element_color(x,[[0,255,0],None,None])
            else: #powerup isn't available!!!
                p2_hud.update_HUD_element_value(x,"x")
                p2_hud.update_HUD_element_color(x,[[255,0,0],None,None])
    #update P2's shell HUD
    for x in range(9,13):
        if(p2_tank.reload_time() != True): #the tank hasn't finished reloading yet?
            if(p2_tank.current_shell == x - 9): #display the reload time left if we're loading this type of shell.
                #Else, just draw the key needed to use the shell type.
                p2_hud.update_HUD_element_value(x,str(int(p2_tank.reload_time())))
                p2_hud.update_HUD_element_color(x,[[255,0,0],None,None])
                continue
        #the tank has a shell ready, or we're not loading this type of shell?
        key_to_press = None  #check to see if we can display the key to use the shell...
        for key in range(0,len(menu.keys)):
            if(p2_tank_bullets[x - 9] == menu.keys[key][0]):
                key_to_press = menu.keys[key][1]
                break
        if(key_to_press != None):
            p2_hud.update_HUD_element_value(x,key_to_press)
        else:
            p2_hud.update_HUD_element_value(x,"")
        p2_hud.update_HUD_element_color(x,[[0,255,0],None,None])
    for x in range(13,17):
        p2_hud.update_HUD_element_value(x,str(int(p2_tank.shells[x - 13])))

    #update our tank's collision box
    screen_scale = my_arena.get_scale(visible_arena,p1_screen) #get our display's scale
    players[0].screen_location = [(p1_screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (p1_screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]
    #Update P2's collision box
    players[1].screen_location = [(p2_screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (p2_screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]

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
        #collided_tiles = my_arena.check_collision(visible_arena,players[p].map_location,players[p].return_collision(my_arena.TILE_SIZE,3))
        collided_tiles = my_arena.check_collision([2,2],[int(players[p].overall_location[0]), int(players[p].overall_location[1])],players[p].return_collision(my_arena.TILE_SIZE,3))
        for x in collided_tiles: #iterate through all collision boxes we hit (every tile we're touching)
            if(x[0] in blocks): #we're touching something Not Allowed?
                players[p].unmove()

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
                    #brick is destroyed (ID 13)
                    my_arena.modify_tiles([[b[2],13]])
                elif(tmp_brick.armor < 7): #the brick took ~10HP of damage (a little less to make sure explosive and regular shells damage bricks)
                    #shuffle tiles by 2! (if b[0] <= 13 - 2 then we can increment b[0] by 2, otherwise block is destroyed.)
                    if(b[0] <= 13 - 2):
                        my_arena.modify_tiles([[b[2],b[0] + 2]])
                    else: #Destroyed!!
                        my_arena.modify_tiles([[b[2],13]])
                elif(tmp_brick.armor < 10): #the brick took ~5HP of damage (comment this out if hollow shell brick damage should be disabled).
                    #shuffle brick tile by 1! (if b[0] <= 13 - 1 then increment b[0] by 1, else block is destroyed.)
                    if(b[0] <= 13 - 1):
                        my_arena.modify_tiles([[b[2],b[0] + 1]])
                    else: #Destroyed!
                        my_arena.modify_tiles([[b[2],13]])
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
    #draw everything onscreen (p2 viewport)
    my_arena.draw_arena(visible_arena,players[1].map_location,p2_screen)
    players[1].draw(p2_screen, screen_scale, my_arena.TILE_SIZE)
    for x in range(0,len(bullets)):
        bullets[x].draw(p2_screen, screen_scale, p2_tank.map_location, my_arena.TILE_SIZE)
    for x in range(0,len(powerups)):
        powerups[x].draw(p2_screen, screen_scale, p2_tank.map_location, my_arena.TILE_SIZE)
    for x in range(0,len(players)):
        if(x == 1):
            continue
        if(players[x].destroyed == True):
            continue
        players[x].draw(p2_screen, screen_scale, my_arena.TILE_SIZE, players[1].map_location)
    #draw the particle affects on p2_screen
    for x in range(0,len(particles)):
        particles[x].draw(my_arena.TILE_SIZE, screen_scale, p2_tank.map_location, p2_screen)
    #draw P2's menu system
    p2_mh.draw_menu([0,0],[p2_screen.get_width(),p2_screen.get_height()],p2_screen,[mousepos[0] - p1_screen.get_width(),mousepos[1] - p1_screen.get_height()])
    p2_hud.draw_HUD(p2_screen) #draw P2's HUD

    #Update the display
    screen.blit(p1_screen,[0,0])
    screen.blit(p2_screen,[screen.get_width() / 2,screen.get_height() / 2])
    pygame.display.flip() #update the display
    p1_screen.fill([0,0,0]) #clear the screen for next frame
    my_arena.shuffle_tiles() #shuffle the arena's water tiles
    
pygame.quit() #exit pygame

p1_acct.return_tank(tank,True)
print("\n\n\n")
p2_acct.return_tank(p2_tank,True)
print("\n\n\n")

print(p1_acct)
print("\n\n\n")
print(p2_acct)
print("\n\n\n")
