##Tank Battalion Online ---VERSION 1.0---
##Copyright (C) 2023  Lincoln V.
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

# - Changelog:
#   fixed font.py positioning issue in menus
#   miscellaneous engine bugfixes
#   added snap-to-block turning
#   change music options
#   autodetect music functionality (new music will be automatically detected by the game; just place it in the correct directory: sfx/music/lobby, queue, ingame)
#   bots will turn to face an enemy when driving the other way if rating is greater than a certain amount
#   matchmaker tries to queue in more players if at all possible (players < 8)
#   player settings are saved by the server in a player's account profile
#   timeout added to battles (teams still alive get n-way tie; teams dead get n-th place)
#   packets per second and compute cycles per second are now displayed in the window header during a battle (20 PPS is the maximum the server will send a client)
#   added a minimap
#   in-game communication is now private to your own team. However, you are spotted by the enemy's radar systems, which can detect your use of radio communications.
#   tanks become slightly grey when they are in the "unspotted" state during Experience Battles
#   improved battle outcome display
#   added a server-side speedhax anticheat
#   added the ability to see the upgrade status of potential opponents in the battle queue menu
#   players receive a gift of 30 hollow shells every 24 hrs to avoid bankrupt accounts
#   slightly reduced the bitrate needed to sustain 20PPS
#   triple-threaded the client code (it was previously double-threaded)

import sys, pygame
#set up an external import directory (the TBO client code)
sys.path.insert(0, "python/libraries")
sys.path.insert(0, "python/maps")
import battle_client
battle_client.init("python/libraries/")
#this should auto-run the game code
engine = battle_client.BattleEngine(None,5031)
pygame.quit() #exit pygame
