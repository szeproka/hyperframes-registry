"""Trims every transition preview so the move starts at most LEAD seconds in and the loop ends
TAIL seconds after it settles: no long wait on a still frame before or after.

Motion is found by comparing each frame with the one before, at 64x36 in gray. Already trimmed
previews are left alone, so running it again changes nothing.
Usage: python3 tools/trim_transition_previews.py [name ...]   (default: the Transitions tab)
Prints one line per item: name, then "trimmed a-b of c", "kept" or "skipped (...)".
"""

import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import refresh  # noqa: E402

LEAD = 0.5
TAIL = 0.5
W, H = 64, 36
# Mean gray-level change per pixel above which a frame counts as moving (encoder noise is ~0.1).
MOTION = 0.6


def items(names):
    for path in sorted(glob.glob(os.path.join(refresh.REG, "*", "*", "registry-item.json"))):
        item = json.load(open(path))
        if names and item["name"] not in names:
            continue
        if not names and "hf-tab:transitions" not in item.get("tags", []):
            continue
        yield item


def frame_rate(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", video], capture_output=True, text=True, check=True).stdout
    num, den = out.split()[0].strip(",").split("/")
    return float(num) / float(den)


def motion_span(video):
    """(first moving frame, last moving frame, frame count, fps), or None if nothing moves."""
    fps = frame_rate(video)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    frames = [raw[i:i + W * H] for i in range(0, len(raw) - W * H + 1, W * H)]
    moving = [i for i in range(1, len(frames))
              if sum(abs(a - b) for a, b in zip(frames[i], frames[i - 1])) / (W * H) > MOTION]
    if not moving:
        return None
    return moving[0] - 1, moving[-1], len(frames), fps


def trim(item):
    video = (item.get("preview") or {}).get("video")
    if not video:
        return "skipped (no preview)"
    path = os.path.join(refresh.PREVIEWS, video.rsplit("/", 1)[-1])
    if not os.path.exists(path):
        return "skipped (file missing)"
    span = motion_span(path)
    if span is None:
        return "skipped (no motion)"
    first, last, count, fps = span
    start = max(0, first - round(LEAD * fps))
    end = min(count, last + 1 + round(TAIL * fps))
    if start == 0 and end == count:
        return "kept"
    tmp = path + ".trim.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-an",
                    "-vf", f"trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, path)
    return f"trimmed {start / fps:.2f}-{end / fps:.2f} of {count / fps:.2f}s"


if __name__ == "__main__":
    for it in items(set(sys.argv[1:])):
        print(it["name"], trim(it), flush=True)
