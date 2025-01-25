##"EntityTest.py" demo ---VERSION 0.01---
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

import pygame, arena, entity

#pygame stuff
pygame.init()
screen = pygame.display.set_mode([320, 240], pygame.RESIZABLE)

#tank images
T1U = pygame.image.load("../../pix/tanks/P1U1.png")
T1U1 = pygame.image.load("../../pix/tanks/P1U2.png")
T2U = pygame.image.load("../../pix/tanks/P2U1.png")
T2U1 = pygame.image.load("../../pix/tanks/P2U2.png")

#list of all blocks we cannot run through
blocks = [16,17,18,19,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36]

#our arena map we will be drawing
my_map = [[31, 26, 26, 26, 26, 26, 26, 22, 22, 26, 26, 26, 26, 26, 26, 28],
          [27, 5, 9, 5, 2, 1, 4, 30, 29, 3, 2, 1, 8, 7, 6, 27],
          [27, 9, 34, 26, 26, 35, 3, 2, 1, 4, 34, 26, 26, 35, 5, 27],
          [27, 9, 5, 6, 9, 9, 36, 18, 36, 18, 1, 5, 6, 9, 9, 27],
          [27, 0, 16, 19, 16, 9, 18, 11, 11, 11, 11, 16, 7, 16, 17, 27],
          [27, 0, 0, 0, 19, 11, 11, 11, 11, 18, 11, 19, 9, 9, 9, 27],
          [27, 0, 19, 0, 16, 11, 18, 18, 18, 18, 11, 16, 9, 19, 10, 27],
          [27, 37, 17, 0, 19, 11, 19, 19, 19, 19, 11, 19, 9, 17, 38, 27],
          [27, 9, 19, 0, 16, 11, 18, 18, 18, 18, 11, 16, 10, 19, 10, 27],
          [27, 9, 9, 9, 19, 11, 18, 11, 11, 11, 11, 19, 10, 10, 10, 27],
          [27, 17, 16, 8, 16, 11, 11, 11, 11, 18, 9, 16, 19, 16, 10, 27],
          [27, 9, 9, 5, 6, 7, 18, 36, 18, 36, 6, 5, 9, 10, 10, 27],
          [27, 9, 34, 26, 26, 35, 4, 3, 2, 7, 34, 26, 26, 35, 10, 27],
          [27, 5, 6, 7, 3, 2, 1, 31, 28, 1, 7, 6, 5, 9, 9, 27],
          [30, 26, 26, 26, 26, 26, 26, 23, 23, 26, 26, 26, 26, 26, 26, 29]]

#all the tiles we can draw in the arena
path = ""
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

#define our tile shuffle system
my_shuffle = [
    [11,12], #water
    [12,13],
    [13,14],
    [14,15],
    [15,11],
    [1,2], #forest
    [2,3],
    [3,4],
    [4,1],
    [5,6], #grass
    [6,7],
    [7,8],
    [8,5]]

my_arena = arena.Arena(my_map, my_tiles, my_shuffle) #create an arena object
my_arena.stretch = False
visible_arena = [15,15]
screen_scale = my_arena.get_scale(visible_arena,screen)

#create our tank object
tank = entity.Tank([T1U,T1U1], ["Player name","The Good Guys"])
#increase the tank's RPM
tank.RPM = 80.0
#set its location onscreen
tank.screen_location = [(screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]

#list of bullet objects
bullets = []

#list of tanks other than ourselves
tanks = []

#spawn some random tanks...
for b in range(0,4):
    atank = entity.Tank([T2U,T2U1], ["Player name", "The Bad Guys"])
    atank.map_location = [(b + 1), (b + 1)]
    tanks.append(atank)

#way in which bricks change to destroyed - listed from least to most destroyed
bricks = [
    16, #0 hits
    17,
    18,
    19, #3 hits
    20 #destroyed
    ]

#constants; list of keypress IDs for various tank controls
tank_move = [pygame.K_UP,
             pygame.K_LEFT,
             pygame.K_DOWN,
             pygame.K_RIGHT
             ]
tank_bullets = [pygame.K_a,
                pygame.K_s,
                pygame.K_d,
                pygame.K_f
                ]
tank_shoot = pygame.K_SPACE
tank_powerups = [pygame.K_1,
                 pygame.K_2,
                 pygame.K_3,
                 pygame.K_4,
                 pygame.K_5,
                 pygame.K_6,
                 ]
change_arena_size = [
    pygame.K_k,
    pygame.K_l
    ]

running = True
current_frame = 0 #framecounter
keypresses = []
tank.screen_location = [(screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]
tank.goto([5,7], my_arena.TILE_SIZE, screen_scale)
while running:
    #event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #we wants out?
            running = False
        elif(event.type == pygame.KEYDOWN and event.key not in keypresses):
            keypresses.append(event.key)
        elif(event.type == pygame.KEYUP and event.key in keypresses):
            keypresses.remove(event.key)

    # - Update framecounter -
    current_frame += 1
    if(current_frame > 65535):
        current_frame = 0

    # - Update screen_scale -
    screen_scale = my_arena.get_scale(visible_arena,screen)

    #tank controls handling
    for x in range(0,len(tank_move)):
        if(tank_move[x] in keypresses):
            tank.move(x * 90, my_arena.TILE_SIZE, screen_scale) #move in whatever direction needed
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

    #update our tank's collision box
    screen_scale = my_arena.get_scale(visible_arena,screen) #get our display's scale
    tank.screen_location = [(screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]

    tank.clock(my_arena.TILE_SIZE, screen_scale, [], current_frame) #handle tank timing stuff

    collided_tiles = my_arena.check_collision([2,2],[int(tank.overall_location[0]), int(tank.overall_location[1])],tank.return_collision(my_arena.TILE_SIZE,3))
    for x in collided_tiles: #iterate through all collision boxes we hit (every tile we're touching)
        if(x[0] in blocks): #we're touching something Not Allowed?
            tank.unmove()
            break #we only should run this ONCE. Twice could cause wall clipping...
    
    #change arena size?
    if(current_frame % 16 == 0):
        if(change_arena_size[0] in keypresses):
            visible_arena[0] += 1
            visible_arena[1] += 1
        elif(change_arena_size[1] in keypresses and visible_arena[0] > 1 and visible_arena[1] > 1):
            visible_arena[0] -= 1
            visible_arena[1] -= 1

    #handle bullet motion, timing and deletion
    for x in range(0,len(bullets)):
        bullets[x].clock([],0) #run the bullet timing function
        bullets[x].move() #move the bullet
        bullet_collision_box = bullets[x].return_collision(my_arena.TILE_SIZE)
        collided_tiles = my_arena.check_collision([len(my_map[0]),len(my_map[1])],[0,0],bullet_collision_box)
        for b in collided_tiles:
            #if the bullet hit a brick in particular...and NOT a destroyed one!!
            if(b[0] in bricks and b[0] != bricks[len(bricks) - 1]):
                tmp_brick = entity.Brick(6, 15) #HP does not matter, so long as it is above 5, 15 armor.
                damage_outcome = entity.handle_damage([tmp_brick,bullets[x]])
                #print(damage_outcome[1][0]) #damage number: Index [1][0]
                #b[2] is the tile position in the arena (index)
                if(tmp_brick.armor < 2): #the brick took at least 13HP of damage? Destroyed!! (only shell that does this is disk, *was* 20 damage)
                    #brick is destroyed (ID 13)
                    my_arena.modify_tiles([[b[2],20]])
                    tank.clear_unmove_flag()
                elif(tmp_brick.armor < 7): #the brick took ~10HP of damage (a little less to make sure explosive and regular shells damage bricks)
                    #shuffle tiles by 2! (if b[0] <= 20 - 2 then we can increment b[0] by 2, otherwise block is destroyed.)
                    if(b[0] < 20 - 2):
                        my_arena.modify_tiles([[b[2],b[0] + 2]])
                    else: #Destroyed!!
                        my_arena.modify_tiles([[b[2],20]])
                        tank.clear_unmove_flag()
                elif(tmp_brick.armor < 13): #the brick took ~2HP of damage (comment this out if hollow shell brick damage should be disabled).
                    #shuffle brick tile by 1! (if b[0] <= 20 - 1 then increment b[0] by 1, else block is destroyed.)
                    if(b[0] < 20 - 1):
                        my_arena.modify_tiles([[b[2],b[0] + 1]])
                    else: #Destroyed!
                        my_arena.modify_tiles([[b[2],20]])
                        tank.clear_unmove_flag()
            elif(b[0] in blocks): #if the bullet hits a wall, it is most definitely destroyed.
                bullets[x].destroyed = True
        if(bullets[x].destroyed == True): #if the bullet is destroyed, delete it
            del(bullets[x])
            break

    #handle all tanks other than ourselves
    for x in range(0,len(tanks)):
        tanks[x].clock() #clock all tank timers
        #check if any tanks are DEAD
        if(tanks[x].destroyed == True):
            del(tanks[x]) #delete the tank from existance!
            break #exit the "for x in range..." loop so that we don't get an IndexError.
        #check if any bullets hit this tank
        for b in range(0,len(bullets)):
            collide = entity.check_collision(bullets[b],tanks[x],my_arena.TILE_SIZE)
            if(collide[0] == True): #a bullet hit a tank??
                entity.handle_damage([bullets[b],tanks[x]]) #damage the tank, the bullet goes poof.
                bullets[b].destroyed = True
            if(bullets[b].destroyed == True): #if da bullet be gone, delete it.
                del(bullets[b])
                break

    #draw everything onscreen
    my_arena.draw_arena(visible_arena,tank.map_location,screen)
    tank.draw(screen, screen_scale, my_arena.TILE_SIZE)
    for x in range(0,len(bullets)):
        bullets[x].draw(screen, screen_scale, tank.map_location, my_arena.TILE_SIZE)
    for x in range(0,len(tanks)):
        tanks[x].draw(screen, screen_scale, my_arena.TILE_SIZE, tank.map_location)

    pygame.display.flip() #update the display
    screen.fill([0,0,0]) #clear the screen for next frame
    my_arena.shuffle_tiles() #shuffle the arena's water tiles
    
pygame.quit()
