"""Generate assets/profile.svg, the whole README as one animated SVG.

Composes the existing banner, stats and languages cards with the whoami text
and the stack table, so run it after make_banner.py / generate_stats.py.
The banner's background (hex dump, glows, scanlines, frame) is dropped and
redrawn once across the whole card so the header blends into the rest.
Embedded cards keep their own animations; ids are prefixed per card so they
cannot collide, and the stats cards' delays are shifted so they play after the stack.
"""

from __future__ import annotations

import re
import textwrap
from html import escape
from pathlib import Path

from make_banner import HEX_ROWS, hex_line

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUT = ASSETS / "profile.svg"

WIDTH = 1200
PAD = 48
BANNER_H = 400
CARD_W, CARD_H = 495, 230

ABOUT = [
    "Computer Engineer from Portugal, with an MSc in Cybersecurity and Digital Forensics "
    "from the University of Leiria and Oeste.",
    "I work across offense, defence and the infrastructure underneath both: malware analysis "
    "and detection engineering, mobile and disk forensics, penetration testing, SIEM, and the "
    "networks and virtualisation platforms these run on.",
]

# (label, accent, items) — accents follow the site palette: sec red, dev green, net blue.
STACK = [
    ("Security", "#f87171", ["Wazuh", "YARA", "Metasploit", "Burp Suite", "Ghidra", "Wireshark", "Kali Linux", "pfSense"]),
    ("Languages", "#d8b4fe", ["Python", "Java", "C#", "Rust", "TypeScript", "Bash", "PowerShell", "Solidity"]),
    ("Frameworks", "#4ade80", ["Spring Boot", ".NET", "Vue.js", "React", "Flask"]),
    ("Infrastructure", "#a855f7", ["Proxmox", "Kubernetes", "Docker", "VMware", "Hyper-V", "MikroTik", "GNS3"]),
    ("Networking", "#60a5fa", ["BGP", "OSPF", "MPLS L3VPN", "WireGuard", "SDN"]),
]

ABOUT_WRAP = 140  # chars per line at 17px sans (~7.5px/char) inside the 1104px text column
CHAR_W = 7.6  # mono 12.5px advance; shortcut: estimated, exact only with a font metrics lib
CHIP_H, CHIP_GAP, ROW_H = 28, 10, 46
HEX_ROW_H = 22

# Banner layers replaced by the full-height background in build().
BANNER_BACKGROUND = [
    r'<rect width="1200" height="400" fill="#030106"/>.*?<rect width="1200" height="400" fill="url\(#scan\)"/>',
    r'<rect x="\.5" y="\.5" width="1199" height="399" rx="16" fill="none"[^>]*/>',
]

STYLE = """
    .mono { font-family: 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
    .sans { font-family: 'Hanken Grotesk', 'Segoe UI', system-ui, -apple-system, Helvetica, Arial, sans-serif; }
    .faint { fill: #6b6480; } .dim { fill: #9a92ad; } .soft { fill: #c4b5fd; } .txt { fill: #e9e6f0; }
    .p-type { clip-path: inset(0 100% 0 0); animation: p-type var(--d, .5s) steps(var(--s, 16)) forwards; animation-delay: var(--t, 0s); }
    @keyframes p-type { to { clip-path: inset(0 0 0 0); } }
    .p-in { opacity: 0; animation: p-in .55s ease-out forwards; animation-delay: var(--t, 0s); }
    @keyframes p-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
    .p-caret { animation: p-blink 1.05s steps(1) infinite; }
    .p-hex { fill: #a855f7; opacity: .16; font-size: 14px; }
    .p-scroll { animation: p-scroll 38s linear infinite; }
    @keyframes p-scroll { from { transform: translateY(0); } to { transform: translateY(-{loop}px); } }
    @keyframes p-blink { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }
    @media (prefers-reduced-motion: reduce) {
      .p-type { animation: none; clip-path: none; }
      .p-in { animation: none; opacity: 1; }
      .p-caret, .p-scroll { animation: none; }
    }
"""


def embed(
    path: Path, prefix: str, x: float, y: float, w: float, h: float, delay: float = 0.0, drop: tuple[str, ...] = ()
) -> str:
    """Inline another SVG as a nested <svg>, prefixing its ids and shifting its animation delays.

    Each regex in `drop` must match once and is removed, so a layout change in the source fails loudly.
    """
    src = path.read_text(encoding="utf-8")
    for pattern in drop:
        src, n = re.subn(pattern, "", src, count=1, flags=re.S)
        if n != 1:
            raise ValueError(f"{path}: pattern to drop not found: {pattern}")
    src = re.sub(r'\bid="([^"]+)"', rf'id="{prefix}\1"', src)
    src = re.sub(r"url\(#([^)]+)\)", rf"url(#{prefix}\1)", src)
    if delay:
        src = re.sub(r"animation-delay:\s*([\d.]+)s", lambda m: f"animation-delay:{float(m[1]) + delay:.2f}s", src)
    viewbox = re.search(r'viewBox="([^"]+)"', src)
    if not viewbox:
        raise ValueError(f"{path} has no viewBox")
    open_tag = re.match(r"\s*<svg\b[^>]*>", src)
    if not open_tag:
        raise ValueError(f"{path} does not start with <svg>")
    body = src[open_tag.end():]
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{viewbox[1]}">{body}'


def background(height: int) -> str:
    """Hex dump, glows and scanlines from the banner, stretched over the full card height."""
    loop = HEX_ROWS * HEX_ROW_H
    rows = (height + loop) // HEX_ROW_H + 2
    hex_rows = "\n        ".join(
        f'<text x="0" y="{r * HEX_ROW_H}">{hex_line(r % HEX_ROWS)}</text>' for r in range(rows)
    )
    return f"""<rect width="{WIDTH}" height="{height}" fill="#030106"/>
    <g mask="url(#p-hexMask)">
      <!-- separate groups: the CSS scroll transform would replace a transform attribute on the same element -->
      <g transform="translate(560 18)"><g class="mono p-hex p-scroll">
        {hex_rows}
      </g></g>
    </g>
    <rect width="{WIDTH}" height="{BANNER_H}" fill="url(#p-glowTop)"/>
    <rect width="{WIDTH}" height="{height}" fill="url(#p-glowCorner)"/>
    <rect width="{WIDTH}" height="{height}" fill="url(#p-scan)"/>"""


def prompt(x: float, y: float, cmd: str, t: float) -> str:
    return (
        f'<text x="{x}" y="{y}" class="mono p-type" font-size="15" style="--d:.45s;--s:{len(cmd) + 2};--t:{t:.2f}s">'
        f'<tspan class="faint">$ </tspan><tspan class="txt">{escape(cmd)}</tspan></text>'
    )


def chip_width(label: str) -> float:
    return len(label) * CHAR_W + 30


def render_stack(x: float, y: float, t: float) -> tuple[str, float, float]:
    """Return (svg, height, time the last chip appears)."""
    out = []
    chip_x0 = x + 170
    for r, (label, accent, items) in enumerate(STACK):
        ry = y + r * ROW_H
        out.append(
            f'<text x="{x}" y="{ry + 19}" class="mono soft p-in" font-size="13.5" font-weight="700" style="--t:{t:.2f}s">{label}</text>'
        )
        cx = chip_x0
        for item in items:
            w = chip_width(item)
            out.append(
                f'<g class="p-in" style="--t:{t:.2f}s">'
                f'<rect x="{cx:.1f}" y="{ry}" width="{w:.1f}" height="{CHIP_H}" rx="6" fill="#0b0712" stroke="{accent}" stroke-opacity=".35"/>'
                f'<circle cx="{cx + 12:.1f}" cy="{ry + CHIP_H / 2}" r="3" fill="{accent}"/>'
                f'<text x="{cx + 22:.1f}" y="{ry + 18.5}" class="mono txt" font-size="12.5">{escape(item)}</text></g>'
            )
            cx += w + CHIP_GAP
            t += 0.035
        t += 0.08
    return "\n    ".join(out), len(STACK) * ROW_H, t


def build() -> str:
    parts = [embed(ASSETS / "banner.svg", "b-", 0, 0, WIDTH, BANNER_H, drop=tuple(BANNER_BACKGROUND))]

    # Terminal window holding whoami + stack.
    win_y = BANNER_H + 28
    tx = PAD + 28
    y = win_y + 36 + 40
    t = 4.6
    body = [prompt(tx, y, "whoami", t)]
    t += 0.6
    y += 34
    for para in ABOUT:
        for line in textwrap.wrap(para, ABOUT_WRAP):
            body.append(f'<text x="{tx}" y="{y}" class="sans p-in" font-size="17" fill="#d9d4e6" style="--t:{t:.2f}s">{escape(line)}</text>')
            y += 26
            t += 0.12
        y += 12
    y += 26
    body.append(prompt(tx, y, "cat stack.txt", t))
    t += 0.6
    stack_svg, stack_h, t = render_stack(tx, y + 20, t)
    body.append(stack_svg)
    y += 20 + stack_h + 4
    body.append(
        f'<g class="mono p-in" font-size="15" style="--t:{t:.2f}s"><text x="{tx}" y="{y + 12}" class="faint">$</text>'
        f'<rect x="{tx + 16}" y="{y}" width="9" height="16" fill="#d8b4fe" class="p-caret"/></g>'
    )
    win_h = y + 36 - win_y
    wx, ww = PAD, WIDTH - 2 * PAD
    window = f"""<rect x="{wx}" y="{win_y}" width="{ww}" height="{win_h}" rx="12" fill="#07040d" stroke="#a855f7" stroke-opacity=".28"/>
  <rect x="{wx}" y="{win_y}" width="{ww}" height="{win_h}" rx="12" fill="url(#p-glow)"/>
  <line x1="{wx}" y1="{win_y + 36}" x2="{wx + ww}" y2="{win_y + 36}" stroke="#a855f7" stroke-opacity=".16"/>
  <circle cx="{wx + 20}" cy="{win_y + 18}" r="5" fill="#ff5f57" opacity=".85"/>
  <circle cx="{wx + 37}" cy="{win_y + 18}" r="5" fill="#febc2e" opacity=".85"/>
  <circle cx="{wx + 54}" cy="{win_y + 18}" r="5" fill="#28c840" opacity=".85"/>
  <text x="{wx + 72}" y="{win_y + 22.5}" class="mono faint" font-size="12">tiago@<tspan class="soft">whyn0t101</tspan>: ~/about</text>
  {chr(10).join("  " + b for b in body)}"""
    parts.append(window)

    # Stats cards, scaled to share the row with a gap.
    sy = win_y + win_h + 28
    gap = 24
    cw = (WIDTH - 2 * PAD - gap) / 2
    ch = cw * CARD_H / CARD_W
    parts.append(prompt(PAD + 4, sy + 14, "gh stats", t - 0.2))
    sy += 30
    parts.append(embed(ASSETS / "stats.svg", "s-", PAD, sy, cw, ch, t))
    parts.append(embed(ASSETS / "languages.svg", "l-", PAD + cw + gap, sy, cw, ch, t))
    sy += ch + 34
    parts.append(
        f'<text x="{WIDTH / 2}" y="{sy}" class="mono faint p-in" font-size="12.5" text-anchor="middle" style="--t:{t + 1.2:.2f}s">'
        f'stats refresh daily via GitHub Actions  ·  <tspan class="soft">whyn0t101.github.io</tspan></text>'
    )
    height = round(sy + 30)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" role="img" aria-label="Tiago Pereira — Computer Engineer, MSc Cybersecurity and Digital Forensics. About, stack and GitHub stats.">
  <title>Tiago Pereira — Computer Engineer · Cybersecurity &amp; Forensics</title>
  <style>{STYLE.replace("{loop}", str(HEX_ROWS * HEX_ROW_H))}</style>
  <defs>
    <radialGradient id="p-glow" cx="100%" cy="0%" r="80%">
      <stop offset="0" stop-color="#581c87" stop-opacity=".3"/>
      <stop offset="1" stop-color="#581c87" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="p-glowTop" cx="50%" cy="-10%" r="85%">
      <stop offset="0" stop-color="#581c87" stop-opacity=".55"/>
      <stop offset=".6" stop-color="#581c87" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="p-glowCorner" cx="100%" cy="100%" r="70%">
      <stop offset="0" stop-color="#3b0764" stop-opacity=".45"/>
      <stop offset="1" stop-color="#3b0764" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="p-hexFade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity=".25"/>
      <stop offset=".55" stop-color="#fff" stop-opacity="1"/>
      <stop offset="1" stop-color="#fff" stop-opacity=".6"/>
    </linearGradient>
    <mask id="p-hexMask"><rect width="{WIDTH}" height="{height}" fill="url(#p-hexFade)"/></mask>
    <pattern id="p-scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect y="3" width="4" height="1" fill="#000" opacity=".22"/>
    </pattern>
    <clipPath id="p-frame"><rect width="{WIDTH}" height="{height}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#p-frame)">
    {background(height)}
  </g>
  {chr(10).join("  " + p for p in parts).lstrip()}
  <rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="16" fill="none" stroke="#a855f7" stroke-opacity=".22"/>
</svg>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
