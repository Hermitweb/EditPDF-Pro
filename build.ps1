# EditPDF Pro Build Script
Write-Host "=== EditPDF Pro 打包 ==="
$projectDir = "D:\EditPDFPro"
$srcDir = "$projectDir\src"
$distDir = "$projectDir\dist"

# Clean previous build
Remove-Item -Recurse -Force "$projectDir\build", "$projectDir\dist" -ErrorAction SilentlyContinue

# PyInstaller
pyinstaller --onefile --windowed --name "EditPDF-Pro" --icon NONE `
  --add-data "$srcDir\app;app" `
  --add-data "$srcDir\core;core" `
  --add-data "$srcDir\ui;ui" `
  --add-data "$srcDir\utils;utils" `
  --hidden-import "PyQt5" `
  --hidden-import "fitz" `
  --hidden-import "qfluentwidgets" `
  --hidden-import "PIL" `
  --distpath "$distDir" `
  "$srcDir\main.py"

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item "$distDir\EditPDF-Pro.exe").Length / 1MB
    Write-Host "OK: EditPDF-Pro.exe ($([math]::Round($size,1)) MB)"
} else {
    Write-Host "Build failed"
}
