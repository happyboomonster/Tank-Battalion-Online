##Tank Battalion Online ---VERSION 1.0---
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

TL;DR:
	To play the game, simply start the "Tank Battalion Online.py" script with Python 3!
	Alternatively, use one of the executables contained in the same folder as this README document. Run it!
	For more information on how to play, a game manual is located inside the "docs" folder.
	If you want to host your own TBO server, since there is no official game server, there is more info on that in a document inside the "docs" folder.
	REDUCE YOUR SCREEN RESOLUTION IF YOUR FRAMERATE IS TOO LOW!

System Requirements:
	- OS:
		- TBO_Windows_x86_64: Windows 10+. Sometimes Win10 apps can run on earlier versions; I believe I managed to get the game to start on Windows 7.
		- TBO_Windows_x86: Windows XP or newer. You'll probably need Service Pack 3 installed if you're running XP, although I am not 100% sure.
		- TBO_Linux_x86_64: Debian 11+ or equivalent. Other Linux distros: Make sure your LIBC version is the same or newer than Debian 11's LIBC.
		- TBO_Linux_x86: Debian 12+ or equivalent. Same as above ^^
	- CPU:	Minimum: Anything that runs Python 3 and Pygame (I've done it on a 1-core Pentium 4 @ 1.8 GHz. It did not go well ; ~1 FPS @ 1920x1080).
		20FPS: Made after 2010, running at 2.0+ GHz clock speed, with at least 3 cores (A Core i7-720QM will get close to 20FPS at 1920x1080)
		60FPS: I get *close* to 60 FPS at 1920x1080 with an Intel Core i5-10500H. Figure it out from here.
		Recommended: As fast as you can afford...I did what I could to optimise the game, but...I'm not a wizard,
			and Python isn't exactly a fast programming language.
	- GPU:	CAN IT RUN PAINT???
	- RAM:	I have tested that the game runs with 512 MB of RAM on Windows XP. Maybe even 256 MB could work on a lightweight operating system?

If you are running the game via Python:
	- Make sure you have Pygame installed! The earliest version I have tested is around 1.9.x, which worked fine.
	- Also, the game MUST be run using Python 3! (just don't try 2.x, it's EOL and 3 runs faster anyways...)

Have fun! (hopefully there are no more bugs left in the game)

IGNORED BUGS:
 - Controller button numbers are not displayed on HUD in offline mode
 - Entering the lobby menu from login/matchmaker/ingame takes twice as long to load as "Loading..." appears for
 - The button to switch from Keyboard to Joystick mode in offline mode has to be pressed twice for some reason (I *think* this is a Pygame bug?)
 - The last death explosion from a game does not happen
 - Battle outcomes are not always recorded correctly. As a result, players will sometimes be incorrectly awarded for their contributions to the battle.
 - Sometimes when turning in one direction and changing to another before completing the first turn, the player's tank will infinitely spin in circles until the player tries to move in a new direction.
