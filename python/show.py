import time
import win32gui
import win32process
import win32api

print("⏳ 3 saniye içinde istediğin pencereye TIKLA...")

time.sleep(3)

# Mouse pozisyonu
x, y = win32api.GetCursorPos()

# O noktadaki pencere
hwnd = win32gui.WindowFromPoint((x, y))

# PID al
_, pid = win32process.GetWindowThreadProcessId(hwnd)

title = win32gui.GetWindowText(hwnd)
cls = win32gui.GetClassName(hwnd)

print("\n✅ TIKLANAN PENCERE")
print(f"HWND : {hwnd}")
print(f"PID  : {pid}")
print(f"TITLE: {title}")
print(f"CLASS: {cls}")
