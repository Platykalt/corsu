@echo off
setlocal
rem Corsu installer for Windows. Release archives bring their own Python; otherwise Python 3.10 or newer is needed.
set PYTHONUTF8=1
cd /d "%~dp0"
rem At the top of a release archive, or in the install folder of the source code.
if not exist "src\installer.py" cd ..
set "python="
if exist "runtime\x86_64\python\python.exe" set "python=runtime\x86_64\python\python.exe"
if not defined python (where py >nul 2>nul && set "python=py -3")
if not defined python (python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul && set "python=python")
if not defined python goto :nopython
rem Options (--text keeps everything in this window) go to the installer.
if not "%~1"=="" (%python% src\installer.py %* & goto :end)
rem Without options, open the Corsu app. When it cannot start, the installer runs here instead, in text mode: it
rem repairs or updates the installed Corsu and keeps its choices, so a broken window never blocks a repair.
%python% src\app.py && goto :end
echo.
echo The Corsu window could not open; installing or repairing here instead.
echo La fenetre de Corsu n'a pas pu s'ouvrir ; installation ou reparation ici a la place.
echo.
%python% src\installer.py
goto :end
:nopython
echo Python 3 is required to install Corsu.
where winget >nul 2>nul || (echo Install Python from https://www.python.org/downloads/ and run this file again. & goto :end)
set /p answer=Install Python 3 now with winget? [y/N]
if /i not "%answer%"=="y" goto :end
winget install --id Python.Python.3.13 --exact --accept-source-agreements --accept-package-agreements || goto :end
echo Python installed. Double-click "Install for Windows.cmd" again.
:end
if not defined CI pause
