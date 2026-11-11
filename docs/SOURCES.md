# Upstream source register

Checked 11 November 2026. These links are canonical starting points, not permanent guarantees. Recheck current terms before installation or testing.

## Repositories and documentation

- **OpenCode:** https://github.com/anomalyco/opencode and https://opencode.ai/docs/
  - Current upstream README uses the `dev` branch and documents `@opencode/cli` installation and built-in build/plan agents.
- **PentAGI:** https://github.com/vxcontrol/pentagi
  - README: https://raw.githubusercontent.com/vxcontrol/pentagi/main/README.md
  - EULA: https://github.com/vxcontrol/pentagi/blob/main/EULA.md
  - Review licensing, Docker access, agent networking and tool downloads before deployment.
- **CyberGym:** https://github.com/sunblaze-ucb/cybergym
  - README documents Python/Docker requirements, ~240GB benchmark data, ~10TB full server data, a 10-task subset, private binding and firewall guidance.
- **Ollama:** https://github.com/ollama/ollama and https://ollama.com/
  - Existing installation and models remain unverified until the user runs the PC audit / explicit connection test.
- **OpenRouter limits:** https://openrouter.ai/docs/api_reference/limits
  - Free limits and account conditions can change. SENTINEL does not hard-code the previously quoted 50/day figure.

## Researcher/platform rules

- **HackerOne — Hai Security & Trust:** https://docs.hackerone.com/en/articles/10908081-hai-security-trust
  - The researcher FAQ states that AI tools may not operate fully autonomously and that human experts must investigate, validate and confirm vulnerabilities before submission.
- **Intigriti — Community Code of Conduct:** https://kb.intigriti.com/en/articles/5247238-community-code-of-conduct
  - Responsible AI use is permitted; researchers must personally identify and verify issues, avoid fabricated/misleading content and disclose AI use.
- **Intigriti — payout lifecycle:** https://kb.intigriti.com/en/articles/3379564-payout-lifecycle
  - Programme acceptance and payout creation are real external events; SENTINEL records them only after user confirmation.

## Cost position

The local core uses open-source/runtime components and SQLite with no required subscription. Local inference still consumes hardware/electricity. Third-party tools, model providers, enterprise features and downloaded components can have separate costs or terms. No price is treated as permanently verified.
