
from dataclasses import dataclass

from lexer.regex_parser import RegexToken, regex_to_postfix


@dataclass(frozen=True)
class _Fragment:
    """Thompson 算法中的 NFA 片段。"""
    start: int
    accept: int


@dataclass
class NFA:
    """非确定有限自动机。"""

    start: int
    accept: int

    # None 表示 epsilon (ε) 转移
    transitions: dict[int, dict[str | None, set[int]]]

    def epsilon_closure(self, states: set[int]) -> set[int]:
        """计算状态集合的 epsilon 闭包。"""
        closure = set(states)
        stack = list(states)

        while stack:
            state = stack.pop()

            for target in self.transitions[state].get(None, set()):
                if target not in closure:
                    closure.add(target)
                    stack.append(target)

        return closure

    def accepts(self, text: str) -> bool:
        """模拟 NFA，判断完整字符串是否被接受。"""
        current = self.epsilon_closure({self.start})

        for char in text:
            next_states: set[int] = set()

            for state in current:
                next_states.update(
                    self.transitions[state].get(char, set())
                )

            current = self.epsilon_closure(next_states)

            if not current:
                return False

        return self.accept in current


def postfix_to_nfa(postfix: list[RegexToken]) -> NFA:
    """使用 Thompson 算法构造 NFA。"""

    transitions: dict[int, dict[str | None, set[int]]] = {}
    next_id = 0
    stack: list[_Fragment] = []

    def new_state() -> int:
        nonlocal next_id

        state = next_id
        next_id += 1
        transitions[state] = {}

        return state

    def add_edge(
        source: int,
        symbol: str | None,
        target: int,
    ) -> None:
        transitions[source].setdefault(symbol, set()).add(target)

    for token in postfix:
        kind = token.kind

        # 1. 普通字符和字符集合
        if kind in {"LITERAL", "CHAR_CLASS"}:
            start = new_state()
            accept = new_state()

            if kind == "LITERAL":
                if (
                    not isinstance(token.value, str)
                    or len(token.value) != 1
                ):
                    raise ValueError("Invalid literal token")

                add_edge(start, token.value, accept)

            else:
                if (
                    not isinstance(token.value, frozenset)
                    or not token.value
                ):
                    raise ValueError("Invalid character class token")

                for char in token.value:
                    add_edge(start, char, accept)

            stack.append(_Fragment(start, accept))

        # 2. 连接与选择运算
        elif kind in {"CONCAT", "OR"}:
            if len(stack) < 2:
                raise ValueError(
                    f"{kind} requires two operands"
                )

            right = stack.pop()
            left = stack.pop()

            if kind == "CONCAT":
                add_edge(left.accept, None, right.start)

                stack.append(
                    _Fragment(left.start, right.accept)
                )

            else:
                start = new_state()
                accept = new_state()

                add_edge(start, None, left.start)
                add_edge(start, None, right.start)

                add_edge(left.accept, None, accept)
                add_edge(right.accept, None, accept)

                stack.append(_Fragment(start, accept))

        # 3. Kleene 闭包与一次或多次重复
        elif kind in {"STAR", "PLUS"}:
            if not stack:
                raise ValueError(
                    f"{kind} requires one operand"
                )

            part = stack.pop()
            start = new_state()
            accept = new_state()

            add_edge(start, None, part.start)

            # STAR 可以不读取任何字符
            if kind == "STAR":
                add_edge(start, None, accept)

            # 重复前面的表达式
            add_edge(part.accept, None, part.start)

            # 结束重复
            add_edge(part.accept, None, accept)

            stack.append(_Fragment(start, accept))

        else:
            raise ValueError(
                f"Unsupported token kind: {kind}"
            )

    if len(stack) != 1:
        raise ValueError(
            "Invalid postfix regular expression"
        )

    result = stack.pop()

    return NFA(
        start=result.start,
        accept=result.accept,
        transitions=transitions,
    )


def regex_to_nfa(pattern: str) -> NFA:
    """普通正则表达式 -> 后缀表达式 -> NFA。"""
    postfix = regex_to_postfix(pattern)
    return postfix_to_nfa(postfix)