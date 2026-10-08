Native worker runs now save local recovery state before starting, every sixty
seconds when state changes, and after success, failure, timeout or graceful
interruption. Saves carry the native attempt ID and actual final exit. Saving
needs no AI answer, preserves the last good checkpoint on failure, and does not
accept code or restart a provider. Available in source for the v0.5.4 milestone;
authorized continuation and lead cooldown restart remain pending.
