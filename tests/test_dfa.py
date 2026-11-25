
from itertools import product

import pytest

from lexer.nfa import regex_to_nfa
from lexer.dfa import nfa_to_dfa, regex_to_dfa


@pytest.mark.parametrize(
    "pattern, accepted, rejected",
    [
        ("a", ["a"], ["", "b", "aa"]),
        ("ab", ["ab"], ["", "a", "b", "aba"]),
        ("a|b", ["a", "b"], ["", "ab", "c"]),
        ("a*", ["", "a", "aaa"], ["b", "ab"]),
        ("a+", ["a", "aaa"], ["", "b", "ab"]),

        (
            "(a|b)+c",
            ["ac", "bc", "abc", "abbac"],
            ["", "c", "ab", "ca"],
        ),

        (
            "[0-9]+",
            ["0", "123", "45678"],
            ["", "abc", "12a"],
        ),

        (
            "[a-zA-Z_][a-zA-Z0-9_]*",
            ["a", "_name", "count123"],
            ["", "123abc", "a-b"],
        ),
    ],
)
def test_regex_to_dfa(pattern, accepted, rejected):
    dfa = regex_to_dfa(pattern)

    for text in accepted:
        assert dfa.accepts(text), (
            f"{pattern!r} should accept {text!r}"
        )

    for text in rejected:
        assert not dfa.accepts(text), (
            f"{pattern!r} should reject {text!r}"
        )


def test_dfa_matches_nfa():
    """验证 NFA 和 DFA 对相同输入给出相同结果。"""

    patterns = [
        "a",
        "ab",
        "a|b",
        "a*",
        "a+",
        "(a|b)+c",
        "[0-9]+",
    ]

    for pattern in patterns:
        nfa = regex_to_nfa(pattern)
        dfa = nfa_to_dfa(nfa)

        # 穷举长度 0~3 的测试字符串
        for length in range(4):
            for chars in product("abc01", repeat=length):
                text = "".join(chars)

                assert nfa.accepts(text) == dfa.accepts(text), (
                    f"Mismatch: {pattern!r}, {text!r}"
                )


def test_dfa_has_deterministic_transitions():
    """每个状态对同一字符只有一个目标状态。"""

    dfa = regex_to_dfa("a|ab")

    for edges in dfa.transitions.values():
        for target in edges.values():
            assert isinstance(target, int)
            assert target in dfa.transitions