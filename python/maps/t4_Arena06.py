##"t4_Arena06.py" ---VERSION 0.01---
## - 3rd largest 4-team TBO arena -
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

ARENA_NAME = "t4_Arena06"

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
    arena = [[31, 26, 26, 26, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 22, 26, 26, 26, 28], [27, 37, 11, 11, 33, 10, 10, 10, 11, 11, 11, 10, 11, 11, 11, 16, 16, 11, 11, 11, 10, 3, 3, 6, 2, 5, 5, 33, 8, 7, 38, 27], [27, 11, 16, 11, 10, 10, 36, 10, 11, 36, 11, 32, 11, 36, 11, 11, 11, 11, 36, 11, 32, 7, 36, 7, 2, 36, 5, 4, 8, 16, 3, 27], [27, 11, 11, 11, 10, 36, 10, 10, 11, 16, 11, 27, 11, 11, 36, 10, 10, 36, 10, 11, 27, 8, 16, 3, 7, 10, 36, 5, 2, 6, 3, 27], [24, 35, 11, 11, 36, 10, 10, 36, 11, 32, 11, 33, 10, 11, 11, 11, 10, 7, 10, 11, 33, 4, 32, 10, 36, 10, 10, 36, 2, 5, 34, 25], [27, 11, 11, 36, 10, 11, 11, 11, 11, 27, 11, 16, 10, 10, 10, 11, 10, 4, 10, 11, 16, 4, 27, 10, 11, 11, 11, 10, 36, 5, 5, 27], [27, 11, 36, 10, 10, 11, 36, 10, 10, 33, 11, 36, 1, 1, 36, 11, 10, 36, 10, 11, 36, 10, 33, 11, 11, 36, 11, 10, 10, 36, 10, 27], [27, 11, 11, 11, 10, 11, 11, 36, 10, 10, 11, 10, 6, 36, 10, 11, 11, 10, 36, 11, 11, 11, 11, 11, 36, 10, 11, 11, 11, 10, 10, 27], [27, 10, 36, 11, 34, 35, 11, 11, 19, 10, 11, 10, 36, 5, 10, 10, 11, 11, 10, 36, 10, 10, 10, 19, 5, 4, 34, 35, 11, 36, 5, 27], [27, 10, 19, 11, 11, 11, 19, 11, 11, 36, 11, 11, 10, 1, 6, 31, 28, 11, 10, 10, 5, 5, 36, 10, 4, 19, 11, 11, 11, 19, 2, 27], [27, 1, 34, 26, 35, 11, 34, 35, 11, 10, 36, 11, 11, 36, 6, 30, 29, 11, 36, 2, 6, 36, 10, 10, 34, 35, 11, 34, 26, 35, 5, 27], [27, 8, 8, 10, 10, 11, 11, 11, 11, 10, 5, 36, 11, 11, 10, 10, 10, 11, 10, 7, 36, 11, 11, 11, 11, 11, 11, 11, 11, 10, 2, 27], [27, 3, 8, 10, 19, 19, 10, 10, 36, 5, 1, 2, 36, 11, 11, 16, 16, 11, 10, 36, 11, 11, 10, 36, 11, 11, 19, 19, 11, 10, 2, 27], [27, 3, 36, 10, 10, 10, 10, 36, 8, 8, 36, 2, 6, 36, 11, 11, 11, 11, 36, 10, 11, 36, 2, 7, 36, 11, 11, 11, 11, 36, 6, 27], [27, 7, 2, 36, 4, 5, 36, 3, 3, 8, 1, 5, 3, 7, 36, 11, 11, 36, 6, 10, 11, 10, 7, 2, 7, 36, 10, 10, 36, 7, 7, 27], [27, 16, 6, 7, 8, 8, 1, 6, 7, 31, 28, 2, 16, 7, 7, 17, 17, 1, 1, 16, 11, 31, 28, 10, 10, 10, 10, 10, 4, 7, 16, 27], [27, 16, 2, 7, 3, 10, 1, 6, 6, 30, 29, 8, 16, 4, 8, 17, 17, 6, 6, 16, 11, 30, 29, 10, 11, 11, 11, 10, 8, 4, 16, 27], [27, 5, 5, 36, 10, 10, 36, 3, 3, 8, 5, 5, 6, 8, 36, 11, 11, 36, 2, 10, 11, 11, 11, 11, 11, 36, 11, 11, 36, 5, 5, 27], [27, 5, 36, 11, 11, 11, 11, 36, 6, 4, 36, 2, 2, 36, 11, 11, 11, 11, 36, 10, 10, 36, 10, 10, 36, 10, 10, 11, 11, 36, 10, 27], [27, 10, 10, 11, 19, 19, 11, 10, 36, 5, 2, 7, 36, 10, 11, 16, 16, 11, 10, 36, 5, 5, 6, 36, 4, 5, 19, 19, 11, 11, 11, 27], [27, 11, 11, 11, 10, 11, 11, 10, 3, 5, 2, 36, 6, 10, 11, 10, 10, 11, 11, 11, 36, 1, 2, 7, 4, 4, 5, 10, 10, 10, 11, 27], [27, 11, 34, 26, 35, 11, 34, 35, 6, 6, 36, 10, 10, 36, 11, 31, 28, 10, 36, 11, 10, 36, 6, 3, 34, 35, 3, 34, 26, 35, 11, 27], [27, 11, 19, 11, 11, 11, 19, 3, 3, 36, 10, 11, 11, 11, 11, 30, 29, 10, 11, 11, 10, 1, 36, 7, 8, 19, 6, 6, 10, 19, 11, 27], [27, 11, 36, 11, 34, 35, 8, 4, 19, 10, 10, 11, 36, 10, 10, 10, 10, 11, 11, 36, 10, 10, 10, 19, 4, 8, 34, 35, 10, 36, 11, 27], [27, 11, 10, 11, 11, 10, 10, 36, 11, 11, 11, 11, 11, 36, 1, 10, 11, 11, 36, 1, 10, 11, 11, 11, 36, 5, 10, 10, 11, 11, 11, 27], [27, 11, 36, 10, 11, 10, 36, 10, 11, 32, 11, 36, 11, 10, 36, 10, 11, 36, 6, 6, 36, 11, 32, 11, 10, 36, 10, 11, 11, 36, 10, 27], [27, 11, 11, 36, 11, 11, 10, 10, 11, 27, 11, 16, 11, 10, 3, 10, 11, 11, 10, 10, 16, 11, 27, 11, 10, 11, 11, 11, 36, 3, 8, 27], [24, 35, 11, 10, 36, 11, 11, 36, 11, 33, 11, 32, 11, 10, 8, 10, 10, 11, 11, 10, 32, 11, 33, 11, 36, 11, 10, 36, 3, 7, 34, 25], [27, 11, 11, 11, 10, 36, 11, 11, 11, 16, 11, 27, 11, 10, 36, 3, 6, 36, 11, 11, 27, 11, 16, 11, 11, 11, 36, 8, 7, 7, 1, 27], [27, 11, 16, 11, 10, 10, 36, 10, 10, 36, 11, 33, 11, 36, 3, 6, 2, 5, 36, 11, 33, 11, 36, 10, 10, 36, 5, 5, 4, 16, 1, 27], [27, 39, 11, 11, 32, 2, 6, 3, 8, 10, 11, 11, 11, 10, 10, 16, 16, 5, 10, 11, 11, 11, 10, 7, 2, 2, 2, 32, 4, 5, 40, 27], [30, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
