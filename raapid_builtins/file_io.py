from ctypes import CFUNCTYPE, c_char_p, c_int, c_void_p
import os

from . import retained_string

FUNCTIONS = {
    "read_file": ("char_ptr", ("char_ptr",)),
    "write_file": ("int", ("char_ptr", "char_ptr")),
    "delete_file": ("int", ("char_ptr",)),
}

def _read_file(path_ptr: bytes) -> int:
    try:
        file_path = path_ptr.decode('utf-8')
        with open(file_path, 'r', encoding='utf-8') as f:
            return retained_string(f.read())
    except Exception:
        return retained_string("")

def _write_file(path_ptr: bytes, content_ptr: bytes) -> int:
    try:
        file_path = path_ptr.decode('utf-8')
        content = content_ptr.decode('utf-8')
        
        # Auto-create parent folders (like 'test/') if they don't exist yet
        dirname = os.path.dirname(file_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1  # Success
    except Exception:
        return 0  # Failure

def _delete_file(path_ptr: bytes) -> int:
    try:
        file_path = path_ptr.decode('utf-8')
        if os.path.exists(file_path):
            os.remove(file_path)
            return 1
        return 0
    except Exception:
        return 0

CALLBACKS = {
    "read_file": CFUNCTYPE(c_void_p, c_char_p)(_read_file),
    "write_file": CFUNCTYPE(c_int, c_char_p, c_char_p)(_write_file),
    "delete_file": CFUNCTYPE(c_int, c_char_p)(_delete_file),
}
