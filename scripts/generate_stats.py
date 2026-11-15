"""Generate assets/stats.svg and assets/languages.svg from the GitHub GraphQL API.

Self-hosted instead of github-readme-stats so the cards match the site's
theme and never break on a rate-limited public instance. Runs in
.github/workflows/profile-assets.yml; locally: GITHUB_TOKEN=... python scripts/generate_stats.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

API = "https://api.github.com/graphql"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGIN = os.environ.get("PROFILE_LOGIN", "WhyN0t101")

# Languages that are build/markup noise rather than something written by hand.
IGNORED_LANGUAGES = {"HTML", "CSS", "SCSS", "Makefile", "Dockerfile", "Batchfile", "ShaderLab", "HLSL", "GLSL", "Procfile"}
TOP_LANGUAGES = 6
# Site palette: purple ramp first, then the category accents (sec / net / dev).
PALETTE = ["#d8b4fe", "#a855f7", "#60a5fa", "#4ade80", "#f87171", "#7c3aed", "#9a92ad"]

QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


@dataclass
class Stats:
    repos: int = 0
    stars: int = 0
    followers: int = 0
    pull_requests: int = 0
    issues: int = 0
    contributed_to: int = 0
    commits_year: int = 0
    contributions_year: int = 0
    weekly: list[int] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)


def graphql(token: str, variables: dict) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]


def fetch_pages(token: str, login: str) -> list[dict]:
    pages, cursor = [], None
    while True:
        user = graphql(token, {"login": login, "cursor": cursor})
        pages.append(user)
        info = user["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            return pages
        cursor = info["endCursor"]


def aggregate(pages: list[dict]) -> Stats:
    """Fold paginated API responses into one Stats object."""
    first = pages[0]
    contrib = first["contributionsCollection"]
    weeks = contrib["contributionCalendar"]["weeks"]
    stats = Stats(
        repos=first["repositories"]["totalCount"],
        followers=first["followers"]["totalCount"],
        pull_requests=first["pullRequests"]["totalCount"],
        issues=first["issues"]["totalCount"],
        contributed_to=first["repositoriesContributedTo"]["totalCount"],
        commits_year=contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"],
        contributions_year=contrib["contributionCalendar"]["totalContributions"],
        weekly=[sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks],
    )
    for page in pages:
        for repo in page["repositories"]["nodes"]:
            stats.stars += repo["stargazerCount"]
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                if name in IGNORED_LANGUAGES:
                    continue
                stats.languages[name] = stats.languages.get(name, 0) + edge["size"]
    return stats


def top_languages(languages: dict[str, int], limit: int = TOP_LANGUAGES) -> list[tuple[str, float]]:
    """Return (name, percent) pairs; everything past `limit` is folded into 'Other'."""
    total = sum(languages.values())
    if total == 0:
        return []
    ranked = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)
    head, tail = ranked[:limit], ranked[limit:]
    result = [(name, size * 100 / total) for name, size in head]
    if tail:
        result.append(("Other", sum(size for _, size in tail) * 100 / total))
    return result


# ---------------------------------------------------------------- rendering

CARD_W, CARD_H = 495, 230

STYLE = """
    .mono { font-family: 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
    .faint { fill: #6b6480; } .dim { fill: #9a92ad; } .soft { fill: #c4b5fd; } .txt { fill: #e9e6f0; }
    .row { opacity: 0; animation: in .5s ease-out forwards; }
    @keyframes in { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: none; } }
    .bar { transform-box: fill-box; transform-origin: 0 100%; transform: scaleY(0); animation: grow .6s ease-out forwards; }
    @keyframes grow { to { transform: scaleY(1); } }
    .seg { transform-box: fill-box; transform-origin: 0 50%; transform: scaleX(0); animation: grow-x .8s ease-out forwards; }
    @keyframes grow-x { to { transform: scaleX(1); } }
    @media (prefers-reduced-motion: reduce) { .row, .bar, .seg { animation: none; opacity: 1; transform: none; } }
"""


def frame(title: str, body: str, height: int = CARD_H) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {height}" width="{CARD_W}" height="{height}" role="img" aria-label="{escape(title)}">
  <title>{escape(title)}</title>
  <style>{STYLE}</style>
  <defs>
    <radialGradient id="g" cx="100%" cy="0%" r="90%">
      <stop offset="0" stop-color="#581c87" stop-opacity=".35"/>
      <stop offset="1" stop-color="#581c87" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect x=".5" y=".5" width="{CARD_W - 1}" height="{height - 1}" rx="12" fill="#07040d" stroke="#a855f7" stroke-opacity=".28"/>
  <rect x=".5" y=".5" width="{CARD_W - 1}" height="{height - 1}" rx="12" fill="url(#g)"/>
  <line x1="1" y1="36" x2="{CARD_W - 1}" y2="36" stroke="#a855f7" stroke-opacity=".16"/>
  <circle cx="20" cy="18" r="5" fill="#ff5f57" opacity=".85"/>
  <circle cx="37" cy="18" r="5" fill="#febc2e" opacity=".85"/>
  <circle cx="54" cy="18" r="5" fill="#28c840" opacity=".85"/>
  <text x="72" y="22.5" class="mono faint" font-size="12">tiago@<tspan class="soft">whyn0t101</tspan>: {escape(title)}</text>
{body}
</svg>
"""


def fmt(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 10_000 else f"{n:,}"


def render_stats(stats: Stats) -> str:
    rows = [
        ("contributions", "last year", stats.contributions_year),
        ("commits", "last year", stats.commits_year),
        ("pull requests", "all time", stats.pull_requests),
        ("issues", "all time", stats.issues),
        ("contributed to", "repos", stats.contributed_to),
        ("public repos", "owned", stats.repos),
        ("stars", "earned", stats.stars),
    ]
    lines = [
        '  <text x="20" y="62" class="mono" font-size="13"><tspan class="faint">$ </tspan>'
        '<tspan class="txt">gh stats --user whyn0t101</tspan></text>'
    ]
    for i, (label, hint, value) in enumerate(rows):
        y = 90 + i * 19
        lines.append(
            f'  <g class="row mono" font-size="12.5" style="animation-delay:{0.15 + i * 0.08:.2f}s">'
            f'<text x="20" y="{y}" class="dim">{label}</text>'
            f'<text x="134" y="{y}" class="faint">{hint}</text>'
            f'<text x="248" y="{y}" class="soft" text-anchor="end" font-weight="600">{fmt(value)}</text></g>'
        )
    lines.append(render_activity(stats.weekly, x=274, y=82, w=201, h=114))
    return frame("~/stats", "\n".join(lines))


def render_activity(weekly: list[int], x: int, y: int, w: int, h: int) -> str:
    """Weekly contribution bars for the last year, scaled to the busiest week."""
    weeks = weekly[-52:]
    peak = max(weeks, default=0) or 1
    gap = 1.2
    bw = (w - gap * (len(weeks) - 1)) / max(len(weeks), 1)
    parts = [
        f'  <text x="{x}" y="{y - 10}" class="mono faint" font-size="11">activity · 52 weeks</text>',
        f'  <line x1="{x}" y1="{y + h}" x2="{x + w}" y2="{y + h}" stroke="#a855f7" stroke-opacity=".25"/>',
    ]
    for i, count in enumerate(weeks):
        bh = max(2.0, count / peak * (h - 8)) if count else 2.0
        bx = x + i * (bw + gap)
        fill = "#d8b4fe" if count == peak and count else "#a855f7"
        opacity = 0.9 if count else 0.18
        parts.append(
            f'  <rect class="bar" x="{bx:.2f}" y="{y + h - bh:.2f}" width="{bw:.2f}" height="{bh:.2f}" rx="1" '
            f'fill="{fill}" opacity="{opacity}" style="animation-delay:{0.3 + i * 0.012:.3f}s"/>'
        )
    parts.append(
        f'  <text x="{x + w}" y="{y + h + 16}" class="mono faint" font-size="10.5" text-anchor="end">peak {peak if any(weeks) else 0}/wk</text>'
    )
    return "\n".join(parts)


def render_languages(langs: list[tuple[str, float]]) -> str:
    lines = [
        '  <text x="20" y="62" class="mono" font-size="13"><tspan class="faint">$ </tspan>'
        '<tspan class="txt">linguist --top --by-bytes</tspan></text>'
    ]
    bar_x, bar_y, bar_w = 20, 78, CARD_W - 40
    lines.append(f'  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="#a855f7" opacity=".1"/>')
    lines.append(f'  <clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>')
    lines.append('  <g clip-path="url(#bar)">')
    cursor = bar_x
    for i, (_, pct) in enumerate(langs):
        seg = bar_w * pct / 100
        lines.append(
            f'    <rect class="seg" x="{cursor:.2f}" y="{bar_y}" width="{seg + 0.5:.2f}" height="10" '
            f'fill="{PALETTE[i % len(PALETTE)]}" style="animation-delay:{0.1 + i * 0.1:.2f}s"/>'
        )
        cursor += seg
    lines.append("  </g>")
    for i, (name, pct) in enumerate(langs):
        col, row = i % 2, i // 2
        x, y = 20 + col * 232, 126 + row * 30
        lines.append(
            f'  <g class="row mono" font-size="12.5" style="animation-delay:{0.2 + i * 0.08:.2f}s">'
            f'<rect x="{x}" y="{y - 9}" width="9" height="9" rx="2" fill="{PALETTE[i % len(PALETTE)]}"/>'
            f'<text x="{x + 17}" y="{y}" class="txt">{escape(name)}</text>'
            f'<text x="{x + 210}" y="{y}" class="dim" text-anchor="end">{pct:.1f}%</text></g>'
        )
    if not langs:
        lines.append('  <text x="20" y="118" class="mono dim" font-size="12.5">no language data yet</text>')
    return frame("~/languages", "\n".join(lines))


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set", file=sys.stderr)
        return 1
    stats = aggregate(fetch_pages(token, LOGIN))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "stats.svg").write_text(render_stats(stats), encoding="utf-8")
    (OUT_DIR / "languages.svg").write_text(render_languages(top_languages(stats.languages)), encoding="utf-8")
    print(f"wrote stats.svg and languages.svg to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
