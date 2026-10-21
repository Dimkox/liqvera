# TLS trust remediation — 2026-10-21

The owner requested fixing all four TLS blockers from the [initial Getzilla audit](2026-10-21-getzilla-initial.md). This source change preserves payment behavior, SQL migrations, sealed evidence and WalletConnect configuration. Source verification and production rollout are separate evidence boundaries.

| Finding | Correction |
| --- | --- |
| SR-01: certifi trusted a compromised emSign root | Both Python closures pin certifi 2026.10.19. Capture and report rebuild their installed closure. |
| SR-02: gateway could retain the root through Node trust | Node explicitly uses the corrected OpenSSL store, including the spawned gateway child. Both CA packages pin 20261020-r0. |
| SR-03: Caddy's Go verifier predates the incident denylist | Caddy remains 2.11.7, built with digest-pinned Go 1.27.3 and unchanged x/net/x/crypto inputs. |
| SR-04: pip's vendored roots predate the correction | pip pins 26.2.2. Docker/CI bootstrap from its SHA-256-bound wheel offline before index access. Runtime pip/ensurepip remain absent. |

All six Dockerfiles update CA trust before BusyBox source downloads. Python, Node and Caddy build/runtime stages use corrected trust. PostgreSQL's source recipe is hardened too; its existing live container is intentionally retained because it has internal-only networks and none of the reported outbound TLS paths. No database restart or migration is needed for these four findings.

On CI, corrected pip supplies the CA file and a newly empty directory replaces additional OpenSSL lookup paths before setup-node, pip downloads and npm. Both variables persist for later steps. This prevents modern pip's additive system trust and Node's bundled roots from reintroducing the incident root. The initial checksum-verified wheel and pinned checkout action are the bootstrap boundary.

Offline regressions check four incident root fingerprints, a nonempty valid trust set and verification settings. Python explicitly inspects lazily loaded hashed CA directories, including directory lists. Node verifies inherited OpenSSL mode and fails closed on directory-list overrides that its enumeration cannot inspect correctly. The public certificate fixture has no private key. These are trust-store/inheritance checks, not simulated exploit or live-payment acceptance.

Bounded candidate validation passes: six Docker builds; capture/report TLS, CPython and BusyBox regressions; Node parent/child trust; edge/web/PostgreSQL CA probes; Caddy configuration; 71 gateway tests including 13 real disposable-PostgreSQL cases using the new gateway and database images; four negative/positive hashed-directory regression cases. Fresh supplemental OSV and PyPI advisory queries cover all 65 lock entries / 52 unique versions with zero findings. The old certifi version remains a positive advisory control. Binary govulncheck on the Go 1.27.3 Caddy candidate reports zero affected symbols/packages; the module-only OpenPGP finding remains non-applicable to the built proxy.

Independent read-only code and security review reproduced and resolved additional CI/CA-directory gaps. At this source checkpoint, full successor review, the final gate and exact committed-image rollout were pending. They are now recorded separately in the [TLS deployment evidence](2026-10-21-tls-deployment.md): all four TLS blockers are closed and the corrected images are live. The raw external gate retains disclosed formatting/public-address findings. Candidate images labelled uncommitted must not be deployed. Retained old images are recovery material and must not be described as remediated.

Primary references: [certifi advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2), [pip 26.2.2 release](https://pypi.org/project/pip/26.2.2/), [Go verifier advisory](https://pkg.go.dev/vuln/GO-2026-6809), [Node CA selection](https://nodejs.org/download/release/v24.18.1/docs/api/cli.html#--use-bundled-ca---use-openssl-ca).
