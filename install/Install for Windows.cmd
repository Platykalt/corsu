@echo off
setlocal
rem Corsu installer for Windows. Release archives bring their own Python; otherwise Python 3.10 or newer is needed.
set PYTHONUTF8=1
cd /d "%~dp0"
rem At the top of a release archive, or in the install folder of the source code.
if not exist "src\installer.py" cd ..
rem Without options, open the Corsu app; --text keeps everything in this window.
set "script=src\installer.py"
if "%~1"=="" set "script=src\app.py"
if "%~1"=="--text" shift
if exist "runtime\x86_64\python\python.exe" ("runtime\x86_64\python\python.exe" %script% %* & goto :end)
where py >nul 2>nul && (py -3 %script% %* & goto :end)
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul && (python %script% %* & goto :end)
echo Python 3 is required to install Corsu.
where winget >nul 2>nul || (echo Install Python from https://www.python.org/downloads/ and run this file again. & goto :end)
set /p answer=Install Python 3 now with winget? [y/N] 
if /i not "%answer%"=="y" goto :end
winget install --id Python.Python.3.13 --exact --accept-source-agreements --accept-package-agreements || goto :end
echo Python installed. Double-click "Install for Windows.cmd" again.
:end
if not defined CI pause
