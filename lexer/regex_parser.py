
from dataclasses import dataclass


@dataclass(frozen=True)
class RegexToken:
    kind: str
    value: str | frozenset[str] | None = None


def parse_char_class(
    pattern: str,
    start: int
) -> tuple[frozenset[str], int]:
    """
    解析从 '[' 开始的字符集合。

    示例：
        [a-c]   -> {'a', 'b', 'c'}
        [0-9]   -> {'0', ..., '9'}
        [a-zA-Z_] -> 大小写字母和下划线

    返回：
        (字符集合, 右括号后一个位置)
    """

    chars: set[str] = set()
    i = start + 1

    if i >= len(pattern) or pattern[i] == "]":
        raise ValueError("Empty or incomplete character class")

    # 第一阶段不支持否定字符集合，如 [^0-9]
    if pattern[i] == "^":
        raise ValueError("Negated character classes are not supported")

    def read_char(pos: int) -> tuple[str, int]:
        """读取字符集合中的一个字符，支持反斜杠转义。"""

        if pos >= len(pattern) or pattern[pos] == "]":
            raise ValueError("Invalid character class")

        if pattern[pos] == "\\":
            if pos + 1 >= len(pattern):
                raise ValueError("Incomplete escape sequence")
            return pattern[pos + 1], pos + 2

        return pattern[pos], pos + 1

    while i < len(pattern) and pattern[i] != "]":
        first, i = read_char(i)

        # 检查是否存在字符范围，例如 a-z
        if (
            i + 1 < len(pattern)
            and pattern[i] == "-"
            and pattern[i + 1] != "]"
        ):
            last, i = read_char(i + 1)

            if ord(first) > ord(last):
                raise ValueError(
                    f"Invalid character range: {first}-{last}"
                )

            # 将范围展开为独立字符
            for code in range(ord(first), ord(last) + 1):
                chars.add(chr(code))

        else:
            chars.add(first)

    if i >= len(pattern):
        raise ValueError("Unclosed character class")

    return frozenset(chars), i + 1


def tokenize_regex(pattern: str) -> list[RegexToken]:
    """
    将正则表达式转换为 RegexToken 序列。

    支持：
        普通字符
        | 选择
        * Kleene 闭包
        () 分组
        \\ 转义
        [] 字符集合
    """

    operators = {
        "|": "OR",
        "*": "STAR",
        "+": "PLUS",
        "(": "LPAREN",
        ")": "RPAREN",
    }

    tokens: list[RegexToken] = []
    i = 0

    while i < len(pattern):
        ch = pattern[i]

        # 处理转义字符
        if ch == "\\":
            if i + 1 >= len(pattern):
                raise ValueError("Incomplete escape sequence")

            tokens.append(
                RegexToken("LITERAL", pattern[i + 1])
            )
            i += 2
            continue

        # 处理字符集合，例如 [a-zA-Z_]
        if ch == "[":
            char_set, next_pos = parse_char_class(pattern, i)

            tokens.append(
                RegexToken("CHAR_CLASS", char_set)
            )

            i = next_pos
            continue

        # 处理正则运算符
        if ch in operators:
            tokens.append(RegexToken(operators[ch]))

        # 普通字符
        else:
            tokens.append(RegexToken("LITERAL", ch))

        i += 1

    return tokens


def regex_to_postfix(pattern: str) -> list[RegexToken]:
    """
    将中缀正则表达式转换为后缀表达式。

    例如：
        a(b|c)* -> a b c | * CONCAT
        ab      -> a b CONCAT
        a|b     -> a b OR

    使用运算符栈处理优先级和括号。
    """

    # 第一步：分词
    tokens = tokenize_regex(pattern)

    # 第二步：插入显式连接运算符
    tokens = insert_concat(tokens)

    if not tokens:
        raise ValueError("Empty regular expression")

    # 运算符优先级
    precedence = {
        "OR": 1,
        "CONCAT": 2,
    }

    output: list[RegexToken] = []
    operator_stack: list[RegexToken] = []

    # True 表示当前位置需要一个操作数
    expecting_operand = True

    for token in tokens:
        kind = token.kind

        # 1. 普通字符直接加入输出
        if kind in {"LITERAL", "CHAR_CLASS"}:
            if not expecting_operand:
                raise ValueError("Missing operator")

            output.append(token)
            expecting_operand = False

        # 2. 左括号入栈
        elif kind == "LPAREN":
            if not expecting_operand:
                raise ValueError("Missing operator before '('")

            operator_stack.append(token)
            expecting_operand = True

        # 3. 右括号：弹出直到左括号
        elif kind == "RPAREN":
            if expecting_operand:
                raise ValueError("Invalid expression before ')'")

            while (
                operator_stack
                and operator_stack[-1].kind != "LPAREN"
            ):
                output.append(operator_stack.pop())

            if not operator_stack:
                raise ValueError("Mismatched parentheses")

            operator_stack.pop()
            expecting_operand = False

        # 4. 闭包运算符直接加入后缀输出
        elif kind in {"STAR", "PLUS"}:
            if expecting_operand:
                raise ValueError(
                    f"{kind} requires an operand"
                )

            output.append(token)
            expecting_operand = False

        # 5. 二元运算符：按照优先级出栈
        elif kind in precedence:
            if expecting_operand:
                raise ValueError("Operator requires a left operand")

            while (
                operator_stack
                and operator_stack[-1].kind in precedence
                and precedence[operator_stack[-1].kind]
                    >= precedence[kind]
            ):
                output.append(operator_stack.pop())

            operator_stack.append(token)
            expecting_operand = True

        else:
            raise ValueError(f"Unsupported token: {kind}")

    if expecting_operand:
        raise ValueError("Incomplete regular expression")

    # 6. 弹出栈中剩余运算符
    while operator_stack:
        token = operator_stack.pop()

        if token.kind == "LPAREN":
            raise ValueError("Mismatched parentheses")

        output.append(token)

    return output


def insert_concat(tokens: list[RegexToken]) -> list[RegexToken]:
    """
    在正则表达式中自动插入显式连接运算符 CONCAT。

    例如：
        ab       -> a·b
        a(b|c)*  -> a·(b|c)*
        a*b      -> a*·b

    返回插入 CONCAT 后的 Token 序列。
    """
    result = []

    # 可以作为连接运算左侧的 Token 类型
    end_types = {
        "LITERAL",
        "CHAR_CLASS",
        "RPAREN",
        "STAR",
        "PLUS",
    }

    # 可以作为连接运算右侧的 Token 类型
    start_types = {
        "LITERAL",
        "CHAR_CLASS",
        "LPAREN",
    }

    for i, current in enumerate(tokens):

        # 从第二个 Token 开始检查相邻关系
        if i > 0:
            previous = tokens[i - 1]

            # 前一个 Token 能结束表达式，
            # 当前 Token 能开始表达式，则需要连接
            if previous.kind in end_types and current.kind in start_types:
                result.append(RegexToken("CONCAT"))

        # 添加当前 Token
        result.append(current)

    return result