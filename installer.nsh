; Custom NSIS installer script for Electronics Store Inventory
; This script customizes the Windows installer

!macro customInstall
  ; Create application data directory
  CreateDirectory "$APPDATA\ElectronicsStoreInventory"
  
  ; Set permissions for the application data directory
  AccessControl::GrantOnFile "$APPDATA\ElectronicsStoreInventory" "(S-1-5-32-545)" "FullAccess"
  
  ; Create desktop shortcut with custom icon
  CreateShortCut "$DESKTOP\Electronics Store Inventory.lnk" "$INSTDIR\Electronics Store Inventory.exe" "" "$INSTDIR\resources\app\assets\icon.ico"
  
  ; Create start menu shortcut
  CreateDirectory "$SMPROGRAMS\Electronics Store"
  CreateShortCut "$SMPROGRAMS\Electronics Store\Electronics Store Inventory.lnk" "$INSTDIR\Electronics Store Inventory.exe"
  CreateShortCut "$SMPROGRAMS\Electronics Store\Uninstall.lnk" "$INSTDIR\Uninstall Electronics Store Inventory.exe"
!macroend

!macro customUnInstall
  ; Remove application data directory (optional - ask user)
  MessageBox MB_YESNO "Do you want to remove all application data and settings?" IDNO skip_data_removal
    RMDir /r "$APPDATA\ElectronicsStoreInventory"
  skip_data_removal:
  
  ; Remove desktop shortcut
  Delete "$DESKTOP\Electronics Store Inventory.lnk"
  
  ; Remove start menu shortcuts
  RMDir /r "$SMPROGRAMS\Electronics Store"
!macroend
