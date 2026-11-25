
from itertools import product

import pytest

from lexer.dfa import DFA, regex_to_dfa
from lexer.dfa_minimizer import (
    minimize_dfa,
    regex_to_min_dfa,
)


@pytest.mark.parametrize(
    "pattern",
    [
        "a",
        "ab",
        "a|b",
        "a*",
        "a+",
        "(a|b)+c",
        "[0-9]+",
        "[a-zA-Z_][a-zA-Z0-9_]*",
    ],
)
def test_minimized_dfa_matches_original(pattern):
    """最小化不能改变原来的识别结果。"""

    original = regex_to_dfa(pattern)
    minimized = regex_to_min_dfa(pattern)

    # 穷举长度 0~3 的字符串
    for length in range(4):
        for chars in product(
            "abc01_", repeat=length
        ):
            text = "".join(chars)

            assert original.accepts(text) == (
                minimized.accepts(text)
            ), (
                f"Mismatch: {pattern!r}, {text!r}"
            )


def test_equivalent_states_are_merged():
    """验证两个等价接受态能够合并。"""

    dfa = DFA(
        start=0,
        accept_states={1, 2},
        transitions={
            0: {"a": 1, "b": 2},
            1: {"a": 1, "b": 1},
            2: {"a": 2, "b": 2},
        },
    )

    minimized = minimize_dfa(dfa)

    # 原来 3 个状态，最小化后应为 2 个
    assert len(minimized.transitions) == 2

    assert minimized.accepts("a")
    assert minimized.accepts("b")
    assert minimized.accepts("abba")
    assert not minimized.accepts("")


def test_unreachable_states_are_removed():
    """不可达状态不应该保留。"""

    dfa = DFA(
        start=0,
        accept_states={1, 3},
        transitions={
            0: {"a": 1},
            1: {"a": 1},
            3: {"a": 3},
        },
    )

    minimized = minimize_dfa(dfa)

    assert len(minimized.transitions) == 2
    assert minimized.accepts("a")
    assert not minimized.accepts("")


def test_missing_transitions_use_dead_state():
    """缺失的转移必须保持拒绝行为。"""

    dfa = DFA(
        start=0,
        accept_states={1},
        transitions={
            0: {"a": 1, "b": 0},
            1: {"a": 1},
        },
    )

    minimized = minimize_dfa(dfa)

    assert len(minimized.transitions) == 3
    assert minimized.accepts("a")
    assert minimized.accepts("aaa")
    assert not minimized.accepts("ab")
    assert not minimized.accepts("aab")
    assert not minimized.accepts("b")


def test_minimization_is_idempotent():
    """最小化两次不应继续改变 DFA。"""

    dfa = regex_to_dfa("(a|b)+c")

    first = minimize_dfa(dfa)
    second = minimize_dfa(first)

    assert first == second