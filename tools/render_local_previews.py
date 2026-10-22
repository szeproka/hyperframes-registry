"""Render poster + hover video for blocks that exist only in this checkout (not yet pushed).

refresh.py installs items with `hyperframes add`, which only reads an https registry; a block
written locally (e.g. by split_transitions.py) is copied into the render project instead.
Usage: python3 tools/render_local_previews.py name [name ...]
Writes previews/<name>.jpg and .mp4 and the item's `preview` links. LOOK at every result before
pushing: a render once picked up a personal video (see NO_PREVIEW in refresh.py).
"""

import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh  # noqa: E402


def prepare_local(name, type_dir):
    proj = refresh.render_project()
    src = os.path.join(refresh.REG, type_dir, name, name + ".html")
    if not os.path.exists(src):
        return None
    rel = f"compositions/{name}.html"
    os.makedirs(os.path.join(proj, "compositions"), exist_ok=True)
    shutil.copy(src, os.path.join(proj, rel))
    item = json.load(open(os.path.join(refresh.REG, type_dir, name, "registry-item.json")))
    html = open(src).read()
    cid = (re.search(r'data-composition-id="([^"]+)"', html) or [None, name])[1]
    dims = item.get("dimensions") or {}
    page = refresh.host_page(rel, cid, item.get("duration") or 5, dims.get("width", 1920), dims.get("height", 1080))
    open(os.path.join(proj, "index.html"), "w").write(page)
    return proj, float(item.get("duration") or 5)


refresh.prepare_page = prepare_local


def main(names):
    for i, name in enumerate(names, 1):
        path = os.path.join(refresh.REG, "blocks", name, "registry-item.json")
        item = json.load(open(path))
        jpg = os.path.join(refresh.PREVIEWS, name + ".jpg")
        mp4 = os.path.join(refresh.PREVIEWS, name + ".mp4")
        preview = {}
        if refresh.render_video(name, "blocks", mp4):
            preview["video"] = refresh.VIDEO_BASE + name + ".mp4"
        if refresh.render_poster(name, "blocks", jpg):
            preview["poster"] = refresh.PREVIEW_BASE + name + ".jpg"
        if preview:
            item["preview"] = preview
            refresh.write_json(path, item)
        refresh.log(f"[{i}/{len(names)}] {name}: {', '.join(preview) or 'FAILED'}")


if __name__ == "__main__":
    main(sys.argv[1:])
