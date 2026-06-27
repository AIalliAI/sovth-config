# Fleet in Action — Real-World Workflows

![Fleet in Action](https://v3b.fal.media/files/b/0a9fe883/LcLSgCmxJlCSw2Ls-PcBc_JpjZxNTE.png)

## Overview

Theory is useful; examples are better. This tutorial walks through real-world scenarios where the full fleet works together — from idea to deployed result — showing exactly which agents are involved and how they hand off.

---

## Scenario 1: Building a CI Monitoring Bot

**Goal:** A Discord bot that watches CI pipelines and posts daily summaries.

### Phase 1: Planning

**User → Anser (Discord):**

> *"I want a bot that monitors our GitHub Actions pipelines and posts a daily status report to Discord. Plan this out."*

**Anser's plan document:**

| Phase | Agent | Task | Tools |
|-------|-------|------|-------|
| 1. Research | Crow | Research GitHub Actions API, Discord webhook patterns | web_search, web_extract |
| 2. Design | Anser | Structure bot architecture, define message format | file |
| 3. Build | Chizul | Implement bot — GitHub API polling, Discord message formatting | terminal, file |
| 4. Review | Klerik | Security review, edge case testing, linting | terminal |
| 5. Deploy | Frieza | Deploy as cron job, provision any needed infra | terminal, cronjob |
| 6. Document | Kashik | Record architecture, decisions, and lessons | session_search, file |

### Phase 2: Dispatch

**User → Senter:**

> *"Dispatch the CI monitoring bot plan."*

Senter creates Kanban tasks for each phase, assigns them, and tracks progress.

### Phase 3: Execution

1. **Crow** researches for ~5 minutes, returns: "GitHub Actions API at `api.github.com/repos/:owner/:repo/actions/runs`, Discord webhooks accept JSON with `embeds` array, rate limits are 5000/hr for GitHub, 30/min for Discord."

2. **Chizul** implements: writes a Python script that polls GitHub, formats a Discord embed, posts via webhook. Tests locally.

3. **Klerik** reviews: checks for token exposure, verifies rate limit handling, confirms error recovery. Flags one issue — webhook URL in plaintext. Chizul fixes with env var.

4. **Frieza** deploys: creates a cron job (`0 9 * * *`) running the script, provisions a small VM if needed.

5. **Kashik** documents: records the architecture decision (Python over Node because of `requests` library simplicity), logs the review findings, updates the system wiki.

---

## Scenario 2: Weekly AI Research Pipeline

**Goal:** Every Sunday, research new AI papers, turn the best into guides, and publish reviewed content.

### The Setup

**User → Senter:**

> *"Set up a weekly pipeline: Crow researches new AI papers every Sunday at 6am, Kashik turns the best into guides at 9am, Klerik reviews at noon. Approved guides get published."*

**Senter creates three cron jobs:**

```yaml
# Job 1: Crow research
schedule: "0 6 * * 0"  # Sunday 6am
agent: crow
task: "Search arxiv for the top 5 AI papers from the past week. For each: extract abstract, identify key findings, write to ~/crow-lore/ai-papers-{date}/"

# Job 2: Kashik guides
schedule: "0 9 * * 0"  # Sunday 9am
agent: kashik
task: "Read ~/crow-lore/ai-papers-{date}/, produce universal guides for actionable papers, publish to ~/guides/"

# Job 3: Klerik review
schedule: "0 12 * * 0"  # Sunday noon
agent: klerik
task: "Review all guides in ~/guides/ published today. Check accuracy, clarity, completeness. Approve or flag fixes."
```

### What Happens Each Sunday

1. **6:00 AM** — Crow wakes, queries arxiv API, extracts 5 papers, writes structured lore
2. **9:00 AM** — Kashik scans Crow's lore, identifies 3 papers guide-worthy, produces guides with steps/pitfalls/examples
3. **12:00 PM** — Klerik reviews the 3 guides, approves 2, flags 1 for revision (missing edge case)
4. Kashik revises, Klerik re-reviews, all 3 published

The user wakes up Monday to 3 new AI guides, fully researched and reviewed, delivered to Discord.

---

## Scenario 3: Profile Creation Chain

**Goal:** A Discord user asks for a new agent profile. The fleet creates it end-to-end.

### The Flow

1. **Discord user:** "I need a profile that monitors my servers and alerts me when disk space is low."

2. **Anser** catches the question, plans the profile:
   - Agent name: "Watchdog"
   - Role: Server health monitor
   - Tools needed: terminal (df, free, top), cronjob (scheduling), Discord webhook (alerts)
   - Skills: system-monitoring

3. **Anser** hands the plan to **Senter.**

4. **Senter** dispatches:
   - **Nous Girl** brainstorms the SOUL.md — personality, tone, communication style
   - **Klerik** reviews and refines Nous Girl's draft
   - **Chizul** creates the profile directory, config.yaml, skill files
   - **Klerik** does final review
   - Approved profile is pushed to `SouthpawIN/watchdog`

5. **Anser** responds in Discord: "Here's your Watchdog profile — install with `hermes profile install https://github.com/SouthpawIN/watchdog`"

6. **Kashik** records the entire creation chain — who contributed what, which decisions were made, what the review found.

---

## Scenario 4: Infrastructure Migration

**Goal:** Migrate a service from one cluster to another with zero downtime.

### The Chain

```
Senter (dispatch)
  ├── Crow (research migration patterns, risks)
  ├── Anser (plan the migration phases)
  ├── Chizul (update configs, test locally)
  ├── Klerik (review config changes, verify rollback plan)
  └── Frieza (execute migration, monitor health)
```

**Key handoffs:**
- Crow's research informs Anser's plan
- Anser's plan tells Senter the task order
- Chizul's config changes must pass Klerik before Frieza touches them
- Frieza monitors health during migration — if anything fails, rollback is automatic
- Kashik documents the entire migration for future reference

---

## Scenario 5: Documentation Blitz

**Goal:** Document an entire codebase in one pass.

### The Chain

```
Crow (research codebase structure)
  ↓
Nous Girl (brainstorm doc structure, tone)
  ↓
Kashik (write the docs — tutorials, API refs, guides)
  ↓
Klerik (review for accuracy, clarity)
  ↓
Kashik (publish approved docs)
```

**What makes this work:**
- Crow reads the codebase, identifies all modules, their purposes, and their relationships
- Nous Girl suggests a documentation structure that makes sense for the audience
- Kashik writes every page — tutorials for beginners, API references for developers
- Klerik verifies every code example actually works

---

## Fleet Interaction Map

```
                    ┌─────────────────────────────┐
                    │         DISCORD             │
                    │  (users, questions, ideas)  │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │           ANSER             │
                    │  Support + Project Planning │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │           SENTER            │
                    │   Triage + Orchestration    │
                    └──┬───────┬───────┬───────┬──┘
                       │       │       │       │
          ┌────────────▼─┐ ┌───▼───┐ ┌─▼───────▼─┐ ┌──────────┐
          │    CHIZUL    │ │ CROW  │ │   ANSER   │ │  FRIEZA  │
          │    Build     │ │Research│ │   Plan    │ │  Deploy  │
          └──────┬───────┘ └───┬───┘ └───────────┘ └──────────┘
                 │             │
          ┌──────▼───────┐ ┌───▼───────┐
          │    KLERIK    │ │  KASHIK   │
          │    Review    │ │  Record   │
          └──────────────┘ └───────────┘
```

Every arrow is a handoff. Every handoff preserves context. Every agent knows what came before.

---

## Next Steps

Now that you've seen the fleet in action:

1. **Install the fleet** — See [Getting Started](01-getting-started.md)
2. **Plan your first project** — See [Project Planning](02-project-planning.md)
3. **Orchestrate a workflow** — See [Agent Orchestration](03-agent-orchestration.md)

---

*Part of the SouthpawIN agent fleet tutorials*
