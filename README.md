# helios_studio

Video assets for a robotics/autonomy series built around the Helios project. See
[`context/`](context/) for the series plan, project briefing, and episode scripts.

This repo is the **video tooling**: a reusable Manim component library plus
per-episode scenes, set up for a Neovim-native, mpv-previewed workflow.

## Layout

```
helios_studio/
  context/        series plan, Helios briefing, episode scripts (the source of truth)
  helios_manim/   reusable Mobjects: Node, TypedPort/TypedArrow, Packet, Pipeline, type map
  scenes/         per-episode Manim scenes (ep01_boxes_and_arrows.py, …)
  tools/          preview.sh — render + drive the mpv preview window
  nvim/           helios.lua — Neovim keymaps for the render loop
  media/          Manim render outputs (gitignored)
  assets/         captured sim footage, audio, thumbnails (gitignored)
```

> Note: the component package is `helios_manim/` (not `manim/`) so it doesn't
> shadow the installed `manim` package on import.

## Setup (one time)

```sh
# System libs Manim's bindings build against:
brew install cairo pango pkg-config ffmpeg mpv

# Python env (uv fetches Python 3.12 — Manim has no 3.14 wheels yet):
uv sync
```

If `uv sync` ever fails to find cairo, prefix it with the brew pkg-config path:
`PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig" uv sync`.

## The Neovim workflow

Enable project-local config once in your `init.lua`:

```lua
vim.o.exrc = true   -- auto-sources this repo's .nvim.lua (which loads nvim/helios.lua)
```

Then, with a scene file open, keymaps (normal mode):

| Key          | Action                                                       |
|--------------|--------------------------------------------------------------|
| `<leader>mr` | Render the scene **under the cursor** (draft) → mpv          |
| `<leader>mf` | Render the **last frame only** (fast layout tuning) → mpv    |
| `<leader>mF` | Render a high-quality **final** (`-qh`) → mpv                |
| `<leader>mn` | Render a scene **by name** (prompt) → mpv                    |

Renders run async — Neovim never blocks. One mpv window stays open and reloads on
every render (works for both `.mp4` animations and `-s` still frames), so the
edit → render → see loop has no window churn. Close mpv any time; the next render
opens a fresh one.

### Without Neovim

`tools/preview.sh` is a standalone CLI:

```sh
tools/preview.sh scenes/ep01_boxes_and_arrows.py SingleBox          # draft animation
tools/preview.sh scenes/ep01_boxes_and_arrows.py SingleBox frame    # last frame only
tools/preview.sh scenes/ep01_boxes_and_arrows.py SingleBox final    # -qh final
```

Or drop to raw Manim: `uv run manim render -ql -p scenes/<file>.py <Scene>`.

## Component library

Scenes compose from `helios_manim` primitives instead of redrawing boxes:

```python
from helios_manim import Node, TypedArrow, Packet, Pipeline

pipe = Pipeline.from_topology(
    nodes={"sensor": {"label": "sensor"}, "est": {"label": "estimator"}},
    edges=[("sensor", "est", "LaserScan")],
)
```

The type → colour/shape map lives in `helios_manim/types.py` — the single source
of truth so a `Pose` looks like a `Pose` in every episode. `scenes/` currently
holds episode-1 beat stubs (see `context/ep01_boxes_and_arrows.md`).
