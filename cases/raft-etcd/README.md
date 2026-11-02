# 案1 raft-etcd — W2 转录案卷 README

- 波次/角色：field-trial W2（转录工程师）。本目录只转录与声明主张：未运行 wuxing-gua 任何命令、未计算真值（W2 纪律①②）。
- 上游：`dossier/selection.json` case-01-raft-etcd（W1 选案与对称主张）。

## 转录对象

etcd-io/raft（go.etcd.io/raft）单节点**角色状态机**（Follower / Candidate / Leader / PreCandidate）。

来源钉定（一手公开代码，逐边引用行号）：

| 来源 | 版本 | 获取方式（本会话实跑） |
|---|---|---|
| raft.go | main @ `c51f010c851edd0dada5af41bafbf68e54617767`（提交日期 2026-10-23） | `git clone --depth 1 https://github.com/etcd-io/raft.git`（raw.githubusercontent.com 在本会话被网络重置不可达，改走 git 协议；本地留档 `_scratch/sources/raft/repo/`，含 .git HEAD） |
| raftpb/raftpb.go | 同上 | 同上 |
| Raft 论文 | ATC'14（raft.github.io/raft.pdf） | W1 快照 `dossier/sources/raft-paper.pdf`；仅作主张来源，不进转录 |

W1 主张"raft.go:51-54 实证 4 态"经本会话独立复核成立：`raft.go:49-56` StateType 恰四值（StateFollower=51 行、StateCandidate=52、StateLeader=53、StatePreCandidate=54）。W1 引用的 becomeFollower:896 在现 HEAD 已漂移为 891，本卷一律以 `c51f010c851` HEAD 行号为准。

## 模型规模（落盘实值，见 model.json）

- 状态：4 真实态 + 0 填充态（4 = 2^2，n_bits=2，无填充）。
- 事件：14（raftpb.MessageType 24 个中收 14、裁剪 10；裁剪清单与理由在 meta.trimmed_events）。
- 事件表：4×14 = 56 格**全部逐格引证**（meta.transcription_notes.cell_citations），跨态迁移边 12 条。
- 被告群：3 个（主张群 1 + 对照群 1 + 语义分派对照群 1），全部声明 `semantics`、带 `meta.claim`。

## 转录口径（完整版在 model.json meta.transcription_rules）

1. **K1 preVote=true**：StatePreCandidate 仅在该配置可达（campaign:1029-1035）；W1 风险项"论文三态图中没有 PreCandidate"由此解决——以代码四态为准。
2. **K2 checkQuorum=true**：Leader 的 MsgCheckQuorum 失 quorum 降级边（raft.go:1281-1284）。
3. **K3 投票响应取 VoteWon 分支**（raft.go:1688-1698）；VoteLost 降级分支（1699-1702）为条件分支，确定性单值表不收。
4. **K4 只转录 current-term 行为**；高 term 交叉降级规则（raft.go:1104-1130）不收。
5. **K5 裁剪**：MsgUnreachable/SnapStatus/TransferLeader/ReadIndex/ReadIndexResp/MsgStorage*(4)/MsgForgetLeader 共 10 个（无角色迁移或存储内部消息）。
6. **K6 惩罚自环**：无 case 臂/显式 ignore/ErrProposalDropped 的 (态,事件) → 自环 r=-1.0（沿用工具仓 examples/eventfsm 的"非法自环"惯例，属转录约定）；显式处理的自环 r=0.0。
7. **K7 奖励**：仅进入 Leader（becomeLeader:933）+1.0；协议无奖励维度，此为声明性约定。

## 未收录清单（宁缺毋滥，全文在 meta.transcription_notes.not_collected）

- 高 term 交叉降级规则（1104-1130）：term 条件分支无法在确定性 (态,事件) 表中单值化。
- Candidate/PreCandidate 的 VoteLost 降级分支（1698-1702）：quorum 条件分支。
- Leader 高 term 收 MsgApp/MsgHeartbeat/MsgSnap 降级（1119-1127）：同 K4。
- poll() 计票中间态（1075-1088）：非角色迁移。
- CampaignType 差异（campaignTransfer 等）：参数非消息类型。
- 论文三态图口径：论文 Figure 2 无 PreCandidate，以代码为准（已声明）。

## 被告群（groups/）

| 文件 | 置换 | semantics | 主张（meta.claim 摘要） |
|---|---|---|---|
| g1_claim_cand_precand_swap_fixed.json | swap Candidate↔PreCandidate | fixed | W1 主张（副本等价可互换）的状态级类比：两个选举等待角色等价；完成事件不同（MsgVoteResp vs MsgPreVoteResp），是否构成协议错误由工具/基准裁决 |
| g2_control_follower_leader_swap_fixed.json | swap Follower↔Leader | fixed | 对照：角色互换不应为对称（与主张方向相反的判别组） |
| g3_claim_twin_cand_precand_swap_relabel.json | 同 g1 置换 | relabel | 语义分派对照：同一置换在两种读法下的读数差即工具判据分派行为 |

## 自证记录（本会话实跑）

- `python -X utf8 -I make_raft_etcd.py` → 生成 model.json(15,491B) + 3 个群文件。
- `python -X utf8 -I make_raft_etcd.py --check` → 4 个文件全部 OK，exit 0（逐字节自证）。
- 自写结构校验（非工具）：trans 4×14、56 格全引证、概率和=1、群置换合法、跨态边=12。

--check 覆盖 model.json 与 groups/*.json 的字节一致性；本 README 为手工文档，不在字节自证范围内（声明）。
