-- Hacked together semantic highlighting for part names
-- Make a single pass over the buffer looking for definitions and
-- usage of part names. Apply extmarks as we go. This will fail
-- on use before definition but I never do that.

local bake_ns = vim.api.nvim_create_namespace("bake_tags")

-- Scan the buffer and apply tags
local function apply_tags()
	local bufnr = vim.api.nvim_get_current_buf()

	-- Clear existing tags from namespace
	vim.api.nvim_buf_clear_namespace(bufnr, bake_ns, 0, -1)

	local parts = {} -- collect the part names
	-- get the lines from the buffer
	local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
	-- process the lines in a single pass
	for line_idx, line in ipairs(lines) do
		-- match a part definition
		local sc, part, ec = line:match("^()([%a_][%w_]+)()[ ^%dg%%]*:")
		if part then
			-- add it to the set of part names
			parts[part] = true
			vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sc - 1, {
				end_col = ec - 1,
				hl_group = "PartName",
			})
		elseif line:match("^%s+%a") then
			-- part ingredients
			for sc, word, ec in line:gmatch("()([%a_][%w_]+)()") do
				-- check each word to see if it is a part name
				if parts[word] then
					vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sc - 1, {
						end_col = ec - 1,
						hl_group = "PartName",
					})
				end
			end
		elseif line:match("^│") then
			-- part totals line in the table
			local sc, part, ec = line:match("^│%s+()([%a_][%w_]+)()")
			if parts[part] then
				vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sc - 1, {
					end_col = ec - 1,
					hl_group = "PartName",
				})
				-- handle the total numbers
				for sw, _, ew in line:gmatch("()( [-%d.+]+g?)()") do
					vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sw - 1, {
						end_col = ew - 1,
						hl_group = "PartTotals",
					})
				end
				-- mark the entire line
				vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, 0, {
					end_col = #line,
					hl_group = "PartHead",
				})
			else
				-- part ingredients in the table
				for sc, word, ec in line:gmatch("()([%a_][%w_]+)()") do
					if parts[word] then
						vim.api.nvim_buf_set_extmark(bufnr, bake_ns, line_idx - 1, sc - 1, {
							end_col = ec - 1,
							hl_group = "PartName",
						})
					end
				end
			end
		end
	end
end

return apply_tags
