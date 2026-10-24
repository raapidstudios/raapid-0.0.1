# Contributing to Raapid

Thanks for helping improve Raapid!

## Before opening a pull request

1. Open an issue for large changes so the design can be discussed first.
2. Keep changes focused and document user-visible syntax or behavior changes.
3. Add or update a `.raap` example when changing language behavior.
4. Run the smoke tests:

   ```bash
   python main.py run test/test.raap
   python main.py run test/module_smoke.raap
   ```

5. Include your Python version, operating system, and full error output when reporting a bug.

## Scope

Raapid is experimental. Its language syntax and compiler APIs may change. Avoid committing generated build artifacts, virtual environments, caches, or local debug output.
