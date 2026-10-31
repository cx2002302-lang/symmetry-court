# Which "identical" do you mean?

A self-judgment guide for the two symmetry standards used in Symmetry Court.

**Who this is for.** You ran the court (or any equivariance judge) on your own
state machine, two columns disagreed, and now you want to know which column
describes *your* system — without reading a line of the judge's code.

**The whole issue in one sentence.** When a judge says "this renaming preserves
the system's behaviour", it has silently assumed something about your *action
names* — and there are two common assumptions, which give opposite answers on
the same machine.

---

## 1. The two definitions

Both definitions ask the same thing: does the state renaming `π` preserve the
transition table? They differ only in what happens to the action (event) name.

**fixed** — the action name must survive unchanged:

```text
π( T(s, a) )  =  T( π(s), a )          for every state s and action a
```

**relabel** — the action may be renamed along with the states (an action `b`
must exist at the renamed state; it does not have to be `a`):

```text
π( T(s, a) )  =  T( π(s), b )          for some action b, per (s, a)
```

Under `relabel`, a swap of two states is allowed to also swap the meanings of
events. Under `fixed`, events are nailed to the world outside the machine and
cannot be renamed at all.

Neither is "the strict one" and "the loose one" in any moral sense. They answer
different questions, and each is correct for one large class of systems — and
wrong for the other.

---

## 2. The three questions

Ask them in order; the standard falls out.

**Q1 — What *is* an action in your system?**

- An **event that arrives from outside** — a packet, a message, a timeout, a
  signal — something your specification or interop document names and another
  party could send: you are in **fixed** territory. TCP's `rcv FIN` is the
  canonical example: the peer decides when it arrives, and no renaming of TCP's
  internal states changes what a FIN is.
- An **instruction indexed by a state coordinate** — "flip switch a", "advance
  milestone a", "toggle bit a", where the action's identity is bound to a
  position inside the state: you are in **relabel** territory. If you rename
  the switches, the instruction manual must be renamed with them, or every
  button label points at the wrong device.

**Q2 — If the states were renamed, must the action labels follow?**

Imagine a compression tool renames your states. Then look at your logs, your
spec text, your on-the-wire meanings:

- If the action labels **must be rewritten too** for all of that text to stay
  honest — the labels were coordinates, and coordinates travel with the map:
  **relabel**.
- If the action labels **must stay put** (they name external facts that no
  internal renaming can touch): **fixed**.

**Q3 — Would silent event-name rewriting corrupt anything published?**

If a compression that quietly rewrites "rcv FIN" into "rcv ACK of FIN" would
make your specification, your protocol analyzer, or your interop tests lie —
**fixed**. If your "actions" appear in no external contract (they are internal
knobs of a simulation, a game, a scheduling model), **relabel** is not merely
tolerable; it is the semantically correct reading.

---

## 3. Worked example A — two switches (relabel is the right standard)

A machine with two independent switches. A state is a pair `(A, B)` of bits;
actions are `flipA` and `flipB`; `T((A,B), flipA) = (¬A, B)`.

Claim: swapping switch A and switch B is a symmetry of this system. Everyone
agrees — the switches are interchangeable hardware.

Take the state `s = (0,0)` and the action `flipA`:

| step | value |
|---|---|
| `T(s, flipA)` — switch A goes on | `(1,0)` |
| `π(T(s, flipA))` — swap the names A/B in the result | `(0,1)` |
| `π(s)` — swap names at the start | `(0,0)` (symmetric start) |
| `T(π(s), flipA)` — flip the switch now called "A" | `(1,0)` |

**fixed** demands `(0,1) = (1,0)` — false. The fixed standard *rejects* a swap
that any engineer knows is harmless. Why? Because after renaming the hardware,
the instruction "flip A" still points at the old unit's position. The standard
is not wrong — it was fed a lie: in a renamed world, "flip A" means flip the
*other* switch.

**relabel** instead asks: at `π(s) = (0,0)`, is there an action whose result is
`(0,1)`? Yes — `flipB`. The action name was renamed along with the states,
which is exactly what a rewritten instruction manual does. Verdict: symmetry
confirmed, and this time it matches the engineer's intuition.

**Moral:** for coordinate-bound actions, the relabel standard is the correct
one, and the fixed standard produces false rejections.

*(This example is hand-worked from the definition above — two switches are
small enough to check by eye, no tool needed. The same conflict, found on a
real judge with real case models, is what forced the two standards to be made
explicit.)*

---

## 4. Worked example B — the TCP twins (fixed is the right standard)

The flagship case of this repository (see `twin-trial.md`): TCP's `CLOSING`
and `FIN-WAIT-2` states, transcribed from RFC 9293 §3.3.2 Figure 5. Each twin
has one entrance and one exit, and both exits lead to the same next state —
and the crossing is perfect:

```text
FIN-WAIT-1 --rcv ACK of FIN--> FIN-WAIT-2 --rcv FIN-->          TIME-WAIT
FIN-WAIT-1 --rcv FIN---------> CLOSING    --rcv ACK of FIN-->   TIME-WAIT
```

What sends FIN-WAIT-2 out is exactly what brought CLOSING in, and vice versa.
On a wire diagram with the event labels erased, the twins are
interchangeable; a structure-only check says so.

But look at what the swap has to assume under **relabel**: the event `rcv FIN`
("the peer hung up on us") and the event `rcv ACK of FIN` ("the peer confirmed
our hang-up request") get exchanged with the states. In real TCP these are two
different things that happen at two different moments of two different closing
paths. A compression that merges them merges "the other side hung up" with
"the other side confirmed our hang-up" — the protocol stops being TCP.

**fixed** refuses the swap, because it demands `rcv FIN` stay `rcv FIN` — and
then the diamond does not close. Verdict: not a symmetry. This matches what
the standard's own text distinguishes.

**Moral:** for event-driven protocol machines, the fixed standard is the
correct one, and the relabel standard produces false acceptances.

---

## 5. Which standard, which system

| your system | actions are… | standard |
|---|---|---|
| protocol / interop state machine (TCP, DHCP, SMTP, TLS…) | external events, named in a public spec | **fixed** |
| switch board / milestone bits / puzzle coordinates | instructions bound to a state position | **relabel** |
| simulation with internal knobs | internal controls, no external contract | **relabel** |
| anything with both kinds mixed | — | run **both**; read the disagreement as a finding |

That last row is the honest one. Mixed systems exist, and for them no single
standard is "the answer" — the disagreement between the two columns is the
diagnostic.

---

## 6. How Symmetry Court applies this

- Every defendant group in `cases/<name>/groups/` carries a **semantics
  declaration** — for event-driven machines, `fixed`. You declare; nothing is
  guessed.
- The trial runs the engine **twice** per group — once under the relabel
  standard, once under fixed — plus an independent **networkx jury** that
  answers the graph question both structure-only and with event labels. Three
  columns land in `verdicts/<case>.verdict.json`
  (`wuxing-gua@relabel`, `wuxing-gua@fixed`, `networkx@labeled`) with an
  explicit agree/disagree line.
- The engine, consulted on its own outside the court, will pick a judge from
  the model's shape when nothing is declared (a bit-string judge for
  action-count ≤ state-bits models, a generalized judge otherwise), or honor
  its `--strict` flag (fixed) or a group-file declaration. All of that is
  upstream wuxing-gua behavior; the court's contribution is that **you never
  consume a verdict whose standard stayed implicit**.

## 7. Small print

- A "pass" always means: *structurally interchangeable under the named
  standard*. It is not a blessing to compress. You still have to pick the
  standard on purpose, with Q1–Q3.
- If the only symmetry a judge finds is the identity, that is not the judge
  failing. An automorphism group of size one says the system's own event
  structure already pins every state — a property of the protocol, worth
  knowing, not a defect to fix.
