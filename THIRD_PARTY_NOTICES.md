# Third-party notices

SENTINEL’s source is MIT licensed. Dependencies and external tools retain their own licences and terms. This file is a source register, not legal advice or a permanent assertion of upstream pricing.

## Direct application/runtime dependencies

- FastAPI, Starlette, Pydantic, Uvicorn, HTTPX, AnyIO, python-multipart and psutil — installed through `requirements.txt`; review their package metadata and licence files.
- React, React DOM, React Router, Lucide React, Vite, TypeScript and the Vite React plugin — installed through `package-lock.json`; review their package licences.
- SQLite and Python/Node.js runtimes — separate upstream licences.

## Optional host tools

- Docker Desktop / Docker Engine / Compose: https://docs.docker.com/ and https://docs.docker.com/desktop/release-notes/
- Ollama: https://github.com/ollama/ollama and https://ollama.com/
- OpenCode: https://github.com/anomalyco/opencode — current package metadata is checked from npm; historical package names are not assumed.
- Python: https://www.python.org/
- Node.js: https://nodejs.org/
- Git for Windows: https://github.com/git-for-windows/git
- Windows Package Manager: https://learn.microsoft.com/windows/package-manager/winget/install

Exact package IDs and official release providers are registered in `backend/registry.py` and `host_companion/updates.py`. No paid provider is required by SENTINEL, but upstream subscription, enterprise, usage and distribution terms must be reviewed before installation.

## Research platforms and AI rules

- HackerOne Hai Security & Trust: https://docs.hackerone.com/en/articles/10908081-hai-security-trust
- Intigriti Community Code of Conduct: https://kb.intigriti.com/en/articles/5247238-community-code-of-conduct

Programme and platform rules take precedence. Human validation, AI disclosure and permission requirements must be checked currently for every engagement.

## Not bundled

PentAGI, CyberGym, Ollama model weights, Docker images and bug-bounty platform content are not bundled. See `docs/SOURCES.md` for source and large-dataset cautions.

## Repository artwork

The SENTINEL banner background was AI-generated for this project and typeset with DejaVu Sans. DejaVu fonts retain their own licence: https://dejavu-fonts.github.io/License.html. Lucide interface icons are used through the `lucide-react` package under its upstream licence.
