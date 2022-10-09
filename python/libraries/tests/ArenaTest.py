##"ArenaTest.py" demo ---VERSION 0.01---
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

import pygame, arena

#pygame stuff
pygame.init()
screen = pygame.display.set_mode([320, 240], pygame.RESIZABLE)
pygame.key.set_repeat(5,5)

#tank images
T1L = pygame.image.load("../../pix/Characters(gub)/p1L.png")
T1R = pygame.image.load("../../pix/Characters(gub)/p1R.png")
T1D = pygame.image.load("../../pix/Characters(gub)/p1D.png")
T1U = pygame.image.load("../../pix/Characters(gub)/p1U.png")

blocks = [9,10,11,12,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29] #list of all blocks we cannot run through

#our arena map we will be drawing
my_map = [[ 5, 6, 1, 2, 0, 0, 1, 2, 0, 0, 1, 2],
          [ 8, 7, 2, 1, 0, 0, 2, 1, 0, 0, 2, 1],
          [ 4, 4, 3, 3, 4, 4,14,14,14, 4, 3, 3],
          [ 4, 4, 3, 3, 4, 4, 3, 3,14, 4, 3, 3],
          [ 5, 6, 7, 8, 0, 0,19, 2,14, 8, 7, 6],
          [ 0, 0, 2, 7, 0, 0, 2, 5,14, 7, 2, 1],
          [ 4, 4, 3, 6, 5, 6, 3, 6,14, 4, 3, 3],
          [ 4, 4, 3, 3, 4, 7, 8, 7, 4, 4, 3, 3],
          [ 0, 0, 1, 2, 0, 0, 1,13, 0, 0, 1, 2],
          [ 0, 0, 2, 1, 0, 0, 2, 1, 0, 0, 2, 1],
          [ 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3],
          [ 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3]]

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
visible_arena = [10,10]

#tank variables
tank_direction = 'up'
tank_velocity = [0,0]
tank_arena_position = [10,10] #where we are located within the arena (this coordinate stays in 1x1 tile resolution)
tank_blit_position = [0,0]

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
            elif(event.key == pygame.K_DOWN): #we pressed down (move the map up)
                tank_velocity[1] -= 0.01
                tank_direction = 'down'
            elif(event.key == pygame.K_LEFT): #we pressed left (move the map right)
                tank_velocity[0] += 0.01
                tank_direction = 'left'
            elif(event.key == pygame.K_RIGHT): #we pressed right (move the map left)
                tank_velocity[0] -= 0.01
                tank_direction = 'right'

    #update our tank's collision box
    screen_scale = my_arena.get_scale(visible_arena,screen) #get our display's scale

    #draw everything onscreen
    my_arena.draw_arena(visible_arena,tank_arena_position,screen)
    if tank_direction == 'up': #draw the tank
        screen.blit(pygame.transform.scale(T1U, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    elif tank_direction == 'down':
        screen.blit(pygame.transform.scale(T1D, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    elif tank_direction == 'left':
        screen.blit(pygame.transform.scale(T1L, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
    elif tank_direction == 'right':
        screen.blit(pygame.transform.scale(T1R, [my_arena.TILE_SIZE * screen_scale[0],my_arena.TILE_SIZE * screen_scale[1]]), [tank_blit_position[0], tank_blit_position[1]])
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
