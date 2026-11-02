# 案2 hadoop-mr-task — W2 转录案卷 README

- 波次/角色：field-trial W2。未运行 wuxing-gua、未算真值、逐格一手引证（W2 纪律①②③）。
- 上游：`dossier/selection.json` case-02-hadoop-mr-task（W1 选案与对称主张）。

## 转录对象

apache/hadoop trunk MRv2 **Task 级声明式状态机**（`TaskStateInternal` 7 态 × `TaskEventType` 9 事件）。

来源钉定（一手公开代码，逐行引用）：

| 来源 | 版本 | 获取方式（本会话实跑） |
|---|---|---|
| TaskStateInternal.java | trunk @ `e66f40daf3cc4ebbb5164cec1ce54b71eddec8a4` | `git ls-remote https://github.com/apache/hadoop.git refs/heads/trunk` 记录 SHA；文件经 jsdelivr CDN 抓取（raw.githubusercontent 本会话不可达），留档 `_scratch/sources/hadoop/` |
| TaskImpl.java（stateMachineFactory 24 个 addTransition 行） | 同上 | 同上 |
| TaskEventType.java（9 事件） | 同上 | 同上 |
| yarn StateMachineFactory.java（未注册事件行为） | 同上 | 同上 |
| MapReduce 论文（OSDI'04） | W1 快照 | 仅作主张来源，不进转录 |

本会话独立复核与 W1 dossier 一致：TaskStateInternal.java:22 恰 7 态（NEW, SCHEDULED, RUNNING, SUCCEEDED, FAILED, KILL_WAIT, KILLED；**trunk 无 COMMIT_PENDING**——2.x 旧口径未混入）；TaskImpl.java 恰 24 个 addTransition 行（行号清单在 model.json meta）。

## 模型规模（落盘实值，见 model.json）

- 状态：7 真实态 + 1 填充哑态 filler_7（8 = 2^3，n_bits=3）。填充态边不引用真实事件语义（红线）。
- 事件：9（TaskEventType.java 全集，无裁剪）。
- 事件表：8×9 = 72 格**全部逐格引证**；多目标 EnumSet 行 8 个展开后共 83 个结果分支（72+11），跨态结果分支 18。
- 被告群：3 个（主张群 1 + 对照群 2），全部声明 `semantics: fixed`、带 `meta.claim`。本案只有 1 个填充态，无填充对换正控组（如实声明）。

## 转录口径（完整版在 meta.transcription_rules）

1. **H1 多目标 EnumSet 行 → 等概率占位**：8 行（167 T_RECOVER 4 目标；182/201/209/213/217/234 双目标；231 三目标）。分支条件在各 Transition 内部类（重试上限/追溯失败判别等），不在 (态,事件) 维度，故等概率占位并声明——这是本案最大的口径决策，W1 风险项"T_RECOVER 多目标边须声明"由此落点。
2. **H2 未注册 (态,事件) → -1.0 惩罚自环**：YARN StateMachineFactory.java:305 对未注册组合抛 InvalidStateTransitionException（本会话拉取该文件核验行号）。
3. **H3 显式注册的 Ignore-able 行 → 0.0 自环**（TaskImpl.java:222-228, 241-246 源码注释"Ignore-able transitions"），与 H2 的未注册惩罚区分。
4. **H4 奖励约定**：仅"从其他态进入 SUCCEEDED"分支 +1.0（RUNNING|T_ATTEMPT_SUCCEEDED:195-197；NEW|T_RECOVER 的 SUCCEEDED 分支）；声明性约定，非框架语义。
5. **H5 以 trunk 为准**：不混录 2.x COMMIT_PENDING、不混录 Hadoop 1.x TaskStatus.State（W1 风险项）。

## 未收录清单（meta.transcription_notes.not_collected）

- 各 Transition 类内部运行时条件（maxAttempts、map/reduce 追溯判别等）：等概率占位已声明，条件本身不收。
- COMMIT_PENDING（trunk 已无）：按 trunk 原文。
- TaskAttempt 级状态机：W1 dossier 限定 Task 级。
- Hadoop 1.x 口径：W1 dossier 风险项。

## 被告群（groups/）

| 文件 | 置换 | 主张（meta.claim 摘要） |
|---|---|---|
| g1_claim_failed_killed_swap_fixed.json | swap FAILED↔KILLED | W1 主张（重跑等价）的终态级类比：两种终局等价可互换 |
| g2_control_new_scheduled_swap_fixed.json | swap NEW↔SCHEDULED | 对照：流水线相邻阶段等价主张 |
| g3_control_running_killwait_swap_fixed.json | swap RUNNING↔KILL_WAIT | 对照：执行与等待死亡等价主张（W1"KILL_WAIT 自环多防漏标"已逐格引证） |

## 自证记录（本会话实跑）

- `python -X utf8 -I make_hadoop_mr_task.py` → 生成 model.json(21,304B) + 3 个群文件。
- `python -X utf8 -I make_hadoop_mr_task.py --check` → 4 文件全 OK，exit 0（逐字节自证）。
- 自写结构校验（非工具）：trans 8×9、72 格全引证、概率和=1（容差 1e-6 内）、群置换合法、结果分支 83、跨态分支 18。

--check 覆盖 model.json 与 groups/*.json；README 为手工文档，不在字节自证范围（声明）。
