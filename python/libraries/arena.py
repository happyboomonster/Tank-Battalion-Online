##"arena.py" library ---VERSION 0.21---
## - For drawing (and manipulating) maps within Tank Battalion Online -
##Copyright (C) 2023  Lincoln V.
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

import pygame
import time
import _thread

#path to images: ../.. (brings into main directory)
#                   /pix/blocks/ground
#                   / (images in this directory)
#                   File names: asphalt.png, cement.png, dirt.png, forest.png
#                               grass.png, water-1.png, water-2.png,
#                               water-3.png, water-4.png;

class Arena():
    def __init__(self,initial_map,tiles,shuffle_patterns): #pass this class the initial map, and the tiles to draw the map.
        self.TILE_SIZE = 20 #constant which tells how large (in pixels) our tiles are
        self.arena = initial_map[:] #holds the full arena
        self.tiles = tiles[:] #the tiles which make the arena
        self.stretch = True #should we stretch the arena to draw it on our screen without any clipping?

        #    --- Tile SCALING stuff ---
        self.scaled_tiles = tiles[:]
        self.last_screen_size = [-1,-1] #whenever the screen size does not equal this, the tiles need to be rescaled.

        #    --- Tile Shuffling stuff ---
        self.shuffle_speed = 4 #times per second we shuffle tiles (will not be quite exact)
        self.old_time = 0 #when we last shuffled tiles
        self.shuffle_patterns = shuffle_patterns[:] #format: [[tile#,new_tile#],[tile#,new_tile#]]

        #    --- Collision stuff ---
        #    This constant is how far a tile can be collided with another tile before the collision
        #  is simply labeled as "center" as opposed to "left", "right" or some other direction.
        self.EDGE_OFFSET = 4 / self.TILE_SIZE
        self.offscreen_arena = [0.0, 0.0] #how many tiles of arena are offscreen to either our LEFT or TOP?

        #    --- AI stuff ---
        self.flag_locations = [] #this holds the location of all flags in the game

        #    --- Multithreading stuff ---
        self.lock = _thread.allocate_lock()

    def set_flag_locations(self,flag_numbers): #pass the tile numbers of all flags in the map, and the arena will find them for you.
        for f in range(0,len(flag_numbers)):
            flag_found = False
            for y in range(0,len(self.arena)):
                for x in range(0,len(self.arena[0])):
                    if(self.arena[y][x] == flag_numbers[f]):
                        self.flag_locations.append([x, y])
                        flag_found = True
                        break
            if(flag_found == False):
                self.flag_locations.append(None)

    def update_tile_scale(self, screen_dimensions, scale_x, scale_y): #updates the scaled tiles we use to draw our screen more quickly than scaling EVERY frame
        if(screen_dimensions[0] != self.last_screen_size[0] or screen_dimensions[1] != self.last_screen_size[1]):
            self.last_screen_size = screen_dimensions[:] #update our last_screen_size to reflect the fact that we updated our texture scale
            for x in range(0,len(self.tiles)):
                scaled_tile = pygame.transform.scale(self.tiles[x],[int(self.TILE_SIZE * scale_x), int(self.TILE_SIZE * scale_y)])
                self.scaled_tiles[x] = scaled_tile

    def shuffle_tiles(self): #if we set any tiles to be shuffled, let's do it here...
        if(self.old_time + 1 / self.shuffle_speed < time.time()): #have we hit another time to shuffle tiles?
            self.old_time = time.time() #reset our timer
            for y in range(0,len(self.arena)): #shuffle all the arena tiles
                for x in range(0,len(self.arena[0])):
                    for shuffle in range(0,len(self.shuffle_patterns)):
                        if(self.arena[y][x] == self.shuffle_patterns[shuffle][0]): #do we need to change this arena tile?
                            self.arena[y][x] = self.shuffle_patterns[shuffle][1]
                            break #exit this loop

    #this function lets you modify a group of tiles in the arena, based on their type and when they occur in the arena.
    #For example, if we wanted to replace a bunch of water blocks, you'd pass new_tiles like so:
    #[ [water_tile_pos,new_tile#], [water_tile_pos,new_tile#], [water_tile_pos,new_tile#] ]
    def modify_tiles(self,new_tiles):
        for x in range(0,len(new_tiles)): #find all tiles we need to change, and apply the change.
            self.arena[new_tiles[x][0][1]][new_tiles[x][0][0]] = new_tiles[x][1]

    #checks if a tile has collided with an EDGE of another tile. if not, just returns the tile ID and the word "center".
    #player tile format: [list of 4 coords (x,y,x2,y2) ] ***USES MAP COORDS, NOT PIXEL COORDS OF ANY SORT***
    def check_edge_collision(self,tile,player_tile): #tile format: [ID#, tile coords (len of 4)]
        #    --- define all the collision boxes for our tile's edges ---
        left_edge = [tile[1][0], tile[1][0] + self.EDGE_OFFSET]
        right_edge = [tile[1][2] - self.EDGE_OFFSET, tile[1][2]]
        top_edge = [tile[1][1], tile[1][1] + self.EDGE_OFFSET]
        bottom_edge = [tile[1][3] - self.EDGE_OFFSET, tile[1][3]]

        if(player_tile[0] < left_edge[1] and player_tile[2] > left_edge[0]): #we collided with the left edge...
            collision_type = 'left'
        elif(player_tile[0] < right_edge[1] and player_tile[2] > right_edge[0]): #we collided with the right edge...
            collision_type = 'right'
        elif(player_tile[1] < top_edge[1] and player_tile[3] > top_edge[0]): #we collided with the top edge...
            collision_type = 'top'
        elif(player_tile[1] < bottom_edge[1] and player_tile[3] > bottom_edge[0]): #we collided with the bottom edge...
            collision_type = 'bottom'
        else:
            collision_type = 'center'
        return [tile[0], collision_type] #return the block ID#, along with the collision type (direction).

    def get_scale(self,tile_viewport,screen): #returns the scale of both X and Y axes of our screen
        #    --- Find our screen's scale ---
        screen_dimensions = [screen.get_width(), screen.get_height()] #get our screen dimensions
        size_arena_x = (2 + tile_viewport[0]) * self.TILE_SIZE #find out our partial arena size's dimensions
        size_arena_y = (2 + tile_viewport[1]) * self.TILE_SIZE
        if(self.stretch == True): #we're gonna stretch our screen?
            #Decrementing size_arena by TILE_SIZE is just something we do to avoid collision + visual bugs
            scale_x = screen_dimensions[0] / (size_arena_x - 2 * self.TILE_SIZE)
            scale_y = screen_dimensions[1] / (size_arena_y - 2 * self.TILE_SIZE)
        else: #we're gonna use clipping to fill the screen with collision boxes instead of warping anything
            scale_x = screen_dimensions[0] / (size_arena_x - 2 * self.TILE_SIZE)
            scale_y = screen_dimensions[1] / (size_arena_y - 2 * self.TILE_SIZE)
            if(scale_x > scale_y): #set our scales to the same multiplier, whichever is larger
                scale_y = scale_x
            else:
                scale_x = scale_y
        return [scale_x,scale_y] #return our screen scales
    
    #checks collision with a moving tile (e.g. a TILE_SIZE x TILE_SIZE player).
    #assumes player_pos is in MAP COORDINATES, NOT PIXEL COORDINATES!
    def check_collision(self,tile_viewport,offset,player_pos):
        collision_boxes = self.get_collision_boxes(tile_viewport, offset) #start by getting nearby collision boxes
        collided_blocks = [] #list of blocks we bumped into...
        for x in range(0,len(collision_boxes)): #now we check if we've touched any of the boxes!
            if(player_pos[0] < collision_boxes[x][1][2]): #checking if we collided with this collision box in the X axis
                if(player_pos[2] > collision_boxes[x][1][0]): #checking X axis collision
                    if(player_pos[1] < collision_boxes[x][1][3]): #checking Y axis collision
                        if(player_pos[3] > collision_boxes[x][1][1]): #checking Y axis collision
                            #collision has happened! Now we check to see whether the collision is on an edge or not.
                            collision_data = self.check_edge_collision(collision_boxes[x],player_pos)
                            collision_data.append(collision_boxes[x][2]) #we need XY arena data here!
                            collided_blocks.append(collision_data[:])
        return collided_blocks #return our collision data - Format: [ [block#, collision direction, position], [block#, collision direction, position]... ]

    #grabs the collision coordinates for everything onscreen; returns them in map coordinates (1 = 1 tile, not 1 pixel).
    def get_collision_boxes(self,tile_viewport,offset): #this new method of doing this just seems a little too easy...
        collision_boxes = []
        offset = [int(offset[0]), int(offset[1])] #"intify" offset
        for y in range(offset[1],offset[1] + tile_viewport[1]): #iterate through all Y squares we want to check
            for x in range(offset[0], offset[0] + tile_viewport[0]): #iterate through all X squares we want to check
                #[new_arena[y][x],scaled_coordinates, [list_offset[0] + x, list_offset[1] + y]]
                #(tile ID#, coordinates, [arena x, arena y position])
                box_coords = [x, y, x + 1, y + 1]
                try:
                    collision_boxes.append([self.arena[y][x], box_coords[:], [x, y]])
                except IndexError: #if we're checking collision off the sides of the map, well...just ignore it.
                    pass
        return collision_boxes #return all the squares of collision we found!

    def draw_arena(self,tile_viewport,offset,screen): #offset is in tiles
        # - Set up screen dimension stuff -
        screen_dimensions = [screen.get_width(), screen.get_height()] #get our screen dimensions
        size_arena_x = tile_viewport[0] * self.TILE_SIZE #find out the size of the partial arena we are going to draw
        size_arena_y = tile_viewport[1] * self.TILE_SIZE
        #    --- Try to handle stretching our screen ---
        if(self.stretch == True): #we're gonna stretch our screen?
            #Decrementing size_arena by TILE_SIZE is to avoid a very bad visual glitch
            scale_x = screen_dimensions[0] / (size_arena_x)
            scale_y = screen_dimensions[1] / (size_arena_y)
        else: #we're gonna use clipping to fill the screen instead without warping anything
            scale_x = screen_dimensions[0] / (size_arena_x)
            scale_y = screen_dimensions[1] / (size_arena_y)
            if(scale_x > scale_y): #set our scales to the same multiplier, whichever is larger
                scale_y = scale_x
            else:
                scale_x = scale_y
        #    --- Update our tile scale ---
        self.update_tile_scale(screen_dimensions, scale_x, scale_y)
        #    --- change our offset to between -/+1 rather than ranging anywhere ---
        final_offset = [-(offset[0] - int(offset[0])), -(offset[1] - int(offset[1]))]
        # - Draw our partial map -
        for pre_y in range(int(offset[1]) - 1, int(offset[1]) + 1 + tile_viewport[1]): #iterate through all our rows of arena we need to draw
            for pre_x in range(int(offset[0]) - 1, int(offset[0]) + 1 + tile_viewport[0]): #iterate through all individual arena squares we need to draw
                y = pre_y - int(offset[1])
                x = pre_x - int(offset[0])
                #check if drawing this square would be offscreen on the X axis
                if(x * self.TILE_SIZE * scale_x + (final_offset[0] * self.TILE_SIZE * scale_x) > screen_dimensions[0] or x * self.TILE_SIZE * scale_x + (final_offset[0] * self.TILE_SIZE * scale_x) < -(self.TILE_SIZE * scale_x)):
                    continue #skip drawing this because it will be offscreen on the X axis
                #check if drawing this tile would be offscreen on the Y axis
                elif(y * self.TILE_SIZE * scale_y + (final_offset[1] * self.TILE_SIZE * scale_y) > screen_dimensions[1] or y * self.TILE_SIZE * scale_y + (final_offset[1] * self.TILE_SIZE * scale_y) < -(self.TILE_SIZE * scale_y)):
                    continue #skip drawing this because it will be offscreen on the Y axis
                else:
                    try:
                        if(self.arena[pre_y][pre_x] == None or pre_y < 0 or pre_x < 0): #is there no arena data for this index? (negative indexes give mirror images of the map, which annoys me a lot)
                            continue #just skip it...
                        screen.blit(self.scaled_tiles[self.arena[pre_y][pre_x]], [int(x * self.TILE_SIZE * scale_x + (final_offset[0] * self.TILE_SIZE * scale_x)), int(y * self.TILE_SIZE * scale_y + (final_offset[1] * self.TILE_SIZE * scale_y))])
                    except IndexError: #sometimes we try to draw beyond our arena boundaries. If so, we just don't try to draw that tile.
                        pass

    # - Returns a pygame Surface() object where 1 px represents 1 block -
    def draw_minimap(self, collideable_tiles):
        minimap = pygame.Surface([len(self.arena[0]),len(self.arena)])
        for y in range(0,len(self.arena)):
            for x in range(0,len(self.arena[0])):
                if(self.arena[y][x] in collideable_tiles):
                    minimap.set_at([x,y],[0,0,0]) #black for a wall
                else:
                    minimap.set_at([x,y],[255,255,255]) #white for open space
        return minimap

###NOT so quick demo; Display some blocks on a resizable window and scrolls them at your will (use the arrow keys). Also displays a minimap in the corner of the screen.
##
###create a pygame screen
##screen = pygame.display.set_mode([100,100], pygame.RESIZABLE)
##
###our arena map we will be drawing
##my_map = [[ 5, 6, 1, 2, 0, 0, 1, 2, 0, 0, 1, 2],
##          [ 8, 7, 2, 1, 0, 0, 2, 1, 0, 0, 2, 1],
##          [ 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3],
##          [ 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3],
##          [ 5, 6, 7, 8, 0, 0, 1, 2, 0, 8, 7, 6],
##          [ 0, 0, 2, 7, 0, 0, 2, 5, 6, 7, 2, 1],
##          [ 4, 4, 3, 6, 5, 6, 3, 6, 4, 4, 3, 3],
##          [ 4, 4, 3, 3, 4, 7, 8, 7, 4, 4, 3, 3],
##          [ 0, 0, 1, 2, 0, 0, 1, 2, 0, 0, 1, 2],
##          [ 0, 0, 2, 1, 0, 0, 2, 1, 0, 0, 2, 1],
##          [ 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3],
##          [ 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3]]
##
##collideable_tiles = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29]
##
###all the tiles we can draw in the arena
##my_tiles = [pygame.image.load("../../pix/blocks/ground/asphalt.png"), #0
##            pygame.image.load("../../pix/blocks/ground/forest.png"),
##            pygame.image.load("../../pix/blocks/ground/grass.png"),
##            pygame.image.load("../../pix/blocks/ground/dirt.png"),
##            pygame.image.load("../../pix/blocks/ground/cement.png"),
##            pygame.image.load("../../pix/blocks/ground/water-1.png"), #5
##            pygame.image.load("../../pix/blocks/ground/water-2.png"),
##            pygame.image.load("../../pix/blocks/ground/water-3.png"),
##            pygame.image.load("../../pix/blocks/ground/water-4.png"), #8
##            pygame.image.load("../../pix/blocks/brick/brick0h.png"), #9
##            pygame.image.load("../../pix/blocks/brick/brick1h.png"),
##            pygame.image.load("../../pix/blocks/brick/brick2h.png"),
##            pygame.image.load("../../pix/blocks/brick/brick3h.png"),
##            pygame.image.load("../../pix/blocks/brick/brick_destroyed.png"), #13
##            pygame.image.load("../../pix/blocks/wall/wall.png"), #14
##            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-top.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-bottom.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-left.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-edge/wall-edge-right.png"), #18
##            pygame.image.load("../../pix/blocks/wall/wall-double-edge/wall-double-edge-horizontal.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-double-edge/wall-double-edge-vertical.png"), #20
##            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-top-right.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-bottom-right.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-bottom-left.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-corner/wall-corner-top-left.png"), #24
##            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-top.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-bottom.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-left.png"),
##            pygame.image.load("../../pix/blocks/wall/wall-peninsula/wall-peninsula-right.png"), #28
##            pygame.image.load("../../pix/blocks/wall/wall-island.png")] #29
##
###define our tile shuffle system
##my_shuffle = [[5,6],
##              [6,7],
##              [7,8],
##              [8,5]]
##
###create an arena
##my_arena = Arena(my_map, my_tiles, my_shuffle)
##
###whether to stretch the arena to fit the screen
##my_arena.stretch = True
##
###set a key repeat
##pygame.key.set_repeat(2,2)
##
###variables used within the loop
##x = 0
##y = 0
##running = True
##
##while running:
##    #shift over the arena we're drawing a bit (uncomment this for this to work)
##    #if X is not greater than the length of the X axis of our arena * my_arena.TILE_SIZE
##    #if(x / my_arena.TILE_SIZE < len(my_map[0])):
##    #    x += 0.1 #then increment X to continue scrolling the arena!
##    #else: #else reset X to 0
##    #    x = 0
##
##    #test out modify_tiles()
##    #if(int(x%2) == 0):
##    #    my_arena.modify_tiles([[[5,5],9]])
##    #else:
##    #    my_arena.modify_tiles([[[5,5],0]])
##
##    #draw the arena
##    my_arena.shuffle_tiles()
##    my_arena.draw_arena([6,6],[x,y],screen)
##    screen.blit(my_arena.draw_minimap(collideable_tiles), [0,0])
##    pygame.display.flip() #update the display
##    screen.fill([0,0,0]) #clear the display for next frame
##
##    #make sure we can exit this demo
##    for event in pygame.event.get():
##        if(event.type == pygame.QUIT):
##            running = False
##        elif(event.type == pygame.KEYDOWN): #use the arrow keys to move the map around!
##            if(event.key == pygame.K_UP):
##                y += 0.01
##            elif(event.key == pygame.K_DOWN):
##                y -= 0.01
##            elif(event.key == pygame.K_LEFT):
##                x += 0.01
##            elif(event.key == pygame.K_RIGHT):
##                x -= 0.01
##
##pygame.quit()
