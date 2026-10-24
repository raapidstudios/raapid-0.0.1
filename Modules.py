from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path

import AST
from Lexer import Lexer
from Parser import Parser
from raapid_builtins import BUILTIN_FUNCTIONS, BUILTIN_MODULES


@dataclass
class ModuleExports:
    functions: dict[str, str]
    module_name: str | None = None


@dataclass
class LoadedProgram:
    program: AST.Program
    builtin_modules: set[str]


class ModuleLoadError(Exception):
    pass


class ModuleLoader:
    def __init__(self) -> None:
        self._cache: dict[Path, ModuleExports] = {}
        self._active: set[Path] = set()
        self._module_functions: list[AST.FunctionStatement] = []
        self._builtin_modules: set[str] = set()

    def load(self, entry_path: Path) -> LoadedProgram:
        program = self._parse_file(entry_path)
        aliases = self._resolve_imports(program.statements, entry_path.parent)
        local_functions = {
            statement.name: statement.name
            for statement in program.statements
            if isinstance(statement, AST.FunctionStatement)
        }
        for statement in program.statements:
            if not isinstance(statement, AST.ImportStatement):
                self._rewrite_statement(statement, local_functions, aliases)

        program.statements = [
            *self._module_functions,
            *(statement for statement in program.statements if not isinstance(statement, AST.ImportStatement)),
        ]
        return LoadedProgram(program, self._builtin_modules)

    def _parse_file(self, path: Path) -> AST.Program:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ModuleLoadError(f"Cannot read module '{path}': {error}") from error
        parser = Parser(Lexer(source))
        program = parser.parse_program()
        if parser.errors:
            errors = "\n".join(parser.errors)
            raise ModuleLoadError(f"Parse errors in '{path}':\n{errors}")
        return program

    def _resolve_imports(self, statements: list[AST.Statement], relative_to: Path) -> dict[str, tuple[str, ModuleExports]]:
        aliases: dict[str, tuple[str, ModuleExports]] = {}
        for statement in statements:
            if not isinstance(statement, AST.ImportStatement):
                continue
            module_name = statement.module_name
            if module_name in BUILTIN_MODULES:
                alias = statement.alias or module_name
                if alias in aliases:
                    raise ModuleLoadError(f"Duplicate module alias: {alias}")
                aliases[alias] = ("builtin", ModuleExports({}, module_name))
                self._builtin_modules.add(module_name)
                continue

            module_path = Path(module_name)
            if module_path.suffix and module_path.suffix != ".raap":
                raise ModuleLoadError(f"Module files must use the .raap extension: {module_name}")
            if not module_path.suffix:
                module_path = module_path.with_suffix(".raap")
            resolved_path = (relative_to / module_path).resolve()
            exports = self._load_source_module(resolved_path)
            alias = statement.alias or module_path.stem
            if alias in aliases:
                raise ModuleLoadError(f"Duplicate module alias: {alias}")
            aliases[alias] = ("source", exports)
        return aliases

    def _load_source_module(self, path: Path) -> ModuleExports:
        if path in self._active:
            raise ModuleLoadError(f"Circular module import detected: {path}")
        cached = self._cache.get(path)
        if cached is not None:
            return cached

        self._active.add(path)
        try:
            program = self._parse_file(path)
            for statement in program.statements:
                if not isinstance(statement, (AST.FunctionStatement, AST.ImportStatement)):
                    raise ModuleLoadError(f"Imported module '{path}' may only contain imports and function declarations")

            aliases = self._resolve_imports(program.statements, path.parent)
            functions = [statement for statement in program.statements if isinstance(statement, AST.FunctionStatement)]
            prefix = "__raapid_" + sha1(str(path).encode("utf-8")).hexdigest()[:10] + "_"
            exports = ModuleExports({function.name: prefix + function.name for function in functions})
            self._cache[path] = exports

            for function in functions:
                function.name = exports.functions[function.name]
                self._rewrite_block(function.body, exports.functions, aliases)
                self._module_functions.append(function)
            return exports
        finally:
            self._active.remove(path)

    def _rewrite_block(self, block: AST.BlockStatement, local_functions: dict[str, str], aliases: dict[str, tuple[str, ModuleExports]]) -> None:
        for statement in block.statements:
            self._rewrite_statement(statement, local_functions, aliases)

    def _rewrite_statement(self, statement: AST.Statement, local_functions: dict[str, str], aliases: dict[str, tuple[str, ModuleExports]]) -> None:
        if isinstance(statement, AST.FunctionStatement):
            self._rewrite_block(statement.body, local_functions, aliases)
        elif isinstance(statement, AST.BlockStatement):
            self._rewrite_block(statement, local_functions, aliases)
        elif isinstance(statement, AST.SayStatement):
            statement.expressions = [self._rewrite_expression(expression, local_functions, aliases) for expression in statement.expressions]
            statement.expression = statement.expressions[0] if statement.expressions else None
        elif isinstance(statement, (AST.LetStatement, AST.MakeStatement)):
            statement.value = self._rewrite_expression(statement.value, local_functions, aliases)
        elif isinstance(statement, AST.SetStatement):
            statement.target = self._rewrite_expression(statement.target, local_functions, aliases)
            statement.value = self._rewrite_expression(statement.value, local_functions, aliases)
        elif isinstance(statement, AST.AskStatement):
            statement.prompt = self._rewrite_expression(statement.prompt, local_functions, aliases)
        elif isinstance(statement, AST.ExpressionStatement):
            statement.expression = self._rewrite_expression(statement.expression, local_functions, aliases)
        elif isinstance(statement, (AST.ReturnStatement, AST.GiveStatement, AST.ReturningStatement)):
            if statement.value is not None:
                statement.value = self._rewrite_expression(statement.value, local_functions, aliases)
        elif isinstance(statement, AST.IfStatement):
            statement.condition = self._rewrite_expression(statement.condition, local_functions, aliases)
            self._rewrite_block(statement.consequence, local_functions, aliases)
            if isinstance(statement.alternative, AST.BlockStatement):
                self._rewrite_block(statement.alternative, local_functions, aliases)
            elif isinstance(statement.alternative, AST.IfStatement):
                self._rewrite_statement(statement.alternative, local_functions, aliases)
        elif isinstance(statement, AST.WhileStatement):
            statement.condition = self._rewrite_expression(statement.condition, local_functions, aliases)
            self._rewrite_block(statement.body, local_functions, aliases)
        elif isinstance(statement, AST.ForStatement):
            for field in ("start", "end", "iterable"):
                expression = getattr(statement, field)
                if expression is not None:
                    setattr(statement, field, self._rewrite_expression(expression, local_functions, aliases))
            self._rewrite_block(statement.body, local_functions, aliases)
        elif isinstance(statement, AST.RepeatStatement):
            statement.count = self._rewrite_expression(statement.count, local_functions, aliases)
            self._rewrite_block(statement.body, local_functions, aliases)

    def _rewrite_expression(self, expression: AST.Expression, local_functions: dict[str, str], aliases: dict[str, tuple[str, ModuleExports]]) -> AST.Expression:
        if isinstance(expression, AST.CallExpression):
            if isinstance(expression.function, AST.Identifier):
                expression.function.value = local_functions.get(expression.function.value, expression.function.value)
            elif isinstance(expression.function, AST.MemberExpression) and isinstance(expression.function.target, AST.Identifier):
                alias = expression.function.target.value
                imported = aliases.get(alias)
                if imported is None:
                    raise ModuleLoadError(f"Module alias '{alias}' was not imported")
                module_kind, exports = imported
                if module_kind == "builtin":
                    module_name = exports.module_name
                    if module_name is None:
                        raise ModuleLoadError(f"Cannot resolve built-in module alias '{alias}'")
                    if expression.function.member not in BUILTIN_FUNCTIONS[module_name]:
                        raise ModuleLoadError(
                            f"Built-in module '{module_name}' does not export function "
                            f"'{expression.function.member}'"
                        )
                    expression.function = AST.Identifier(f"__raapid_builtin_{module_name}_{expression.function.member}")
                else:
                    function_name = exports.functions.get(expression.function.member)
                    if function_name is None:
                        raise ModuleLoadError(f"Module '{alias}' does not export function '{expression.function.member}'")
                    expression.function = AST.Identifier(function_name)
            expression.arguments = [self._rewrite_expression(argument, local_functions, aliases) for argument in expression.arguments]
            return expression
        if isinstance(expression, AST.InfixExpression):
            expression.left_node = self._rewrite_expression(expression.left_node, local_functions, aliases)
            expression.right_node = self._rewrite_expression(expression.right_node, local_functions, aliases)
        elif isinstance(expression, AST.PrefixExpression):
            expression.right = self._rewrite_expression(expression.right, local_functions, aliases)
        elif isinstance(expression, AST.ArrayLiteral):
            expression.elements = [self._rewrite_expression(element, local_functions, aliases) for element in expression.elements]
        elif isinstance(expression, AST.IndexExpression):
            expression.array = self._rewrite_expression(expression.array, local_functions, aliases)
            expression.index = self._rewrite_expression(expression.index, local_functions, aliases)
        return expression
