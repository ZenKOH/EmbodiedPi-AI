# Local AI Setup

EmbodiedPi AI works without local AI by using the default `rule` provider. For local model experiments, use an Ollama-compatible endpoint.

## Ollama mode

```bash
export EMBODIEDPI_LLM_PROVIDER=ollama
export EMBODIEDPI_OLLAMA_URL=http://localhost:11434/api/generate
export EMBODIEDPI_OLLAMA_MODEL=llama3.2:1b
python -m embodiedpi.cli ask "please wave hello" --dry-run
```

## Raspberry Pi constraints

Treat Raspberry Pi as a hybrid edge system:

- rule mode for safe demos and testing;
- local small models for private light tasks;
- cloud mode for heavier reasoning;
- AI HAT+ / AI HAT+ 2 for supported vision and local acceleration experiments.

Regardless of model provider, keep JSON-only prompting and strict schema validation enabled.
