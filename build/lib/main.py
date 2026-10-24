import argparse
from pathlib import Path
import sys

import llvmlite.binding as llvm

from Compiler import Compiler
from JITcompile import initialize_llvm_jit, run_jit_engine
from Modules import ModuleLoader


def run_file(source_path: Path) -> int:
    if source_path.suffix != ".raap":
        raise ValueError("Raapid source files must use the .raap extension")
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    loaded = ModuleLoader().load(source_path)
    compiler = Compiler(loaded.builtin_modules)
    compiler.compile(loaded.program)
    compiler.module.triple = llvm.get_default_triple()
    llvm_module = llvm.parse_assembly(str(compiler.module))
    llvm_module.verify()

    initialize_llvm_jit()
    return run_jit_engine(str(llvm_module))


def main(argv: list[str] | None = None) -> int:
    argument_parser = argparse.ArgumentParser(prog="raapid", description="Run Raapid source files")
    commands = argument_parser.add_subparsers(dest="command", required=True)
    run_command = commands.add_parser("run", help="compile and run a .raap file")
    run_command.add_argument("file", type=Path, help="path to a .raap source file")
    arguments = argument_parser.parse_args(argv)

    try:
        exit_code = run_file(arguments.file)
    except Exception as error:
        print(f"raapid: {error}", file=sys.stderr)
        return 1
    print(f"Program exited natively with code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())