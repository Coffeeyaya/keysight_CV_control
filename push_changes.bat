@echo off
echo Committing and pushing all local changes to GitHub...
git add .
git commit -m "test"
git push
echo Done.
pause
