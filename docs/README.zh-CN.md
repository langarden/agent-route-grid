# agent-route-grid（中文）

> **多 Agent 团队的审计路由层** —— 基于风险区的路由策略、工作区隔离、哈希链决策留痕。
> **谁执行、谁复核、谁拍板——可见、可验证。**

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Tests](https://img.shields.io/badge/tests-35%20passed-green)
![Deps](https://img.shields.io/badge/runtime%20deps-0-green)
![Status](https://img.shields.io/badge/status-research%20prototype-orange)

> 研究报告级 / AI 辅助开发 · MIT 许可 · 维护者：`agent-route-grid maintainers`

---

多 Agent 团队长大就会乱：没人知道该谁拍板、有没有人复核、到底发生了什么。
本库把路由变成**可见的策略**，把每次决策变成**可验证的记录**。

## 路由分区（Zone）

| 区域 | 场景 | 策略 |
|:--|:--|:--|
| `green` | 低风险例行 | 协调者直接自执行 |
| `yellow` | 中风险 | 委派一个 worker，然后**独立复核** |
| `red` | 高风险/危急 | **全员复核**（面板），聚合；任一故障保持 fail-closed |
| `purple` | 训练/带教 | 当成练级任务，带裁判复核 |

映射规则确定性、可注入：传你自己的 `ZonePolicy` 即可。

## 产品家族（Verifiable-agent 家族）

| 仓库 | 角色 |
|:--|:--|
| agent-call-audit | Agent 调用**审计引擎** |
| agent-memory-ledger | 可验证**记忆层** |
| agent-audit-gateway | 引擎的 HTTP **网关** |
| **agent-route-grid** | 多 Agent **路由编排**（本仓库） |

## 安装与快速开始

```bash
pip install agent-route-grid
# 或源码安装
pip install -e .
```

```python
from routegrid import AgentSpec, Coordinator, Task

team = [
    AgentSpec(name="worker", capabilities=("lookup",), scope="ws-w"),
    AgentSpec(name="reviewer", capabilities=("lookup",), scope="ws-r",
              review_capable=True),
]
co = Coordinator(team, timeout_s=2.0)
res = co.route(
    Task(name="medium decision", risk="medium", requires=("lookup",)),
    worker_fns={"worker": lambda t: {"summary": "done"}},
    reviewer_fns={"reviewer": lambda t, ctx: {"verdict": "approve"}},
)
print(res.zone, res.strategy, res.fail_closed)
```

worker 是**注入的 callable**——协调者不执行业务逻辑，只做路由、超时、收集、留痕。

## 5 条失败封闭不变量

1. worker 故障 → 调用与结果都标 fail-closed
2. 复核缺失/故障 → 结果保持 fail-closed
3. 面板有异议 → 任一复核成员非 ok，保持拒绝语义
4. 工作区隔离 → 写别人的 workspace 一律拒绝
5. 留痕防篡改 → `verify()` 能发现链上任何修改

## 路线图（征集中）

- 异步编排（面板 fan-out 并发）
- 人类介入复核的插件钩子
- 留痕导出（MCP / OTel）

## 安全与边界

- 参考实现，生产使用前请审阅代码
- 漏洞请私信 `2307788504@qq.com`（勿开公开 issue）

## 相关

- 家族体系：agent-call-audit（引擎）· agent-memory-ledger（记忆）· agent-audit-gateway（网关）