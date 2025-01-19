require("mason").setup()
require("mason-lspconfig").setup()

local lspconfig = require("lspconfig")
local mason_lspconfig = require("mason-lspconfig")

mason_lspconfig.setup_handlers({
  -- Default handler for all LSP servers
  function(server_name)
    lspconfig[server_name].setup({
      on_attach = function(client, bufnr)
        -- your on_attach function, as in your original config
      end,
      capabilities = vim.lsp.protocol.make_client_capabilities(),
    })
  end,

  -- You can also set specific configurations for specific servers if needed
  ["pyright"] = function()
    lspconfig.pyright.setup({
      -- Specific configurations for Pyright
    })
  end,
})
