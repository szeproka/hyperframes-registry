#!/usr/bin/env python3
"""Refresh this patched registry from heygen-com/hyperframes and re-apply the fixes.

Steps: fetch upstream's registry/, replace ours with it, re-apply the item patches, give every item
a working poster (kept from a previous run, taken from the official preview video, or rendered with
the HyperFrames CLI), drop dead preview links, then commit and push.

Usage: python3 tools/refresh.py [--no-push] [--keep-work]
Needs: git, curl, ffmpeg/ffprobe, node and the `hyperframes` CLI on PATH.
"""
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import split_transitions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "registry")
PREVIEWS = os.path.join(ROOT, "previews")
WORK = os.path.expanduser("~/.cache/hyperframes-registry-refresh")
UPSTREAM_GIT = "https://github.com/heygen-com/hyperframes.git"
UPSTREAM_PARTS = ["blocks", "components", "examples", "catalog-artifact", "registry.json"]
# Previews go through raw.githubusercontent: jsDelivr's gh/...@main left cold files hanging 20 s
# and more (measured 2026-10-22), raw answers in ~0.3 s. Its .mp4 type is
# application/octet-stream, which Chrome still plays; browsers keep its files 5 min, then
# revalidate cheaply by ETag.
PREVIEW_BASE = "https://raw.githubusercontent.com/szeproka/hyperframes-registry/main/previews/"
VIDEO_BASE = PREVIEW_BASE
# Links written on 2026-10-22 pointed at jsDelivr; they are ours too and get rewritten.
LEGACY_PREVIEW_BASE = "https://cdn.jsdelivr.net/gh/szeproka/hyperframes-registry@main/previews/"
OUR_BASES = (PREVIEW_BASE, LEGACY_PREVIEW_BASE)
# Items never rendered for a preview: ascii-render-pass's render picked up a personal video of
# the owner's (2026-10-22), so it ships with no preview at all.
NO_PREVIEW = {"ascii-render-pass"}
TYPE_DIRS = {"hyperframes:block": "blocks", "hyperframes:component": "components"}


def log(msg):
    print(msg, flush=True)


def run(cmd, cwd=None, check=True, timeout=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
    return r


# ── 1. Upstream ────────────────────────────────────────────────────────────────

def fetch_upstream():
    up = os.path.join(WORK, "upstream")
    if not os.path.isdir(os.path.join(up, ".git")):
        shutil.rmtree(up, ignore_errors=True)
        os.makedirs(WORK, exist_ok=True)
        run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none", "--sparse", UPSTREAM_GIT, up])
        run(["git", "sparse-checkout", "set", "--no-cone"] + [f"/registry/{p}" + ("" if "." in p else "/") for p in UPSTREAM_PARTS], cwd=up)
    else:
        run(["git", "fetch", "--quiet", "--depth", "1", "origin", "main"], cwd=up)
        run(["git", "reset", "--quiet", "--hard", "origin/main"], cwd=up)
    head = run(["git", "log", "-1", "--format=%H (%cd)"], cwd=up).stdout.strip()
    return up, head


def replace_registry(up):
    for part in UPSTREAM_PARTS:
        dst = os.path.join(REG, part)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        elif os.path.exists(dst):
            os.remove(dst)
        src = os.path.join(up, "registry", part)
        (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, dst)


# ── 2. Item patches (each skips itself when upstream already fixed the item) ──────────

def patch_us_map():
    p = os.path.join(REG, "blocks/us-map/us-map.html")
    s = open(p).read()
    if "fetch(US_TOPO_URL)" not in s:
        return "upstream no longer fetches; skipped"
    a = s.index("fetch(US_TOPO_URL)")
    b = s.index(".then((us) => {", a)
    body = b + len(".then((us) => {")
    i, depth = body, 1
    while depth:
        depth += (s[i] == "{") - (s[i] == "}")
        i += 1
    j = i
    while s[j].isspace():
        j += 1
    if s[j] != ")":
        raise SystemExit("us-map: unexpected code shape around the fetch callback, patch needs updating")
    s = s[:a] + "((us) => {" + s[body:i] + ")(window.US_ATLAS_STATES_10M)" + s[j + 1:]
    tag = '<script src="https://cdn.jsdelivr.net/npm/topojson-client'
    if tag not in s:
        raise SystemExit("us-map: topojson-client script tag not found, patch needs updating")
    s = s.replace(tag, '<script src="assets/data/us-atlas-states-10m.js"></script>\n    ' + tag, 1)
    open(p, "w").write(s)
    os.makedirs(os.path.join(REG, "blocks/us-map/assets"), exist_ok=True)
    data = run(["curl", "-sfL", "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"]).stdout
    json.loads(data)
    with open(os.path.join(REG, "blocks/us-map/assets/us-atlas-states-10m.js"), "w") as f:
        f.write("window.US_ATLAS_STATES_10M = " + data.strip() + ";\n")
    m = os.path.join(REG, "blocks/us-map/registry-item.json")
    item = json.load(open(m))
    if not any(f["target"] == "assets/data/us-atlas-states-10m.js" for f in item["files"]):
        item["files"].append({"path": "assets/us-atlas-states-10m.js", "target": "assets/data/us-atlas-states-10m.js", "type": "hyperframes:asset"})
    write_json(m, item)
    return "map data bundled, timeline built synchronously"


def patch_vfx_magnetic():
    p = os.path.join(REG, "blocks/vfx-magnetic/vfx-magnetic.html")
    s = open(p).read()
    old = "gl.texElementImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, content);"
    if old not in s:
        return "old 6-argument call gone; skipped"
    anchor = "      // ── Capture + Render"
    if anchor not in s:
        raise SystemExit("vfx-magnetic: anchor comment not found, patch needs updating")
    s = s.replace(old, "uploadContent();")
    s = s.replace(anchor, """      // Current Chrome takes texElementImage2D(target, internalformat, element); older builds took 6 args.
      function uploadContent() {
        if (gl.texElementImage2D.length === 3) gl.texElementImage2D(gl.TEXTURE_2D, gl.RGBA8, content);
        else gl.texElementImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, content);
      }

""" + anchor, 1)
    open(p, "w").write(s)
    return "texElementImage2D: new 3-argument form"


def patch_vfx_shatter():
    p = os.path.join(REG, "blocks/vfx-shatter/vfx-shatter.html")
    s = open(p).read()
    if "No cached paint record" in s or "function refreshCapture" in s:
        return "already safe; skipped"
    pairs = [
        ("""      function capturePanels() {
        ctxA.clearRect(0, 0, W, H);
        ctxA.drawElementImage(panelA, 0, 0, W, H);
        ctxB.clearRect(0, 0, W, H);
        ctxB.drawElementImage(panelB, 0, 0, W, H);
      }""", """      // drawElementImage throws until the capture canvas has painted its children once,
      // so a capture before the first paint is skipped instead of crashing the runtime.
      function capturePanels() {
        try {
          ctxA.drawElementImage(panelA, 0, 0, W, H);
          ctxB.drawElementImage(panelB, 0, 0, W, H);
          return true;
        } catch (e) {
          return false;
        }
      }"""),
        ("""        capturePanels();
        texA.needsUpdate = true;
        texB.needsUpdate = true;

        if (renderState.phase === 0) {""", """        if (capturePanels()) {
          texA.needsUpdate = true;
          texB.needsUpdate = true;
        }

        if (renderState.phase === 0) {"""),
        ("""      setTimeout(function () {
        capturePanels();
        texA.needsUpdate = true;
        texB.needsUpdate = true;
        tl.seek(0);
      }, 0);""", """      function refreshCapture() {
        if (capturePanels()) {
          texA.needsUpdate = true;
          texB.needsUpdate = true;
          renderFrame(timeProxy.t);
        }
      }
      capA.onpaint = refreshCapture;
      capB.onpaint = refreshCapture;
      setTimeout(function () {
        if (capA.requestPaint) capA.requestPaint();
        if (capB.requestPaint) capB.requestPaint();
        refreshCapture();
        tl.seek(0);
      }, 0);"""),
    ]
    for old, new in pairs:
        if s.count(old) != 1:
            raise SystemExit("vfx-shatter: upstream code changed, patch needs updating")
        s = s.replace(old, new)
    open(p, "w").write(s)
    return "capture waits for the first paint"


PATCHES = [("us-map", patch_us_map), ("vfx-magnetic", patch_vfx_magnetic), ("vfx-shatter", patch_vfx_shatter)]


# ── 2b. Studio tabs ──────────────────────────────────────────────────────────────────

# Studio's catalog tabs only know a few tags; these rules add the one it looks for (originals kept).
TAG_RULES = [
    ("code-animation", {"code", "terminal", "vscode"}, set()),
    ("transition", {"transition-primitive", "transitions-dev-port"}, set()),
    ("social", {"mock-ui", "chat", "notification", "notifications", "social-proof", "testimonial", "social-overlay",
                "share-sheet", "avatar", "avatars", "lower-third"}, set()),
    ("data", {"data-viz", "stat", "stats", "counter", "gauge", "diagram", "flowchart", "finance", "telemetry"}, set()),
    ("shader", {"webgpu", "webgpu-shader", "vfx", "3d-motion", "ascii", "particles", "slit-scan", "svg-filter", "hologram", "canvas"},
     {"text-effects", "typography", "text"}),
    ("text-effect", {"typography", "text", "text-effects", "kinetic-type", "kinetic-text", "text-treatment", "letters",
                     "typewriter", "headline", "type", "wordmark", "title", "typing"}, {"carousel", "cursor"}),
    ("effect", {"effects", "cursor", "camera", "background", "pointer", "pointers", "gesture", "beat", "spring", "trail"}, {"character"}),
]

def studio_tab(tags):
    """The tab Studio's Catalog panel files an item under (its first matching tag, as Studio's own code does)."""
    t = set(tags or [])
    if not t: return "scenes"
    for name, keys in [("captions", {"captions", "caption-style"}), ("code-animation", {"code-animation"}), ("transitions", {"transition"}),
                       ("social", {"social", "overlay"}), ("data", {"data", "chart", "map"}), ("vfx", {"html-in-canvas", "webgl", "shader"}),
                       ("text-effects", {"text-effect"}), ("effects", {"effect", "grain", "vignette"})]:
        if t & keys: return name
    return "scenes"

def with_studio_tags(tags):
    """The item's tags plus, at most, the one tag that moves it out of the catch-all Scenes tab."""
    out = list(tags or [])
    for added, triggers, excludes in TAG_RULES:
        if studio_tab(out) != "scenes": break
        t = set(out)
        if t & triggers and not t & excludes and added not in t:
            out.append(added)
    return out


def apply_studio_tags():
    moved = 0
    for type_dir in ("blocks", "components"):
        for name in os.listdir(os.path.join(REG, type_dir)):
            path = os.path.join(REG, type_dir, name, "registry-item.json")
            if not os.path.exists(path):
                continue
            item = json.load(open(path))
            tags = with_studio_tags(item.get("tags"))
            if tags != (item.get("tags") or []):
                item["tags"] = tags
                write_json(path, item)
                moved += 1
    return moved


# ── 3. Previews ─────────────────────────────────────────────────────────────────

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def http_ok(url):
    r = run(["curl", "-s", "-o", "/dev/null", "-I", "-w", "%{http_code}", "--max-time", "20", url], check=False)
    return r.stdout.strip() == "200"


def contrast(png):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", png, "-vf", "scale=96:54,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return statistics.pstdev(raw) if raw else -1


def to_jpg(src, dst, seek=None):
    cmd = ["ffmpeg", "-v", "error", "-y"] + (["-ss", seek] if seek else []) + ["-i", src, "-frames:v", "1", "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", dst]
    subprocess.run(cmd, capture_output=True)
    return os.path.exists(dst)


def poster_from_video(url, dst):
    dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", url], check=False).stdout.strip() or "4"
    return to_jpg(url, dst, f"{float(dur) / 2:.2f}")


def render_project():
    proj = os.path.join(WORK, "render")
    if not os.path.isfile(os.path.join(proj, "hyperframes.json")):
        shutil.rmtree(proj, ignore_errors=True)
        env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
        subprocess.run(["hyperframes", "init", "render", "--non-interactive"], cwd=WORK, env=env, capture_output=True)
        # Install from this patched registry, so fixed items render fixed.
        cfg = json.load(open(os.path.join(proj, "hyperframes.json")))
        cfg["registry"] = "https://raw.githubusercontent.com/szeproka/hyperframes-registry/main/registry"
        write_json(os.path.join(proj, "hyperframes.json"), cfg)
    return proj


def host_page(src, cid, dur, w, h):
    return f"""<!doctype html><html lang="en"><head><meta charset="UTF-8" />
<style>html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden;background:#000}} #root{{position:relative;width:100%;height:100%}} #root > .clip{{position:absolute;inset:0}}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}">
<div class="clip" data-composition-id="{cid}" data-composition-src="{src}" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}"></div></div></body></html>"""


def prepare_page(name, type_dir):
    """Install the item in a scratch project and write an index.html that plays it as Studio would.
    Returns (project dir, duration) or None."""
    proj = render_project()
    r = run(["hyperframes", "add", name, "--json"], cwd=proj, check=False, timeout=300)
    try:
        written = [os.path.relpath(p, proj) for p in json.loads(r.stdout)["written"]]
    except (ValueError, KeyError):
        return None
    html_path = next((p for p in written if p.endswith(name + ".html")), None)
    if not html_path:
        return None
    item = json.load(open(os.path.join(REG, type_dir, name, "registry-item.json")))
    if type_dir == "components":
        demo = os.path.join(REG, type_dir, name, "demo.html")
        if not os.path.exists(demo):
            return None
        page = open(demo).read()
        page = re.sub(r'data-composition-src="\./[^"]+"', f'data-composition-src="{html_path}"', page)
        if re.search(r"<body[^>]*>\s*<template(?![^>]*data-slot)", page):
            dur = (re.search(r'data-duration="([0-9.]+)"', page) or [None, "5"])[1]
            page = host_page(html_path, name, dur, 1920, 1080)
    else:
        html = open(os.path.join(proj, html_path)).read()
        cid = (re.search(r'data-composition-id="([^"]+)"', html) or [None, name])[1]
        dims = item.get("dimensions") or {}
        page = host_page(html_path, cid, item.get("duration") or 5, dims.get("width", 1920), dims.get("height", 1080))
    open(os.path.join(proj, "index.html"), "w").write(page)
    return proj, float((re.search(r'data-duration="([0-9.]+)"', page) or [None, "5"])[1])


def render_poster(name, type_dir, dst):
    """Keep the richest of 3 frames."""
    prepared = prepare_page(name, type_dir)
    if not prepared:
        return False
    proj, dur = prepared
    tmp = os.path.join(WORK, "frames")
    shutil.rmtree(tmp, ignore_errors=True)
    times = ",".join(f"{dur * f:.2f}" for f in (0.4, 0.6, 0.8))
    subprocess.run(["hyperframes", "snapshot", "--at", times, "--no-end", "--timeout", "15000", "-o", tmp], cwd=proj, capture_output=True, timeout=300)
    frames = [os.path.join(tmp, f) for f in sorted(os.listdir(tmp)) if f.startswith("frame-")] if os.path.isdir(tmp) else []
    if not frames:
        return False
    best = max(frames, key=contrast)
    return to_jpg(best, dst)


def render_video(name, type_dir, dst):
    """Small looping hover preview: draft render, 640 px wide, at most 8 s, no audio."""
    prepared = prepare_page(name, type_dir)
    if not prepared:
        return False
    proj, _ = prepared
    # Transparent compositions export on white but show on black in Studio and in the posters: pin black.
    index = os.path.join(proj, "index.html")
    page = open(index).read()
    pin = "<style>html,body{background:#000 !important}</style>"
    if pin not in page:
        page = re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + pin, page, count=1) if re.search(r"<head[^>]*>", page) else pin + page
        open(index, "w").write(page)
    tmp = os.path.join(WORK, "preview-tmp.mp4")
    if os.path.exists(tmp):
        os.remove(tmp)
    subprocess.run(["hyperframes", "render", "--quality", "draft", "--fps", "24", "--workers", "1", "--quiet", "-o", tmp], cwd=proj, capture_output=True, timeout=900)
    if not (os.path.exists(tmp) and os.path.getsize(tmp)):
        return False
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-t", "8", "-an", "-vf", "scale='min(640,iw)':-2", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], capture_output=True)
    return os.path.exists(dst) and os.path.getsize(dst) > 0


def refresh_previews():
    items = []
    for type_dir in ("blocks", "components"):
        for name in sorted(os.listdir(os.path.join(REG, type_dir))):
            p = os.path.join(REG, type_dir, name, "registry-item.json")
            if os.path.exists(p):
                items.append((type_dir, name, p, json.load(open(p))))
    urls = sorted({u for _, _, _, it in items for k, u in (it.get("preview") or {}).items() if not u.startswith(OUR_BASES)})
    log(f"Checking {len(urls)} official preview links...")
    with ThreadPoolExecutor(24) as ex:
        ok = dict(zip(urls, ex.map(http_ok, urls)))
    os.makedirs(PREVIEWS, exist_ok=True)
    kept = from_video = rendered = failed = videos = 0
    todo = []
    for type_dir, name, path, it in items:
        if name in NO_PREVIEW:
            it.pop("preview", None)
            write_json(path, it)
            continue
        pv = dict(it.get("preview") or {})
        if "video" in pv and not pv["video"].startswith(OUR_BASES) and not ok.get(pv["video"], False):
            pv.pop("video")
        if "video" not in pv or pv["video"].startswith(OUR_BASES):
            video = os.path.join(PREVIEWS, name + ".mp4")
            if os.path.exists(video) or render_video(name, type_dir, video):
                pv["video"] = VIDEO_BASE + name + ".mp4"
                videos += 1
        poster = pv.get("poster")
        if poster and not poster.startswith(OUR_BASES) and ok.get(poster, False):
            it["preview"] = pv
            write_json(path, it)
            continue
        todo.append((type_dir, name, path, it, pv))
    log(f"{len(todo)} items need our own poster")
    for i, (type_dir, name, path, it, pv) in enumerate(todo, 1):
        dst = os.path.join(PREVIEWS, name + ".jpg")
        how = "kept"
        if os.path.exists(dst):
            kept += 1
        elif "video" in pv and poster_from_video(pv["video"], dst):
            from_video += 1
            how = "from video"
        elif render_poster(name, type_dir, dst):
            rendered += 1
            how = "rendered"
        else:
            failed += 1
            how = "FAILED"
        if os.path.exists(dst):
            pv["poster"] = PREVIEW_BASE + name + ".jpg"
        if how != "kept":
            log(f"  [{i}/{len(todo)}] {name}: {how}")
        it["preview"] = {k: pv[k] for k in ("video", "poster") if k in pv}
        write_json(path, it)
    names = {name for _, name, _, _ in items}
    for f in os.listdir(PREVIEWS):
        if f.endswith((".jpg", ".mp4")) and f[:-4] not in names:
            os.remove(os.path.join(PREVIEWS, f))
    log(f"    hover videos of our own: {videos}")
    return kept, from_video, rendered, failed


# ── 4. Publish ──────────────────────────────────────────────────────────────────

def publish(head, push):
    with open(os.path.join(ROOT, "UPSTREAM"), "w") as f:
        f.write(f"heygen-com/hyperframes {head}\n")
    run(["git", "add", "-A"], cwd=ROOT)
    if run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=False).returncode == 0:
        log("No change since the last refresh.")
        return
    stat = run(["git", "diff", "--cached", "--shortstat"], cwd=ROOT).stdout.strip()
    run(["git", "commit", "-q", "-m", f"Refresh from upstream {head.split()[0][:12]}"], cwd=ROOT)
    log(f"Committed: {stat}")
    if push:
        run(["git", "push", "-q", "origin", "main"], cwd=ROOT, timeout=1800)
        cache = os.path.expanduser("~/.hyperframes/cache")
        for f in os.listdir(cache) if os.path.isdir(cache) else []:
            if "szeproka_hyperframes_registry" in f:
                os.remove(os.path.join(cache, f))
        log("Pushed. Studio reads the new catalog on the next start of a project (GitHub may take ~5 min).")
    else:
        log("Not pushed (--no-push).")


def main():
    push = "--no-push" not in sys.argv
    if run(["git", "status", "--porcelain"], cwd=ROOT).stdout.strip():
        raise SystemExit("The registry folder has uncommitted changes; commit or discard them first.")
    log("1/4 Fetching HeyGen's registry...")
    up, head = fetch_upstream()
    log(f"    upstream {head}")
    replace_registry(up)
    log("2/4 Re-applying fixes...")
    for name, fn in PATCHES:
        log(f"    {name}: {fn()}")
    log(f"    transitions split: {len(split_transitions.split())} blocks, one per transition")
    log(f"    Studio tabs: {apply_studio_tags()} items given the tag their tab needs")
    log("3/4 Previews...")
    kept, from_video, rendered, failed = refresh_previews()
    log(f"    posters: {kept} kept, {from_video} from official videos, {rendered} rendered, {failed} failed")
    log("4/4 Publishing...")
    publish(head, push)
    if "--keep-work" not in sys.argv:
        shutil.rmtree(os.path.join(WORK, "render"), ignore_errors=True)
        shutil.rmtree(os.path.join(WORK, "frames"), ignore_errors=True)
    log("Done.")


if __name__ == "__main__":
    main()
