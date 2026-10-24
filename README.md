# Raapid

**Raapid 0.0.1** is an early, experimental programming language compiled to LLVM IR and executed with an in-process JIT.

> **Status:** Pre-release / experimental. Syntax and APIs may change between releases. Do not use it for untrusted programs.

## Requirements

- Python 3.11 or newer
- `llvmlite` 0.50 or newer (installed automatically by pip)

LLVM-backed execution depends on the supported Python and `llvmlite` combination for your platform.

## Install from source

From the project directory:

```bash
python -m pip install .
```

This installs the `raapid` command in the active Python environment. For development, use an editable install:

```bash
python -m pip install -e .
```

## Run a program

```bash
raapid run test/test.raap
```

Or, without installing the command:

```bash
python main.py run test/test.raap
```

Raapid source files must use the `.raap` extension. The command accepts a path to the source file:

```bash
raapid run path/to/program.raap
```

## Source modules

An imported `.raap` file may contain function declarations and imports. Imports are resolved relative to the importing file. Use an explicit alias or the file's name without its extension:

```text
import "math_helpers.raap" as helpers

say helpers.double(21)
```

Imported functions need typed parameters, and functions that return a value need a return type:

```text
function double(value: int) returning int {
    return value * 2
}
```

## Built-in modules

Built-in modules are implemented as separate Python modules in the
`raapid_builtins` package. Add a module there with `FUNCTIONS` declarations and
matching `CALLBACKS`; the package discovers these modules automatically, so
they become available to Raapid imports without editing a central module list.

```text
import random
import time
import date

say random.randint(1, 6)
say random.random()
say time.now()
time.sleep(0.25)
say date.today()
```

- `time.now()` returns the local date and time as `YYYY-MM-DD HH:MM:SS`.
- `date.today()` returns the local date in ISO format.

## Development smoke tests

Run the small no-input example:

```bash
python main.py run test/test.raap
```

Run the module/import example:

```bash
python main.py run test/module_smoke.raap
```

`test/hello.raap` is a larger interactive example and asks for input.

## Contributing

Issues and pull requests are welcome. Please include a minimal `.raap` reproduction for bugs and test changes against existing examples. See `CONTRIBUTING.md`.

## License

Raapid is distributed under the MIT License. See `LICENSE`.
