# Prerequisites

Install these tools before using the Salesforce AI Workspace:

- Python 3.11 or newer.
- Git.
- Salesforce CLI `sf`.
- VS Code.
- GitHub Copilot access.
- Azure DevOps access to read Work Items through VS Code MCP.

Optional:

- Node.js/npm if the Salesforce project itself needs Node tooling.
- `pypdf` or `PyPDF2` only if PDF knowledge import is needed.
- GitHub CLI only if a future approved workflow explicitly requires it.

No external LLM API keys are required. Do not configure OpenAI, Anthropic, Gemini, LangChain, LangGraph, or provider-switching API keys for this workspace.

Do not configure ADO PATs or employee credentials in repository files. Azure DevOps authentication for `/fetch-us` is handled by VS Code and the approved read-only MCP flow.
