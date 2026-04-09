#!/usr/bin/env python3
"""
Generate research/index.mdx — the landing page for the 研究 tab.
Scans all subdirectories under research/ and builds a structured index with
titles + first-line excerpts from each .md file.
"""
import os
import re
from pathlib import Path

RESEARCH_DIR = Path("/Volumes/SSK SSD/Projects/mintlify-docs/research")
OUTPUT_FILE = RESEARCH_DIR / "index.mdx"

# Area display names and descriptions (matches docs.json navigation groups)
AREA_META = {
    "bayesian":            ("Bayesian Statistics",      "Bayesian data analysis, MCMC methods, hierarchical models, and probabilistic inference."),
    "causal-inference":    ("Causal Inference",        "Causal reasoning, potential outcomes framework, and identification strategies."),
    "differential-geometry":("Differential Geometry",  "Curves, surfaces, and Riemannian geometry — the mathematics of smooth spaces."),
    "discrete-mathematics":("Discrete Mathematics",    "Logic, combinatorics, graph theory, and discrete structures."),
    "information-geometry":("Information Geometry",    "Statistical manifolds, exponential families, Amari's information geometry, and Orlicz spaces."),
    "schubert":            ("Schubert Calculus",       "Cohomology of flag varieties, Schubert polynomials, quantum cohomology, and enumerative geometry."),
    "statistic":           ("Mathematical Statistics", "Statistical theory, estimators, hypothesis testing, and asymptotic methods."),
}

# Regex to extract the first ATX heading (# Title)
HEADING_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
# Strip markdown bold/italic markup
STRIP_RE = re.compile(r"\*+|_+|`+")

def slugify(name: str) -> str:
    """Convert a display name to a URL slug matching docs.json path conventions."""
    return name.lower().replace(" ", "-")

def extract_title(body: str, filename: str) -> str:
    """Get title from first heading, fallback to cleaned filename."""
    m = HEADING_RE.search(body)
    if m:
        title = m.group(1).strip()
        # Strip formatting markup
        title = STRIP_RE.sub("", title)
        return title
    # Fallback: clean up filename
    name = Path(filename).stem
    name = re.sub(r"[-_]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def get_excerpt(body: str, max_chars: int = 200) -> str:
    """Extract a short excerpt from the first non-heading paragraph."""
    lines = body.splitlines()
    excerpt_lines = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if stripped.startswith("#"):
            continue
        excerpt_lines.append(stripped)
        if sum(len(l) for l in excerpt_lines) > max_chars:
            break
    excerpt = " ".join(excerpt_lines)
    # Clean up
    excerpt = re.sub(r"\s+", " ", excerpt).strip()
    # Truncate
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rsplit(" ", 1)[0] + "..."
    return excerpt if excerpt else "No description available."

def find_md_files(base: Path) -> list[tuple[str, str, str, str]]:
    """
    Recursively find all .md files under base.
    Returns list of (relative_path, title, excerpt, group_slug).
    """
    results = []
    # Map subdirectory names to group slugs (same as key names in AREA_META)
    subdirs = {d.name: d.name for d in base.iterdir() if d.is_dir() and d.name in AREA_META}

    for subdir_name, group_slug in subdirs.items():
        subdir = base / subdir_name
        for md_file in sorted(subdir.rglob("*.md")):
            rel = md_file.relative_to(base)
            body = md_file.read_text(encoding="utf-8", errors="replace")
            title = extract_title(body, md_file.name)
            excerpt = get_excerpt(body)
            # Build the docs path (matches docs.json format)
            # e.g. research/bayesian/01-three-steps/01-three-steps
            parts = list(rel.parts)
            # Remove .md extension from last part
            parts[-1] = parts[-1][:-3]
            docs_path = "research/" + "/".join(parts)
            results.append((docs_path, title, excerpt, group_slug))
    return results

def build_mdx(pages: list[tuple[str, str, str, str]]) -> str:
    """Build the MDX index page content."""
    lines = [
        '---',
        'title: 研究索引',
        'description: Overview of all research notes — Bayesian, Information Geometry, Schubert Calculus, and more.',
        '---',
        '',
        '# 研究索引',
        '',
        '<div style={{textAlign: "center", marginBottom: "2rem"}}>',
        '',
    ]

    # Group pages by area
    by_area: dict[str, list] = {}
    for page in pages:
        by_area.setdefault(page[3], []).append(page)

    # Shortcut links for each area
    lines.append("## 快速跳转")
    lines.append("")
    lines.append("<div style={{display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'center', marginBottom: '2rem'}}>")
    for area_slug, (display_name, _) in AREA_META.items():
        count = len(by_area.get(area_slug, []))
        lines.append(f'<a href=#{area_slug} style={{padding: "0.4rem 0.8rem", backgroundColor: "#f3f4f6", borderRadius: "0.4rem", fontSize: "0.875rem", color: "#374151", textDecoration: "none"}}>{display_name} ({count})</a>')
    lines.append("</div>")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"共 **{len(pages)}** 篇研究笔记，涵盖数学、统计学与几何学多个领域。")
    lines.append("")

    # Detailed sections per area
    for area_slug, (display_name, description) in AREA_META.items():
        area_pages = by_area.get(area_slug, [])
        lines.append(f"## {display_name}")
        lines.append("")
        lines.append(f"*{description}*")
        lines.append("")
        lines.append(f"| 标题 | 摘要 |")
        lines.append("|------|------|")
        for docs_path, title, excerpt, _ in area_pages:
            url = f"/{docs_path}"
            # Truncate title for table
            title_short = title[:60] + ("..." if len(title) > 60 else "")
            excerpt_short = excerpt[:120] + ("..." if len(excerpt) > 120 else "")
            lines.append(f"| [{title_short}]({url}) | {excerpt_short} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)

def main():
    pages = find_md_files(RESEARCH_DIR)
    mdx = build_mdx(pages)
    OUTPUT_FILE.write_text(mdx, encoding="utf-8")
    print(f"✓ Written {len(pages)} pages to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
