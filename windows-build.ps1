# Save this as windows-build.ps1
Write-Host "🚀 Windows APK Build Solution for Electronics Store App" -ForegroundColor Green

# Step 1: Clean project
Write-Host "`n🧹 Step 1: Cleaning project..." -ForegroundColor Yellow
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue
npm cache clean --force

# Step 2: Install dependencies
Write-Host "`n📦 Step 2: Installing dependencies..." -ForegroundColor Yellow
npm install --legacy-peer-deps --no-optional

# Step 3: Fix es-abstract missing file
Write-Host "`n🔧 Step 3: Fixing es-abstract module..." -ForegroundColor Yellow
$esAbstractPath = "node_modules\es-abstract\helpers"
if (-not (Test-Path $esAbstractPath)) {
    New-Item -ItemType Directory -Path $esAbstractPath -Force
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

Set-Content -Path "$esAbstractPath\bytesAsFloat32.js" -Value $bytesAsFloat32Content
Write-Host "✅ Created missing bytesAsFloat32.js" -ForegroundColor Green

# Step 4: Verify installation
Write-Host "`n✅ Step 4: Verifying installation..." -ForegroundColor Yellow
try {
    $result = node -e "try { require('expo'); console.log('✅ Expo: OK'); } catch(e) { console.log('❌ Expo: Failed'); }"
    Write-Host $result -ForegroundColor Green
} catch {
    Write-Host "❌ Verification failed" -ForegroundColor Red
}

# Step 5: Build APK
Write-Host "`n🏗️  Step 5: Building APK..." -ForegroundColor Yellow
Write-Host "This may take 10-15 minutes..." -ForegroundColor Cyan
eas build --platform android --profile preview --non-interactive

Write-Host "`n🎉 Build process completed!" -ForegroundColor Green