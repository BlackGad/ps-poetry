1. plugin activates if there are in pyproject.toml file section `[tool.ps-plugin]` exist
2. monorepo functionality is built in so `host-project = ".."` will set main project link
3. internally main plugin settings will be picked up from host project after resolve
4. You dont need monorepo module if you will operate only with host project