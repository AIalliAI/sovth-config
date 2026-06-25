#!/usr/bin/env python3
"""
Turbofit Model Database — Daily Research Script

Scans research sources for new models, pricing changes, and benchmark updates.
Outputs a diff report of what changed. The agent reviews and applies changes
to model-database.yaml, then syncs to GitHub.

Usage:
    python3 research-models.py [--dry-run] [--source <source_name>]

Sources are defined in model-database.yaml under research_sources.
"""

import json
import sys
import os
import re
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "references", "model-database.yaml")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "references", "research-report.md")

# Sources to check
SOURCES = {
    "openrouter_models": {
        "url": "https://openrouter.ai/api/v1/models",
        "type": "pricing",
        "description": "OpenRouter API — live model list with pricing",
    },
    "huggingface_gguf": {
        "url": "https://huggingface.co/api/models?search=GGUF&sort=lastModified&direction=-1&limit=20",
        "type": "local_models",
        "description": "HuggingFace — recently updated GGUF models",
    },
    "pricepertoken": {
        "url": "https://pricepertoken.com/news/model-releases",
        "type": "model_releases",
        "description": "Price Per Token — new model releases and price changes",
    },
    "llmcheck": {
        "url": "https://llmcheck.net/blog/",
        "type": "benchmarks",
        "description": "LLMCheck — benchmark rankings for local models",
    },
}

# Known model families to watch for
WATCH_FAMILIES = [
    "qwen", "glm", "deepseek", "mimo", "minimax", "kimi", "llama",
    "grok", "phi", "gemma", "mistral", "nemotron", "step", "falcon",
    "command", "claude", "gpt", "gemini", "yi", "codestral", "devstral",
]

def fetch_url(url, timeout=15):
    """Fetch URL content with proper headers."""
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) turbofit-research/1.0",
        "Accept": "application/json, text/html",
    })
    try:
        with urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read().decode("utf-8", errors="replace")
            return data, content_type
    except (URLError, HTTPError, Exception) as e:
        return None, str(e)

def parse_openrouter_models(json_text):
    """Parse OpenRouter /api/v1/models response for pricing data."""
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return []

    models = []
    for m in data.get("data", []):
        slug = m.get("id", "")
        pricing = m.get("pricing", {})
        context_length = m.get("context_length", 0)
        architecture = m.get("architecture", {})
        modality = m.get("modality", "")

        # Check if it matches a watched family
        slug_lower = slug.lower()
        matched_family = None
        for family in WATCH_FAMILIES:
            if family in slug_lower:
                matched_family = family
                break

        if not matched_family:
            continue

        prompt_price = float(pricing.get("prompt", "0") or "0")
        completion_price = float(pricing.get("completion", "0") or "0")
        input_price = prompt_price * 1_000_000
        output_price = completion_price * 1_000_000

        models.append({
            "slug": slug,
            "family": matched_family,
            "input_per_m": round(input_price, 4),
            "output_per_m": round(output_price, 4),
            "context_length": context_length,
            "modality": modality,
            "architecture": architecture.get("modality", ""),
            "is_free": prompt_price == 0 and completion_price == 0,
        })

    return models

def parse_huggingface_gguf(json_text):
    """Parse HuggingFace API response for recently updated GGUF models."""
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return []

    models = []
    for m in data:
        model_id = m.get("id", "")
        last_modified = m.get("lastModified", "")
        downloads = m.get("downloads", 0)

        model_lower = model_id.lower()
        matched_family = None
        for family in WATCH_FAMILIES:
            if family in model_lower:
                matched_family = family
                break

        if not matched_family:
            continue

        models.append({
            "repo": model_id,
            "family": matched_family,
            "last_modified": last_modified,
            "downloads": downloads,
        })

    return models

def check_pricepertoken(html_text):
    """Extract recent model releases from Price Per Token news page."""
    releases = []
    for family in WATCH_FAMILIES:
        pattern = rf"(?i){family}[\s\-]?(?:v?[\d.]+)?[\s\w]*"
        matches = re.findall(pattern, html_text)
        for match in matches[:3]:
            clean = match.strip()
            if len(clean) > 5 and clean not in [r["name"] for r in releases]:
                releases.append({"name": clean, "family": family, "source": "pricepertoken"})

    return releases[:20]

def generate_report(openrouter_models, hf_models, ppt_releases, errors):
    """Generate markdown report of findings."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# Turbofit Model Research Report — {today}",
        "",
        "## Summary",
        f"- OpenRouter models scanned: {len(openrouter_models)}",
        f"- HuggingFace GGUF models found: {len(hf_models)}",
        f"- Price Per Token releases detected: {len(ppt_releases)}",
        f"- Errors: {len(errors)}",
        "",
    ]

    if errors:
        lines.append("## Errors")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    if openrouter_models:
        lines.append("## OpenRouter Model Pricing (watched families)")
        lines.append("")
        lines.append("| Slug | Family | Input $/M | Output $/M | Context | Free | Modality |")
        lines.append("|------|--------|----------|------------|---------|------|-----------|")
        for m in sorted(openrouter_models, key=lambda x: x["family"]):
            free = "YES" if m["is_free"] else "no"
            ctx_k = m["context_length"] // 1000 if m["context_length"] else 0
            lines.append(
                f"| {m['slug']} | {m['family']} | ${m['input_per_m']:.4f} | ${m['output_per_m']:.4f} | {ctx_k}K | {free} | {m['modality']} |"
            )
        lines.append("")

    free_models = [m for m in openrouter_models if m["is_free"]]
    if free_models:
        lines.append("## Free Models on OpenRouter")
        lines.append("")
        for m in free_models:
            ctx_k = m["context_length"] // 1000 if m["context_length"] else 0
            lines.append(f"- **{m['slug']}** -- {ctx_k}K ctx, modality: {m['modality']}")
        lines.append("")

    if hf_models:
        lines.append("## Recently Updated GGUF Models on HuggingFace")
        lines.append("")
        lines.append("| Repo | Family | Last Modified | Downloads |")
        lines.append("|------|--------|--------------|-----------|")
        for m in sorted(hf_models, key=lambda x: x["last_modified"], reverse=True):
            lines.append(f"| {m['repo']} | {m['family']} | {m['last_modified']} | {m['downloads']:,} |")
        lines.append("")

    if ppt_releases:
        lines.append("## Recent Model Releases (Price Per Token)")
        lines.append("")
        for r in ppt_releases:
            lines.append(f"- **{r['name']}** (family: {r['family']})")
        lines.append("")

    lines.append("## Action Items")
    lines.append("")
    lines.append("The agent should review the above and:")
    lines.append("1. Add any NEW models to `model-database.yaml`")
    lines.append("2. Update pricing for existing models if changed")
    lines.append("3. Update benchmark scores if new data available")
    lines.append("4. Check if any free endpoints changed status")
    lines.append("5. Note any models that should be added to the pairing matrix")
    lines.append("")

    return "\n".join(lines)

def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Turbofit Model Research -- {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    errors = []
    openrouter_models = []
    hf_models = []
    ppt_releases = []

    # 1. Fetch OpenRouter model list
    print("\n1. Fetching OpenRouter models...")
    data, ct = fetch_url(SOURCES["openrouter_models"]["url"])
    if data:
        openrouter_models = parse_openrouter_models(data)
        print(f"   Found {len(openrouter_models)} watched-family models on OpenRouter")
    else:
        errors.append(f"OpenRouter API: {ct}")
        print(f"   ERROR: {ct}")

    # 2. Fetch HuggingFace GGUF trending
    print("\n2. Fetching HuggingFace GGUF models...")
    data, ct = fetch_url(SOURCES["huggingface_gguf"]["url"])
    if data:
        hf_models = parse_huggingface_gguf(data)
        print(f"   Found {len(hf_models)} recently updated GGUF models")
    else:
        errors.append(f"HuggingFace API: {ct}")
        print(f"   ERROR: {ct}")

    # 3. Fetch Price Per Token releases
    print("\n3. Fetching Price Per Token releases...")
    data, ct = fetch_url(SOURCES["pricepertoken"]["url"])
    if data:
        ppt_releases = check_pricepertoken(data)
        print(f"   Detected {len(ppt_releases)} potential releases")
    else:
        errors.append(f"Price Per Token: {ct}")
        print(f"   ERROR: {ct}")

    # 4. Generate report
    print("\n4. Generating report...")
    report = generate_report(openrouter_models, hf_models, ppt_releases, errors)

    if dry_run:
        print("\n--- DRY RUN -- Report preview ---\n")
        print(report[:3000])
        print("\n...(truncated)...")
    else:
        with open(OUTPUT_PATH, "w") as f:
            f.write(report)
        print(f"   Report written to {OUTPUT_PATH}")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {len(openrouter_models)} OR models, {len(hf_models)} HF GGUF, {len(ppt_releases)} PPT releases, {len(errors)} errors")

    if not openrouter_models and not hf_models and not ppt_releases:
        print("STATUS: ALL_SOURCES_FAILED")
        sys.exit(1)

    print("STATUS: OK")

if __name__ == "__main__":
    main()
