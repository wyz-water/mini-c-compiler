
import pytest

from lexer.nfa import regex_to_nfa


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
def test_regex_to_nfa(pattern, accepted, rejected):
    nfa = regex_to_nfa(pattern)

    for text in accepted:
        assert nfa.accepts(text), (
            f"{pattern!r} should accept {text!r}"
        )

    for text in rejected:
        assert not nfa.accepts(text), (
            f"{pattern!r} should reject {text!r}"
        )