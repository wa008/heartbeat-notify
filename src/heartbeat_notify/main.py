import sys
import time
import logging
import yaml
import click
from pathlib import Path
from typing import Optional
from .monitor import AppConfig, check_file
from .notifier import send_discord_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("heartbeat-notify")

@click.command()
@click.option('--config', '-c', type=click.Path(), default='config.yaml', help='Path to configuration YAML file. Default is config.yaml.')
@click.option('--interval', '-i', type=int, default=60, help='Run in a loop with this interval in seconds. Default is 60. Set to 0 to run once.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging.')
def cli(config, interval, verbose):
    """
    Heartbeat Notify: Monitor file updates and notify via Discord.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    config_path = Path(config)
    
    # Load Config
    app_config = load_config(config_path)
    if not app_config:
        sys.exit(1)

    logger.info(f"Loaded configuration with {len(app_config.files)} files to monitor.")

    # State for alive notifications (set of today's sent timestamps "HH:MM")
    # We clear this set when the day changes.
    last_sent_day = time.localtime().tm_yday
    sent_today = set()

    # Track config file modification time
    last_config_mtime = get_config_mtime(config_path)

    # Track notified files to prevent spam
    # Set of file paths that we have already sent a stalled notification for.
    notified_files = set()

    # Main Loop
    while True:
        # Check for config updates
        current_config_mtime = get_config_mtime(config_path)
        if current_config_mtime != last_config_mtime:
            logger.info("Configuration file changed. Reloading...")
            new_config = load_config(config_path)
            if new_config:
                app_config = new_config
                last_config_mtime = current_config_mtime
                logger.info(f"Configuration reloaded. Monitoring {len(app_config.files)} files.")
                # We do NOT clear notified_files here to avoid re-notifying stale files just because config changed.
            else:
                logger.error("Failed to reload configuration. Keeping previous configuration.")
                # Update mtime anyway to avoid spamming error logs every cycle if the file remains broken
                last_config_mtime = current_config_mtime

        current_time_struct = time.localtime()
        current_day = current_time_struct.tm_yday
        
        # Reset sent_today if day changed
        if current_day != last_sent_day:
            sent_today.clear()
            last_sent_day = current_day

        run_check_cycle(app_config, notified_files)
        
        # Check alive schedule
        current_hhmm = time.strftime("%H:%M", current_time_struct)
        if current_hhmm in app_config.alive_schedule and current_hhmm not in sent_today:
            msg = (
                f"🟢 **Process Alive**\n"
                f"**Time**: {current_hhmm}\n"
                f"Heartbeat monitor is running successfully."
            )
            logger.info("Sending alive notification.")
            if app_config.default_webhook_url:
                send_discord_notification(app_config.default_webhook_url, msg)
                sent_today.add(current_hhmm)
            else:
                logger.warning("Alive schedule triggered but no default webhook URL configured.")

        if not interval:
            break
        
        logger.debug(f"Sleeping for {interval} seconds...")
        time.sleep(interval)

def get_config_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0

def load_config(path: Path) -> Optional[AppConfig]:
    try:
        with open(path, 'r') as f:
            raw_config = yaml.safe_load(f)
        return AppConfig(**raw_config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def run_check_cycle(app_config: AppConfig, notified_files: set):
    for file_config in app_config.files:
        try:
            is_stalled = check_file(file_config)
            file_id = str(file_config.resolved_path)
            
            if is_stalled:
                if file_id not in notified_files:
                    url = file_config.webhook_url or app_config.default_webhook_url
                    if url:
                        message = (
                            f"⚠️ **Heartbeat Missed**\n"
                            f"**File**: `{file_config.name}`\n"
                            f"**Path**: `{file_config.path}`\n"
                            f"**Status**: Stalled (No update in {file_config.heartbeat_seconds}s)"
                        )
                        logger.info(f"File {file_config.name} is stalled. Sending notification.")
                        send_discord_notification(url, message)
                        notified_files.add(file_id)
                    else:
                        logger.warning(f"File {file_config.name} is stalled but no webhook URL is configured.")
                else:
                    logger.debug(f"File {file_config.name} is stalled, but notification already sent.")
            else:
                logger.debug(f"File {file_config.name} is healthy.")
                if file_id in notified_files:
                    logger.info(f"File {file_config.name} has recovered. Resetting notification state.")
                    notified_files.remove(file_id)
                    
        except Exception as e:
            logger.error(f"Error checking file {file_config.name}: {e}")

if __name__ == "__main__":
    cli()
