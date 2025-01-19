vim.opt.tabstop = 3
vim.opt.list = true              -- Enable list mode (if you want it)
vim.opt.timeoutlen = 300
vim.opt.ttimeoutlen = 100 -- Timeout for key repeat (default: 100ms)
vim.opt.relativenumber = true
vim.opt.listchars = {
    tab = "  ",                  -- Use spaces for tab display
    trail = "·",                 -- (Optional) Use · for trailing spaces
    extends = ">",               -- (Optional) Show > for extended text
    precedes = "<",              -- (Optional) Show < for preceding text
    nbsp = "+",                  -- (Optional) Show + for non-breaking spaces
}

-- settings for netrw
vim.api.nvim_create_autocmd("FileType", {
		  pattern = "netrw",
		  callback = function()
					 vim.wo.number = true
					 vim.wo.relativenumber = true
		  end,
})

--auto-update plugins 
vim.api.nvim_create_autocmd("VimEnter", {
		  callback=function() 
					 require"lazy".update({show = false,})
		  end,
})
vim.opt.termguicolors = true
