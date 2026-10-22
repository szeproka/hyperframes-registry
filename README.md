# HyperFrames registry, patched

A copy of the official [HyperFrames](https://github.com/heygen-com/hyperframes) catalog
(`registry/` from `heygen-com/hyperframes`, Apache-2.0, see `LICENSE`) with fixes for items that
do not play, and a preview image for every item.

## Use it

In a HyperFrames project's `hyperframes.json`:

```json
"registry": "https://raw.githubusercontent.com/szeproka/hyperframes-registry/main/registry"
```

Studio's Catalog tab and `hyperframes add` then read this registry instead of the official one.

## What differs from upstream

| Item | Problem upstream | Fix |
| --- | --- | --- |
| `us-map` | Builds its timeline inside `fetch(...).then`, so renders show an empty background | Map geometry shipped as `assets/data/us-atlas-states-10m.js`, timeline built synchronously (same approach as upstream PR #3953) |
| `vfx-magnetic` | `texElementImage2D` now takes `(target, internalformat, element)`; the 6-argument call throws | Uses the 3-argument form when available, the old one otherwise |
| `vfx-shatter` | `drawElementImage` before the first paint throws "No cached paint record", the runtime fails | Capture skipped until the canvas has painted, then refreshed from `onpaint` |
| Previews | 334 of 448 items have no poster, or a poster/video URL that answers 403 | Posters rendered from each item's own demo, stored in `previews/`; dead video links removed |

Everything else is unchanged from upstream commit noted in `UPSTREAM`.
