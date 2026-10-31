# 对称法庭 Symmetry Court

[![CI: court selftest](https://img.shields.io/badge/court-selftest_pass-brightgreen)](https://github.com/cx2002302-lang/symmetry-court#quick-start) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Engine: wuxing-gua@e1b1fa8](https://img.shields.io/badge/engine-wuxing--gua%40e1b1fa8-grey)](NOTICE)

**给状态机的对称性主张开庭。** 一条主张、三位裁判、两套写明的口径、一份人人可复跑的判决书。—— English: [README.md](README.md)

---

## 认识这对双胞胎

翻开 TCP 标准——RFC 9293 §3.3.2 Figure 5——看关闭过程的两大分支。靠近末尾有两个状态，`CLOSING` 和 `FIN-WAIT-2`，画出来几乎是一对双胞胎：各自一条进门、一条出门，两条出门都通向同一个下一站；而且把其中一条出门送出去的事件，恰好是把另一条送进门的事件。把图上的事件标签擦掉，交换这两个状态，整张图严丝合缝地叠回自己身上。

但把标签读回来。`FIN-WAIT-2` 的出门事件是 **对方挂断了电话**（`rcv FIN`）；`CLOSING` 的出门事件是 **对方确认了我们的挂断请求**（`rcv ACK of FIN`）。这是两条不同关闭路径上的两个不同时刻——内部状态怎么改名，都变不成同一个事件。

转折来了。我们拿这对状态的交换去问一个对称性判据引擎："这次交换保不保行为？"它答 **pass**。我们又拿同一个问题去问一个独立的图计算库——这次把事件标签按住不许动——它答 **不行，恒等是唯一的对称**。两个答案都对。因为它们答的是 **两个不同的问题**："事件名可以跟着状态一起改名吗"和"事件名必须钉在原地吗"。引擎的默认口径默认前者，规范文本要求后者——而在问题被写下来之前，工具和陪审团谁也没说自己答的是哪一问。

**这就是这个仓库存在的理由。** 对称法庭把一条关于状态机的对称性主张，交给三位裁判，在 **两套写明名字的口径** 下各跑一遍，每一列都落进判决书文件，然后明说三方一致还是分歧。裁判意见不合时——双胞胎案正是不合——分歧本身就是发现，公开记录，不做和稀泥处理。

旗舰案例的完整叙事在 [docs/twin-trial.md](docs/twin-trial.md)。

## 三方仲裁是什么

对每一案里的每条对称性主张（一个"被告群"），法庭跑三列：

| 列 | 谁 | 答什么 |
|---|---|---|
| `wuxing-gua@relabel` | 内嵌判据引擎，relabel 口径 | **事件名可以跟着状态一起改名**时，交换是否成立 |
| `wuxing-gua@fixed` | 同一引擎，fixed 口径（`--strict`） | **事件名必须钉在原地**时，交换是否成立 |
| `networkx@labeled` | 独立陪审团（networkx），标签固定 | 同一个图问题，由另一套独立代码算 |

另有一列透明备查：陪审团的"只看结构"答案（标签擦掉版），记录在案卷的 expected / verdict 文件里。

三位裁判刻意互相独立：引擎是字节级原样内嵌的零依赖包，陪审团是另一套基于 networkx 的独立实现。任何一边有 bug，都藏不住——只会表现为列间分歧。每份判决都带一句明确的 agree/disagree 判语；`selftest` 把每份判决逐字段对 expected 记录重放，判决书偏离回执时不可能静默过关。

要点不是某一列"赢"，而是每一列 **默认的口径都被写明了**——双胞胎案暴露的缺口，缺的正是这个。

## 五分钟快速上手

```bash
git clone https://github.com/cx2002302-lang/symmetry-court.git
cd symmetry-court

# 唯一要装的：陪审团的依赖（引擎本身零依赖）
python -X utf8 -m pip install networkx

python -X utf8 -m symmetry_court list        # 看案卷
python -X utf8 -m symmetry_court arbitrate   # 开庭——每案出一张判决表
python -X utf8 -m symmetry_court selftest    # 全案重放对 expected（退出码 0 = 全绿）
```

（`python -X utf8` 是本项目在 Windows 上的固定写法；其他平台上 `python3 -X utf8` 行为一致。）

arbitrate 会在控制台打印判决表，并把完整庭审记录写进 `verdicts/<case>.verdict.json`。selftest 是门禁：退出码 `0` 表示仓里每份判决仍与 expected 记录逐字段一致。

### 怎么读判决

每个被告群、每种口径一行：

- **exit code** —— 引擎约定：`0` 放行，`1` 拒答，`2` 样本不足（仅采样模式；本法庭用不到），`3` 输入或内部错误；
- **verdict** —— 在该列写明口径下的 pass / reject；
- **`worst_tv`** —— 本次检验量到的最大失配（改名前后行为的总变差）；
- **`judge`** —— 引擎实际用的是哪套内部判据，便于追溯；
- **agree/disagree** —— 法庭对"三列对这名被告说的是不是同一个故事"的一句话判语。

**pass 永远只表示**：*在写明的那套口径下，结构上可以互换*。它不等于"可以放心压缩"。口径要你自己挑，挑法见下一节。

## 案卷

案卷现有 3 宗案件（回执：对 `cases/` 目录跑 `python -X utf8 -m symmetry_court list`）。下表每个数字都有仓内指名的回执文件背书——没有一个数来自记忆。

| 案件 | 协议 | 出处 | 状态数 | 孪生对 | relabel | fixed | networkx（带标签） |
|---|---|---|---|---|---|---|---|
| `tcp` | TCP 连接状态机 | RFC 9293 §3.3.2 Figure 5 | 16 状态、20 条转移、12 种事件 | CLOSING ↔ FIN-WAIT-2 | pass（exit 0，worst_tv 0.0） | reject（exit 1，worst_tv 1.0） | 非对称——仅恒等（只看结构：是） |
| `dhcp` | DHCP 客户端状态机 | RFC 2131 §4.4 Figure 5 | 16 状态（8 协议态 + 8 补位）、18 条转移、15 种事件 | RENEWING ↔ REBINDING（转录裁定：不可互换） | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |
| `imap` | IMAP4rev1 连接状态机 | RFC 3501 §3 + §6（正文规范，无 drawn 图） | 8 状态（4 协议态 + 4 补位）、11 条转移、6 种事件 | AUTHENTICATED ↔ SELECTED（SELECT/CLOSE 双向环） | reject（exit 1，worst_tv 1.0） | reject（exit 1，worst_tv 1.0） | 非对称（结构与带标签口径皆非） |

`tcp` 行的注：状态数含 5 个补位哑态（引擎位串约定所需，16 态中 11 个为协议态）；案卷里其余两名被告——一个无聊换位、一个荒谬换位——在两套口径下都被拒（`cases/tcp/expected.json` 中 4/4 行 reject），这是"判官不是橡皮图章"在记录里的样子。底本转录里的一条边在逐边复核后被删除（`SYN-SENT` 上的 `CLOSE`：Figure 5 没有画这条箭头，且 §3.10.4 写明"删除 TCB"）；更正记录在模型元数据的转录注记里。`dhcp` 行的判决是数据说了算，不是感觉：两个续租状态共用同一完成标签 `DHCPACK/Record lease`，但连 relabel 口径都拒绝这次换位——因为 `REBINDING` 没有回到 `RENEWING` 的边。`imap` 行转录自 RFC 3501 的正文（其 §3 无图）；每条边都引用写明它的原句。TCP 没有回报概念，该案奖励层按设计全零，全部结论来自转移层（`dhcp`、`imap` 同）。

## 『两种一样』——三问自判

整份案卷压在一个区分上：当判据说"这次改名保行为"，它对你的 **动作（事件）名** 已经做了假设。

1. **你的系统里，动作到底是什么？** 从外部到来的事件（包、消息、超时——名字写在对方也能引用的规范里）：**fixed** 地界。绑在状态坐标上的指令（"翻开关 a"）：**relabel** 地界。
2. **状态改名后，动作名必须跟着改吗？** 改名后若日志、规范、线上含义要继续诚实，动作名必须跟着状态一起重写：**relabel**。若动作名指的是任何内部改名都碰不到的外部事实：**fixed**。
3. **悄悄重写事件名会弄坏什么公开的东西吗？** 若一次把 `rcv FIN` 悄悄写成 `rcv ACK of FIN` 的压缩会让你的规范撒谎：**fixed**。

拿不准就两套都跑（法庭向来如此），把分歧当发现读。长版指引——含两个能手算复核的最小例子——在 [docs/which-identical.md](docs/which-identical.md)。

## 边界诚实

- **discover 守卫事件类系统。** 引擎的找群器（`discover`）是在 relabel 家族判据下提候选群的——它为坐标绑定制系统而造。在事件驱动状态机上，discover 的提案只当线索、不当结论：任何压缩之前，先按 fixed 口径重审一遍。法庭的 check 列做的正是这次重审。
- **平凡群是协议自己的性质。** 若只找到恒等这一个对称，不是判据失职：它说明协议自己的事件结构已经把每个状态钉死了。带着事件标签读的 TCP 恰好就是这种系统——值得知道，不是缺陷。
- **标准里的图常常只是示意。** TCP Figure 5 省略了"任意状态收到 RST"的转移（图注 Note 3 自己写明）；这些边 **不收录**，缺失记录在案卷元数据里，而不是靠编造补齐。
- **pass ≠ 业务放行。** 每份判决书里的每个 pass，都只在对应该列写明的那套口径下成立。双胞胎在 relabel 列的 pass 是真的——而恰恰是那套口径下合并它们，机器就不再是 TCP。

## 参与贡献

新增案例是这里的主贡献方式：选一部公开标准，逐边转录、逐边注出处，起草被告群（含一名你预期败诉的），开庭，落 expected 记录，用确定性生成器封卷。六步流程与守则见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 致谢与来源

- **wuxing_gua 判据引擎** —— 字节级原样内嵌、零修改；钉死的源码版本与来源记录在 [NOTICE](NOTICE)。引擎为同作者自有代码，自带 MIT 许可；零依赖（纯标准库）。
- **networkx** —— 独立陪审团，仅用于仲裁臂（BSD 许可；引擎不依赖它）。
- **RFC 9293**（传输控制协议）—— `tcp` 案出处，转录自 §3.3.2 Figure 5。
- **RFC 2131**（动态主机配置协议）—— `dhcp` 案出处，转录自 §4.4 Figure 5。
- **RFC 3501**（互联网消息访问协议 IMAP4rev1）—— `imap` 案出处，转录自 §3（状态）与 §6（分状态命令）。

定位口径，明说：在我们检索过的范围内，没有见到这个组合的对标——公开标准的状态机、在两套写明名字的等变口径下受审、配独立陪审团与可复跑判决书。若你知道对标在哪里，我们真心想听：开个 issue。

## 许可

MIT——见 [LICENSE](LICENSE)。内嵌引擎保留其自身 MIT 许可条款，记录在 [NOTICE](NOTICE)。
