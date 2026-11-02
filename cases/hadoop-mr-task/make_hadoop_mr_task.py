#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_hadoop_mr_task.py — W2 盲测案卷生成器（案2 hadoop-mr-task）

生成 model.json 与 groups/*.json；`--check` 逐字节自证。
只写转录文件：不运行 wuxing-gua、不算真值、逐格给一手行号（W2 纪律①②③）。

转录对象：apache/hadoop trunk MRv2 TaskImpl 声明式状态机（TaskStateInternal 7 态）。
来源钉定：github.com/apache/hadoop trunk @ e66f40daf3cc4ebbb5164cec1ce54b71eddec8a4
（2026-10-31 经 jsdelivr CDN 抓取 raw 文件并 `git ls-remote` 记录 trunk SHA；
本地留档 _scratch/sources/hadoop/）。
"""
import json
import os
import sys

CASE_DIR = os.path.dirname(os.path.abspath(__file__))

N_BITS = 3  # 7 真实态 + 1 填充 = 8 = 2^3
STATES = ["NEW", "SCHEDULED", "RUNNING", "SUCCEEDED", "FAILED", "KILL_WAIT", "KILLED",
          "filler_7"]
EVENTS = ["T_KILL", "T_SCHEDULE", "T_RECOVER", "T_ADD_SPEC_ATTEMPT",
          "T_ATTEMPT_LAUNCHED", "T_ATTEMPT_COMMIT_PENDING", "T_ATTEMPT_FAILED",
          "T_ATTEMPT_SUCCEEDED", "T_ATTEMPT_KILLED"]
GOALS = [3]  # SUCCEEDED（目标态标记；非吸收——retroactive 边 TaskImpl.java:231-236 可离开）

NEW, SCHED, RUN, SUCC, FAIL, KW, KILLED, FILL = range(8)

# 多目标 EnumSet 行 → 等概率占位（声明性约定，条件分支依据见各行 Transition 类）
def dist(*items):
    p = 1.0 / len(items)
    return tuple((p, t, r) for (t, r) in items)

CITES = {}
TABLE = {}

def cell(state, event, targets, cite):
    key = "%s|%s" % (state, event)
    assert key not in TABLE, key
    TABLE[key] = targets
    CITES[key] = cite

SELF0 = (("self", 0.0),)
SELFN1 = (("self", -1.0),)
IMPL = "TaskImpl.java"

# ---- NEW (0) — TaskImpl.java:162-172 ----
cell("NEW", "T_KILL", ((KILLED, 0.0),), IMPL + ":165-166 addTransition(NEW, KILLED, T_KILL, KillNewTransition)")
cell("NEW", "T_SCHEDULE", ((SCHED, 0.0),), IMPL + ":163-164 addTransition(NEW, SCHEDULED, T_SCHEDULE, InitialScheduleTransition)")
cell("NEW", "T_RECOVER", dist((FAIL, 0.0), (KILLED, 0.0), (RUN, 0.0), (SUCC, 1.0)),
     IMPL + ":167-172 addTransition(NEW, EnumSet{FAILED,KILLED,RUNNING,SUCCEEDED}, T_RECOVER, RecoverTransition)；多目标条件分支→等概率占位（声明），SUCCEEDED 分支按奖励约定 +1.0")
for e in ["T_ADD_SPEC_ATTEMPT", "T_ATTEMPT_LAUNCHED", "T_ATTEMPT_COMMIT_PENDING",
          "T_ATTEMPT_FAILED", "T_ATTEMPT_SUCCEEDED", "T_ATTEMPT_KILLED"]:
    cell("NEW", e, SELFN1,
         "TaskImpl.java:162-172 NEW 态无该事件行；YARN StateMachineFactory.java:305 doTransition 对未注册 (态,事件) 抛 InvalidStateTransitionException → 转录为 -1.0 惩罚自环（声明性约定）")

# ---- SCHEDULED (1) — TaskImpl.java:174-185 ----
cell("SCHEDULED", "T_KILL", ((KW, 0.0),), IMPL + ":178-179 addTransition(SCHEDULED, KILL_WAIT, T_KILL, KILL_TRANSITION)")
cell("SCHEDULED", "T_SCHEDULE", SELFN1, "TaskImpl.java:174-185 SCHEDULED 态无 T_SCHEDULE 行；StateMachineFactory.java:305 未注册异常 → -1.0")
cell("SCHEDULED", "T_RECOVER", SELFN1, "TaskImpl.java:174-185 SCHEDULED 态无 T_RECOVER 行；StateMachineFactory.java:305 → -1.0")
cell("SCHEDULED", "T_ADD_SPEC_ATTEMPT", SELFN1, "TaskImpl.java:174-185 SCHEDULED 态无 T_ADD_SPEC_ATTEMPT 行；StateMachineFactory.java:305 → -1.0")
cell("SCHEDULED", "T_ATTEMPT_LAUNCHED", ((RUN, 0.0),), IMPL + ":176-177 addTransition(SCHEDULED, RUNNING, T_ATTEMPT_LAUNCHED, LaunchTransition)")
cell("SCHEDULED", "T_ATTEMPT_COMMIT_PENDING", SELFN1, "TaskImpl.java:174-185 SCHEDULED 态无 T_ATTEMPT_COMMIT_PENDING 行；StateMachineFactory.java:305 → -1.0")
cell("SCHEDULED", "T_ATTEMPT_FAILED", dist((SCHED, 0.0), (FAIL, 0.0)),
     IMPL + ":182-185 addTransition(SCHEDULED, EnumSet{SCHEDULED,FAILED}, T_ATTEMPT_FAILED, AttemptFailedTransition)；重试/失败条件分支→等概率占位（声明）")
cell("SCHEDULED", "T_ATTEMPT_SUCCEEDED", SELFN1, "TaskImpl.java:174-185 SCHEDULED 态无 T_ATTEMPT_SUCCEEDED 行；StateMachineFactory.java:305 → -1.0")
cell("SCHEDULED", "T_ATTEMPT_KILLED", ((SCHED, 0.0),), IMPL + ":180-181 addTransition(SCHEDULED, SCHEDULED, T_ATTEMPT_KILLED, ATTEMPT_KILLED_TRANSITION)（同态自环）")

# ---- RUNNING (2) — TaskImpl.java:187-206 ----
cell("RUNNING", "T_KILL", ((KW, 0.0),), IMPL + ":205-206 addTransition(RUNNING, KILL_WAIT, T_KILL, KILL_TRANSITION)")
cell("RUNNING", "T_SCHEDULE", SELFN1, "TaskImpl.java:187-206 RUNNING 态无 T_SCHEDULE 行；StateMachineFactory.java:305 → -1.0")
cell("RUNNING", "T_RECOVER", SELFN1, "TaskImpl.java:187-206 RUNNING 态无 T_RECOVER 行；StateMachineFactory.java:305 → -1.0")
cell("RUNNING", "T_ADD_SPEC_ATTEMPT", ((RUN, 0.0),), IMPL + ":193-194 addTransition(RUNNING, RUNNING, T_ADD_SPEC_ATTEMPT, RedundantScheduleTransition)（同态自环）")
cell("RUNNING", "T_ATTEMPT_LAUNCHED", ((RUN, 0.0),), IMPL + ":188-189 addTransition(RUNNING, RUNNING, T_ATTEMPT_LAUNCHED)（注释: more attempts may start later；同态自环）")
cell("RUNNING", "T_ATTEMPT_COMMIT_PENDING", ((RUN, 0.0),), IMPL + ":190-192 addTransition(RUNNING, RUNNING, T_ATTEMPT_COMMIT_PENDING, AttemptCommitPendingTransition)（同态自环）")
cell("RUNNING", "T_ATTEMPT_FAILED", dist((RUN, 0.0), (FAIL, 0.0)),
     IMPL + ":201-204 addTransition(RUNNING, EnumSet{RUNNING,FAILED}, T_ATTEMPT_FAILED, AttemptFailedTransition)；条件分支→等概率占位（声明）")
cell("RUNNING", "T_ATTEMPT_SUCCEEDED", ((SUCC, 1.0),), IMPL + ":195-197 addTransition(RUNNING, SUCCEEDED, T_ATTEMPT_SUCCEEDED, AttemptSucceededTransition)；奖励约定：进入 SUCCEEDED +1.0")
cell("RUNNING", "T_ATTEMPT_KILLED", ((RUN, 0.0),), IMPL + ":198-200 addTransition(RUNNING, RUNNING, T_ATTEMPT_KILLED, ATTEMPT_KILLED_TRANSITION)（同态自环）")

# ---- SUCCEEDED (3) — TaskImpl.java:230-246 ----
cell("SUCCEEDED", "T_KILL", ((SUCC, 0.0),), IMPL + ":241-246 addTransition(SUCCEEDED, SUCCEEDED, EnumSet{T_ADD_SPEC_ATTEMPT,T_ATTEMPT_COMMIT_PENDING,T_ATTEMPT_LAUNCHED,T_KILL})（源码注释 Ignore-able transitions；显式忽略行 → 0.0 自环）")
cell("SUCCEEDED", "T_SCHEDULE", SELFN1, "TaskImpl.java:230-246 SUCCEEDED 态无 T_SCHEDULE 行；StateMachineFactory.java:305 → -1.0")
cell("SUCCEEDED", "T_RECOVER", SELFN1, "TaskImpl.java:230-246 SUCCEEDED 态无 T_RECOVER 行；StateMachineFactory.java:305 → -1.0")
cell("SUCCEEDED", "T_ADD_SPEC_ATTEMPT", ((SUCC, 0.0),), IMPL + ":241-246 Ignore-able 行（显式忽略 → 0.0 自环）")
cell("SUCCEEDED", "T_ATTEMPT_LAUNCHED", ((SUCC, 0.0),), IMPL + ":241-246 Ignore-able 行（显式忽略 → 0.0 自环）")
cell("SUCCEEDED", "T_ATTEMPT_COMMIT_PENDING", ((SUCC, 0.0),), IMPL + ":241-246 Ignore-able 行（显式忽略 → 0.0 自环）")
cell("SUCCEEDED", "T_ATTEMPT_FAILED", dist((SCHED, 0.0), (SUCC, 0.0), (FAIL, 0.0)),
     IMPL + ":231-233 addTransition(SUCCEEDED, EnumSet{SCHEDULED,SUCCEEDED,FAILED}, T_ATTEMPT_FAILED, RetroactiveFailureTransition)；追溯失败条件分支→等概率占位（声明）")
cell("SUCCEEDED", "T_ATTEMPT_SUCCEEDED", ((SUCC, 0.0),), IMPL + ":237-239 addTransition(SUCCEEDED, SUCCEEDED, T_ATTEMPT_SUCCEEDED, AttemptSucceededAtSucceededTransition)（同态自环，非进入 SUCCEEDED → 0.0）")
cell("SUCCEEDED", "T_ATTEMPT_KILLED", dist((SCHED, 0.0), (SUCC, 0.0)),
     IMPL + ":234-236 addTransition(SUCCEEDED, EnumSet{SCHEDULED,SUCCEEDED}, T_ATTEMPT_KILLED, RetroactiveKilledTransition)；条件分支→等概率占位（声明）")

# ---- FAILED (4) — TaskImpl.java:248-256 ----
for e in ["T_KILL", "T_ADD_SPEC_ATTEMPT", "T_ATTEMPT_COMMIT_PENDING", "T_ATTEMPT_FAILED",
          "T_ATTEMPT_KILLED", "T_ATTEMPT_LAUNCHED", "T_ATTEMPT_SUCCEEDED"]:
    cell("FAILED", e, ((FAIL, 0.0),),
         "TaskImpl.java:249-256 addTransition(FAILED, FAILED, EnumSet{T_KILL,T_ADD_SPEC_ATTEMPT,T_ATTEMPT_COMMIT_PENDING,T_ATTEMPT_FAILED,T_ATTEMPT_KILLED,T_ATTEMPT_LAUNCHED,T_ATTEMPT_SUCCEEDED})（终态自环，显式注册）")
for e in ["T_SCHEDULE", "T_RECOVER"]:
    cell("FAILED", e, SELFN1, "TaskImpl.java:248-256 FAILED 态无该事件行；StateMachineFactory.java:305 → -1.0")

# ---- KILL_WAIT (5) — TaskImpl.java:208-228 ----
cell("KILL_WAIT", "T_KILL", ((KW, 0.0),), IMPL + ":222-228 Ignore-able 行 EnumSet{T_KILL,T_ATTEMPT_LAUNCHED,T_ATTEMPT_COMMIT_PENDING,T_ADD_SPEC_ATTEMPT}（显式忽略 → 0.0 自环）")
cell("KILL_WAIT", "T_SCHEDULE", SELFN1, "TaskImpl.java:208-228 KILL_WAIT 态无 T_SCHEDULE 行；StateMachineFactory.java:305 → -1.0")
cell("KILL_WAIT", "T_RECOVER", SELFN1, "TaskImpl.java:208-228 KILL_WAIT 态无 T_RECOVER 行；StateMachineFactory.java:305 → -1.0")
cell("KILL_WAIT", "T_ADD_SPEC_ATTEMPT", ((KW, 0.0),), IMPL + ":222-228 Ignore-able 行（显式忽略 → 0.0 自环）")
cell("KILL_WAIT", "T_ATTEMPT_LAUNCHED", ((KW, 0.0),), IMPL + ":222-228 Ignore-able 行（显式忽略 → 0.0 自环）")
cell("KILL_WAIT", "T_ATTEMPT_COMMIT_PENDING", ((KW, 0.0),), IMPL + ":222-228 Ignore-able 行（显式忽略 → 0.0 自环）")
cell("KILL_WAIT", "T_ATTEMPT_FAILED", dist((KW, 0.0), (KILLED, 0.0)),
     IMPL + ":217-220 addTransition(KILL_WAIT, EnumSet{KILL_WAIT,KILLED}, T_ATTEMPT_FAILED, KillWaitAttemptFailedTransition)；条件分支→等概率占位（声明）")
cell("KILL_WAIT", "T_ATTEMPT_SUCCEEDED", dist((KW, 0.0), (KILLED, 0.0)),
     IMPL + ":213-216 addTransition(KILL_WAIT, EnumSet{KILL_WAIT,KILLED}, T_ATTEMPT_SUCCEEDED, KillWaitAttemptSucceededTransition)；条件分支→等概率占位（声明）")
cell("KILL_WAIT", "T_ATTEMPT_KILLED", dist((KW, 0.0), (KILLED, 0.0)),
     IMPL + ":209-212 addTransition(KILL_WAIT, EnumSet{KILL_WAIT,KILLED}, T_ATTEMPT_KILLED, KillWaitAttemptKilledTransition)；条件分支→等概率占位（声明）")

# ---- KILLED (6) — TaskImpl.java:258-270 ----
for e in ["T_KILL", "T_SCHEDULE", "T_ATTEMPT_KILLED", "T_ADD_SPEC_ATTEMPT"]:
    cell("KILLED", e, ((KILLED, 0.0),),
         "TaskImpl.java:266-270 addTransition(KILLED, KILLED, EnumSet{T_KILL,T_SCHEDULE,T_ATTEMPT_KILLED,T_ADD_SPEC_ATTEMPT})（终态自环，显式注册；注释 259-265 说明竞态成因）")
for e in ["T_RECOVER", "T_ATTEMPT_LAUNCHED", "T_ATTEMPT_COMMIT_PENDING",
          "T_ATTEMPT_FAILED", "T_ATTEMPT_SUCCEEDED"]:
    cell("KILLED", e, SELFN1, "TaskImpl.java:258-270 KILLED 态无该事件行；StateMachineFactory.java:305 → -1.0")

# ---- filler (7)：填充哑态，边不引用任何真实事件语义（W2 红线） ----
for e in EVENTS:
    cell("filler_7", e, ((FILL, 0.0),),
         "填充态（2^n_bits 幂次契约，参照工具仓 examples eventfsm/gw 系 padding 惯例）：全事件自环 r=0.0，不引用真实事件语义")

NOT_COLLECTED = [
    {"item": "各 Transition 类内部的运行时条件（如 AttemptFailedTransition 的 maxAttempts 重试上限、RetroactiveFailureTransition 的 map/reduce 判别）",
     "why": "条件在事件对象/作业上下文数据中，非 (态,事件) 表可单值化；已以等概率占位声明，分支依据 = TaskImpl.java 对应 Transition 内部类"},
    {"item": "COMMIT_PENDING 状态（本仓 trunk 已无）",
     "why": "TaskStateInternal.java:22 实证 7 态不含 COMMIT_PENDING（旧版本 2.x 有）；按 trunk 原文转录，W1 states_estimate=7 与本会话复核一致"},
    {"item": "TaskAttempt 级状态机（org.apache.hadoop.mapreduce.v2.app.job.impl.TaskAttemptImpl）",
     "why": "W1 dossier 明确以 Task 级为准，attempt 级不收（防范围膨胀）"},
    {"item": "Hadoop 1.x TaskStatus.State 口径",
     "why": "W1 dossier 风险项：以 MRv2 TaskImpl 为准，1.x 不收"},
]

SOURCE_CITATION = [
    "apache/hadoop trunk @ e66f40daf3cc4ebbb5164cec1ce54b71eddec8a4（git ls-remote refs/heads/trunk, 2026-10-31）：",
    "  - hadoop-mapreduce-project/hadoop-mapreduce-client/hadoop-mapreduce-client-app/src/main/java/org/apache/hadoop/mapreduce/v2/app/job/TaskStateInternal.java:19-23（7 值枚举, line 22）",
    "  - .../job/event/TaskEventType.java:24-41（9 事件: T_KILL:27, T_SCHEDULE:30, T_RECOVER:31, T_ADD_SPEC_ATTEMPT:34, T_ATTEMPT_LAUNCHED:37, T_ATTEMPT_COMMIT_PENDING:38, T_ATTEMPT_FAILED:39, T_ATTEMPT_SUCCEEDED:40, T_ATTEMPT_KILLED:41）",
    "  - .../job/impl/TaskImpl.java:154-273 stateMachineFactory（24 个 addTransition 行: 163,165,167,176,178,180,182,188,190,193,195,198,201,205,209,213,217,222,231,234,237,241,249,266）",
    "  - hadoop-yarn-project/hadoop-yarn/hadoop-yarn-common/src/main/java/org/apache/hadoop/yarn/state/StateMachineFactory.java:305（未注册 (态,事件) 抛 InvalidStateTransitionException）",
    "  - 本地留档 _scratch/sources/hadoop/（jsdelivr CDN 抓取，trunk SHA 经 git ls-remote 核对）",
    "论文（仅作主张来源）: Dean & Ghemawat, MapReduce, OSDI'04, §3.3/§3.6（W1 快照 dossier/sources/mapreduce-osdi04.pdf）",
]

REWARD_RULE = (
    "+1.0 仅'从其他态进入 SUCCEEDED'的结果分支（RUNNING|T_ATTEMPT_SUCCEEDED 195-197；NEW|T_RECOVER 的 SUCCEEDED 分支 167-172）；"
    "-1.0 为未注册 (态,事件)（YARN StateMachineFactory 抛 InvalidStateTransitionException, :305）；"
    "显式注册的终态/忽略自环 0.0。奖励为转录约定非框架语义（声明）。"
)

TRANSCRIPTION_RULES = (
    "H1 多目标 EnumSet 行→等概率占位（条件分支未加权重；8 个多目标行: 167,182,201,209,213,217,231,234）；"
    "H2 未注册 (态,事件)→-1.0 自环（StateMachineFactory.java:305）；"
    "H3 显式注册的 Ignore-able 行→0.0 自环（与未注册惩罚区分）；"
    "H4 奖励约定见 reward_rule；H5 以 trunk 为准（非 2.x/1.x 口径）。"
)


def build_trans():
    # 格目标的三种形态：("self", r) / (态号, r) / (p, 态号, r)（dist() 等概率分支）
    trans = []
    for si, sname in enumerate(STATES):
        row = []
        for ei, ename in enumerate(EVENTS):
            key = "%s|%s" % (sname, ename)
            targets = TABLE[key]
            cell_out = []
            for t in targets:
                if isinstance(t, tuple) and len(t) == 3:
                    p, tgt, r = t
                    cell_out.append([round(p, 16), tgt, r])
                elif t[0] == "self":
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
            out["%s|%s" % (sname, ename)] = CITES["%s|%s" % (sname, ename)]
    return out


def build_model():
    return {
        "n_bits": N_BITS,
        "n_actions": len(EVENTS),
        "n_states": 2 ** N_BITS,
        "goals": GOALS,
        "meta": {
            "source_system": "apache/hadoop MRv2 TaskImpl declarative state machine (TaskStateInternal), transcribed by field-trial W2 from pinned public source",
            "source_citation": SOURCE_CITATION,
            "variant": "event-driven-framework-fsm",
            "encoding": "7 个真实态（TaskStateInternal.java:22 声明序）+ 1 个填充哑态 filler_7（8=2^3）；填充态边不引用真实事件语义",
            "state_names": STATES,
            "event_names": EVENTS,
            "semantics_class": "event: 9 个动作是 MRAppMaster TaskEvent 类型（TaskEventType），名字独立于状态 -> groups 必须声明 semantics {\"action\": \"fixed\"}",
            "transcription_rules": TRANSCRIPTION_RULES,
            "reward_rule": REWARD_RULE,
            "transcription_notes": {
                "cell_citations": cell_citations(),
                "not_collected": NOT_COLLECTED,
                "unregistered_cell_rule": "未注册 (态,事件) 格引证统一为 TaskImpl.java 对应态区间 + StateMachineFactory.java:305",
                "addTransition_rows": "24 行（163,165,167,176,178,180,182,188,190,193,195,198,201,205,209,213,217,222,231,234,237,241,249,266）；8 态×9 事件=72 格全显式，8 个多目标 EnumSet 行展开后共 83 个结果分支（72+11），跨态结果分支 18",
            },
            "regenerate": "python -X utf8 make_hadoop_mr_task.py",
            "generator": "make_hadoop_mr_task.py（W2 转录工程师；不运行 wuxing-gua、不算真值）",
        },
        "trans": build_trans(),
    }


def perm_identity(n):
    return list(range(n))


def perm_swap(n, i, j):
    p = list(range(n))
    p[i], p[j] = p[j], p[i]
    return p


GNAMES = [
    "g1_claim_failed_killed_swap_fixed.json",
    "g2_control_new_scheduled_swap_fixed.json",
    "g3_control_running_killwait_swap_fixed.json",
]


def build_groups():
    claim_zh = ("相同输入分片的 map/reduce 任务在任意 worker 上（重）执行结果等价——primary 与 backup 执行可互换，"
                "任一次成功即算完成；任务失败后可在任何其他 worker 上重跑顶替。（W1 dossier case-02 symmetric_claim 原文）")
    groups = []
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, FAIL, KILLED)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": claim_zh + " 终态级类比（被告主张）：FAILED 与 KILLED 都是任务终局，"
                                "若'失败与被杀对任务等价、重跑顶替语义相同'成立，则此对换应保持系统行为；"
                                "两态的注册事件集不同（FAILED 7 个 vs KILLED 4 个）且前驱事件不同，裁决交给工具与独立基准。",
            "construction": "order-2 对换：FAILED(4) <-> KILLED(6)",
            "dossier_ref": "dossier/selection.json case-02-hadoop-mr-task symmetric_claim",
            "semantics_note": "事件驱动框架（TaskEventType）-> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, NEW, SCHED)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "对照主张：NEW（已创建未调度）与 SCHEDULED（已调度待 launch）是流水线相邻阶段，"
                     "若主张'调度前后等价可互换'则此对换应保持行为；两态事件集不同（NEW 有 T_RECOVER，SCHEDULED 无），判别交由工具/基准。",
            "construction": "order-2 对换：NEW(0) <-> SCHEDULED(1)",
            "dossier_ref": "dossier/selection.json case-02-hadoop-mr-task（对照组）",
            "semantics_note": "事件驱动框架 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, RUN, KW)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "对照主张：RUNNING（执行中）与 KILL_WAIT（等待被杀确认）若等价可互换，"
                     "则'运行与等待死亡无区别'；两态的自环/完成事件结构差异显著，判别交由工具/基准。",
            "construction": "order-2 对换：RUNNING(2) <-> KILL_WAIT(5)",
            "dossier_ref": "dossier/selection.json case-02-hadoop-mr-task（对照组；W1 风险项'KILL_WAIT 自循环边多防漏标'已逐格引证）",
            "semantics_note": "事件驱动框架 -> fixed",
        },
    })
    return groups


def dump_json(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def compute_outputs():
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
