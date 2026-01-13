# Heartbeat Notify

A Python tool to monitor file modification times and send Discord notifications if a file hasn't been updated for a specified duration.

## Installation

```bash
# Install from PyPI
pip install heartbeat-notify

# Install locally (editable mode)
pip install -e .

# Install locally (using uv)
uv pip install .
```

## Usage

1. Create a configuration file (e.g., `config.yaml`).
2. Run the monitor:

```bash
heartbeat-notify --config config.yaml
```
