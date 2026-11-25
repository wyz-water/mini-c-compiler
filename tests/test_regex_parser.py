import pytest

from lexer.regex_parser import (
    RegexToken,
    regex_to_postfix,
    tokenize_regex,
    insert_concat,
)

def t(kind, value=None):
    return RegexToken(kind, value)


def test_single_character():
    result = regex_to_postfix("a")
    assert result == [t("LITERAL", "a")]


def test_concatenation():
    result = regex_to_postfix("ab")
    assert result == [
        t("LITERAL", "a"),
        t("LITERAL", "b"),
        t("CONCAT"),
    ]


def test_alternation():
    result = regex_to_postfix("a|b")
    assert result == [
        t("LITERAL", "a"),
        t("LITERAL", "b"),
        t("OR"),
    ]


def test_kleene_star():
    result = regex_to_postfix("a*")
    assert result == [
        t("LITERAL", "a"),
        t("STAR"),
    ]


def test_complex_expression():
    result = regex_to_postfix("a(b|c)*")
    assert result == [
        t("LITERAL", "a"),
        t("LITERAL", "b"),
        t("LITERAL", "c"),
        t("OR"),
        t("STAR"),
        t("CONCAT"),
    ]
    
    
def test_tokenize_regex():
    result = tokenize_regex("a(b|c)*")

    expected = [
        RegexToken("LITERAL", "a"),
        RegexToken("LPAREN"),
        RegexToken("LITERAL", "b"),
        RegexToken("OR"),
        RegexToken("LITERAL", "c"),
        RegexToken("RPAREN"),
        RegexToken("STAR"),
    ]

    assert result == expected
    
def test_insert_concat():
    tokens = tokenize_regex("ab")
    result = insert_concat(tokens)

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("CONCAT"),
        RegexToken("LITERAL", "b"),
    ]


def test_insert_concat_complex():
    tokens = tokenize_regex("a(b|c)*")
    result = insert_concat(tokens)

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("CONCAT"),
        RegexToken("LPAREN"),
        RegexToken("LITERAL", "b"),
        RegexToken("OR"),
        RegexToken("LITERAL", "c"),
        RegexToken("RPAREN"),
        RegexToken("STAR"),
    ]


def test_tokenize_escaped_operator():
    """测试转义字符能否被识别为普通字符。"""

    # \* 表示普通星号，而不是 Kleene 闭包
    result = tokenize_regex(r"\*")

    expected = [
        RegexToken("LITERAL", "*")
    ]

    assert result == expected


def test_tokenize_escaped_parenthesis():
    """测试转义括号。"""

    result = tokenize_regex(r"\(")

    expected = [
        RegexToken("LITERAL", "(")
    ]

    assert result == expected
    

def test_operator_precedence():
    result = regex_to_postfix("a|bc")

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("LITERAL", "b"),
        RegexToken("LITERAL", "c"),
        RegexToken("CONCAT"),
        RegexToken("OR"),
    ]
    
    
def test_char_class_digits():
    result = tokenize_regex("[0-9]")

    assert result == [
        RegexToken(
            "CHAR_CLASS",
            frozenset("0123456789")
        )
    ]


def test_char_class_identifier():
    result = tokenize_regex("[a-zA-Z_]")

    expected_chars = frozenset(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    )

    assert result == [
        RegexToken("CHAR_CLASS", expected_chars)
    ]


def test_char_class_concat():
    result = regex_to_postfix("a[0-2]")

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("CHAR_CLASS", frozenset("012")),
        RegexToken("CONCAT"),
    ]


def test_identifier_regex_postfix():
    result = regex_to_postfix(
        "[a-zA-Z_][a-zA-Z0-9_]*"
    )

    first = frozenset(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    )

    second = first | frozenset("0123456789")

    assert result == [
        RegexToken("CHAR_CLASS", first),
        RegexToken("CHAR_CLASS", second),
        RegexToken("STAR"),
        RegexToken("CONCAT"),
    ]
    
def test_tokenize_plus():
    result = tokenize_regex("a+")

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("PLUS"),
    ]


def test_plus_postfix():
    result = regex_to_postfix("a+")

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("PLUS"),
    ]


def test_plus_char_class():
    result = regex_to_postfix("[0-9]+")

    assert result == [
        RegexToken(
            "CHAR_CLASS",
            frozenset("0123456789")
        ),
        RegexToken("PLUS"),
    ]


def test_plus_concat():
    result = regex_to_postfix("a+b")

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("PLUS"),
        RegexToken("LITERAL", "b"),
        RegexToken("CONCAT"),
    ]


def test_plus_group():
    result = regex_to_postfix("(a|b)+c")

    assert result == [
        RegexToken("LITERAL", "a"),
        RegexToken("LITERAL", "b"),
        RegexToken("OR"),
        RegexToken("PLUS"),
        RegexToken("LITERAL", "c"),
        RegexToken("CONCAT"),
    ]


def test_plus_without_operand():
    with pytest.raises(ValueError):
        regex_to_postfix("+a")