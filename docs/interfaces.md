# 四人共同遵守的最小接口约定（草案）

修改本文件或 `shared/models.py` 前，请先在 Issue / PR 里讨论，并确保其他成员同步更新。

## A → B：Token

`Token(kind: str, lexeme: str, line: int, column: int)`

- `line`、`column` 均从 1 开始
- `lexeme` 始终是字符串，数字 `123` 的 lexeme 仍为 `"123"`
- 词法扫描器在末尾补充一个 `kind="EOF"` 的 Token
- Token 类型使用大写英文名称，不混用符号名与字面量

建议 Token 名称：
`INT IF ELSE WHILE READ WRITE IDENT NUMBER`
`PLUS MINUS MUL DIV LT GT LE GE EQ NE ASSIGN`
`SEMI COMMA LPAREN RPAREN LBRACE RBRACE EOF`

注意：这是团队内部约定，而不是教师规定的 Token 命名方式。
原项目附录允许的语言规则应以项目 PDF 为准。

约定的调用形式（待开发）：

```python
tokens = scanner.scan(source_code)  # -> list[Token]
```

## B → C：AST

使用 `ASTNode(kind, value=None, children=[])`。节点类型与孩子位置：

| kind | value | children |
|---|---|---|
| `Program` | 无 | 按顺序排列的语句 |
| `Block` | 无 | 按顺序排列的语句 |
| `VarDecl` | 变量名 | 0 或 1 个初始化表达式 |
| `Assign` | 被赋值变量名 | 1 个右侧表达式 |
| `If` | 无 | 条件、then 语句、可选 else 语句 |
| `While` | 无 | 条件、循环体 |
| `Read` | 变量名 | 无 |
| `Write` | 无 | 1 个表达式 |
| `BinaryOp` | 运算符（如 `+`、`>=`） | 左、右两个操作数 |
| `Identifier` | 变量名 | 无 |
| `Number` | 整数 | 无 |

注意：这是一份建议的精简 AST 约定。B/C 应在第一次开发会确认，并共同处理 `if-else`、空语句序列等情况。

约定的调用形式（待开发）：

```python
ast = parser.parse(tokens)          # -> ASTNode
```

## C → D：三地址代码

使用 `Quadruple(op, arg1, arg2, result)`。
例如 `t1 = 3 * 4` 可表示为 `Quadruple("*", 3, 4, "t1")`。

约定的调用形式（待开发）：

```python
quadruples = ir_generator.generate(ast)  # -> list[Quadruple]
```

跳转、标签、读写四元式的 op 命名，需在 C 与 D 之间另行明确，
不要在开发中各自发明不一致的格式。

## D：可视化、输出与测试

- AST 可先消费模拟的 `ASTNode` 对象，不必等待 B 的分析器完成
- `output/` 中的自动生成文件暂不纳入 Git，答辩前按要求保存展示结果
- 使用 `python -m pytest` 运行自动化测试
- AST 图片可使用 Graphviz 绘制，构造 AST 的算法仍需团队自主编写

## 错误报告

A 与 B 最低要求报告 `phase`, `line`, `column`, `message`。
具体异常类可在后续 PR 中统一定义。
