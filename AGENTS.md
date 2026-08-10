# AGENTS.md

This repository owns the local OpenSPG + KAG evaluation environment.

- Keep the Docker Compose project name `tidewise-reason`.
- Follow the official OpenSPG/KAG 0.8 topology unless a documented experiment requires otherwise.
- Keep runtime source checkouts, Python environments, data and credentials out of Git.
- Bind local evaluation ports to loopback by default.
- Do not treat the bundled demo credentials or Compose file as production configuration.
- Verify changes through the Web endpoint and the KAG/KNEXT CLIs.
