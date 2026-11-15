"""Generate assets/banner.svg, the animated profile header.

The look mirrors whyn0t101.github.io: near-black background, a scrolling
forensic hex dump behind a terminal window, purple accents. Run it again
after editing the text constants below.
"""

from pathlib import Path

WIDTH, HEIGHT = 1200, 400
OUT = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"

NAME = "Tiago Pereira"
ROLE = "Computer Engineer · Cybersecurity &amp; Forensics"
EDU = "MSc Cybersecurity &amp; Digital Forensics  ·  BSc Computer Engineering"
FOCUS = "malware analysis · digital forensics · pentesting · secure network design"

HEX_ROWS = 24
HEX_BYTES = 16


def byte_at(row: int, col: int) -> int:
    """Deterministic pseudo-random byte, same hash idea as the site's HexDump."""
    h = (row * 2654435761 + col * 40503 + 0x9E3779B9) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return h & 0xFF


def hex_line(row: int) -> str:
    data = [byte_at(row, c) for c in range(HEX_BYTES)]
    hexes = " ".join(f"{b:02x}" for b in data)
    ascii_col = "".join(chr(b) if 0x30 <= b <= 0x7A and chr(b).isalnum() else "." for b in data)
    return f"{row * 16:08x}  {hexes}  |{ascii_col}|"


def hex_block() -> str:
    # Two identical stacks so a translate of exactly one stack height loops seamlessly.
    row_h = 22
    lines = []
    for rep in range(2):
        for r in range(HEX_ROWS):
            y = (rep * HEX_ROWS + r) * row_h
            lines.append(f'<text x="0" y="{y}">{hex_line(r)}</text>')
    return "\n      ".join(lines), HEX_ROWS * row_h


def build() -> str:
    hex_lines, loop_h = hex_block()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="{NAME} — {ROLE}">
  <title>{NAME} — {ROLE}</title>
  <style>
    .mono {{ font-family: 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }}
    .sans {{ font-family: 'Hanken Grotesk', 'Segoe UI', system-ui, -apple-system, Helvetica, Arial, sans-serif; }}
    .hex {{ fill: #a855f7; opacity: .16; font-size: 14px; }}
    .scroll {{ animation: scroll 38s linear infinite; }}
    @keyframes scroll {{ from {{ transform: translateY(0); }} to {{ transform: translateY(-{loop_h}px); }} }}

    .faint {{ fill: #6b6480; }}
    .dim {{ fill: #9a92ad; }}
    .soft {{ fill: #c4b5fd; }}
    .user {{ fill: #4ade80; }}
    .path {{ fill: #60a5fa; }}

    .type {{ clip-path: inset(0 100% 0 0); animation: type var(--d, .8s) steps(var(--s, 20)) forwards; animation-delay: var(--t, 0s); }}
    @keyframes type {{ to {{ clip-path: inset(0 0 0 0); }} }}
    .fade {{ opacity: 0; animation: fade .6s ease-out forwards; animation-delay: var(--t, 0s); }}
    @keyframes fade {{ to {{ opacity: 1; }} }}
    .caret {{ animation: blink 1.05s steps(1) infinite; }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 50.01%, 100% {{ opacity: 0; }} }}
    .led {{ animation: pulse 2.4s ease-in-out infinite; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}

    @media (prefers-reduced-motion: reduce) {{
      .scroll, .caret, .led {{ animation: none; }}
      .type {{ animation: none; clip-path: none; }}
      .fade {{ animation: none; opacity: 1; }}
    }}
  </style>
  <defs>
    <radialGradient id="glowTop" cx="50%" cy="-10%" r="85%">
      <stop offset="0" stop-color="#581c87" stop-opacity=".55"/>
      <stop offset=".6" stop-color="#581c87" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowCorner" cx="100%" cy="100%" r="70%">
      <stop offset="0" stop-color="#3b0764" stop-opacity=".45"/>
      <stop offset="1" stop-color="#3b0764" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff"/>
      <stop offset=".55" stop-color="#c4b5fd"/>
      <stop offset="1" stop-color="#a855f7"/>
    </linearGradient>
    <linearGradient id="termFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0f0a18" stop-opacity=".92"/>
      <stop offset="1" stop-color="#090610" stop-opacity=".95"/>
    </linearGradient>
    <linearGradient id="hexFade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity=".25"/>
      <stop offset=".55" stop-color="#fff" stop-opacity="1"/>
      <stop offset="1" stop-color="#fff" stop-opacity=".6"/>
    </linearGradient>
    <mask id="hexMask"><rect width="{WIDTH}" height="{HEIGHT}" fill="url(#hexFade)"/></mask>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect y="3" width="4" height="1" fill="#000" opacity=".22"/>
    </pattern>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="18"/>
    </filter>
    <clipPath id="frame"><rect width="{WIDTH}" height="{HEIGHT}" rx="16"/></clipPath>
  </defs>

  <g clip-path="url(#frame)">
    <rect width="{WIDTH}" height="{HEIGHT}" fill="#030106"/>
    <g mask="url(#hexMask)">
      <g class="mono hex scroll" transform="translate(560 18)">
      {hex_lines}
      </g>
    </g>
    <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glowTop)"/>
    <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glowCorner)"/>
    <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#scan)"/>

    <!-- terminal window -->
    <rect x="48" y="44" width="760" height="316" rx="12" fill="#a855f7" opacity=".18" filter="url(#glow)"/>
    <rect x="48" y="44" width="760" height="316" rx="12" fill="url(#termFill)" stroke="#a855f7" stroke-opacity=".28"/>
    <path d="M60 44h736a12 12 0 0 1 12 12v24H48V56a12 12 0 0 1 12-12z" fill="#ffffff" opacity=".02"/>
    <line x1="48" y1="80" x2="808" y2="80" stroke="#a855f7" stroke-opacity=".16"/>
    <circle cx="70" cy="62" r="5.5" fill="#ff5f57" opacity=".85"/>
    <circle cx="89" cy="62" r="5.5" fill="#febc2e" opacity=".85"/>
    <circle cx="108" cy="62" r="5.5" fill="#28c840" opacity=".85"/>
    <text x="130" y="66.5" class="mono faint" font-size="13">tiago@<tspan class="soft">whyn0t101</tspan>: ~</text>
    <g class="mono" font-size="12.5">
      <circle cx="694" cy="62" r="3.5" fill="#4ade80" class="led"/>
      <text x="704" y="66.5" class="dim">online</text>
    </g>

    <g class="mono" font-size="16">
      <text x="72" y="118" class="type" style="--d:.6s;--s:22;--t:.3s"><tspan class="user">tiago</tspan><tspan class="faint">@</tspan><tspan class="soft">whyn0t101</tspan><tspan class="faint">:</tspan><tspan class="path">~</tspan><tspan class="faint">$ </tspan><tspan fill="#e9e6f0">whoami</tspan></text>
    </g>
    <text x="70" y="182" class="sans fade" font-size="54" font-weight="800" letter-spacing="-1.5" fill="url(#name)" style="--t:1.1s">{NAME}</text>
    <text x="72" y="218" class="sans fade" font-size="22" font-weight="600" fill="#f2eef9" style="--t:1.5s">{ROLE}</text>
    <text x="72" y="244" class="mono fade dim" font-size="13.5" style="--t:1.8s">{EDU}</text>

    <g class="mono" font-size="14">
      <text x="72" y="286" class="type" style="--d:.5s;--s:16;--t:2.3s"><tspan class="faint">$ </tspan><tspan fill="#e9e6f0">cat focus.txt</tspan></text>
      <text x="72" y="310" class="type soft" style="--d:1.4s;--s:60;--t:3s">{FOCUS}</text>
    </g>
    <g class="mono fade" font-size="14" style="--t:4.4s">
      <text x="72" y="338" class="faint">$</text>
      <rect x="86" y="326" width="9" height="16" fill="#d8b4fe" class="caret"/>
    </g>
  </g>
  <rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="16" fill="none" stroke="#a855f7" stroke-opacity=".22"/>
</svg>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
