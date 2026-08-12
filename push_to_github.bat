@echo off
echo ========================================
echo Git Push Script for Anchorv2
echo ========================================
echo.

REM Check if git is initialized (it already is from our previous commands)
echo Step 1: Verifying git status...
git status
echo.

REM The repository is already initialized and committed
REM Now we need to handle the authentication issue

echo Step 2: Current remote configuration...
git remote -v
echo.

echo ========================================
echo AUTHENTICATION OPTIONS:
echo ========================================
echo.
echo You have several options to authenticate:
echo.
echo OPTION A: Push to your own GitHub account (Abhaykumar234)
echo    1. Create a new repository at: https://github.com/new
echo       Name it: Anchorv2
echo    2. Then run: git remote set-url origin https://github.com/Abhaykumar234/Anchorv2.git
echo    3. Then run: git push -u origin main
echo.
echo OPTION B: Use Personal Access Token for muskaankumari1910-png's repo
echo    1. Get collaborator access from muskaankumari1910-png
echo    2. Create a Personal Access Token at: https://github.com/settings/tokens
echo    3. Then run: git push -u origin main
echo    4. When prompted, use your token as the password
echo.
echo OPTION C: Use SSH (Recommended)
echo    1. Generate SSH key: ssh-keygen -t ed25519 -C "your_email@example.com"
echo    2. Add to GitHub: https://github.com/settings/keys
echo    3. Change remote: git remote set-url origin git@github.com:muskaankumari1910-png/Anchorv2.git
echo    4. Then run: git push -u origin main
echo.
echo ========================================
echo.
pause
