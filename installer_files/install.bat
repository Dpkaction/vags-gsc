@echo off
title GSC Coin Wallet Setup
echo.
echo ========================================
echo    GSC Coin Wallet Setup v2.0
echo    Professional Cryptocurrency Wallet
echo ========================================
echo.
echo Installing GSC Coin Wallet...
echo.

set "INSTALL_DIR=%PROGRAMFILES%\GSC Coin"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Copying files...
copy "GSC_Coin_Wallet.exe" "%INSTALL_DIR%\" >nul
copy "README.txt" "%INSTALL_DIR%\" >nul
copy "LICENSE.txt" "%INSTALL_DIR%\" >nul

echo Creating shortcuts...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\GSC Coin Wallet.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\GSC_Coin_Wallet.exe'; $Shortcut.Description = 'GSC Coin Professional Wallet'; $Shortcut.Save()"

powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\GSC Coin Wallet.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\GSC_Coin_Wallet.exe'; $Shortcut.Description = 'GSC Coin Professional Wallet'; $Shortcut.Save()"

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo GSC Coin Wallet has been installed to:
echo %INSTALL_DIR%
echo.
echo Shortcuts created:
echo - Desktop: GSC Coin Wallet
echo - Start Menu: GSC Coin Wallet
echo.
echo Features included:
echo - 21.75 trillion GSC total supply
echo - Bitcoin-like mining and rewards
echo - Professional wallet interface
echo - Complete blockchain functionality
echo.
set /p "launch=Launch GSC Coin Wallet now? (Y/N): "
if /i "%launch%"=="Y" start "" "%INSTALL_DIR%\GSC_Coin_Wallet.exe"
echo.
echo Thank you for installing GSC Coin Wallet!
pause
