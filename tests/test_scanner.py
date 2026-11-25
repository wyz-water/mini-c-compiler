
import json

import pytest

from lexer.scanner import (
    DEFAULT_RULES,
    LexerGenerator,
    LexerRule,
    LexicalError,
)
from shared.models import Token


@pytest.fixture(scope="module")
def scanner():
    return LexerGenerator.from_json(
        DEFAULT_RULES
    ).build()


def test_basic_program(scanner):
    result = scanner.scan("int a = 10;")

    assert result == [
        Token("INT", "int", 1, 1),
        Token("IDENT", "a", 1, 5),
        Token("ASSIGN", "=", 1, 7),
        Token("NUMBER", "10", 1, 9),
        Token("SEMI", ";", 1, 11),
        Token("EOF", "", 1, 12),
    ]


def test_keyword_priority(scanner):
    result = scanner.scan(
        "int ifx if else while read write int2"
    )

    assert [token.kind for token in result] == [
        "INT", "IDENT", "IF", "ELSE",
        "WHILE", "READ", "WRITE",
        "IDENT", "EOF",
    ]


def test_longest_match(scanner):
    result = scanner.scan(
        "intx >= 10 == 10 != 9;"
    )

    assert [token.kind for token in result] == [
        "IDENT", "GE", "NUMBER",
        "EQ", "NUMBER", "NE",
        "NUMBER", "SEMI", "EOF",
    ]


def test_operators(scanner):
    result = scanner.scan("a+b*c/(2-1);")

    assert [token.kind for token in result] == [
        "IDENT", "PLUS", "IDENT",
        "MUL", "IDENT", "DIV",
        "LPAREN", "NUMBER", "MINUS",
        "NUMBER", "RPAREN", "SEMI",
        "EOF",
    ]


def test_line_and_column(scanner):
    result = scanner.scan(
        "int x;\r\nwrite(x);\n"
    )

    assert Token("INT", "int", 1, 1) in result
    assert Token("WRITE", "write", 2, 1) in result
    assert result[-1] == Token("EOF", "", 3, 1)


def test_invalid_character(scanner):
    with pytest.raises(LexicalError) as exc:
        scanner.scan("int x = @;")

    assert exc.value.phase == "lexer"
    assert exc.value.line == 1
    assert exc.value.column == 9


def test_custom_rule_file(tmp_path):
    """改变规则文件即可生成不同的扫描器。"""

    path = tmp_path / "custom_rules.json"

    path.write_text(
        json.dumps([
            {"kind": "WORD", "pattern": "ab+"},
            {"kind": "A", "pattern": "a"},
            {
                "kind": "SPACE",
                "pattern": "[ ]+",
                "skip": True,
            },
        ]),
        encoding="utf-8",
    )

    custom = LexerGenerator.from_json(path).build()

    assert custom.scan("abbb a") == [
        Token("WORD", "abbb", 1, 1),
        Token("A", "a", 1, 6),
        Token("EOF", "", 1, 7),
    ]


def test_empty_matching_rule_rejected():
    """禁止可能匹配空字符串的词法规则。"""

    generator = LexerGenerator([
        LexerRule("BAD", "a*")
    ])

    with pytest.raises(ValueError):
        generator.build()