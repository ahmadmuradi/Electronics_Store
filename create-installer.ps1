# Electronics Store Desktop App Installer Creator
# This script creates a self-extracting installer

Write-Host "🚀 Creating Electronics Store Desktop App Installer..." -ForegroundColor Green
Write-Host ""

$appName = "Electronics Store Inventory"
$version = "1.0.0"
$buildDir = Join-Path $PSScriptRoot "build"
$installerDir = Join-Path $PSScriptRoot "installer"
$outputDir = Join-Path $PSScriptRoot "releases"

# Create directories
if (!(Test-Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host "📁 Preparing installer files..." -ForegroundColor Yellow

# Copy build files to installer directory
if (Test-Path $buildDir) {
    Copy-Item -Path "$buildDir\*" -Destination $installerDir -Recurse -Force
    Write-Host "✅ Copied application files"
} else {
    Write-Host "❌ Build directory not found. Please run build-simple.js first." -ForegroundColor Red
    exit 1
}

# Create installer script
$installerScript = @"
@echo off
echo ====================================================
echo Electronics Store Inventory - Desktop Application
echo Version $version
echo ====================================================
echo.

set INSTALL_DIR=%USERPROFILE%\ElectronicsStore
set DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\Electronics Store.lnk
set STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Electronics Store

echo 📁 Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo 📦 Copying application files...
xcopy "%~dp0*" "%INSTALL_DIR%\" /E /I /Y /Q

echo 🔗 Creating shortcuts...
if not exist "%STARTMENU_DIR%" mkdir "%STARTMENU_DIR%"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\shortcut.vbs"
echo sLinkFile = "%DESKTOP_SHORTCUT%" >> "%TEMP%\shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\shortcut.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\start.bat" >> "%TEMP%\shortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\shortcut.vbs"
echo oLink.Description = "Electronics Store Inventory Management" >> "%TEMP%\shortcut.vbs"
echo oLink.Save >> "%TEMP%\shortcut.vbs"
cscript "%TEMP%\shortcut.vbs" /nologo

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\startmenu.vbs"
echo sLinkFile = "%STARTMENU_DIR%\Electronics Store Inventory.lnk" >> "%TEMP%\startmenu.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\startmenu.vbs"
echo oLink.TargetPath = "%INSTALL_DIR%\start.bat" >> "%TEMP%\startmenu.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\startmenu.vbs"
echo oLink.Description = "Electronics Store Inventory Management" >> "%TEMP%\startmenu.vbs"
echo oLink.Save >> "%TEMP%\startmenu.vbs"
cscript "%TEMP%\startmenu.vbs" /nologo

del "%TEMP%\shortcut.vbs" 2>nul
del "%TEMP%\startmenu.vbs" 2>nul

echo.
echo ✅ Installation completed successfully!
echo.
echo 📍 Installation location: %INSTALL_DIR%
echo 🖥️  Desktop shortcut created
echo 📋 Start menu shortcut created
echo.
echo To start the application:
echo 1. Double-click the desktop shortcut, or
echo 2. Use the start menu shortcut, or  
echo 3. Navigate to %INSTALL_DIR% and run start.bat
echo.
pause
"@

$installerScript | Out-File -FilePath (Join-Path $installerDir "install.bat") -Encoding ASCII

# Create uninstaller
$uninstallerScript = @"
@echo off
echo ====================================================
echo Electronics Store Inventory - Uninstaller
echo ====================================================
echo.

set INSTALL_DIR=%USERPROFILE%\ElectronicsStore
set DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\Electronics Store.lnk
set STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Electronics Store

echo Are you sure you want to uninstall Electronics Store Inventory?
pause

echo 🗑️  Removing shortcuts...
if exist "%DESKTOP_SHORTCUT%" del "%DESKTOP_SHORTCUT%"
if exist "%STARTMENU_DIR%" rmdir /s /q "%STARTMENU_DIR%"

echo 📁 Removing application files...
if exist "%INSTALL_DIR%" (
    cd /d "%USERPROFILE%"
    rmdir /s /q "%INSTALL_DIR%"
)

echo.
echo ✅ Uninstallation completed!
echo.
pause
"@

$uninstallerScript | Out-File -FilePath (Join-Path $installerDir "uninstall.bat") -Encoding ASCII

# Create a ZIP package
Write-Host "📦 Creating installer package..." -ForegroundColor Yellow

$zipPath = Join-Path $outputDir "ElectronicsStore-Desktop-v$version-Installer.zip"

# Use PowerShell 5.0+ Compress-Archive if available
if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
    Compress-Archive -Path "$installerDir\*" -DestinationPath $zipPath -Force
    Write-Host "✅ Created ZIP installer: $zipPath"
} else {
    Write-Host "⚠️  Compress-Archive not available. Files prepared in: $installerDir"
}

# Create a self-extracting executable using built-in tools
Write-Host "🔧 Creating self-extracting installer..." -ForegroundColor Yellow

$sfxScript = @"
@echo off
echo Extracting Electronics Store Inventory...
echo Please wait...

set TEMP_DIR=%TEMP%\ElectronicsStore_Setup
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

echo Extracting files...
powershell -command "Expand-Archive -Path '%~dp0ElectronicsStore-Desktop-v$version-Installer.zip' -DestinationPath '%TEMP_DIR%' -Force"

if exist "%TEMP_DIR%\install.bat" (
    cd /d "%TEMP_DIR%"
    call install.bat
    cd /d "%TEMP%"
    rmdir /s /q "%TEMP_DIR%"
) else (
    echo Error: Installation files not found!
    pause
)
"@

$sfxPath = Join-Path $outputDir "ElectronicsStore-Desktop-v$version-Setup.exe"
$sfxScript | Out-File -FilePath "$sfxPath.bat" -Encoding ASCII

Write-Host ""
Write-Host "🎉 Installer creation completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Available packages:" -ForegroundColor Cyan
Write-Host "   • ZIP Installer: $zipPath"
Write-Host "   • Batch Setup: $sfxPath.bat"
Write-Host ""
Write-Host "📁 Installer files location: $installerDir"
Write-Host "📁 Release packages location: $outputDir"
Write-Host ""
Write-Host "To distribute:" -ForegroundColor Yellow
Write-Host "1. Share the ZIP file for manual installation"
Write-Host "2. Run the .bat file for automatic setup"
Write-Host ""
