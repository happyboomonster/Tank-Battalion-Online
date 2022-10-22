##"font.py" library ---VERSION 0.04---
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

SIZE = 14 #constant pixel size for font at scale 1.0

dictionary = [ #a list which interprets the match of a symbol to a number index
        ["a",0],
        ["b",1],
        ["c",2],
        ["d",3],
        ["e",4],
        ["f",5],
        ["g",6],
        ["h",7],
        ["i",8],
        ["j",9],
        ["k",10],
        ["l",11],
        ["m",12],
        ["n",13],
        ["o",14],
        ["p",15],
        ["q",16],
        ["r",17],
        ["s",18],
        ["t",19],
        ["u",20],
        ["v",21],
        ["w",22],
        ["x",23],
        ["y",24],
        ["z",25],
        ["0",26],
        ["1",27],
        ["2",28],
        ["3",29],
        ["4",30],
        ["5",31],
        ["6",32],
        ["7",33],
        ["8",34],
        ["9",35],
        ["-",36],
        [" ",37],
        ["?",38],
        [".",39],
        [">",40], #down arrow
        ["^",41],
        ["/",42],
        ["+",43],
        ["%",44],
        [",",45]
        ]

font = [ #a line based font (abcdefghijklmnopqrstuvwxyz0123456789- ?.), size 10PX
        [[0,0],[10,0],[10,10],[10,3],[0,3],[0,0],[0,10]], #A
        [[0,10],[0,0],[10,3],[0,5],[10,8],[0,10]], #B
        [[10,0],[0,0],[0,10],[10,10]], #C
        [[0,0],[10,5],[0,10],[0,0]], #D
        [[10,0],[0,0],[0,5],[10,5],[0,5],[0,10],[10,10]], #E
        [[10,0],[0,0],[0,5],[10,5],[0,5],[0,10]], #F
        [[10,0],[0,0],[0,10],[10,10],[10,8],[8,8]], #G
        [[0,0],[0,10],[0,5],[10,5],[10,0],[10,10]], #H
        [[0,0],[10,0],[5,0],[5,10],[0,10],[10,10]], #I
        [[0,0],[10,0],[5,0],[5,10],[0,8]], #J
        [[0,0],[0,10],[0,5],[10,0],[0,5],[10,10]], #K
        [[0,0],[0,10],[10,10]], #L
        [[0,10],[0,0],[5,5],[10,0],[10,10]], #M
        [[0,10],[0,0],[10,10],[10,0]], #N
        [[0,0],[10,0],[10,10],[0,10],[0,0]], #O
        [[0,10],[0,0],[10,3],[0,6]], #P
        [[5,5],[0,10],[0,0],[10,0],[5,5],[10,10]], #Q
        [[0,10],[0,0],[10,3],[0,6],[10,10]], #R
        [[10,0],[0,3],[10,6],[0,10]], #S
        [[5,10],[5,0],[0,0],[10,0]], #T
        [[0,0],[0,10],[10,10],[10,0]], #U
        [[0,0],[5,10],[10,0]], #V
        [[0,0],[2,10],[5,0],[8,10],[10,0]], #W
        [[0,0],[10,10],[5,5],[10,0],[0,10]], #X
        [[0,0],[5,5],[10,0],[5,5],[5,10]], #Y
        [[0,0],[10,0],[0,10],[10,10]], #Z
        [[10,10],[0,10],[0,0],[10,0],[10,10],[0,0]], #0
        [[5,0],[5,10]], #1
        [[0,2],[5,0],[10,2],[0,10],[10,10]], #2
        [[0,0],[10,0],[10,5],[0,5],[10,5],[10,10],[0,10]], #3
        [[0,0],[0,4],[10,4],[8,4],[8,0],[8,10]], #4
        [[10,0],[0,0],[0,5],[10,8],[0,10]], #5
        [[10,2],[10,0],[0,0],[0,10],[10,10],[10,7],[0,7]], #6
        [[0,0],[10,0],[0,10]], #7
        [[0,3],[5,0],[10,3],[0,8],[5,10],[10,8],[0,3]], #8
        [[0,10],[10,7],[5,0],[0,5],[5,6],[10,7]], #9
        [[0,5],[10,5]], #-
        [], #[space]
        [[0,1],[5,0],[10,1],[10,4],[5,5],[5,10]], #?
        [[5,9],[6,9],[6,10],[5,10],[5,9]], #.
        [[4,0],[6,0],[6,5],[10,5],[5,10],[0,5],[4,5],[4,0]], #down arrow
        [[4,10],[6,10],[6,5],[10,5],[5,0],[0,5],[4,5],[4,10]], #up arrow
        [[0,10],[10,0]], #/
        [[5,0],[5,10],[5,5],[0,5],[10,5]], #+
        [[10,0],[0,10],[5,5],[1,1],[3,1],[3,3],[1,3],[1,1],[9,9],[7,9],[7,7],[9,7],[9,9]], #%
        [[4,8],[6,8],[3,10],[4,8]] #,
        ]

#a single font which can be used on pygame's screen surface in any size of position
def draw_words(words, coords, color, scale, screen):
    global dictionary
    global font
    global SIZE

    words = list(words)
    for x in range(0,len(words)): #draw each letter in the string entered
        for findindex in dictionary: #find the index of the letter we used
            if(findindex[0] == words[x].lower()): #we found the letter's index?
                for drawletter in range(0,len(font[findindex[1]]) - 1): #then DRAW IT!
                    pointA = font[findindex[1]][drawletter][:] #find the points we need
                    pointB = font[findindex[1]][drawletter + 1][:]
                    pointA[0] = int(pointA[0] * 1.0 * scale) #scale them correctly
                    pointA[1] = int(pointA[1] * 1.0 * scale)
                    pointB[0] = int(pointB[0] * 1.0 * scale)
                    pointB[1] = int(pointB[1] * 1.0 * scale)
                    pointA[0] += int(coords[0] + (x * SIZE * scale)) #position them correctly
                    pointA[1] += int(coords[1])
                    pointB[0] += int(coords[0] + (x * SIZE * scale))
                    pointB[1] += int(coords[1])
                    pygame.draw.line(screen,color,pointA,pointB,int(1.0 * scale) + 1) #draw the line between those points
                break #exit this "findletter's index" loop, and move on to the next one
