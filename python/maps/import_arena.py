##"import_arena.py" ---VERSION 0.01---
## - A quick library which imports TBO maps into a game with much EZ -
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

# - Import any new arenas you make here, and then add them to the list below (indicated further down) - #

#t2 arenas
import t2_Arena01
import t2_Arena02
import t2_Arena03
import t2_Arena04
import t2_Arena05
import t2_Arena06
import t2_Arena07
import t2_Arena08

#t3 arenas
import t3_Arena01
import t3_Arena02
import t3_Arena03
import t3_Arena04
import t3_Arena05
import t3_Arena06
import t3_Arena07

#t4 arenas
import t4_Arena01
import t4_Arena02
import t4_Arena03
import t4_Arena04
import t4_Arena05
import t4_Arena06
import t4_Arena07
import t4_Arena08

# - The beginning of the relative path to our images -
path = ""

# - Add your arena to this list to have them appear ingame! - #

#add our arena libraries into a list
arena_libraries = [
    t2_Arena01, t2_Arena02, t2_Arena03, t2_Arena04, t2_Arena05, t2_Arena06, t2_Arena07, t2_Arena08,
    t3_Arena01, t3_Arena02, t3_Arena03, t3_Arena04, t3_Arena05, t3_Arena06, t3_Arena07,
    t4_Arena01, t4_Arena02, t4_Arena03, t4_Arena04, t4_Arena05, t4_Arena06, t4_Arena07, t4_Arena08
                   ]

def return_arena(arena_name, convert=False): #returns the arena + tileset with the arena_name specified.
    global path
    for x in arena_libraries:
        if(x.ARENA_NAME == arena_name):
            return x.get_arena(path, convert)
    return None

def return_arena_numerical(arena_number, convert=False): #returns the arena + tileset with the arena_name specified.
    global path
    if(len(arena_libraries) > arena_number): #we're not getting an index error?
        return [arena_libraries[arena_number].get_arena(path, convert),arena_libraries[arena_number].ARENA_NAME]
    return None #arena doesn't exist?

### - Quick test code making sure that the arena is retrieved correctly -
##arena = return_arena("t2_Arena01")
##for x in range(0,len(arena[0])):
##    print(arena[0][x])
