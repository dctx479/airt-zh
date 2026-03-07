# AIRT — AI Red Team Academy

A free, open-source course covering offensive security testing of AI systems — from prompt injection to supply chain attacks. 60+ hours of content with hands-on Docker labs.

🌐 **[View the course →](https://0x4d31.github.io/airt/)**

## Modules

| # | Module | Topics |
|---|--------|--------|
| 1 | Foundations of AI Red Teaming | MITRE ATLAS, OWASP LLM Top 10, threat modeling |
| 2 | Prompt Injection Attacks | Direct/indirect injection, jailbreaks, filter bypasses |
| 3 | RAG Exploitation & Vector Database Attacks | Knowledge base poisoning, embedding attacks |
| 4 | Multi-Agent System Exploitation | Agent hijacking, tool abuse, memory poisoning |
| 5 | AI Supply Chain & Infrastructure Attacks | Model backdoors, pickle exploits, dependency attacks |
| 6 | Model Extraction & Inference Attacks | Model stealing, membership inference, side channels |
| 7 | Automated AI Red Teaming at Scale | garak, PyRIT, promptfoo, CI/CD integration |
| 8 | Post-Exploitation & Impact Analysis | Lateral movement, reporting, regulatory frameworks |

## Hands-on Labs

Each module includes a Docker-based lab environment. No cloud API keys needed — everything runs locally via [Ollama](https://ollama.com/).

### Quick Start

```bash
# Clone the repo
git clone https://github.com/0x4d31/airt.git
cd airt/labs

# Start any lab (e.g., Lab 01)
cd lab01-foundations
docker compose up

# Access the lab interface
open http://localhost:8888
```

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- 8 GB+ RAM (16 GB recommended for Labs 07–08)
- ~20 GB disk space for model downloads

## License

Content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Code and lab files are licensed under [MIT](LICENSE).

---

Built with [Perplexity Computer](https://www.perplexity.ai/computer).
