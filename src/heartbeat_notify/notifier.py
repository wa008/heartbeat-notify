import requests
import logging

logger = logging.getLogger(__name__)

def send_discord_notification(webhook_url: str, message: str):
    """
    Sends a message to a Discord webhook.
    """
    if not webhook_url:
        logger.warning("No webhook URL provided for notification.")
        return

    payload = {
        "content": message
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Notification sent successfully.")
    except requests.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
