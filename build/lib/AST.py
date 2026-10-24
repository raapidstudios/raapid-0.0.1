from abc import ABC, abstractmethod
from enum import Enum

class NodeType(Enum):
    Program = "Program"
    ExpressionStatement = "ExpressionStatement"
    LetStatement = "LetStatement"
    SayStatement = "SayStatement"
    AskStatement = "AskStatement"
    SetStatement = "SetStatement"
    FunctionStatement = "FunctionStatement"
    ReturnStatement = "ReturnStatement"
    IfStatement = "IfStatement"
    WhileStatement = "WhileStatement"
    ForStatement = "ForStatement"
    MakeStatement = "MakeStatement"
    GiveStatement = "GiveStatement"
    ReturningStatement = "ReturningStatement"
    RepeatStatement = "RepeatStatement"
    ImportStatement = "ImportStatement"
    BlockStatement = "BlockStatement"
    InfixExpression = "InfixExpression"
    Identifier = "Identifier"
    AddressOfExpression = "AddressOfExpression"
    ValueAtExpression = "ValueAtExpression"
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    StringLiteral = "StringLiteral"
    BooleanLiteral = "BooleanLiteral"
    ArrayLiteral = "ArrayLiteral"
    IndexExpression = "IndexExpression"
    CallExpression = "CallExpression"
    PrefixExpression = "PrefixExpression"
    MemberExpression = "MemberExpression"

class Node(ABC):    
    @abstractmethod
    def type(self) -> NodeType:
        pass
    @abstractmethod
    def json(self) -> dict:
        pass

class Statement(Node):
    pass
class Expression(Node):
    pass

class Program(Node):
    def __init__(self) -> None:
        self.statements : list[Statement] = []
    def type(self) -> NodeType:
        return NodeType.Program
    def json(self) -> dict:
        return {"type": self.type().value, "statements": [{stmt.type().value: stmt.json()} for stmt in self.statements]}

class ExpressionStatement(Statement):
    def __init__(self, expression: Expression = None) -> None:
        self.expression : Expression = expression
    def type(self) -> NodeType:
        return NodeType.ExpressionStatement
    def json(self) -> dict:
        return {"type": self.type().value, "expression": self.expression.json() if self.expression else None}

class LetStatement(Statement):
    def __init__(self, name: 'Identifier' = None, value: Expression = None) -> None:
        self.name : Identifier = name
        self.value : Expression = value
    def type(self) -> NodeType:
        return NodeType.LetStatement
    def json(self) -> dict:
        return {"type": self.type().value, "name": self.name.json() if self.name else None, "value": self.value.json() if self.value else None}

class SayStatement(Statement):
    def __init__(self, expression: Expression = None) -> None:
        self.expression : Expression = expression
        self.expressions : list[Expression] = [expression] if expression is not None else []
    def type(self) -> NodeType:
        return NodeType.SayStatement
    def json(self) -> dict:
        return {"type": self.type().value, "expressions": [expression.json() for expression in self.expressions]}

class SetStatement(Statement):
    def __init__(self, target: Expression = None, value: Expression = None) -> None:
        self.target : Expression = target
        self.value : Expression = value
    def type(self) -> NodeType:
        return NodeType.SetStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "target": self.target.json() if self.target else None,
            "value": self.value.json() if self.value else None
        }

class AskStatement(Statement):
    def __init__(self, prompt: Expression = None, name: 'Identifier' = None, var_type: str | None = None) -> None:
        self.prompt : Expression = prompt       # StringLiteral
        self.name : Identifier = name           # Identifier ("age")
        self.var_type : str = var_type          # Type string ("int")
        
    def type(self) -> NodeType:
        return NodeType.AskStatement
        
    def json(self) -> dict:
        return {
            "type": self.type().value, 
            "prompt": self.prompt.json() if self.prompt else None, 
            "name": self.name.json() if self.name else None,
            "var_type": self.var_type
        }

class BlockStatement(Statement):
    def __init__(self) -> None:
        self.statements: list[Statement] = []
    def type(self) -> NodeType:
        return NodeType.BlockStatement
    def json(self) -> dict:
        return {"type": self.type().value, "statements": [{stmt.type().value: stmt.json()} for stmt in self.statements]}

class IfStatement(Statement):
    def __init__(self, condition: Expression = None, consequence: BlockStatement = None, alternative: Node = None) -> None:
        self.condition: Expression = condition
        self.consequence: BlockStatement = consequence
        self.alternative: Node = alternative
    def type(self) -> NodeType:
        return NodeType.IfStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "condition": self.condition.json() if self.condition else None,
            "consequence": self.consequence.json() if self.consequence else None,
            "alternative": self.alternative.json() if self.alternative else None
        }

class WhileStatement(Statement):
    def __init__(self, condition: Expression = None, body: BlockStatement = None) -> None:
        self.condition: Expression = condition
        self.body: BlockStatement = body
    def type(self) -> NodeType:
        return NodeType.WhileStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "condition": self.condition.json() if self.condition else None,
            "body": self.body.json() if self.body else None
        }

class ForStatement(Statement):
    def __init__(self, variable: 'Identifier' = None, body: BlockStatement = None, mode: str = "range", start: Expression = None, end: Expression = None, iterable: Expression = None) -> None:
        self.variable: Identifier = variable
        self.body: BlockStatement = body
        self.mode: str = mode
        self.start: Expression = start
        self.end: Expression = end
        self.iterable: Expression = iterable
    def type(self) -> NodeType:
        return NodeType.ForStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "mode": self.mode,
            "variable": self.variable.json() if self.variable else None,
            "start": self.start.json() if self.start else None,
            "end": self.end.json() if self.end else None,
            "iterable": self.iterable.json() if self.iterable else None,
            "body": self.body.json() if self.body else None
        }

class RepeatStatement(Statement):
    def __init__(self, count: Expression = None, body: BlockStatement = None) -> None:
        self.count: Expression = count
        self.body: BlockStatement = body
    def type(self) -> NodeType:
        return NodeType.RepeatStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "count": self.count.json() if self.count else None,
            "body": self.body.json() if self.body else None
        }

class ImportStatement(Statement):
    def __init__(self, module_name: str, alias: str | None = None) -> None:
        self.module_name: str = module_name
        self.alias: str | None = alias
    def type(self) -> NodeType:
        return NodeType.ImportStatement
    def json(self) -> dict:
        return {"type": self.type().value, "module_name": self.module_name, "alias": self.alias}

class MakeStatement(Statement):
    def __init__(self, name: 'Identifier' = None, value: Expression = None) -> None:
        self.name : Identifier = name
        self.value : Expression = value
    def type(self) -> NodeType:
        return NodeType.MakeStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json() if self.name else None,
            "value": self.value.json() if self.value else None
        }

class GiveStatement(Statement):
    def __init__(self, value: Expression = None) -> None:
        self.value : Expression = value
    def type(self) -> NodeType:
        return NodeType.GiveStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value.json() if self.value else None
        }

class ReturningStatement(Statement):
    def __init__(self, value: Expression = None) -> None:
        self.value : Expression = value
    def type(self) -> NodeType:
        return NodeType.ReturningStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value.json() if self.value else None
        }

class FunctionParameter:
    def __init__(self, name: str, type_name: str | None = None) -> None:
        self.name: str = name
        self.type_name: str = type_name
    def json(self) -> dict:
        return {"name": self.name, "type": self.type_name}

class FunctionStatement(Statement):
    def __init__(self, name: str, parameters: list[FunctionParameter], return_type: str | None, body: BlockStatement) -> None:
        self.name: str = name
        self.parameters: list[FunctionParameter] = parameters
        self.return_type: str = return_type
        self.body: BlockStatement = body
    def type(self) -> NodeType:
        return NodeType.FunctionStatement
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name,
            "parameters": [parameter.json() for parameter in self.parameters],
            "return_type": self.return_type,
            "body": self.body.json()
        }

class ReturnStatement(Statement):
    def __init__(self, value: Expression = None) -> None:
        self.value: Expression = value
    def type(self) -> NodeType:
        return NodeType.ReturnStatement
    def json(self) -> dict:
        return {"type": self.type().value, "value": self.value.json() if self.value else None}

class Identifier(Expression):
    def __init__(self, value: str = None) -> None:
        self.value : str = value
    def type(self) -> NodeType:
        return NodeType.Identifier
    def json(self) -> dict:
        return {"type": self.type().value, "value": self.value}

class AddressOfExpression(Expression):
    def __init__(self, target: Identifier = None) -> None:
        self.target : Identifier = target
    def type(self) -> NodeType:
        return NodeType.AddressOfExpression
    def json(self) -> dict:
        return {"type": self.type().value, "target": self.target.json() if self.target else None}

class ValueAtExpression(Expression):
    def __init__(self, pointer: Identifier = None) -> None:
        self.pointer : Identifier = pointer
    def type(self) -> NodeType:
        return NodeType.ValueAtExpression
    def json(self) -> dict:
        return {"type": self.type().value, "pointer": self.pointer.json() if self.pointer else None}

class InfixExpression(Expression):
    def __init__(self, left_node: Expression, operator: str, right_node: Expression) -> None:
        self.left_node : Expression = left_node
        self.operator : str = operator
        self.right_node : Expression = right_node
    def type(self) -> NodeType:
        return NodeType.InfixExpression
    def json(self) -> dict:
        return {"type": self.type().value, "left_node": self.left_node.json() if self.left_node else None, "operator": self.operator, "right_node": self.right_node.json() if self.right_node else None}

class IntegerLiteral(Expression):
    def __init__(self, value: int = None) -> None:
        self.value : int = value
    def type(self) -> NodeType:
        return NodeType.IntegerLiteral
    def json(self) -> dict:
        return {"type": self.type().value, "value": self.value}

class FloatLiteral(Expression):
    def __init__(self, value: float = None) -> None:
        self.value : float = value
    def type(self) -> NodeType:
        return NodeType.FloatLiteral
    def json(self) -> dict:
        return {"type": self.type().value, "value": self.value}

class StringLiteral(Expression):
    def __init__(self, value: str = "") -> None:
        self.value : str = value
    def type(self) -> NodeType:
        return NodeType.StringLiteral
    def json(self) -> dict:
        return {"type": self.type().value, "value": self.value}

class BooleanLiteral(Expression):
    def __init__(self, value: bool = False) -> None:
        self.value : bool = value
    def type(self) -> NodeType:
        return NodeType.BooleanLiteral
    def json(self) -> dict:
        return {"type": self.type().value, "value": self.value}

class ArrayLiteral(Expression):
    def __init__(self, elements: list[Expression] | None = None) -> None:
        self.elements: list[Expression] = elements or []
    def type(self) -> NodeType:
        return NodeType.ArrayLiteral
    def json(self) -> dict:
        return {"type": self.type().value, "elements": [element.json() for element in self.elements]}

class IndexExpression(Expression):
    def __init__(self, array: Expression = None, index: Expression = None) -> None:
        self.array: Expression = array
        self.index: Expression = index
    def type(self) -> NodeType:
        return NodeType.IndexExpression
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "array": self.array.json() if self.array else None,
            "index": self.index.json() if self.index else None
        }

class CallExpression(Expression):
    def __init__(self, function: Expression = None, arguments: list[Expression] | None = None) -> None:
        self.function: Expression = function
        self.arguments: list[Expression] = arguments or []
    def type(self) -> NodeType:
        return NodeType.CallExpression
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "function": self.function.json() if self.function else None,
            "arguments": [argument.json() for argument in self.arguments]
        }

class PrefixExpression(Expression):
    def __init__(self, operator: str, right: Expression) -> None:
        self.operator: str = operator
        self.right: Expression = right
    def type(self) -> NodeType:
        return NodeType.PrefixExpression
    def json(self) -> dict:
        return {"type": self.type().value, "operator": self.operator, "right": self.right.json()}

class MemberExpression(Expression):
    def __init__(self, target: Expression, member: str) -> None:
        self.target: Expression = target
        self.member: str = member
    def type(self) -> NodeType:
        return NodeType.MemberExpression
    def json(self) -> dict:
        return {"type": self.type().value, "target": self.target.json(), "member": self.member}