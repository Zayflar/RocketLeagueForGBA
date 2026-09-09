#!/bin/bash
set -e

BUILD_ONLY=0
if [ "${1:-}" = "--build-only" ]; then
    BUILD_ONLY=1
elif [ "$#" -ne 0 ]; then
    echo "Usage: $0 [--build-only]"
    exit 2
fi

# Always build and launch the ROM that lives beside this script. This prevents
# mGBA from opening a same-named ROM from an older Rocket GBA project.
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================="
echo "   GBA 3D Rocket League Compiler (Linux)"
echo "====================================================="
echo " Controls:"
echo "   Z / S      = D-Pad Up / Down (Drive / Reverse)"
echo "   Q / D      = D-Pad Left / Right (Steer)"
echo "   K          = A Button (Jump)"
echo "   L          = B Button (Boost)"
echo "   C          = Select"
echo "   Enter      = Start (Start Match / Replay)"
echo "   I          = L Shoulder (Drift)"
echo "   O          = R Shoulder (Camera)"
echo "====================================================="

# Locate devkitPro and devkitARM
export DEVKITPRO=${DEVKITPRO:-/opt/devkitpro}
export DEVKITARM=${DEVKITARM:-$DEVKITPRO/devkitARM}

if [ ! -d "$DEVKITPRO" ]; then
    echo "Error: Could not locate devkitPro at $DEVKITPRO"
    echo "Please run ./install_linux.sh first!"
    exit 1
fi

if [ ! -d "$DEVKITARM" ]; then
    echo "Error: Could not locate devkitARM at $DEVKITARM"
    exit 1
fi

# Configure mGBA
MGBA_CONFIG_DIR="$HOME/.config/mgba"
MGBA_CONFIG_FILE="$MGBA_CONFIG_DIR/config.ini"

# Prefer mgba-qt (better display filters + UI) over SDL build
if [ -x "/usr/games/mgba-qt" ]; then
    MGBA_CMD="/usr/games/mgba-qt"
elif [ -x "$(command -v mgba-qt)" ]; then
    MGBA_CMD="mgba-qt"
elif [ -x "/usr/games/mgba" ]; then
    MGBA_CMD="/usr/games/mgba"
elif [ -x "$(command -v mgba)" ]; then
    MGBA_CMD="mgba"
else
    MGBA_CMD=""
fi

if [ -n "$MGBA_CMD" ] && [ "${ROCKETGBA_CONFIGURE_MGBA:-0}" = "1" ]; then
    echo "Configuring mGBA settings for best visual quality..."

    # Write a complete config.ini with:
    #  - 2x integer scaling (sharp, no blurring between pixels)
    #  - Bilinear smoothing for the upscale stage
    #  - Frame blending to reduce flicker on fast motion
    #  - Key bindings (ZQSD + K/L)
    # Configuration is a convenience, never a prerequisite for compiling.
    # Some installations deliberately expose this directory read-only.
    if mkdir -p "$MGBA_CONFIG_DIR" 2>/dev/null && cat << 'EOF' > "$MGBA_CONFIG_FILE"
[General]
resampleVideo=bilinear
showFps=0
showOsd=0
mute=0

[gba]
skipBios=1

[qt]
resolutionScale=3
showMenubar=0
showStatusbar=0
showOsd=0
resampleVideo=bilinear
frameBlend=0
lockIntegerScaling=0

[gba.input.QT_K]
keyA=75
keyB=76
keySelect=67
keyStart=16777220
keyUp=90
keyDown=83
keyLeft=81
keyRight=68
keyL=73
keyR=79
EOF
    then
        echo "mGBA configured: 3x scale, bilinear smoothing, keys mapped!"
    else
        echo "Warning: mGBA config is not writable; keeping existing settings."
    fi
fi

echo "Compiling..."
make clean
make

GBA_ROM="$SCRIPT_DIR/gba_3d.gba"
if [ -f "$GBA_ROM" ]; then
    echo "====================================================="
    echo -e "\033[32m SUCCESS: ROM Compiled!\033[0m"
    echo -e "\033[32m ROM: $GBA_ROM\033[0m"
    echo "====================================================="

    if [ "$BUILD_ONLY" -eq 1 ]; then
        echo "Build-only mode: emulator launch skipped."
    elif [ -n "$MGBA_CMD" ]; then
        echo "Launching: $MGBA_CMD"
        # Standard GBA hardware has no mouse. When the Qt desktop emulator is
        # used, this small companion turns a click on the Tutorial row into one
        # dedicated Select input; it does not inject gameplay controls.
        CLICK_BRIDGE_PID=""
        case "$MGBA_CMD" in
            *mgba-qt*)
                if [ -n "${DISPLAY:-}" ] && [ -f "$SCRIPT_DIR/tutorial_click_bridge.py" ]; then
                    python3 "$SCRIPT_DIR/tutorial_click_bridge.py" &
                    CLICK_BRIDGE_PID=$!
                fi
                ;;
        esac
        "$MGBA_CMD" "$GBA_ROM"
        if [ -n "$CLICK_BRIDGE_PID" ]; then
            kill "$CLICK_BRIDGE_PID" 2>/dev/null || true
        fi
    else
        echo "mGBA not found. Launch the ROM manually."
    fi
else
    echo -e "\033[31m ERROR: Compilation failed! No ROM generated.\033[0m"
    exit 1
fi
