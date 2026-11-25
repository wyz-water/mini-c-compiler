
from collections import deque
from dataclasses import dataclass

from lexer.nfa import NFA, regex_to_nfa


@dataclass
class DFA:
    """确定有限自动机。"""

    start: int
    accept_states: set[int]
    transitions: dict[int, dict[str, int]]

    def accepts(self, text: str) -> bool:
        """判断 DFA 是否接受完整输入字符串。"""

        current = self.start

        for char in text:
            next_state = self.transitions[current].get(char)

            if next_state is None:
                return False

            current = next_state

        return current in self.accept_states


def nfa_to_dfa(nfa: NFA) -> DFA:
    """通过子集构造法将 ε-NFA 转换为 DFA。"""

    # 1. 收集 NFA 中所有非 epsilon 输入字符
    alphabet = sorted({
        symbol
        for edges in nfa.transitions.values()
        for symbol in edges
        if symbol is not None
    })

    # 2. DFA 初始状态 = NFA 初态的 epsilon 闭包
    start_subset = frozenset(
        nfa.epsilon_closure({nfa.start})
    )

    # 每个 NFA 状态集合对应一个 DFA 状态编号
    subset_to_id: dict[frozenset[int], int] = {
        start_subset: 0
    }

    # 使用队列逐个处理尚未展开的 DFA 状态
    queue = deque([start_subset])

    transitions: dict[int, dict[str, int]] = {}
    accept_states: set[int] = set()

    # 3. 不断扩展新的 DFA 状态
    while queue:
        subset = queue.popleft()
        current_id = subset_to_id[subset]

        transitions[current_id] = {}

        # 子集包含 NFA 接受态，则它是 DFA 接受态
        if nfa.accept in subset:
            accept_states.add(current_id)

        # 对每个输入字符计算转移
        for symbol in alphabet:
            moved: set[int] = set()

            # move(subset, symbol)
            for state in subset:
                moved.update(
                    nfa.transitions[state].get(symbol, set())
                )

            # epsilon-closure(move(...))
            next_subset = frozenset(
                nfa.epsilon_closure(moved)
            )

            # 如果是首次发现的状态集合，分配新编号
            if next_subset not in subset_to_id:
                new_id = len(subset_to_id)
                subset_to_id[next_subset] = new_id
                queue.append(next_subset)

            # 记录确定的状态转移
            transitions[current_id][symbol] = (
                subset_to_id[next_subset]
            )

    return DFA(
        start=0,
        accept_states=accept_states,
        transitions=transitions,
    )


def regex_to_dfa(pattern: str) -> DFA:
    """将正则表达式转换成 DFA。"""

    nfa = regex_to_nfa(pattern)
    return nfa_to_dfa(nfa)