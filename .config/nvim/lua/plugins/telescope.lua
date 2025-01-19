return {
  {
    'nvim-telescope/telescope.nvim',
    tag = '0.1.8',
    dependencies = {
		  'nvim-lua/plenary.nvim',
		  'BurntSushi/ripgrep',
         },
    config = function()
	local additional_args = {""}

      require('telescope').setup({
        defaults = {
          -- Default configuration for telescope goes here:
          mappings = {
            i = {
              -- Custom key mappings in insert mode
            }
          }
        },
        pickers = {
          -- Configuration for builtin pickers
					 find_files = {
					  find_command = {"rg", "--files"}
					 },
					 live_grep = {},
					 grep_string = {},
					 current_buffer_fuzzy_find = {}, -- current_buffer_fzf,
        },
        extensions = {
          fzf = {
            fuzzy = true,                    -- false will only do exact matching
            override_generic_sorter = true,  -- override the generic sorter
            override_file_sorter = true,     -- override the file sorter
            case_mode = "smart_case",        -- or "ignore_case" or "respect_case"
                                             -- the default case_mode is "smart_case"
          }
        }
      })
      require('telescope').load_extension('fzf')
    end
  },
  {
       'nvim-telescope/telescope-fzf-native.nvim',
       build = 'cmake -S. -Bbuild -DCMAKE_BUILD_TYPE=Release && cmake --build build --config Release'
  }
}
