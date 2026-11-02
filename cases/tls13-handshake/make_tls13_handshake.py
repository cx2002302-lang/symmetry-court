#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_tls13_handshake.py — W2 盲测案卷生成器（案4 tls13-handshake）

生成 model.json 与 groups/*.json；`--check` 逐字节自证。
只写转录文件：不运行 wuxing-gua、不算真值、逐边给 RFC 条号+行号（W2 纪律①②③）。

转录对象：RFC 8446（TLS 1.3）Appendix A 客户端+服务端握手状态机（8+9=17 态，两侧合并为
一个不交并转移系统）。严禁混入 TCP 状态机（W1 风险项/TCP 属 symmetry-court 既有物）。
来源钉定：https://www.rfc-editor.org/rfc/rfc8446.txt（RFC 冻结文本 2018-08，无版本漂移；
本地快照 dossier/sources/rfc8446.txt，W2 本会话对 6671-6768 行逐行复核）。
"""
import json
import os
import sys

CASE_DIR = os.path.dirname(os.path.abspath(__file__))

N_BITS = 5  # 17 真实态 + 15 填充 = 32 = 2^5
C_STATES = ["c_START", "c_WAIT_SH", "c_WAIT_EE", "c_WAIT_CERT_CR", "c_WAIT_CERT",
            "c_WAIT_CV", "c_WAIT_FINISHED", "c_CONNECTED"]
S_STATES = ["s_START", "s_RECVD_CH", "s_NEGOTIATED", "s_WAIT_EOED", "s_WAIT_FLIGHT2",
            "s_WAIT_CERT", "s_WAIT_CV", "s_WAIT_FINISHED", "s_CONNECTED"]
STATES = C_STATES + S_STATES + ["filler_%d" % i for i in range(17, 32)]
C_EVENTS = ["c_send_clienthello", "c_recv_helloretryrequest", "c_recv_serverhello",
            "c_recv_encryptedextensions", "c_recv_certificate", "c_recv_certificaterequest",
            "c_recv_certificateverify", "c_recv_finished"]
S_EVENTS = ["s_recv_clienthello", "s_send_helloretryrequest", "s_select_parameters",
            "s_send_serverhello_flight", "s_recv_endofearlydata", "s_client_auth_branch",
            "s_recv_certificate_nonempty", "s_recv_certificate_empty",
            "s_recv_certificateverify", "s_recv_finished"]
EVENTS = C_EVENTS + S_EVENTS
GOALS = [7, 16]  # 两侧 CONNECTED（吸收；握手后为应用数据阶段，Appendix A 无出边）

cSTART, cSH, cEE, cCCR, cCERT, cCV, cFIN, cCONN = range(8)
sSTART, sRCH, sNEG, sEOED, sFL2, sCERT, sCV, sFIN, sCONN = range(8, 17)

E = {name: i for i, name in enumerate(EVENTS)}

CITES = {}
TABLE = {}

def cell(state, event, targets, cite):
    key = "%s|%s" % (state, event)
    assert key not in TABLE, key
    TABLE[key] = targets
    CITES[key] = cite

SELF0 = (("self", 0.0),)
SELFN1 = (("self", -1.0),)

A1 = "RFC 8446 §A.1 (rfc8446.txt)"
A2 = "RFC 8446 §A.2 (rfc8446.txt)"
CN = "未注册格类规则（统一 -1.0）：Appendix A 图中该 (态,事件) 组合无对应箭头"

# ---- 客户端 8 态（图 6682-6711）----
cell("c_START", "c_send_clienthello", ((cSH, 0.0),), A1 + ":6682-6686 'Send ClientHello' 箭头 START->WAIT_SH")
cell("c_START", "c_recv_helloretryrequest", SELFN1, CN + "（勘误 2026-10-31：原图 6682-6686 角标记法 START<----+ 的回边实自 WAIT_SH 出发，START 无此事件箭头）")
cell("c_WAIT_SH", "c_recv_helloretryrequest", ((cSTART, 0.0),), A1 + ":6682-6686 'Recv HelloRetryRequest' 回边 WAIT_SH-->START（角标 + 于 6686 行 WAIT_SH----+，勘误自 START 自环改此）")
cell("c_WAIT_SH", "c_recv_serverhello", ((cEE, 0.0),), A1 + ":6687-6690 'Recv ServerHello' 箭头 WAIT_SH->WAIT_EE")
cell("c_WAIT_EE", "c_recv_encryptedextensions", (((0.5, cCCR, 0.0)), ((0.5, cFIN, 0.0))),
     A1 + ":6691-6703 'Recv EncryptedExtensions' 后 Using certificate -> WAIT_CERT_CR / Using PSK -> WAIT_FINISHED（分支为握手模式条件→等概率占位, 声明）")
cell("c_WAIT_CERT_CR", "c_recv_certificate", ((cCV, 0.0),), A1 + ":6695-6701 'Recv Certificate' 箭头 WAIT_CERT_CR->WAIT_CV（无 CertReq 情形）; 规范依据 §4.4.2 txt:3535")
cell("c_WAIT_CERT_CR", "c_recv_certificaterequest", ((cCERT, 0.0),), A1 + ":6696-6699 'Recv CertificateRequest' 箭头 WAIT_CERT_CR->WAIT_CERT; 规范依据 §4.3.2 txt:3334")
cell("c_WAIT_CERT", "c_recv_certificate", ((cCV, 0.0),), A1 + ":6698-6701 'Recv Certificate' 箭头 WAIT_CERT->WAIT_CV; §4.4.2 txt:3535")
cell("c_WAIT_CV", "c_recv_certificateverify", ((cFIN, 0.0),), A1 + ":6701-6703 'Recv CertificateVerify' 箭头 WAIT_CV->WAIT_FINISHED; §4.4.3 txt:3823")
cell("c_WAIT_FINISHED", "c_recv_finished", ((cCONN, 1.0),),
     A1 + ":6704-6711 'Recv Finished'（其间 [Send EndOfEarlyData]/[Send Certificate+CV]/Send Finished 为同飞行动作）-> CONNECTED; §4.4.4 txt:3945; 奖励约定：进入 CONNECTED +1.0")
cell("c_CONNECTED", "c_recv_finished", ((cCONN, 0.0),), A1 + ":6711 CONNECTED 为图终点（吸收自环）")
for e in C_EVENTS:
    if ("c_CONNECTED|%s" % e) not in TABLE:
        cell("c_CONNECTED", e, ((cCONN, 0.0),), A1 + ":6711 CONNECTED 吸收（图终点无出边）→ 全事件自环 0.0")

# ---- 服务端 9 态（图 6729-6768）----
cell("s_START", "s_recv_clienthello", ((sRCH, 0.0),), A2 + ":6729-6732 'Recv ClientHello' 箭头 START->RECVD_CH")
cell("s_START", "s_send_helloretryrequest", SELFN1, CN + "（勘误 2026-10-31：回边实自 RECVD_CH 出发）")
cell("s_RECVD_CH", "s_send_helloretryrequest", ((sSTART, 0.0),), A2 + ":6729-6732 'Send HelloRetryRequest' 回边 RECVD_CH-->START（勘误自 START 自环改此）")
cell("s_RECVD_CH", "s_select_parameters", ((sNEG, 0.0),), A2 + ":6733-6735 'Select parameters' 箭头 RECVD_CH->NEGOTIATED")
cell("s_NEGOTIATED", "s_send_serverhello_flight", (((0.5, sEOED, 0.0)), ((0.5, sFL2, 0.0))),
     A2 + ":6736-6752 ServerHello...Finished 一轮飞行后 No 0-RTT -> WAIT_FLIGHT2 / 0-RTT -> WAIT_EOED（分支条件→等概率占位, 声明; §4.2.10 Early Data txt:2893）")
cell("s_WAIT_EOED", "s_recv_endofearlydata", ((sFL2, 0.0),), A2 + ":6747-6752 'Recv EndOfEarlyData' 箭头 WAIT_EOED->WAIT_FLIGHT2; §4.2.10 txt:2893")
cell("s_WAIT_FLIGHT2", "s_client_auth_branch", (((0.5, sCERT, 0.0)), ((0.5, sFIN, 0.0))),
     A2 + ":6754-6764 No auth -> WAIT_FINISHED / Client auth -> WAIT_CERT（服务端配置条件→等概率占位, 声明; §4.3.2 txt:3334）")
cell("s_WAIT_CERT", "s_recv_certificate_nonempty", ((sCV, 0.0),), A2 + ":6758-6761 'Recv Certificate' 箭头 WAIT_CERT->WAIT_CV; §4.4.2 txt:3535")
cell("s_WAIT_CERT", "s_recv_certificate_empty", ((sFIN, 0.0),), A2 + ":6759-6764 'Recv empty Certificate' 箭头 WAIT_CERT->WAIT_FINISHED")
cell("s_WAIT_CV", "s_recv_certificateverify", ((sFIN, 0.0),), A2 + ":6762-6764 'Recv CertificateVerify' 箭头 WAIT_CV->WAIT_FINISHED; §4.4.3 txt:3823")
cell("s_WAIT_FINISHED", "s_recv_finished", ((sCONN, 1.0),), A2 + ":6765-6768 'Recv Finished' 箭头 WAIT_FINISHED->CONNECTED; §4.4.4 txt:3945; 奖励约定 +1.0")
for e in S_EVENTS:
    if ("s_CONNECTED|%s" % e) not in TABLE:
        cell("s_CONNECTED", e, ((sCONN, 0.0),), A2 + ":6768 CONNECTED 吸收（图终点无出边）→ 全事件自环 0.0")

# ---- 其余真实态的未注册格（统一类规则）+ 填充态 ----
for sname in C_STATES + S_STATES:
    for e in EVENTS:
        if ("%s|%s" % (sname, e)) not in TABLE:
            # 对侧事件打到本侧态 = 跨侧无箭头；同侧未画箭头组合同样未注册
            cell(sname, e, SELFN1, CN + "（%s 无 '%s' 出箭头; 对侧事件对本侧态亦无语义）" % (sname, e))
for i in range(17, 32):
    sname = "filler_%d" % i
    for e in EVENTS:
        cell(sname, e, (("self", 0.0),),
             "填充态（2^n_bits 幂次契约，参照工具仓 padding 惯例）：全事件自环 r=0.0，不引用真实事件语义")

NOT_COLLECTED = [
    {"item": "client PSK 分支与 certificate 分支的判别条件（是否持有 PSK/是否收到 CertReq）",
     "why": "握手模式为会话条件，非 (态,事件) 维度；已等概率占位声明（c_WAIT_EE 行）"},
    {"item": "server 0-RTT 有无、client auth 有无的判别条件",
     "why": "同上（s_NEGOTIATED / s_WAIT_FLIGHT2 行）"},
    {"item": "Appendix A 中 [Send EndOfEarlyData]、[Send Certificate [+ CertificateVerify]]、Send Finished、K_* 密钥计算等动作",
     "why": "为同飞行内的动作标注而非独立状态迁移事件（图 6704-6710）；折叠进 Recv Finished 边的引证"},
    {"item": "KeyUpdate / post-handshake 消息 / 会话恢复（PSK binder）后的状态重入",
     "why": "Appendix A 图未画；§2.2/§4.6 为消息机制非相迁移"},
    {"item": "alert/关闭转移（close_notify）",
     "why": "Appendix A 图无关闭相；不虚构状态"},
    {"item": "HelloRetryRequest 后中间态（部分实现有 HELLO_RETRY_REQUEST 中间态）",
     "why": "（勘误 2026-10-31）RFC 图把 HRR 画为 WAIT_SH/RECVD_CH 指回 START 的回边（6682-6686/6729-6732），原转录误作 START 自环，已修"},
    {"item": "TCP 状态机任何元素",
     "why": "W1 风险项红线：TCP 属 symmetry-court 既有物，严禁混入"},
]

SOURCE_CITATION = [
    "RFC 8446 (TLS 1.3), https://www.rfc-editor.org/rfc/rfc8446.txt（2018-08 冻结文本; W1 快照 dossier/sources/rfc8446.txt,",
    " W2 本会话对 Appendix A 6671-6768 行逐行复核）:",
    "  - §A.1 Client 状态机图 txt:6682-6711（8 态: START, WAIT_SH, WAIT_EE, WAIT_CERT_CR, WAIT_CERT, WAIT_CV, WAIT_FINISHED, CONNECTED）",
    "  - §A.2 Server 状态机图 txt:6729-6768（9 态: START, RECVD_CH, NEGOTIATED, WAIT_EOED, WAIT_FLIGHT2, WAIT_CERT, WAIT_CV, WAIT_FINISHED, CONNECTED）",
    "  - §4 规范锚点（transcription_notes 逐边回引）: §4.1.2 ClientHello txt:1485; §4.1.3 HelloRetryRequest txt:1816;",
    "    §4.2.10 Early Data txt:2893; §4.3.2 Certificate Request txt:3334; §4.4.2 Certificate txt:3535;",
    "    §4.4.3 CertificateVerify txt:3823; §4.4.4 Finished txt:3945",
    "  - Appendix A 自述（txt:6673-6676）: 'This appendix provides a summary of the legal state transitions... State names... have no formal meaning'",
    "    —— 本卷以 Appendix A 图为迁移结构一手依据、§4 为关键边规范锚点（W1 风险项口径）",
]

REWARD_RULE = (
    "+1.0 仅两侧 'Recv Finished -> CONNECTED' 两条边（握手完成）；-1.0 为图中无箭头的未注册 (态,事件)；"
    "CONNECTED 吸收自环与填充态 0.0。奖励为转录约定非协议语义（声明）。"
)

TRANSCRIPTION_RULES = (
    "T1 两侧合并为一个不交并转移系统（client 8 态 + server 9 态 = 17 态, n_bits=5）；"
    "T2 条件分支→等概率占位 3 处（c_WAIT_EE 的 PSK/cert 分支、s_NEGOTIATED 的 0-RTT 分支、s_WAIT_FLIGHT2 的 auth 分支）；"
    "T3 server 的 empty/non-empty Certificate 拆为两个事件（图 6759-6764 两条不同目标箭头）；"
    "T4 s_client_auth_branch 为把配置条件事件化（图 6755 'No auth | Client auth' 分支标注）；"
    "T5 对侧事件打到本侧态 = 未注册 -1.0（跨侧无语义）；T6 奖励约定见 reward_rule。"
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
            "source_system": "RFC 8446 (TLS 1.3) Appendix A client+server handshake state machines, transcribed by field-trial W2 from pinned public RFC text",
            "source_citation": SOURCE_CITATION,
            "variant": "event-driven-protocol-fsm",
            "encoding": "17 个真实态（client 8 + server 9, 不交并）+ 15 个填充哑态（32=2^5）；态名前缀 c_/s_ 区分侧；填充态边不引用真实事件语义",
            "state_names": STATES,
            "event_names": EVENTS,
            "semantics_class": "event: 18 个动作是 TLS 握手报文动作（Send/Recv/Select），名字属于协议 -> groups 必须声明 semantics {\"action\": \"fixed\"}",
            "transcription_rules": TRANSCRIPTION_RULES,
            "reward_rule": REWARD_RULE,
            "transcription_notes": {
                "cell_citations": cell_citations(),
                "not_collected": NOT_COLLECTED,
                "unregistered_cell_rule": "图中无箭头的 (态,事件) 统一 -1.0；每格引证注明本态无该出箭头",
            },
            "regenerate": "python -X utf8 make_tls13_handshake.py",
            "generator": "make_tls13_handshake.py（W2 转录工程师；不运行 wuxing-gua、不算真值）",
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
    "g1_claim_waitcert_waitcv_swap_fixed.json",
    "g2_control_crossside_waitcert_swap_fixed.json",
    "g3_pads_swap_fixed.json",
]


def build_groups():
    claim_zh = ("supported_groups 支持集合内的任意 named group（如 x25519 <-> secp256r1 <-> ffdhe2048）在握手状态机层面可互换："
                "server 在客户端支持集合内任选其一，客户端对任一群走同一状态机；换群只换 key_share 载荷，不换状态迁移结构。"
                "（互换维度=同侧内的群参数，非 client/server 两侧互换。）（W1 dossier case-04 symmetric_claim 原文）")
    groups = []
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, cCERT, cCV)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": claim_zh + " 状态级类比（被告主张）：'换载荷不换结构'的最近类比=证书层两个等待子步"
                                "（c_WAIT_CERT / c_WAIT_CV）等价可互换——它们只差下一报文是 Certificate 还是"
                                " CertificateVerify；若合并二者不是协议错误，此对换应保持行为。注意：群参数本身"
                                "不出现在状态里，本置换是该主张可做的最强状态级检验，裁决交工具/基准。",
            "construction": "order-2 对换：c_WAIT_CERT(4) <-> c_WAIT_CV(5)",
            "dossier_ref": "dossier/selection.json case-04-tls13-handshake symmetric_claim",
            "semantics_note": "协议报文事件 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, cCERT, sCERT)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "对照主张：Appendix A 两侧图示形似镜像（两侧都有 WAIT_CERT），"
                     "若主张'同名等待态跨侧等价'则此对换应保持行为；两侧协议角色不同（客户端收证书 vs 服务端验客户端证书），"
                     "判别交工具/基准。",
            "construction": "order-2 对换：c_WAIT_CERT(4) <-> s_WAIT_CERT(13)",
            "dossier_ref": "dossier/selection.json case-04-tls13-handshake（对照组；镜像直觉判别）",
            "semantics_note": "协议报文事件 -> fixed",
        },
    })
    groups.append({
        "n_states": 2 ** N_BITS,
        "elements": [perm_identity(2 ** N_BITS), perm_swap(2 ** N_BITS, 17, 18)],
        "semantics": {"action": "fixed"},
        "meta": {
            "claim": "正控对照：填充哑态 filler_17/filler_18 行完全相同（全事件自环 0.0、不引用真实事件语义），"
                     "对换在 fixed 口径下是真对称；检验工具对平凡真对称的放行（rung 1c pads 惯例）。",
            "construction": "order-2 对换：filler_17(17) <-> filler_18(18)",
            "dossier_ref": "dossier/selection.json case-04-tls13-handshake（正控组）",
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
