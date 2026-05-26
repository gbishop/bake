-- nvim/after/ftplugin/bake.lua
--

vim.bo.textwidth = 68
-- break lines at textwidth
vim.bo.formatoptions = vim.bo.formatoptions .. "t"

-- Run my bake script
vim.keymap.set("n", "<leader>r", function()
	local original_lines = vim.api.nvim_buf_get_lines(0, 0, -1, true)
	local formatted_lines

	formatted_lines = vim.fn.systemlist("python /home/gb/bake/bake.py", original_lines)
	if vim.v.shell_error ~= 0 then
		vim.notify(table.concat(formatted_lines, "\n"), vim.log.levels.ERROR)
		return
	end

	local view = vim.fn.winsaveview()
	vim.api.nvim_buf_set_lines(0, 0, -1, true, formatted_lines)
	vim.fn.winrestview(view)
end, { desc = "Format a recipe", buffer = true })

-- Run my bake script and rewrite to bp
vim.keymap.set("n", "<leader>R", function()
	local original_lines = vim.api.nvim_buf_get_lines(0, 0, -1, true)
	local formatted_lines

	formatted_lines = vim.fn.systemlist("python /home/gb/bake/bake.py -R", original_lines)
	if vim.v.shell_error ~= 0 then
		vim.notify(table.concat(formatted_lines, "\n"), vim.log.levels.ERROR)
		return
	end

	local view = vim.fn.winsaveview()
	vim.api.nvim_buf_set_lines(0, 0, -1, true, formatted_lines)
	vim.fn.winrestview(view)
end, { desc = "Format a recipe", buffer = true })

-- hack for bulleted list.
local function format_to_bullet()
	local bufnr = 0
	local cursor_pos = vim.api.nvim_win_get_cursor(0)
	if cursor_pos[2] ~= 0 then
		vim.cmd("normal! (")
		cursor_pos = vim.api.nvim_win_get_cursor(0)
	end
	local line_num = cursor_pos[1] - 1
	local line_content = vim.api.nvim_buf_get_lines(bufnr, line_num, line_num + 1, false)[1]

	local new_line
	-- Logic: Check if line starts with optional space, a marker (*, -, or 1.), and a space
	if line_content:match("^%s*[%*%-%d+%.•]+%s+") then
		-- CASE 1: Replace existing marker, keep indentation
		new_line = line_content:gsub("^(%s*)[%*%-%d+%.•]+%s+", "%1• ")
	else
		-- CASE 2: No marker found, prepend bullet to the start of the text (after indentation)
		new_line = line_content:gsub("^(%s*)(.*)", "%1• %2")
	end

	-- Apply changes
	vim.api.nvim_buf_set_lines(bufnr, line_num, line_num + 1, false, { new_line })

	-- Format paragraph
	vim.cmd("normal! gwip")

	-- Restore cursor to the start of the line
	vim.api.nvim_win_set_cursor(0, { line_num + 1, 0 })
end

vim.keymap.set("n", "<leader>b", format_to_bullet, { desc = "Bulletize and format paragraph" })

-- 1. Create a dedicated namespace for your semantic tags
local bake_ns = vim.api.nvim_create_namespace("bake_tags")

-- 2. Define how the tag looks
vim.api.nvim_set_hl(0, "PartName", { fg = "#FFB86C", bold = true })

-- 3. A function to scan the buffer and apply tags
local function apply_semantic_tags()
	local bufnr = vim.api.nvim_get_current_buf()

	-- Clear existing tags from our namespace first
	vim.api.nvim_buf_clear_namespace(bufnr, bake_ns, 0, -1)

	local parts = {}
	local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
	for line_idx, line in ipairs(lines) do
		local start_char, part, end_char = line:match("^()([a-zA-Z_%d]+)()[ ^0-9g%%]*:")
		if start_char ~= nil then
			parts[part] = true
			-- Apply the extmark (0-indexed line and character offsets)
			vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, start_char - 1, {
				end_col = end_char - 1,
				hl_group = "PartName",
				-- Optional: You can attach non-visual attributes or virtual text too!
			})
		elseif line:match("^%s") then
			for sw, word, ew in line:gmatch("()(%w+)()") do
				if parts[word] then
					vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sw - 1, {
						end_col = ew - 1,
						hl_group = "PartName",
					})
				end
			end
		elseif line:match("^│") then
			local sw, part, ew = line:match("^│%s+()(%w+)()")
			if parts[part] then
				vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sw - 1, {
					end_col = ew - 1,
					hl_group = "PartName",
				})
				for sw, number, ew in line:gmatch("()([-0-9.+g])()") do
					vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sw - 1, {
						end_col = ew - 1,
						hl_group = "PartTotals",
					})
				end
			end
		end
	end
end

-- 4. Automatically run it when text changes or when opening a file
vim.api.nvim_create_autocmd({ "BufEnter", "TextChanged", "InsertLeave" }, {
	pattern = "*.bake", -- or your specific file extension
	callback = apply_semantic_tags,
})
