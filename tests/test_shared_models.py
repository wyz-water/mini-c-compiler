"""校验模块之间约定的数据格式，不测试任何编译算法。"""

from shared import ASTNode, Quadruple, Token


def test_token_contract() -> None:
    token = Token("IDENT", "count", 1, 5)
    assert token.kind == "IDENT"
    assert token.lexeme == "count"
    assert (token.line, token.column) == (1, 5)


def test_ast_contract() -> None:
    expr = ASTNode(
        kind="BinaryOp",
        value="+",
        children=[
            ASTNode(kind="Number", value=2),
            ASTNode(kind="Number", value=3),
        ],
    )
    assign = ASTNode(kind="Assign", value="a", children=[expr])
    assert assign.children[0].kind == "BinaryOp"
    assert assign.children[0].children[1].value == 3


def test_quadruple_contract() -> None:
    quad = Quadruple(op="*", arg1=3, arg2=4, result="t1")
    assert (quad.op, quad.result) == ("*", "t1")
