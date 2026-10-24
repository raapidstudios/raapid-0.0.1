from ctypes import c_char_p, c_void_p, cast
from importlib import import_module
from pkgutil import iter_modules
from typing import Any


_string_results: list[bytes] = []


def retained_string(value: str) -> int:
    result = value.encode("ascii")
    _string_results.append(result)
    return cast(c_char_p(result), c_void_p).value or 0


BUILTIN_FUNCTIONS: dict[str, dict[str, tuple[str, tuple[str, ...]]]] = {}
_callbacks: dict[str, Any] = {}

for module_info in sorted(iter_modules(__path__), key=lambda info: info.name):
    if module_info.name.startswith("_"):
        continue
    builtin_module = import_module(f"{__name__}.{module_info.name}")
    functions = builtin_module.FUNCTIONS
    callbacks = builtin_module.CALLBACKS
    if functions.keys() != callbacks.keys():
        raise ValueError(f"Built-in module '{module_info.name}' must define a callback for each function")
    BUILTIN_FUNCTIONS[module_info.name] = functions
    _callbacks.update(
        {
            f"__raapid_builtin_{module_info.name}_{function_name}": callback
            for function_name, callback in callbacks.items()
        }
    )

BUILTIN_MODULES = set(BUILTIN_FUNCTIONS)


def register_builtin_symbols(llvm: Any) -> None:
    for symbol, callback in _callbacks.items():
        llvm.add_symbol(symbol, cast(callback, c_void_p).value)
