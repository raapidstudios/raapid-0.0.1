from ctypes import CFUNCTYPE, c_float, c_int
import random as _random


FUNCTIONS = {
    "randint": ("int", ("int", "int")),
    "random": ("float", ()),
}


CALLBACKS = {
    "randint": CFUNCTYPE(c_int, c_int, c_int)(_random.randint),
    "random": CFUNCTYPE(c_float)(_random.random),
}
