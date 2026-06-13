-- Project-local Neovim config, auto-sourced when you open nvim in this repo
-- *if* you have `vim.o.exrc = true` in your init.lua.
--
-- It wires up the Manim render-loop keymaps from nvim/helios.lua. If you'd
-- rather load it globally, ignore this file and require the module yourself.
---@diagnostic disable: undefined-global  -- `vim` is provided by the Neovim runtime
package.path = vim.fn.getcwd() .. "/nvim/?.lua;" .. package.path
require("helios").setup()
