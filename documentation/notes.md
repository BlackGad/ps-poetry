# Plugin Behavior Notes

* The plugin activates only when a `[tool.ps-plugin]` section is present in `pyproject.toml`
* Monorepo support is built in: setting `host-project = ".."` in `[tool.ps-plugin]` links the component to its host project
* Plugin settings are resolved from the host project after the monorepo link is established
* The monorepo module is not required when operating only with the host project directly
