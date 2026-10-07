# WORK-POLICY-IPC-REPAIR-1

Admission uses one already-open pipe and a bounded COMPLETE handshake, so a timeout, EOF, or partial broker reply refuses before any provider starts. The slot holder releases and is reaped on success, provider failure, timeout, signal, and a quality-start failure. A quality-start failure returns its own status. The guard suite bounds its waits and cleans up the processes it owns.
