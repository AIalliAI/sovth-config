# Project Planning with the Agent Fleet

![Project Planning](https://v3b.fal.media/files/b/0a9fe87a/evZb4pB-5QLIBfb1ADrEv_DLGucjGs.png)

## Overview

Project planning turns rough ideas into executable plans. The fleet has a dedicated planning workflow: **Anser** analyzes your concept against the full Hermes ecosystem and produces a structured plan document. **Senter** then dispatches it across the fleet for execution.

This tutorial covers the end-to-end planning workflow — from idea to deployed result.

---

## The Planning Chain

```
Your Idea → Anser (plans) → Plan Document → Senter (dispatches) → Agents (build)
                                              ↓
                                         Kashik (records)
```

---

## Step 1: Feed Anser Your Idea

Anser is the planning entry point. Give it as much context as you have:

```bash
hermes chat --profile anser
```

**Good prompts for planning:**

> *"I want an agent that monitors our CI pipelines and posts a daily summary to Discord. What would that take?"*

> *"Plan out a system where Crow researches new AI papers weekly, Kashik turns them into guides, and Klerik reviews the guides before publication."*

> *"I need a multi-step workflow: scrape docs from 5 competitor APIs, compare their approaches, and generate a report. Which agents do I use and in what order?"*

---

## Step 2: What Anser Does

When Anser receives a planning request, it:

1. **Analyzes the idea** — What are the moving parts? Constraints? Desired outcomes?
2. **Audits the Hermes ecosystem** — What profiles, skills, tools, and plugins exist that can help?
3. **Structures the plan** — Breaks into phases with tasks, agent assignments, and dependencies
4. **Produces a plan document** — Written as a file attachment, ready for Senter

---

## Step 3: Understanding the Plan Document

Anser's plan documents follow a standard structure:

### Project Overview
One paragraph summarizing what's being built and why.

### Phases
Ordered stages with clear goals:
- **Phase 1: Research** — Crow investigates the problem space
- **Phase 2: Design** — Nous Girl brainstorms approaches, Anser structures the design
- **Phase 3: Build** — Chizul implements, Frieza provisions infrastructure
- **Phase 4: Review** — Klerik checks quality, catches issues
- **Phase 5: Document** — Kashik records everything, writes public guides

### Task Table
Each task has:
- **ID** — unique identifier
- **Description** — what needs to happen
- **Agent** — who does it
- **Dependencies** — what must complete first
- **Tools** — which Hermes tools are needed

### Estimated Effort
Rough time per phase based on complexity and agent availability.

### Next Steps
What to do first — typically "give this plan to Senter for dispatch."

---

## Step 4: Hand Off to Senter

Once Anser produces the plan:

```bash
hermes chat --profile senter
```

Say:

> *"Here's the plan Anser produced for the CI monitoring bot. Dispatch it."*

Senter reads the plan document, creates Kanban tasks for each phase, and assigns them to the right agents. You can check progress anytime:

> *"What's the status of the CI monitoring bot project?"*

---

## Example: Planning a Weekly Research Pipeline

**User to Anser:**

> *"I want a system where Crow researches new AI papers every Sunday, Kashik turns the best ones into guides, and Klerik reviews the guides before they go live. Plan this."*

**Anser's plan would include:**

- **Phase 1:** Crow cron job (weekly, Sunday 6am) — searches arxiv, extracts top 5 papers, writes research lore
- **Phase 2:** Kashik cron job (Sunday 9am) — reads Crow's lore, produces guide drafts
- **Phase 3:** Klerik cron job (Sunday 12pm) — reviews guides, approves or flags fixes
- **Phase 4:** Publication — approved guides go to `~/guides/`

Anser identifies the Hermes tools needed: `cronjob` for scheduling, `web_search` + `web_extract` for Crow, `llm-wiki` for Kashik, file tools for Klerik review.

---

## Advanced Planning Patterns

### Pattern 1: Fan-Out Research
One research question → Crow researches multiple angles in parallel → Kashik synthesizes into one guide.

### Pattern 2: Build-Review Cycle
Chizul builds → Klerik reviews → Chizul fixes → Klerik approves → Frieza deploys.

### Pattern 3: Continuous Documentation
Every agent action → Kashik observes → wiki updates → Klerik uses wikis to improve agent profiles.

### Pattern 4: Discord-Driven Planning
User asks in Discord → Anser catches it → plans the project → Senter dispatches → result delivered back to Discord.

---

## Next Tutorial

- **[Agent Orchestration](03-agent-orchestration.md)** — Deep dive into multi-agent handoffs

---

*Part of the SouthpawIN agent fleet tutorials*
