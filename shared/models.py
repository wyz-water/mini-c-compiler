"""供四个模块共同使用的最小数据契约；如需改动请先讨论。"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Token:
    kind: str          # 如 INT / IDENT / NUMBER / ASSIGN / EOF
    lexeme: str        # 源代码中的原始文本，如 "a"、"123"
    line: int          # 从 1 开始计数
    column: int        # 从 1 开始计数


@dataclass(slots=True)
class ASTNode:
    kind: str          # 如 Assign / BinaryOp / Identifier / Number
    value: str | int | None = None
    children: list["ASTNode"] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Quadruple:
    op: str
    arg1: str | int | None = None
    arg2: str | int | None = None
    result: str | None = None
