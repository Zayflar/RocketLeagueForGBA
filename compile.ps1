# ==============================================================================
# GBA 3D Rocket League Auto-Compiler Script
# Controls: ZQSD=D-Pad  K=A(Jump)  L=B(Boost)  M/Ù=L/R  C=Select  Enter=Start
# ==============================================================================
$ErrorActionPreference = "Stop"

# 1. Locate devkitPro and devkitARM
$devkitProPath = $env:DEVKITPRO
$devkitARMPath = $env:DEVKITARM

if ([string]::IsNullOrWhiteSpace($devkitProPath) -or -not (Test-Path $devkitProPath)) {
    if (Test-Path "C:\devkitPro") { $devkitProPath = "C:\devkitPro" }
}
if ([string]::IsNullOrWhiteSpace($devkitARMPath) -or -not (Test-Path $devkitARMPath)) {
    if (Test-Path "$devkitProPath\devkitARM") { $devkitARMPath = "$devkitProPath\devkitARM" }
}

if ([string]::IsNullOrWhiteSpace($devkitProPath) -or -not (Test-Path $devkitProPath)) {
    Write-Error "Could not locate devkitPro! Ensure it is under C:\devkitPro or DEVKITPRO env var is set."
}
if ([string]::IsNullOrWhiteSpace($devkitARMPath) -or -not (Test-Path $devkitARMPath)) {
    Write-Error "Could not locate devkitARM under $devkitProPath\devkitARM!"
}

# 2. Check for devkitPro MSYS2 bash
$bashPath = "$devkitProPath\msys2\usr\bin\bash.exe"
if (-not (Test-Path $bashPath)) {
    Write-Error "Could not find MSYS2 bash at: $bashPath"
}

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   GBA 3D Rocket League Compiler" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Controls:" -ForegroundColor Yellow
Write-Host "   Z / S      = D-Pad Up / Down (Drive / Reverse)" -ForegroundColor Gray
Write-Host "   Q / D      = D-Pad Left / Right (Steer)" -ForegroundColor Gray
Write-Host "   K          = A Button (Jump)" -ForegroundColor Gray
Write-Host "   L          = B Button (Boost)" -ForegroundColor Gray
Write-Host "   C          = Select" -ForegroundColor Gray
Write-Host "   Enter      = Start (Start Match / Replay)" -ForegroundColor Gray
Write-Host "   M / Ù      = L / R Shoulder" -ForegroundColor Gray
Write-Host "=====================================================" -ForegroundColor Cyan

# 3. Locate mGBA before compile so we can configure it
$mgbaPath = $null
$mgbaCmd = Get-Command "mgba.exe", "mgba" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($mgbaCmd)                                             { $mgbaPath = $mgbaCmd.Source }
elseif (Test-Path "C:\Program Files\mGBA\mGBA.exe")      { $mgbaPath = "C:\Program Files\mGBA\mGBA.exe" }
elseif (Test-Path "C:\Program Files (x86)\mGBA\mGBA.exe"){ $mgbaPath = "C:\Program Files (x86)\mGBA\mGBA.exe" }

# 4. Write mGBA key configuration (Qt key codes)
#    Qt::Key_X=88  Qt::Key_W=87  Qt::Key_C=67  Qt::Key_Return=16777220
#    Qt::Key_Up=16777235 Down=16777237 Left=16777234 Right=16777236
#    Qt::Key_A=65 (L shoulder)  Qt::Key_S=83 (R shoulder)
$mgbaConfigDir = [System.IO.Path]::Combine($env:APPDATA, "mGBA")
$mgbaConfigFile = [System.IO.Path]::Combine($mgbaConfigDir, "config.ini")

if (Test-Path $mgbaConfigDir) {
    Write-Host "Configuring mGBA key bindings..." -ForegroundColor Yellow

    # Read existing config or start fresh
    $configLines = @()
    if (Test-Path $mgbaConfigFile) {
        $configLines = Get-Content $mgbaConfigFile
    }

    # Key map: GBA button -> Qt key code
    $keyMap = @{
        "keyA"      = 75          # K key
        "keyB"      = 76          # L key
        "keySelect" = 67          # C key
        "keyStart"  = 16777220    # Enter
        "keyUp"     = 90          # Z key
        "keyDown"   = 83          # S key
        "keyLeft"   = 81          # Q key
        "keyRight"  = 68          # D key
        "keyL"      = 77          # M key
        "keyR"      = 217         # Ù key (Ugrave)
    }

    # Find or create [ports.qt] section
    $inQtSection = $false
    $qtSectionFound = $false
    $newLines = @()
    $appliedKeys = @{}

    foreach ($line in $configLines) {
        if ($line -match "^\[gba\.input\.QT_K\]") {
            $inQtSection = $true
            $qtSectionFound = $true
            $newLines += $line
            continue
        }
        if ($inQtSection -and $line -match "^\[") {
            # Leaving the [gba.input.QT_K] section — flush unapplied keys first
            foreach ($kv in $keyMap.GetEnumerator()) {
                if (-not $appliedKeys.ContainsKey($kv.Key)) {
                    $newLines += "$($kv.Key)=$($kv.Value)"
                }
            }
            $inQtSection = $false
        }
        if ($inQtSection) {
            $replaced = $false
            foreach ($kv in $keyMap.GetEnumerator()) {
                if ($line -match "^$($kv.Key)\s*=") {
                    $newLines += "$($kv.Key)=$($kv.Value)"
                    $appliedKeys[$kv.Key] = $true
                    $replaced = $true
                    break
                }
            }
            if (-not $replaced) { $newLines += $line }
        } else {
            $newLines += $line
        }
    }

    # If we never found [gba.input.QT_K], append it
    if (-not $qtSectionFound) {
        $newLines += "[gba.input.QT_K]"
        foreach ($kv in $keyMap.GetEnumerator()) {
            $newLines += "$($kv.Key)=$($kv.Value)"
        }
    } elseif ($inQtSection) {
        # Section was last — flush remaining unapplied keys
        foreach ($kv in $keyMap.GetEnumerator()) {
            if (-not $appliedKeys.ContainsKey($kv.Key)) {
                $newLines += "$($kv.Key)=$($kv.Value)"
            }
        }
    }

    $newLines | Set-Content $mgbaConfigFile -Encoding UTF8
    Write-Host " mGBA keys configured: ZQSD=D-Pad  K=A  L=B  M/Ù=L/R  C=Select  Enter=Start" -ForegroundColor Green
} else {
    Write-Host " mGBA config directory not found; set keys manually in mGBA settings." -ForegroundColor Gray
}

# 5. Setup compiler environment
$env:DEVKITPRO = $devkitProPath
$env:DEVKITARM = $devkitARMPath
$winPath = Get-Location | Select-Object -ExpandProperty Path
$unixPath = "/c" + ($winPath.Substring(2).Replace('\', '/'))

Write-Host "Compiling..." -ForegroundColor Yellow

# 6. Invoke bash to compile the GBA project
try {
    $compileCmd = "cd '$unixPath' && make clean && make"
    Start-Process -FilePath $bashPath -ArgumentList "-lc", "`"$compileCmd`"" -NoNewWindow -Wait

    $gbaRomFile = Join-Path $winPath "gba_3d.gba"
    if (Test-Path $gbaRomFile) {
        Write-Host "=====================================================" -ForegroundColor Green
        Write-Host " SUCCESS: ROM Compiled!" -ForegroundColor Green
        Write-Host " ROM: $gbaRomFile" -ForegroundColor Green
        Write-Host "=====================================================" -ForegroundColor Green

        if ($mgbaPath) {
            Write-Host "Launching: $mgbaPath" -ForegroundColor Cyan
            Start-Process -FilePath $mgbaPath -ArgumentList "`"$gbaRomFile`""
        } else {
            Write-Host "mGBA not found. Launch the ROM manually." -ForegroundColor Gray
        }
    } else {
        Write-Error "Build finished but no ROM was generated."
    }
} catch {
    Write-Host "=====================================================" -ForegroundColor Red
    Write-Host " ERROR: Compilation failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "=====================================================" -ForegroundColor Red
    Exit 1
}
