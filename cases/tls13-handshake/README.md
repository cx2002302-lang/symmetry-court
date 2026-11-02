# 案4 tls13-handshake — W2 转录案卷 README

- 波次/角色：field-trial W2。未运行 wuxing-gua、未算真值、逐边给 RFC 条号+txt 行号（W2 纪律①②③）。
- 上游：`dossier/selection.json` case-04-tls13-handshake（W1 选案与对称主张）。
- 红线遵守：**未混入任何 TCP 状态机元素**（W1 风险项；TCP 属 symmetry-court 既有物，已在 not_collected 显式声明）。

## 转录对象

RFC 8446（TLS 1.3）**Appendix A 客户端+服务端握手状态机**（client 8 态 + server 9 态 = 17 态，两侧合并为不交并转移系统）。

来源钉定：

| 来源 | 核验方式（本会话实跑） |
|---|---|
| RFC 8446 txt（2018-08 冻结文本，无版本漂移） | W1 快照 `dossier/sources/rfc8446.txt`；W2 本会话对 Appendix A（txt:6671-6768）逐行复核：§A.1 客户端图 6682-6711（8 态），§A.2 服务端图 6729-6768（9 态），与 W1 states_estimate=17 一致 |
| §4 规范锚点 | §4.1.2 ClientHello txt:1485、§4.1.3 HRR txt:1816、§4.2.10 Early Data txt:2893、§4.3.2 CertificateRequest txt:3334、§4.4.2 Certificate txt:3535、§4.4.3 CertificateVerify txt:3823、§4.4.4 Finished txt:3945（关键边在 cell_citations 中回引） |

Appendix A 自述"state names have no formal meaning、为 legal state transitions 之摘要"（txt:6673-6676）——本卷以 Appendix A 图为迁移结构一手依据、§4 为关键边规范锚点（W1 风险项口径）。

## 模型规模（落盘实值，见 model.json）

- 状态：17 真实态（c_/s_ 前缀分侧）+ 15 填充哑态（32 = 2^5，n_bits=5）。
- 事件：18（客户端 8 + 服务端 10；W1 估计 8-9/侧，服务端因 **empty/non-empty Certificate 拆分**（图 6759-6764 两条不同目标箭头）与 **auth 分支事件化**（图 6755）为 10——拆分口径已在 transcription_rules T3/T4 声明）。
- 事件表：32×18 = 576 格全部逐格引证；结果分支 579，跨态分支 20（client 9 + server 11，与图逐条对应）。
- 被告群：3 个（主张群 1 + 跨侧镜像对照群 1 + 填充正控群 1）。

## 转录口径（完整版在 meta.transcription_rules）

1. **T1 不交并合并**：两侧独立状态机合并为一个转移系统，事件空间取并（18）。
2. **T2 条件分支等概率占位**（3 处）：c_WAIT_EE 的 PSK/certificate 分支（图 6692-6703）、s_NEGOTIATED 的 0-RTT 分支（图 6743-6752）、s_WAIT_FLIGHT2 的 client-auth 分支（图 6754-6764）。W1 风险项"条件边拆分/合并口径须声明"由此落点。
3. **T3** server Recv Certificate 按 empty/non-empty 拆两事件（图中两条不同目标箭头）。
4. **T4** s_client_auth_branch：把配置条件事件化（图中分支标注 "No auth | Client auth"）。
5. **T5** 对侧事件打到本侧态 = 未注册 -1.0（跨侧无语义）。
6. **T6** 奖励：两侧 Recv Finished→CONNECTED 各 +1.0（声明性约定）。

## 未收录清单（7 项，全文在 not_collected）

PSK/cert 与 0-RTT/auth 的判别条件、飞行内动作标注（[Send EndOfEarlyData] 等）、KeyUpdate/会话恢复重入、alert/关闭转移、HRR 中间态（按图画为 START 自环）、**TCP 任何元素（红线）**。

## 被告群（groups/）

| 文件 | 置换 | 主张摘要 |
|---|---|---|
| g1_claim_waitcert_waitcv_swap_fixed.json | swap c_WAIT_CERT↔c_WAIT_CV | W1"换群只换载荷不换结构"的状态级类比：证书层两等待子步等价（群参数不出现在状态里，此为该主张可做的最强状态级检验——已在 meta.claim 声明） |
| g2_control_crossside_waitcert_swap_fixed.json | swap c_WAIT_CERT↔s_WAIT_CERT | 对照：同名态跨侧镜像等价直觉 |
| g3_pads_swap_fixed.json | swap filler_17↔filler_18 | 正控：填充对换是真对称 |

## 自证记录（本会话实跑）

- `python -X utf8 -I make_tls13_handshake.py` → 生成 model.json(148,994B) + 3 群文件。
- `python -X utf8 -I make_tls13_handshake.py --check` → 4 文件全 OK，exit 0。
- 自写结构校验（非工具）：trans 32×18、576 格全引证、概率和=1、群置换合法、跨态分支 20。

--check 覆盖 model.json 与 groups/*.json；README 手工文档不在字节自证范围（声明）。
