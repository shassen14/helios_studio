-- helios_studio :: Neovim integration for the Manim render loop.
--
-- What it gives you (Python buffers only):
--   <leader>mr  render the scene under the cursor  (draft animation -> mpv)
--   <leader>mf  render the LAST FRAME only          (fast layout tuning -> mpv)
--   <leader>mn  render a scene picked from a prompt (draft animation -> mpv)
--   <leader>mF  render high-quality FINAL           (slow; -qh -> mpv)
--
-- All renders are async (vim.fn.jobstart) so the editor never blocks. mpv keeps
-- one window open and reloads on each render (see tools/preview.sh).
--
-- INSTALL — pick one:
--   1. Project-local (recommended): add `vim.o.exrc = true` to your init.lua.
--      The repo already ships a `.nvim.lua` that loads this module, so exrc
--      auto-sources it whenever you open Neovim in this directory.
--   2. Global: copy this file onto your runtimepath and call
--          require("helios").setup()
--      from your init.lua, guarded by a cwd check if you like.
--
-- mpv preview controls (the window stays open and reloads on each render):
--   q      close the preview     <  restart the clip
--   space  pause/play            ./,  step one frame fwd/back
---@diagnostic disable: undefined-global  -- `vim` is provided by the Neovim runtime

local M = {}

-- Find the project root by walking up from the current file to a pyproject.toml.
local function project_root()
  local marker = vim.fs.find("pyproject.toml", {
    upward = true,
    path = vim.fn.expand("%:p:h"),
  })[1]
  if marker then
    return vim.fs.dirname(marker)
  end
  return vim.fn.getcwd()
end

-- Scan upward from the cursor for the nearest `class Foo(...):` and return Foo.
local function scene_under_cursor()
  local lnum = vim.fn.line(".")
  for i = lnum, 1, -1 do
    local line = vim.fn.getline(i)
    local name = line:match("^%s*class%s+([%w_]+)%s*%(")
    if name then
      return name
    end
  end
  return nil
end

-- Run tools/preview.sh <file> <scene> <mode> asynchronously, streaming status.
local function render(scene, mode)
  if not scene then
    vim.notify("helios: no Scene class found under cursor", vim.log.levels.WARN)
    return
  end
  local root = project_root()
  local file = vim.fn.expand("%:p")
  local script = root .. "/tools/preview.sh"

  vim.notify(("helios: rendering %s (%s)…"):format(scene, mode), vim.log.levels.INFO)
  vim.fn.jobstart({ script, file, scene, mode }, {
    cwd = root,
    on_exit = function(_, code)
      vim.schedule(function()
        if code == 0 then
          vim.notify(("helios: %s ready ▶ mpv"):format(scene), vim.log.levels.INFO)
        else
          vim.notify(("helios: render failed (exit %d) — :messages / run in shell"):format(code),
            vim.log.levels.ERROR)
        end
      end)
    end,
  })
end

function M.setup(opts)
  opts = opts or {}
  local lead = opts.prefix or "<leader>m"

  local function map(suffix, fn, desc)
    vim.keymap.set("n", lead .. suffix, fn, { desc = desc, silent = true })
  end

  map("r", function() render(scene_under_cursor(), "video") end, "Manim: render scene under cursor")
  map("f", function() render(scene_under_cursor(), "frame") end, "Manim: render last frame (fast)")
  map("F", function() render(scene_under_cursor(), "final") end, "Manim: render FINAL (-qh)")
  map("n", function()
    vim.ui.input({ prompt = "Scene to render: " }, function(name)
      if name and #name > 0 then render(name, "video") end
    end)
  end, "Manim: render named scene")
end

return M
