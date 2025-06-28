# Utility functions for monitor detection without external dependencies.
import sys
import subprocess
import ctypes


class Monitor:
    """Simple representation of a display monitor."""

    def __init__(self, width, height, x=0, y=0, name=""):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.name = name or f"{x},{y}"  # fallback name

    def __repr__(self):
        return f"Monitor(name={self.name!r}, width={self.width}, height={self.height}, x={self.x}, y={self.y})"


def _monitors_windows():
    monitors = []
    user32 = ctypes.windll.user32
    MONITORINFOF_PRIMARY = 1

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    class MONITORINFOEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        ctypes.c_double,
    )

    def callback(hMonitor, _hdcMonitor, _lprcMonitor, _dwData):
        info = MONITORINFOEX()
        info.cbSize = ctypes.sizeof(MONITORINFOEX)
        user32.GetMonitorInfoW(hMonitor, ctypes.byref(info))
        monitors.append(
            Monitor(
                width=info.rcMonitor.right - info.rcMonitor.left,
                height=info.rcMonitor.bottom - info.rcMonitor.top,
                x=info.rcMonitor.left,
                y=info.rcMonitor.top,
                name=info.szDevice,
            )
        )
        return 1

    if not user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(callback), 0):
        return []
    return monitors


def _monitors_darwin():
    monitors = []
    try:
        quartz = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    except OSError:
        return monitors

    CGMainDisplayID = quartz.CGMainDisplayID
    CGGetActiveDisplayList = quartz.CGGetActiveDisplayList
    CGDisplayBounds = quartz.CGDisplayBounds

    CGGetActiveDisplayList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
    CGDisplayBounds.argtypes = [ctypes.c_uint32]
    CGDisplayBounds.restype = ctypes.c_void_p

    max_displays = 16
    active_displays = (ctypes.c_uint32 * max_displays)()
    display_count = ctypes.c_uint32(0)
    if CGGetActiveDisplayList(max_displays, active_displays, ctypes.byref(display_count)) != 0:
        return monitors

    class CGRect(ctypes.Structure):
        _fields_ = [("origin_x", ctypes.c_double), ("origin_y", ctypes.c_double), ("size_w", ctypes.c_double), ("size_h", ctypes.c_double)]

    for i in range(display_count.value):
        did = active_displays[i]
        rect_ptr = ctypes.cast(CGDisplayBounds(did), ctypes.POINTER(CGRect))
        rect = rect_ptr.contents
        monitors.append(Monitor(int(rect.size_w), int(rect.size_h), int(rect.origin_x), int(rect.origin_y), name=str(did)))
    return monitors


def _monitors_linux():
    monitors = []
    try:
        output = subprocess.check_output(["xrandr", "--listmonitors"], stderr=subprocess.DEVNULL, text=True)
    except Exception:
        return monitors
    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4 and parts[1].startswith("+"):  # lines like "0: +*eDP-1 1920/..+0+0 eDP-1"
            name = parts[-1]
            geometry = parts[2]
            size, position = geometry.split("+", 1)
            width, height = size.split("x")
            x, y = position.split("+")
            monitors.append(Monitor(int(width), int(height), int(x), int(y), name=name))
    return monitors


def enumerate_monitors(root):
    """Return list of monitors using best effort without external packages."""
    monitors = []
    if sys.platform.startswith("win"):
        monitors = _monitors_windows()
    elif sys.platform == "darwin":
        monitors = _monitors_darwin()
    else:
        monitors = _monitors_linux()

    if not monitors:
        monitors = [Monitor(root.winfo_screenwidth(), root.winfo_screenheight(), 0, 0, name="Default")]
    return monitors

