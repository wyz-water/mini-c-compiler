# mini-C Compiler (课程期末项目)

Python 3.11 开发的 mini-C 编译器课程项目。

## 计划功能

- 读取词法规则，构造 NFA / DFA / 最小化 DFA，扫描源程序得到 Token
- 读取上下文无关文法，生成 SLR(1) 分析表并构造 AST
- 从 AST 生成三地址代码
- 展示 AST、错误报告、测试结果

**当前状态：仅完成项目初始化与公共数据结构，尚未实现核心算法。**

## 环境

建议统一使用 Python 3.11。

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python main.py
```

Graphviz 的 Python 包不等于系统 `dot` 可执行程序。
后续需要输出 PNG 时，还需安装 Graphviz 软件并配置 PATH。

## 协作约定

- `main`：已审核、可集成的代码
- `feature/lexer`：词法分析器生成器
- `feature/parser`：语法分析器生成器
- `feature/ir`：AST 与三地址代码
- `feature/integration`：集成、可视化和测试
- 功能开发从 `main` 创建分支，通过 PR 合并
- PR 链接对应 Issue，至少一位其他成员评审
- 先读 `docs/interfaces.md`，修改共享接口需全组讨论

## 目录说明

| 路径 | 作用 |
|---|---|
| `shared/` | 公共 Token / AST / Quadruple 类型 |
| `lexer/` | 词法分析器生成与扫描 |
| `parser/` | 文法读取、SLR(1)、AST 构造 |
| `compiler/` | AST 到三地址代码翻译 |
| `visualizer/` | AST 图像导出 |
| `rules/` | 词法与语法规则（团队自行录入、校验） |
| `tests/` | 单元测试及集成测试 |
| `examples/` | mini-C 测试程序 |
| `output/` | 自动生成的结果（默认不纳入版本库） |
| `docs/` | 接口及设计决策 |

## 学术规范

核心编译算法须由团队理解并自主实现。README 与公共接口模板不替代算法实现。
