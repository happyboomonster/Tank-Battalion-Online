##"import_arena.py" - A quick external library which can find and import TBO maps with much EZ.
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

#t2 arenas
import t2_Arena01
import t2_Arena02

#t3 arenas
import t3_Arena01
import t3_Arena02

#t4 arenas
import t4_Arena01
import t4_Arena02
import t4_Arena03

# - The beginning of the relative path to our images -
path = ""

#add our arena libraries into a list
arena_libraries = [
    t2_Arena01, t2_Arena02,
    t3_Arena01, t3_Arena02,
    t4_Arena01, t4_Arena02, t4_Arena03
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

##quick test code making sure that the arena is retrieved correctly
##arena = return_arena("Arena01")
##for x in range(0,len(arena[0])):
##    print(arena[0][x])
