import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int
from Builtins import register_builtin_symbols

def initialize_llvm_jit():
    """Initializes the native target and assembly printer components required for JIT execution."""
    # Removed llvm.initialize() because it's now handled automatically!
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

def run_jit_engine(llvm_ir_str: str) -> int:
    """Compiles the LLVM IR string to machine code in memory and executes it.
    
    Returns:
        int: The native exit status return code from the compiled main function.
    """
    register_builtin_symbols(llvm)

    # 1. Parse the text IR into a live LLVM Module object
    parsed_mod = llvm.parse_assembly(llvm_ir_str)
    
    # 2. Create a target machine configuration matching your native CPU architecture
    target_machine = llvm.Target.from_default_triple().create_target_machine()
    
    # 3. Optimize and compile the live module structure down to target machine code
    backing_mod = llvm.parse_assembly("")
    execution_engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    execution_engine.add_module(parsed_mod)
    execution_engine.finalize_object()
    
    # 4. Find the memory address pointer pointing to your compiled "main" function
    func_ptr = execution_engine.get_function_address("main")
    
    # 5. Typecast the raw hardware pointer into a callable Python function signature
    c_main_function = CFUNCTYPE(c_int)(func_ptr)
    
    # 6. Execute the compiled native binary directly on your hardware chip!
    return_code = c_main_function()
    
    return return_code
