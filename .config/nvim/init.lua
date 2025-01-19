require("config.keymaps")
require("config.lazy")
require("config.settings")
require("config.lsp-setup")

-- Auto-save session on exit
vim.cmd([[
  autocmd VimLeave * mksession! ~/.local/share/nvim/session.vim
]])


