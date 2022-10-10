##Tank Battalion Online ---VERSION 1.0---
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

import sys, pygame
#set up an external import directory (the TBO client code)
sys.path.insert(0, "python/libraries")
sys.path.insert(0, "python/maps")
import battle_client
battle_client.init("python/libraries/")
#this should auto-run the game code
engine = battle_client.BattleEngine(None,5031)
pygame.quit() #exit pygame
