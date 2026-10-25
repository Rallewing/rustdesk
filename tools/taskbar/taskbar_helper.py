"""Windows taskbar switch for Ralf PC Remote; no network service or admin rights."""
import sys

AUTOHIDE = 1


class TaskbarController:
    def __init__(self, shell):
        self.shell = shell
        self.initial_state = shell.get_state()

    def toggle(self):
        state = self.shell.get_state() ^ AUTOHIDE
        if state & AUTOHIDE:
            self.shell.move_pointer_inside()
        self.shell.set_state(state)
        return bool(self.shell.get_state() & AUTOHIDE)

    def restore(self):
        self.shell.set_state(self.initial_state)


def main():
    if sys.platform != 'win32':
        raise SystemExit('Dieser Helfer laeuft auf dem Windows-PC, nicht auf dem Handy.')
    import ctypes
    from ctypes import wintypes as w
    import tkinter as tk
    from tkinter import messagebox

    class APPBARDATA(ctypes.Structure):
        _fields_ = [('cbSize', w.DWORD), ('hWnd', w.HWND),
                    ('uCallbackMessage', w.UINT), ('uEdge', w.UINT),
                    ('rc', w.RECT), ('lParam', w.LPARAM)]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [('cbSize', w.DWORD), ('rcMonitor', w.RECT),
                    ('rcWork', w.RECT), ('dwFlags', w.DWORD)]

    user = ctypes.WinDLL('user32', use_last_error=True)
    shell32 = ctypes.WinDLL('shell32', use_last_error=True)
    user.FindWindowW.argtypes = [w.LPCWSTR, w.LPCWSTR]
    user.FindWindowW.restype = w.HWND
    user.RegisterHotKey.argtypes = [w.HWND, ctypes.c_int, w.UINT, w.UINT]
    user.RegisterHotKey.restype = w.BOOL
    user.UnregisterHotKey.argtypes = [w.HWND, ctypes.c_int]
    user.UnregisterHotKey.restype = w.BOOL
    user.GetCursorPos.argtypes = [ctypes.POINTER(w.POINT)]
    user.GetCursorPos.restype = w.BOOL
    user.MonitorFromPoint.argtypes = [w.POINT, w.DWORD]
    user.MonitorFromPoint.restype = w.HANDLE
    user.GetMonitorInfoW.argtypes = [w.HANDLE, ctypes.POINTER(MONITORINFO)]
    user.GetMonitorInfoW.restype = w.BOOL
    user.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user.SetCursorPos.restype = w.BOOL
    shell32.SHAppBarMessage.argtypes = [w.DWORD, ctypes.POINTER(APPBARDATA)]
    shell32.SHAppBarMessage.restype = ctypes.c_size_t

    class WindowsShell:
        def data(self):
            hwnd = user.FindWindowW('Shell_TrayWnd', None)
            if not hwnd:
                raise RuntimeError('Die Windows-Taskleiste wurde nicht gefunden.')
            data = APPBARDATA()
            data.cbSize = ctypes.sizeof(data)
            data.hWnd = hwnd
            return data

        def get_state(self):
            return int(shell32.SHAppBarMessage(4, ctypes.byref(self.data())))

        def set_state(self, state):
            data = self.data()
            data.lParam = state
            shell32.SHAppBarMessage(10, ctypes.byref(data))
            if (self.get_state() & AUTOHIDE) != (state & AUTOHIDE):
                raise RuntimeError('Windows hat die Taskleisten-Einstellung nicht uebernommen.')

        def move_pointer_inside(self):
            point = w.POINT()
            if not user.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())
            monitor = user.MonitorFromPoint(point, 2)
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(info)
            if not user.GetMonitorInfoW(monitor, ctypes.byref(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            r = info.rcWork
            if not user.SetCursorPos((r.left + r.right) // 2, (r.top + r.bottom) // 2):
                raise ctypes.WinError(ctypes.get_last_error())

    root = tk.Tk()
    root.title('Ralf PC Remote - Taskleisten-Helfer')
    root.geometry('460x190')
    root.resizable(False, False)
    root.update_idletasks()
    hwnd = root.winfo_id()
    if not user.RegisterHotKey(hwnd, 0x5241, 0x4007, 0x7A):
        messagebox.showerror('Helfer nicht gestartet',
                            'Der Helfer laeuft bereits oder Strg+Alt+Umschalt+F11 ist belegt.')
        root.destroy()
        return
    controller = None
    previous_proc = None
    set_proc = getattr(user, 'SetWindowLongPtrW', user.SetWindowLongW)
    set_proc.argtypes = [w.HWND, ctypes.c_int, ctypes.c_void_p]
    set_proc.restype = ctypes.c_void_p
    user.CallWindowProcW.argtypes = [ctypes.c_void_p, w.HWND, w.UINT, w.WPARAM, w.LPARAM]
    user.CallWindowProcW.restype = ctypes.c_ssize_t
    try:
        controller = TaskbarController(WindowsShell())
        status = tk.StringVar(value='Bereit. In der Handy-App auf Taskleiste tippen.')
        tk.Label(root, textvariable=status, wraplength=430, pady=15).pack()

        def toggle():
            try:
                hidden = controller.toggle()
                status.set('Taskleiste: automatisch ausblenden' if hidden else 'Taskleiste: dauerhaft eingeblendet')
            except Exception as exc:
                messagebox.showerror('Taskleiste konnte nicht umgeschaltet werden', str(exc))

        wndproc_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, w.HWND, w.UINT, w.WPARAM, w.LPARAM)

        @wndproc_type
        def window_proc(window, message, wparam, lparam):
            if message == 0x0312 and wparam == 0x5241:
                toggle()
                return 0
            return user.CallWindowProcW(previous_proc, window, message, wparam, lparam)

        ctypes.set_last_error(0)
        previous_proc = set_proc(hwnd, -4, ctypes.cast(window_proc, ctypes.c_void_p))
        if not previous_proc:
            raise ctypes.WinError(ctypes.get_last_error())
        tk.Button(root, text='Taskleiste hier testen', command=toggle).pack(pady=5)
        tk.Button(root, text='Beenden und vorherige Einstellung wiederherstellen', command=root.quit).pack(pady=5)
        root.protocol('WM_DELETE_WINDOW', root.quit)
        root.mainloop()
    finally:
        user.UnregisterHotKey(hwnd, 0x5241)
        if previous_proc:
            set_proc(hwnd, -4, previous_proc)
        if controller is not None:
            try:
                controller.restore()
            except Exception as exc:
                messagebox.showerror('Wiederherstellung fehlgeschlagen', str(exc))
        root.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if sys.platform == 'win32':
            from tkinter import messagebox
            messagebox.showerror('Taskleisten-Helfer konnte nicht starten', str(exc))
        else:
            raise
