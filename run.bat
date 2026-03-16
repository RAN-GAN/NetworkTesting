@echo off

REM Simple Python Script Monitor
set "SHARED_PATH=C:\Users\ASUS\Downloads\host"
set "LOCAL_PATH=%~dp0"
set "VERSION_FILE=support\version.txt"
set "EXCEL_FILE=support\SKG_Credentials.xlsx"

set "SCRIPT_TITLE=Python Load Test"

echo Starting monitor...
echo Shared: %SHARED_PATH%
echo Local: %LOCAL_PATH%

:LOOP
echo.
echo Checking for updates...

REM Check if shared version file exists
echo Looking for "%SHARED_PATH%\%VERSION_FILE%"
if not exist "%SHARED_PATH%\%VERSION_FILE%" (
    echo No shared version file found!
    goto WAIT
)

REM Compare local and shared version files
if exist "%LOCAL_PATH%\%VERSION_FILE%" (
    REM Compare file contents. errorlevel 0 means files are identical (no update)
    fc "%SHARED_PATH%\%VERSION_FILE%" "%LOCAL_PATH%\%VERSION_FILE%" >nul
    if not errorlevel 1 (
        echo No update needed
        goto CHECK_RUNNING
    )
)

echo Update found! Copying files...

REM =======================================================
REM Kill any existing Python script instances
REM =======================================================
echo Attempting to kill Python processes...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /F /IM python.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo Copying new files...
copy "%SHARED_PATH%\%VERSION_FILE%" "%LOCAL_PATH%\support" >nul
copy "%SHARED_PATH%\%EXCEL_FILE%" "%LOCAL_PATH%\support" >nul

REM =======================================================
REM Read version.txt -> first line = VERSION_NO, second line = SCRIPT_FILE
REM =======================================================
set "VERSION_NO="
set "SCRIPT_FILE="
for /f "usebackq delims=" %%A in ("%LOCAL_PATH%\%VERSION_FILE%") do (
    if not defined VERSION_NO (
        set "VERSION_NO=%%A"
    ) else if not defined SCRIPT_FILE (
        set "SCRIPT_FILE=support\%%A"
    )
)

echo Version = %VERSION_NO%
echo Script to run = %SCRIPT_FILE%

copy "%SHARED_PATH%\%SCRIPT_FILE%" "%LOCAL_PATH%\support" >nul

echo Files copied. Starting NEW script...
cd /d "%LOCAL_PATH%"

echo Starting local script from "%LOCAL_PATH%\%SCRIPT_FILE%"
start "%SCRIPT_TITLE%" /MIN python "%LOCAL_PATH%\%SCRIPT_FILE%"
goto WAIT

:CHECK_RUNNING
REM Check if the specific script is running using its Title
tasklist /FI "WINDOWTITLE eq %SCRIPT_TITLE%" | find "python.exe" >nul
if errorlevel 1 (
    echo Script is NOT running
) else (
    echo Script is running fine.
)

:WAIT
echo Waiting 10 seconds...
timeout /t 10 /nobreak >nul
goto LOOP
