return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
		"WhoIsSethDaniel/mason-tool-installer.nvim",
      "hrsh7th/cmp-nvim-lsp",  -- Ensure LSP works with nvim-cmp
		{
			 'nvim-flutter/flutter-tools.nvim',
			 lazy = false,
			 dependencies = {
				  'nvim-lua/plenary.nvim',
				  'stevearc/dressing.nvim', -- optional for vim.ui.select
			 },
		}
    },
    config = function()
      -- Setup mason
      require("mason").setup()

      -- Setup mason-lspconfig
      require("mason-lspconfig").setup({
        ensure_installed = { "lua_ls", "pyright" }, -- Add LSP servers here
        automatic_installation = true,
      })

      local lspconfig = require("lspconfig")
      local capabilities = require("cmp_nvim_lsp").default_capabilities() -- Enable nvim-cmp for LSP

      local on_attach = function(client, bufnr)
        local opts = { noremap = true, silent = true, buffer = bufnr }
        vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
        vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
        vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, opts)
        vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
      end


		require("mason-lspconfig").setup_handlers({
		  function(server)
			 lspconfig[server].setup({
				capabilities = capabilities,
				on_attach = on_attach,
			 })
		  end,
		})

		require("flutter-tools").setup({
			lsp = {
--				 color = { -- show the derived colours for dart variables
--					enabled = false, -- whether or not to highlight color variables at all, only supported on flutter >= 2.10
--					background = false, -- highlight the background
--					background_color = nil, -- required, when background is transparent (i.e. background_color = { r = 19, g = 17, b = 24},)
--					foreground = false, -- highlight the foreground
--					virtual_text = true, -- show the highlight using virtual text
--					virtual_text_str = "■", -- the virtual text character to highlight
--				 },
				 capabilities = capabilities,
				 on_attach = on_attach,
			  }
			})
      -- Define and setup LSP servers
      --local servers = { "lua_ls", "pyright" }
      --for _, server in ipairs(servers) do
      --  lspconfig[server].setup({
      --    capabilities = capabilities,
      --    on_attach = on_attach,
      --  })
      --end
    end,
  }
}
