##"ArenaTest.py" demo ---VERSION 0.02---
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

import pygame, time #other people's libraries
import arena #my own library

#pygame stuff
pygame.init()
screen = pygame.display.set_mode([320, 240], pygame.RESIZABLE)
pygame.key.set_repeat(5,5)

#tank images
T1U1 = pygame.image.load("../../pix/tanks/P1U1.png")
T1U2 = pygame.image.load("../../pix/tanks/P1U2.png")
image_cycle = [T1U1, T1U2]
image_ct = 0 #which image we're currently using

blocks = [15,16,17,18,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35] #list of all blocks we cannot run through

#our arena map we will be drawing
my_map = [[ 5, 6, 1, 2,11, 0, 1, 2,16,16, 1, 2],
          [ 8, 7,35, 1,11,11, 2, 1,16,39,36, 1],
          [ 4, 4, 3, 3, 4,11,11,11,11,38,37, 3],
          [18,18, 3, 3, 4, 4, 3, 3,11, 4, 3, 3],
          [18,18, 7, 8, 0, 0,19, 2,11, 8, 7, 6],
          [ 0, 0, 2, 7, 0, 0, 2, 5,11, 7, 2, 1],
          [ 4, 4, 3, 6, 5, 6, 3, 6,11,11,11, 3],
          [19,19, 3, 3, 4, 7, 8, 7, 4, 4,11, 3],
          [19,19, 1, 2,10,10, 9, 9, 0, 0,11,11],
          [ 0, 0, 2, 1, 0, 0, 2, 1, 0, 0, 2, 1],
          [15,15, 3, 3, 4, 4, 3, 3, 4,17,17, 3],
          [15,15, 3, 3,30,25,21,21,27,17,17, 3],
          [33,25,25,25,24, 0,23,20,24, 0, 2, 1],
          [15,15, 3, 3,32, 4,29,28,17,17, 3, 3],
          [15,15, 3, 3, 4, 4, 3, 3, 4,17,17, 3]]

#all the tiles we can draw in the arena
my_tiles = [pygame.image.load("../../pix/blocks/original_20x20/ground/asphalt.png"), #0
            pygame.image.load("../../pix/blocks/original_20x20/ground/forest-1.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/forest-2.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/forest-1.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/forest-3.png"), #4
            pygame.image.load("../../pix/blocks/original_20x20/ground/grass-1.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/grass-2.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/grass-1.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/grass-3.png"), #8
            pygame.image.load("../../pix/blocks/original_20x20/ground/dirt.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/cement.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/water-1.png"), #11
            pygame.image.load("../../pix/blocks/original_20x20/ground/water-2.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/water-3.png"),
            pygame.image.load("../../pix/blocks/original_20x20/ground/water-4.png"), #14
            pygame.image.load("../../pix/blocks/original_20x20/brick/brick0h.png"), #15
            pygame.image.load("../../pix/blocks/original_20x20/brick/brick1h.png"),
            pygame.image.load("../../pix/blocks/original_20x20/brick/brick2h.png"),
            pygame.image.load("../../pix/blocks/original_20x20/brick/brick3h.png"),
            pygame.image.load("../../pix/blocks/original_20x20/brick/brick_destroyed.png"), #19
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall.png"), #20
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-top.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-bottom.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-left.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-edge/wall-edge-right.png"), #24
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-double-edge/wall-double-edge-horizontal.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-double-edge/wall-double-edge-vertical.png"), #26
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-top-right.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-bottom-right.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-bottom-left.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-corner/wall-corner-top-left.png"), #30
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-top.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-bottom.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-left.png"),
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-peninsula/wall-peninsula-right.png"), #34
            pygame.image.load("../../pix/blocks/original_20x20/wall/wall-island.png"), #35
            pygame.image.load("../../pix/blocks/original_20x20/flags/team-1.png"),
            pygame.image.load("../../pix/blocks/original_20x20/flags/team-2.png"),
            pygame.image.load("../../pix/blocks/original_20x20/flags/team-3.png"),
            pygame.image.load("../../pix/blocks/original_20x20/flags/team-4.png")]

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

my_arena = arena.Arena(my_map, my_tiles, my_shuffle) #create an arena object
visible_arena = [10,10]

#tank variables
tank_direction = 'up'
tank_velocity = [0,0]
tank_arena_position = [12,12] #where we are located within the arena (this coordinate stays in 1x1 tile resolution)
tank_blit_position = [0,0]
tank_drive_time = time.time() #every time.time() - tank_drive_time > 0.25s, we change which driving frame we're using.

# - Updates which tread frame we're currently using -
def check_drive_time():
    global tank_drive_time, image_cycle, image_ct
    if(time.time() - tank_drive_time > 0.25):
        tank_drive_time = time.time()
        image_ct += 1
        if(image_ct > len(image_cycle) - 1):
            image_ct = 0

running = True
while running:
    #event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #we wants out?
            running = False
        elif(event.type == pygame.KEYDOWN):
            if(event.key == pygame.K_UP): #we pressed up (move the map down)
                tank_velocity[1] += 0.01
                tank_direction = 'up'
                check_drive_time()
            elif(event.key == pygame.K_DOWN): #we pressed down (move the map up)
                tank_velocity[1] -= 0.01
                tank_direction = 'down'
                check_drive_time()
            elif(event.key == pygame.K_LEFT): #we pressed left (move the map right)
                tank_velocity[0] += 0.01
                tank_direction = 'left'
                check_drive_time()
            elif(event.key == pygame.K_RIGHT): #we pressed right (move the map left)
                tank_velocity[0] -= 0.01
                tank_direction = 'right'
                check_drive_time()

    #update our tank's collision box
    screen_scale = my_arena.get_scale(visible_arena,screen) #get our display's scale

    #draw everything onscreen
    my_arena.draw_arena(visible_arena,tank_arena_position,screen)
    current_frame = image_cycle[image_ct] #which tread animation frame are we using?
    if tank_direction == 'up': #draw the tank
        tmp_surf = pygame.transform.rotate(current_frame, 0)
        screen.blit(pygame.transform.scale(tmp_surf, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    elif tank_direction == 'down':
        tmp_surf = pygame.transform.rotate(current_frame, 180)
        screen.blit(pygame.transform.scale(tmp_surf, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    elif tank_direction == 'left':
        tmp_surf = pygame.transform.rotate(current_frame, 90)
        screen.blit(pygame.transform.scale(tmp_surf, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    elif tank_direction == 'right':
        tmp_surf = pygame.transform.rotate(current_frame, 270)
        screen.blit(pygame.transform.scale(tmp_surf, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    #Draw the tank's collision box (keep this commented out unless debugging)
    #pygame.draw.rect(screen,[0,0,0],[tank_collision_position[0],tank_collision_position[1],tank_collision_position[2] - tank_collision_position[0],tank_collision_position[3] - tank_collision_position[1]],2)

    #handle moving the tank and repositioning the map
    tank_arena_position[0] -= tank_velocity[0] #move the tank (really it's the arena, but it's synonymous with moving the tank)
    tank_arena_position[1] -= tank_velocity[1]
    collided_tiles = my_arena.check_collision(visible_arena,tank_arena_position,[tank_arena_position[0] + 0.05, tank_arena_position[1] + 0.05, tank_arena_position[0] + 0.95, tank_arena_position[1] + 0.95])
    for x in collided_tiles: #iterate through all collision boxes we hit (every tile we're touching)
        if(x[0] in blocks): #we're touching something Not Allowed?
            tank_arena_position[0] += tank_velocity[0] #move our tank back to its old position
            tank_arena_position[1] += tank_velocity[1]
    tank_velocity = [0,0] #reset tank_velocity so we're not moving anymore this frame

    pygame.display.flip() #update the display
    screen.fill([0,0,0]) #clear the screen for next frame
    my_arena.shuffle_tiles() #shuffle the arena's water tiles
    
pygame.quit()
