-- ~/.config/nvim/lua/plugins/treesitter.lua
return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate",
  config = function()
    require("nvim-treesitter.configs").setup({
      ensure_installed = {"cpp", "python","markdown", "go"},  -- Add languages as needed
      sync_install = false,
      highlight = { enable = true },
      indent = { enable = true },
    })
  end
}

