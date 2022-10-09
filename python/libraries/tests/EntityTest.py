##"EntityTest.py" demo ---VERSION 0.01---
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

import pygame, arena, entity

#pygame stuff
pygame.init()
screen = pygame.display.set_mode([320, 240], pygame.RESIZABLE)

#tank images
T1U = pygame.image.load("../../pix/Characters(gub)/p1U.png")
T2U = pygame.image.load("../../pix/Characters(gub)/p2U.png")

#list of all blocks we cannot run through
blocks = []
for x in range(9,30):
    blocks.append(x)
blocks.remove(13) #destroyed bricks can be driven through!

#our arena map we will be drawing
my_map = [[24,19,19,19,19,19,19,19,19,19,19,21],
          [20, 7, 2, 1, 0, 0, 2, 1, 0, 0, 2,20],
          [20, 4, 3,11, 9, 9,27,19,21, 4, 3,20],
          [20, 4, 3,11, 4, 4, 3, 3,20, 4, 3,20],
          [20, 6, 7,11, 0, 0,29, 9,20, 8, 7,20],
          [20, 0, 2, 7, 0, 0, 2, 5,20, 7, 2,20],
          [20, 4, 3, 6, 5, 6, 3, 6,26, 9, 3,20],
          [20, 4, 3, 3, 4, 7, 9, 7, 4, 9, 3,20],
          [20, 0, 1, 2, 0, 0, 9, 9, 0, 9, 1,20],
          [20, 0, 2, 1, 0, 0, 2, 9, 9, 9, 2,20],
          [20, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3,20],
          [23,19,19,19,19,19,19,19,19,19,19,22]]

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
            pygame.image.load("../../pix/blocks/wall/wall-island.png")] #29

#define our tile shuffle system
my_shuffle = [[5,6],
              [6,7],
              [7,8],
              [8,5]]

my_arena = arena.Arena(my_map, my_tiles, my_shuffle) #create an arena object
my_arena.stretch = False

#create our tank object
tank = entity.Tank(T1U, ["Player name","The Good Guys"])
#increase the tank's RPM
tank.RPM = 80.0
#set its location onscreen
tank.screen_location = [screen.get_width() / 2, screen.get_height() / 2]

#list of bullet objects
bullets = []

#list of tanks other than ourselves
tanks = []

#spawn some random tanks...
for b in range(0,4):
    atank = entity.Tank(T2U, ["Player name", "The Bad Guys"])
    atank.map_location = [(b + 1), (b + 1)]
    tanks.append(atank)

#way in which bricks change to destroyed - listed from least to most destroyed
bricks = [
    9, #0 hits
    10,
    11,
    12, #3 hits
    13 #destroyed
    ]

visible_arena = [15,15]

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
keypresses = []
screen_scale = my_arena.get_scale(visible_arena,screen)
while running:
    #event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #we wants out?
            running = False
        elif(event.type == pygame.KEYDOWN):
            keypresses.append(event.key)
        elif(event.type == pygame.KEYUP):
            keypresses.remove(event.key)

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
    #change arena size?
    if(change_arena_size[0] in keypresses):
        visible_arena[0] += 1
        visible_arena[1] += 1
    elif(change_arena_size[1] in keypresses):
        visible_arena[0] -= 1
        visible_arena[1] -= 1

    tank.clock(my_arena.TILE_SIZE, screen_scale) #handle tank timing stuff

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
            elif(b[0] in blocks): #if the bullet hits a wall, it is most definitely destroyed.
                bullets[x].destroyed = True
        if(bullets[x].destroyed == True): #if the bullet is destroyed, delete it
            del(bullets[x])
            break

    #update our tank's collision box
    screen_scale = my_arena.get_scale(visible_arena,screen) #get our display's scale
    tank.screen_location = [(screen.get_width() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[0], (screen.get_height() / 2) - (my_arena.TILE_SIZE / 2) * screen_scale[1]]
    tank_collision_position = tank.return_collision(my_arena.TILE_SIZE, 2)

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

    #handle moving the tank and repositioning the map
    collided_tiles = my_arena.check_collision(visible_arena,tank.map_location,tank_collision_position)
    for x in collided_tiles: #iterate through all collision boxes we hit (every tile we're touching)
        if(x[0] in blocks): #we're touching something Not Allowed?
            tank.unmove()

    pygame.display.flip() #update the display
    screen.fill([0,0,0]) #clear the screen for next frame
    my_arena.shuffle_tiles() #shuffle the arena's water tiles
    
pygame.quit()
