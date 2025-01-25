##"t2_Arena04.py" ---VERSION 0.01---
## - A large(er) two-team arena for TBO -
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

ARENA_NAME = "t2_Arena04"

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
    arena = [[31, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 28], [27, 5, 11, 11, 11, 11, 11, 11, 10, 9, 9, 9, 9, 5, 5, 11, 11, 11, 11, 11, 7, 8, 27], [27, 5, 36, 11, 36, 11, 11, 32, 10, 32, 9, 32, 9, 32, 5, 32, 11, 11, 36, 11, 36, 5, 27], [27, 7, 7, 11, 11, 11, 16, 27, 0, 27, 9, 27, 9, 27, 1, 27, 16, 11, 11, 11, 11, 11, 27], [27, 11, 36, 11, 36, 10, 10, 27, 0, 27, 10, 27, 9, 27, 1, 27, 7, 6, 36, 11, 36, 11, 27], [27, 11, 11, 11, 10, 10, 0, 33, 0, 27, 0, 27, 9, 27, 6, 33, 4, 6, 5, 11, 11, 11, 27], [27, 11, 11, 16, 10, 0, 0, 0, 0, 27, 0, 27, 8, 27, 2, 3, 3, 3, 5, 16, 11, 11, 27], [27, 11, 10, 34, 26, 35, 0, 0, 10, 33, 10, 27, 8, 33, 2, 2, 5, 34, 26, 35, 5, 11, 27], [27, 10, 10, 10, 0, 0, 0, 10, 10, 9, 9, 27, 1, 1, 5, 3, 3, 4, 4, 6, 5, 5, 27], [24, 35, 11, 34, 26, 26, 26, 35, 9, 16, 5, 33, 7, 16, 1, 34, 26, 26, 26, 35, 11, 34, 25], [27, 11, 11, 11, 10, 0, 0, 0, 10, 9, 9, 8, 2, 2, 2, 8, 8, 5, 5, 11, 11, 11, 27], [27, 37, 11, 34, 26, 26, 26, 26, 26, 35, 7, 36, 8, 34, 26, 26, 26, 26, 26, 35, 11, 38, 27], [27, 11, 11, 11, 10, 0, 0, 0, 10, 9, 9, 5, 5, 1, 1, 5, 5, 8, 8, 11, 11, 11, 27], [24, 35, 11, 34, 26, 26, 26, 35, 9, 16, 6, 32, 2, 16, 1, 34, 26, 26, 26, 35, 11, 34, 25], [27, 10, 10, 10, 0, 0, 0, 10, 10, 9, 9, 27, 2, 6, 3, 5, 1, 1, 1, 6, 5, 5, 27], [27, 10, 10, 34, 26, 35, 0, 0, 10, 32, 10, 27, 6, 32, 3, 3, 4, 34, 26, 35, 5, 11, 27], [27, 11, 10, 16, 0, 0, 0, 0, 0, 27, 0, 27, 9, 27, 5, 4, 4, 1, 7, 16, 11, 11, 27], [27, 11, 11, 10, 10, 10, 0, 32, 0, 27, 0, 27, 9, 27, 1, 32, 1, 7, 5, 11, 11, 11, 27], [27, 11, 36, 11, 36, 10, 0, 27, 0, 27, 10, 27, 9, 27, 6, 27, 5, 6, 36, 11, 36, 11, 27], [27, 11, 5, 5, 11, 10, 16, 27, 0, 27, 9, 27, 9, 27, 1, 27, 16, 11, 11, 8, 7, 8, 27], [27, 11, 36, 5, 36, 11, 10, 33, 10, 33, 9, 33, 9, 33, 8, 33, 11, 11, 36, 5, 36, 11, 27], [27, 11, 11, 7, 7, 11, 11, 10, 10, 9, 9, 9, 9, 5, 5, 11, 11, 11, 11, 11, 11, 11, 27], [30, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 29]]
    return [arena, tiles, shuffle_pattern, blocks, bricks, destroyed_brick, flags]
