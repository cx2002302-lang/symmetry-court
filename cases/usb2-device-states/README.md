# 案5 usb2-device-states — W2 转录案卷 README

- 波次/角色：field-trial W2。未运行 wuxing-gua、未算真值、逐边给 spec 条号+图证（W2 纪律①②③）。
- 上游：`dossier/selection.json` case-05-usb2-device-states（W1 选案与对称主张）。

## 转录对象

USB 2.0 规范 **Chapter 9 §9.1 设备可见状态机**（Figure 9-1 / Table 9-1：Attached, Powered, Default, Address, Configured, Suspended 六态）。

来源钉定（W1 风险项"Figure 9-1 为图，三方互证"的落实）：

| 来源 | 核验方式（本会话实跑） |
|---|---|
| usb.org 官方包 usb_20_20250603.zip → usb_20_20240927/usb_20.pdf | W1 快照 `dossier/sources/usb20/`（zip+全文 txt） |
| Figure 9-1（doc p.240 = PDF p.268） | W2 本会话 `pdftotext -layout` 重抽 + **PyMuPDF 渲染 PNG 三次放大目视核验每条弧线方向与箭头落点**（Attached→Powered "Hub Configured"、Powered→Attached "Hub Reset or Deconfigured"、Powered→Default "Reset"、Default→Address "Address Assigned"、Address↔Configured "Device Configured/Deconfigured"、四对 "Bus Inactive/Bus Activity"、左侧 "Power Interruption" 弧与 Reset 大圆弧交叉处判读存疑） |
| Table 9-1（doc p.240-241） | 快照全文 + layout 重抽：6 态 Yes/No/-- 矩阵逐行核验 |
| §9.1.1.1-9.1.1.6 正文（doc p.241-242） | 快照全文定位每条边的正文触发句（VBUS applied / reset / unique address / SetConfiguration() non-zero / bus inactivity / bus activity） |

## 模型规模（落盘实值，见 model.json）

- 状态：6 真实态 + 2 填充哑态（8 = 2^3，n_bits=3）。
- 事件：8（hub_configured / hub_reset_or_deconfigured / reset / address_assigned / device_configured / device_deconfigured / bus_inactive / bus_activity），与 W1 建议核心口径 8 一致；图内标签逐条映射。
- 事件表：8×8 = 64 格全部逐格引证（图弧+正文句）；结果分支 67（bus_activity 四目标占位 +3），跨态分支 14。
- 被告群：3 个（主张群 1 + 端点对照群 1 + 填充正控群 1）。

## 转录口径（完整版在 meta.transcription_rules）

1. **U1 图文互证**：每条边给 Figure 9-1 弧线标签 + §9.1.1.x 正文句（W1 风险项"三方互证"）。
2. **U2 Suspended 回弧**：图中四条 "Bus Activity" 弧按来源态配对；单 Suspended 态编码下四目标等概率占位（声明）。
3. **U3** suspend 入边按图 4 条（Powered/Default/Address/Configured 各一）。
4. **U4 Power Interruption 弧不收**：栅格化图中该弧起点与 Reset 大圆弧交叉，起点态（Default/Address/Configured 候选）无法单值判读；§9.1.1.2 有规范语义（power source change → return to the Powered state）但未逐态指明——按宁缺毋滥记未收录（这是本案最重要的未收录决策）。
5. **U5** 奖励：仅 Address→Configured +1.0（Table 9-1 Configured 行 "The host may now use the function provided by the device"）。

## 未收录清单（7 项，全文在 not_collected）

attach/detach（态外目标）、Power Interruption 回弧（图判读歧义）、Hub Reset 弧是否多源（图中仅画自 Powered）、selective suspend 触发词（与 bus_inactive 同目标边，折叠声明）、电气层 chirp 细节（W1 风险项）、remote wakeup（可选能力）。

W1 边估计 9-12；本转录跨态分支 14（四对 suspend/resume 弧按图全收）——多出部分即 U2/U3 口径，已声明。

## 被告群（groups/）

| 文件 | 置换 | 主张摘要 |
|---|---|---|
| g1_claim_default_address_swap_fixed.json | swap Default↔Address | W1 枚举等价主张的状态级类比：地址只是载荷、两个枚举中间态等价 |
| g2_control_attached_configured_swap_fixed.json | swap Attached↔Configured | 对照：枚举路径两端点等价主张（结构差异最大） |
| g3_pads_swap_fixed.json | swap filler_6↔filler_7 | 正控：填充对换是真对称 |

## 自证记录（本会话实跑）

- `python -X utf8 -I make_usb2_device_states.py` → 生成 model.json(18,626B) + 3 群文件。
- `python -X utf8 -I make_usb2_device_states.py --check` → 4 文件全 OK，exit 0。
- 自写结构校验（非工具）：trans 8×8、64 格全引证、概率和=1、群置换合法、跨态分支 14。

--check 覆盖 model.json 与 groups/*.json；README 手工文档不在字节自证范围（声明）。
