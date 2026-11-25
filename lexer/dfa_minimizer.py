
from collections import deque

from lexer.dfa import DFA


def minimize_dfa(dfa: DFA) -> DFA:
    """使用状态等价划分法最小化 DFA。"""

    # 1. 只保留从初始状态能够到达的状态
    reachable: set[int] = set()
    pending = [dfa.start]

    while pending:
        state = pending.pop()

        if state in reachable:
            continue

        reachable.add(state)
        pending.extend(
            dfa.transitions.get(state, {}).values()
        )

    # 收集输入字母表
    alphabet = sorted({
        symbol
        for state in reachable
        for symbol in dfa.transitions.get(state, {})
    })

    # 复制转移表，不修改原始 DFA
    edges = {
        state: dict(dfa.transitions.get(state, {}))
        for state in reachable
    }

    # 2. 补全缺失转移，统一指向死状态
    if any(
        symbol not in edges[state]
        for state in reachable
        for symbol in alphabet
    ):
        dead = max(reachable) + 1

        edges[dead] = {
            symbol: dead for symbol in alphabet
        }

        for state in reachable:
            for symbol in alphabet:
                edges[state].setdefault(symbol, dead)

        reachable.add(dead)

    # 3. 初始划分：接受态和非接受态
    accepting = reachable & dfa.accept_states
    rejecting = reachable - accepting

    groups = [
        group
        for group in (accepting, rejecting)
        if group
    ]

    # 4. 反复划分，直到所有组稳定
    while True:
        group_of = {
            state: index
            for index, group in enumerate(groups)
            for state in group
        }

        refined = []

        for group in groups:
            buckets: dict[tuple[int, ...], set[int]] = {}

            for state in sorted(group):
                # 状态在每个字符上转移到哪个组
                signature = tuple(
                    group_of[edges[state][symbol]]
                    for symbol in alphabet
                )

                buckets.setdefault(
                    signature, set()
                ).add(state)

            refined.extend(buckets.values())

        # 没有新分组产生，说明划分稳定
        if len(refined) == len(groups):
            break

        groups = refined

    # 5. 为每个等价状态组建立新的 DFA 状态
    group_of = {
        state: index
        for index, group in enumerate(groups)
        for state in group
    }

    start_group = group_of[dfa.start]

    # 从新的初态开始重新编号
    new_id = {start_group: 0}
    pending = deque([start_group])

    new_edges: dict[int, dict[str, int]] = {}
    new_accepts: set[int] = set()

    while pending:
        group_index = pending.popleft()
        state_id = new_id[group_index]

        group = groups[group_index]
        representative = min(group)

        # 该组包含原接受态，则新状态也是接受态
        if group & accepting:
            new_accepts.add(state_id)

        new_edges[state_id] = {}

        for symbol in alphabet:
            target_group = group_of[
                edges[representative][symbol]
            ]

            if target_group not in new_id:
                new_id[target_group] = len(new_id)
                pending.append(target_group)

            new_edges[state_id][symbol] = (
                new_id[target_group]
            )

    return DFA(
        start=0,
        accept_states=new_accepts,
        transitions=new_edges,
    )


def regex_to_min_dfa(pattern: str) -> DFA:
    """正则表达式 -> NFA -> DFA -> 最小化 DFA。"""

    from lexer.dfa import regex_to_dfa

    dfa = regex_to_dfa(pattern)
    return minimize_dfa(dfa)