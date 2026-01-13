import sys
import time
import logging
import yaml
import click
from pathlib import Path
from .monitor import AppConfig, check_file
from .notifier import send_discord_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("heartbeat-notify")

@click.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='Path to configuration YAML file.')
@click.option('--interval', '-i', type=int, help='Run in a loop with this interval in seconds. If not set, runs once.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging.')
def cli(config, interval, verbose):
    """
    Heartbeat Notify: Monitor file updates and notify via Discord.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    config_path = Path(config)
    
    # Load Config
    try:
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
        app_config = AppConfig(**raw_config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    logger.info(f"Loaded configuration with {len(app_config.files)} files to monitor.")

    # State for alive notifications (set of today's sent timestamps "HH:MM")
    # We clear this set when the day changes.
    last_sent_day = time.localtime().tm_yday
    sent_today = set()

    # Main Loop
    while True:
        current_time_struct = time.localtime()
        current_day = current_time_struct.tm_yday
        
        # Reset sent_today if day changed
        if current_day != last_sent_day:
            sent_today.clear()
            last_sent_day = current_day

        run_check_cycle(app_config)
        
        # Check alive schedule
        current_hhmm = time.strftime("%H:%M", current_time_struct)
        if current_hhmm in app_config.alive_schedule and current_hhmm not in sent_today:
            msg = f"🟢 **Process Alive**: Heartbeat monitor is running. Time: {current_hhmm}"
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

def run_check_cycle(app_config: AppConfig):
    for file_config in app_config.files:
        try:
            is_stalled = check_file(file_config)
            if is_stalled:
                url = file_config.webhook_url or app_config.default_webhook_url
                if url:
                    message = f"⚠️ **Heartbeat Missed**: File `{file_config.name}` (`{file_config.path}`) has not been updated in over {file_config.heartbeat_seconds} seconds."
                    logger.info(f"File {file_config.name} is stalled. Sending notification.")
                    send_discord_notification(url, message)
                    
                    # Optional: Avoid spamming? Currently it will spam every cycle.
                    # Ideally we should state manage this too, but per requirements we just notify.
                else:
                    logger.warning(f"File {file_config.name} is stalled but no webhook URL is configured.")
            else:
                logger.debug(f"File {file_config.name} is healthy.")
        except Exception as e:
            logger.error(f"Error checking file {file_config.name}: {e}")

if __name__ == "__main__":
    cli()
