"""Operações Win32 restritas às janelas dos processos iniciados pelo app."""
import ctypes
from ctypes import wintypes


user32 = ctypes.windll.user32
user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
user32.MonitorFromPoint.restype = wintypes.HANDLE
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsIconic.argtypes = [wintypes.HWND]


class ProcessEntry(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD),
                ("pid", wintypes.DWORD), ("heap", ctypes.c_size_t),
                ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
                ("parent", wintypes.DWORD), ("priority", wintypes.LONG),
                ("flags", wintypes.DWORD), ("exe", wintypes.WCHAR * 260)]


def process_family(pid):
    kernel = ctypes.windll.kernel32
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return {pid}
    parents = {}
    entry = ProcessEntry()
    entry.size = ctypes.sizeof(entry)
    try:
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            parents[entry.pid] = entry.parent
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    family = {pid}
    while True:
        children = {child for child, parent in parents.items() if parent in family}
        if children <= family:
            return family
        family.update(children)


class MonitorInfo(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                ("work", wintypes.RECT), ("flags", wintypes.DWORD)]


def work_area(x=None, y=None, scale=1):
    point = wintypes.POINT(int((x or 0) * scale), int((y or 0) * scale))
    monitor = user32.MonitorFromPoint(point, 2)
    info = MonitorInfo()
    info.size = ctypes.sizeof(info)
    user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return 0, 0, 1280, 720
    return tuple(int(value / scale) for value in
                 (info.work.left, info.work.top, info.work.right, info.work.bottom))


def fit_bounds(x, y, width, height, scale=1):
    left, top, right, bottom = work_area(x, y, scale)
    width, height = min(width, right - left), min(height, bottom - top)
    x = left + (right - left - width) // 2 if x is None else x
    y = top + 40 if y is None else y
    return max(left, min(x, right - width)), max(top, min(y, bottom - height)), width, height


def focus_process(pid):
    handles = []
    family = process_family(pid)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def inspect(handle, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value in family and user32.IsWindowVisible(handle):
            handles.append(handle)
        return True

    user32.EnumWindows(inspect, 0)
    if not handles:
        return False
    handle = handles[0]
    if user32.IsIconic(handle):
        user32.ShowWindow(handle, 9)
    return bool(user32.SetForegroundWindow(handle)) or user32.GetForegroundWindow() == handle


def show_error(title, message):
    user32.MessageBoxW(None, message, title, 0x10)
