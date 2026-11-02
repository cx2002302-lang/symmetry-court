#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_usb2_device_states.py — W2 盲测案卷生成器（案5 usb2-device-states）

生成 model.json 与 groups/*.json；`--check` 逐字节自证。
只写转录文件：不运行 wuxing-gua、不算真值、逐边给 spec 条号+图证（W2 纪律①②③）。

转录对象：USB 2.0 规范 Chapter 9 §9.1 设备可见状态机（Figure 9-1 / Table 9-1）。
来源钉定：usb.org 官方包 usb_20_20250603.zip -> usb_20_20240927/usb_20.pdf
（W1 快照 dossier/sources/usb20/；W2 本会话用 pdftotext -layout + PyMuPDF 渲染
Figure 9-1 页逐箭头目视核验）。
"""
import json
import os
import sys

CASE_DIR = os.path.dirname(os.path.abspath(__file__))

N_BITS = 3  # 6 真实态 + 2 填充 = 8 = 2^3
STATES = ["Attached", "Powered", "Default", "Address", "Configured", "Suspended",
          "filler_6", "filler_7"]
EVENTS = ["hub_configured", "hub_reset_or_deconfigured", "reset", "address_assigned",
          "device_configured", "device_deconfigured", "bus_inactive", "bus_activity"]
GOALS = []  # Configured 可被 deconfigure/suspend 离开；全图无吸收态

ATT, POW, DEF, ADR, CFG, SUS = range(6)

FIG = "USB 2.0 spec Figure 9-1 (doc p.240, PDF p.268; W2 本会话 PyMuPDF 渲染目视核验箭头方向)"
TB = "USB 2.0 spec Table 9-1 (doc p.240-241)"

CITES = {}
TABLE = {}

def cell(state, event, targets, cite):
    key = "%s|%s" % (state, event)
    assert key not in TABLE, key
    TABLE[key] = targets
    CITES[key] = cite

SELF0 = (("self", 0.0),)
SELFN1 = (("self", -1.0),)

# ---- Attached (0) ----
cell("Attached", "hub_configured", ((POW, 0.0),),
     FIG + "：Attached 右下弧 'Hub Configured' 箭头入 Powered；正文 §9.1.1.2：'they are not considered to be in "
           "the Powered state until they are attached to the USB and VBUS is applied'")
for e in ["hub_reset_or_deconfigured", "reset", "address_assigned", "device_configured",
          "device_deconfigured", "bus_inactive", "bus_activity"]:
    cell("Attached", e, SELFN1,
         "Figure 9-1 中 Attached 无该出箭头（其唯一出弧为 'Hub Configured'）→ 图判读：未收录，记 -1.0")

# ---- Powered (1) ----
cell("Powered", "hub_reset_or_deconfigured", ((ATT, 0.0),),
     FIG + "：Powered 左上弧 'Hub Reset or Deconfigured' 箭头入 Attached")
cell("Powered", "reset", ((DEF, 0.0),),
     FIG + "：Powered 下方弧 'Reset' 箭头入 Default；正文 §9.1.1.3：'After receiving a reset, the device is then "
           "addressable at the default address'；§9.1.1 note：'USB devices perform a reset operation in response to "
           "reset signaling on the upstream facing port'")
cell("Powered", "bus_inactive", ((SUS, 0.0),),
     FIG + "：Powered-Suspended 弧对 'Bus Inactive'；正文 §9.1.1.6：'Attached devices must be prepared to suspend at "
           "any time they are powered'")
for e in ["hub_configured", "address_assigned", "device_configured", "device_deconfigured",
          "bus_activity"]:
    cell("Powered", e, SELFN1, "Figure 9-1 中 Powered 无该出箭头 → 图判读：未收录，记 -1.0")

# ---- Default (2) ----
cell("Default", "address_assigned", ((ADR, 0.0),),
     FIG + "：Default 下方弧 'Address Assigned' 箭头入 Address；正文 §9.1.1.4：'Each USB device is assigned a unique "
           "address by the host after attachment or after reset'")
cell("Default", "bus_inactive", ((SUS, 0.0),),
     FIG + "：Default-Suspended 弧对 'Bus Inactive'；§9.1.1.6")
for e in ["hub_configured", "hub_reset_or_deconfigured", "reset", "device_configured",
          "device_deconfigured", "bus_activity"]:
    cell("Default", e, SELFN1, "Figure 9-1 中 Default 无该出箭头 → 图判读：未收录，记 -1.0")

# ---- Address (3) ----
cell("Address", "device_configured", ((CFG, 1.0),),
     FIG + "：Address-Configured 弧对 'Device Configured' 箭头入 Configured；正文 §9.1.1.5：'configuration involves "
           "correctly processing a SetConfiguration() request with a non-zero configuration value'；Table 9-1 Configured 行："
           "'The host may now use the function provided by the device'；奖励约定：进入 Configured +1.0")
cell("Address", "bus_inactive", ((SUS, 0.0),), FIG + "：Address-Suspended 弧对 'Bus Inactive'；§9.1.1.6")
for e in ["hub_configured", "hub_reset_or_deconfigured", "reset", "address_assigned",
          "device_deconfigured", "bus_activity"]:
    cell("Address", e, SELFN1, "Figure 9-1 中 Address 无该出箭头 → 图判读：未收录，记 -1.0")

# ---- Configured (4) ----
cell("Configured", "device_deconfigured", ((ADR, 0.0),),
     FIG + "：Configured-Address 弧对 'Device Deconfigured' 箭头入 Address；正文 §9.1.1.2：电源源切换时 'the device will "
           "lose its current configuration and address and return to the Powered state'（回落 Powered 的弧线未单列转录，见 not_collected）"
           "与 'must return to the Address state'（自供电>100mA 配置切总线供电）")
cell("Configured", "bus_inactive", ((SUS, 0.0),), FIG + "：Configured-Suspended 弧对 'Bus Inactive'；§9.1.1.6")
for e in ["hub_configured", "hub_reset_or_deconfigured", "reset", "address_assigned",
          "device_configured", "bus_activity"]:
    cell("Configured", e, SELFN1, "Figure 9-1 中 Configured 无该出箭头 → 图判读：未收录，记 -1.0")

# ---- Suspended (5) ----
cell("Suspended", "bus_activity",
     (((0.25, POW, 0.0)), ((0.25, DEF, 0.0)), ((0.25, ADR, 0.0)), ((0.25, CFG, 0.0))),
     FIG + "：四条 'Bus Activity' 回弧按来源态配对（Powered/Default/Address/Configured 各一）；"
           "单 Suspended 态编码下四目标等概率占位（声明；§9.1.1.6：'A USB device exits suspend mode when there is bus activity'）")
for e in ["hub_configured", "hub_reset_or_deconfigured", "reset", "address_assigned",
          "device_configured", "device_deconfigured", "bus_inactive"]:
    cell("Suspended", e, SELFN1, "Figure 9-1 中 Suspended 无该出箭头 → 图判读：未收录，记 -1.0")

# ---- fillers ----
for si in ["filler_6", "filler_7"]:
    for e in EVENTS:
        cell(si, e, (("self", 0.0),),
             "填充态（2^n_bits 幂次契约，参照工具仓 padding 惯例）：全事件自环 r=0.0，不引用真实事件语义")

NOT_COLLECTED = [
    {"item": "attach 入边（'not attached' -> Attached）",
     "why": "来源态'not attached'不在 Figure 9-1 六态之内（Table 9-1 第一行全 '--'，§9.1.1.1：detached 状态本规范不定义）；无模型内源态"},
    {"item": "detach 出边（各态 -> 'not attached'）",
     "why": "同上，目标态不在模型内"},
    {"item": "Power Interruption 回弧（Default -> Powered）与 Configured -> Powered 大回弧",
     "why": "栅格化图中 Power Interruption 弧起点与 Reset 大圆弧交叉，起点态（Default/Address/Configured 候选）无法单值判读；"
            "§9.1.1.2 给出规范语义（power source change -> return to the Powered state）但未逐态指明——按宁缺毋滥不收，理由留档"},
    {"item": "Hub Reset or Deconfigured 弧是否可自 Default/Address/Configured 触发",
     "why": "图中该弧仅画自 Powered；其他态同触发未画出"},
    {"item": "selective suspend（hub port disabled -> Suspended, §9.1.1.6）",
     "why": "与 bus_inactive 同目标边；图箭头标签只有 'Bus Inactive'，按图转录并把该触发词记于此"},
    {"item": "高/全/低速 reset chirp 与电气层细节（Chapter 7）",
     "why": "W1 dossier 风险项：电气层不收"},
    {"item": "Suspended 期间 remote wakeup（§9.1.1.6 可选能力）",
     "why": "可选设备能力非状态迁移"},
]

SOURCE_CITATION = [
    "Universal Serial Bus Specification Revision 2.0（USB-IF 官方包 usb_20_20250603.zip -> usb_20_20240927/usb_20.pdf;",
    " W1 快照 dossier/sources/usb20/；来源页 https://www.usb.org/document-library/usb-20-specification）：",
    "  - §9.1 USB Device States（doc p.239）",
    "  - §9.1.1 Visible Device States（doc p.239）+ §9.1.1 note（reset signaling 句）",
    "  - Figure 9-1 Device State Diagram（doc p.240 = PDF p.268；W2 本会话 pdftotext -layout + PyMuPDF 渲染 PNG 逐箭头目视核验）",
    "  - Table 9-1 Visible Device States（doc p.240-241；6 态 Yes/No/-- 矩阵 + '-- Other attributes are not significant'）",
    "  - §9.1.1.1 Attached / §9.1.1.2 Powered（VBUS applied 句、power source change 回落句）/ §9.1.1.3 Default（reset 句）/",
    "    §9.1.1.4 Address（unique address 句）/ §9.1.1.5 Configured（SetConfiguration() non-zero 句）/ §9.1.1.6 Suspended（bus inactivity 句、",
    "    bus activity 恢复句、selective suspend 句）（doc p.241-242）",
    "  - 本地快照全文 usb_20_spec.txt（W1 pdftotext 抽取，30360 行；W2 复用并 -layout 重抽 §9.1 区域）",
]

REWARD_RULE = (
    "+1.0 仅 Address|device_configured -> Configured 一条边（Table 9-1 Configured 行 'The host may now use the function "
    "provided by the device'）；-1.0 为图中无箭头的 (态,事件)；Suspended 多目标占位自环与填充态 0.0。"
    "奖励为转录约定非规范语义（声明）。"
)

TRANSCRIPTION_RULES = (
    "U1 图文互证：每条边给 Figure 9-1 弧线标签 + §9.1.1.x 正文句（W1 风险项'三方互证'落实为图+表+正文三源）；"
    "U2 Suspended 的 bus_activity 回弧按图中来源态配对，单态编码下四目标等概率占位（声明）；"
    "U3 suspend 入边按图 4 条（Powered/Default/Address/Configured 各一）；"
    "U4 Power Interruption/attach/detach 弧因图判读歧义或态外目标不收（not_collected）；"
    "U5 奖励约定见 reward_rule。"
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
            "source_system": "USB 2.0 Specification Chapter 9 device visible state machine (Figure 9-1 / Table 9-1), transcribed by field-trial W2 from the official USB-IF package",
            "source_citation": SOURCE_CITATION,
            "variant": "event-driven-hardware-fsm",
            "encoding": "6 个真实态（Table 9-1 顺序）+ 2 个填充哑态（8=2^3）；填充态边不引用真实事件语义",
            "state_names": STATES,
            "event_names": EVENTS,
            "semantics_class": "event: 8 个动作是总线/主机侧外部事件（hub 配置与复位、总线复位、地址分配、SetConfiguration、总线静默与活动），名字属于协议 -> groups 必须声明 semantics {\"action\": \"fixed\"}",
            "transcription_rules": TRANSCRIPTION_RULES,
            "reward_rule": REWARD_RULE,
            "transcription_notes": {
                "cell_citations": cell_citations(),
                "not_collected": NOT_COLLECTED,
                "unregistered_cell_rule": "图中无箭头的 (态,事件) 统一 -1.0；引证注明'图判读：未收录'",
            },
            "regenerate": "python -X utf8 make_usb2_device_states.py",
            "generator": "make_usb2_device_states.py（W2 转录工程师；不运行 wuxing-gua、不算真值）",
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
    "g1_claim_default_address_swap_fixed.json",
    "g2_control_attached_configured_swap_fixed.json",
    "g3_pads_swap_fixed.json",
]


def build_groups():
    claim_zh = ("同一设备的枚举路径 Attached -> Powered -> Default -> Address -> Configured 与所插端口、所分配地址值无关："
                "任意可工作端口热插拔都走同一状态序列；主机按描述符（而非端口/地址实例）识别绑定设备，相同描述符的设备实例对主机等价。"
                "（W1 dossier case-05 symmetric_claim 原文）")
    groups = []
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, DEF, ADR)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": claim_zh + " 状态级类比（被告主张）：Default（已复位未编址）与 Address（已编址未配置）两个枚举中间态"
                                "等价可互换——若'地址值只是载荷、路径与端口无关'则此对换应保持行为；"
                                "两态的入边事件不同（reset vs address_assigned），裁决交工具/基准。",
            "construction": "order-2 对换：Default(2) <-> Address(3)",
            "dossier_ref": "dossier/selection.json case-05-usb2-device-states symmetric_claim",
            "semantics_note": "总线/主机侧事件 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, ATT, CFG)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "对照主张：Attached（仅贴上未供电）与 Configured（主机可用）为枚举路径两端点，"
                     "若主张'端点态等价'则此对换应保持行为；两态结构差异最大（Attached 仅 1 出边 vs Configured 2 出边），判别交工具/基准。",
            "construction": "order-2 对换：Attached(0) <-> Configured(4)",
            "dossier_ref": "dossier/selection.json case-05-usb2-device-states（对照组）",
            "semantics_note": "总线/主机侧事件 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, 6, 7)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "正控对照：填充哑态 filler_6/filler_7 行完全相同（全事件自环 0.0、不引用真实事件语义），"
                     "对换在 fixed 口径下是真对称；检验工具对平凡真对称的放行（rung 1c pads 惯例）。",
            "construction": "order-2 对换：filler_6(6) <-> filler_7(7)",
            "dossier_ref": "dossier/selection.json case-05-usb2-device-states（正控组）",
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
