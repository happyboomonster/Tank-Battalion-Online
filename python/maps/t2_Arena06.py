##"t2_Arena06.py" ---VERSION 0.01---
## - A 1000-block two-team arena for TBO -
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

ARENA_NAME = "t2_Arena06"

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
    flags = [37,38]

    # - Define the arena -
    arena = [[31, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [27, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 19, 18, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 19, 19, 5, 0, 0, 0, 0, 0, 27], [27, 10, 32, 5, 5, 31, 35, 0, 0, 32, 10, 36, 0, 0, 0, 0, 0, 0, 32, 0, 0, 0, 0, 0, 0, 0, 36, 6, 16, 7, 0, 19, 9, 5, 0, 19, 9, 5, 5, 27], [27, 10, 27, 1, 6, 33, 0, 0, 34, 29, 10, 10, 36, 0, 0, 0, 0, 0, 27, 0, 0, 0, 0, 0, 0, 36, 6, 6, 2, 0, 0, 0, 0, 0, 0, 19, 19, 0, 0, 27], [27, 11, 30, 35, 5, 0, 0, 10, 10, 11, 11, 11, 11, 36, 0, 0, 0, 0, 33, 0, 0, 0, 0, 0, 36, 1, 5, 16, 0, 0, 0, 34, 26, 26, 26, 26, 35, 0, 10, 27], [27, 11, 11, 10, 0, 0, 32, 9, 32, 11, 34, 28, 11, 11, 36, 0, 0, 6, 5, 0, 0, 0, 0, 36, 5, 5, 16, 0, 0, 36, 0, 0, 0, 0, 0, 0, 0, 0, 0, 27], [27, 11, 31, 35, 0, 34, 29, 5, 33, 11, 11, 30, 35, 11, 10, 36, 5, 5, 16, 16, 0, 0, 36, 9, 9, 0, 0, 0, 36, 0, 0, 34, 26, 26, 35, 6, 34, 35, 6, 27], [27, 11, 27, 6, 0, 5, 5, 9, 9, 10, 11, 11, 11, 11, 10, 10, 9, 16, 11, 11, 10, 0, 0, 9, 0, 0, 0, 36, 0, 0, 7, 7, 7, 2, 6, 6, 5, 5, 5, 27], [27, 10, 33, 6, 0, 34, 26, 26, 26, 26, 26, 26, 26, 26, 35, 9, 16, 11, 11, 11, 11, 16, 10, 0, 0, 36, 0, 0, 0, 32, 7, 34, 22, 35, 7, 32, 10, 36, 10, 27], [27, 5, 2, 6, 0, 0, 0, 0, 5, 5, 5, 6, 6, 6, 9, 9, 10, 11, 11, 36, 11, 10, 10, 10, 36, 0, 0, 36, 10, 33, 8, 2, 27, 4, 7, 27, 10, 11, 11, 27], [27, 5, 9, 16, 16, 9, 9, 0, 5, 34, 26, 35, 6, 36, 7, 9, 9, 16, 11, 11, 11, 11, 34, 35, 0, 0, 36, 11, 11, 18, 8, 8, 33, 5, 4, 27, 11, 32, 11, 27], [27, 9, 9, 10, 10, 10, 9, 0, 6, 18, 4, 8, 3, 7, 7, 36, 10, 10, 11, 11, 37, 36, 11, 10, 0, 36, 11, 11, 11, 18, 9, 9, 6, 5, 1, 27, 11, 33, 11, 27], [27, 10, 10, 10, 11, 10, 32, 0, 6, 32, 5, 16, 4, 8, 36, 9, 10, 11, 11, 34, 35, 11, 11, 10, 36, 10, 11, 32, 11, 32, 9, 34, 26, 26, 26, 29, 11, 11, 11, 27], [27, 11, 11, 11, 11, 31, 29, 0, 6, 27, 1, 4, 4, 36, 5, 0, 10, 11, 36, 38, 11, 11, 16, 10, 10, 10, 11, 33, 11, 33, 10, 9, 5, 5, 16, 10, 10, 10, 18, 27], [27, 19, 19, 11, 11, 27, 0, 0, 8, 33, 5, 5, 18, 5, 0, 0, 34, 35, 11, 11, 11, 11, 11, 10, 10, 10, 11, 11, 11, 10, 10, 9, 32, 5, 9, 9, 9, 18, 10, 27], [27, 19, 19, 11, 31, 29, 0, 32, 8, 2, 6, 36, 5, 0, 0, 36, 10, 11, 11, 11, 36, 11, 11, 16, 9, 34, 26, 26, 26, 26, 35, 9, 30, 26, 26, 35, 5, 19, 9, 27], [27, 11, 11, 11, 27, 0, 0, 33, 6, 6, 36, 0, 0, 0, 36, 0, 10, 10, 16, 11, 11, 11, 16, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 18, 0, 27], [27, 10, 31, 26, 29, 0, 32, 7, 7, 36, 0, 0, 36, 0, 0, 0, 9, 9, 10, 11, 11, 16, 0, 0, 8, 36, 8, 31, 22, 28, 5, 5, 5, 31, 26, 35, 8, 7, 18, 27], [27, 10, 33, 0, 0, 0, 33, 7, 36, 0, 0, 36, 0, 0, 0, 8, 8, 9, 9, 16, 16, 0, 0, 36, 7, 7, 7, 24, 23, 29, 5, 5, 5, 27, 5, 8, 8, 3, 6, 27], [27, 0, 0, 0, 32, 0, 0, 0, 0, 0, 36, 0, 0, 5, 16, 8, 8, 36, 5, 1, 5, 0, 7, 7, 36, 3, 2, 33, 5, 5, 1, 1, 5, 27, 5, 1, 8, 32, 2, 27], [27, 0, 34, 26, 23, 26, 26, 26, 35, 0, 0, 0, 5, 16, 7, 3, 36, 6, 2, 6, 32, 0, 6, 6, 3, 18, 2, 5, 5, 31, 35, 5, 7, 33, 2, 6, 5, 27, 1, 27], [27, 0, 0, 0, 0, 5, 19, 19, 5, 0, 0, 16, 6, 2, 7, 36, 8, 8, 2, 7, 27, 0, 6, 2, 8, 8, 36, 5, 1, 27, 5, 3, 7, 3, 2, 32, 2, 33, 5, 27], [27, 5, 5, 19, 0, 5, 9, 19, 5, 0, 5, 16, 6, 6, 36, 8, 8, 7, 7, 7, 33, 0, 5, 5, 4, 7, 7, 36, 6, 33, 5, 5, 34, 26, 26, 29, 7, 18, 6, 27], [27, 5, 19, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 19, 18, 19, 7, 6, 6, 6, 1, 8, 8, 8, 8, 3, 7, 2, 2, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
