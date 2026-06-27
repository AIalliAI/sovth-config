# Getting Started with the SouthpawIN Agent Fleet

![Getting Started](https://v3b.fal.media/files/b/0a9fe879/EBv6TtM3QTr7hL6l-lz7o_z1SKkut2.png)

## Overview

The SouthpawIN agent fleet is a coordinated team of Hermes agent profiles, each specialized for a different job. Together they form a self-improving ecosystem — agents create, review, document, and refine each other's work.

This tutorial walks you through setting up the entire fleet and understanding how the pieces fit together.

---

## The Fleet at a Glance

| Agent | Role | Installs With |
|-------|------|--------------|
| **Senter** | Triage orchestrator — routes requests, decomposes tasks | `hermes profile install https://github.com/SouthpawIN/senter` |
| **Chizul** | Builder — implements code, configs, file changes | `hermes profile install https://github.com/SouthpawIN/chizul` |
| **Klerik** | QA reviewer — enforces standards, catches issues | `hermes profile install https://github.com/SouthpawIN/klerik` |
| **Anser** | Community support + project planner | `hermes profile install https://github.com/SouthpawIN/anser` |
| **Kashik** | Silent historian — maintains fleet continuity | `hermes profile install https://github.com/SouthpawIN/kashik` |
| **Crow** | Deep researcher — investigates topics | `hermes profile install https://github.com/SouthpawIN/crow` |
| **Frieza** | Infrastructure — deploys, provisions, monitors | `hermes profile install https://github.com/SouthpawIN/frieza` |
| **Nous Girl** | Brainstormer — creative ideation | *(bundled with fleet)* |
| **Sirvir** | Turbofit wizard — model selection & benchmarking | `hermes profile install https://github.com/SouthpawIN/sirvir` |

---

## Step 1: Install the Fleet

```bash
# Install all core agents (one-liner)
for agent in senter chizul klerik anser kashik crow frieza sirvir; do
    hermes profile install "https://github.com/SouthpawIN/$agent"
done

# Verify
hermes profile list
```

Each agent installs as a self-contained profile with its own skills, config, and memory.

---

## Step 2: Understand the Flow

The fleet operates in a chain:

```
Idea/Request → Senter (triage) → Specialist Agent → Klerik (review) → Done
                                      ↓
                                 Kashik (documents everything)
```

**Senter** is the entry point. Give Senter anything — a bug report, a feature idea, a research question — and it routes to the right agent.

**Anser** handles Discord and also does project planning — give Anser a rough concept and it produces a structured plan document for Senter to dispatch.

**Kashik** silently watches everything and maintains the institutional memory — nothing is forgotten.

---

## Step 3: Run Your First Orchestration

```bash
# Start with Senter
hermes chat --profile senter
```

Then say something like:

> *"Crow, research the best Python libraries for audio processing. Then have Kashik turn the findings into a guide. Klerik should review the guide before it ships."*

Senter will:
1. Dispatch Crow to research
2. Route findings to Kashik for guide writing
3. Send the guide to Klerik for review
4. Report back when everything is done

---

## Step 4: Set Up Project Planning

```bash
# Start with Anser for planning
hermes chat --profile anser
```

Say:

> *"I want to build a Discord bot that monitors channels for bug reports, extracts them, creates GitHub issues, and notifies the team. Plan this out for me."*

Anser will audit available Hermes tools and agents, then produce a plan document with phases, task assignments, dependencies, and tool requirements — ready to hand to Senter for dispatch.

---

## Next Steps

- **[Project Planning](02-project-planning.md)** — Deep dive into planning with Anser
- **[Agent Orchestration](03-agent-orchestration.md)** — Multi-agent workflows and handoffs
- **[Fleet in Action](04-fleet-in-action.md)** — Real-world examples of the fleet working together

---

*Part of the SouthpawIN agent fleet tutorials*
