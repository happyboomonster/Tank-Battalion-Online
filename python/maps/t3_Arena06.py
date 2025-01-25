##"t3_Arena06.py" ---VERSION 0.01---
## - Three-team battlefield for TBO -
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

ARENA_NAME = "t3_Arena06"

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
    flags = [37,38,39]

    # - Define the arena -
    arena = [[31, 26, 26, 22, 26, 26, 26, 26, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [27, 0, 0, 33, 0, 0, 0, 0, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 0, 16, 3, 7, 10, 10, 27], [27, 0, 7, 7, 0, 0, 0, 36, 4, 32, 0, 33, 0, 32, 0, 33, 0, 32, 0, 33, 0, 32, 0, 33, 0, 32, 0, 32, 0, 33, 0, 32, 0, 33, 0, 32, 0, 33, 0, 32, 0, 33, 0, 31, 35, 0, 4, 7, 36, 11, 10, 27], [27, 0, 8, 8, 3, 7, 36, 8, 8, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 27, 0, 0, 19, 36, 11, 11, 11, 27], [27, 0, 34, 35, 7, 36, 5, 9, 16, 30, 26, 26, 26, 23, 26, 26, 26, 21, 26, 26, 26, 23, 26, 26, 26, 25, 0, 30, 26, 22, 26, 23, 26, 26, 22, 23, 26, 26, 26, 23, 26, 26, 26, 29, 0, 0, 19, 10, 11, 19, 11, 27], [27, 0, 0, 0, 8, 4, 5, 7, 36, 10, 11, 11, 11, 11, 11, 11, 11, 27, 5, 8, 0, 0, 0, 0, 0, 33, 0, 7, 5, 33, 2, 6, 9, 10, 27, 2, 6, 7, 18, 0, 0, 0, 0, 0, 0, 0, 19, 11, 11, 19, 11, 27], [27, 5, 36, 0, 0, 8, 5, 36, 10, 10, 36, 10, 34, 35, 19, 32, 10, 27, 6, 16, 0, 34, 35, 7, 6, 6, 7, 19, 4, 3, 7, 18, 10, 11, 27, 2, 36, 6, 7, 0, 36, 3, 6, 6, 36, 10, 11, 11, 19, 19, 11, 27], [27, 9, 9, 0, 0, 36, 2, 2, 8, 36, 9, 9, 19, 5, 5, 27, 10, 27, 0, 0, 0, 8, 3, 7, 34, 35, 4, 19, 8, 7, 36, 11, 11, 11, 27, 7, 7, 36, 7, 0, 0, 36, 7, 36, 9, 10, 19, 11, 11, 19, 11, 27], [27, 9, 36, 9, 0, 0, 36, 2, 7, 7, 6, 9, 32, 6, 2, 33, 9, 27, 0, 36, 16, 34, 35, 6, 1, 18, 8, 19, 9, 36, 10, 11, 16, 11, 27, 7, 4, 8, 36, 7, 0, 0, 19, 8, 9, 19, 19, 19, 11, 11, 11, 27], [27, 10, 9, 36, 9, 0, 0, 19, 7, 2, 36, 7, 27, 3, 7, 19, 9, 27, 0, 8, 7, 1, 1, 6, 6, 32, 8, 9, 9, 10, 10, 11, 11, 11, 27, 6, 32, 4, 5, 36, 7, 0, 0, 36, 6, 2, 19, 10, 10, 36, 10, 27], [27, 10, 10, 9, 36, 5, 0, 0, 36, 6, 7, 8, 33, 19, 34, 35, 9, 27, 0, 34, 26, 35, 19, 34, 26, 23, 26, 26, 35, 19, 34, 26, 35, 10, 27, 5, 24, 35, 5, 3, 19, 8, 0, 0, 36, 2, 5, 9, 36, 9, 9, 27], [24, 35, 10, 9, 8, 19, 5, 0, 37, 36, 7, 4, 1, 6, 2, 6, 5, 27, 0, 0, 0, 0, 0, 0, 0, 38, 5, 1, 1, 6, 6, 9, 9, 10, 27, 4, 33, 6, 6, 36, 11, 36, 8, 39, 8, 36, 5, 36, 5, 6, 9, 27], [27, 11, 11, 17, 8, 5, 36, 8, 7, 8, 36, 4, 1, 36, 18, 36, 5, 27, 10, 34, 26, 35, 19, 34, 26, 22, 26, 26, 35, 19, 34, 26, 35, 9, 27, 4, 3, 6, 36, 11, 11, 11, 36, 0, 0, 5, 19, 5, 3, 36, 6, 27], [27, 11, 11, 11, 36, 9, 9, 36, 0, 0, 7, 19, 6, 6, 18, 18, 1, 27, 11, 11, 11, 11, 11, 10, 10, 33, 5, 5, 5, 6, 6, 1, 7, 7, 27, 8, 7, 36, 11, 11, 32, 11, 11, 36, 0, 0, 5, 36, 8, 4, 8, 27], [27, 11, 36, 11, 11, 17, 10, 9, 36, 0, 0, 7, 36, 2, 7, 36, 1, 27, 16, 11, 16, 11, 36, 10, 10, 9, 9, 32, 1, 36, 6, 9, 34, 26, 25, 7, 36, 11, 11, 34, 21, 35, 11, 11, 19, 0, 0, 5, 36, 3, 7, 27], [27, 11, 11, 11, 11, 11, 10, 10, 10, 36, 0, 0, 6, 36, 7, 7, 1, 27, 16, 11, 11, 10, 10, 36, 10, 36, 18, 27, 8, 4, 19, 9, 9, 10, 27, 9, 10, 10, 11, 11, 33, 11, 11, 36, 2, 36, 0, 0, 6, 36, 7, 27], [27, 10, 34, 35, 10, 16, 10, 32, 10, 10, 36, 0, 0, 6, 36, 8, 8, 27, 11, 11, 36, 10, 10, 10, 11, 11, 11, 33, 8, 1, 7, 17, 10, 10, 24, 35, 9, 34, 28, 11, 11, 11, 36, 6, 6, 1, 36, 0, 0, 6, 2, 27], [27, 9, 9, 9, 9, 9, 9, 33, 11, 11, 11, 36, 0, 0, 5, 32, 8, 27, 11, 36, 10, 10, 36, 11, 11, 36, 11, 19, 7, 36, 2, 7, 36, 11, 27, 5, 9, 9, 33, 10, 11, 18, 7, 7, 36, 5, 5, 36, 0, 34, 26, 25], [24, 26, 35, 5, 5, 32, 8, 19, 11, 32, 11, 11, 36, 0, 0, 27, 5, 27, 10, 10, 10, 10, 10, 11, 36, 11, 11, 32, 1, 6, 6, 19, 11, 11, 27, 5, 32, 9, 9, 10, 36, 0, 0, 0, 0, 0, 0, 0, 0, 10, 10, 27], [27, 6, 2, 6, 1, 27, 7, 32, 11, 33, 11, 11, 11, 36, 0, 33, 1, 27, 10, 32, 19, 16, 32, 11, 11, 11, 10, 33, 5, 5, 17, 11, 11, 11, 27, 6, 24, 35, 9, 36, 0, 0, 34, 35, 19, 34, 35, 10, 10, 36, 10, 27], [27, 7, 7, 34, 26, 29, 7, 33, 11, 11, 11, 32, 11, 10, 0, 7, 2, 27, 9, 33, 9, 9, 33, 10, 10, 36, 10, 10, 9, 36, 11, 11, 36, 11, 27, 2, 27, 8, 5, 0, 0, 9, 9, 9, 10, 11, 11, 11, 19, 11, 11, 27], [27, 4, 7, 4, 5, 2, 7, 16, 11, 11, 34, 29, 11, 10, 0, 10, 34, 25, 9, 5, 5, 9, 9, 10, 9, 9, 10, 32, 9, 9, 11, 11, 11, 11, 27, 3, 33, 5, 36, 0, 5, 34, 35, 10, 36, 11, 11, 19, 19, 11, 11, 27], [27, 5, 36, 5, 36, 6, 6, 36, 11, 11, 11, 11, 11, 36, 0, 0, 0, 30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 29, 0, 0, 0, 0, 0, 36, 9, 9, 10, 10, 11, 36, 11, 11, 36, 11, 27], [27, 2, 2, 6, 16, 9, 9, 9, 10, 31, 22, 28, 10, 10, 19, 32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 31, 22, 28, 7, 8, 8, 9, 32, 10, 11, 11, 11, 11, 11, 11, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 23, 23, 23, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 23, 23, 26, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
