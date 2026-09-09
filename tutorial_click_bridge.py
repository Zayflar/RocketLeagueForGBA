#!/usr/bin/env python3
"""Turn a click on the main-menu Tutorial row into one safe GBA input.

The ROM stays standard GBA software: mouse handling belongs to the desktop
launcher.  This bridge never tries to navigate a menu or drive the car.  It
only emits the configured Select key (C), which the title screen treats as the
direct Tutorial shortcut.
"""

import ctypes
import ctypes.util
import time


BUTTON1_MASK = 1 << 8


def configure_x11():
    x11_path = ctypes.util.find_library("X11")
    xtst_path = ctypes.util.find_library("Xtst")
    if not x11_path or not xtst_path:
        return None, None

    x11 = ctypes.CDLL(x11_path)
    xtst = ctypes.CDLL(xtst_path)
    display_p = ctypes.c_void_p
    window_t = ctypes.c_ulong
    int_p = ctypes.POINTER(ctypes.c_int)
    uint_p = ctypes.POINTER(ctypes.c_uint)
    window_p = ctypes.POINTER(window_t)

    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = display_p
    x11.XCloseDisplay.argtypes = [display_p]
    x11.XRootWindow.argtypes = [display_p, ctypes.c_int]
    x11.XRootWindow.restype = window_t
    x11.XQueryPointer.argtypes = [display_p, window_t, window_p, window_p,
                                  int_p, int_p, int_p, int_p, uint_p]
    x11.XQueryPointer.restype = ctypes.c_int
    x11.XGetGeometry.argtypes = [display_p, window_t, window_p, int_p, int_p,
                                 uint_p, uint_p, uint_p, uint_p]
    x11.XGetGeometry.restype = ctypes.c_int
    x11.XTranslateCoordinates.argtypes = [display_p, window_t, window_t,
                                          ctypes.c_int, ctypes.c_int, int_p,
                                          int_p, window_p]
    x11.XTranslateCoordinates.restype = ctypes.c_int
    x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
    x11.XStringToKeysym.restype = ctypes.c_ulong
    x11.XKeysymToKeycode.argtypes = [display_p, ctypes.c_ulong]
    x11.XKeysymToKeycode.restype = ctypes.c_ubyte
    x11.XFlush.argtypes = [display_p]
    xtst.XTestFakeKeyEvent.argtypes = [display_p, ctypes.c_uint, ctypes.c_int,
                                       ctypes.c_ulong]
    xtst.XTestFakeKeyEvent.restype = ctypes.c_int
    return x11, xtst


def get_bounds(display, x11, window, root):
    root_out = ctypes.c_ulong()
    child_out = ctypes.c_ulong()
    x = ctypes.c_int()
    y = ctypes.c_int()
    width = ctypes.c_uint()
    height = ctypes.c_uint()
    border = ctypes.c_uint()
    depth = ctypes.c_uint()
    if not x11.XGetGeometry(display, window, ctypes.byref(root_out),
                            ctypes.byref(x), ctypes.byref(y),
                            ctypes.byref(width), ctypes.byref(height),
                            ctypes.byref(border), ctypes.byref(depth)):
        return None

    root_x = ctypes.c_int()
    root_y = ctypes.c_int()
    if not x11.XTranslateCoordinates(display, window, root, 0, 0,
                                     ctypes.byref(root_x), ctypes.byref(root_y),
                                     ctypes.byref(child_out)):
        return None
    if width.value < 160 or height.value < 120:
        return None
    return root_x.value, root_y.value, width.value, height.value


def emit_tutorial_key(display, x11, xtst):
    keysym = x11.XStringToKeysym(b"c")
    keycode = x11.XKeysymToKeycode(display, keysym)
    if not keycode:
        return
    xtst.XTestFakeKeyEvent(display, keycode, 1, 0)
    x11.XFlush(display)
    time.sleep(0.04)
    xtst.XTestFakeKeyEvent(display, keycode, 0, 0)
    x11.XFlush(display)


def main():
    x11, xtst = configure_x11()
    if x11 is None:
        return
    display = x11.XOpenDisplay(None)
    if not display:
        return
    root = x11.XRootWindow(display, 0)
    previous_down = False

    try:
        while True:
            root_out = ctypes.c_ulong()
            child_out = ctypes.c_ulong()
            root_x = ctypes.c_int()
            root_y = ctypes.c_int()
            win_x = ctypes.c_int()
            win_y = ctypes.c_int()
            mask = ctypes.c_uint()
            has_pointer = x11.XQueryPointer(
                display, root, ctypes.byref(root_out), ctypes.byref(child_out),
                ctypes.byref(root_x), ctypes.byref(root_y), ctypes.byref(win_x),
                ctypes.byref(win_y), ctypes.byref(mask))
            down = bool(mask.value & BUTTON1_MASK)

            if has_pointer and down and not previous_down and child_out.value:
                bounds = get_bounds(display, x11, child_out.value, root)
                if bounds:
                    left, top, width, height = bounds
                    local_x = (root_x.value - left) / width
                    local_y = (root_y.value - top) / height
                    # Tutorial is the centered fourth row at y=130 on the
                    # 160-pixel game screen. A generous row hit box supports
                    # 2x/3x scaling and normal window decorations.
                    if 0.18 <= local_x <= 0.82 and 0.72 <= local_y <= 0.89:
                        time.sleep(0.05)  # let mGBA focus itself first
                        emit_tutorial_key(display, x11, xtst)
            previous_down = down
            time.sleep(0.012)
    finally:
        x11.XCloseDisplay(display)


if __name__ == "__main__":
    main()
