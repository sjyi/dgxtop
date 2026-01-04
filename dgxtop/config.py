#!/usr/bin/env python3
"""Configuration management for DGXTOP Ubuntu"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorTheme:
    """Color theme for dashing components (0-8 color codes)"""

    name: str
    primary: int
    secondary: int
    warning: int
    critical: int


@dataclass
class AppConfig:
    """Application configuration"""

    update_interval: float = 1.0
    color_theme: str = "green"
    redline_threshold: float = 80.0
    history_length: int = 60
    log_level: str = "INFO"
    gpu_enabled: bool = True


COLOR_THEMES: Dict[str, ColorTheme] = {
    "green": ColorTheme("green", primary=2, secondary=2, warning=3, critical=1),
    "amber": ColorTheme("amber", primary=3, secondary=3, warning=1, critical=1),
    "blue": ColorTheme("blue", primary=4, secondary=6, warning=3, critical=1),
}
