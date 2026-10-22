"""One Catalog tab per item, for the Studio fork's 13 tabs (owner's call, 2026-10-22).

Upstream tags mix purpose and technique ("transition" on a badge pop, "shader" on a cut), so the
Catalog's tabs were a mess. Each item gets exactly one `hf-tab:<id>` tag; the fork's Studio files
items by it. Explicit lists win; anything new from upstream falls back to `by_tags`.
"""

TABS = [
    ("transitions", "Transitions"),  # cuts between shots
    ("elements", "Elements"),  # interface pieces changing state: badge, toggle, menu, card
    ("text", "Text"),  # kinetic type, titles, text reveals
    ("captions", "Captions"),  # subtitle styles
    ("callouts", "Callouts"),  # lower thirds, annotations, cursors, CTAs over footage
    ("social", "Social"),  # social posts, chat, notifications, proof
    ("data", "Data"),  # charts, counters, maps, diagrams
    ("code", "Code"),  # code and terminals
    ("mockups", "Mockups"),  # devices, app screens, product demos, galleries, comparisons
    ("backgrounds", "Backgrounds"),  # gradients, textures, patterns, ambient fields
    ("looks", "Looks & FX"),  # grain, light, glitch, distortion laid over the picture
    ("3d", "3D & Camera"),  # 3D objects and titles, camera moves
    ("scenes", "Scenes"),  # whole scenes: intros, outros, logo stings, promos
]

_LISTS = {
    "transitions": """
        beat-freeze-cut chromatic-radial-split cinematic-zoom cross-warp-morph domain-warp-dissolve
        editorial-flash-overlay flash-through-white glitch gravitational-lens hw-scribble-transition
        light-leak mk-clone-wall-transition ridged-burn ripple-waves sdf-iris swirl-vortex
        thermal-distortion whip-pan chromatic-aberration-wipe curtain-reveal cut-the-curve
        directional-wipe fade-through grid-pixelate-wipe halftone-dissolve iris-reveal match-cut
        paper-collage-reveal parallax-device-dive parallax-unzoom parallax-zoom rubber-band-bumper
        torn-paper-rip type-match-cut whip-pan-cut zoom-through-transition
    """,
    "elements": """
        avatar-group-hover badge-pop card-resize icon-swap input-feedback menu-morph
        micro-transitions morph-swap number-pop-in page-slide panel-reveal skeleton-reveal
        success-check tabs-slide-indicator tilt-card gesture-tap toggle-flip pull-to-refresh
        swipe-rail icon-morph-beat modal-morph sheet-spring-up spring-pop gloss-sweep
        settings-toggle-flow signup-flow onboarding-stepper-flow state-chip-rail
        spring-stack-shuffle physical-exit pendulum-swing split-tilt-cards stagger-cascade
        grid-card-assemble stagger-lattice keyframe-scrub-stack separator outline-draw
        spotlight-card focus-swap offset-path-traveler soft-blob-touch
    """,
    "text": """
        text-stagger text-state-swap text-match-cut code-slice-hero caption-blend-difference
        streaming-text typed-prompt hw-title hw-write-title hw-path-text weight-wave
        split-flap-board yt-prism-title vox-annotate shimmer-sweep shutter-slam extended-keyframe
        wordmark-tiles marker-checklist-card
    """,
    "captions": "mk-callout-highlight",
    "callouts": """
        lower-third-bild news-ticker yt-lower-third hw-arrow hw-box-label hw-callout-circle
        hw-underline hw-text-cloud cursor-annotate yt-circle-pointer yt-feather-highlight
        agent-cursor dart-cursor magnetic-cursor multiplayer-cursors oversized-cursor press-ripple
        touch-indicator tracing-beam arc-motion-path cta-close cta-lockup store-badge-lockup
        telemetry-hud
    """,
    "social": """
        instagram-follow tiktok-follow x-post reddit-post spotify-card yt-comment-card x-follow-card
        macos-notification thread-message-stack chat-message chat-thread typing-indicator
        notes-typing notification-pileup notification-stack native-notification-pop
        testimonial-card testimonial-proof-card social-proof-card avatar-cloud overwhelm-surround
        ai-answer-rank ai-chat-reveal chatgpt-exchange claude-exchange message-thread-reveal
        notes-reveal notification-cascade share-sheet-carousel slack-notification-ad scroll-feed
        logo-wall trust-strip
    """,
    "data": """
        bar-chart-race data-chart flowchart flowchart-vertical mk-line-graph mk-progress-stat
        mk-specs-list mk-usage-arc oscilloscope-trace spain-map us-map us-map-bubble us-map-flow
        us-map-hex world-map week-in-merges apple-money-count north-korea-locked-down
        nyc-paris-flight animated-bar-chart chart-story conic-progress-ring count-up decline-chart
        number-wheel star-rating-fill hw-pipeline constellation-hub radial-surround
    """,
    "code": "terminal-simulator code-terminal-run",
    "mockups": """
        app-showcase browser-device-stage device-frame-stage multi-device-splay ios26-liquid-glass
        macos-tahoe-liquid-glass vfx-iphone-device liquid-glass-notification liquid-glass-widgets
        screen-flow-carousel sticky-mock-swap ui-focus-zoom ui-3d-reveal vector-editor-rig
        camera-scan-gate segmentation-flood mk-placeholder-grid yt-vertical-fill hw-frame
        cuboid-carousel before-after-wipe comparison-split grade-split-reveal vpn-youtube-spot
        velocity-throw-snap
    """,
    "backgrounds": """
        aurora blob color-wheel falling-lines flowing-gradient fractal-noise gabor-noise godrays
        marble mesh-gradient plasma prism ripples sine-wave spiral stripes strands sun-burst swirl
        voronoi worley-noise lens-flare halftone-field gallery-tunnel spiral-galaxy
        vfx-anamorphic-flare vfx-liquid-background mk-background yt-lcd-background aurora-drift
        beat-pulse-background dynamic-grid grain-field mesh-gradient-bg waveform mk-emphasis-type
    """,
    "looks": """
        grain-overlay vignette yt-screen-warp camcorder-hud freeze-frame-dressing snow starfield
        light-sweep-pass organic-light-leak-overlay cinemagraph ascii-render-pass
        ordered-dither-pass slit-scan-reveal filmed-screen motion-blur echo-smear echo-trail
        stop-motion-cadence hw-boil confetti beat-accent vfx-liquid-glass vfx-magnetic vfx-portal
        vfx-shatter ink-bleed-reveal particle-image-reveal svg-mask-reveal vfx-text-cursor
    """,
    "3d": """
        chrome-orb frost goo heatmap hologram holographic light-edge liquid-metal nebula obsidian
        plastic thin-film water cosmic-orb product-turntable exploded-stack extruded-logo
        glass-hero glass-shard-title canopy-part-title wireframe-portal-title
        frost-sequence-camera-orbit orbit-card three-orbiting-cards camera-rig-depth-stack
        camera-dolly-zoom rack-focus camera-shake yt-camera-move push-in pull-back-reveal
        pan-stations scroll-camera-story drift-hold focus-rack perspective-marquee
    """,
    "scenes": """
        blue-sweater-intro-video logo-outro yt-logo-intro logo-sting logo-brand-close
        heygen-avatar-promo-card beat-timeline lottie-character-walk facet-morph
        locked-nucleus-orbit svg-stroke-trace whiteboard-ink svg-line-draw-loader
        ascii-trail-reveal gooey-split
    """,
}

EXPLICIT = {name: tab for tab, names in _LISTS.items() for name in names.split()}


def by_tags(name, tags):
    """For items no list names: the first matching purpose, then technique."""
    t = set(tags or [])
    if name.startswith("transition-") or name.startswith("transitions-"):
        return "transitions"
    if name.startswith("caption-") or t & {"captions", "caption-style"}:
        return "captions"
    if name.startswith(("carousel-", "carousel")):
        return "mockups"
    if name.startswith(("lt-",)) or "lower-third" in t:
        return "callouts"
    if t & {"code-animation", "code", "terminal"}:
        return "code"
    if t & {"cursor", "annotation"}:
        return "callouts"
    if t & {"data", "chart", "map", "data-viz"}:
        return "data"
    if t & {"social", "chat", "notification"}:
        return "social"
    if t & {"text-effect", "typography", "kinetic-type"}:
        return "text"
    if "transition" in t:
        return "transitions"
    if t & {"device", "mock-ui", "product-demo", "ui-props"}:
        return "mockups"
    if t & {"camera", "3d", "3d-object", "3d-motion"}:
        return "3d"
    if "background" in t:
        return "backgrounds"
    if t & {"overlay", "effect", "effects", "texture", "shader", "webgl", "html-in-canvas"}:
        return "looks"
    return "scenes"


def tab_for(name, tags):
    return EXPLICIT.get(name) or by_tags(name, tags)


# ── Families: inside a tab, items made and presented the same way sit together ────────────

def _has(tags, *keys):
    return bool(set(tags or []) & set(keys))


# (family, test(name, tags, description)); the first that matches wins.
FAMILY_RULES = [
    ("One → Two (full frame)", lambda n, t, d: n.startswith("transition-")),
    ("Shader transitions", lambda n, t, d: d.startswith("Shader transition")),
    ("Shaders library (WebGPU)", lambda n, t, d: "A WebGPU shader" in d),
    ("transitions.dev UI kit", lambda n, t, d: _has(t, "transitions-dev-port")),
    ("Caption styles", lambda n, t, d: n.startswith("caption-") or n == "mk-callout-highlight"),
    ("Lower thirds", lambda n, t, d: n.startswith("lt-") or _has(t, "lower-third")),
    ("Handwritten kit", lambda n, t, d: n.startswith("hw-") or _has(t, "handwritten")),
    ("Minimal kit", lambda n, t, d: n.startswith("mk-")),
    ("Creator kit", lambda n, t, d: n.startswith("yt-") or _has(t, "creator")),
    ("Carousels", lambda n, t, d: n.startswith("carousel-") or n == "cuboid-carousel"),
    ("Code editors & terminals", lambda n, t, d: _has(t, "code-animation", "terminal")),
    ("Cursors & pointers", lambda n, t, d: _has(t, "cursor", "pointer", "pointers")),
    ("Maps", lambda n, t, d: _has(t, "map")),
    ("Vertical ad templates", lambda n, t, d: _has(t, "ad-template")),
    ("Platform cards", lambda n, t, d: d.startswith("Animated ") and _has(t, "social")),
    ("Chat & notifications", lambda n, t, d: _has(t, "chat", "notification", "messages", "conversation")),
    ("HTML-in-Canvas VFX", lambda n, t, d: _has(t, "html-in-canvas")),
    ("3D motion (Blender)", lambda n, t, d: _has(t, "3d-motion")),
    ("Three.js objects", lambda n, t, d: _has(t, "three-js", "3d-object")),
    ("Footage overlays", lambda n, t, d: _has(t, "media-treatment-overlay", "overlay", "vignette", "grain")),
    ("Camera moves", lambda n, t, d: _has(t, "camera")),
    ("Full-frame wipes & reveals", lambda n, t, d: _has(t, "transition") and _has(t, "texture", "wipe", "paper rip", "torn paper", "curtain", "collage", "halftone", "pixelate")),
    ("Scene bridges (demo cards)", lambda n, t, d: _has(t, "transition", "transition-primitive")),
    ("UI props", lambda n, t, d: _has(t, "ui-props", "prop", "ui-flow")),
    ("Product demos", lambda n, t, d: _has(t, "product-demo", "device", "mock-ui", "app")),
    ("Charts & counters", lambda n, t, d: _has(t, "data", "chart", "data-viz", "counter", "stats")),
    ("Text animations", lambda n, t, d: _has(t, "text-effect", "typography", "kinetic-type", "text")),
    ("Anime.js-style", lambda n, t, d: _has(t, "anime-inspired", "advanced-motion", "hyperframes-native")),
    ("Motion primitives", lambda n, t, d: _has(t, "motion-primitive", "video-primitive")),
    ("WebGL scenes", lambda n, t, d: _has(t, "webgl", "shader", "webgpu")),
]


def family_for(name, tags, description):
    for family, test in FAMILY_RULES:
        if test(name, tags or [], description or ""):
            return family
    return "Other"
