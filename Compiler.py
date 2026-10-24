from llvmlite import ir
import AST
from raapid_builtins import BUILTIN_FUNCTIONS

class Compiler:
    def __init__(self, builtin_modules: set[str] | None = None):
        self.type_map: dict[str, ir.Type] = {
            "int": ir.IntType(32),
            "bool": ir.IntType(1),
            "boolean": ir.IntType(1),
            "float": ir.FloatType(),
            "void": ir.VoidType(),
            "string": ir.PointerType(ir.IntType(8)),
            "char_ptr": ir.PointerType(ir.IntType(8))
        }
        self.module: ir.Module = ir.Module("Raapid")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.symbols: dict[str, tuple[ir.AllocaInstr, ir.Type]] = {}
        self.str_count: int = 0
        self.say_count: int = 0
        self.functions: dict[str, ir.Function] = {}
        self.function_nodes: dict[str, AST.FunctionStatement] = {}
        self.function_parameter_types: dict[str, list[str]] = {}
        self.function_return_types: dict[str, str] = {}
        self.current_return_type: ir.Type | None = None
        self.builtin_modules = builtin_modules or set()
        
        printf_ty = ir.FunctionType(ir.IntType(32), [self.type_map["char_ptr"]], var_arg=True)
        scanf_ty = ir.FunctionType(ir.IntType(32), [self.type_map["char_ptr"]], var_arg=True)
        self.printf_func = ir.Function(self.module, printf_ty, name="printf")
        self.scanf_func = ir.Function(self.module, scanf_ty, name="scanf")
        strcmp_ty = ir.FunctionType(ir.IntType(32), [self.type_map["char_ptr"], self.type_map["char_ptr"]])
        self.strcmp_func = ir.Function(self.module, strcmp_ty, name="strcmp")
        strncpy_ty = ir.FunctionType(self.type_map["char_ptr"], [self.type_map["char_ptr"], self.type_map["char_ptr"], ir.IntType(64)])
        self.strncpy_func = ir.Function(self.module, strncpy_ty, name="strncpy")

        
        self.int_format = self._make_global_string("int_fmt", "%d\n\0")
        self.float_format = self._make_global_string("float_fmt", "%f\n\0")
        self.str_format = self._make_global_string("str_fmt", "%s\n\0")
        self.bool_format = self._make_global_string("bool_fmt", "%s\n\0")
        self.p_format = self._make_global_string("p_fmt", "%p\n\0")
        
        self.true_string = self._make_global_string("true_str", "true\0")
        self.false_string = self._make_global_string("false_str", "false\0")

    def _make_global_string(self, name: str, value: str) -> ir.GlobalVariable:
        typ = ir.ArrayType(ir.IntType(8), len(value))
        global_var = ir.GlobalVariable(self.module, typ, name=name)
        global_var.initializer = ir.Constant(typ, bytearray(value.encode("utf8")))
        global_var.global_constant = True
        return global_var

    def compile(self, node: AST.Node) -> ir.Value | tuple[ir.Value, ir.Type] | None:
        if node is None:
            return None
        match node.type():
            case AST.NodeType.Program:
                self.visit_program(node)
            case AST.NodeType.ExpressionStatement:
                self.visit_expression_statement(node)
            case AST.NodeType.LetStatement:
                self.visit_let_statement(node)
            case AST.NodeType.SayStatement:
                self.visit_say_statement(node)
            case AST.NodeType.SetStatement:
                self.visit_set_statement(node)
            case AST.NodeType.FunctionStatement:
                self.visit_function_statement(node)
            case AST.NodeType.ReturnStatement:
                self.visit_return_statement(node)
            case AST.NodeType.AskStatement:
                self.visit_ask_statement(node)
            case AST.NodeType.IfStatement:
                self.visit_if_statement(node)
            case AST.NodeType.WhileStatement:
                self.visit_while_statement(node)
            case AST.NodeType.ForStatement:
                self.visit_for_statement(node)
            case AST.NodeType.RepeatStatement:
                self.visit_repeat_statement(node)
            case AST.NodeType.MakeStatement:
                self.visit_make_statement(node)
            case AST.NodeType.GiveStatement:
                self.visit_give_statement(node)
            case AST.NodeType.ReturningStatement:
                self.visit_returning_statement(node)
            case AST.NodeType.InfixExpression:
                return self.visit_infix_expression(node)
            case AST.NodeType.CallExpression:
                return self.visit_call_expression(node)
            case AST.NodeType.Identifier:
                return self.visit_identifier(node)
            case AST.NodeType.AddressOfExpression:
                return self.visit_address_of(node)
            case AST.NodeType.ValueAtExpression:
                return self.visit_value_at(node)
            case AST.NodeType.ArrayLiteral | AST.NodeType.IndexExpression:
                return self.resolve_value(node)
        return None

    def visit_program(self, node: AST.Program) -> None:
        self._declare_builtin_functions()
        function_nodes = [statement for statement in node.statements if isinstance(statement, AST.FunctionStatement)]
        self._infer_function_signatures(function_nodes)
        for statement in function_nodes:
            self._declare_function(statement)

        func_name: str = "main"
        param_types: list[ir.Type] = []
        return_type: ir.Type = self.type_map["int"]
        func_type = ir.FunctionType(return_type, param_types)
        main_func = ir.Function(self.module, func_type, name=func_name)
        block = main_func.append_basic_block(f"{func_name}_entry")
        self.builder = ir.IRBuilder(block)
        for stmt in node.statements:
            self.compile(stmt)
        return_value: ir.Constant = ir.Constant(self.type_map["int"], 0)
        self.builder.ret(return_value)

    def _declare_builtin_functions(self) -> None:
        for module_name in self.builtin_modules:
            for function_name, (return_type_name, parameter_type_names) in BUILTIN_FUNCTIONS[module_name].items():
                symbol = f"__raapid_builtin_{module_name}_{function_name}"
                return_type = self._get_language_type(return_type_name)
                parameter_types = [self._get_language_type(type_name) for type_name in parameter_type_names]
                function_type = ir.FunctionType(return_type, parameter_types)
                self.functions[symbol] = ir.Function(self.module, function_type, name=symbol)

    def _get_language_type(self, type_name: str | None) -> ir.Type:
        if type_name == "none":
            type_name = "void"
        try:
            return self.type_map[type_name]
        except KeyError as error:
            raise TypeError(f"Unsupported function type: {type_name}") from error

    def _declare_function(self, node: AST.FunctionStatement) -> None:
        if node.name == "main" or node.name in self.module.globals:
            raise NameError(f"Function name is already in use: {node.name}")
        parameter_names = [parameter.name for parameter in node.parameters]
        if len(parameter_names) != len(set(parameter_names)):
            raise NameError(f"Duplicate parameter name in function: {node.name}")
        parameter_type_names = self.function_parameter_types[node.name]
        return_type_name = self.function_return_types[node.name]
        parameter_types = [self._get_language_type(type_name) for type_name in parameter_type_names]
        return_type = self._get_language_type(return_type_name)
        function_type = ir.FunctionType(return_type, parameter_types)
        function = ir.Function(self.module, function_type, name=node.name)
        for argument, parameter in zip(function.args, node.parameters):
            argument.name = parameter.name
        self.functions[node.name] = function
        self.function_nodes[node.name] = node

    def visit_function_statement(self, node: AST.FunctionStatement) -> None:
        function = self.functions.get(node.name)
        if function is None:
            raise TypeError("Function declarations are only supported at the top level")

        previous_builder = self.builder
        previous_symbols = self.symbols
        previous_return_type = self.current_return_type
        self.symbols = {}
        self.current_return_type = function.function_type.return_type
        entry_block = function.append_basic_block(f"{node.name}_entry")
        self.builder = ir.IRBuilder(entry_block)
        try:
            for argument, parameter in zip(function.args, node.parameters):
                pointer = self.builder.alloca(argument.type, name=parameter.name)
                self.builder.store(argument, pointer)
                self.symbols[parameter.name] = (pointer, argument.type)

            for statement in node.body.statements:
                if self.builder.block.is_terminated:
                    break
                self.compile(statement)

            if not self.builder.block.is_terminated:
                if isinstance(self.current_return_type, ir.VoidType):
                    self.builder.ret_void()
                else:
                    raise TypeError(f"Function '{node.name}' must return {node.return_type} on every path")
        finally:
            self.builder = previous_builder
            self.symbols = previous_symbols
            self.current_return_type = previous_return_type

    def visit_return_statement(self, node: AST.ReturnStatement) -> None:
        if self.current_return_type is None:
            raise TypeError("Return statements are only valid inside functions")
        if node.value is None:
            if not isinstance(self.current_return_type, ir.VoidType):
                raise TypeError("A non-void function must return a value")
            self.builder.ret_void()
            return

        if isinstance(self.current_return_type, ir.VoidType):
            raise TypeError("A void function cannot return a value")
        value, value_type = self.resolve_value(node.value)
        if value_type != self.current_return_type:
            raise TypeError(f"Return type {value_type} does not match function return type {self.current_return_type}")
        self.builder.ret(value)

    def visit_give_statement(self, node: AST.GiveStatement) -> None:
        self.visit_return_statement(AST.ReturnStatement(node.value))

    def visit_returning_statement(self, node: AST.ReturningStatement) -> None:
        self.visit_return_statement(AST.ReturnStatement(node.value))

    def visit_call_expression(self, node: AST.CallExpression) -> tuple[ir.Value, ir.Type]:
        if not isinstance(node.function, AST.Identifier):
            raise TypeError("Only named functions can be called")
        function = self.functions.get(node.function.value)
        if function is None:
            raise NameError(f"Undefined function: {node.function.value}")
        if len(node.arguments) != len(function.args):
            raise TypeError(f"Function '{node.function.value}' expects {len(function.args)} arguments, got {len(node.arguments)}")

        arguments: list[ir.Value] = []
        for expression, parameter in zip(node.arguments, function.args):
            value, value_type = self.resolve_value(expression)
            if value_type != parameter.type:
                raise TypeError(f"Argument type {value_type} does not match parameter type {parameter.type}")
            arguments.append(value)

        return_type = function.function_type.return_type
        name = f"call_{node.function.value}" if not isinstance(return_type, ir.VoidType) else ""
        result = self.builder.call(function, arguments, name=name)
        return result, return_type

    def _infer_function_signatures(self, nodes: list[AST.FunctionStatement]) -> None:
        parameter_types: dict[str, dict[str, str | None]] = {
            node.name: {parameter.name: parameter.type_name for parameter in node.parameters}
            for node in nodes
        }
        return_types: dict[str, str | None] = {node.name: node.return_type for node in nodes}

        for _ in range(len(nodes) + 2):
            changed = False
            for node in nodes:
                parameters = parameter_types[node.name]
                self._constrain_block(node.body, parameters, return_types)
                for parameter in node.parameters:
                    if parameters[parameter.name] is None:
                        raise TypeError(f"Cannot infer type for parameter '{parameter.name}' in function '{node.name}'; add an annotation")

                returns = self._collect_returns(node.body)
                inferred_returns = [self._infer_expression_type(expression, parameters, return_types) for expression in returns]
                inferred_returns = [type_name for type_name in inferred_returns if type_name is not None]
                if return_types[node.name] is None:
                    if inferred_returns:
                        if any(type_name != inferred_returns[0] for type_name in inferred_returns):
                            raise TypeError(f"Function '{node.name}' returns values with different types")
                        return_types[node.name] = inferred_returns[0]
                        changed = True
                    elif not returns:
                        return_types[node.name] = "void"
                        changed = True
            if not changed:
                break

        for node in nodes:
            for parameter in node.parameters:
                if parameter_types[node.name][parameter.name] is None:
                    raise TypeError(f"Cannot infer type for parameter '{parameter.name}' in function '{node.name}'; add an annotation")
            if return_types[node.name] is None:
                raise TypeError(f"Cannot infer return type for function '{node.name}'; add 'returning type'")
            self.function_parameter_types[node.name] = [parameter_types[node.name][parameter.name] for parameter in node.parameters]
            self.function_return_types[node.name] = return_types[node.name]

    def _constrain_block(self, block: AST.BlockStatement, parameter_types: dict[str, str | None], return_types: dict[str, str | None]) -> None:
        for statement in block.statements:
            expressions: list[AST.Expression] = []
            if isinstance(statement, AST.IfStatement):
                expressions.append(statement.condition)
                self._constrain_block(statement.consequence, parameter_types, return_types)
                if isinstance(statement.alternative, AST.BlockStatement):
                    self._constrain_block(statement.alternative, parameter_types, return_types)
                elif isinstance(statement.alternative, AST.IfStatement):
                    self._constrain_block(AST.BlockStatement(), parameter_types, return_types)
                    self._constrain_statement(statement.alternative, parameter_types, return_types)
            else:
                self._constrain_statement(statement, parameter_types, return_types)

    def _constrain_statement(self, statement: AST.Statement, parameter_types: dict[str, str | None], return_types: dict[str, str | None]) -> None:
        expressions: list[AST.Expression] = []
        if isinstance(statement, AST.ReturnStatement | AST.GiveStatement | AST.ReturningStatement):
            if statement.value is not None:
                expressions.append(statement.value)
        elif isinstance(statement, AST.SayStatement):
            expressions.extend(statement.expressions)
        elif isinstance(statement, AST.LetStatement | AST.MakeStatement):
            if statement.value is not None:
                expressions.append(statement.value)
        elif isinstance(statement, AST.ExpressionStatement):
            if statement.expression is not None:
                expressions.append(statement.expression)
        elif isinstance(statement, AST.IfStatement):
            self._constrain_block(statement.consequence, parameter_types, return_types)
            if isinstance(statement.alternative, AST.BlockStatement):
                self._constrain_block(statement.alternative, parameter_types, return_types)
            elif isinstance(statement.alternative, AST.IfStatement):
                self._constrain_statement(statement.alternative, parameter_types, return_types)
            expressions.append(statement.condition)
        elif isinstance(statement, AST.WhileStatement):
            expressions.append(statement.condition)
            self._constrain_block(statement.body, parameter_types, return_types)
        elif isinstance(statement, AST.RepeatStatement):
            expressions.append(statement.count)
            self._constrain_block(statement.body, parameter_types, return_types)
        for expression in expressions:
            self._constrain_expression(expression, parameter_types, return_types)

    def _constrain_expression(self, expression: AST.Expression, parameter_types: dict[str, str | None], return_types: dict[str, str | None]) -> None:
        if isinstance(expression, AST.InfixExpression):
            left_type = self._infer_expression_type(expression.left_node, parameter_types, return_types)
            right_type = self._infer_expression_type(expression.right_node, parameter_types, return_types)
            if isinstance(expression.left_node, AST.Identifier) and expression.left_node.value in parameter_types and parameter_types[expression.left_node.value] is None and right_type in ("int", "float", "string", "boolean"):
                parameter_types[expression.left_node.value] = right_type
            if isinstance(expression.right_node, AST.Identifier) and expression.right_node.value in parameter_types and parameter_types[expression.right_node.value] is None and left_type in ("int", "float", "string", "boolean"):
                parameter_types[expression.right_node.value] = left_type
            self._constrain_expression(expression.left_node, parameter_types, return_types)
            self._constrain_expression(expression.right_node, parameter_types, return_types)
        elif isinstance(expression, AST.CallExpression):
            for argument in expression.arguments:
                self._constrain_expression(argument, parameter_types, return_types)

    def _infer_expression_type(self, expression: AST.Expression, parameter_types: dict[str, str | None], return_types: dict[str, str | None]) -> str | None:
        if isinstance(expression, AST.IntegerLiteral):
            return "int"
        if isinstance(expression, AST.FloatLiteral):
            return "float"
        if isinstance(expression, AST.StringLiteral):
            return "string"
        if isinstance(expression, AST.BooleanLiteral):
            return "boolean"
        if isinstance(expression, AST.Identifier):
            return parameter_types.get(expression.value)
        if isinstance(expression, AST.CallExpression) and isinstance(expression.function, AST.Identifier):
            return return_types.get(expression.function.value)
        if isinstance(expression, AST.PrefixExpression):
            return "boolean" if expression.operator in ("!", "not") else self._infer_expression_type(expression.right, parameter_types, return_types)
        if isinstance(expression, AST.InfixExpression):
            if expression.operator in ("and", "&&", "or", "||", "==", "!=", ">", "<", ">=", "<="):
                if expression.operator in ("==", "!=", ">", "<", ">=", "<="):
                    left_type = self._infer_expression_type(expression.left_node, parameter_types, return_types)
                    right_type = self._infer_expression_type(expression.right_node, parameter_types, return_types)
                    return "boolean" if left_type is not None or right_type is not None else None
                return "boolean"
            left_type = self._infer_expression_type(expression.left_node, parameter_types, return_types)
            right_type = self._infer_expression_type(expression.right_node, parameter_types, return_types)
            return left_type or right_type
        return None

    def _collect_returns(self, block: AST.BlockStatement) -> list[AST.Expression]:
        returns: list[AST.Expression] = []
        for statement in block.statements:
            if isinstance(statement, AST.ReturnStatement | AST.GiveStatement | AST.ReturningStatement):
                if statement.value is not None:
                    returns.append(statement.value)
            elif isinstance(statement, AST.IfStatement):
                returns.extend(self._collect_returns(statement.consequence))
                if isinstance(statement.alternative, AST.BlockStatement):
                    returns.extend(self._collect_returns(statement.alternative))
                elif isinstance(statement.alternative, AST.IfStatement):
                    returns.extend(self._collect_returns(AST.BlockStatement()))
                    returns.extend(self._collect_returns(AST.BlockStatement()))
                    self._collect_if_returns(statement.alternative, returns)
            elif isinstance(statement, AST.WhileStatement | AST.ForStatement | AST.RepeatStatement):
                returns.extend(self._collect_returns(statement.body))
        return returns

    def _collect_if_returns(self, statement: AST.IfStatement, returns: list[AST.Expression]) -> None:
        returns.extend(self._collect_returns(statement.consequence))
        if isinstance(statement.alternative, AST.BlockStatement):
            returns.extend(self._collect_returns(statement.alternative))
        elif isinstance(statement.alternative, AST.IfStatement):
            self._collect_if_returns(statement.alternative, returns)

    def visit_expression_statement(self, node: AST.ExpressionStatement) -> None:
        self.compile(node.expression)

    def visit_let_statement(self, node: AST.LetStatement) -> None:
        val, val_type = self.resolve_value(node.value)
        var_name = node.name.value
        
        # Allocate stack memory matching the value type
        ptr = self.builder.alloca(val_type, name=var_name)
        self.builder.store(val, ptr)
        
        # Save the pointer and its value type to the symbol table
        self.symbols[var_name] = (ptr, val_type)


    def visit_ask_statement(self, node: AST.AskStatement) -> None:
        # ---- Step 1: Render the Prompt ----
        prompt_ptr, _ = self.resolve_value(node.prompt)
        self.builder.call(self.printf_func, [prompt_ptr])
        
        var_name = node.name.value
        zero = ir.Constant(ir.IntType(32), 0)
        declared_type = node.var_type
        if declared_type is None and var_name in self.symbols:
            existing_type = self.symbols[var_name][1]
            if isinstance(existing_type, ir.IntType) and existing_type.width == 1:
                declared_type = "boolean"
            elif isinstance(existing_type, ir.IntType):
                declared_type = "int"
            elif isinstance(existing_type, ir.FloatType):
                declared_type = "float"
            elif isinstance(existing_type, ir.PointerType):
                declared_type = "string"
        if declared_type is None:
            declared_type = "int"

        # ---- Step 2: Handle memory allocations based on type ----
        if declared_type == "string":
            # For strings, allocate a fixed-size character buffer (e.g., 256 bytes)
            target_type = ir.ArrayType(ir.IntType(8), 256)
            if var_name not in self.symbols:
                ptr = self.builder.alloca(target_type, name=var_name)
                # Store it in symbols as a char_ptr because strings are passed around as char pointers
                char_ptr_type = self.type_map["char_ptr"]
                self.symbols[var_name] = (ptr, char_ptr_type)
            else:
                ptr, _ = self.symbols[var_name]

            # Use %s format for string scanning
            scan_fmt = self._make_global_string(f"scan_str_{var_name}", "%s\0")
            scan_cast = self.builder.gep(scan_fmt, [zero, zero])
            # Direct buffer decay to char_ptr for scanf
            buf_ptr = self.builder.gep(ptr, [zero, zero])
            self.builder.call(self.scanf_func, [scan_cast, buf_ptr])

        else:
            # Handle int and float numbers
            target_type = self.type_map.get(declared_type)
            if not target_type:
                raise TypeError(f"Unsupported input target type: {declared_type}")
                
            if var_name not in self.symbols:
                ptr = self.builder.alloca(target_type, name=var_name)
                self.symbols[var_name] = (ptr, target_type)
            else:
                ptr, target_type = self.symbols[var_name]

            if isinstance(target_type, ir.IntType) and target_type.width == 32:
                scan_fmt = self._make_global_string(f"scan_int_{var_name}", "%d\0")
                scan_cast = self.builder.gep(scan_fmt, [zero, zero])
                self.builder.call(self.scanf_func, [scan_cast, ptr])
                
            elif isinstance(target_type, ir.FloatType):
                scan_fmt = self._make_global_string(f"scan_float_{var_name}", "%f\0")
                scan_cast = self.builder.gep(scan_fmt, [zero, zero])
                self.builder.call(self.scanf_func, [scan_cast, ptr])

    def visit_say_statement(self, node: AST.SayStatement) -> None:
        zero = ir.Constant(ir.IntType(32), 0)
        format_parts: list[str] = []
        values: list[ir.Value] = []
        for expression in node.expressions:
            val, val_type = self.resolve_value(expression)
            if isinstance(val_type, ir.IntType) and val_type.width == 1:
                true_ptr = self.builder.gep(self.true_string, [zero, zero])
                false_ptr = self.builder.gep(self.false_string, [zero, zero])
                val = self.builder.select(val, true_ptr, false_ptr)
                format_parts.append("%s")
            elif isinstance(val_type, ir.IntType):
                format_parts.append("%d")
            elif isinstance(val_type, ir.FloatType):
                val = self.builder.fpext(val, ir.DoubleType())
                format_parts.append("%f")
            elif isinstance(val_type, ir.ArrayType) and val_type.element == ir.IntType(8):
                if isinstance(val.type, ir.PointerType):
                    val = self.builder.gep(val, [zero, zero])
                else:
                    temp_alloc = self.builder.alloca(val_type)
                    self.builder.store(val, temp_alloc)
                    val = self.builder.gep(temp_alloc, [zero, zero])
                format_parts.append("%s")
            elif isinstance(val_type, ir.PointerType):
                if isinstance(val_type.pointee, ir.IntType) and val_type.pointee.width == 8:
                    format_parts.append("%s")
                else:
                    val = self.builder.bitcast(val, self.type_map["char_ptr"])
                    format_parts.append("%p")
            else:
                raise TypeError(f"Say statement does not support outputting type: {val_type}")
            values.append(val)

        format_text = " ".join(format_parts) + "\n\0"
        format_global = self._make_global_string(f"say_fmt_{self.say_count}", format_text)
        self.say_count += 1
        char_ptr = self.builder.gep(format_global, [zero, zero], name="fmt_cast")
        self.builder.call(self.printf_func, [char_ptr, *values])

    def visit_set_statement(self, node: AST.SetStatement) -> None:
        value, value_type = self.resolve_value(node.value)
        if isinstance(node.target, AST.Identifier):
            var_name = node.target.value
            if var_name not in self.symbols:
                raise NameError(f"Cannot assign to undefined identifier: {var_name}")
            target_ptr, target_type = self.symbols[var_name]
            if target_type != value_type:
                raise TypeError(f"Cannot assign value of type {value_type} to {target_type}")
            self.builder.store(value, target_ptr)
            return

        if isinstance(node.target, AST.IndexExpression):
            array_type = None
            if isinstance(node.target.array, AST.Identifier):
                var_name = node.target.array.value
                if var_name not in self.symbols:
                    raise NameError(f"Undefined array identifier: {var_name}")
                array_ptr, array_type = self.symbols[var_name]
            else:
                array_value, array_type = self.resolve_value(node.target.array)
                array_ptr = self.builder.alloca(array_type)
                self.builder.store(array_value, array_ptr)
            if not isinstance(array_type, ir.ArrayType):
                raise TypeError("Indexed assignment requires an array")
            index, index_type = self.resolve_value(node.target.index)
            if index_type != self.type_map["int"]:
                raise TypeError("Array indices must be integers")
            zero = ir.Constant(self.type_map["int"], 0)
            target_ptr = self.builder.gep(array_ptr, [zero, index])
            if value_type != array_type.element:
                raise TypeError(f"Cannot assign value of type {value_type} to array element {array_type.element}")
            self.builder.store(value, target_ptr)
            return

        if not isinstance(node.target, AST.ValueAtExpression):
            raise TypeError("Set target must be a variable, array element, or 'value at' expression")

        var_name = node.target.pointer.value
        if var_name not in self.symbols:
            raise NameError(f"Cannot assign through undefined pointer identifier: {var_name}")

        pointer_slot, pointer_type = self.symbols[var_name]
        if not isinstance(pointer_type, ir.PointerType):
            raise TypeError(f"Cannot assign through non-pointer variable: {var_name}")

        target_address = self.builder.load(pointer_slot, name=f"addr_stored_in_{var_name}")
        target_type = pointer_type.pointee

        if isinstance(target_type, ir.ArrayType) and target_type.element == ir.IntType(8):
            if not (isinstance(value_type, ir.PointerType) and isinstance(value_type.pointee, ir.IntType) and value_type.pointee.width == 8):
                raise TypeError("A character buffer can only be assigned a string value")
            destination = self.builder.gep(target_address, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
            self.builder.call(self.strncpy_func, [destination, value, ir.Constant(ir.IntType(64), target_type.count)])
            last_index = ir.Constant(ir.IntType(32), target_type.count - 1)
            terminator_ptr = self.builder.gep(target_address, [ir.Constant(ir.IntType(32), 0), last_index])
            self.builder.store(ir.Constant(ir.IntType(8), 0), terminator_ptr)
        elif target_type == value_type:
            self.builder.store(value, target_address)
        else:
            raise TypeError(f"Cannot assign value of type {value_type} through pointer to {target_type}")

    def visit_if_statement(self, node: AST.IfStatement) -> None:
        cond_val, cond_type = self.resolve_value(node.condition)
        parent_function = self.builder.function
        then_block = parent_function.append_basic_block("if_then")
        alternative_block = parent_function.append_basic_block("if_alternative")
        merge_block = parent_function.append_basic_block("if_merge")
        
        self.builder.cbranch(cond_val, then_block, alternative_block)
        
        self.builder.position_at_end(then_block)
        for stmt in node.consequence.statements:
            if self.builder.block.is_terminated:
                break
            self.compile(stmt)
        then_terminated = self.builder.block.is_terminated
        if not then_terminated:
            self.builder.branch(merge_block)

        self.builder.position_at_end(alternative_block)
        if isinstance(node.alternative, AST.IfStatement):
            self.visit_if_statement(node.alternative)
        elif isinstance(node.alternative, AST.BlockStatement):
            for stmt in node.alternative.statements:
                if self.builder.block.is_terminated:
                    break
                self.compile(stmt)
        alternative_terminated = self.builder.block.is_terminated
        if not alternative_terminated:
            self.builder.branch(merge_block)
            
        self.builder.position_at_end(merge_block)
        if then_terminated and alternative_terminated:
            self.builder.unreachable()

    def visit_for_statement(self, node: AST.ForStatement) -> None:
        if node.mode == "range":
            start, start_type = self.resolve_value(node.start)
            end, end_type = self.resolve_value(node.end)
            if start_type != self.type_map["int"] or end_type != self.type_map["int"]:
                raise TypeError("Range loop bounds must be integers")
            self._emit_counted_loop(node.variable.value, start, end, inclusive=True, body=node.body)
            return

        iterable, array_type = self.resolve_value(node.iterable)
        if not isinstance(array_type, ir.ArrayType):
            raise TypeError("Array for-loops require a list or array expression")
        array_ptr = self.builder.alloca(array_type, name="for_array")
        self.builder.store(iterable, array_ptr)
        zero = ir.Constant(self.type_map["int"], 0)
        index_ptr = self.builder.alloca(self.type_map["int"], name="for_index")
        element_ptr = self.builder.alloca(array_type.element, name=node.variable.value)
        previous_binding = self.symbols.get(node.variable.value)
        self.symbols[node.variable.value] = (element_ptr, array_type.element)
        self.builder.store(ir.Constant(self.type_map["int"], 0), index_ptr)

        function = self.builder.function
        condition_block = function.append_basic_block("for_array_cond")
        body_block = function.append_basic_block("for_array_body")
        increment_block = function.append_basic_block("for_array_increment")
        merge_block = function.append_basic_block("for_array_merge")
        self.builder.branch(condition_block)

        self.builder.position_at_end(condition_block)
        index = self.builder.load(index_ptr)
        has_next = self.builder.icmp_signed("<", index, ir.Constant(self.type_map["int"], array_type.count))
        self.builder.cbranch(has_next, body_block, merge_block)

        self.builder.position_at_end(body_block)
        item_ptr = self.builder.gep(array_ptr, [zero, index])
        item = self.builder.load(item_ptr)
        self.builder.store(item, element_ptr)
        for statement in node.body.statements:
            self.compile(statement)
        if not self.builder.block.is_terminated:
            self.builder.branch(increment_block)

        self.builder.position_at_end(increment_block)
        next_index = self.builder.add(index, ir.Constant(self.type_map["int"], 1))
        self.builder.store(next_index, index_ptr)
        self.builder.branch(condition_block)
        self.builder.position_at_end(merge_block)
        if previous_binding is None:
            self.symbols.pop(node.variable.value, None)
        else:
            self.symbols[node.variable.value] = previous_binding

    def _emit_counted_loop(self, variable_name: str, start: ir.Value, end: ir.Value, inclusive: bool, body: AST.BlockStatement) -> None:
        previous_binding = self.symbols.get(variable_name)
        index_ptr = self.builder.alloca(self.type_map["int"], name=variable_name)
        self.symbols[variable_name] = (index_ptr, self.type_map["int"])
        self.builder.store(start, index_ptr)

        function = self.builder.function
        condition_block = function.append_basic_block("counted_cond")
        body_block = function.append_basic_block("counted_body")
        increment_block = function.append_basic_block("counted_increment")
        merge_block = function.append_basic_block("counted_merge")
        self.builder.branch(condition_block)

        self.builder.position_at_end(condition_block)
        index = self.builder.load(index_ptr)
        comparison = "<=" if inclusive else "<"
        has_next = self.builder.icmp_signed(comparison, index, end)
        self.builder.cbranch(has_next, body_block, merge_block)

        self.builder.position_at_end(body_block)
        for statement in body.statements:
            self.compile(statement)
        if not self.builder.block.is_terminated:
            self.builder.branch(increment_block)

        self.builder.position_at_end(increment_block)
        next_index = self.builder.add(index, ir.Constant(self.type_map["int"], 1))
        self.builder.store(next_index, index_ptr)
        self.builder.branch(condition_block)
        self.builder.position_at_end(merge_block)
        if previous_binding is None:
            self.symbols.pop(variable_name, None)
        else:
            self.symbols[variable_name] = previous_binding

    def visit_repeat_statement(self, node: AST.RepeatStatement) -> None:
        count, count_type = self.resolve_value(node.count)
        if count_type != self.type_map["int"]:
            raise TypeError("Repeat count must be an integer")
        self._emit_counted_loop("repeat_index", ir.Constant(self.type_map["int"], 0), count, inclusive=False, body=node.body)

    def visit_while_statement(self, node: AST.WhileStatement) -> None:
        parent_function = self.builder.function
        cond_block = parent_function.append_basic_block("while_cond")
        body_block = parent_function.append_basic_block("while_body")
        merge_block = parent_function.append_basic_block("while_merge")

        self.builder.branch(cond_block)

        self.builder.position_at_end(cond_block)
        cond_val, cond_type = self.resolve_value(node.condition)
        self.builder.cbranch(cond_val, body_block, merge_block)

        self.builder.position_at_end(body_block)
        for stmt in node.body.statements:
            self.compile(stmt)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)

        self.builder.position_at_end(merge_block)

    def visit_make_statement(self, node: AST.MakeStatement) -> None:
        value, value_type = self.resolve_value(node.value)
        var_name = node.name.value
        ptr = self.builder.alloca(value_type, name=var_name)
        self.builder.store(value, ptr)
        self.symbols[var_name] = (ptr, value_type)

    def visit_identifier(self, node: AST.Identifier) -> tuple[ir.Value, ir.Type]:
        var_name = node.value
        if var_name not in self.symbols:
            raise NameError(f"Undefined variable identifier: {var_name}")
        ptr, val_type = self.symbols[var_name]
        
        # If it's a structural character array (a string buffer), return its pointer address directly
        if isinstance(ptr.type.pointee, ir.ArrayType) and ptr.type.pointee.element == ir.IntType(8):
            zero = ir.Constant(ir.IntType(32), 0)
            val = self.builder.gep(ptr, [zero, zero], name=f"str_decay_{var_name}")
            return val, val_type
            
        val = self.builder.load(ptr, name=f"load_{var_name}")
        return val, val_type


    def visit_address_of(self, node: AST.AddressOfExpression) -> tuple[ir.Value, ir.Type]:
        var_name = node.target.value
        if var_name not in self.symbols:
            raise NameError(f"Cannot get address of undefined identifier: {var_name}")
            
        ptr, val_type = self.symbols[var_name]
        return ptr, ptr.type


    def visit_value_at(self, node: AST.ValueAtExpression) -> tuple[ir.Value, ir.Type]:
        var_name = node.pointer.value
        if var_name not in self.symbols:
            raise NameError(f"Cannot dereference undefined pointer identifier: {var_name}")
            
        ptr, val_type = self.symbols[var_name]
        
        # Load the address pointer stored inside your pointer variable
        target_address = self.builder.load(ptr, name=f"addr_stored_in_{var_name}")
        
        # If it points to a string pointer container layout (i8** or pointer to Array)
        if isinstance(val_type, ir.PointerType):
            if isinstance(val_type.pointee, ir.PointerType) and isinstance(val_type.pointee.pointee, ir.IntType) and val_type.pointee.pointee.width == 8:
                return target_address, self.type_map["char_ptr"]
            if isinstance(val_type.pointee, ir.ArrayType) and val_type.pointee.element == ir.IntType(8):
                return target_address, val_type.pointee

        # Traditional value dereferencing for basic data types like integers or floats
        actual_val = self.builder.load(target_address, name=f"val_at_{var_name}")
        return actual_val, val_type.pointee

    def visit_infix_expression(self, node: AST.InfixExpression) -> tuple[ir.Value, ir.Type]:
        operator: str = node.operator
        if operator in ("and", "&&", "or", "||"):
            left_value, left_type = self.resolve_value(node.left_node)
            if left_type != self.type_map["bool"]:
                raise TypeError("Logical operators require boolean operands")
            function = self.builder.function
            right_block = function.append_basic_block("logic_rhs")
            merge_block = function.append_basic_block("logic_merge")
            is_and = operator in ("and", "&&")
            short_circuit_value = ir.Constant(self.type_map["bool"], int(not is_and))
            if is_and:
                self.builder.cbranch(left_value, right_block, merge_block)
            else:
                self.builder.cbranch(left_value, merge_block, right_block)
            left_block = self.builder.block
            self.builder.position_at_end(right_block)
            right_value, right_type = self.resolve_value(node.right_node)
            if right_type != self.type_map["bool"]:
                raise TypeError("Logical operators require boolean operands")
            right_end_block = self.builder.block
            self.builder.branch(merge_block)
            self.builder.position_at_end(merge_block)
            result = self.builder.phi(self.type_map["bool"], name="logic_result")
            result.add_incoming(short_circuit_value, left_block)
            result.add_incoming(right_value, right_end_block)
            return result, self.type_map["bool"]

        left_value, left_type = self.resolve_value(node.left_node)
        right_value, right_type = self.resolve_value(node.right_node)
        
        if operator in ["/", "^"]:
            if isinstance(left_type, ir.IntType):
                left_value = self.builder.sitofp(left_value, ir.FloatType())
                left_type = ir.FloatType()
            if isinstance(right_type, ir.IntType):
                right_value = self.builder.sitofp(right_value, ir.FloatType())
                right_type = ir.FloatType()
                
        if isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.IntType):
            right_value = self.builder.sitofp(right_value, ir.FloatType())
            right_type = ir.FloatType()
        elif isinstance(left_type, ir.IntType) and isinstance(right_type, ir.FloatType):
            left_value = self.builder.sitofp(left_value, ir.FloatType())
            left_type = ir.FloatType()
            
        value = None
        Type = None
        
        if isinstance(left_type, ir.IntType) and isinstance(right_type, ir.IntType):
            if operator in ["+", "-", "*", "%"]:
                Type = self.type_map["int"]
                if operator == "+": value = self.builder.add(left_value, right_value)
                elif operator == "-": value = self.builder.sub(left_value, right_value)
                elif operator == "*": value = self.builder.mul(left_value, right_value)
                elif operator == "%": value = self.builder.srem(left_value, right_value)
            elif operator in [">", "<", "<=", ">=", "==", "!="]:
                Type = self.type_map["bool"]
                value = self.builder.icmp_signed(operator, left_value, right_value)
                
        elif isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.FloatType):
            if operator in ["+", "-", "*", "/", "%"]:
                Type = self.type_map["float"]
                if operator == "+": value = self.builder.fadd(left_value, right_value)
                elif operator == "-": value = self.builder.fsub(left_value, right_value)
                elif operator == "*": value = self.builder.fmul(left_value, right_value)
                elif operator == "/": value = self.builder.fdiv(left_value, right_value)
                elif operator == "%": value = self.builder.frem(left_value, right_value)
            elif operator == "^":
                Type = self.type_map["float"]
                powf_signature = ir.FunctionType(Type, [Type, Type])
                powf_func = self.module.declare_intrinsic('llvm.pow', tys=[Type], fnty=powf_signature)
                value = self.builder.call(powf_func, [left_value, right_value])
            elif operator in [">", "<", "<=", ">=", "==", "!="]:
                Type = self.type_map["bool"]
                op_map = {">": "ogt", "<": "olt", "<=": "ole", ">=": "oge", "==": "oeq", "!=": "one"}
                value = self.builder.fcmp_ordered(op_map[operator], left_value, right_value)

        elif isinstance(left_type, ir.PointerType) and isinstance(right_type, ir.PointerType):
            if operator in ("==", "!="):
                # Check if both sides are character pointers (Strings)
                is_left_str = isinstance(left_type.pointee, ir.IntType) and left_type.pointee.width == 8
                is_right_str = isinstance(right_type.pointee, ir.IntType) and right_type.pointee.width == 8
                
                if is_left_str and is_right_str:
                    Type = self.type_map["bool"]
                    # Call strcmp: returns 0 if strings match
                    strcmp_res = self.builder.call(self.strcmp_func, [left_value, right_value])
                    zero_int = ir.Constant(ir.IntType(32), 0)
                    # If strcmp result == 0, then condition is true
                    comparison = "==" if operator == "==" else "!="
                    value = self.builder.icmp_signed(comparison, strcmp_res, zero_int)
                else:
                    # Fallback for non-string pointer equality checks
                    Type = self.type_map["bool"]
                    value = self.builder.icmp_unsigned(operator, left_value, right_value)
            elif operator in [">", "<"]:
                Type = self.type_map["bool"]
                value = self.builder.icmp_unsigned(operator, left_value, right_value)

                
        if value is None:
            raise RuntimeError(f"Unsupported infix operation: {left_type} {operator} {right_type}")
        return value, Type

    def visit_prefix_expression(self, node: AST.PrefixExpression) -> tuple[ir.Value, ir.Type]:
        value, value_type = self.resolve_value(node.right)
        if node.operator in ("!", "not"):
            if value_type != self.type_map["bool"]:
                raise TypeError("The not operator requires a boolean operand")
            return self.builder.not_(value), self.type_map["bool"]
        raise TypeError(f"Unsupported prefix operator: {node.operator}")
        
    def resolve_value(self, node: AST.Expression, value_type: str = None) -> tuple[ir.Value, ir.Type]:
        match node.type():
            case AST.NodeType.IntegerLiteral:
                val, Type = node.value, self.type_map["int" if value_type is None else value_type]
                return ir.Constant(Type, val), Type
            case AST.NodeType.FloatLiteral:
                val, Type = node.value, self.type_map["float" if value_type is None else value_type]
                return ir.Constant(Type, val), Type
            case AST.NodeType.StringLiteral:
                self.str_count += 1
                str_val = node.value + "\0"
                global_str = self._make_global_string(f"str_lit{self.str_count}", str_val)
                zero = ir.Constant(ir.IntType(32), 0)
                char_ptr = self.builder.gep(global_str, [zero, zero], name=f"str_ptr_{self.str_count}")
                return char_ptr, self.type_map["char_ptr"]
            case AST.NodeType.BooleanLiteral:
                val, Type = node.value, self.type_map["bool" if value_type is None else value_type]
                return ir.Constant(Type, int(val)), Type
            case AST.NodeType.ArrayLiteral:
                if not node.elements:
                    element_type = self.type_map["int"]
                    array_type = ir.ArrayType(element_type, 0)
                    return ir.Constant(array_type, []), array_type
                values = [self.resolve_value(element) for element in node.elements]
                element_type = values[0][1]
                if any(item_type != element_type for _, item_type in values):
                    raise TypeError("All elements in a list must have the same type")
                array_type = ir.ArrayType(element_type, len(values))
                aggregate: ir.Value = ir.Constant(array_type, ir.Undefined)
                for index, (item, _) in enumerate(values):
                    aggregate = self.builder.insert_value(aggregate, item, index)
                return aggregate, array_type
            case AST.NodeType.IndexExpression:
                array_value, array_type = self.resolve_value(node.array)
                if not isinstance(array_type, ir.ArrayType):
                    raise TypeError("Indexing requires an array")
                index, index_type = self.resolve_value(node.index)
                if index_type != self.type_map["int"]:
                    raise TypeError("Array indices must be integers")
                array_ptr = self.builder.alloca(array_type, name="indexed_array")
                self.builder.store(array_value, array_ptr)
                zero = ir.Constant(self.type_map["int"], 0)
                element_ptr = self.builder.gep(array_ptr, [zero, index])
                return self.builder.load(element_ptr), array_type.element
            case AST.NodeType.CallExpression:
                return self.visit_call_expression(node)
            case AST.NodeType.PrefixExpression:
                return self.visit_prefix_expression(node)
            case AST.NodeType.InfixExpression:
                return self.visit_infix_expression(node) 
            case AST.NodeType.Identifier:
                return self.visit_identifier(node)
            case AST.NodeType.AddressOfExpression:
                return self.visit_address_of(node) 
            case AST.NodeType.ValueAtExpression:
                return self.visit_value_at(node)  
            case _:
                raise NotImplementedError(f"Cannot resolve compiler value type for node: {node.type()}")
