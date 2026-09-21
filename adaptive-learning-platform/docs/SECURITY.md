# Security

Learner code is never executed by the API interpreter. `DockerCodeRunner` uses an ephemeral container with no network, a read-only root filesystem, a small tmpfs, CPU/memory/PID limits, all Linux capabilities dropped, and `no-new-privileges`. The host Docker socket is high privilege; production must replace this local backend with a separately isolated sandbox service.

Research pages are untrusted. The ingestion seam removes obvious instruction-like content, bounds text size, and passes evidence only through constrained provider inputs. Production ingestion still requires robust HTML parsing, malware controls, SSRF protection, allow/deny policies, and provenance capture.

V1 authentication uses a development header and demonstrates authorization failures, but it is not internet-grade authentication. Replace it with signed, expiring sessions and CSRF protection. Add rate limits, audit retention, deletion/export controls, secret rotation, and encrypted artifact storage before production.

The API does not log secrets or raw learner code. Provider response storage is disabled. Sensitive learner text minimization and jurisdiction-specific privacy review remain deployment responsibilities.
