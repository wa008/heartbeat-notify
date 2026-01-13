import time
import os
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class FileMonitorConfig(BaseModel):
    name: str
    path: Path
    heartbeat_seconds: int = Field(..., description="Time in seconds before considering the file stalled")
    webhook_url: Optional[str] = None
    
    @property
    def resolved_path(self) -> Path:
        return self.path.expanduser().resolve()

class AppConfig(BaseModel):
    default_webhook_url: Optional[str] = None
    files: List[FileMonitorConfig]
    alive_schedule: List[str] = Field(default_factory=list, description="List of times (HH:MM) to send alive notifications")
    log_file: Optional[str] = Field(None, description="Path to a log file")


def get_file_age(file_path: Path) -> float:
    """Returns the time in seconds since the last modification."""
    try:
        stat = file_path.stat()
        return time.time() - stat.st_mtime
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return float('inf')  # Treat missing file as infinitely old

def check_file(config: FileMonitorConfig) -> bool:
    """
    Checks if a file is stalled. Returns True if stalled, False otherwise.
    """
    path = config.resolved_path
    if not path.exists():
        logger.warning(f"File {config.name} at {path} does not exist.")
        return True # Missing file is effectively 'stalled' or broken heart
    
    age = get_file_age(path)
    logger.debug(f"File {config.name} age: {age:.2f}s (Threshold: {config.heartbeat_seconds}s)")
    
    return age > config.heartbeat_seconds
