$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".packaging-venv\Scripts\python.exe"
$distRoot = Join-Path $PSScriptRoot "dist"
$buildRoot = Join-Path $PSScriptRoot "build"

$serviceBuild = Join-Path $distRoot "WatchDogService"
$finalBuild = Join-Path $distRoot "WatchDog"

if (!(Test-Path $python)) {
    throw "Packaging Python was not found at: $python"
}

Write-Host "Cleaning previous generated builds..."

Remove-Item $serviceBuild -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $finalBuild -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $buildRoot "WatchDogService") `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue
Remove-Item (Join-Path $buildRoot "WatchDog") `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

Write-Host "Building WatchDogService.exe..."

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name WatchDogService `
    --paths . `
    --distpath $distRoot `
    --workpath (Join-Path $buildRoot "WatchDogService") `
    --hidden-import services.benchmark_runner `
    --collect-all ultralytics `
    --collect-all torch `
    --collect-all torchvision `
    --collect-all deep_sort_realtime `
    --collect-all cv2 `
    service_main.py

if ($LASTEXITCODE -ne 0) {
    throw "WatchDogService build failed."
}

Write-Host "Building WatchDog.exe..."

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name WatchDog `
    --paths . `
    --distpath $distRoot `
    --workpath (Join-Path $buildRoot "WatchDog") `
    main.py

if ($LASTEXITCODE -ne 0) {
    throw "WatchDog GUI build failed."
}

Write-Host "Assembling final package..."

$serviceDestination = Join-Path $finalBuild "service"
$assetsDestination = Join-Path $finalBuild "resources\assets"
$weightsDestination = Join-Path `
    $finalBuild `
    "resources\pipeline\models\weights"

New-Item -ItemType Directory -Force $serviceDestination | Out-Null
New-Item -ItemType Directory -Force $assetsDestination | Out-Null
New-Item -ItemType Directory -Force $weightsDestination | Out-Null

Copy-Item `
    (Join-Path $serviceBuild "*") `
    $serviceDestination `
    -Recurse `
    -Force

Copy-Item `
    (Join-Path $PSScriptRoot "assets\clear-presence.mp4") `
    (Join-Path $assetsDestination "clear-presence.mp4") `
    -Force

Copy-Item `
    (Join-Path $PSScriptRoot "pipeline\models\weights\best.pt") `
    (Join-Path $weightsDestination "best.pt") `
    -Force

Copy-Item `
    (Join-Path $PSScriptRoot "pipeline\models\weights\yolov8n.pt") `
    (Join-Path $weightsDestination "yolov8n.pt") `
    -Force

$requiredFiles = @(
    (Join-Path $finalBuild "WatchDog.exe"),
    (Join-Path $finalBuild "service\WatchDogService.exe"),
    (Join-Path $finalBuild "resources\assets\clear-presence.mp4"),
    (Join-Path $finalBuild "resources\pipeline\models\weights\best.pt"),
    (Join-Path $finalBuild "resources\pipeline\models\weights\yolov8n.pt")
)

foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        throw "Required packaged file is missing: $file"
    }
}

Write-Host ""
Write-Host "Build completed successfully."
Write-Host "Final package: $finalBuild"