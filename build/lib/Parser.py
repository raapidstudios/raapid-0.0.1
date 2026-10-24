from enum import Enum, auto
from typing import Callable

import AST
from Lexer import Lexer
from Token import Token, TokenType


class PrecedenceType(Enum):
    P_LOWEST = 0
    P_OR = auto()
    P_AND = auto()
    P_EQUALS = auto()
    P_LESSGREATER = auto()
    P_SUM = auto()
    P_PRODUCT = auto()
    P_EXPONENT = auto()
    P_MODULUS = auto()
    P_PREFIX = auto()
    P_CALL = auto()
    P_MEMBER = auto()
    P_INDEX = auto()


PRECEDENCE: dict[TokenType, PrecedenceType] = {
    TokenType.OR: PrecedenceType.P_OR,
    TokenType.AND: PrecedenceType.P_AND,
    TokenType.EQ_COMP: PrecedenceType.P_EQUALS,
    TokenType.NEQ: PrecedenceType.P_EQUALS,
    TokenType.GT: PrecedenceType.P_LESSGREATER,
    TokenType.LT: PrecedenceType.P_LESSGREATER,
    TokenType.LTE: PrecedenceType.P_LESSGREATER,
    TokenType.GTE: PrecedenceType.P_LESSGREATER,
    TokenType.PLUS: PrecedenceType.P_SUM,
    TokenType.MINUS: PrecedenceType.P_SUM,
    TokenType.ASTERISK: PrecedenceType.P_PRODUCT,
    TokenType.SLASH: PrecedenceType.P_PRODUCT,
    TokenType.POWER: PrecedenceType.P_EXPONENT,
    TokenType.MODULUS: PrecedenceType.P_MODULUS,
    TokenType.L_PAREN: PrecedenceType.P_CALL,
    TokenType.DOT: PrecedenceType.P_MEMBER,
    TokenType.L_BRACKET: PrecedenceType.P_INDEX,
}


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer
        self.errors: list[str] = []
        self.current_token: Token | None = None
        self.peek_token: Token | None = None
        self.prefix_parse_fns: dict[TokenType, Callable] = {
            TokenType.INT: self.parse_integer_literal,
            TokenType.FLOAT: self.parse_float_literal,
            TokenType.STRING: self.parse_string_literal,
            TokenType.L_BRACKET: self.parse_array_literal,
            TokenType.TRUE: self.parse_boolean_literal,
            TokenType.FALSE: self.parse_boolean_literal,
            TokenType.L_PAREN: self.parse_grouped_expression,
            TokenType.IDENTIFIER: self.parse_identifier,
            TokenType.NOT: self.parse_prefix_expression,
        }
        self.infix_parse_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.parse_infix_expression,
            TokenType.MINUS: self.parse_infix_expression,
            TokenType.ASTERISK: self.parse_infix_expression,
            TokenType.SLASH: self.parse_infix_expression,
            TokenType.POWER: self.parse_infix_expression,
            TokenType.MODULUS: self.parse_infix_expression,
            TokenType.EQ_COMP: self.parse_infix_expression,
            TokenType.NEQ: self.parse_infix_expression,
            TokenType.GT: self.parse_infix_expression,
            TokenType.LT: self.parse_infix_expression,
            TokenType.LTE: self.parse_infix_expression,
            TokenType.GTE: self.parse_infix_expression,
            TokenType.AND: self.parse_infix_expression,
            TokenType.OR: self.parse_infix_expression,
            TokenType.L_BRACKET: self.parse_index_expression,
            TokenType.L_PAREN: self.parse_call_expression,
            TokenType.DOT: self.parse_member_expression,
        }
        self.next_token()
        self.next_token()

    def next_token(self) -> None:
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def peek_token_is(self, token_type: TokenType) -> bool:
        return self.peek_token is not None and self.peek_token.type == token_type

    def expect_peek(self, token_type: TokenType) -> bool:
        if self.peek_token_is(token_type):
            self.next_token()
            return True
        self.peek_error(token_type)
        return False

    def current_precedence(self) -> PrecedenceType:
        if self.current_token is None:
            return PrecedenceType.P_LOWEST
        return PRECEDENCE.get(self.current_token.type, PrecedenceType.P_LOWEST)

    def peek_precedence(self) -> PrecedenceType:
        if self.peek_token is None:
            return PrecedenceType.P_LOWEST
        return PRECEDENCE.get(self.peek_token.type, PrecedenceType.P_LOWEST)

    def peek_error(self, token_type: TokenType) -> None:
        got_type = self.peek_token.type if self.peek_token else "NONE"
        self.errors.append(f"Expected next token to be {token_type}, got {got_type} instead.")

    def no_prefix_parse_fn_error(self, token_type: TokenType) -> None:
        self.errors.append(f"No prefix parse function for {token_type} found.")

    def parse_program(self) -> AST.Program:
        program = AST.Program()
        while self.current_token is not None and self.current_token.type != TokenType.EOF:
            statement = self.parse_statement()
            if statement is not None:
                program.statements.append(statement)
            self.next_token()
        return program

    def parse_statement(self) -> AST.Statement | None:
        match self.current_token.type:
            case TokenType.LET:
                return self.parse_let_statement()
            case TokenType.IMPORT:
                return self.parse_import_statement()
            case TokenType.MAKE:
                return self.parse_make_statement()
            case TokenType.SET:
                return self.parse_set_statement()
            case TokenType.SAY:
                return self.parse_say_statement()
            case TokenType.ASK:
                return self.parse_ask_statement()
            case TokenType.IF:
                return self.parse_if_statement()
            case TokenType.WHILE:
                return self.parse_while_statement()
            case TokenType.FOR:
                return self.parse_for_statement()
            case TokenType.REPEAT:
                return self.parse_repeat_statement()
            case TokenType.FUNCTION:
                return self.parse_function_statement()
            case TokenType.RETURN:
                return self.parse_return_statement()
            case TokenType.GIVE:
                return self.parse_give_statement()
            case TokenType.RETURNING:
                return self.parse_returning_statement()
            case _:
                return self.parse_expression_statement()

    def parse_let_statement(self) -> AST.LetStatement | None:
        if not self.expect_peek(TokenType.IDENTIFIER):
            return None
        name = self.parse_identifier()
        if not self.expect_peek(TokenType.EQ):
            return None
        self.next_token()
        value = self.parse_expression(PrecedenceType.P_LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.LetStatement(name, value)

    def parse_import_statement(self) -> AST.ImportStatement | None:
        self.next_token()
        if self.current_token.type not in (TokenType.STRING, TokenType.IDENTIFIER):
            self.errors.append("Expected a module name or quoted .raap path after 'import'.")
            return None
        module_name = str(self.current_token.literal)
        alias = None
        if self.peek_token_is(TokenType.AS):
            self.next_token()
            if not self.expect_peek(TokenType.IDENTIFIER):
                return None
            alias = self.current_token.literal
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.ImportStatement(module_name, alias)

    def parse_make_statement(self) -> AST.MakeStatement | AST.FunctionStatement | None:
        if not self.expect_peek(TokenType.IDENTIFIER):
            return None
        name = self.parse_identifier()
        if self.peek_token_is(TokenType.L_PAREN):
            return self.parse_function_declaration(name.value)
        if not self.expect_peek(TokenType.ASSIGN):
            return None
        self.next_token()
        value = self.parse_expression(PrecedenceType.P_LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.MakeStatement(name, value)

    def parse_function_statement(self) -> AST.FunctionStatement | None:
        if not self.expect_peek(TokenType.IDENTIFIER):
            return None
        return self.parse_function_declaration(self.current_token.literal)

    def parse_function_declaration(self, name: str) -> AST.FunctionStatement | None:
        if not self.expect_peek(TokenType.L_PAREN):
            return None
        parameters: list[AST.FunctionParameter] = []
        if not self.peek_token_is(TokenType.R_PAREN):
            self.next_token()
            while True:
                if self.current_token.type != TokenType.IDENTIFIER:
                    self.errors.append("Expected a parameter name in function declaration.")
                    return None
                parameter_name = self.current_token.literal
                parameter_type = None
                if self.peek_token_is(TokenType.COLON):
                    self.next_token()
                    self.next_token()
                    valid_types = [TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STRING, TokenType.TYPE_BOOLEAN]
                    if self.current_token.type not in valid_types:
                        self.errors.append("Expected a parameter type (int, float, string, or boolean).")
                        return None
                    parameter_type = self.current_token.literal
                parameters.append(AST.FunctionParameter(parameter_name, parameter_type))
                if not self.peek_token_is(TokenType.COMMA):
                    break
                self.next_token()
                self.next_token()

        if not self.expect_peek(TokenType.R_PAREN):
            return None
        return_type = None
        if self.peek_token_is(TokenType.RETURNING):
            self.next_token()
            self.next_token()
            valid_return_types = [TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STRING, TokenType.TYPE_BOOLEAN, TokenType.TYPE_VOID, TokenType.TYPE_NONE]
            if self.current_token.type not in valid_return_types:
                self.errors.append("Expected a function return type (int, float, string, boolean, void, or none).")
                return None
            return_type = self.current_token.literal
        elif self.peek_token_is(TokenType.COLON):
            self.next_token()
            self.next_token()
            valid_return_types = [TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STRING, TokenType.TYPE_BOOLEAN, TokenType.TYPE_VOID, TokenType.TYPE_NONE]
            if self.current_token.type not in valid_return_types:
                self.errors.append("Expected a function return type (int, float, string, boolean, void, or none).")
                return None
            return_type = self.current_token.literal
        if not self.expect_peek(TokenType.L_BRACE):
            return None
        body = self.parse_block_statement()
        return AST.FunctionStatement(name, parameters, return_type, body)

    def parse_say_statement(self) -> AST.SayStatement:
        self.next_token()
        statement = AST.SayStatement()
        statement.expression = self.parse_expression(PrecedenceType.P_LOWEST)
        statement.expressions.append(statement.expression)
        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            statement.expressions.append(self.parse_expression(PrecedenceType.P_LOWEST))
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return statement

    def parse_set_statement(self) -> AST.SetStatement | None:
        self.next_token()
        target = self.parse_expression(PrecedenceType.P_LOWEST)
        if not self.expect_peek(TokenType.TO):
            return None
        self.next_token()
        value = self.parse_expression(PrecedenceType.P_LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.SetStatement(target, value)

    def parse_give_statement(self) -> AST.GiveStatement:
        self.next_token()
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.literal == "back":
            self.next_token()
        value = self.parse_expression(PrecedenceType.P_LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.GiveStatement(value)

    def parse_returning_statement(self) -> AST.ReturningStatement | None:
        if not self.expect_peek(TokenType.IDENTIFIER):
            return None
        value = self.parse_expression(PrecedenceType.P_LOWEST)
        return AST.ReturningStatement(value)

    def parse_return_statement(self) -> AST.ReturnStatement:
        if self.peek_token_is(TokenType.R_BRACE) or self.peek_token_is(TokenType.EOF):
            return AST.ReturnStatement()
        self.next_token()
        value = None if self.current_token.type == TokenType.SEMICOLON else self.parse_expression(PrecedenceType.P_LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.ReturnStatement(value)

    def parse_ask_statement(self) -> AST.AskStatement | None:
        self.next_token()
        if self.current_token.type != TokenType.STRING:
            self.errors.append(f"Expected a prompt string after 'ask', got {self.current_token.type}")
            return None
        prompt = self.parse_string_literal()
        if not self.expect_peek(TokenType.IDENTIFIER) or self.current_token.literal != "store":
            self.errors.append("Expected keyword 'store' after prompt string.")
            return None
        if self.peek_token_is(TokenType.IN):
            self.next_token()
        elif self.peek_token is not None and self.peek_token.type == TokenType.IDENTIFIER and self.peek_token.literal == "in":
            self.next_token()
        else:
            self.errors.append("Expected keyword 'in' after 'store'.")
            return None
        if not self.expect_peek(TokenType.IDENTIFIER):
            self.errors.append("Expected a variable identifier after 'in'.")
            return None
        name = self.parse_identifier()
        var_type = None
        if self.peek_token_is(TokenType.COLON):
            self.next_token()
            self.next_token()
            valid_types = [TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_STRING, TokenType.TYPE_BOOLEAN]
            if self.current_token.type not in valid_types:
                self.errors.append(f"Expected a valid type keyword after ':', got {self.current_token.literal}")
                return None
            var_type = self.current_token.literal
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.AskStatement(prompt, name, var_type)

    def parse_if_statement(self) -> AST.IfStatement | None:
        self.next_token()
        statement = AST.IfStatement()
        statement.condition = self.parse_expression(PrecedenceType.P_LOWEST)
        if not self.expect_peek(TokenType.L_BRACE):
            return None
        statement.consequence = self.parse_block_statement()
        if self.peek_token_is(TokenType.ELIF):
            self.next_token()
            statement.alternative = self.parse_if_statement()
        elif self.peek_token_is(TokenType.ELSE):
            self.next_token()
            if not self.expect_peek(TokenType.L_BRACE):
                return None
            statement.alternative = self.parse_block_statement()
        return statement

    def parse_while_statement(self) -> AST.WhileStatement | None:
        self.next_token()
        statement = AST.WhileStatement()
        statement.condition = self.parse_expression(PrecedenceType.P_LOWEST)
        if not self.expect_peek(TokenType.L_BRACE):
            return None
        statement.body = self.parse_block_statement()
        return statement

    def parse_for_statement(self) -> AST.ForStatement | None:
        if not self.expect_peek(TokenType.IDENTIFIER):
            return None
        variable = self.parse_identifier()
        if self.peek_token_is(TokenType.FROM):
            self.next_token()
            self.next_token()
            start = self.parse_expression(PrecedenceType.P_LOWEST)
            if not self.expect_peek(TokenType.TO):
                return None
            self.next_token()
            end = self.parse_expression(PrecedenceType.P_LOWEST)
            if not self.expect_peek(TokenType.L_BRACE):
                return None
            statement = AST.ForStatement(variable=variable, mode="range", start=start, end=end)
        elif self.peek_token_is(TokenType.IN):
            self.next_token()
            self.next_token()
            iterable = self.parse_expression(PrecedenceType.P_LOWEST)
            if not self.expect_peek(TokenType.L_BRACE):
                return None
            statement = AST.ForStatement(variable=variable, mode="array", iterable=iterable)
        else:
            self.peek_error(TokenType.FROM)
            return None
        statement.body = self.parse_block_statement()
        return statement

    def parse_repeat_statement(self) -> AST.RepeatStatement | None:
        if not self.expect_peek(TokenType.L_BRACE):
            return None
        body = self.parse_block_statement()
        self.next_token()
        count = self.parse_expression(PrecedenceType.P_LOWEST)
        if not self.expect_peek(TokenType.TIMES):
            return None
        return AST.RepeatStatement(count, body)

    def parse_block_statement(self) -> AST.BlockStatement:
        block = AST.BlockStatement()
        self.next_token()
        while self.current_token is not None and self.current_token.type not in (TokenType.R_BRACE, TokenType.EOF):
            statement = self.parse_statement()
            if statement is not None:
                block.statements.append(statement)
            self.next_token()
        return block

    def parse_expression_statement(self) -> AST.ExpressionStatement:
        expression = self.parse_expression(PrecedenceType.P_LOWEST)
        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()
        return AST.ExpressionStatement(expression)

    def parse_expression(self, precedence: PrecedenceType) -> AST.Expression | None:
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.literal == "address" and self.peek_token is not None and self.peek_token.literal == "of":
            return self.parse_address_of_expression()
        if self.current_token.type == TokenType.IDENTIFIER and self.current_token.literal == "value" and self.peek_token is not None and self.peek_token.literal == "at":
            return self.parse_value_at_expression()
        prefix = self.prefix_parse_fns.get(self.current_token.type)
        if prefix is None:
            self.no_prefix_parse_fn_error(self.current_token.type)
            return None
        left = prefix()
        while self.peek_token is not None and self.peek_token.type != TokenType.SEMICOLON and precedence.value < self.peek_precedence().value:
            infix = self.infix_parse_fns.get(self.peek_token.type)
            if infix is None:
                break
            self.next_token()
            left = infix(left)
        return left

    def parse_address_of_expression(self) -> AST.AddressOfExpression | None:
        self.next_token()
        self.next_token()
        if self.current_token.type != TokenType.IDENTIFIER:
            return None
        return AST.AddressOfExpression(AST.Identifier(self.current_token.literal))

    def parse_value_at_expression(self) -> AST.ValueAtExpression | None:
        self.next_token()
        self.next_token()
        if self.current_token.type != TokenType.IDENTIFIER:
            return None
        return AST.ValueAtExpression(AST.Identifier(self.current_token.literal))

    def parse_infix_expression(self, left: AST.Expression) -> AST.InfixExpression:
        expression = AST.InfixExpression(left, self.current_token.literal, None)
        precedence = self.current_precedence()
        self.next_token()
        expression.right_node = self.parse_expression(precedence)
        return expression

    def parse_prefix_expression(self) -> AST.PrefixExpression:
        operator = self.current_token.literal
        self.next_token()
        return AST.PrefixExpression(operator, self.parse_expression(PrecedenceType.P_PREFIX))

    def parse_grouped_expression(self) -> AST.Expression | None:
        self.next_token()
        expression = self.parse_expression(PrecedenceType.P_LOWEST)
        if not self.expect_peek(TokenType.R_PAREN):
            return None
        return expression

    def parse_array_literal(self) -> AST.ArrayLiteral | None:
        elements: list[AST.Expression] = []
        if self.peek_token_is(TokenType.R_BRACKET):
            self.next_token()
            return AST.ArrayLiteral(elements)
        self.next_token()
        elements.append(self.parse_expression(PrecedenceType.P_LOWEST))
        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            elements.append(self.parse_expression(PrecedenceType.P_LOWEST))
        if not self.expect_peek(TokenType.R_BRACKET):
            return None
        return AST.ArrayLiteral(elements)

    def parse_index_expression(self, array: AST.Expression) -> AST.IndexExpression | None:
        self.next_token()
        index = self.parse_expression(PrecedenceType.P_LOWEST)
        if not self.expect_peek(TokenType.R_BRACKET):
            return None
        return AST.IndexExpression(array, index)

    def parse_call_expression(self, function: AST.Expression) -> AST.CallExpression | None:
        arguments: list[AST.Expression] = []
        if self.peek_token_is(TokenType.R_PAREN):
            self.next_token()
            return AST.CallExpression(function, arguments)
        self.next_token()
        arguments.append(self.parse_expression(PrecedenceType.P_LOWEST))
        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()
            arguments.append(self.parse_expression(PrecedenceType.P_LOWEST))
        if not self.expect_peek(TokenType.R_PAREN):
            return None
        return AST.CallExpression(function, arguments)

    def parse_member_expression(self, target: AST.Expression) -> AST.MemberExpression | None:
        if not self.expect_peek(TokenType.IDENTIFIER):
            return None
        return AST.MemberExpression(target, self.current_token.literal)

    def parse_identifier(self) -> AST.Identifier:
        return AST.Identifier(self.current_token.literal)

    def parse_integer_literal(self) -> AST.IntegerLiteral | None:
        try:
            return AST.IntegerLiteral(int(self.current_token.literal))
        except ValueError:
            return None

    def parse_float_literal(self) -> AST.FloatLiteral | None:
        try:
            return AST.FloatLiteral(float(self.current_token.literal))
        except ValueError:
            return None

    def parse_boolean_literal(self) -> AST.BooleanLiteral:
        return AST.BooleanLiteral(self.current_token.type == TokenType.TRUE)

    def parse_string_literal(self) -> AST.StringLiteral:
        return AST.StringLiteral(self.current_token.literal)