##"t4_Arena03.py" ---VERSION 0.01---
## - 529-block 4-team TBO arena -
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

import pygame

ARENA_NAME = "t4_Arena03"

def get_arena(path="", convert=False):
    # - Define the tiles used for this arena -
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

    # - Convert all images IF we requested them to be converted -
    if(convert):
        for x in range(0,len(tiles)):
            tiles[x] = tiles[x].convert()

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
        ]

    # - The destroyed brick tile -
    destroyed_brick = 20

    # - The blocks we cannot run through (needs to be implemented inside import_arena) -
    blocks = [16,17,18,19,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36]

    # - Which tiles are flags? -
    flags = [37,38,39,40]

    # - Define the arena -
    arena = [[31, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [27, 11, 11, 11, 19, 10, 2, 2, 6, 7, 7, 3, 4, 8, 10, 11, 11, 11, 19, 10, 10, 10, 27], [27, 11, 16, 11, 16, 10, 36, 6, 32, 3, 34, 22, 35, 4, 32, 11, 36, 11, 16, 10, 16, 10, 27], [27, 11, 11, 11, 10, 10, 5, 1, 27, 7, 4, 27, 5, 5, 27, 11, 11, 11, 10, 10, 10, 10, 27], [27, 19, 16, 10, 36, 10, 5, 34, 23, 35, 4, 27, 1, 34, 23, 35, 10, 10, 36, 10, 16, 19, 27], [27, 10, 10, 10, 10, 36, 10, 10, 10, 10, 10, 27, 10, 10, 10, 6, 2, 36, 10, 10, 10, 10, 27], [27, 5, 36, 6, 2, 10, 18, 10, 10, 19, 10, 27, 10, 19, 10, 5, 18, 11, 11, 11, 36, 10, 27], [27, 5, 1, 6, 32, 10, 10, 36, 10, 10, 10, 27, 10, 10, 10, 36, 10, 11, 32, 11, 11, 11, 27], [27, 6, 34, 26, 25, 10, 10, 10, 36, 10, 10, 27, 10, 10, 36, 10, 10, 11, 24, 26, 35, 11, 27], [27, 2, 2, 7, 33, 10, 19, 10, 10, 9, 9, 27, 9, 9, 10, 10, 19, 11, 33, 11, 11, 11, 27], [27, 7, 32, 7, 3, 10, 10, 10, 10, 9, 37, 27, 38, 9, 10, 10, 10, 11, 11, 11, 32, 10, 27], [27, 7, 24, 26, 26, 26, 26, 26, 26, 26, 26, 21, 26, 26, 26, 26, 26, 26, 26, 26, 25, 5, 27], [27, 3, 33, 5, 5, 10, 10, 10, 10, 9, 39, 27, 40, 9, 10, 10, 10, 10, 3, 6, 33, 1, 27], [27, 4, 4, 8, 32, 10, 19, 10, 10, 9, 9, 27, 9, 9, 10, 10, 19, 10, 32, 6, 2, 5, 27], [27, 8, 34, 26, 25, 10, 10, 10, 36, 10, 10, 27, 10, 10, 36, 10, 10, 10, 24, 26, 35, 6, 27], [27, 8, 1, 5, 33, 10, 10, 36, 10, 10, 10, 27, 10, 10, 10, 36, 10, 10, 33, 3, 2, 6, 27], [27, 1, 36, 5, 2, 10, 18, 10, 10, 19, 10, 27, 10, 19, 10, 10, 18, 10, 3, 7, 36, 2, 27], [27, 10, 10, 10, 10, 36, 10, 10, 10, 10, 10, 27, 10, 10, 10, 10, 10, 36, 10, 10, 10, 10, 27], [27, 19, 16, 10, 36, 10, 5, 34, 22, 35, 8, 27, 5, 34, 22, 35, 2, 10, 36, 10, 16, 19, 27], [27, 11, 11, 11, 10, 10, 5, 1, 27, 7, 8, 27, 1, 5, 27, 1, 6, 10, 10, 11, 11, 11, 27], [27, 11, 16, 11, 16, 10, 36, 6, 33, 3, 34, 23, 35, 4, 33, 5, 36, 10, 16, 11, 16, 11, 27], [27, 11, 11, 11, 19, 10, 6, 2, 2, 7, 7, 3, 8, 4, 8, 5, 1, 10, 19, 11, 11, 11, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
