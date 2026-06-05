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

local abbreviations = {
	["pg"] = "prairie_gold",
	["pr"] = "prairie_gold",
	["ww"] = "whole_wheat",
	["hr"] = "hard_red",
	["bc"] = "bronze_chief",
	["hy"] = "hydration",
	["pf"] = "potato_flakes",
	["fm"] = "flaxseed_meal",
	["aa"] = "ascorbic_acid_1p",
}
for lhs, rhs in pairs(abbreviations) do
	vim.keymap.set("ia", lhs, rhs, { buffer = true })
end
