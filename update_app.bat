@echo off
echo Resetting local files and pulling latest code from GitHub...
git fetch --all
git reset --hard origin/main
echo Update complete.
pause
