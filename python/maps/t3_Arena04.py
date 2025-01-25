##"t3_Arena04.py" ---VERSION 0.01---
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

ARENA_NAME = "t3_Arena04"

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
    arena = [[31, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [27, 0, 0, 0, 0, 0, 0, 9, 0, 0, 3, 3, 0, 16, 16, 1, 6, 6, 10, 10, 10, 11, 11, 10, 10, 10, 0, 27], [27, 0, 0, 32, 0, 0, 36, 5, 9, 9, 36, 2, 2, 3, 8, 1, 1, 34, 35, 10, 11, 36, 11, 11, 36, 10, 0, 27], [27, 0, 34, 29, 0, 32, 1, 5, 5, 36, 3, 5, 1, 5, 1, 5, 2, 2, 0, 36, 11, 11, 11, 36, 5, 9, 0, 27], [27, 0, 0, 0, 0, 33, 1, 34, 35, 9, 9, 34, 35, 7, 7, 34, 35, 0, 0, 0, 10, 11, 36, 0, 36, 5, 0, 27], [27, 10, 10, 10, 32, 9, 9, 4, 4, 6, 6, 5, 8, 7, 5, 5, 6, 0, 0, 0, 0, 36, 0, 0, 0, 36, 0, 27], [27, 11, 11, 11, 33, 10, 34, 35, 6, 9, 36, 8, 8, 37, 5, 6, 6, 36, 0, 0, 36, 10, 10, 0, 0, 0, 0, 27], [24, 26, 35, 11, 11, 11, 10, 10, 32, 9, 0, 34, 35, 8, 5, 34, 35, 0, 0, 32, 10, 10, 10, 10, 0, 34, 26, 25], [27, 0, 0, 34, 35, 11, 11, 10, 33, 0, 0, 0, 19, 16, 16, 19, 0, 0, 34, 23, 35, 11, 10, 31, 35, 0, 0, 27], [27, 0, 0, 0, 0, 36, 11, 11, 11, 11, 0, 0, 0, 19, 19, 0, 0, 36, 11, 11, 11, 11, 34, 29, 10, 10, 10, 27], [27, 0, 0, 0, 9, 10, 10, 34, 35, 11, 11, 11, 0, 0, 0, 0, 11, 11, 11, 31, 28, 11, 11, 11, 11, 11, 11, 27], [27, 0, 36, 9, 9, 7, 10, 9, 9, 31, 28, 11, 11, 11, 11, 11, 11, 34, 26, 21, 29, 18, 34, 35, 10, 32, 10, 27], [27, 0, 9, 6, 36, 7, 16, 8, 9, 30, 21, 35, 16, 19, 19, 16, 36, 0, 0, 0, 0, 0, 0, 10, 10, 33, 10, 27], [27, 0, 9, 6, 5, 36, 4, 5, 5, 6, 11, 11, 11, 16, 16, 0, 0, 0, 36, 0, 0, 18, 0, 0, 36, 0, 10, 27], [27, 19, 9, 32, 5, 3, 6, 31, 28, 10, 11, 32, 11, 11, 32, 10, 0, 36, 0, 0, 36, 0, 0, 36, 0, 0, 10, 27], [27, 0, 0, 33, 4, 3, 2, 7, 27, 10, 11, 24, 35, 11, 27, 10, 10, 0, 0, 0, 0, 0, 36, 0, 0, 32, 5, 27], [27, 0, 0, 16, 5, 32, 2, 1, 33, 11, 11, 33, 11, 11, 27, 10, 34, 26, 28, 10, 0, 0, 0, 0, 0, 27, 8, 27], [27, 0, 32, 5, 5, 33, 1, 38, 11, 11, 36, 10, 11, 34, 25, 11, 11, 11, 27, 10, 10, 39, 10, 10, 34, 25, 8, 27], [27, 0, 27, 5, 18, 18, 10, 11, 11, 16, 9, 10, 11, 11, 27, 11, 32, 11, 33, 11, 11, 11, 36, 5, 5, 33, 3, 27], [27, 0, 33, 0, 32, 10, 11, 11, 36, 9, 7, 36, 10, 11, 33, 11, 33, 11, 11, 11, 36, 11, 11, 36, 2, 6, 7, 27], [27, 0, 0, 0, 33, 11, 11, 10, 5, 36, 1, 6, 36, 11, 11, 11, 18, 10, 10, 10, 18, 11, 11, 11, 36, 10, 19, 27], [27, 0, 0, 10, 11, 11, 18, 4, 5, 0, 36, 2, 5, 31, 26, 26, 35, 10, 34, 26, 35, 11, 11, 36, 11, 11, 11, 27], [27, 19, 10, 11, 11, 36, 7, 8, 36, 0, 0, 36, 5, 27, 5, 10, 11, 11, 11, 11, 11, 11, 36, 11, 11, 36, 10, 27], [27, 10, 11, 11, 36, 2, 3, 36, 0, 0, 0, 0, 0, 27, 5, 10, 11, 36, 10, 10, 10, 36, 11, 11, 32, 7, 5, 27], [27, 11, 11, 36, 5, 6, 36, 10, 10, 36, 0, 0, 0, 27, 2, 36, 11, 11, 36, 10, 36, 11, 11, 34, 29, 4, 7, 27], [27, 11, 36, 9, 5, 36, 10, 10, 11, 11, 36, 10, 0, 27, 6, 3, 36, 11, 11, 36, 11, 11, 36, 5, 2, 36, 7, 27], [27, 10, 19, 9, 9, 9, 10, 11, 11, 11, 11, 10, 10, 27, 3, 8, 8, 19, 11, 11, 11, 10, 5, 5, 5, 5, 18, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
