<!--
Unio — Copyright (C) 2026 Daniel Mitev
Original project: https://github.com/danielmevit/unio
-->

### Unio 0.5.0 runtime and installer

- Rename the installer and runtime to `unio-install.sh` and `unio`, with
  `UNIO_*` configuration, Unio completion, templates, help and legal notices.
- Remove recognized legacy installed commands and completions while preserving
  unrelated files. Copy the default legacy config once to `~/.config/unio`,
  leaving the original intact and existing Unio configuration untouched.
- Convert project worker markers and owned guard hooks during init and doctor,
  and exclude `.unio-worker` from Git.
- Rename the runtime tests and update quality tools; extend branding coverage
  for cleanup boundaries, config migration and project conversion.
