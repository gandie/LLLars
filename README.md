# LLLars - Large Language Lars

The stupid AI agent.

Ever wanted a small local-running code agent that just works?

This project is the result of countless hours of experimenting,
trying to find balance between 4 characteristics of an agent
driven coding task:

- Task design
- Model choice
- Tool orchestration
- Agentic coding process

While the first two items - "Task design" and "Model choice" may
live in user space, "Tool orchestration" and the "Agentic coding process"
itself are hidden behind walls not reachable for ordinary users.

In practice, poor balancing of those four items leads to chaos and
overengineering, in worst case even dressed as progress.

## Installation

### Requirements

- Python 3.11+
- PowerShell (Windows)
- A running Ollama endpoint (default: `http://localhost:11434`)

### Install from local source

```powershell
pip install .
```

This installs the `lllars` CLI entry point.

### Editable install (development)

```powershell
pip install -e .
```

### Quick start

1. Copy and adapt the example config:

```powershell
Copy-Item .\lllars.example.json .\lllars.json
```

2. Run the agent:

```powershell
lllars --config .\lllars.json --prompt "Describe this repository"
```