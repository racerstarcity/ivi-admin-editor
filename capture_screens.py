import ctypes, win32gui, win32con, time, os, subprocess
from PIL import ImageGrab

os.system("taskkill /f /im ivi_meta.exe 2>nul")
time.sleep(1)

proc = subprocess.Popen(["dist\\ivi_meta.exe"])
time.sleep(5)

# Capture main window
hwnd = win32gui.FindWindow(None, "ИВИ")
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 100, 100, 540, 580, win32con.SWP_SHOWWINDOW)
time.sleep(2)

def capture(title, outpath):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        return
    rect = win32gui.GetWindowRect(hwnd)
    full = ImageGrab.grab()
    x, y, x2, y2 = rect
    if x < 0: x = 0
    if y < 0: y = 0
    crop = full.crop((x, y, min(x2, full.width), min(y2, full.height)))
    avg = sum(crop.getextrema()[0]) / 255
    print(f"  {title}: {crop.size} bright={avg:.2f}")
    if avg > 0.05:
        crop.save(outpath)

capture("ИВИ", "dist\\screenshot_main.png")

# Open markers by clicking Метки button
rect = win32gui.GetWindowRect(hwnd)
ctypes.windll.user32.SetCursorPos(rect[0] + 440, rect[3] - 25)
ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
time.sleep(3)

capture("Метки", "dist\\screenshot_markers.png")

time.sleep(0.5)
proc.kill()
