##"setup.py" - The .EXE build script for TBO ---VERSION 0.02---
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

from distutils.core import setup
import py2exe
import sys #needed to find all my various libraries...
sys.path.insert(0,"python/libraries")
sys.path.insert(0,"python/maps")
sys.path.insert(0,"pix/")

setup(console=["Tank Battalion Online.py"])
