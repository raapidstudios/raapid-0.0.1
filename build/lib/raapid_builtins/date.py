from ctypes import CFUNCTYPE, c_void_p
from datetime import date

from . import retained_string


FUNCTIONS = {
    "today": ("char_ptr", ()),
}


def _today() -> int:
    return retained_string(date.today().isoformat())


CALLBACKS = {
    "today": CFUNCTYPE(c_void_p)(_today),
}
