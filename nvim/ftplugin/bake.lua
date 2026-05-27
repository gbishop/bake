-- nvim/after/ftplugin/bake.lua
--

vim.bo.textwidth = 68
-- break lines at textwidth
vim.bo.formatoptions = vim.bo.formatoptions .. "t"

-- Run my bake script
local run_bake = require("run_bake")

vim.keymap.set("n", "<leader>r", function()
	run_bake("")
end, { desc = "Format a recipe", buffer = true })

vim.keymap.set("n", "<leader>R", function()
	run_bake("-R")
end, { desc = "Format and convert to BP", buffer = true })

-- Semantic tagging
local throttle = require("throttle")
local apply_tags = require("apply_tags")

vim.api.nvim_create_autocmd({ "BufEnter", "TextChanged", "InsertLeave" }, {
	pattern = "*.bake",
	callback = throttle(apply_tags, 500),
})
