##"t4_Arena08.py" ---VERSION 0.01---
## - The largest 4-team arena for TBO -
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

ARENA_NAME = "t4_Arena08"

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
    arena = [[31, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [24, 29, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 2, 3, 8, 33, 2, 3, 8, 5, 2, 3, 10, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 27], [27, 7, 11, 6, 34, 22, 28, 5, 32, 11, 34, 35, 11, 5, 32, 5, 9, 9, 9, 9, 9, 9, 9, 3, 34, 35, 9, 34, 26, 26, 26, 26, 35, 9, 34, 35, 0, 0, 27], [27, 2, 32, 5, 5, 24, 25, 6, 27, 1, 2, 19, 7, 34, 23, 35, 9, 19, 20, 16, 9, 19, 9, 20, 5, 9, 9, 0, 10, 5, 6, 7, 8, 5, 6, 7, 36, 0, 27], [27, 5, 24, 35, 0, 30, 29, 0, 24, 26, 35, 0, 0, 0, 0, 0, 0, 20, 9, 20, 9, 20, 9, 36, 6, 16, 10, 11, 32, 11, 32, 11, 16, 2, 16, 8, 20, 0, 27], [27, 8, 27, 1, 6, 3, 4, 5, 27, 4, 3, 6, 16, 36, 11, 11, 9, 16, 20, 37, 9, 16, 9, 20, 3, 16, 10, 11, 33, 11, 33, 11, 16, 3, 16, 5, 36, 0, 27], [27, 3, 27, 11, 34, 28, 11, 11, 33, 11, 34, 35, 11, 11, 11, 11, 9, 20, 9, 9, 20, 9, 9, 36, 8, 16, 16, 0, 11, 36, 11, 4, 3, 16, 7, 6, 20, 0, 27], [27, 2, 27, 11, 11, 27, 11, 11, 11, 11, 11, 11, 11, 11, 31, 35, 9, 19, 9, 16, 20, 19, 9, 20, 5, 9, 10, 0, 10, 5, 8, 7, 6, 5, 8, 7, 36, 0, 27], [27, 5, 24, 28, 1, 24, 26, 26, 26, 26, 26, 26, 35, 5, 33, 1, 9, 9, 0, 9, 9, 9, 9, 5, 34, 35, 9, 34, 26, 26, 26, 26, 35, 9, 34, 35, 0, 0, 27], [27, 0, 24, 25, 0, 27, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 5, 32, 3, 2, 3, 10, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 27], [27, 0, 24, 29, 0, 27, 0, 34, 26, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 26, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 25], [27, 0, 27, 0, 0, 27, 0, 0, 0, 27, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 33, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 27], [27, 0, 27, 0, 34, 21, 26, 35, 0, 27, 0, 32, 4, 36, 1, 4, 3, 2, 1, 36, 4, 0, 0, 4, 1, 6, 11, 6, 32, 6, 32, 5, 11, 32, 11, 31, 28, 7, 27], [27, 0, 27, 0, 0, 27, 0, 0, 0, 27, 0, 33, 7, 8, 36, 11, 11, 7, 36, 8, 3, 19, 0, 16, 2, 19, 4, 1, 27, 1, 27, 2, 3, 33, 3, 30, 29, 1, 27], [27, 0, 24, 35, 0, 27, 0, 34, 26, 21, 0, 2, 6, 11, 11, 36, 11, 36, 11, 7, 2, 3, 0, 0, 0, 0, 0, 34, 29, 0, 30, 35, 0, 0, 0, 0, 0, 0, 27], [27, 0, 27, 0, 0, 27, 0, 0, 0, 27, 0, 36, 11, 11, 11, 16, 11, 16, 11, 36, 1, 16, 0, 38, 0, 16, 5, 6, 7, 19, 7, 6, 5, 6, 34, 26, 35, 0, 27], [27, 0, 27, 0, 34, 21, 26, 35, 0, 27, 0, 2, 32, 6, 11, 36, 11, 36, 11, 5, 4, 1, 0, 0, 0, 0, 8, 34, 28, 1, 31, 35, 4, 16, 7, 4, 19, 0, 27], [27, 0, 27, 0, 0, 27, 0, 0, 0, 24, 35, 7, 30, 35, 11, 11, 11, 11, 36, 8, 3, 19, 0, 16, 0, 19, 7, 4, 27, 2, 27, 2, 3, 36, 6, 3, 3, 0, 27], [27, 0, 24, 35, 0, 27, 0, 34, 26, 21, 0, 2, 3, 6, 3, 34, 35, 2, 3, 36, 2, 1, 0, 1, 0, 1, 6, 7, 33, 7, 33, 5, 36, 6, 5, 32, 6, 0, 27], [27, 0, 27, 0, 0, 27, 0, 0, 0, 0, 0, 0, 32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 31, 25, 0, 0, 27], [27, 0, 27, 0, 34, 23, 22, 22, 22, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 22, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 25, 0, 34, 25], [27, 0, 27, 0, 0, 0, 30, 23, 29, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 33, 6, 3, 4, 5, 9, 9, 9, 10, 10, 10, 9, 9, 6, 5, 27, 0, 0, 27], [27, 0, 27, 0, 36, 0, 0, 0, 10, 10, 32, 10, 34, 28, 10, 10, 16, 0, 4, 7, 4, 7, 4, 1, 2, 7, 9, 31, 35, 11, 10, 36, 9, 5, 8, 24, 35, 0, 27], [27, 0, 27, 0, 0, 0, 33, 0, 34, 26, 25, 10, 11, 30, 35, 9, 5, 2, 19, 6, 16, 8, 19, 2, 3, 8, 34, 29, 11, 11, 36, 10, 9, 16, 7, 27, 0, 0, 27], [27, 0, 27, 0, 32, 0, 0, 0, 10, 10, 33, 11, 11, 10, 17, 19, 9, 7, 8, 5, 9, 5, 9, 3, 4, 18, 17, 11, 11, 36, 11, 10, 10, 9, 2, 27, 0, 34, 25], [27, 0, 27, 0, 33, 0, 32, 0, 10, 11, 11, 11, 11, 10, 10, 18, 36, 4, 16, 9, 39, 9, 16, 4, 36, 19, 11, 11, 11, 11, 11, 16, 10, 16, 1, 27, 0, 0, 27], [27, 0, 27, 0, 0, 0, 27, 0, 32, 10, 31, 35, 11, 11, 17, 19, 9, 6, 5, 9, 9, 9, 6, 5, 6, 18, 17, 11, 11, 36, 10, 9, 9, 1, 8, 24, 35, 0, 27], [27, 0, 24, 26, 35, 0, 27, 0, 33, 10, 27, 10, 10, 31, 35, 10, 10, 0, 19, 6, 16, 6, 19, 6, 9, 9, 34, 28, 11, 11, 36, 10, 3, 16, 7, 27, 0, 0, 27], [27, 0, 27, 0, 0, 0, 27, 0, 0, 0, 33, 0, 34, 29, 10, 10, 16, 0, 0, 5, 8, 7, 4, 3, 8, 9, 10, 30, 35, 11, 11, 36, 9, 7, 2, 27, 0, 34, 25], [27, 0, 27, 0, 34, 26, 21, 22, 28, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 7, 6, 1, 8, 9, 9, 10, 10, 10, 10, 10, 10, 10, 9, 7, 27, 0, 0, 27], [27, 0, 33, 0, 0, 0, 30, 23, 23, 26, 23, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 35, 0, 27], [27, 0, 5, 31, 28, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 11, 16, 11, 11, 11, 10, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 27], [27, 0, 6, 30, 23, 26, 26, 35, 2, 32, 4, 3, 2, 1, 34, 35, 0, 10, 11, 11, 11, 11, 11, 34, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 35, 0, 36, 0, 27], [27, 0, 7, 6, 5, 6, 7, 8, 5, 27, 5, 8, 32, 7, 5, 7, 0, 19, 11, 16, 11, 19, 11, 11, 11, 0, 1, 11, 11, 11, 11, 11, 11, 11, 11, 11, 19, 0, 27], [27, 0, 0, 36, 19, 34, 35, 0, 0, 27, 0, 0, 33, 2, 6, 6, 0, 10, 10, 10, 10, 10, 10, 32, 10, 34, 26, 26, 35, 11, 11, 11, 16, 16, 16, 11, 32, 0, 27], [27, 7, 6, 5, 8, 7, 6, 36, 19, 30, 28, 5, 7, 10, 34, 35, 10, 16, 10, 40, 10, 16, 0, 27, 19, 0, 4, 5, 6, 34, 35, 8, 7, 3, 2, 11, 27, 0, 27], [27, 4, 34, 26, 26, 35, 3, 4, 1, 2, 33, 9, 34, 35, 11, 11, 11, 11, 10, 16, 10, 0, 0, 33, 0, 16, 16, 16, 0, 0, 0, 34, 26, 26, 35, 0, 33, 0, 27], [27, 5, 11, 7, 11, 5, 36, 5, 32, 3, 6, 7, 6, 10, 11, 32, 11, 11, 10, 10, 11, 5, 6, 7, 8, 5, 6, 7, 8, 5, 6, 7, 8, 5, 6, 7, 19, 5, 27], [27, 11, 16, 11, 16, 11, 16, 11, 33, 4, 36, 19, 19, 19, 34, 23, 26, 26, 26, 35, 11, 18, 11, 36, 5, 34, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 35, 2, 27], [27, 11, 11, 11, 11, 11, 11, 11, 8, 1, 8, 7, 9, 9, 10, 10, 11, 11, 11, 11, 11, 11, 11, 7, 2, 1, 1, 4, 3, 2, 1, 1, 4, 3, 2, 1, 4, 3, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
