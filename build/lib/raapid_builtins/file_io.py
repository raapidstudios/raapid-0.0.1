from ctypes import CFUNCTYPE, c_char_p, c_int, c_void_p
import os

from . import retained_string

# 1. Define the LLVM function signatures for your compiler
FUNCTIONS = {
    "read_file": ("char_ptr", ("char_ptr",)),
    "write_file": ("int", ("char_ptr", "char_ptr")),
    "delete_file": ("int", ("char_ptr",)),
}

# 2. Python backend implementations
def _read_file(path_ptr: bytes) -> int:
    """Reads a file and returns a retained string pointer for your JIT."""
    # ctypes provides the string as raw bytes, decode it to use in Python
    file_path = path_ptr.decode('utf-8')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return retained_string(content)
    except Exception:
        # Return an empty string or error layout based on your language's style
        return retained_string("")

def _write_file(path_ptr: bytes, content_ptr: bytes) -> int:
    """Writes text to a file. Returns 1 on success, 0 on failure."""
    file_path = path_ptr.decode('utf-8')
    content = content_ptr.decode('utf-8')
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1  # Success
    except Exception:
        return 0  # Failure

def _delete_file(path_ptr: bytes) -> int:
    """Removes a file from disk. Returns 1 on success, 0 on failure."""
    file_path = path_ptr.decode('utf-8')
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return 1
        return 0
    except Exception:
        return 0

# 3. Expose the native memory callbacks for your LLVM JIT engine
CALLBACKS = {
    # c_char_p automatically converts incoming LLVM i8* pointers to Python bytes
    "read_file": CFUNCTYPE(c_void_p, c_char_p)(_read_file),
    "write_file": CFUNCTYPE(c_int, c_char_p, c_char_p)(_write_file),
    "delete_file": CFUNCTYPE(c_int, c_char_p)(_delete_file),
}
