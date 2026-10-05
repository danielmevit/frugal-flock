<!--
Unio — Copyright (C) 2026 Daniel Mitev
Original project: https://github.com/danielmevit/unio
-->

### Unio 0.5.0 examples, bridge and prototype

- Rename visible product names, source headers, repository URLs, command
  examples and installer references in the examples, the local Activity
  preview and the interactive prototype to Unio.
- Use `unio`, `unio-install.sh`, `UNIO_*` and `~/.config/unio`. The old
  command, environment and config names are gone from these trees.
- The Activity preview defaults to the `unio` engine on PATH. An explicit
  `--engine` path still overrides that default. The session header is
  `X-Unio-Session`. Request and draft schemas are unchanged.
- The stamp example resolves the checkout that contains the script. That
  checkout stays inside the legacy local workspace
  `/mnt/d/Vibe Coding/_vm/frugal-flock`, which is not renamed.
