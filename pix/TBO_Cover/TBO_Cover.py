##"TBO_Cover.py" ---VERSION 0.01---
## - Draws the CD cover/printed CD image for TBO in a Pygame window
##Copyright (C) 2025  Lincoln V.
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

#Imports
import pygame
import font
import math

#Display setup
screen = pygame.display.set_mode([640,480],pygame.RESIZABLE)
cover = pygame.image.load("Cover_Final_V2.png")
pygame.display.set_caption("TBO Cover Art (boring)")
size = [640,480]

#case, back, or cd lettering?
lettering = "case"

#Main Loop
running = True
while running:
    #Event loop
    for event in pygame.event.get():
        if(event.type == pygame.QUIT):
            running = False
        elif(event.type == pygame.WINDOWRESIZED):
            size = [screen.get_width(), screen.get_height()]

    #Get scale
    if(size[0] / size[1] > 640 / 480): #bigger X axis
        scale = size[1] / 480.0
    else: #bigger Y axis
        scale = size[0] / 640.0

    #Setup screen dimensions
    midpoint = [size[0] / 2, size[1] / 2]
    offset = [-screen.get_width() / 2 + 640.0 * scale / 2, screen.get_height() / 2 - 480.0 * scale / 2]
    
    #Draw stuff (based on 640x480 screen)
    screen.fill([0,0,0])
    screen.blit(pygame.transform.scale(cover, [int(640*scale),int(480*scale)]),[-offset[0],offset[1]])
    if(lettering == "case"):
        pygame.draw.rect(screen, [75,75,75], [-offset[0],offset[1],640*scale,480*scale],math.ceil(5 * scale))
        tbo_scale = 2.0 * scale
        tbo_mid = 21 * font.SIZE * tbo_scale / 2
        font.draw_words("Tank Battalion Online", [midpoint[0] - tbo_mid,offset[1] + 95 * scale], [255,255,0], tbo_scale, screen)
        v_scale = 2.0 * scale
        v_mid = 4 * font.SIZE * v_scale / 2
        font.draw_words("V1.0", [midpoint[0] + tbo_mid - v_mid * 2,offset[1] + (115 + 10) * scale], [255,0,0], v_scale, screen)
        created_scale = 1.0 * scale
        created_mid = len("Created by Lincoln V.") * font.SIZE * created_scale / 2
        font.draw_words("Created by Lincoln V.", [offset[0] + size[0] - created_mid * 2 - 5 * scale,offset[1] + 459 * scale], [255,255,255], created_scale, screen)
    elif(lettering == "cd"):
        pygame.draw.circle(screen, [75,75,75], [midpoint[0],midpoint[1]], math.ceil(240*scale), math.ceil(5*scale))
        pygame.draw.circle(screen, [75,75,75], [midpoint[0],midpoint[1]], math.ceil(5*scale), math.ceil(5*scale))
        tbo_scale = 1.25 * scale
        tbo_mid = 21 * font.SIZE * tbo_scale / 2
        font.draw_words("Tank Battalion Online", [midpoint[0] - tbo_mid,offset[1] + 100 * scale], [255,255,0], tbo_scale, screen)
        v_scale = 1.25 * scale
        v_mid = 4 * font.SIZE * v_scale / 2
        font.draw_words("V1.0", [midpoint[0] - v_mid * 2 + tbo_mid,offset[1] + 118 * scale], [255,0,0], v_scale, screen)
        created_scale = 1.0 * scale
        created_mid = len("Created by Lincoln V.") * font.SIZE * created_scale / 2
        font.draw_words("Created by Lincoln V.", [midpoint[0] - created_mid,offset[1] + 385 * scale], [255,255,255], created_scale, screen)
    elif(lettering == "back"):
        screen.fill([0,0,0])
        pygame.draw.rect(screen, [75,75,75], [-offset[0],offset[1],640*scale,480*scale],math.ceil(5 * scale))
        gpl_scale = 1.0 * scale
        font.draw_words("NOTICE - Licenced under GNU GPL V3.", [-offset[0] + 10 * scale,offset[1] + (480 - 20 - 15) * scale], [255,255,255], gpl_scale, screen)
        font.draw_words("More info in LICENSE file on CD.", [-offset[0] + 10 * scale,offset[1] + (480 - 20) * scale], [255,255,255], gpl_scale, screen)
    pygame.display.flip() #Yeah, I always forget this line and nothing shows up...

pygame.quit() #close pygame window
