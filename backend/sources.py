VERIFIED_AT = "2026-11-11"

REPOSITORIES = [
    {
        "name": "OpenCode",
        "repository": "anomalyco/opencode",
        "url": "https://github.com/anomalyco/opencode",
        "role": "Development orchestrator; retain the existing installation after the PC audit.",
        "status": "verified_upstream",
        "cost": "Open-source core; model/provider costs depend on configuration.",
        "caution": "The current README uses the dev branch and @opencode/cli. Do not follow archived opencode-ai/opencode instructions.",
    },
    {
        "name": "PentAGI",
        "repository": "vxcontrol/pentagi",
        "url": "https://github.com/vxcontrol/pentagi",
        "role": "Possible later controlled research engine; not deployed in milestone one.",
        "status": "review_required",
        "cost": "Self-hosted source is available; third-party tools, enterprise features and model usage can have separate terms/costs.",
        "caution": "Review the EULA, Docker access and network isolation before installation. SENTINEL does not mount the Docker socket.",
    },
    {
        "name": "CyberGym",
        "repository": "sunblaze-ucb/cybergym",
        "url": "https://github.com/sunblaze-ucb/cybergym",
        "role": "Local benchmark only; never a live-target testing engine.",
        "status": "verified_upstream",
        "cost": "Apache-2.0 code; substantial storage and compute may be required.",
        "caution": "Upstream documents ~240GB benchmark data and ~10TB full server data. Use the documented subset only after explicit approval; keep all services private.",
    },
    {
        "name": "Ollama",
        "repository": "ollama/ollama",
        "url": "https://github.com/ollama/ollama",
        "role": "Default local inference provider; existing models must be audited first.",
        "status": "existing_install_unverified",
        "cost": "No per-request API charge for local inference; hardware and electricity still apply.",
        "caution": "Model capability and tool-calling support must be measured locally, not assumed.",
    },
]

POLICIES = [
    {
        "name": "HackerOne — AI tools and human oversight",
        "url": "https://docs.hackerone.com/en/articles/10908081-hai-security-trust",
        "checked_at": VERIFIED_AT,
        "summary": "HackerOne states that AI tools may not operate fully autonomously; human experts must investigate, validate and confirm potential vulnerabilities before submission.",
    },
    {
        "name": "Intigriti — Community Code of Conduct",
        "url": "https://kb.intigriti.com/en/articles/5247238-community-code-of-conduct",
        "checked_at": VERIFIED_AT,
        "summary": "Responsible AI use is permitted. Researchers must personally identify and verify findings, avoid fabricated content and disclose AI use.",
    },
    {
        "name": "OpenRouter — API credit and rate limits",
        "url": "https://openrouter.ai/docs/api_reference/limits",
        "checked_at": VERIFIED_AT,
        "summary": "Free-model availability and limits depend on account and current provider policy. SENTINEL therefore uses no fixed quota assumption and disables external AI by default.",
    },
    {
        "name": "CyberGym — local deployment warning",
        "url": "https://github.com/sunblaze-ucb/cybergym#evaluation",
        "checked_at": VERIFIED_AT,
        "summary": "Upstream instructs users to deploy locally, avoid public exposure and configure a private bind address and firewall.",
    },
]
