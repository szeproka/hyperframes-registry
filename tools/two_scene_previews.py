"""Previews for the slot-based scene transitions, shown like every other transition: full frame,
navy ONE scene to orange TWO scene, nothing else on screen.

Each item is mounted at 1920x1080 in the render project with its own demo's variables, its two
scenes passed as <template data-slot> in the host page. iris-reveal and whip-pan-cut also have
scene slots, but inside the component; filling them that way kept their default wireframes
(2026-10-22), so they keep their own previews.
Usage: python3 tools/two_scene_previews.py [name ...]
"""

import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh  # noqa: E402

FONT = 'font-family: "Inter", "Helvetica Neue", Arial, sans-serif'


def scene(word, sub, bg, ink):
    return (
        f'<div style="position:absolute;inset:0;background:{bg};display:flex;flex-direction:column;'
        f'align-items:center;justify-content:center;gap:8px;{FONT}">'
        f'<div style="font-size:220px;font-weight:900;color:{ink};line-height:1">{word}</div>'
        f'<div style="font-size:30px;font-weight:700;letter-spacing:.3em;color:#fff;opacity:.85">{sub}</div></div>'
    )


ONE = scene("ONE", "SCENE A", "#1b263b", "#2b3852")
TWO = scene("TWO", "SCENE B", "#e07a5f", "#e9957f")

# name: (slot names A, B, how slots are filled, duration, variable values from the item's demo)
ITEMS = {
    "torn-paper-rip": ("torn-paper-rip-from", "torn-paper-rip-to", "template", 2.4,
                       {"direction": "right-to-left", "roughness": 72}),
    "halftone-dissolve": ("halftone-dissolve-a", "halftone-dissolve-b", "template", 3.5,
                          {"direction": "center", "dot_size": "large", "dissolve_at": 1.0, "accent": "blue"}),
}


def fill_inline_slots(html, slot_a, slot_b):
    """Lays ONE / TWO over each slot element's default wireframe. The component's markup sits in a
    <template> whose contents alone get cloned, so the style goes inside it too."""
    for slot, content in ((slot_a, ONE), (slot_b, TWO)):
        pattern = re.compile(r'(<div class="[^"]*" data-slot="' + slot + r'">)')
        if len(pattern.findall(html)) != 1:
            raise ValueError(f"slot {slot} not found once")
        html = pattern.sub(lambda m, c=content: m.group(1) + c, html, count=1)
    css = (
        "<style>[data-slot]{position:absolute;inset:0;overflow:hidden}"
        " [data-slot] > :not([style*='position:absolute;inset:0;background']){display:none!important}</style>"
    )
    if html.count("<template>") < 1:
        raise ValueError("no <template> wrapper")
    return html.replace("<template>", "<template>" + css, 1)


def host(name, slot_a, slot_b, mode, dur, values):
    templates = ""
    if mode == "template":
        templates = f'<template data-slot="{slot_a}">{ONE}</template><template data-slot="{slot_b}">{TWO}</template>'
    vals = json.dumps(values).replace("'", "&#39;")
    return f"""<!doctype html><html lang="en"><head><meta charset="UTF-8" />
<style>html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#000}} #root{{position:relative;width:100%;height:100%}} #root > .clip{{position:absolute;inset:0}}</style></head>
<body>{templates}<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="1920" data-height="1080">
<div class="clip" data-composition-id="{name}" data-composition-src="compositions/{name}.html" data-variable-values='{vals}' data-start="0" data-duration="{dur}" data-width="1920" data-height="1080"></div></div></body></html>"""


def render(name):
    slot_a, slot_b, mode, dur, values = ITEMS[name]
    proj = refresh.render_project()
    src = os.path.join(refresh.REG, "components", name, name + ".html")
    html = open(src).read()
    if mode == "inline":
        html = fill_inline_slots(html, slot_a, slot_b)
    os.makedirs(os.path.join(proj, "compositions"), exist_ok=True)
    open(os.path.join(proj, "compositions", name + ".html"), "w").write(html)
    open(os.path.join(proj, "index.html"), "w").write(host(name, slot_a, slot_b, mode, dur, values))
    tmp = os.path.join(refresh.WORK, "two-scene.mp4")
    if os.path.exists(tmp):
        os.remove(tmp)
    subprocess.run(["hyperframes", "render", "--quality", "draft", "--fps", "24", "--workers", "1", "--quiet", "-o", tmp],
                   cwd=proj, capture_output=True, timeout=900)
    if not os.path.exists(tmp):
        return False
    mp4 = os.path.join(refresh.PREVIEWS, name + ".mp4")
    jpg = os.path.join(refresh.PREVIEWS, name + ".jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-an", "-vf", "scale=640:-2", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur * 0.55:.2f}", "-i", tmp, "-frames:v", "1",
                    "-vf", "scale=1280:-2", "-q:v", "3", jpg], check=True)
    path = os.path.join(refresh.REG, "components", name, "registry-item.json")
    item = json.load(open(path))
    item["preview"] = {"video": refresh.VIDEO_BASE + name + ".mp4", "poster": refresh.PREVIEW_BASE + name + ".jpg"}
    refresh.write_json(path, item)
    return True


if __name__ == "__main__":
    for n in sys.argv[1:] or ITEMS:
        print(n, "ok" if render(n) else "FAILED", flush=True)
