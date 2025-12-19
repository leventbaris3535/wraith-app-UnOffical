import sys
import win32gui
import win32con
import win32process


def find_window_by_pid(pid):
    result = []

    def enum_cb(hwnd, _):
        if not win32gui.IsWindow(hwnd):
            return

        _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
        if win_pid != pid:
            return

        # Child / tool window'ları ele
        if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
            return

        result.append(hwnd)

    win32gui.EnumWindows(enum_cb, None)
    return result[0] if result else None


def hide_window(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)


def show_window(hwnd):
    # restore + show
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

    try:
        win32gui.SetForegroundWindow(hwnd)
    except:
        pass


def main():
    if len(sys.argv) != 3:
        print("usage: winctl.exe hide|show <pid>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    pid = int(sys.argv[2])

    hwnd = find_window_by_pid(pid)

    if not hwnd:
        print("HWND NOT FOUND")
        sys.exit(2)

    if cmd == "hide":
        hide_window(hwnd)
        print(f"HIDDEN hwnd={hwnd}")

    elif cmd == "show":
        show_window(hwnd)
        print(f"SHOWN hwnd={hwnd}")

    else:
        print("invalid command")
        sys.exit(3)


if __name__ == "__main__":
    main()
