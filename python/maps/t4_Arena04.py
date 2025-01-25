##"t4_Arena04.py" ---VERSION 0.01---
## - 4-team TBO arena -
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

ARENA_NAME = "t4_Arena04"

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
    arena = [[31, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 22, 26, 26, 26, 22, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [27, 37, 10, 10, 10, 0, 0, 0, 17, 0, 0, 0, 33, 0, 0, 0, 33, 0, 0, 0, 17, 11, 11, 11, 11, 11, 11, 38, 27], [27, 11, 11, 16, 11, 34, 35, 0, 36, 0, 32, 0, 0, 0, 32, 0, 0, 0, 32, 0, 36, 11, 34, 35, 11, 16, 11, 10, 27], [27, 11, 16, 16, 11, 11, 0, 0, 0, 0, 33, 19, 36, 5, 27, 5, 36, 19, 33, 10, 11, 11, 5, 6, 11, 16, 16, 10, 27], [27, 11, 11, 11, 10, 0, 0, 36, 1, 6, 6, 6, 1, 1, 27, 5, 1, 11, 11, 10, 11, 36, 0, 0, 10, 11, 11, 10, 27], [27, 11, 32, 11, 0, 36, 5, 5, 36, 16, 36, 1, 36, 6, 27, 6, 36, 11, 36, 16, 36, 0, 0, 36, 0, 10, 32, 0, 27], [27, 11, 33, 0, 0, 8, 36, 5, 8, 8, 7, 7, 6, 2, 27, 2, 6, 11, 11, 10, 0, 0, 36, 6, 0, 0, 33, 0, 27], [27, 11, 11, 10, 36, 8, 4, 36, 8, 8, 16, 17, 5, 34, 21, 35, 3, 17, 16, 11, 8, 36, 1, 5, 36, 0, 0, 0, 27], [27, 17, 36, 10, 11, 36, 3, 2, 36, 5, 5, 2, 3, 4, 27, 8, 3, 7, 11, 11, 36, 8, 5, 36, 7, 0, 36, 17, 27], [27, 0, 0, 10, 11, 16, 7, 6, 6, 5, 6, 6, 36, 4, 27, 8, 36, 11, 11, 3, 7, 8, 4, 16, 7, 0, 0, 0, 27], [27, 0, 34, 35, 11, 36, 7, 16, 1, 6, 36, 7, 1, 7, 27, 4, 11, 11, 36, 6, 3, 16, 3, 36, 2, 34, 35, 0, 27], [27, 0, 0, 19, 11, 11, 11, 17, 7, 2, 2, 36, 6, 6, 27, 11, 11, 36, 5, 6, 6, 17, 5, 3, 6, 19, 0, 0, 27], [24, 35, 0, 36, 5, 36, 11, 7, 7, 36, 7, 7, 36, 6, 33, 11, 36, 1, 5, 36, 11, 11, 11, 36, 6, 36, 0, 34, 25], [27, 10, 10, 11, 11, 11, 11, 32, 8, 8, 8, 1, 5, 5, 6, 11, 11, 11, 11, 11, 11, 32, 11, 11, 11, 11, 10, 10, 27], [27, 10, 34, 26, 26, 26, 26, 21, 26, 26, 26, 26, 35, 6, 16, 5, 34, 26, 26, 26, 26, 21, 26, 26, 26, 26, 35, 10, 27], [27, 10, 10, 11, 11, 5, 5, 33, 1, 5, 5, 2, 2, 11, 11, 11, 7, 2, 7, 7, 2, 33, 8, 8, 11, 11, 10, 10, 27], [24, 35, 0, 36, 11, 36, 11, 11, 11, 36, 3, 6, 36, 11, 32, 11, 36, 2, 2, 36, 3, 8, 8, 36, 11, 36, 0, 34, 25], [27, 0, 0, 19, 11, 11, 11, 17, 11, 7, 7, 36, 11, 11, 27, 11, 5, 36, 5, 5, 8, 17, 7, 1, 11, 19, 0, 0, 27], [27, 0, 34, 35, 3, 36, 11, 16, 11, 8, 36, 11, 11, 6, 27, 11, 5, 4, 36, 4, 8, 16, 1, 36, 11, 34, 35, 0, 27], [27, 0, 0, 0, 6, 16, 11, 11, 11, 8, 4, 11, 36, 5, 27, 11, 36, 4, 8, 7, 7, 6, 6, 16, 11, 10, 0, 0, 27], [27, 17, 36, 0, 5, 36, 11, 11, 36, 1, 5, 11, 11, 1, 27, 11, 11, 5, 3, 8, 36, 6, 1, 36, 11, 10, 36, 17, 27], [27, 11, 11, 10, 36, 11, 11, 36, 5, 5, 16, 17, 11, 34, 21, 35, 11, 17, 16, 8, 4, 36, 5, 5, 36, 10, 11, 11, 27], [27, 11, 32, 10, 10, 11, 36, 0, 0, 0, 0, 0, 11, 11, 27, 0, 10, 10, 0, 0, 0, 0, 36, 5, 0, 0, 32, 11, 27], [27, 11, 33, 0, 0, 36, 0, 0, 36, 16, 36, 0, 36, 11, 27, 0, 36, 11, 36, 16, 36, 0, 0, 36, 0, 8, 33, 11, 27], [27, 10, 0, 0, 0, 0, 0, 36, 11, 11, 5, 0, 0, 10, 27, 10, 11, 11, 5, 6, 7, 36, 0, 0, 0, 5, 6, 11, 27], [27, 10, 16, 16, 6, 7, 5, 11, 11, 11, 32, 19, 36, 10, 27, 10, 36, 19, 32, 11, 11, 11, 5, 6, 0, 16, 16, 11, 27], [27, 10, 11, 16, 5, 34, 35, 11, 36, 11, 33, 11, 11, 10, 33, 10, 11, 11, 33, 11, 36, 11, 34, 35, 0, 16, 11, 11, 27], [27, 39, 11, 11, 11, 11, 11, 11, 17, 11, 11, 11, 32, 0, 0, 0, 32, 11, 11, 11, 17, 11, 11, 11, 10, 10, 10, 40, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 23, 26, 26, 26, 23, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
