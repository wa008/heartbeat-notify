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

The tool looks for a configuration file at `~/.heartbeat-notify/config.yaml` by default.

1. **Setup Configuration**:
   ```bash
   mkdir -p ~/.heartbeat-notify
   # Create your config file
   vim ~/.heartbeat-notify/config.yaml
   ```

2. **Run the Monitor**:
   ```bash
   # Runs with default config (~/.heartbeat-notify/config.yaml)
   heartbeat-notify

   # Or specify a custom config path
   heartbeat-notify --config my_custom_config.yaml
   ```

## Configuration

Example `config.yaml`:

```yaml
default_webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
log_file: "~/.heartbeat-notify/heartbeat.log"  # Optional: Write logs to file

# Schedule for "Process Alive" notifications (HH:MM in 24h format)
alive_schedule:
  - "09:00"
  - "17:00"

files:
  - name: "Database Backup"
    path: "/var/backups/db.sql"
    heartbeat_seconds: 3600  # Alert if not updated in 1 hour
    
  - name: "Log File"
    path: "/var/log/app.log"
    heartbeat_seconds: 300
    webhook_url: "https://discord.com/api/webhooks/ANOTHER_URL" # Override default URL
```
