"""Split HeyGen's grouped `transitions-*` showcase blocks into one block per transition.

Each upstream showcase plays a title card, then several transitions between two scenes (each with
a name label), then an outro card. Every new block keeps the showcase's HTML but plays only one
transition's time window, with the title card, labels and outro hidden, so a transition starts on
its first scene instead of a title animation. The grouped blocks leave the registry.

The windows were read from each showcase's GSAP timeline (2026-10-22, upstream 2faf660): a window
runs from the moment its demo resets the scenes to the next demo or to the outro. When upstream
changes a showcase, `split()` refuses rather than cutting at the wrong times.
"""

import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "registry")
BLOCKS = os.path.join(REG, "blocks")

# showcase -> (its upstream duration in seconds, [(start, end, title), ...])
SPLITS = {
    "transitions-3d": (11, [(3, 6.5, "3D Card Flip")]),
    "transitions-blur": (20, [(3, 7.5, "Blur Through"), (7.5, 12, "Directional Blur"), (12, 16.5, "Calm Blur Through")]),
    "transitions-cover": (21, [(3, 8, "Staggered Blocks"), (8, 13, "Horizontal Blinds"), (13, 18.2, "Vertical Blinds")]),
    "transitions-destruction": (14, [(3, 10.5, "Page Burn")]),
    "transitions-dissolve": (24, [(3, 7.5, "Crossfade"), (7.5, 12, "Blur Crossfade"), (12, 16.5, "Focus Pull"), (16.5, 21, "Color Dip")]),
    "transitions-distortion": (21, [(3, 8, "Glitch Distortion"), (8, 13, "Chromatic Aberration"), (13, 18, "Ripple Distortion")]),
    "transitions-grid": (11, [(3, 8, "Grid Dissolve")]),
    "transitions-light": (21, [(3, 8, "Light Leak"), (8, 13, "Overexposure Burn"), (13, 18.2, "Film Burn")]),
    "transitions-mechanical": (15, [(3, 7.5, "Shutter"), (7.5, 12, "Clock Wipe")]),
    "transitions-other": (20, [(3, 7.5, "Flash Cut"), (7.5, 12, "Gravity Drop"), (12, 16.5, "Morph Circle")]),
    "transitions-push": (24, [(3, 7.5, "Push Slide"), (7.5, 12, "Vertical Push"), (12, 16.5, "Elastic Push"), (16.5, 21, "Squeeze")]),
    "transitions-radial": (20, [(3, 6.5, "Circle Iris"), (6.5, 10, "Diamond Iris"), (10, 13.5, "Diagonal Split")]),
    "transitions-scale": (15, [(3, 7.5, "Zoom Through"), (7.5, 12, "Zoom Out")]),
}

HIDE_CSS = (
    "\n    <style>\n"
    "      /* One transition only: no showcase title, name labels or outro. */\n"
    '      #title-card, #outro-card, #outro, [id^="info"] { display: none !important; }\n'
    "    </style>\n"
)
REGISTER = 'window.__timelines["main"] = tl;'


def slug(title):
    return "transition-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def windowed(html, start, end):
    length = round(end - start, 3)
    # Stop one frame short: the next demo resets the scenes exactly at `end`.
    stop = round(end - 1 / 30, 3)
    if html.count(REGISTER) != 1 or "</head>" not in html:
        raise ValueError("unexpected showcase layout")
    html = re.sub(r'data-duration="[0-9.]+"', f'data-duration="{length}"', html, count=1)
    html = html.replace("</head>", HIDE_CSS + "  </head>", 1)
    # The showcase timeline keeps every tween, so seeking into the window lands in exactly the
    # state the showcase had there; the window plays that stretch from 0.
    return html.replace(
        REGISTER,
        "var hfWindow = gsap.timeline({ paused: true });\n"
        f'        hfWindow.add(tl.tweenFromTo({start}, {stop}, {{ ease: "none" }}));\n'
        '        window.__timelines["main"] = hfWindow;',
    )


def split():
    """Returns the names of the blocks written. Removes the showcases it split."""
    index_path = os.path.join(REG, "registry.json")
    index = json.load(open(index_path))
    written, removed = [], set()
    for group, (upstream_duration, windows) in SPLITS.items():
        src_dir = os.path.join(BLOCKS, group)
        manifest_path = os.path.join(src_dir, "registry-item.json")
        if not os.path.exists(manifest_path):
            continue
        manifest = json.load(open(manifest_path))
        if manifest.get("duration") != upstream_duration:
            raise SystemExit(f"{group}: upstream changed (duration {manifest.get('duration')}); re-read its windows")
        html = open(os.path.join(src_dir, group + ".html")).read()
        for start, end, title in windows:
            name = slug(title)
            out_dir = os.path.join(BLOCKS, name)
            os.makedirs(out_dir, exist_ok=True)
            open(os.path.join(out_dir, name + ".html"), "w").write(windowed(html, start, end))
            item = {k: v for k, v in manifest.items() if k != "preview"}
            item.update(
                name=name,
                title=title,
                description=f"{title} transition between two scenes",
                duration=round(end - start, 3),
                files=[{"path": name + ".html", "target": f"compositions/{name}.html", "type": "hyperframes:composition"}],
                tags=[t for t in manifest.get("tags", []) if t != "showcase"],
            )
            with open(os.path.join(out_dir, "registry-item.json"), "w") as f:
                json.dump(item, f, indent=2, ensure_ascii=False)
                f.write("\n")
            written.append(name)
        shutil.rmtree(src_dir)
        removed.add(group)
    items = [i for i in index["items"] if i["name"] not in removed]
    known = {i["name"] for i in items}
    items += [{"name": n, "type": "hyperframes:block"} for n in written if n not in known]
    index["items"] = items
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return written


if __name__ == "__main__":
    print("\n".join(split()))
