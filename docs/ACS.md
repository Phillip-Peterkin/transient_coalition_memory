# Adaptive Cognitive Substrate (ACS)

**Status:** long-term product vision (stored). Not a shipped package rename.
**Alternate name:** Living Knowledge Substrate (LKS).
**Present research program:** Transient Coalition Memory (TCM) — see
[`NORTH_STAR.md`](NORTH_STAR.md) and
[`TCM_Vision_and_Technical_Report.pdf`](TCM_Vision_and_Technical_Report.pdf).

TCM is the working experimental lineage. ACS is what that lineage is aiming
to become. Do not treat benchmark wins as completion of this vision.

---

## 1. The image, restated as architecture

Electron microscopy of cortex shows no central controller. Dense local wiring
produces global behavior. Memory is not stored in the bulbs; it is stored in
how branches touch.

The same intuition applies to knowledge systems:

| Database instinct | ACS instinct |
|---|---|
| Record / JSON / vector | Living micro-agent |
| Query → retrieve → rank → infer → output | Disturb → activate → recruit → compete → certify → emerge |
| "What is true?" | "Why does this coalition currently believe this is true?" |
| Master memory store | Only interactions |
| Static schema / index | Topology that rewires |

---

## 2. Micro-agents, not cells

Earlier TCM language said "cells." Prefer **micro-agents**.

Each micro-agent knows only a tiny amount. None of them knows "the answer."
The answer is a **coalition**.

A micro-agent can:

- recruit neighbors
- decay
- strengthen
- certify
- contradict
- merge
- split
- die

Each piece of information should carry relational state such as:

- where it came from (provenance)
- who supports it
- who contradicts it
- how often it has been correct
- when it was last reinforced
- what contexts activate it
- how much energy it currently has
- what other facts it tends to co-activate with

Provenance is not metadata bolted on later. It is why a coalition's belief is
inspectable.

---

## 3. Inference as ecosystem disturbance

Most AI memory stacks still do:

```text
Input → Retrieve → Rank → Infer → Output
```

ACS does:

```text
Input
  → Local activation
  → Recruitment
  → Competition
  → Certification
  → Emergent coalition
  → Decision
```

There is no master memory. You disturb the substrate. Certain regions become
active together. The decision is the surviving coalition under certification
pressure — including dormant / reserve mass that was not fully activated.

TCM already implements a sparse version of recruit → certify → reserve →
delayed-learn. ACS keeps that core and refuses to collapse back into denser
retrieval or permanent records.

---

## 4. Memory is the pattern of relationships

The memory is not the individual node.

The memory is the pattern of relationships — support, contradiction,
co-activation, recruitment ease, and certification history.

That is why "better truth-discovery algorithm" undersells the work. Truth
discovery can be one evaluation surface. The product is a substrate where
knowledge lives, competes, cooperates, and reorganizes.

---

## 5. The missing piece: topology adaptation

Brains are not static reconstructions. They rewire.

Belief adaptation without topology adaptation is incomplete. The substrate
itself must change:

- coalitions that repeatedly succeed become easier to recruit
- relationships that never contribute fade
- new pathways form under repeated joint activation
- dead pathways disappear

So the architecture should adapt:

1. **beliefs** (what coalitions currently endorse), and
2. **topology** (which micro-agents can recruit which neighbors, and at what cost).

This is explicitly unfinished in the present TCM/ACI/Mnemosheath lineage.
Learning source reliability, claim anchors, and context bits are necessary
but not sufficient. Graph plasticity is part of the dream.

---

## 6. Naming discipline

| Name | Use for |
|---|---|
| **ACS** (Adaptive Cognitive Substrate) | Long-term product / dream name |
| **LKS** (Living Knowledge Substrate) | Alternate dream name when "ecosystem" framing helps |
| **TCM** | Current research program, frozen Wave XI reference, paper title lineage |
| **ACI / Mnemosheath / …** | Specific experimental mechanisms inside TCM |

Do **not** rename packages, class names, or paper titles casually. Rename only
when mechanism fidelity matches the claim. Until then: TCM implements pieces
of ACS; ACS is not yet shipped.

Class names that still say `Cellular` are historical API. Prefer
"micro-agent" in new vision prose; do not mass-rename code from a vision note
alone.

---

## 7. Fidelity checks specific to ACS

In addition to the rules in [`NORTH_STAR.md`](NORTH_STAR.md) §4:

1. **No master memory.** If a change reintroduces a single authoritative store
   that bypasses coalition certification, it is out of vision.
2. **Coalition answers, not node answers.** Explanations should expose why the
   active coalition believes what it believes (support, contradiction,
   energy, provenance) — not only a ranked document list.
3. **Topology must be allowed to change.** If learning only updates scalar
   beliefs on a fixed graph forever, name that limitation; do not call the
   result ACS-complete.
4. **Disturbance, not exhaustive scan.** Prefer local activation and budgeted
   recruitment over retrieve-everything ranking.
5. **Cure before rebrand.** ACS naming does not excuse skipping the real-data
   weakness ledger (self-sealing attractor, biased recruitment, static
   exchange rate, regime specialization).

When in doubt: preserve the ecosystem, name the tradeoff, do not paper over
persistence as intelligence.
