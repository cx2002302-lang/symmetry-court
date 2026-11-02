# 案3 k8s-pod-lifecycle — W2 转录案卷 README

- 波次/角色：field-trial W2。未运行 wuxing-gua、未算真值、逐边一手文档引句（W2 纪律①②③）。
- 上游：`dossier/selection.json` case-03-k8s-pod-lifecycle（W1 选案与对称主张）。

## 转录对象

Kubernetes 官方文档 **Pod Lifecycle 页的 PodPhase 五相生命周期**（Pending / Running / Succeeded / Failed / Unknown）。W1 dossier 风险项明示：文档是散文非迁移表，逐边回原文找依据、不确定的边记未收录——本案是五案中转录判定主观性最高的一案，每个弱判读格在引证中显式标注 `weak`。

来源钉定：

| 来源 | 核验方式（本会话实跑） |
|---|---|
| kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ | W1 快照 `dossier/sources/k8s_pod_lifecycle.html` + W2 本会话 WebFetch 在线抽查：5 相定义、lifecycle 句、node-death 句、1.27 deletion 句、PodGC 句**逐句一致**（2026-10-31） |
| Deployment / Service 页 | W1 快照，仅作主张来源，不进转录 |

## 模型规模（落盘实值，见 model.json）

- 状态：5 真实相 + 3 填充哑态（8 = 2^3，n_bits=3）。
- 事件：7（container_start / all_containers_succeeded / any_container_failed / node_lost / kubelet_unreachable / pod_deletion / gc_mark_failed），在 W1 估计 6-8 区间内。
- 事件表：8×7 = 56 格全部逐格引证（引官方原句）；结果分支 57，跨态分支 13（W1 估计 7-10 边，本转录 13 条跨态分支——多出的部分来自 PodGC 句支撑的 gc_mark_failed 与 1.27 deletion 条件分支，口径已声明）。
- 被告群：3 个（主张群 1 + 方向对照群 1 + 填充对换正控群 1）。

## 证据强度分级（meta.transcription_notes.evidence_grading）

- **强**（迁移语句/相定义直接支撑）：Pending→Running（lifecycle 句）、Running→Succeeded/Failed（lifecycle 句+相定义）、node_lost 三边（"If a node dies or is disconnected..."）、gc_mark_failed 四格（PodGC 句 "mark them as failed if they are in a non-terminal phase"）、Succeeded/Failed 吸收（相定义"will not be restarted"+terminal 集合）。
- **弱**（定义式判读，引证标注 weak）：Pending/Running→Unknown（Unknown 相定义 "This phase typically occurs due to an error in communicating with the node..."——定义暗示而非迁移语句）。
- **未收录**（7 项，全文在 not_collected）：Pending→Failed 直达、Pending 的 deletion/Succeeded、Unknown 恢复、Running→Pending、容器级三态、condition 字段、kubelet restart 行为。

## 转录口径

1. **K1 散文转录纪律**：每格回引文档原句；无语句支撑的格 -1.0 并入 not_collected。
2. **K2 pod_deletion 条件分支**（Failed/Succeeded 取决于容器退出状态，1.27 句）→ 等概率占位。
3. **K3 Unknown 两格弱依据**显式标注。
4. **K4** Succeeded/Failed 吸收态；**K5** 奖励：进入 Succeeded +1.0（声明性约定）。

## 被告群（groups/）

| 文件 | 置换 | 主张摘要 |
|---|---|---|
| g1_claim_succeeded_failed_swap_fixed.json | swap Succeeded↔Failed | W1 副本可互换主张的终相级类比：两个 terminal 相下副本替换语义等价 |
| g2_control_pending_running_swap_fixed.json | swap Pending↔Running | 对照：lifecycle 句的方向性（Pending 先于 Running）是否被尊重 |
| g3_pads_swap_fixed.json | swap filler_5↔filler_6 | 正控：填充对换是真对称（rung 1c pads 惯例），检验工具对平凡真对称的放行 |

## 自证记录（本会话实跑）

- `python -X utf8 -I make_k8s_pod_lifecycle.py` → 生成 model.json(22,747B) + 3 群文件。
- `python -X utf8 -I make_k8s_pod_lifecycle.py --check` → 4 文件全 OK，exit 0。
- 自写结构校验（非工具）：trans 8×7、56 格全引证、概率和=1、群置换合法、跨态分支 13。

--check 覆盖 model.json 与 groups/*.json；README 手工文档不在字节自证范围（声明）。
