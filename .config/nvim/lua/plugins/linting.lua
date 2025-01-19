return {
		  "mfussenegger/nvim-lint",
		  events = {
					 "BufReadPre",
					 "BufNewFile",
		  },
		  config = function()
					 local lint = require("lint")

					 lint.linters_by_ft = {
							 javascript = { "eslint_d" },
							 typescript = { "eslint_d" },
							 javascriptreact = { "eslint_d" },
							 typescriptreact = { "eslint_d" },
							 svelte = { "eslint_d" },
							 python = { "pylint" },					 
					 }

					 lint.linters.pylint.cmd = 'python'
					 lint.linters.pylint.args = {'-m', 'pylint', '-f', 'json'}

					 vim.api.nvim_create_autocmd({ "BufEnter", "BufWritePost", "InsertLeave"}, {
								group = vim.api.nvim_create_augroup("lint", {clear = true}),
								callback = function()
										  lint.try_lint()
								end,
					 })

					 vim.keymap.set('n', '<leader>l', function() 
								lint.try_lint()
					 end, {desc = "Trigger linting for current file"})
		  end,
}
