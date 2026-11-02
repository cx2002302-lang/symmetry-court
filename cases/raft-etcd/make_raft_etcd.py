#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_raft_etcd.py — W2 盲测案卷生成器（案1 raft-etcd）

生成 model.json 与 groups/*.json；`--check` 重新生成并逐字节比对自证。
本脚本只写转录文件：
  * 不运行 wuxing-gua 任何命令（盲测纪律 W2-①）；
  * 不计算任何"真值"（W2-②）；
  * 每个 (状态,事件) 格都给一手公开来源行号（W2-③）。

转录对象：etcd-io/raft（go.etcd.io/raft）单节点角色状态机。
来源钉定：github.com/etcd-io/raft main @ c51f010c851edd0dada5af41bafbf68e54617767
（克隆日期 2026-10-31，HEAD 提交日期 2026-10-23，浅克隆本机留档
 _scratch/sources/raft/repo/）。
"""
import json
import os
import sys

CASE_DIR = os.path.dirname(os.path.abspath(__file__))

N_BITS = 2
STATES = ["Follower", "Candidate", "Leader", "PreCandidate"]
EVENTS = [
    "MsgHup", "MsgBeat", "MsgProp", "MsgApp", "MsgAppResp", "MsgVote",
    "MsgVoteResp", "MsgSnap", "MsgHeartbeat", "MsgHeartbeatResp",
    "MsgCheckQuorum", "MsgTimeoutNow", "MsgPreVote", "MsgPreVoteResp",
]
GOALS = []  # raft 角色循环，无吸收态（Leader 可被更高 term 拉回 Follower）

F, C, L, P = 0, 1, 2, 3

# 转录口径（meta.transcription_rules 展开）：
#   K1  preVote=true：StatePreCandidate 仅在该配置下可达（campaign:1029-1035）。
#   K2  checkQuorum=true：Leader 的 MsgCheckQuorum 失 quorum 降级边才生效（1281-1284）。
#   K3  投票响应取 quorum.VoteWon 分支（1688-1698）；VoteLost 降级分支（1699-1702）
#       为条件分支，确定性单值表不收，记入 not_collected。
#   K4  只转录 current-term 行为；高 term 交叉降级规则（Step 1104-1130）不收。
#   K5  裁剪 10 个消息类型（清单见 TRIMMED）。
#   K6  无 case 臂/显式 ignore 的 (态,事件) → 自环 r=-1.0（"协议不行动"声明性惩罚，
#       参照本仓 examples/eventfsm 的非法自环惯例）；显式处理的同态自环 r=0.0。
#   K7  奖励：进入 Leader（becomeLeader:933-943 的唯一入边）+1.0，其余 0.0/-1.0。

# 每格决策：KEY = "态|事件"；VAL = (目标列表, 引证)
#   目标列表元素 = ("self", r) 或 (目标态序号, r) 或 ("dist", [(p, 目标, r), ...])
SELF0 = (("self", 0.0),)
SELFN1 = (("self", -1.0),)

CITES = {}
TABLE = {}

def cell(state, event, targets, cite):
    key = "%s|%s" % (state, event)
    assert key not in TABLE, key
    TABLE[key] = targets
    CITES[key] = cite

# ---- Follower (0) ----
cell("Follower", "MsgHup", ((P, 0.0),),
     "raft.go:1190-1194 case pb.MsgHup -> hup:973-990 -> campaign:1029-1035 -> becomePreCandidate:917-924（K1: preVote=true 走 campaignPreElection）")
cell("Follower", "MsgBeat", SELFN1,
     "stepFollower raft.go:1710-1770 无 MsgBeat case，switch 落空无行动（显式 default 缺省）")
cell("Follower", "MsgProp", SELF0,
     "stepFollower raft.go:1712-1721 case pb.MsgProp：转发给 leader 或丢弃，角色不变")
cell("Follower", "MsgApp", SELF0,
     "stepFollower raft.go:1722-1725 case pb.MsgApp：handleAppendEntries，角色不变")
cell("Follower", "MsgAppResp", SELFN1,
     "stepFollower raft.go:1710-1770 无 MsgAppResp case，无行动")
cell("Follower", "MsgVote", SELF0,
     "Step raft.go:1212-1262 case pb.MsgVote,pb.MsgPreVote：current-term 投票/拒票，角色不变（K4）")
cell("Follower", "MsgVoteResp", SELFN1,
     "stepFollower raft.go:1710-1770 无 MsgVoteResp case，无行动")
cell("Follower", "MsgSnap", SELF0,
     "stepFollower raft.go:1730-1733 case pb.MsgSnap：handleSnapshot，角色不变")
cell("Follower", "MsgHeartbeat", SELF0,
     "stepFollower raft.go:1726-1729 case pb.MsgHeartbeat：handleHeartbeat，角色不变")
cell("Follower", "MsgHeartbeatResp", SELFN1,
     "stepFollower raft.go:1710-1770 无 MsgHeartbeatResp case，无行动")
cell("Follower", "MsgCheckQuorum", SELFN1,
     "stepFollower raft.go:1710-1770 无 MsgCheckQuorum case，无行动")
cell("Follower", "MsgTimeoutNow", ((C, 0.0),),
     "stepFollower raft.go:1750-1755 case pb.MsgTimeoutNow：hup(campaignTransfer) -> campaign:1037-1039 -> becomeCandidate:902-910（注释：leadership transfer 不用 pre-vote）")
cell("Follower", "MsgPreVote", SELF0,
     "Step raft.go:1212-1262 case pb.MsgVote,pb.MsgPreVote：current-term 投票/拒票，角色不变；高 term 也不改 term（raft.go:1112-1114）")
cell("Follower", "MsgPreVoteResp", SELFN1,
     "stepFollower raft.go:1710-1770 无 MsgPreVoteResp case，无行动")

# ---- Candidate (1) ----
cell("Candidate", "MsgHup", ((P, 0.0),),
     "Step raft.go:1190-1194 -> hup:973-990 -> campaign:1029-1035（K1: 每轮选举先回 PreCandidate）")
cell("Candidate", "MsgBeat", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgBeat case，无行动")
cell("Candidate", "MsgProp", SELFN1,
     "stepCandidate raft.go:1676-1678 case pb.MsgProp：return ErrProposalDropped（显式丢弃；K6 惩罚自环）")
cell("Candidate", "MsgApp", ((F, 0.0),),
     "stepCandidate raft.go:1679-1681 case pb.MsgApp：becomeFollower(m.Term, m.From)（注释 always m.Term == r.Term；K4 高 term 分支另记）")
cell("Candidate", "MsgAppResp", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgAppResp case，无行动")
cell("Candidate", "MsgVote", SELF0,
     "Step raft.go:1212-1262：current-term 投票/拒票不改角色；stepCandidate 无 MsgVote case（K4 高 term 分支不收）")
cell("Candidate", "MsgVoteResp", ((L, 1.0),),
     "stepCandidate raft.go:1688-1697 case myVoteRespType(=MsgVoteResp,1663-1673)：quorum.VoteWon 分支 -> becomeLeader:933-942（K3 取胜选分支）；K7 竞得 leadership +1.0")
cell("Candidate", "MsgSnap", ((F, 0.0),),
     "stepCandidate raft.go:1685-1687 case pb.MsgSnap：becomeFollower(m.Term, m.From)")
cell("Candidate", "MsgHeartbeat", ((F, 0.0),),
     "stepCandidate raft.go:1682-1684 case pb.MsgHeartbeat：becomeFollower(m.Term, m.From)")
cell("Candidate", "MsgHeartbeatResp", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgHeartbeatResp case，无行动")
cell("Candidate", "MsgCheckQuorum", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgCheckQuorum case，无行动")
cell("Candidate", "MsgTimeoutNow", SELFN1,
     "stepCandidate raft.go:1704-1707 case pb.MsgTimeoutNow：Debugf 忽略（显式 ignore；K6 惩罚自环）")
cell("Candidate", "MsgPreVote", SELF0,
     "Step raft.go:1112-1114（PreVote 永不改 term）+ 1212-1262（投票）；stepCandidate 无 MsgPreVote case")
cell("Candidate", "MsgPreVoteResp", SELFN1,
     "stepCandidate raft.go:1665-1673：MsgPreVoteResp 非 Candidate 的 myVoteRespType（stale 注释 1666-1668），switch 落空无行动")

# ---- Leader (2) ----
cell("Leader", "MsgHup", SELFN1,
     "hup raft.go:974-976：already leader，ignoring MsgHup（显式 ignore；K6 惩罚自环）")
cell("Leader", "MsgBeat", SELF0,
     "stepLeader raft.go:1278-1280 case pb.MsgBeat：bcastHeartbeat()，角色不变")
cell("Leader", "MsgProp", SELF0,
     "stepLeader raft.go:1294 起 case pb.MsgProp：appendEntry 提案，角色不变")
cell("Leader", "MsgApp", SELFN1,
     "stepLeader raft.go:1275-1662 无 MsgApp case（current-term 下 leader 收 MsgApp 无行动；K4 高 term 降级另记）")
cell("Leader", "MsgAppResp", SELF0,
     "stepLeader raft.go:1376 起 case pb.MsgAppResp：maybeCommit 推进，角色不变")
cell("Leader", "MsgVote", SELF0,
     "Step raft.go:1212-1262：current-term 投票/拒票不改角色（K4 高 term 降级不收）")
cell("Leader", "MsgVoteResp", SELFN1,
     "stepLeader raft.go:1275-1662 无 MsgVoteResp case，无行动")
cell("Leader", "MsgSnap", SELFN1,
     "stepLeader raft.go:1275-1662 无 MsgSnap case，无行动")
cell("Leader", "MsgHeartbeat", SELFN1,
     "stepLeader raft.go:1275-1662 无 MsgHeartbeat case，无行动")
cell("Leader", "MsgHeartbeatResp", SELF0,
     "stepLeader raft.go:1571 起 case pb.MsgHeartbeatResp：进度更新，角色不变")
cell("Leader", "MsgCheckQuorum", ((F, 0.0),),
     "stepLeader raft.go:1281-1293 case pb.MsgCheckQuorum：!r.trk.QuorumActive() -> becomeFollower(r.Term, None)（K2: checkQuorum=true 取触发分支）")
cell("Leader", "MsgTimeoutNow", SELFN1,
     "stepLeader raft.go:1275-1662 无 MsgTimeoutNow case，无行动")
cell("Leader", "MsgPreVote", SELF0,
     "Step raft.go:1112-1114 + 1212-1262：PreVote 不改 term、投票不改角色")
cell("Leader", "MsgPreVoteResp", SELFN1,
     "stepLeader raft.go:1275-1662 无 MsgPreVoteResp case，无行动")

# ---- PreCandidate (3) ----
cell("PreCandidate", "MsgHup", SELF0,
     "Step raft.go:1190-1194 -> hup:973-990 -> campaign:1029-1035 -> becomePreCandidate:917-924（新一轮预选举，态不变 term+1）")
cell("PreCandidate", "MsgBeat", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgBeat case，无行动")
cell("PreCandidate", "MsgProp", SELFN1,
     "stepCandidate raft.go:1676-1678：return ErrProposalDropped（K6 惩罚自环）")
cell("PreCandidate", "MsgApp", ((F, 0.0),),
     "stepCandidate raft.go:1679-1681 case pb.MsgApp：becomeFollower(m.Term, m.From)（对两候选态共用，注释 1663-1664）")
cell("PreCandidate", "MsgAppResp", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgAppResp case，无行动")
cell("PreCandidate", "MsgVote", SELF0,
     "Step raft.go:1212-1262：current-term 投票/拒票不改角色（K4 高 term 降级不收）")
cell("PreCandidate", "MsgVoteResp", SELFN1,
     "stepCandidate raft.go:1665-1673：MsgVoteResp 非 PreCandidate 的 myVoteRespType（stale），switch 落空无行动")
cell("PreCandidate", "MsgSnap", ((F, 0.0),),
     "stepCandidate raft.go:1685-1687 case pb.MsgSnap：becomeFollower(m.Term, m.From)")
cell("PreCandidate", "MsgHeartbeat", ((F, 0.0),),
     "stepCandidate raft.go:1682-1684 case pb.MsgHeartbeat：becomeFollower(m.Term, m.From)")
cell("PreCandidate", "MsgHeartbeatResp", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgHeartbeatResp case，无行动")
cell("PreCandidate", "MsgCheckQuorum", SELFN1,
     "stepCandidate raft.go:1665-1708 无 MsgCheckQuorum case，无行动")
cell("PreCandidate", "MsgTimeoutNow", SELFN1,
     "stepCandidate raft.go:1704-1707：显式忽略（K6 惩罚自环）")
cell("PreCandidate", "MsgPreVote", SELF0,
     "Step raft.go:1112-1114 + 1212-1262：PreVote 不改 term、投票不改角色")
cell("PreCandidate", "MsgPreVoteResp", ((C, 0.0),),
     "stepCandidate raft.go:1688-1695：myVoteRespType(=MsgPreVoteResp) quorum.VoteWon 分支 -> state==StatePreCandidate -> campaign(campaignElection) -> becomeCandidate:902-910（K3 胜选分支）")

TRIMMED = {
    "MsgUnreachable": "raftpb/raft.pb.go:99；stepLeader:1621-1626 仅心跳失败跟踪，无角色迁移，裁剪",
    "MsgSnapStatus": "raftpb/raft.pb.go:100；stepLeader:1603-1619 快照恢复跟踪，无角色迁移，裁剪",
    "MsgTransferLeader": "raftpb/raft.pb.go:102；stepFollower:1734-1740 仅转发给 leader（触发 MsgTimeoutNow），无直接角色迁移，裁剪",
    "MsgReadIndex": "raftpb/raft.pb.go:104；stepFollower:1756-1762 转发/stepLeader:1354-1363 线性读，无角色迁移，裁剪",
    "MsgReadIndexResp": "raftpb/raft.pb.go:105；stepFollower:1763-1768 记录读结果，无角色迁移，裁剪",
    "MsgStorageAppend": "raftpb/raft.pb.go:108；异步存储内部消息（AsyncStorageWrites），非协议角色事件，裁剪",
    "MsgStorageAppendResp": "raftpb/raft.pb.go:109；同上，裁剪",
    "MsgStorageApply": "raftpb/raft.pb.go:110；同上，裁剪",
    "MsgStorageApplyResp": "raftpb/raft.pb.go:111；同上，裁剪",
    "MsgForgetLeader": "raftpb/raft.pb.go:112；stepFollower:1741-1749 仅清 lead 字段不改角色态，裁剪",
}

NOT_COLLECTED = [
    {"item": "高 term 交叉降级规则（任意角色收到更高 term 消息 -> becomeFollower）",
     "why": "raft.go:1104-1130 为 term 数据条件分支，确定性 (态,事件) 单值表无法单值化；K4 口径只收 current-term 行为"},
    {"item": "Candidate/PreCandidate 的 VoteLost 降级分支（becomeFollower(r.Term, None)）",
     "why": "raft.go:1698-1702 为 quorum 计票条件分支；K3 口径只收 VoteWon 胜选分支"},
    {"item": "Leader 收到 MsgApp/MsgHeartbeat/MsgSnap 高 term 降级",
     "why": "raft.go:1119-1127 同为 term 条件分支（K4）；current-term 下 stepLeader 无对应 case"},
    {"item": "poll() 内部计票（quorum.VoteResult 的 Pending 中间态）",
     "why": "raft.go:1075-1088 计票过程非角色迁移；只收计票结果触发的 become* 边"},
    {"item": "campaignTransfer 与 campaignElection/campaignPreElection 的类型差异",
     "why": "CampaignType 为参数非消息类型（raft.go:973-990,1025-1039）；事件维度取 pb.MessageType"},
    {"item": "raft 论文三态图（Figure 2：leader/follower/candidate）与代码四态口径差异",
     "why": "W1 dossier 已声明 StatePreCandidate 为代码新增（raft.go:54，论文三态图无）；本转录以代码为准（K1 口径），论文仅作主张来源"},
]

SOURCE_CITATION = [
    "etcd-io/raft main @ c51f010c851edd0dada5af41bafbf68e54617767（HEAD 提交日期 2026-10-23，2026-10-31 浅克隆）:",
    "  - raft.go:49-56 StateType 四值（StateFollower=51, StateCandidate=52, StateLeader=53, StatePreCandidate=54）",
    "  - raftpb/raft.pb.go:89-112 MessageType 枚举（0..23）；本转录收 14 个、裁剪 10 个（见 trimmed_events）",
    "  - Step:1089；hup:973；campaign:1025；poll:1075；becomeFollower:891；becomeCandidate:902；becomePreCandidate:917；becomeLeader:933",
    "  - stepLeader:1275；stepCandidate:1665（与 PreCandidate 共用，注释 1663-1664）；stepFollower:1710",
    "  - 本地留档 _scratch/sources/raft/repo/（含 .git HEAD）",
    "论文（仅作主张来源，非转录对象）: Ongaro & Ousterhout, 'In Search of an Understandable Consensus Algorithm', ATC'14, §5.1, §5.4.1（raft.github.io/raft.pdf）",
]

REWARD_RULE = (
    "+1.0 仅 Candidate|MsgVoteResp -> Leader（竞得 leadership, becomeLeader:933）一条边；"
    "-1.0 为无 case 臂/显式 ignore/ErrProposalDropped 的 (态,事件)（协议不行动，声明性惩罚）；"
    "其余处理型自环与角色迁移边 0.0。raft 协议无奖励维度，此为转录约定非协议语义。"
)

TRANSCRIPTION_RULES = (
    "K1 preVote=true（StatePreCandidate 可达前提, campaign:1029-1035）；"
    "K2 checkQuorum=true（Leader 降级边前提, 1281-1284）；"
    "K3 投票响应取 VoteWon 胜选分支（1688-1698）；"
    "K4 只转录 current-term 行为（高 term 交叉降级 raft.go:1104-1130 不收）；"
    "K5 裁剪 10 个无角色迁移/存储内部消息类型（见 trimmed_events）；"
    "K6 无行动格=-1.0 惩罚自环、显式处理自环=0.0；"
    "K7 奖励约定见 reward_rule。"
)


def build_trans():
    """表：trans[state][event] = [[p, target, reward], ...]"""
    trans = []
    for si, sname in enumerate(STATES):
        row = []
        for ei, ename in enumerate(EVENTS):
            key = "%s|%s" % (sname, ename)
            targets = TABLE[key]
            cell_out = []
            for t in targets:
                if t[0] == "self":
                    cell_out.append([1.0, si, t[1]])
                else:
                    cell_out.append([1.0, t[0], t[1]])
            row.append(cell_out)
        trans.append(row)
    return trans


def cell_citations():
    out = {}
    for sname in STATES:
        for ename in EVENTS:
            key = "%s|%s" % (sname, ename)
            out[key] = CITES[key]
    return out


def build_model():
    return {
        "n_bits": N_BITS,
        "n_actions": len(EVENTS),
        "n_states": 2 ** N_BITS,
        "goals": GOALS,
        "meta": {
            "source_system": "etcd-io/raft (go.etcd.io/raft) single-node role state machine (Follower/Candidate/Leader/PreCandidate), transcribed by field-trial W2 from pinned public source",
            "source_citation": SOURCE_CITATION,
            "variant": "event-driven-protocol-fsm",
            "encoding": "4 个真实角色态占满 2^2=4 全空间，无填充态；状态序 = raft.go:51-54 声明序",
            "state_names": STATES,
            "event_names": EVENTS,
            "semantics_class": "event: 14 个动作是 Raft 协议消息类型（raftpb.MessageType），名字属于协议、不随状态重命名 -> groups 必须声明 semantics {\"action\": \"fixed\"}（docs/judge-semantics.md）",
            "transcription_rules": TRANSCRIPTION_RULES,
            "reward_rule": REWARD_RULE,
            "trimmed_events": TRIMMED,
            "transcription_notes": {
                "cell_citations": cell_citations(),
                "not_collected": NOT_COLLECTED,
                "unregistered_cell_rule": "本模型 4 态×14 事件=56 格全部显式给出（无未注册格）；-1.0 格的引证即各格 '无 case/显式 ignore' 行号",
            },
            "regenerate": "python -X utf8 make_raft_etcd.py",
            "generator": "make_raft_etcd.py（W2 转录工程师；本脚本不运行 wuxing-gua、不算真值）",
        },
        "trans": build_trans(),
    }


def perm_identity(n):
    return list(range(n))


def perm_swap(n, i, j):
    p = list(range(n))
    p[i], p[j] = p[j], p[i]
    return p


def build_groups():
    claim_zh = ("同一集群内、相同配置且日志前缀相同的任意两个 follower 副本在协议层面等价可互换："
                "任一个都可通过同一选举机制胜出成为 leader 并服务同一份日志；角色归属只由日志新旧与票数决定，"
                "与节点身份无关。（W1 dossier case-01 symmetric_claim 原文）")
    groups = []
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, C, P)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": claim_zh + " 状态级类比（被告主张）：Candidate 与 PreCandidate 是同一选举机制的两个等待角色，"
                                "若主张等价可互换，则此对换置换应保持系统行为；两态的完成事件不同"
                                "（MsgVoteResp vs MsgPreVoteResp），事件名钉死口径下合并它们是否为协议错误由工具与独立基准裁决。",
            "construction": "order-2 对换：Candidate(1) <-> PreCandidate(3)；identity + 单对换自动闭包",
            "dossier_ref": "dossier/selection.json case-01-raft-etcd symmetric_claim",
            "semantics_note": "事件驱动协议（raftpb.MessageType）-> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, F, L)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "对照主张：Follower 与 Leader 承担不同协议角色（服务日志 vs 接收复制），"
                     "若把角色互换当对称即主张'领导与追随等价'；该候选与 W1 主张方向相反，"
                     "用于检验工具能否把结构性不同的角色区分开。",
            "construction": "order-2 对换：Follower(0) <-> Leader(2)",
            "dossier_ref": "dossier/selection.json case-01-raft-etcd（对照组）",
            "semantics_note": "事件驱动协议 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, C, P)],
        "semantics": {"action": "relabel"},
        "meta": {
            "claim": "与 g1_claim 同一置换、不同语义声明（relabel：事件名可随状态换名）。"
                     "两文件读数差 = 工具判据分派（strict vs generalized）对陌生人系统的可见行为，"
                     "由 W3 独立基准与 W4 盲跑对照裁决，本文件不预判胜负。",
            "construction": "order-2 对换：Candidate(1) <-> PreCandidate(3)；semantics=relabel",
            "dossier_ref": "dossier/selection.json case-01-raft-etcd（语义分派对照）",
            "semantics_note": "刻意反口径声明（事件类系统本应 fixed），用于暴露判据分派差异",
        },
    })
    return groups


def dump_json(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


GNAMES = [
    "g1_claim_cand_precand_swap_fixed.json",
    "g2_control_follower_leader_swap_fixed.json",
    "g3_claim_twin_cand_precand_swap_relabel.json",
]


def compute_outputs():
    """在内存中确定性地生成全部案卷字节（model.json + groups/*.json）。"""
    outputs = {}
    outputs["model.json"] = dump_json(build_model())
    for gname, g in zip(GNAMES, build_groups()):
        outputs["groups/" + gname] = dump_json(g)
    return outputs


def write_all():
    outputs = compute_outputs()
    gd = os.path.join(CASE_DIR, "groups")
    os.makedirs(gd, exist_ok=True)
    for rel, data in outputs.items():
        with open(os.path.join(CASE_DIR, rel), "wb") as f:
            f.write(data)
    return outputs


def main():
    if "--check" in sys.argv:
        expected = compute_outputs()
        all_ok = True
        for rel in sorted(expected):
            path = os.path.join(CASE_DIR, rel)
            if not os.path.isfile(path):
                all_ok = False
                print("MISSING %s" % rel)
                continue
            with open(path, "rb") as f:
                actual = f.read()
            if actual == expected[rel]:
                print("OK  %s (%d bytes)" % (rel, len(expected[rel])))
            else:
                all_ok = False
                print("MISMATCH %s" % rel)
        sys.exit(0 if all_ok else 1)
    else:
        outputs = write_all()
        for rel in sorted(outputs):
            print("WROTE %s (%d bytes)" % (rel, len(outputs[rel])))


if __name__ == "__main__":
    main()
