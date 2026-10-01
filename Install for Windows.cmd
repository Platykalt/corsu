@echo off
setlocal
rem Corsu installer for Windows. Requires Python 3.10 or newer.
set PYTHONUTF8=1
cd /d "%~dp0"
where py >nul 2>nul && (py -3 src\installer.py %* & goto :end)
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul && (python src\installer.py %* & goto :end)
echo Python 3 is required to install Corsu.
where winget >nul 2>nul || (echo Install Python from https://www.python.org/downloads/ and run this file again. & goto :end)
set /p answer=Install Python 3 now with winget? [y/N] 
if /i not "%answer%"=="y" goto :end
winget install --id Python.Python.3.13 --exact --accept-source-agreements --accept-package-agreements || goto :end
echo Python installed. Double-click "Install for Windows.cmd" again.
:end
if not defined CI pause
