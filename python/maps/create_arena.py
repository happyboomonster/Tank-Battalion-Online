##"create_arena.py" ---VERSION 0.03---
## - A program which facilitates creating TBO maps -
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

import pygame, sys, time, math, import_arena #other people's libraries
pygame.init()
screen = pygame.display.set_mode([640,480],pygame.RESIZABLE) #display window
sys.path.append("../libraries")
import arena #my own libraries

#*** Define some data we NEED to make maps ***#

# - Define the tiles used for this arena -
path = "../maps/"
tiles = [pygame.image.load(path + "../../pix/blocks/original_20x20/ground/asphalt.png"), #0
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

tiles_string = '''[pygame.image.load(path + "../../pix/blocks/original_20x20/ground/asphalt.png"), #0
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
        ]'''

# - Define a shuffle pattern for tile images -
shuffle_pattern = [
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

# - Which tiles are smashable, and which order do they smash in? -
bricks = [
    16, #0 hits
    17,
    18,
    19 #3 hits
#       20 #destroyed (but this isn't supposed to be here since it has its own constant)
    ]

# - The destroyed brick tile -
destroyed_brick = 20

# - The blocks we cannot run through -
blocks = [16,17,18,19,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36]

# - Which tiles are flags? -
flags = [37,38,39,40]

#*** End defining crucial data ***#

# - Draws all available tiles in a square 400x400 Pygame surface -
def draw_arena_tiles(selected=0):
    global tiles
    surf = pygame.Surface([400,400])
    tiles_per_dimension = int(math.ceil(math.sqrt(len(tiles))))
    font = pygame.font.Font(None, int(surf.get_width() / tiles_per_dimension / 2))
    for x in range(0,len(tiles)):
        if(selected == x): #number coloring
            color = [255,255,0]
        else:
            color = [255,255,255]
        surf_size = [surf.get_width() / tiles_per_dimension, surf.get_height() / tiles_per_dimension]
        scaled_tile = pygame.transform.scale(tiles[x], [int(surf_size[0]) - 2, int(surf_size[1]) - 2])
        scaled_tile.blit(font.render(str(x), False, color),[3,3])
        xpos = (x % tiles_per_dimension) * surf.get_width() / tiles_per_dimension
        ypos = int(x / tiles_per_dimension) * surf.get_height() / tiles_per_dimension
        surf.blit(scaled_tile, [int(xpos) + 1, int(ypos) + 1])
        pygame.draw.rect(surf, [255,255,255], [int(xpos), int(ypos), int(surf_size[0]), int(surf_size[1])], 1) #draw a white border around each tile
    return surf

def save_arena():
    global my_arena
    global blocks
    global destroyed_brick
    global flags
    global shuffle_pattern
    global tiles_string

    # - Find how many teams are actually in the map -
    flags_found = []
    for x in range(0,len(my_arena.arena[0])):
        for y in range(0,len(my_arena.arena)):
            if(my_arena.arena[y][x] in flags and my_arena.arena[y][x] not in flags_found):
                flags_found.append(my_arena.arena[y][x])
    # - Arrange them in order -
    if(len(flags_found) > 0):
        map_flags = [flags_found[0]]
        for x in range(1,len(flags_found)):
            added = False
            for y in range(0,len(map_flags)):
                if(flags_found[x] < map_flags[y]):
                    added = True
                    map_flags.insert(y, flags_found[x])
                    break
            if(not added):
                map_flags.append(flags_found[x])
    else:
        map_flags = []

    print("\n\n[SAVE OUTPUT]\n\n")
    print("tiles = " + tiles_string)
    print("\nshuffle_pattern = " + str(shuffle_pattern))
    print("\nbricks = " + str(bricks))
    print("\nflags = " + str(map_flags))
    print("\ndestroyed_brick = " + str(destroyed_brick))
    print("\nblocks = " + str(blocks))
    print("\narena = " + str(my_arena.arena))
    print("\n\n[END SAVE OUTPUT] Copy this data into a new .py file, and add an entry for the map into import_arena.py. It should then be utilized by TBO as a regular map.")

def load_arena():
    global my_arena, tiles, tiles_string, shuffle_pattern, blocks, bricks, destroyed_brick, flags, display_surf
    name = input("[LOAD] Please enter the name of the arena you want to load (it must be entered inside import_arena.py to be recognized): ")
    arena_pack = import_arena.return_arena(name, False)
    if(arena_pack == None): #faulty arena name?
        print("[ERROR] No such arena name!")
    else:
        my_arena.arena = arena_pack[0][:]
        tiles = arena_pack[1]
        my_arena.tiles = tiles
        scales = my_arena.get_scale([5,10], pygame.Surface([240,480]))
        my_arena.update_tile_scale([display_surf.get_width(), display_surf.get_height()],
                                scales[0], scales[1], override=True) #make sure the arena begins using the new tile set
        tiles_string = "[NOTICE] Please use the tile set from the map you loaded, rather than copying the tile set from this save output."
        shuffle_pattern = arena_pack[2][:]
        blocks = arena_pack[3][:]
        bricks = arena_pack[4][:]
        destroyed_brick = arena_pack[5]
        flags = arena_pack[6]

# - Create an empty arena (we'll resize it as the player needs) -
my_map = [[0,0],[0,0]]
viewing_location = [0,0] #where are we editing on the map?
modifying_location = [viewing_location[0] + 2, viewing_location[1] + 5]
tile_num = 0
next_tile_num = [] #holds the # keypresses we most recently made in string formats to determine what our next tile_num should be
my_arena = arena.Arena(my_map, tiles, [])

# - Controls list -
help_messages = [
    "CONTROLS:",
    " - Draw: Space",
    " - Add Column, Row: c, r",
    " - Subtract Column, Row: v, t",
    " - Save Map: s",
    " - Load Level: l",
    " - Navigate Map: Arrow Keys",
    " - Switch tile type: Press two number keys",
    " - Inc/Dec movement speed: -/=",
    " - Exit map editor: ESC",
    "Press any key to exit this screen...",
    ]


# - Actual map creation functions:
#[done]   - Saving just prints out map data for use in a .py map file (arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags)
#[done]   - All tiles are displayed onscreen. Numbers are used to select which tile will be drawn, not with the mouse.
#[done]   - The arena does not have Menuhandler() buttons implemented on it, since it needs to be keyboard and mouse-friendly.
#[done]   - A cursor will always be in the middle of the arena, which will place a tile when the space bar is pressed (odd-size arena viewport required).
#[done]   - The window will always retain a constant aspect ratio at 640x480 resolution to avoid aspect ratio display issues.
#[done]   - It is expected that this program is being run on a PC, not a controller-based system. As such, there are no provisions for joystick support.
#[done]   - Keys - and = (unshifted + and _) will increase and decrease the target framerate of this software by 2.5FPS each keypress.
#[done]   - Loading levels (L key)

# - Miscellaneous setup stuff -
pygame.font.init()
font = pygame.font.Font(None, 40)
clock = pygame.time.Clock() #for keeping a constant FPS
display_surf = pygame.Surface([640,480]) #this is where all our rendering actually happens. It gets copied & scaled to "screen" after all rendering is complete.
target_framerate = 10.0 #how many FPS do we WANT? (some functionality is tied to framerate, so it is useful to decrease it sometimes)
keys = [] #holds all keys currently pressed
p1_keys = [] #holds all keys which were depressed THIS frame
press_event = False #tells whether we pressed a key THIS frame
help_msg = True #this tells whether a help message should be displayed.
running = True
while running:
    # - Pygame event loop -
    p1_keys = [] #clear single-press keys list
    for event in pygame.event.get():
        if(event.type == pygame.QUIT): #check for quitting (we also check the ESC key in keys[])
            running = False
        elif(event.type == pygame.KEYDOWN): #update the keys[] list
            if(event.key not in keys):
                press_event = True
                keys.append(event.key)
            if(event.key not in p1_keys):
                press_event = True
                p1_keys.append(event.key)
            if(help_msg == True):
                help_msg = False
        elif(event.type == pygame.KEYUP): #update the keys[] list
            if(event.key in keys):
                keys.remove(event.key)

    # - ALL press dependent checks happen FIRST -
    if(press_event):
        # - Check whether we need to show the help screen -
        if(pygame.K_F1 in p1_keys):
            help_msg = True
        # - Check whether we want a framerate decrease -
        if(pygame.K_MINUS in p1_keys):
            target_framerate -= 2.5
            if(target_framerate < 5): #5FPS min
                target_framerate = 5.0
        # - Check whether we want a framerate increase -
        if(pygame.K_EQUALS in p1_keys):
            target_framerate += 2.5
            if(target_framerate > 30): #some editing functions will be unusable @ 60FPS, so...
                target_framerate = 30.0
        # - Check for number keypresses -
        for x in range(0,10):
            if(x + pygame.K_0 in p1_keys):
                #Number X was just pressed
                next_tile_num.insert(0,str(x))
                if(len(next_tile_num) >= 2): #handle converting next_tile_num to tile_num
                    tile_num = int(next_tile_num[1] + next_tile_num[0])
                    next_tile_num = []
        # - Check for adding columns and rows -
        if(pygame.K_c in p1_keys):
            if(modifying_location[0] >= 0 and modifying_location[0] <= len(my_arena.arena[0])): #we are selecting a valid X coordinate to add a column?
                if(modifying_location[0] == len(my_arena.arena[0])): #we need to append() a new column.
                    for x in range(0,len(my_arena.arena)):
                        my_arena.arena[x].append(tile_num)
                else: #we need to insert() a new column.
                    for x in range(0,len(my_arena.arena)):
                        my_arena.arena[x].insert(modifying_location[0], tile_num)
        if(pygame.K_r in p1_keys):
            if(modifying_location[1] >= 0 and modifying_location[1] <= len(my_arena.arena)): #we are selecting a valid Y coordinate to add a row?
                new_row = [] #prepare a new empty row
                for x in range(0,len(my_arena.arena[0])):
                    new_row.append(tile_num)
                if(modifying_location[1] == len(my_arena.arena)): #we need to append() a new row.
                    my_arena.arena.append(new_row)
                else: #we need to insert() a new row.
                    my_arena.arena.insert(modifying_location[1], new_row)
        # - Check for removing columns and rows -
        if(pygame.K_v in p1_keys):
            if(modifying_location[0] >= 0 and modifying_location[0] < len(my_arena.arena[0])): #we are selecting a valid X coordinate to remove a column?
                if(len(my_arena.arena[0]) > 2): #if the map is less than 3 tiles in size, we are not going to allow the designer to remove another column.
                    for x in range(0,len(my_arena.arena)):
                        my_arena.arena[x].pop(modifying_location[0])
        if(pygame.K_t in p1_keys):
            if(modifying_location[1] >= 0 and modifying_location[1] < len(my_arena.arena)): #we are selecting a valid Y coordinate to remove a row?
                if(len(my_arena.arena) > 2): #if the map is less than 3 tiles in size, we are not going to allow the designer to remove another row.
                    my_arena.arena.pop(modifying_location[1])
        # - Check for whether the designer asked to save the arena -
        if(pygame.K_s in p1_keys):
            save_arena()
        # - Check whether the designer wanted to load a new arena -
        if(pygame.K_l in p1_keys):
            screen.fill([0,0,0])
            pygame.display.set_caption("Please follow the instructions in the terminal the program is running in...")
            pygame.display.flip()
            load_arena()
            pygame.event.clear() #flush out all pygame event requests
            keys = [] #empty the keys[] list as well
        # - Check for single-keypress movement requests -
        if(pygame.K_UP in p1_keys):
            viewing_location[1] -= 1
            if(viewing_location[1] < -8): #the map's almost off-screen!
                viewing_location[1] = -8
        elif(pygame.K_DOWN in p1_keys):
            viewing_location[1] += 1
            if(viewing_location[1] > len(my_arena.arena) - 2): #the map's almost off-screen!
                viewing_location[1] = len(my_arena.arena) - 2
        if(pygame.K_RIGHT in p1_keys):
            viewing_location[0] += 1
            if(viewing_location[0] > len(my_arena.arena[0]) - 2):
                viewing_location[0] = len(my_arena.arena[0]) - 2
        elif(pygame.K_LEFT in p1_keys):
            viewing_location[0] -= 1
            if(viewing_location[0] < -3): #the map's almost off-screen!
                viewing_location[0] = -3
        if(pygame.K_SPACE in p1_keys): #set tile?
            if(modifying_location[0] < len(my_arena.arena[0]) and modifying_location[1] < len(my_arena.arena) and modifying_location[0] >= 0 and modifying_location[1] >= 0): #this is a valid coordinate (no IndexErrors?)
                my_arena.arena[modifying_location[1]][modifying_location[0]] = tile_num

    # - NON press-dependent input checks -
    if(not press_event):
        if(pygame.K_UP in keys):
            viewing_location[1] -= 1
            if(viewing_location[1] < -8): #the map's almost off-screen!
                viewing_location[1] = -8
        elif(pygame.K_DOWN in keys):
            viewing_location[1] += 1
            if(viewing_location[1] > len(my_arena.arena) - 2): #the map's almost off-screen!
                viewing_location[1] = len(my_arena.arena) - 2
        if(pygame.K_RIGHT in keys):
            viewing_location[0] += 1
            if(viewing_location[0] > len(my_arena.arena[0]) - 2):
                viewing_location[0] = len(my_arena.arena[0]) - 2
        elif(pygame.K_LEFT in keys):
            viewing_location[0] -= 1
            if(viewing_location[0] < -3): #the map's almost off-screen!
                viewing_location[0] = -3
    modifying_location = [viewing_location[0] + 2, viewing_location[1] + 5] #update where tiles we choose to modify will actually end up
        
    # - NEXT come the loop speed-based input checks -
    # - Check if we intended to quit with the ESC key -
    if(pygame.K_ESCAPE in keys):
        running = False
    if(pygame.K_SPACE in keys): #set tile?
        if(modifying_location[0] < len(my_arena.arena[0]) and modifying_location[1] < len(my_arena.arena) and modifying_location[0] >= 0 and modifying_location[1] >= 0): #this is a valid coordinate (no IndexErrors?)
            my_arena.arena[modifying_location[1]][modifying_location[0]] = tile_num

    # - Draw things on our display_surf -
    display_surf.fill([0,0,0]) #clean our slate to start...
    screen.fill([0,0,0])
    display_surf.blit(draw_arena_tiles(tile_num),[0,40]) #draw the tiles available to us
    arena_surf = pygame.Surface([240 * 4,480 * 4]) #draw our arena (I quadruple our resolution because arena tiles get drawn significantly clearer at higher resolutions; artifacting at the bottom and right edges occurs otherwise)
    my_arena.draw_arena([5,10],viewing_location,arena_surf)
    display_surf.blit(pygame.transform.scale(arena_surf,[240,480]), [400,0])
    help_text = font.render("Press F1 for help...",False,[255,255,255]) #this message stays in the bottom-right corner of the screen UNLESS help_msg == True.
    tiles_text = font.render("Tiles",False,[255,255,255]) #label our tile space
    next_tile_str = "" #draw the numbers we've typed in to switch to a new tile
    for x in range(0,len(next_tile_num)):
        next_tile_str += next_tile_num[len(next_tile_num) - 1 - x]
    next_tile_text = font.render("Next Tile: " + next_tile_str, False, [255,255,255])
    arena_text = font.render("Arena: (" + str(modifying_location[0]) + "," + str(modifying_location[1]) + ")",False,[255,255,255]) #label our arena space
    tiles_text_pos = 400 / 2 - tiles_text.get_width() / 2
    display_surf.blit(tiles_text, [int(tiles_text_pos),0]) #label our tile space
    arena_text_pos = 400 + 240 / 2 - arena_text.get_width() / 2
    display_surf.blit(arena_text, [int(arena_text_pos),0]) #label our arena space
    next_tile_text_pos = 400 / 2 - next_tile_text.get_width() / 2
    display_surf.blit(next_tile_text, [int(next_tile_text_pos),480 - next_tile_text.get_height()])
    if(help_msg != True):
        help_text = pygame.transform.scale(help_text, [int(help_text.get_width() * 2/3), int(help_text.get_height() * 2/3)])
        display_surf.blit(help_text, [display_surf.get_width() - help_text.get_width(), display_surf.get_height() - help_text.get_height()])
    pygame.draw.line(display_surf, [255,255,255], [400,0], [400,480], 3) #draw a dividing line between our arena and tile space
    pygame.draw.rect(display_surf, [255,255,255], [400 + 96 - 2,240 - 2,48 + 4,48 + 4], 3) #draw a cursor around the currently selected arena tile
    pygame.draw.rect(display_surf, [255,255,255], [0, 0, 640, 480], 3) #draw a border around our actual display space
    if(help_msg == True): #display help screen ontop of everything else
        display_surf.fill([0,0,0])
        help_surf = pygame.Surface([640, 40 * len(help_messages)])
        for x in range(0,len(help_messages)):
            help_text_surf = font.render(help_messages[x],False,[255,255,255])
            help_surf.blit(help_text_surf, [0, 40 * x])
        pos = [
            (display_surf.get_width() - help_surf.get_width()) / 2,
            (display_surf.get_height() - help_surf.get_height()) / 2
            ]
        display_surf.blit(help_surf, [int(pos[0]), int(pos[1])])

    # - Draw our display_surf onto our screen -
    scales = [screen.get_width() / display_surf.get_width(), screen.get_height() / display_surf.get_height()]
    if(scales[0] > scales[1]): #scale based on the Y size difference
        screen_scale = scales[1]
    else: #scale based on the X size difference
        screen_scale = scales[0]
    display_size = [display_surf.get_width() * screen_scale, display_surf.get_height() * screen_scale]
    display_offset = [(screen.get_width() - display_size[0]) / 2, (screen.get_height() - display_size[1]) / 2]
    scaled_surf = pygame.transform.scale(display_surf, [int(display_size[0]), int(display_size[1])])
    screen.blit(scaled_surf, [int(display_offset[0]), int(display_offset[1])])
    pygame.display.flip()

    # - Keep a constant framerate, and get our FPS stats -
    clock.tick(int(target_framerate))
    pygame.display.set_caption("TBO Map Editor - Target FPS: " + str(round(target_framerate,1)) + "; FPS: " + str(round(clock.get_fps(),1)))

    # - Reset press_event -
    press_event = False

# - Close the pygame window -
pygame.quit()
