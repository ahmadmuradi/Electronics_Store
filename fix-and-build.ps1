# fix-and-build.ps1
Write-Host "🔧 Fixing Expo Installation and Building APK" -ForegroundColor Green

# Step 1: Clean everything
Write-Host "`n🧹 Step 1: Cleaning project..." -ForegroundColor Yellow
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
npm cache clean --force

# Step 2: Install Expo CLI globally
Write-Host "`n📦 Step 2: Installing Expo CLI..." -ForegroundColor Yellow
npm install -g @expo/cli

# Step 3: Install dependencies with specific Expo version
Write-Host "`n📦 Step 3: Installing project dependencies..." -ForegroundColor Yellow
npm install --legacy-peer-deps --no-optional

# Step 4: Fix missing es-abstract file
Write-Host "`n🔧 Step 4: Fixing es-abstract module..." -ForegroundColor Yellow
$helpersPath = "node_modules\es-abstract\helpers"
if (-not (Test-Path $helpersPath)) {
    New-Item -ItemType Directory -Path $helpersPath -Force
}

$bytesAsFloat32Content = @"
module.exports = function bytesAsFloat32(bytes, littleEndian = false) {
  const buffer = new ArrayBuffer(4);
  const view = new DataView(buffer);
  bytes.forEach((byte, index) => {
    view.setUint8(index, byte);
  });
  return view.getFloat32(0, littleEndian);
};
"@

Set-Content -Path "$helpersPath\bytesAsFloat32.js" -Value $bytesAsFloat32Content
Write-Host "✅ Created missing bytesAsFloat32.js" -ForegroundColor Green

# Step 5: Verify Expo installation
Write-Host "`n✅ Step 5: Verifying Expo installation..." -ForegroundColor Yellow
try {
    $expoCheck = node -e "
        try {
            const expo = require('expo');
            console.log('✅ Expo module loaded successfully');
            console.log('✅ Expo version:', expo.default?.Constants?.expoVersion || 'unknown');
        } catch (e) {
            console.log('❌ Expo module error:', e.message);
        }
    "
    Write-Host $expoCheck -ForegroundColor Green
} catch {
    Write-Host "❌ Expo verification failed" -ForegroundColor Red
}

# Step 6: Configure EAS
Write-Host "`n⚙️  Step 6: Configuring EAS..." -ForegroundColor Yellow
eas configure

# Step 7: Build APK
Write-Host "`n🏗️  Step 7: Building APK..." -ForegroundColor Yellow
Write-Host "This may take 10-15 minutes..." -ForegroundColor Cyan
eas build --platform android --profile preview --non-interactive

Write-Host "`n🎉 Build process completed!" -ForegroundColor Green