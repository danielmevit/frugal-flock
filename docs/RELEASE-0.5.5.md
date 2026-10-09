# Unio 0.5.5 — browser launcher and clearer work map

Unio 0.5.5 packages the browser launcher and makes the interactive work map easier to follow.

[Official release and downloads](https://github.com/danielmevit/unio/releases/tag/v0.5.5).

The browser launcher is now packaged and natively available. Run `unio browser --help` to see explicit startup options for manual execution. You can use `--open-browser` to launch the read-only preview in your default browser, or `--enable-execution`, `--enable-plan-drafts`, and other grants to authorize explicit capabilities. The launcher discovers the workspace safely without manual Python paths.

The browser adds a left-to-right work map with a bounded canvas. It reads from project to worker to task, using an active-first presentation and a neutral hub. Worker cards have been redesigned to dedicate their left quarter to local AI logos and agent names, and the right three quarters to the task title and a clearer muted outcome strip.

Phone pairing, an allowance meter and live lead-session attachment remain planned. This release does not add them. Lead cooldown restart remains experimental and opt-in; a genuine subscription-limit-to-restart cycle remains unobserved.

The complete `bash tools/quality-check.sh` passed on candidate `80457c4ea68f050d3c0eab36e422ae1b502247d7` in 677 seconds. Final publication changes are documentation only, with identical non-Markdown paths, Git modes and blobs. Release assets include the exact-source installer, source archive, license, notice, checksums and provenance. See the [browser startup guide](../bridge/README.md) for capabilities and local access.
