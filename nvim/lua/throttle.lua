--- Throttles a function to execute at most once per `ms` milliseconds.
---@param fn function The function to throttle.
---@param ms number The throttle duration in milliseconds.
---@return function
local function throttle(fn, ms)
	local timer = vim.uv.new_timer()
	local running = false

	return function(...)
		local args = { ... }
		if not running then
			-- Execute on the leading edge (immediately)
			fn(unpack(args))
			running = true

			-- Start timer to clear the lock after 'ms'
			timer:start(ms, 0, function()
				running = false
			end)
		end
	end
end

return throttle
