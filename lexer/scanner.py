
import json
from dataclasses import dataclass
from pathlib import Path

from lexer.dfa import DFA
from lexer.dfa_minimizer import regex_to_min_dfa
from shared.models import Token


DEFAULT_RULES = (
    Path(__file__).resolve().parent.parent
    / "rules"
    / "lexer.json"
)


@dataclass(frozen=True)
class LexerRule:
    kind: str
    pattern: str
    skip: bool = False


class LexicalError(ValueError):
    """词法分析错误。"""

    def __init__(
        self,
        line: int,
        column: int,
        char: str,
    ):
        self.phase = "lexer"
        self.line = line
        self.column = column
        self.message = f"Illegal character {char!r}"

        super().__init__(
            f"Lexer error at {line}:{column}: "
            f"{self.message}"
        )


def _live_states(dfa: DFA) -> set[int]:
    """找出仍有机会到达接受态的 DFA 状态。"""

    incoming: dict[int, set[int]] = {}

    for source, edges in dfa.transitions.items():
        for target in edges.values():
            incoming.setdefault(target, set()).add(source)

    live = set(dfa.accept_states)
    stack = list(live)

    while stack:
        state = stack.pop()

        for previous in incoming.get(state, set()):
            if previous not in live:
                live.add(previous)
                stack.append(previous)

    return live


class Scanner:
    """由词法规则生成的扫描器。"""

    def __init__(
        self,
        compiled: list[
            tuple[LexerRule, DFA, set[int]]
        ],
    ):
        self.compiled = compiled

    def scan(self, source: str) -> list[Token]:
        """扫描 mini-C 源代码，输出 Token 序列。"""

        tokens: list[Token] = []
        position = 0
        line = 1
        column = 1

        while position < len(source):
            best_rule = None
            best_length = 0

            # 逐条尝试规则
            for rule, dfa, live in self.compiled:
                state = dfa.start
                end = position

                while (
                    end < len(source)
                    and state in live
                ):
                    char = source[end]

                    target = dfa.transitions[state].get(char)

                    if target is None:
                        break

                    state = target
                    end += 1

                    # 记录当前最长的完整匹配
                    length = end - position

                    if (
                        state in dfa.accept_states
                        and length > best_length
                    ):
                        best_rule = rule
                        best_length = length

            # 所有规则均无法匹配
            if best_rule is None:
                raise LexicalError(
                    line, column, source[position]
                )

            lexeme = source[
                position:position + best_length
            ]

            # 在更新位置之前记录 Token 的起点
            if not best_rule.skip:
                tokens.append(
                    Token(
                        kind=best_rule.kind,
                        lexeme=lexeme,
                        line=line,
                        column=column,
                    )
                )

            # 更新行号与列号，兼容 LF 和 CRLF
            i = 0

            while i < len(lexeme):
                char = lexeme[i]

                if char == "\r":
                    if (
                        i + 1 < len(lexeme)
                        and lexeme[i + 1] == "\n"
                    ):
                        i += 1

                    line += 1
                    column = 1

                elif char == "\n":
                    line += 1
                    column = 1

                else:
                    column += 1

                i += 1

            position += best_length

        # 按公共接口补充 EOF
        tokens.append(
            Token(
                kind="EOF",
                lexeme="",
                line=line,
                column=column,
            )
        )

        return tokens


class LexerGenerator:
    """读取正则规则并生成 DFA 扫描器。"""

    def __init__(self, rules: list[LexerRule]):
        if not rules:
            raise ValueError("Lexer rules cannot be empty")

        self.rules = rules

    @classmethod
    def from_json(
        cls,
        path: str | Path = DEFAULT_RULES,
    ) -> "LexerGenerator":
        """从 JSON 文件读取词法规则。"""

        data = json.loads(
            Path(path).read_text(encoding="utf-8")
        )

        if not isinstance(data, list):
            raise ValueError("Expected a list of lexer rules")

        rules = []

        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Invalid lexer rule")

            kind = item.get("kind")
            pattern = item.get("pattern")
            skip = item.get("skip", False)

            if (
                not isinstance(kind, str)
                or not kind
                or kind == "EOF"
            ):
                raise ValueError("Invalid token kind")

            if (
                not isinstance(pattern, str)
                or not pattern
            ):
                raise ValueError("Invalid token pattern")

            if not isinstance(skip, bool):
                raise ValueError("Invalid skip value")

            rules.append(
                LexerRule(kind, pattern, skip)
            )

        return cls(rules)

    def build(self) -> Scanner:
        """正则表达式 -> 最小化 DFA -> Scanner。"""

        compiled = []

        for rule in self.rules:
            dfa = regex_to_min_dfa(rule.pattern)

            # 不允许规则匹配空字符串
            # 否则扫描器可能无法向前移动
            if dfa.start in dfa.accept_states:
                raise ValueError(
                    f"Rule {rule.kind} matches empty string"
                )

            compiled.append(
                (rule, dfa, _live_states(dfa))
            )

        return Scanner(compiled)