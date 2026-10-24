from Token import Token, TokenType, lookup_identifier
from typing import Any

class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position : int = -1
        self.read_position : int = 0
        self.line_num : int = 1
        self.current_char : str | None = None
        self.read_char()

    def read_char(self) -> None:
        if self.read_position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.read_position]
        self.position = self.read_position
        self.read_position += 1

    def skip_whitespace(self) -> None:
        while self.current_char in [' ', '\t', '\n', '\r']:
            if self.current_char == '\n':
                self.line_num += 1
            self.read_char()

    def new_token(self, type: TokenType, literal: Any) -> Token:
        return Token(type=type, literal=literal, line_num=self.line_num, position=self.position)

    def is_digit(self, char: str) -> bool:
        return '0' <= char <= '9'

    def is_letter(self, char: str) -> bool:
        return 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char == '_'

    def read_number(self) -> Token:
        start_position : int = self.position
        dot_count : int = 0
        output : str = ""
        while self.current_char is not None and (self.is_digit(self.current_char) or self.current_char == '.'):
            if self.current_char == '.':
                dot_count += 1
                if dot_count > 1:
                    print(f"Error: Too many decimal points on line {self.line_num}, position {self.position}.")
                    return self.new_token(TokenType.ILLEGAL, self.source[start_position:self.position + 1])
            output += self.source[self.position]
            self.read_char()
        if dot_count == 0:
            return self.new_token(TokenType.INT, int(output))
        else:
            return self.new_token(TokenType.FLOAT, float(output))

    def read_identifier(self) -> str:
        position = self.position
        while self.current_char is not None and (self.is_letter(self.current_char) or self.is_digit(self.current_char)):
            self.read_char()
        return self.source[position:self.position]

    def next_token(self) -> Token:
        token: Token = None
        self.skip_whitespace()

        if self.current_char == '+':
            token = self.new_token(TokenType.PLUS, self.current_char)
        elif self.current_char == '-':
            token = self.new_token(TokenType.MINUS, self.current_char)
        elif self.current_char == '*':
            token = self.new_token(TokenType.ASTERISK, self.current_char)
        elif self.current_char == '/':
            token = self.new_token(TokenType.SLASH, self.current_char)
        elif self.current_char == '^':
            token = self.new_token(TokenType.POWER, self.current_char)
        elif self.current_char == '%':
            token = self.new_token(TokenType.MODULUS, self.current_char)
        elif self.current_char == '=':
            # Clean direct character check for double equals '==' without any method calls
            if self.read_position < len(self.source) and self.source[self.read_position] == '=':
                self.read_char() # Consume first '='
                token = self.new_token(TokenType.EQ_COMP, "==")
            else:
                token = self.new_token(TokenType.ASSIGN, self.current_char)
        elif self.current_char == '&' and self.read_position < len(self.source) and self.source[self.read_position] == '&':
            self.read_char()
            token = self.new_token(TokenType.AND, "&&")
        elif self.current_char == '|' and self.read_position < len(self.source) and self.source[self.read_position] == '|':
            self.read_char()
            token = self.new_token(TokenType.OR, "||")
        elif self.current_char == '!':
            if self.read_position < len(self.source) and self.source[self.read_position] == '=':
                self.read_char()
                token = self.new_token(TokenType.NEQ, "!=")
            else:
                token = self.new_token(TokenType.NOT, "!")
        elif self.current_char == '>':
            if self.read_position < len(self.source) and self.source[self.read_position] == '=':
                self.read_char()
                token = self.new_token(TokenType.GTE, ">=")
            else:
                token = self.new_token(TokenType.GT, self.current_char)
        elif self.current_char == '<':
            if self.read_position < len(self.source) and self.source[self.read_position] == '=':
                self.read_char()
                token = self.new_token(TokenType.LTE, "<=")
            else:
                token = self.new_token(TokenType.LT, self.current_char)
        elif self.current_char == '(':
            token = self.new_token(TokenType.L_PAREN, self.current_char)
        elif self.current_char == ')':
            token = self.new_token(TokenType.R_PAREN, self.current_char)
        elif self.current_char == '{':
            token = self.new_token(TokenType.L_BRACE, self.current_char)
        elif self.current_char == '}':
            token = self.new_token(TokenType.R_BRACE, self.current_char)
        elif self.current_char == '[':
            token = self.new_token(TokenType.L_BRACKET, self.current_char)
        elif self.current_char == ']':
            token = self.new_token(TokenType.R_BRACKET, self.current_char)
        elif self.current_char == ';':
            token = self.new_token(TokenType.SEMICOLON, self.current_char)
        elif self.current_char == ':':
            token = self.new_token(TokenType.COLON, self.current_char)
        elif self.current_char == '.':
            token = self.new_token(TokenType.DOT, self.current_char)
        elif self.current_char == ',':
            token = self.new_token(TokenType.COMMA, self.current_char)
        elif self.current_char == '"':
            self.read_char()  
            start_pos = self.position
            while self.current_char is not None and self.current_char != '"':
                if self.current_char == '\n':
                    self.line_num += 1
                self.read_char()
            literal = self.source[start_pos:self.position]
            self.read_char()  
            return self.new_token(TokenType.STRING, literal)
        elif self.current_char is None:
            token = self.new_token(TokenType.EOF, '')
        else:
            if self.current_char is not None and self.is_letter(self.current_char):
                literal : str = self.read_identifier()
                token_type : TokenType = lookup_identifier(literal)
                token = self.new_token(type=token_type, literal=literal)
                return token
            elif self.current_char is not None and self.is_digit(self.current_char):
                token = self.read_number()
                return token
            else:
                token = self.new_token(TokenType.ILLEGAL, f"Illegal character: {self.current_char}")

        self.read_char()
        return token
