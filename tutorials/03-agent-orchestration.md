# Agent Orchestration — Multi-Agent Workflows

![Agent Orchestration](https://v3b.fal.media/files/b/0a9fe87a/Sjz4ITLimunl2Mj2pSDqR_8sKAjUnC.png)

## Overview

Orchestration is what makes the fleet more than the sum of its parts. Individual agents are powerful — but chained together through Senter's dispatch system, they form a self-improving pipeline where each agent's output becomes the next agent's input.

This tutorial covers the orchestration patterns that drive the fleet.

---

## The Orchestration Model

```
                    ┌──────────┐
                    │  Senter  │  ← Entry point. Receives everything.
                    └────┬─────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Chizul  │   │   Crow   │   │  Anser   │
    │ (build)  │   │(research)│   │ (plan)   │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Klerik  │   │  Kashik  │   │  Senter  │
    │ (review) │   │ (record) │   │(dispatch)│
    └────┬─────┘   └──────────┘   └──────────┘
         │
         ▼
    ┌──────────┐
    │  Frieza  │
    │ (deploy) │
    └──────────┘
```

Senter is always the hub. It decides who gets what and in what order.

---

---

![Section](https://v3b.fal.media/files/b/0a9fe954/eEvtYs48bKeLcqmf90_Jm_8E73wpH5.png)

## Pattern 1: Research → Document → Review

The most common pattern. Use it when you need researched, documented, and quality-checked output.

```
Crow (research) → Kashik (document) → Klerik (review) → Published
```

**How to trigger:**

> *"Crow, research WebSocket scaling patterns. Then have Kashik turn the findings into a guide. Klerik should review the guide before it's published."*

**What happens:**
1. Crow searches the web, extracts sources, writes research lore
2. Kashik reads Crow's lore, structures it into a universal guide with steps, pitfalls, examples
3. Klerik reviews the guide — checks accuracy, completeness, clarity — approves or flags fixes
4. Approved guide is published to `~/guides/`

---

## Pattern 2: Build → Review → Deploy

The software delivery pipeline. Chizul implements, Klerik gates quality, Frieza ships.

```
Chizul (build) → Klerik (review) → Chizul (fix) → Klerik (approve) → Frieza (deploy)
```

**How to trigger:**

> *"Chizul, build a health check endpoint for the API. Klerik should review it. If approved, Frieza should deploy it to the staging cluster."*

**What happens:**
1. Chizul implements the endpoint, writes tests, verifies locally
2. Klerik runs linters, security scans, edge case checks
3. If issues found, back to Chizul for fixes. Loop until Klerik approves.
4. Frieza deploys the approved code to staging

---

## Pattern 3: Discord → Plan → Dispatch

Community-driven development. An idea surfaces in Discord, gets planned, and gets built.

```
Discord (user) → Anser (plan) → Senter (dispatch) → Fleet (execute) → Discord (deliver)
```

**How it works:**
1. User asks in Discord: "Can you build a bot that tracks GitHub stars?"
2. Anser catches the question, plans the project, produces a plan document
3. Anser responds in Discord with TL;DR + plan document attached
4. User says "go" → Senter dispatches the plan across the fleet
5. Result delivered back to Discord

---

## Pattern 4: Continuous Observation

Kashik silently watches everything. No one needs to trigger her — she's always running.

```
All agents (output) → Kashik (observe) → Wiki (record) → Klerik (improve agents)
```

**What Kashik tracks:**
- Every session log from every agent
- Every Kanban task creation, completion, and handoff
- Every config change across all profiles
- Every SOUL edit and its outcome

**What this enables:**
- Klerik reads Kashik's `agent-souls.md` to identify behavior issues and prioritize profile fixes
- Nothing is ever forgotten — the full history of every agent is preserved
- New agents can be onboarded with complete context from Kashik's wikis

---

## Pattern 5: Fan-Out Research

One question, multiple angles. Crow researches in parallel, Kashik synthesizes.

```
Crow ──→ angle A ──┐
Crow ──→ angle B ──┼──→ Kashik (synthesize) → Single comprehensive guide
Crow ──→ angle C ──┘
```

**How to trigger:**

> *"Crow, research API gateway patterns from three angles: security, performance, and developer experience. Kashik should combine all three into one guide."*

---

## Pattern 6: Cron-Driven Automation

Scheduled workflows that run without human intervention.

```
Cron (trigger) → Agent (task) → Output (delivered)
```

**Examples:**

| Schedule | Agent | Task |
|----------|-------|------|
| Daily 6am | Crow | Research latest AI papers on arxiv |
| Daily 9am | Kashik | Turn Crow's findings into guides |
| Hourly | Kashik | Scan all session logs, update wikis |
| Every 4h | Sirvir | Check VRAM scaling, adjust models |
| Weekly Sun 2am | Sirvir | Run full benchmark suite |

---

## Orchestration Rules of Thumb

1. **Always enter through Senter.** Don't talk to agents directly for multi-step work.
2. **Let Anser plan first.** For anything multi-agent, get a plan before dispatching.
3. **Klerik gates everything.** No code ships without review. No guide publishes without review.
4. **Kashik documents everything.** You never need to ask her — she's always watching.
5. **Cron for repetition.** Anything that happens more than once should be a cron job.

---

## Next Tutorial

- **[Fleet in Action](04-fleet-in-action.md)** — Real-world examples of the full fleet working together

---

*Part of the SouthpawIN agent fleet tutorials*
