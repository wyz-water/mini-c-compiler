
from dataclasses import dataclass


@dataclass(frozen=True)
class RegexToken:
    kind: str
    value: str | None = None



def tokenize_regex(pattern: str) -> list[RegexToken]:
    """
    将正则表达式拆分为 RegexToken 序列。

    当前支持：
        |  选择运算符
        *  Kleene 闭包
        () 分组
        普通字符
        \\  转义字符

    例如：
        输入：a(b|c)*
        输出：LITERAL(a), LPAREN, LITERAL(b),
             OR, LITERAL(c), RPAREN, STAR
    """

    # 正则运算符与 Token 类型的对应关系
    operators = {
        "|": "OR",
        "*": "STAR",
        "(": "LPAREN",
        ")": "RPAREN",
    }

    tokens: list[RegexToken] = []
    i = 0

    # 从左到右扫描正则表达式
    while i < len(pattern):
        ch = pattern[i]

        # 处理转义字符，例如 \* 表示普通字符 *
        if ch == "\\":
            if i + 1 >= len(pattern):
                raise ValueError(
                    "Invalid regex: incomplete escape sequence"
                )

            tokens.append(
                RegexToken("LITERAL", pattern[i + 1])
            )
            i += 2
            continue

        # 判断是否为正则运算符
        if ch in operators:
            tokens.append(RegexToken(operators[ch]))

        # 其他字符视为普通字符
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
        if kind == "LITERAL":
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
        elif kind == "STAR":
            if expecting_operand:
                raise ValueError("STAR requires an operand")

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
    end_types = {"LITERAL", "RPAREN", "STAR"}

    # 可以作为连接运算右侧的 Token 类型
    start_types = {"LITERAL", "LPAREN"}

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