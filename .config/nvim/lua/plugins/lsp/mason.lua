return {
		  "williamboman/mason.nvim",
		  dependencies = { "WhoIsSethDaniel/mason-tool-installer.nvim",},
		  config = function()
					 local mason = require("mason")
					 
					 local tool_installer = require("mason-tool-installer")

					 mason.setup({
						  ui = {
								icons = {
									 package_installed = "✓",
									 package_pending = "➜",
									 package_uninstalled = "✗"
								}
						  }
					 })


					 tool_installer.setup({
								ensure_installed = {
										  "prettier",
										  "pylint",
								}
					 })
		  end,
}

