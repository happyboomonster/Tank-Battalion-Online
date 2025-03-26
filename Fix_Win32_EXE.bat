::Fix_Win32_EXE.sh ---VERSION 0.01---
:: - Small script that fixes the 32-bit Windows build so Windows XP can run it
::   NOTE: Must be run in the Windows 7.1 SDK terminal! The program used to fix the executable is not in a normal command prompt's PATH.
::Copyright (C) 2025  Lincoln V.
::
::This program is free software: you can redistribute it and/or modify
::it under the terms of the GNU General Public License as published by
::the Free Software Foundation, either version 3 of the License, or
::(at your option) any later version.
::
::This program is distributed in the hope that it will be useful,
::but WITHOUT ANY WARRANTY; without even the implied warranty of
::MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
::GNU General Public License for more details.
::
::You should have received a copy of the GNU General Public License
::along with this program.  If not, see <https://www.gnu.org/licenses/>.

editbin.exe /SUBSYSTEM:WINDOWS,4.0 TBO_Windows_x86.exe
