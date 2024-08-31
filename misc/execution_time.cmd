@echo off
setlocal enabledelayedexpansion

:: Initialize total duration and loop counter
set "totalSeconds=0"
set "count=10"

:: Execute the command 10 times
for /l %%i in (1,1,%count%) do (
    :: Capture start time
    set "start=!time!"
    
    :: Execute your command here
    C:/Users/Adi/AppData/Local/Programs/Python/Python311/python.exe "c:/Users/Adi/Desktop/Thesis/CDGeB-1/Solving Methods/three-tier-solver/src/CDGeB1/main.py" > NUL
    
    :: Capture end time
    set "end=!time!"
    
    :: Calculate duration (this is a simplistic approach; consider edge cases around midnight)
    call :GetSeconds !start! startSeconds
    call :GetSeconds !end! endSeconds
    set /a "duration=endSeconds-startSeconds"
    
    :: Add duration to total duration
    set /a "totalSeconds+=duration"
)

:: Calculate average duration
set /a "average=totalSeconds/count"

:: Output the average execution time
echo Average Execution Time (10 Iterations): %average% seconds

:: End of main script
goto :eof

:: Function to convert HH:MM:SS.CC format time to seconds
:GetSeconds
set "timeStr=%~1"
set "hours=%timeStr:~0,2%"
set "minutes=%timeStr:~3,2%"
set "seconds=%timeStr:~6,2%"
set /a "%2=hours*3600+minutes*60+seconds"
goto :eof