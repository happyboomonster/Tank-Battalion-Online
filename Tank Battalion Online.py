##Tank Battalion Online ---VERSION 1.0---
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

#Changelog: Too many! See docs/TBO-plans.txt for changes!

# - Removes the backslashes in Windows filenames and replaces them with
#   forward slashes, like everyone SHOULD be using
def debackslash(path):
    result = ""
    for char in list(path):
        if(char == "\\"):
            result += "/"
        else:
            result += str(char)
    return result

import sys, pygame, os
#make sure we can find our absolute path
path = debackslash(os.path.abspath(os.path.dirname(sys.argv[0])))
print("Running from path: " + str(path))
#set up an external import directory (the TBO client code)
sys.path.insert(0, path + "/python/libraries")
sys.path.insert(0, path + "/python/maps")
import battle_client
#the path + "..." argument makes sure we can execute from any folder w/o FileNotFound errors
battle_client.init(path + "/python/libraries/")
#this should auto-run the game code
engine = battle_client.BattleEngine(None,5031)
pygame.quit() #exit pygame
