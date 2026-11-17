"""Let Windows Setup detect a running service before replacing its files."""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import os

MUTEX = r'Local\RoleWeaver.ModuleStudio.Service'


@contextmanager
def service_lock(port=8766):
    if os.name != 'nt':
        yield
        return
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateMutexW
    create.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    name = MUTEX if port == 8766 else MUTEX+'.'+str(port)
    ctypes.set_last_error(0)
    handle = create(None, False, name)
    if not handle:
        raise OSError('Could not establish the Role Weaver service installation lock.')
    try:
        if ctypes.get_last_error() == 183:
            raise ValueError('Role Weaver is already running. Open its dashboard or close its service window first.')
        yield
    finally:
        close(handle)
