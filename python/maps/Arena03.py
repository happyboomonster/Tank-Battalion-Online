##"Arena03.py" - A goofy little map meant for no more than 8 players
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

import pygame

ARENA_NAME = "Arena03"

def get_arena(path=""):
    # - Define the tiles used for this arena -
    tiles = [pygame.image.load(path + "../../pix/blocks/ground/asphalt.png"), #0
            pygame.image.load(path + "../../pix/blocks/ground/forest.png"),
            pygame.image.load(path + "../../pix/blocks/ground/grass.png"), #2
            pygame.image.load(path + "../../pix/blocks/ground/dirt.png"),
            pygame.image.load(path + "../../pix/blocks/ground/cement.png"),
            pygame.image.load(path + "../../pix/blocks/ground/water-1.png"), #5
            pygame.image.load(path + "../../pix/blocks/ground/water-2.png"),
            pygame.image.load(path + "../../pix/blocks/ground/water-3.png"),
            pygame.image.load(path + "../../pix/blocks/ground/water-4.png"), #8
            pygame.image.load(path + "../../pix/blocks/brick/brick0h.png"), #9
            pygame.image.load(path + "../../pix/blocks/brick/brick1h.png"),
            pygame.image.load(path + "../../pix/blocks/brick/brick2h.png"), #11
            pygame.image.load(path + "../../pix/blocks/brick/brick3h.png"),
            pygame.image.load(path + "../../pix/blocks/brick/brick_destroyed.png"), #13
            pygame.image.load(path + "../../pix/blocks/wall/wall.png"), #14
            pygame.image.load(path + "../../pix/blocks/wall/wall-edge/wall-edge-top.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-edge/wall-edge-bottom.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-edge/wall-edge-left.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-edge/wall-edge-right.png"), #18
            pygame.image.load(path + "../../pix/blocks/wall/wall-double-edge/wall-double-edge-horizontal.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-double-edge/wall-double-edge-vertical.png"), #20
            pygame.image.load(path + "../../pix/blocks/wall/wall-corner/wall-corner-top-right.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-corner/wall-corner-bottom-right.png"), #22
            pygame.image.load(path + "../../pix/blocks/wall/wall-corner/wall-corner-bottom-left.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-corner/wall-corner-top-left.png"), #24
            pygame.image.load(path + "../../pix/blocks/wall/wall-peninsula/wall-peninsula-top.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-peninsula/wall-peninsula-bottom.png"), #26
            pygame.image.load(path + "../../pix/blocks/wall/wall-peninsula/wall-peninsula-left.png"),
            pygame.image.load(path + "../../pix/blocks/wall/wall-peninsula/wall-peninsula-right.png"), #28
            pygame.image.load(path + "../../pix/blocks/wall/wall-island.png"), #29
            pygame.image.load(path + "../../pix/fortresses/team-blue.png"), #30
            pygame.image.load(path + "../../pix/fortresses/team-green.png"), #31
            pygame.image.load(path + "../../pix/fortresses/team-red.png"), #32
            pygame.image.load(path + "../../pix/fortresses/team-yellow.png") #33
             ]

    # - Define a shuffle pattern for tile images -
    shuffle_pattern = [
        [5,6],
        [6,7],
        [7,8],
        [8,5],
        ]

    # - Which tiles are smashable, and which order do they smash in? -
    bricks = [
        9,
        10,
        11,
        12
        ]

    # - Which tiles are flags? -
    flags = [30,31,32,33]

    # - The destroyed brick tile -
    destroyed_brick = 13

    # - The blocks we cannot run through (needs to be implemented inside import_arena) -
    blocks = []
    for x in range(9,30):
        blocks.append(x)
    blocks.remove(13) #destroyed bricks can be driven through!

    # - Define the arena -
    arena = [ #size 7x10 (y,x)
         [24,19,19,19,19,19,19,19,19,21],
         [20,30, 9, 0, 0,12, 0,11,31,20],
         [20,11,29, 0, 0,25, 0,29, 9,20],
         [20, 0, 0,12,24,22,12, 0, 0,20],
         [20, 9,29, 0,26, 0, 0,29,11,20],
         [20,33,11, 0,12, 0, 0, 9,32,20],
         [23,19,19,19,19,19,19,19,19,22]
         ]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
