"""Render an honest, animated snake that crosses every real contribution cell."""
from collections import defaultdict
from pathlib import Path
import re
import sys

svg_path = Path(sys.argv[1])
source = svg_path.read_text(encoding="utf-8")
if "Generated with https://github.com/Platane/snk" not in source:
    raise SystemExit("Expected Platane/snk input")

levels = {
    match.group(1): int(match.group(2)[1:])
    for match in re.finditer(
        r"\.c\.(c[0-9a-z]+)\{fill:var\(--(c[1-4])\);animation-name:\1\}",
        source,
    )
}
cells = []
for match in re.finditer(
    r'<rect class="c(?: (c[0-9a-z]+))?" x="([0-9.]+)" y="([0-9.]+)"[^>]*/>',
    source,
):
    cells.append((int(float(match.group(2))), int(float(match.group(3))),
                  levels.get(match.group(1), 0)))
if len(cells) < 100 or not any(level for _, _, level in cells):
    raise SystemExit("Contribution grid could not be read")

rows = defaultdict(list)
for cell in cells:
    rows[cell[1]].append(cell)
route = []
for row_index, y in enumerate(sorted(rows)):
    route.extend(sorted(rows[y], reverse=bool(row_index % 2)))
palette = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
duration = "26000ms"
points = [(-18, route[0][1])]
points += [(x, y) for x, y, _ in route]
points += [(route[-1][0] + 16 * offset, route[-1][1])
           for offset in range(1, 7)]
position = lambda index: 100 * (index + 1) / (len(points) - 1)

def gradient(fraction):
    stops = [(0.0, (250, 204, 21)), (0.35, (251, 146, 60)),
             (0.68, (236, 72, 153)), (1.0, (124, 58, 237))]
    for left, right in zip(stops, stops[1:]):
        if fraction <= right[0]:
            ratio = (fraction - left[0]) / (right[0] - left[0])
            rgb = tuple(round(a + (b - a) * ratio)
                        for a, b in zip(left[1], right[1]))
            return "#" + "".join(f"{channel:02x}" for channel in rgb)
    return "#7c3aed"

styles = [
    ".cell{shape-rendering:geometricPrecision;stroke:#d0d7de;stroke-width:.6px;"
    "width:12px;height:12px}",
    ".cell.food{animation-duration:" + duration +
    ";animation-timing-function:steps(1,end);animation-iteration-count:infinite}",
    ".snake{shape-rendering:geometricPrecision;stroke:#fff;stroke-width:.7px;"
    "filter:drop-shadow(0 0 4px #facc15);animation-duration:" + duration +
    ";animation-timing-function:linear,steps(1,end);"
    "animation-iteration-count:infinite}",
    ".pulse{fill:none;stroke:#f59e0b;stroke-width:2;opacity:0;"
    "pointer-events:none;transform-box:fill-box;transform-origin:center;"
    "animation-duration:" + duration +
    ";animation-timing-function:linear;animation-iteration-count:infinite}",
]
grid = []
eaten = []
for index, (x, y, level) in enumerate(route):
    if level:
        event = position(index)
        before = max(0.0, event - 0.015)
        after = min(100.0, event + 0.015)
        styles.append(
            f"@keyframes eat{index}{{0%,{before:.3f}%{{fill:{palette[level]}}}"
            f"{after:.3f}%,100%{{fill:{palette[0]}}}}}"
            f".cell.food.e{index}{{animation-name:eat{index}}}"
        )
        grid.append(
            f'<rect class="cell food e{index}" x="{x}" y="{y}" '
            f'width="12" height="12" rx="2" fill="{palette[level]}"/>'
        )
        eaten.append((event, x + 6, y + 6))
    else:
        grid.append(
            f'<rect class="cell" x="{x}" y="{y}" width="12" height="12" '
            f'rx="2" fill="{palette[0]}"/>'
        )

for segment in range(4):
    frames = []
    for index in range(len(points)):
        x, y = points[max(0, index - segment)]
        pct = 100 * index / (len(points) - 1)
        frames.append(
            f"{pct:.3f}%{{transform:translate({x - 1}px,{y - 1}px)}}"
        )
    styles.append(f"@keyframes move{segment}{{{''.join(frames)}}}")
    styles.append(
        f".snake.s{segment}{{animation-name:move{segment},snakeColor}}"
    )
color_frames = ["0%{fill:#facc15;filter:drop-shadow(0 0 4px #facc15)}"]
for index, (event, _, _) in enumerate(eaten):
    color = gradient((index + 1) / len(eaten))
    color_frames.append(
        f"{event:.3f}%{{fill:{color};"
        f"filter:drop-shadow(0 0 4px {color})}}"
    )
color_frames.append("100%{fill:#7c3aed;filter:drop-shadow(0 0 4px #7c3aed)}")
styles.append("@keyframes snakeColor{" + "".join(color_frames) + "}")

pulses = []
pulse_count = min(20, len(eaten))
for index in range(pulse_count):
    event, x, y = eaten[round((len(eaten) - 1) * (index + .5) / pulse_count)]
    before = max(0.0, event - .45)
    after = min(100.0, event + .9)
    styles.append(
        f"@keyframes pulse{index}{{"
        f"0%,{before:.3f}%{{opacity:0;transform:scale(.15)}}"
        f"{event:.3f}%{{opacity:.9;transform:scale(.6)}}"
        f"{after:.3f}%,100%{{opacity:0;transform:scale(1.5)}}"
        f"}}.pulse.p{index}{{animation-name:pulse{index}}}"
    )
    pulses.append(
        f'<circle class="pulse p{index}" cx="{x}" cy="{y}" r="8"/>'
    )

snake = [
    f'<rect class="snake s{index}" x="0" y="0" width="14" '
    f'height="14" rx="4" fill="#facc15"/>'
    for index in reversed(range(4))
]
result = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="144" '
    'viewBox="-16 -16 880 144" role="img" aria-labelledby="title desc">'
    '<title id="title">Sungsoo Kwon contribution snake</title>'
    '<desc id="desc">A yellow-to-purple snake crosses and eats real '
    'GitHub contribution cells on the original green grid.</desc>'
    '<style>' + "".join(styles) + '</style>' +
    "".join(grid) + "".join(snake) + "".join(pulses) + '</svg>'
)
svg_path.write_text(result, encoding="utf-8")
print(f"Rendered {len(cells)} real calendar cells and {len(eaten)} filled days")
