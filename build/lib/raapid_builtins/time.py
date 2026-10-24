from ctypes import CFUNCTYPE, c_float, c_void_p
import time as _time

from . import retained_string


FUNCTIONS = {
    "now": ("char_ptr", ()),
    "sleep": ("void", ("float",)),
}


def _now() -> int:
    return retained_string(_time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime()))


CALLBACKS = {
    "now": CFUNCTYPE(c_void_p)(_now),
    "sleep": CFUNCTYPE(None, c_float)(_time.sleep),
}
