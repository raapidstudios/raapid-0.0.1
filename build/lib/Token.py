from enum import Enum
from typing import Any

class TokenType(Enum):
    L_BRACE = "{"
    R_BRACE = "}"
    L_BRACKET = "["
    R_BRACKET = "]"
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    IDENTIFIER = "IDENTIFIER"
    COMMA = ","
    SEMICOLON = ";"
    COLON = ":"
    DOT = "."
    EQ = "="
    PLUS = "+"
    MINUS = "-"
    ASTERISK = "*"
    SLASH = "/"
    POWER = "^"
    ASSIGN = "="
    L_PAREN = "("
    R_PAREN = ")"
    MODULUS = "%"
    TYPE_INT = "int"
    TYPE_FLOAT = "float"
    TYPE_STRING = "string"
    TYPE_BOOLEAN = "boolean"
    TRUE = "true"
    FALSE = "false"
    LET = "let"
    SET = "set"
    FUNCTION = "function"
    RETURN = "return"
    TYPE_VOID = "void"
    TYPE_NONE = "none"
    SAY = "say"
    ASK = "ask"
    ELIF = "elif"
    ELSE = "else"
    MAKE = "make"
    RETURNING = "returning"
    GIVE = "give"
    TO = "to"
    GT = ">"
    LT = "<"
    EQ_COMP = "=="
    LTE = "<="
    GTE = ">="
    NEQ = "!="
    AND = "and"
    OR = "or"
    NOT = "not"
    IF = "if"
    WHILE = "while"
    FOR = "for"
    FROM = "from"
    IN = "in"
    REPEAT = "repeat"
    TIMES = "times"
    IMPORT = "import"
    AS = "as"

class Token:
    def __init__(self, type: TokenType, literal: Any, line_num: int, position: int) -> None:
        self.type = type
        self.literal = literal
        self.line_num = line_num
        self.position = position

    def __str__(self) -> str:
        return f"Token(type={self.type}, literal={self.literal}, line_num={self.line_num}, position={self.position})"

    def __repr__(self) -> str:
        return str(self)

KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "say": TokenType.SAY,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "ask": TokenType.ASK,
    "set": TokenType.SET,
    "function": TokenType.FUNCTION,
    "return": TokenType.RETURN,
    "void": TokenType.TYPE_VOID,
    "none": TokenType.TYPE_NONE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "to": TokenType.TO,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "from": TokenType.FROM,
    "in": TokenType.IN,
    "repeat": TokenType.REPEAT,
    "times": TokenType.TIMES,
    "import": TokenType.IMPORT,
    "as": TokenType.AS,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "make": TokenType.MAKE,
    "returning": TokenType.RETURNING,
    "give": TokenType.GIVE,
}

ALT_KEYWORDS: dict[str, TokenType] = {
    "is": TokenType.EQ,
    "be": TokenType.EQ,
}

TYPE_KEYWORDS: list[str] = ["int", "float", "string", "boolean"]

def lookup_identifier(identifier: str) -> TokenType:
    token_type = KEYWORDS.get(identifier)
    if token_type is not None:
        return token_type
    token_type = ALT_KEYWORDS.get(identifier)
    if token_type is not None:
        return token_type
    if identifier == "int":
        return TokenType.TYPE_INT
    elif identifier == "float":
        return TokenType.TYPE_FLOAT
    elif identifier == "string":
        return TokenType.TYPE_STRING
    elif identifier == "boolean":
        return TokenType.TYPE_BOOLEAN
    elif identifier == "void":
        return TokenType.TYPE_VOID
    elif identifier == "none":
        return TokenType.TYPE_NONE
    return TokenType.IDENTIFIER
