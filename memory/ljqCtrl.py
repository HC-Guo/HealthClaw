# ljqCtrl.py - 桌面键鼠控制 (Windows 物理坐标 + DPI 换算)
# 移植自 pc-agent-loop。CRITICAL: 严禁在此工具链中 import pyautogui (会污染 win32api 导致逻辑冲突)。
# 平台：仅 Windows。macOS/Linux 请用 pyautogui 或系统 API，参见 ljqCtrl_sop.md。

import os
import sys
import time
import random
import math

if sys.platform != "win32":
    dpi_scale = 1.0
    def SetCursorPos(z): raise RuntimeError("ljqCtrl is Windows-only. On macOS use: import pyautogui; pyautogui.click(x, y)")
    def Click(x, y=None): raise RuntimeError("ljqCtrl is Windows-only.")
    def Press(cmd, staytime=0): raise RuntimeError("ljqCtrl is Windows-only.")
    def MouseClick(staytime=0.05): pass
    def MouseDClick(staytime=0.05): pass
    def FindBlock(fn, wrect=None, verbose=0, threshold=0.8): return (0, 0), False
    click = Click
    press = Press
else:
    import win32api
    import win32con
    import numpy as np

    dpi_scale = 1
    try:
        from PIL import ImageGrab, Image, ImageEnhance, ImageFilter, ImageDraw
        import cv2
    except Exception:
        pass

    try:
        scr = ImageGrab.grab()
        swidth, sheight = scr.size
        cwidth, cheight = map(win32api.GetSystemMetrics, [win32con.SM_CXSCREEN, win32con.SM_CYSCREEN])
        dpi_scale = cwidth / swidth
    except Exception:
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        cwidth = user32.GetSystemMetrics(0)
        cheight = user32.GetSystemMetrics(1)
        try:
            dpi = user32.GetDpiForSystem()
            dpi_scale = dpi / 96.0
        except Exception:
            dpi_scale = 1.0

    VK_CODE = {
        "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "shift": 0x10, "ctrl": 0x11, "alt": 0x12,
        "esc": 0x1B, "escape": 0x1B, "space": 0x20, "page_up": 0x21, "page_down": 0x22,
        "end": 0x23, "home": 0x24, "left_arrow": 0x25, "up_arrow": 0x26, "right_arrow": 0x27, "down_arrow": 0x28,
        "insert": 0x2D, "del": 0x2E, "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
        "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
        "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45, "f": 0x46, "g": 0x47, "h": 0x48,
        "i": 0x49, "j": 0x4A, "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F, "p": 0x50,
        "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54, "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59, "z": 0x5A,
        "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
        "+": 0xBB, ",": 0xBC, "-": 0xBD, ".": 0xBE, "/": 0xBF, "`": 0xC0, ";": 0xBA, "[": 0xDB, "\\": 0xDC, "]": 0xDD, "'": 0xDE,
    }
    VK_CODE = {k.lower(): v for k, v in VK_CODE.items()}

    def MouseDown():
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)

    def MouseUp():
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def MouseClick(staytime=0.05):
        MouseDown()
        time.sleep(staytime)
        MouseUp()
        time.sleep(0.05)

    def MouseDClick(staytime=0.05):
        MouseDown()
        MouseUp()
        MouseDown()
        MouseUp()
        time.sleep(0.05)

    def SetCursorPos(z):
        z = tuple(map(lambda v: int(v * dpi_scale), z))
        win32api.SetCursorPos(z)
        time.sleep(0.05)

    def Click(x, y=None):
        if isinstance(x, (tuple, list)):
            x, y = int(x[0]), int(x[1])
        else:
            x, y = int(x), int(y)
        SetCursorPos((x, y))
        MouseClick()

    click = Click

    def Press(cmd, staytime=0):
        if isinstance(cmd, list):
            cmds = [x.lower() for x in cmd]
        else:
            cmds = cmd.lower().split("+")
        for z in cmds:
            win32api.keybd_event(VK_CODE.get(z, 0), 0, 0, 0)
            time.sleep(staytime)
        for z in reversed(cmds):
            time.sleep(staytime)
            win32api.keybd_event(VK_CODE.get(z, 0), 0, win32con.KEYEVENTF_KEYUP, 0)

    press = Press

    def GetWRect(sr):
        num = int(sr[-1])
        l, u, r, b = 0, 0, getattr(scr, "size", (1920, 1080))[0], getattr(scr, "size", (1920, 1080))[1]
        if "left" in sr:
            r = l + (r - l) // num
        if "right" in sr:
            l = l + (r - l) * (num - 1) // num
        if "top" in sr:
            b = u + (b - u) // num
        if "bottom" in sr:
            u = u + (b - u) * (num - 1) // num
        return [l, u, r, b]

    def FindBlock(fn, wrect=None, verbose=0, threshold=0.8):
        tic = time.process_time()
        if wrect is not None and isinstance(wrect, Image.Image):
            scr_img, wrect = wrect, None
        else:
            scr_img = ImageGrab.grab(GetWRect(wrect) if isinstance(wrect, str) else wrect) if wrect else ImageGrab.grab()
        blc = Image.open(fn) if isinstance(fn, str) else fn
        try:
            T = cv2.cvtColor(np.array(blc), cv2.COLOR_RGB2BGR)
            B = cv2.cvtColor(np.array(scr_img), cv2.COLOR_RGB2BGR)
        except NameError:
            return (0, 0), False
        tsh, tsw = T.shape[:2]
        res = cv2.matchTemplate(B, T, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        oj, oi = max_loc
        wrect = wrect or [0, 0, scr_img.size[0], scr_img.size[1]]
        if isinstance(wrect, list):
            l, u = wrect[0], wrect[1]
        else:
            l, u = 0, 0
        obj = (oj + l + tsw // 2, oi + u + tsh // 2)
        if verbose:
            print(f"Max match: {max_val:.4f} at ({oj}, {oi}) cost: {time.process_time() - tic:.3f}s")
        return obj, max_val > threshold
