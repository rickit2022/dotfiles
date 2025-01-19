return {
		  "neovim/nvim-lspconfig",
					 event = {"BufReadPre", "BufNewFile"},
					 dependencies = {
					 { 'j-hui/fidget.nvim', opts = {} },
					 'hrsh7th/cmp-nvim-lsp',
					 'hrsh7th/nvim-cmp',
					 },
					 config = function()
								local cmp_nvim = require("cmp_nvim_lsp")
		  
					 end,
}
