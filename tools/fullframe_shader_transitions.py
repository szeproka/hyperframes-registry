"""Make HeyGen's 14 "Shader transition" blocks full frame, between the ONE / TWO scenes.

Upstream plays each WebGL transition in a 1200 px panel next to a 720 px spec sheet (name,
prompt, description). That sheet would ship into any video the block is added to. This patch
widens the GL panel to 1920 px, hides the sheet, grid, divider and counter, and swaps the two
captured scenes for the navy ONE and orange TWO scenes the split transitions use, so every
transition in the Catalog is shown the same way. Idempotent; refuses an unexpected layout.
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS = os.path.join(ROOT, "registry", "blocks")
MARK = "<!-- hf: full-frame shader transition -->"

HIDE_CSS = (
    # Bebas Neue: the block loads it before the scene capture; a font loaded later would be
    # missing from the captured texture.
    "\n        /* hf: full frame, no spec sheet */\n"
    "        .bp-grid, .bp-divider, .bp-number, .bp-right { display: none !important; }\n"
    "        .scene { flex-direction: column; gap: 4px; }\n"
    '        .scene .scene-label { font-family: "Bebas Neue", sans-serif; font-size: 220px;'
    " letter-spacing: 0.02em; opacity: 1; line-height: 1; }\n"
    '        .scene .scene-sub { font-family: "Bebas Neue", sans-serif; font-size: 40px;'
    " letter-spacing: 0.3em; color: #ffffff; opacity: 0.85; }\n"
)

SCENES = (
    '<div id="s1" class="scene" style="background: #1b263b">\n'
    '        <div class="scene-label" style="color: #2b3852">ONE</div>\n'
    '        <div class="scene-sub">SCENE A</div>\n'
    "      </div>\n"
    '      <div id="s2" class="scene" style="background: #e07a5f; opacity: 0">\n'
    '        <div class="scene-label" style="color: #e9957f">TWO</div>\n'
    '        <div class="scene-sub">SCENE B</div>\n'
    "      </div>"
)

SCENE_BLOCK = re.compile(r'<div id="s1" class="scene".*?</div>\s*</div>\s*<div id="s2" class="scene".*?</div>\s*</div>', re.S)


def shader_transitions():
    for name in sorted(os.listdir(BLOCKS)):
        path = os.path.join(BLOCKS, name, "registry-item.json")
        if os.path.exists(path) and json.load(open(path)).get("description", "").startswith("Shader transition"):
            yield name


def patch_one(html):
    if MARK in html:
        return html
    if html.count('class="bp-right"') != 1 or len(SCENE_BLOCK.findall(html)) != 1:
        raise ValueError("unexpected shader transition layout")
    html = SCENE_BLOCK.sub(lambda _: SCENES, html, count=1)
    html = html.replace("1200", "1920")
    last = html.rindex("</style>")
    html = html[:last] + HIDE_CSS + "      " + html[last:]
    return html.replace("<body", MARK + "\n  <body", 1)


def patch():
    """Returns how many blocks were patched now."""
    patched = 0
    for name in shader_transitions():
        path = os.path.join(BLOCKS, name, name + ".html")
        html = open(path).read()
        new = patch_one(html)
        if new != html:
            open(path, "w").write(new)
            patched += 1
    return patched


if __name__ == "__main__":
    print(patch())
