#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_k8s_pod_lifecycle.py — W2 盲测案卷生成器（案3 k8s-pod-lifecycle）

生成 model.json 与 groups/*.json；`--check` 逐字节自证。
只写转录文件：不运行 wuxing-gua、不算真值、逐边给一手文档原句（W2 纪律①②③）。

转录对象：Kubernetes 官方文档 Pod Lifecycle 页的 PodPhase 五相生命周期（散文口径，
W1 dossier 风险项已声明"文档非迁移表，逐边回原文找依据，不确定的边记未收录"）。
来源钉定：https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
（W1 快照 dossier/sources/k8s_pod_lifecycle.html + W2 本会话 WebFetch 在线抽查逐句一致，
2026-10-31）。
"""
import json
import os
import sys

CASE_DIR = os.path.dirname(os.path.abspath(__file__))

N_BITS = 3  # 5 真实态 + 3 填充 = 8 = 2^3
STATES = ["Pending", "Running", "Succeeded", "Failed", "Unknown",
          "filler_5", "filler_6", "filler_7"]
EVENTS = ["container_start", "all_containers_succeeded", "any_container_failed",
          "node_lost", "kubelet_unreachable", "pod_deletion", "gc_mark_failed"]
GOALS = [2, 3]  # Succeeded/Failed 为文档声明的 terminal phases

PENDING, RUNNING, SUCC, FAILED, UNKNOWN = 0, 1, 2, 3, 4

DOC = "kubernetes.io pod-lifecycle 页（W1 快照 + W2 2026-10-31 WebFetch 在线抽查一致）"

def q(text):
    return "引文: \"%s\"（%s）" % (text, DOC)

CITES = {}
TABLE = {}

def cell(state, event, targets, cite):
    key = "%s|%s" % (state, event)
    assert key not in TABLE, key
    TABLE[key] = targets
    CITES[key] = cite

SELF0 = (("self", 0.0),)
SELFN1 = (("self", -1.0),)

LIFECYCLE = ("Pods follow a defined lifecycle, starting in the Pending phase, moving through Running "
             "if at least one of its primary containers starts OK, and then through either the Succeeded "
             "or Failed phases depending on whether any container in the Pod terminated in failure.")
NODE_LOST = ("If a node dies or is disconnected from the rest of the cluster, Kubernetes applies a policy "
             "for setting the phase of all Pods on the lost node to Failed.")
TERMINAL = ("Since Kubernetes 1.27, the kubelet transitions deleted Pods to a terminal phase (Failed or "
            "Succeeded depending on the exit statuses of the pod containers) before their deletion from the API server")
PODGC = ("Along with cleaning up the Pods, PodGC will also mark them as failed if they are in a non-terminal phase.")
UNKNOWN_DEF = ("For some reason the state of the Pod could not be obtained. This phase typically occurs due to "
               "an error in communicating with the node where the Pod should be running.")
SUCC_DEF = "All containers in the Pod have terminated in success, and will not be restarted."
FAILED_DEF = ("All containers in the Pod have terminated, and at least one container has terminated in failure.")

# ---- Pending (0) ----
cell("Pending", "container_start", ((RUNNING, 0.0),),
     q(LIFECYCLE) + "；Running 相定义 \"The Pod has been bound to a node, and all of the containers have been created.\"（同页）")
cell("Pending", "all_containers_succeeded", SELFN1,
     "Pending 相无'全部容器成功终止'语义（Pending 定义：容器尚未建好/未就绪）；文档未给出该迁移 → 未收录，模型记 -1.0 惩罚自环")
cell("Pending", "any_container_failed", SELFN1,
     "文档未给出 Pending 直接因容器失败进入 Failed 的迁移语句（lifecycle 句把 Failed 挂在 Running 之后）→ 未收录，记 -1.0")
cell("Pending", "node_lost", ((FAILED, 0.0),),
     q(NODE_LOST) + "；node death policy 覆盖 lost node 上'所有 Pods'（含 Pending）")
cell("Pending", "kubelet_unreachable", ((UNKNOWN, 0.0),),
     "Unknown 相定义: \"%s\"——定义式弱依据（判读标注：weak，定义暗示相可出现于节点失联，未写成迁移语句）" % UNKNOWN_DEF)
cell("Pending", "pod_deletion", SELFN1,
     "deleted Pods 转 terminal 相的语句以容器退出状态为条件（%s）；Pending 的容器未创建、退出状态无定义 → 未收录，记 -1.0" % TERMINAL)
cell("Pending", "gc_mark_failed", ((FAILED, 0.0),),
     q(PODGC) + "；non-terminal phase 含 Pending")

# ---- Running (1) ----
cell("Running", "container_start", SELFN1,
     "Running 相下'容器又启动一个'的迁移文档未陈述（Running 定义允许 starting/restarting 但未写相变）→ 未收录，记 -1.0")
cell("Running", "all_containers_succeeded", ((SUCC, 1.0),),
     q(LIFECYCLE) + "；Succeeded 相定义: \"%s\"；奖励约定：进入 Succeeded +1.0" % SUCC_DEF)
cell("Running", "any_container_failed", ((FAILED, 0.0),),
     q(LIFECYCLE) + "；Failed 相定义: \"%s\"" % FAILED_DEF)
cell("Running", "node_lost", ((FAILED, 0.0),), q(NODE_LOST))
cell("Running", "kubelet_unreachable", ((UNKNOWN, 0.0),),
     "Unknown 相定义: \"%s\"——定义式弱依据（判读标注：weak）" % UNKNOWN_DEF)
cell("Running", "pod_deletion", (((0.5, SUCC, 1.0)), ((0.5, FAILED, 0.0))),
     q(TERMINAL) + "；退出状态条件分支→等概率占位（声明）；Succeeded 分支按奖励约定 +1.0")
cell("Running", "gc_mark_failed", ((FAILED, 0.0),), q(PODGC) + "；non-terminal phase 含 Running")

# ---- Succeeded (2)：terminal ----
for e in EVENTS:
    cell("Succeeded", e, ((SUCC, 0.0),),
         "Succeeded 相定义: \"%s\" + 文档 terminal 相语义（%s；PodGC 句以 non-terminal phase 反衬 terminal 集合）→ 吸收自环 0.0" % (SUCC_DEF, TERMINAL))

# ---- Failed (3)：terminal ----
for e in EVENTS:
    cell("Failed", e, ((FAILED, 0.0),),
         "Failed 相定义: \"%s\" + 文档 terminal 相语义（%s）→ 吸收自环 0.0" % (FAILED_DEF, TERMINAL))

# ---- Unknown (4) ----
cell("Unknown", "container_start", SELFN1,
     "文档未给出 Unknown 恢复到前一相的迁移语句 → 未收录，记 -1.0")
cell("Unknown", "all_containers_succeeded", SELFN1,
     "文档未给出 Unknown→Succeeded 迁移语句 → 未收录，记 -1.0")
cell("Unknown", "any_container_failed", SELFN1,
     "文档未给出 Unknown→Failed 的容器失败迁移语句 → 未收录，记 -1.0")
cell("Unknown", "node_lost", ((FAILED, 0.0),),
     q(NODE_LOST) + "；断连（disconnected）即 Unknown 相定义所述场景的延续，超时后 phase 置 Failed")
cell("Unknown", "kubelet_unreachable", ((UNKNOWN, 0.0),),
     "Unknown 相定义（%s）：持续失联则停留 Unknown；自环" % UNKNOWN_DEF)
cell("Unknown", "pod_deletion", SELFN1,
     "deleted Pods 转 terminal 相语句对 Unknown 相未逐字覆盖 → 未收录，记 -1.0")
cell("Unknown", "gc_mark_failed", ((FAILED, 0.0),), q(PODGC) + "；non-terminal phase 含 Unknown")

# ---- fillers (5,6,7)：哑态，不引用真实事件语义 ----
for si in ["filler_5", "filler_6", "filler_7"]:
    for e in EVENTS:
        cell(si, e, (("self", 0.0),),
             "填充态（2^n_bits 幂次契约，参照工具仓 padding 惯例）：全事件自环 r=0.0，不引用真实事件语义")

NOT_COLLECTED = [
    {"item": "Pending → Failed（容器失败直达）",
     "why": "lifecycle 句把 Failed 挂在 Running 之后；无 Pending 直达语句"},
    {"item": "Pending → Succeeded / Pending 的 pod_deletion",
     "why": "deleted-Pods 转 terminal 相以'容器退出状态'为条件；Pending 容器未创建，无定义"},
    {"item": "Unknown 恢复（→Pending/Running）或 Unknown→Succeeded",
     "why": "文档无恢复迁移语句"},
    {"item": "Running → Pending（容器全部退出但未到 terminal 判据的中间态）",
     "why": "文档未陈述"},
    {"item": "容器级三态 Waiting/Running/Terminated",
     "why": "W1 dossier 风险项：容器级状态不收，防范围膨胀"},
    {"item": "CrashLoopBackOff / PodScheduled、Ready 等 condition 字段",
     "why": "为 condition/原因标注而非 PodPhase 迁移"},
    {"item": "Kubelet restart 期间 Pod 行为",
     "why": "文档描述为运行时行为非相迁移"},
]

SOURCE_CITATION = [
    "Kubernetes 官方文档 Pod Lifecycle 页: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/",
    "  - W1 快照 dossier/sources/k8s_pod_lifecycle.html；W2 本会话（2026-10-31）WebFetch 在线抽查：5 相定义、lifecycle 句、",
    "    node-death 句、1.27 deletion 句、PodGC 句与快照逐句一致",
    "  - 关键原文（全部在 transcription_notes.cell_citations 逐边回引）: lifecycle 句 / Pending,Running,Succeeded,Failed,Unknown 相定义 /",
    "    \"If a node dies or is disconnected...\" / \"Since Kubernetes 1.27, the kubelet transitions deleted Pods to a terminal phase...\" /",
    "    \"Along with cleaning up the Pods, PodGC will also mark them as failed if they are in a non-terminal phase.\"",
    "辅助主张来源（W1 快照，未进转录）: kubernetes.io Deployment 页、Service 页",
]

REWARD_RULE = (
    "+1.0 仅'进入 Succeeded'的结果分支（Running|all_containers_succeeded；Running|pod_deletion 的 Succeeded 分支）；"
    "-1.0 为文档未陈述迁移的 (相,事件)（含全部'未收录'格）；terminal 相吸收自环与填充态 0.0。"
    "奖励为转录约定非 K8s 语义（声明）。"
)

TRANSCRIPTION_RULES = (
    "K1 散文文档转录：每条边回引文档原句（cell_citations），无语句支撑的格记 -1.0 并入 not_collected；"
    "K2 pod_deletion 的 Succeeded/Failed 条件分支→等概率占位（1.27 句为条件式）；"
    "K3 Unknown 两格（Pending/Running→Unknown）为定义式弱依据，cell_citations 中标注 weak；"
    "K4 Succeeded/Failed 按文档 terminal 语义作吸收态；K5 奖励约定见 reward_rule。"
)


def build_trans():
    trans = []
    for si, sname in enumerate(STATES):
        row = []
        for ei, ename in enumerate(EVENTS):
            targets = TABLE["%s|%s" % (sname, ename)]
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
    return {"%s|%s" % (s, e): CITES["%s|%s" % (s, e)] for s in STATES for e in EVENTS}


def build_model():
    return {
        "n_bits": N_BITS,
        "n_actions": len(EVENTS),
        "n_states": 2 ** N_BITS,
        "goals": GOALS,
        "meta": {
            "source_system": "Kubernetes official docs Pod Lifecycle (PodPhase), transcribed by field-trial W2 from pinned public docs",
            "source_citation": SOURCE_CITATION,
            "variant": "event-driven-observed-lifecycle",
            "encoding": "5 个真实 PodPhase + 3 个填充哑态 filler_5/6/7（8=2^3）；填充态边不引用真实事件语义",
            "state_names": STATES,
            "event_names": EVENTS,
            "semantics_class": "event: 7 个动作是控制面/节点侧外部事件（调度启动、容器终止、节点失联、删除、GC），名字独立于状态 -> groups 必须声明 semantics {\"action\": \"fixed\"}",
            "transcription_rules": TRANSCRIPTION_RULES,
            "reward_rule": REWARD_RULE,
            "transcription_notes": {
                "cell_citations": cell_citations(),
                "not_collected": NOT_COLLECTED,
                "unregistered_cell_rule": "文档未陈述的 (相,事件) 统一 -1.0 惩罚自环，理由在 not_collected",
                "evidence_grading": "强（迁移语句/相定义直接支撑）: Pending→Running, Running→Succeeded/Failed, node_lost 三边, gc 两边, terminal 吸收；弱（定义式判读, 标注 weak）: Pending/Running→Unknown",
            },
            "regenerate": "python -X utf8 make_k8s_pod_lifecycle.py",
            "generator": "make_k8s_pod_lifecycle.py（W2 转录工程师；不运行 wuxing-gua、不算真值）",
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
    "g1_claim_succeeded_failed_swap_fixed.json",
    "g2_control_pending_running_swap_fixed.json",
    "g3_pads_swap_fixed.json",
]


def build_groups():
    claim_zh = ("同一 Deployment 模板产出的 Pod 副本可互换：Service 只按 label/端点集合做负载均衡，副本个体身份无关"
                "（副本增删只触发 EndpointSlices 更新）；任何副本可被删除并在任意节点按同一模板重建。"
                "（W1 dossier case-03 symmetric_claim 原文）")
    groups = []
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, SUCC, FAILED)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": claim_zh + " 终相级类比（被告主张）：两个 terminal 相下副本替换语义等价"
                                "（删除任一终态副本都触发同模板重建），若终相等价则此对换应保持系统行为；"
                                "两相前驱事件不同（all_containers_succeeded vs any_container_failed），裁决交工具/基准。",
            "construction": "order-2 对换：Succeeded(2) <-> Failed(3)",
            "dossier_ref": "dossier/selection.json case-03-k8s-pod-lifecycle symmetric_claim",
            "semantics_note": "控制面/节点侧外部事件 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, PENDING, RUNNING)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "对照主张：文档 lifecycle 句给出 Pending→Running 的方向性（'starting in the Pending phase, moving through Running'），"
                     "若主张两相无序等价则此对换应保持行为；判别交工具/基准。",
            "construction": "order-2 对换：Pending(0) <-> Running(1)",
            "dossier_ref": "dossier/selection.json case-03-k8s-pod-lifecycle（对照组）",
            "semantics_note": "外部事件 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, 5, 6)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "正控对照：两个填充哑态 filler_5/filler_6 行完全相同（全事件自环 0.0、不引用真实事件语义），"
                     "对换在 fixed 口径下是货真价实的对称；用于检验工具对'平凡真对称'的放行行为（参照工具仓 rung 1c pads 惯例）。",
            "construction": "order-2 对换：filler_5(5) <-> filler_6(6)",
            "dossier_ref": "dossier/selection.json case-03-k8s-pod-lifecycle（正控组）",
            "semantics_note": "padding 行不引用事件 -> fixed 下亦真对称",
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
