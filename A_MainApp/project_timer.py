from __future__ import annotations

import csv
import json
import os
import random
import shutil
import sys
import time
from ctypes import POINTER, byref, c_int, c_void_p, cast, sizeof, wintypes
from dataclasses import dataclass
from pathlib import Path

try:
    from ctypes import windll
except ImportError:
    windll = None

try:
    from PySide6.QtCore import QFileSystemWatcher, QPoint, QRectF, QSize, Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient, QTransform
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFrame,
        QGraphicsBlurEffect,
        QGraphicsPixmapItem,
        QGraphicsScene,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSlider,
        QSizePolicy,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:
    print("PySide6 is required. Install it with: python -m pip install -r requirements.txt")
    raise error


APP_NAME = "ProjectTimer"
APP_VERSION = "V1.2_pre"
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)).resolve()


def can_write_to_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".project_timer_write_test"
        test_file.write_text("", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def app_data_dir() -> Path:
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent

    portable_dir = Path(sys.executable).resolve().parent
    if can_write_to_directory(portable_dir):
        return portable_dir

    roaming = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return roaming / APP_NAME


APP_DIR = app_data_dir()
DATA_DIR = APP_DIR / "data"
CONFIG_DIR = APP_DIR / "config"
DATA_FILE = DATA_DIR / "projects.csv"
ARCHIVE_FILE = DATA_DIR / "archive.csv"
ICON_DIR = APP_DIR / "icons"
BACKGROUND_DIR = APP_DIR / "backgrounds"
FONT_DIR = APP_DIR / "fonts"
THEMES_FILE = CONFIG_DIR / "themes.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

BASE_WIDTH = 260
BASE_HEIGHT = 135
DEFAULT_WIDTH = 430
DEFAULT_HEIGHT = round(DEFAULT_WIDTH * BASE_HEIGHT / BASE_WIDTH)
DEFAULT_SCALE = DEFAULT_WIDTH / BASE_WIDTH
MIN_WINDOW_SCALE = 1.0
MAX_WINDOW_SCALE = 3.0
WINDOW_SCALE_STEP = 0.2
MIN_WINDOW_WIDTH = BASE_WIDTH
MIN_WINDOW_HEIGHT = BASE_HEIGHT
MAX_WINDOW_WIDTH = round(BASE_WIDTH * MAX_WINDOW_SCALE)
MAX_WINDOW_HEIGHT = round(BASE_HEIGHT * MAX_WINDOW_SCALE)
LIST_MAX_VISIBLE_PROJECTS = 10
LIST_ROW_BASE_HEIGHT = 26
LIST_ARROW_BASE_SIZE = 12
LIST_ARROW_GAP_BASE = 2
LIST_ARROW_VERTICAL_PADDING_BASE = 2
QT_MAX_WIDGET_SIZE = 16777215
PROJECT_NAME_MAX_LENGTH = 32

WM_SIZING = 0x0214
WMSZ_LEFT = 1
WMSZ_RIGHT = 2
WMSZ_TOP = 3
WMSZ_TOPLEFT = 4
WMSZ_TOPRIGHT = 5
WMSZ_BOTTOM = 6
WMSZ_BOTTOMLEFT = 7
WMSZ_BOTTOMRIGHT = 8
LEFT_RESIZE_EDGES = {WMSZ_LEFT, WMSZ_TOPLEFT, WMSZ_BOTTOMLEFT}
RIGHT_RESIZE_EDGES = {WMSZ_RIGHT, WMSZ_TOPRIGHT, WMSZ_BOTTOMRIGHT}
TOP_RESIZE_EDGES = {WMSZ_TOP, WMSZ_TOPLEFT, WMSZ_TOPRIGHT}
BOTTOM_RESIZE_EDGES = {WMSZ_BOTTOM, WMSZ_BOTTOMLEFT, WMSZ_BOTTOMRIGHT}

CSV_DELIMITER = ";"
CSV_HEADERS = ("name", "time")
DEFAULT_PROJECTS_CSV = (
    "name;time\n"
    "Default;00:00:00\n"
)
DEFAULT_ARCHIVE_CSV = "name;time\n"
DEFAULT_SETTINGS_JSON = """{
  "theme_name": "Obsidian",
  "theme_index": 0,
  "last_project_name": "Default",
  "last_project_index": 0,
  "window_width": 430,
  "window_scale": 1.6538,
  "window_x": null,
  "window_y": null,
  "always_on_top": false,
  "list_mode": false,
  "time_style": "clean"
}
"""
MIN_WINDOW_OPACITY = 45
MAX_WINDOW_OPACITY = 100
DEFAULT_WINDOW_OPACITY = 100
BACKGROUND_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
FONT_EXTENSIONS = (".ttf", ".otf", ".ttc")
DEFAULT_FONT_FAMILY = "Segoe UI"
MIN_FONT_SCALE = 70
MAX_FONT_SCALE = 140
DEFAULT_FONT_SCALE = 100
FONT_SCALE_STEP = 5
THEME_FONT_FAMILIES: list[str] | None = None

THEME_COLOR_FIELDS = (
    "bg",
    "surface",
    "surface_lift",
    "surface_press",
    "border",
    "text",
    "muted",
    "icon",
    "primary",
    "accent",
)

BLUR_DIRECTION_OPTIONS = ("gaussian", "0", "45", "90")
BLUR_DIRECTION_LABELS = {
    "gaussian": "Gaussian",
    "0": "0 deg",
    "45": "45 deg",
    "90": "90 deg",
}

THEME_COLOR_LABELS = (
    ("bg", "Background"),
    ("surface", "Button surface"),
    ("surface_lift", "Hover surface"),
    ("surface_press", "Pressed surface"),
    ("border", "Border"),
    ("text", "Main text"),
    ("muted", "Muted text"),
    ("icon", "Icons"),
    ("primary", "Active button"),
    ("accent", "Active hover"),
)

PICKER_HUES = (0, 14, 28, 42, 56, 72, 92, 112, 132, 154, 176, 198, 218, 238, 258, 278, 298, 318, 338)
PICKER_LIGHTNESS = (22, 42, 62, 84, 106, 130, 154, 178, 204, 230)

DEFAULT_THEME_SETTINGS = {
    "background_enabled": True,
    "animation_enabled": True,
    "glass_enabled": True,
    "background_blur": 28,
    "background_blur_direction": "gaussian",
    "window_opacity": DEFAULT_WINDOW_OPACITY,
    "font_family": DEFAULT_FONT_FAMILY,
    "font_scale": DEFAULT_FONT_SCALE,
    "background_image": "",
}

DEFAULT_THEMES = (
    {
        "name": "Obsidian",
        "bg": "#151515",
        "surface": "#202124",
        "surface_lift": "#2a2b2d",
        "surface_press": "#18191a",
        "border": "#303035",
        "text": "#f4f4f5",
        "muted": "#a1a1aa",
        "icon": "#a1a1aa",
        "primary": "#2dd4bf",
        "accent": "#a3e635",
        **DEFAULT_THEME_SETTINGS,
    },
    {
        "name": "Graphite",
        "bg": "#111318",
        "surface": "#1e222a",
        "surface_lift": "#292f39",
        "surface_press": "#171a20",
        "border": "#363d48",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "icon": "#94a3b8",
        "primary": "#38bdf8",
        "accent": "#c4b5fd",
        **DEFAULT_THEME_SETTINGS,
    },
    {
        "name": "Soft Circuit",
        "bg": "#0e1514",
        "surface": "#182321",
        "surface_lift": "#223330",
        "surface_press": "#111a18",
        "border": "#2f4641",
        "text": "#eefbf7",
        "muted": "#8eb0a8",
        "icon": "#8eb0a8",
        "primary": "#5eead4",
        "accent": "#f0abfc",
        **DEFAULT_THEME_SETTINGS,
    },
    {
        "name": "Neo Tokyo",
        "bg": "#100d18",
        "surface": "#1f1830",
        "surface_lift": "#302347",
        "surface_press": "#171124",
        "border": "#4a3569",
        "text": "#f8f5ff",
        "muted": "#b7a6d9",
        "icon": "#b7a6d9",
        "primary": "#ff4fd8",
        "accent": "#22d3ee",
        **DEFAULT_THEME_SETTINGS,
    },
    {
        "name": "Cyber Lime",
        "bg": "#090d0b",
        "surface": "#121914",
        "surface_lift": "#1c271f",
        "surface_press": "#0c120e",
        "border": "#2b3f30",
        "text": "#f3fff5",
        "muted": "#9ab99f",
        "icon": "#9ab99f",
        "primary": "#a3ff12",
        "accent": "#00e5ff",
        **DEFAULT_THEME_SETTINGS,
    },
    {
        "name": "Vapor Grid",
        "bg": "#0d1020",
        "surface": "#181d33",
        "surface_lift": "#242b49",
        "surface_press": "#11162a",
        "border": "#354069",
        "text": "#f3f6ff",
        "muted": "#9aa9d9",
        "icon": "#9aa9d9",
        "primary": "#8b5cf6",
        "accent": "#06b6d4",
        **DEFAULT_THEME_SETTINGS,
    },
    {
        "name": "Ember Lounge",
        "bg": "#171211",
        "surface": "#231c1a",
        "surface_lift": "#302622",
        "surface_press": "#191312",
        "border": "#4a3831",
        "text": "#fff4ee",
        "muted": "#c9a99b",
        "icon": "#d6b3a4",
        "primary": "#ff7a59",
        "accent": "#ffd166",
        **DEFAULT_THEME_SETTINGS,
    },
)

BACKGROUND_SHAPE_PROFILES = {
    "Obsidian": (
        {"x": 0.10, "y": 0.24, "target_x": 1.10, "target_y": 0.14, "speed": 0.020, "radius": 0.64, "color": "primary"},
        {"x": 0.92, "y": 0.82, "target_x": -0.18, "target_y": 0.72, "speed": 0.015, "radius": 0.58, "color": "accent"},
    ),
    "Graphite": (
        {"x": 0.28, "y": -0.10, "target_x": 0.94, "target_y": 1.04, "speed": 0.018, "radius": 0.68, "color": "primary"},
        {"x": 0.98, "y": 0.44, "target_x": -0.22, "target_y": 0.58, "speed": 0.014, "radius": 0.56, "color": "accent"},
    ),
    "Mint": (
        {"x": 0.18, "y": 0.86, "target_x": 0.88, "target_y": 0.04, "speed": 0.017, "radius": 0.60, "color": "primary"},
        {"x": 1.08, "y": 0.20, "target_x": -0.12, "target_y": 0.36, "speed": 0.013, "radius": 0.52, "color": "accent"},
    ),
    "Lofi Slate": (
        {"x": -0.12, "y": 0.42, "target_x": 1.10, "target_y": 0.34, "speed": 0.016, "radius": 0.62, "color": "primary"},
        {"x": 0.72, "y": 1.08, "target_x": 0.24, "target_y": -0.12, "speed": 0.014, "radius": 0.54, "color": "accent"},
    ),
    "Soft Circuit": (
        {"x": 0.04, "y": 0.72, "target_x": 0.98, "target_y": 0.10, "speed": 0.019, "radius": 0.64, "color": "primary"},
        {"x": 0.86, "y": 0.10, "target_x": -0.18, "target_y": 0.96, "speed": 0.013, "radius": 0.58, "color": "accent"},
    ),
    "Neo Tokyo": (
        {"x": 0.12, "y": 0.16, "target_x": 0.98, "target_y": 0.84, "speed": 0.021, "radius": 0.68, "color": "primary"},
        {"x": 1.12, "y": 0.78, "target_x": -0.16, "target_y": 0.22, "speed": 0.016, "radius": 0.56, "color": "accent"},
    ),
    "Cyber Lime": (
        {"x": 0.24, "y": 1.12, "target_x": 0.66, "target_y": -0.18, "speed": 0.022, "radius": 0.62, "color": "primary"},
        {"x": -0.18, "y": 0.28, "target_x": 1.16, "target_y": 0.52, "speed": 0.018, "radius": 0.54, "color": "accent"},
    ),
    "Vapor Grid": (
        {"x": 0.18, "y": 0.32, "target_x": 1.16, "target_y": 0.18, "speed": 0.022, "radius": 0.62, "color": "primary"},
        {"x": 0.82, "y": 0.74, "target_x": -0.22, "target_y": 0.94, "speed": 0.017, "radius": 0.54, "color": "accent"},
    ),
    "Ember Lounge": (
        {"x": 0.08, "y": 0.76, "target_x": 0.92, "target_y": 0.20, "speed": 0.016, "radius": 0.62, "color": "primary"},
        {"x": 1.02, "y": 0.18, "target_x": -0.14, "target_y": 0.68, "speed": 0.013, "radius": 0.54, "color": "accent"},
    ),
}

ICON_FILE_NAMES = {
    "app": ("app.ico", "time.ico", "timer.ico", "play.ico"),
    "empty": ("empty.ico",),
    "play": ("play.ico",),
    "stop": ("pause.ico",),
    "reset": ("reset.ico",),
    "plus": ("plus.ico", "add.ico"),
    "edit": ("edit.ico",),
    "trash": ("trash.ico", "delete.ico"),
    "lock": ("lock.ico",),
    "unlock": ("unlock.ico", "lock.ico"),
    "zoom_in": ("zoomIn.ico", "zoom_in.ico", "zoom-in.ico"),
    "zoom_out": ("zoomOut.ico", "zoom_out.ico", "zoom-out.ico"),
    "build": ("build.ico", "builder.ico", "theme.ico"),
    "list": ("list.ico",),
    "duplicate": ("duplicate.ico", "copy.ico"),
    "move_up": ("play.ico",),
    "move_down": ("play.ico",),
}
TINTED_ICON_CACHE: dict[tuple[str, str, str], QIcon] = {}
ICON_ROTATIONS = {
    "move_up": -90,
    "move_down": 90,
}


@dataclass
class Project:
    name: str
    seconds: float = 0.0


def format_seconds(seconds: float) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"


def format_seconds_with_units(seconds: float) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02}h:{minutes:02}m:{secs:02}s"


def parse_time_value(value: str) -> int:
    value = value.strip()
    if not value:
        return 0
    if value.isdigit():
        return int(value)

    value = value.replace("h", ":").replace("m", ":").replace("s", "")
    parts = [part for part in value.split(":") if part != ""]
    if len(parts) not in (2, 3):
        raise ValueError("Use seconds, MM:SS, or HH:MM:SS.")
    if any(not part.strip().isdigit() for part in parts):
        raise ValueError("Time can only contain numbers and colons.")

    numbers = [int(part.strip()) for part in parts]
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds

    hours, minutes, seconds = numbers
    return hours * 3600 + minutes * 60 + seconds


def clean_project_name(name: str) -> str:
    return " ".join(name.strip().split())[:PROJECT_NAME_MAX_LENGTH]


def icon_path(name: str) -> str:
    for file_name in ICON_FILE_NAMES.get(name, ()):
        path = ICON_DIR / file_name
        if path.exists():
            return str(path)
    return ""


def tinted_icon(path: str, color: str, rotation: int = 0) -> QIcon:
    normalized = normalize_hex(color, "#000000") or "#000000"
    cache_key = (path, normalized, str(rotation))
    cached = TINTED_ICON_CACHE.get(cache_key)
    if cached is not None:
        return cached

    source_icon = QIcon(path)
    source = source_icon.pixmap(QSize(256, 256))
    if source.isNull():
        return source_icon
    if rotation:
        source = source.transformed(QTransform().rotate(rotation), Qt.TransformationMode.SmoothTransformation)

    tinted = QPixmap(source.size())
    tinted.fill(Qt.GlobalColor.transparent)
    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(normalized))
    painter.end()

    icon = QIcon(tinted)
    TINTED_ICON_CACHE[cache_key] = icon
    return icon


def ensure_background_dir() -> None:
    BACKGROUND_DIR.mkdir(exist_ok=True)


def ensure_font_dir() -> None:
    FONT_DIR.mkdir(exist_ok=True)


def list_background_images() -> list[str]:
    ensure_background_dir()
    images = [
        path.name
        for path in BACKGROUND_DIR.iterdir()
        if path.is_file() and path.suffix.casefold() in BACKGROUND_IMAGE_EXTENSIONS
    ]
    return sorted(images, key=str.casefold)


def register_theme_fonts(force: bool = False) -> list[str]:
    global THEME_FONT_FAMILIES
    if THEME_FONT_FAMILIES is not None and not force:
        return THEME_FONT_FAMILIES

    ensure_font_dir()
    families = [DEFAULT_FONT_FAMILY]
    for path in FONT_DIR.iterdir():
        if not path.is_file() or path.suffix.casefold() not in FONT_EXTENSIONS:
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            continue
        for family in QFontDatabase.applicationFontFamilies(font_id):
            if family and family not in families:
                families.append(family)
    THEME_FONT_FAMILIES = families
    return families


def list_theme_fonts() -> list[str]:
    return register_theme_fonts(force=True)


def theme_font_family(theme: dict[str, object]) -> str:
    family = " ".join(str(theme.get("font_family", DEFAULT_FONT_FAMILY)).strip().split())
    return family or DEFAULT_FONT_FAMILY


def resolved_theme_font_family(theme: dict[str, object]) -> str:
    requested_family = theme_font_family(theme)
    for family in register_theme_fonts():
        if family.casefold() == requested_family.casefold():
            return family
    return DEFAULT_FONT_FAMILY


def theme_font_scale(theme: dict[str, object]) -> int:
    return clamp_int(theme.get("font_scale", DEFAULT_FONT_SCALE), MIN_FONT_SCALE, MAX_FONT_SCALE, DEFAULT_FONT_SCALE)


def scaled_font_size(size: int | float, theme: dict[str, object]) -> int:
    return max(1, round(float(size) * theme_font_scale(theme) / 100))


def qss_font_family(family: str) -> str:
    clean_family = theme_font_family({"font_family": family}).replace("\\", "\\\\").replace('"', '\\"')
    if clean_family == DEFAULT_FONT_FAMILY:
        return f'"{DEFAULT_FONT_FAMILY}", sans-serif'
    return f'"{clean_family}", "{DEFAULT_FONT_FAMILY}", sans-serif'


def background_image_path(file_name: object) -> Path | None:
    name = Path(str(file_name).strip()).name
    if not name:
        return None

    path = BACKGROUND_DIR / name
    if path.is_file() and path.suffix.casefold() in BACKGROUND_IMAGE_EXTENSIONS:
        return path
    return None


def bool_from_theme(value: object, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().casefold()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    return fallback


def clamp_int(value: object, low: int, high: int, fallback: int) -> int:
    try:
        number = int(float(str(value)))
    except (TypeError, ValueError):
        number = fallback
    return max(low, min(high, number))


def normalize_hex(value: object, fallback: str | None = "#000000") -> str | None:
    text = str(value).strip()
    if text and not text.startswith("#") and len(text) == 6:
        text = f"#{text}"

    color = QColor(text)
    if color.isValid():
        return color.name()
    return fallback


def theme_name(value: object, fallback: str = "Custom") -> str:
    name = " ".join(str(value).strip().split())
    return name or fallback


def copy_theme(theme: dict[str, object], fallback: dict[str, str] | None = None) -> dict[str, str]:
    base = dict(fallback or DEFAULT_THEMES[0])
    clean_theme = {"name": theme_name(theme.get("name", base["name"]), base["name"])}
    for field in THEME_COLOR_FIELDS:
        clean_theme[field] = normalize_hex(theme.get(field, base[field]), base[field]) or base[field]

    clean_theme["background_enabled"] = bool_from_theme(
        theme.get("background_enabled", base.get("background_enabled", True)),
        True,
    )
    clean_theme["animation_enabled"] = bool_from_theme(
        theme.get("animation_enabled", base.get("animation_enabled", True)),
        True,
    )
    clean_theme["glass_enabled"] = bool_from_theme(
        theme.get("glass_enabled", base.get("glass_enabled", True)),
        True,
    )
    clean_theme["background_blur"] = clamp_int(
        theme.get("background_blur", base.get("background_blur", 28)),
        0,
        100,
        28,
    )
    clean_theme["background_blur_direction"] = normalize_blur_direction(
        theme.get("background_blur_direction", base.get("background_blur_direction", "gaussian"))
    )
    clean_theme["window_opacity"] = clamp_int(
        theme.get("window_opacity", base.get("window_opacity", DEFAULT_WINDOW_OPACITY)),
        MIN_WINDOW_OPACITY,
        MAX_WINDOW_OPACITY,
        DEFAULT_WINDOW_OPACITY,
    )
    clean_theme["font_family"] = theme_font_family({"font_family": theme.get("font_family", base.get("font_family", DEFAULT_FONT_FAMILY))})
    clean_theme["font_scale"] = theme_font_scale({"font_scale": theme.get("font_scale", base.get("font_scale", DEFAULT_FONT_SCALE))})

    image_name = Path(str(theme.get("background_image", base.get("background_image", ""))).strip()).name
    clean_theme["background_image"] = image_name if Path(image_name).suffix.casefold() in BACKGROUND_IMAGE_EXTENSIONS else ""
    return clean_theme


def load_themes() -> list[dict[str, str]]:
    defaults = [copy_theme(theme) for theme in DEFAULT_THEMES]
    if not THEMES_FILE.exists():
        return defaults

    try:
        data = json.loads(THEMES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return defaults

    raw_themes = data.get("themes", data) if isinstance(data, dict) else data
    if not isinstance(raw_themes, list):
        return defaults

    themes: list[dict[str, str]] = []
    for index, theme in enumerate(raw_themes):
        if isinstance(theme, dict):
            fallback = DEFAULT_THEMES[index % len(DEFAULT_THEMES)]
            themes.append(copy_theme(theme, fallback))
    return themes or defaults


def save_themes(themes: list[dict[str, str]]) -> None:
    payload = {"themes": [copy_theme(theme) for theme in themes]}
    THEMES_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_settings() -> dict[str, object]:
    if not SETTINGS_FILE.exists():
        return {}

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(settings: dict[str, object]) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def default_themes_json() -> str:
    return json.dumps({"themes": [copy_theme(theme) for theme in DEFAULT_THEMES]}, indent=2)


def copy_missing_file(target: Path, bundled_sources: Path | tuple[Path, ...], fallback_text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return

    sources = bundled_sources if isinstance(bundled_sources, tuple) else (bundled_sources,)
    for source in sources:
        try:
            if source.exists() and source.resolve() != target.resolve():
                shutil.copy2(source, target)
                return
        except OSError:
            pass

    target.write_text(fallback_text, encoding="utf-8")


def copy_missing_directory_files(target: Path, bundled_source: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    try:
        if not bundled_source.exists() or bundled_source.resolve() == target.resolve():
            return
    except OSError:
        return

    for item in bundled_source.iterdir():
        destination = target / item.name
        if destination.exists():
            continue
        if item.is_dir():
            shutil.copytree(item, destination)
        elif item.is_file():
            shutil.copy2(item, destination)


def ensure_app_files() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    copy_missing_file(DATA_FILE, (BUNDLE_DIR / "data" / "projects.csv", APP_DIR / "projects.csv", BUNDLE_DIR / "projects.csv"), DEFAULT_PROJECTS_CSV)
    copy_missing_file(ARCHIVE_FILE, (BUNDLE_DIR / "data" / "archive.csv", APP_DIR / "archive.csv", BUNDLE_DIR / "archive.csv"), DEFAULT_ARCHIVE_CSV)
    copy_missing_file(THEMES_FILE, (BUNDLE_DIR / "config" / "themes.json", APP_DIR / "themes.json", BUNDLE_DIR / "themes.json"), default_themes_json())
    copy_missing_file(SETTINGS_FILE, (BUNDLE_DIR / "config" / "settings.json", APP_DIR / "settings.json", BUNDLE_DIR / "settings.json"), DEFAULT_SETTINGS_JSON)
    copy_missing_directory_files(ICON_DIR, BUNDLE_DIR / "icons")
    copy_missing_directory_files(BACKGROUND_DIR, BUNDLE_DIR / "backgrounds")
    copy_missing_directory_files(FONT_DIR, BUNDLE_DIR / "fonts")


def qss_rgba(value: str, alpha: int) -> str:
    red, green, blue = hex_to_rgb(value)
    return f"rgba({red}, {green}, {blue}, {max(0, min(255, alpha))})"


def theme_background_enabled(theme: dict[str, object]) -> bool:
    return bool_from_theme(theme.get("background_enabled"), True)


def theme_animation_enabled(theme: dict[str, object]) -> bool:
    return bool_from_theme(theme.get("animation_enabled"), True)


def theme_glass_enabled(theme: dict[str, object]) -> bool:
    return bool_from_theme(theme.get("glass_enabled"), True)


def theme_background_blur(theme: dict[str, object]) -> int:
    return clamp_int(theme.get("background_blur"), 0, 100, 28)


def normalize_blur_direction(value: object) -> str:
    direction = str(value).strip().casefold()
    return direction if direction in BLUR_DIRECTION_OPTIONS else "gaussian"


def theme_background_blur_direction(theme: dict[str, object]) -> str:
    return normalize_blur_direction(theme.get("background_blur_direction", "gaussian"))


def theme_window_opacity(theme: dict[str, object]) -> int:
    return clamp_int(theme.get("window_opacity"), MIN_WINDOW_OPACITY, MAX_WINDOW_OPACITY, DEFAULT_WINDOW_OPACITY)


def background_shape_profile(theme_name_value: str) -> tuple[dict[str, float | str], ...]:
    profile = BACKGROUND_SHAPE_PROFILES.get(theme_name_value)
    if profile is None:
        clean_name = theme_name_value.casefold()
        for profile_name, candidate in BACKGROUND_SHAPE_PROFILES.items():
            if clean_name.startswith(f"{profile_name.casefold()} copy"):
                profile = candidate
                break
    return profile or BACKGROUND_SHAPE_PROFILES["Vapor Grid"]


def paint_cover_pixmap(painter: QPainter, pixmap: QPixmap, size: QSize) -> None:
    if pixmap.isNull():
        return

    scaled = pixmap.scaled(
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = (size.width() - scaled.width()) // 2
    y = (size.height() - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)


def paint_soft_background_circle(
    painter: QPainter,
    theme: dict[str, str],
    shape: dict[str, float | str],
    width: int,
    height: int,
    alpha_scale: float = 1.0,
) -> None:
    shortest_side = min(width, height)
    color = QColor(theme[str(shape["color"])])
    center_x = float(shape["x"]) * width
    center_y = float(shape["y"]) * height
    radius = shortest_side * float(shape["radius"]) * 1.18

    gradient = QRadialGradient(center_x, center_y, radius)
    stops = (
        (0.0, 108),
        (0.32, 42),
        (0.56, 13),
        (0.74, 4),
        (0.90, 0),
        (1.0, 0),
    )
    for stop, alpha in stops:
        stop_color = QColor(color)
        stop_color.setAlpha(max(0, min(255, round(alpha * alpha_scale))))
        gradient.setColorAt(stop, stop_color)

    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))


def blur_scale_for_pixmap(pixmap: QPixmap) -> float:
    if pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
        return 1.0
    return max(1.0, min(3.2, min(pixmap.width() / BASE_WIDTH, pixmap.height() / BASE_HEIGHT)))


def blur_radius_for_pixmap(pixmap: QPixmap, blur_index: int) -> float:
    strength = max(0, min(100, blur_index)) / 100.0
    return (0.8 + strength * 30.0) * blur_scale_for_pixmap(pixmap)


def gaussian_like_blur(pixmap: QPixmap, blur_index: int) -> QPixmap:
    blur_index = max(0, min(100, blur_index))
    if pixmap.isNull() or blur_index <= 0:
        return pixmap

    radius = blur_radius_for_pixmap(pixmap, blur_index)
    margin = max(4, round(radius * 2.2))
    padded = QPixmap(pixmap.width() + margin * 2, pixmap.height() + margin * 2)
    padded.fill(Qt.GlobalColor.transparent)

    pad_painter = QPainter(padded)
    pad_painter.drawPixmap(margin, margin, pixmap)
    pad_painter.end()

    blur_effect = QGraphicsBlurEffect()
    blur_effect.setBlurRadius(radius)
    blur_effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)

    item = QGraphicsPixmapItem(padded)
    item.setGraphicsEffect(blur_effect)

    scene = QGraphicsScene()
    scene.setSceneRect(QRectF(0, 0, padded.width(), padded.height()))
    scene.addItem(item)

    blurred = QPixmap(padded.size())
    blurred.fill(Qt.GlobalColor.transparent)
    blur_painter = QPainter(blurred)
    blur_painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    blur_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    scene.render(blur_painter, QRectF(blurred.rect()), QRectF(blurred.rect()))
    blur_painter.end()

    return blurred.copy(margin, margin, pixmap.width(), pixmap.height())


def directional_blur(pixmap: QPixmap, blur_index: int, direction: str) -> QPixmap:
    source = gaussian_like_blur(pixmap, min(22, max(0, blur_index // 3)))
    radius = max(1, round((2 + (blur_index / 100.0) * 30) * blur_scale_for_pixmap(pixmap)))
    samples = max(7, min(35, radius * 2 + 1))
    half = max(1.0, (samples - 1) / 2.0)
    vector = {
        "0": (1.0, 0.0),
        "45": (0.707, 0.707),
        "90": (0.0, 1.0),
    }.get(direction, (1.0, 0.0))

    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.setOpacity(0.18)
    painter.drawPixmap(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
    painter.setOpacity(0.82 / samples)
    for index in range(samples):
        offset = ((index - half) / half) * radius
        painter.drawPixmap(round(vector[0] * offset), round(vector[1] * offset), source)
    painter.end()

    return gaussian_like_blur(result, min(20, max(0, blur_index // 5)))


def blurred_pixmap(pixmap: QPixmap, blur_index: int, direction: str = "gaussian") -> QPixmap:
    blur_index = max(0, min(100, blur_index))
    if pixmap.isNull() or blur_index <= 0:
        return pixmap

    direction = normalize_blur_direction(direction)
    if direction == "gaussian":
        return gaussian_like_blur(pixmap, blur_index)
    return directional_blur(pixmap, blur_index, direction)


def paint_background_layers(
    painter: QPainter,
    theme: dict[str, str],
    size: QSize,
    shapes: list[dict[str, float | str]] | tuple[dict[str, float | str], ...],
    image_pixmap: QPixmap | None = None,
    alpha_scale: float = 1.0,
) -> None:
    if size.width() <= 0 or size.height() <= 0:
        return

    layer = QPixmap(size)
    layer.fill(Qt.GlobalColor.transparent)
    layer_painter = QPainter(layer)
    layer_painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pixmap = image_pixmap or QPixmap()
    if theme_background_enabled(theme) and pixmap.isNull():
        image_path = background_image_path(theme.get("background_image", ""))
        pixmap = QPixmap(str(image_path)) if image_path is not None else QPixmap()
    if theme_background_enabled(theme) and not pixmap.isNull():
        paint_cover_pixmap(layer_painter, pixmap, size)
        tint = QColor(theme["bg"])
        tint.setAlpha(74)
        layer_painter.fillRect(0, 0, size.width(), size.height(), tint)

    if theme_animation_enabled(theme):
        circle_alpha = min(1.45, alpha_scale * (1.0 + theme_background_blur(theme) / 180.0))
        layer_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        for shape in shapes:
            paint_soft_background_circle(layer_painter, theme, shape, max(1, size.width()), max(1, size.height()), circle_alpha)

    layer_painter.end()
    painter.drawPixmap(0, 0, blurred_pixmap(layer, theme_background_blur(theme), theme_background_blur_direction(theme)))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        return (0, 0, 0)
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def windows_colorref(value: str) -> int:
    red, green, blue = hex_to_rgb(value)
    return red | (green << 8) | (blue << 16)


def set_windows_title_bar_colors(window: QWidget, caption_color: str, text_color: str) -> None:
    if windll is None:
        return

    try:
        hwnd = int(window.winId())
        caption = c_int(windows_colorref(caption_color))
        text = c_int(windows_colorref(text_color))
        border = c_int(windows_colorref(caption_color))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(caption), sizeof(caption))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, byref(text), sizeof(text))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, byref(border), sizeof(border))
    except Exception:
        pass


def clamp_window_width(width: int) -> int:
    return max(MIN_WINDOW_WIDTH, min(MAX_WINDOW_WIDTH, width))


def clamp_window_height(height: int, base_height: int = BASE_HEIGHT) -> int:
    min_height = round(MIN_WINDOW_SCALE * base_height)
    max_height = round(MAX_WINDOW_SCALE * base_height)
    return max(min_height, min(max_height, height))


def window_aspect_ratio(base_height: int = BASE_HEIGHT) -> float:
    return BASE_WIDTH / max(1, base_height)


def ratio_size_from_width(width: int, base_height: int = BASE_HEIGHT) -> QSize:
    aspect_ratio = window_aspect_ratio(base_height)
    width = clamp_window_width(width)
    height = clamp_window_height(round(width / aspect_ratio), base_height)
    width = clamp_window_width(round(height * aspect_ratio))
    height = clamp_window_height(round(width / aspect_ratio), base_height)
    return QSize(width, height)


def ratio_size_from_height(height: int, base_height: int = BASE_HEIGHT) -> QSize:
    aspect_ratio = window_aspect_ratio(base_height)
    height = clamp_window_height(height, base_height)
    width = clamp_window_width(round(height * aspect_ratio))
    height = clamp_window_height(round(width / aspect_ratio), base_height)
    return QSize(width, height)


def ratio_size_for_resize(size: QSize, old_size: QSize | None = None, base_height: int = BASE_HEIGHT) -> QSize:
    aspect_ratio = window_aspect_ratio(base_height)
    if old_size is None or old_size.width() <= 0 or old_size.height() <= 0:
        width_driven = size.width() / max(1, size.height()) >= aspect_ratio
    else:
        width_driven = abs(size.width() - old_size.width()) >= abs(size.height() - old_size.height())
    return ratio_size_from_width(size.width(), base_height) if width_driven else ratio_size_from_height(size.height(), base_height)


def enforce_windows_resize_rect(
    rect: wintypes.RECT,
    edge: int,
    frame_extra_width: int = 0,
    frame_extra_height: int = 0,
    base_height: int = BASE_HEIGHT,
) -> None:
    aspect_ratio = window_aspect_ratio(base_height)
    client_width = clamp_window_width((rect.right - rect.left) - frame_extra_width)
    client_height = clamp_window_height((rect.bottom - rect.top) - frame_extra_height, base_height)

    horizontal_only = edge in (LEFT_RESIZE_EDGES | RIGHT_RESIZE_EDGES) and edge not in (TOP_RESIZE_EDGES | BOTTOM_RESIZE_EDGES)
    vertical_only = edge in (TOP_RESIZE_EDGES | BOTTOM_RESIZE_EDGES) and edge not in (LEFT_RESIZE_EDGES | RIGHT_RESIZE_EDGES)
    if horizontal_only:
        target = ratio_size_from_width(client_width, base_height)
    elif vertical_only:
        target = ratio_size_from_height(client_height, base_height)
    elif client_width / max(1, client_height) >= aspect_ratio:
        target = ratio_size_from_width(client_width, base_height)
    else:
        target = ratio_size_from_height(client_height, base_height)

    width = target.width() + frame_extra_width
    height = target.height() + frame_extra_height

    if edge in LEFT_RESIZE_EDGES:
        rect.left = rect.right - width
    else:
        rect.right = rect.left + width

    if edge in TOP_RESIZE_EDGES:
        rect.top = rect.bottom - height
    else:
        rect.bottom = rect.top + height


class ProjectStore:
    def __init__(self, path: Path, archive_path: Path) -> None:
        self.path = path
        self.archive_path = archive_path

    def load(self) -> list[Project]:
        if not self.path.exists():
            projects = [Project("Default", 0)]
            self.save(projects)
            return projects

        projects: list[Project] = []
        seen: set[str] = set()
        delimiter = self._detect_delimiter(self.path)
        name_index = 0
        time_index = 1

        with self.path.open("r", encoding="utf-8", newline="") as file:
            for row in csv.reader(file, delimiter=delimiter):
                if not row:
                    continue

                normalized = [cell.strip().casefold() for cell in row]
                if self._is_header(normalized):
                    name_index = self._column_index(normalized, ("name", "project"), 0)
                    time_index = self._column_index(normalized, ("time", "elapsed"), 1)
                    continue

                name_cell = row[name_index] if name_index < len(row) else row[0]
                time_cell = row[time_index] if time_index < len(row) else "0"
                name = clean_project_name(name_cell)
                if not name:
                    continue

                try:
                    seconds = parse_time_value(time_cell)
                except ValueError:
                    seconds = 0

                unique_name = self._unique_name(name, seen)
                seen.add(unique_name.casefold())
                projects.append(Project(unique_name, seconds))

        if not projects:
            projects = [Project("Default", 0)]

        self.save(projects)
        return projects

    def save(self, projects: list[Project]) -> None:
        with self.path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, delimiter=CSV_DELIMITER)
            writer.writerow(CSV_HEADERS)
            for project in projects:
                writer.writerow([project.name, format_seconds(project.seconds)])

    def archive(self, project: Project) -> None:
        write_header = not self.archive_path.exists() or self.archive_path.stat().st_size == 0
        with self.archive_path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, delimiter=CSV_DELIMITER)
            if write_header:
                writer.writerow(CSV_HEADERS)
            writer.writerow([project.name, format_seconds(project.seconds)])

    @staticmethod
    def _detect_delimiter(path: Path) -> str:
        sample = path.read_text(encoding="utf-8").splitlines()
        first_line = next((line for line in sample if line.strip()), "")
        if first_line.count(";") >= first_line.count(","):
            return ";"
        return ","

    @staticmethod
    def _is_header(row: list[str]) -> bool:
        return any(cell in ("name", "project") for cell in row) and any(cell in ("time", "elapsed") for cell in row)

    @staticmethod
    def _column_index(row: list[str], candidates: tuple[str, ...], fallback: int) -> int:
        for candidate in candidates:
            if candidate in row:
                return row.index(candidate)
        return fallback

    @staticmethod
    def _unique_name(name: str, seen: set[str]) -> str:
        if name.casefold() not in seen:
            return name

        counter = 2
        while f"{name} ({counter})".casefold() in seen:
            counter += 1
        return f"{name} ({counter})"


class IconButton(QToolButton):
    def __init__(self, icon_name: str, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.icon_name = icon_name
        self.icon_color = "#a1a1aa"
        self.active_icon_color = "#151515"
        self.setObjectName("IconButton")
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setIconName(icon_name)
        self.setActive(False)

    def setIconName(self, icon_name: str) -> None:
        self.icon_name = icon_name
        self._refresh_icon()

    def setIconPalette(self, icon_color: str, active_icon_color: str) -> None:
        self.icon_color = normalize_hex(icon_color, self.icon_color) or self.icon_color
        self.active_icon_color = normalize_hex(active_icon_color, self.active_icon_color) or self.active_icon_color
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        path = icon_path(self.icon_name)
        if path:
            color = self.active_icon_color if self.property("active") else self.icon_color
            self.setIcon(tinted_icon(path, color, ICON_ROTATIONS.get(self.icon_name, 0)))
            self.setText("")
        else:
            fallback_text = {
                "chevron_left": "<",
                "chevron_right": ">",
                "time_style": "h",
                "plus": "+",
                "build": "B",
                "list": "L",
                "duplicate": "C",
                "move_up": "^",
                "move_down": "v",
            }.get(self.icon_name, "")
            self.setIcon(QIcon())
            self.setText(fallback_text)

    def setScaledSize(self, size: int, icon_ratio: float = 0.62) -> None:
        self.setFixedSize(QSize(size, size))
        icon_size = max(10, round(size * icon_ratio))
        self.setIconSize(QSize(icon_size, icon_size))

    def setActive(self, active: bool) -> None:
        if self.property("active") == active:
            return
        self.setProperty("active", active)
        self._refresh_icon()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


@dataclass
class ProjectListRowItem:
    row: QFrame
    edit_button: IconButton
    remove_button: IconButton
    up_button: IconButton
    down_button: IconButton
    timer_button: IconButton
    reset_button: IconButton


class ProjectListRowFrame(QFrame):
    def __init__(self, owner: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.owner = owner
        self.row_item: ProjectListRowItem | None = None
        self.project_name = ""
        self.time_text = "00:00:00"
        self.name_rect = QRectF()
        self.time_rect = QRectF()
        self.text_pixel_size = 10

    def setProjectName(self, name: str) -> None:
        if self.project_name == name:
            return
        self.project_name = name
        self.update()

    def setTimeText(self, text: str) -> None:
        if self.time_text == text:
            return
        self.time_text = text
        self.update()

    def setTextGeometry(self, name_rect: QRectF, time_rect: QRectF, text_pixel_size: int) -> None:
        if self.name_rect == name_rect and self.time_rect == time_rect and self.text_pixel_size == text_pixel_size:
            return
        self.name_rect = name_rect
        self.time_rect = time_rect
        self.text_pixel_size = text_pixel_size
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        theme = getattr(self.owner, "current_theme", DEFAULT_THEMES[0])
        name_font = QFont(resolved_theme_font_family(theme))
        name_font.setPixelSize(self.text_pixel_size)
        name_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(name_font)
        painter.setPen(QColor(theme["text"]))
        painter.drawText(self.name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.project_name)

        time_font = QFont(resolved_theme_font_family(theme))
        time_font.setPixelSize(self.text_pixel_size)
        time_font.setWeight(QFont.Weight.Bold)
        painter.setFont(time_font)
        painter.setPen(QColor(theme["muted"]))
        painter.drawText(self.time_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.time_text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.row_item is not None and hasattr(self.owner, "_layout_project_list_item"):
            self.owner._layout_project_list_item(self.row_item)


class SimpleColorPickerDialog(QDialog):
    def __init__(self, parent: QWidget, initial_color: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pick Color")
        self.setModal(True)
        self.selected_color = normalize_hex(initial_color) or "#000000"
        current = QColor(self.selected_color)
        self.selected_hue: int | None = self._nearest_hue(current.hslHue()) if current.hslSaturation() > 18 else None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedHeight(30)
        layout.addWidget(self.preview)

        hue_row = QHBoxLayout()
        hue_row.setSpacing(3)
        layout.addLayout(hue_row)

        for hue in PICKER_HUES:
            button = QPushButton()
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(17, 22))
            button.setToolTip("Color family")
            button.setStyleSheet(f"background: {QColor.fromHsl(hue, 210, 126).name()}; border: 0; border-radius: 3px;")
            button.clicked.connect(lambda _checked=False, value=hue: self._select_hue(value))
            hue_row.addWidget(button)

        neutral_button = QPushButton()
        neutral_button.setCursor(Qt.CursorShape.PointingHandCursor)
        neutral_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        neutral_button.setFixedSize(QSize(17, 22))
        neutral_button.setToolTip("Neutral")
        neutral_button.setStyleSheet("background: #888888; border: 0; border-radius: 3px;")
        neutral_button.clicked.connect(lambda _checked=False: self._select_hue(None))
        hue_row.addWidget(neutral_button)

        self.shade_row = QHBoxLayout()
        self.shade_row.setSpacing(4)
        layout.addLayout(self.shade_row)

        hex_row = QHBoxLayout()
        hex_row.setSpacing(6)
        layout.addLayout(hex_row)

        hex_label = QLabel("HEX")
        hex_label.setObjectName("FieldLabel")
        hex_row.addWidget(hex_label)

        self.hex_input = QLineEdit(self.selected_color)
        self.hex_input.setMaxLength(7)
        self.hex_input.editingFinished.connect(self._hex_edited)
        hex_row.addWidget(self.hex_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Use")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._rebuild_shades()
        self._refresh_preview()

    @staticmethod
    def _nearest_hue(hue: int) -> int:
        if hue < 0:
            return PICKER_HUES[0]
        return min(PICKER_HUES, key=lambda candidate: abs(candidate - hue))

    def _select_hue(self, hue: int | None) -> None:
        self.selected_hue = hue
        self._rebuild_shades()

    def _rebuild_shades(self) -> None:
        while self.shade_row.count():
            item = self.shade_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for lightness in PICKER_LIGHTNESS:
            saturation = 0 if self.selected_hue is None else 190
            hue = 0 if self.selected_hue is None else self.selected_hue
            color = QColor.fromHsl(hue, saturation, lightness).name()
            button = QPushButton()
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(29, 29))
            button.setToolTip(color)
            button.setStyleSheet(f"background: {color}; border: 0; border-radius: 4px;")
            button.clicked.connect(lambda _checked=False, value=color: self._set_color(value))
            self.shade_row.addWidget(button)

    def _set_color(self, value: str) -> None:
        color = normalize_hex(value)
        if color is None:
            return
        self.selected_color = color
        self._refresh_preview()

    def _hex_edited(self) -> None:
        color = normalize_hex(self.hex_input.text(), None)
        if color is None:
            self.hex_input.setText(self.selected_color)
            return
        self.selected_color = color
        qcolor = QColor(color)
        self.selected_hue = self._nearest_hue(qcolor.hslHue()) if qcolor.hslSaturation() > 18 else None
        self._rebuild_shades()
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        text_color = "#ffffff" if QColor(self.selected_color).lightness() < 128 else "#111111"
        self.preview.setText(self.selected_color.upper())
        self.preview.setStyleSheet(
            f"background: {self.selected_color}; color: {text_color}; border: 0; border-radius: 5px; font-weight: 700;"
        )
        if self.hex_input.text().lower() != self.selected_color:
            self.hex_input.setText(self.selected_color)


class ColorSwatchButton(QPushButton):
    def __init__(self, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(QSize(34, 22))
        self.setColor(color)

    def setColor(self, color: str) -> None:
        self.color = normalize_hex(color) or "#000000"
        text_color = "#ffffff" if QColor(self.color).lightness() < 128 else "#111111"
        self.setStyleSheet(
            f"background: {self.color}; color: {text_color}; border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 4px;"
        )


class ProjectComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.arrow_color = QColor("#a1a1aa")

    def setArrowColor(self, color: str) -> None:
        arrow_color = QColor(color)
        if arrow_color.isValid():
            self.arrow_color = arrow_color
            self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.arrow_color)

        size = max(4, round(self.height() * 0.16))
        center_x = self.width() - max(9, round(self.height() * 0.38))
        center_y = self.height() / 2 + max(0, round(self.height() * 0.03))
        arrow = QPainterPath()
        arrow.moveTo(center_x - size, center_y - size * 0.45)
        arrow.lineTo(center_x + size, center_y - size * 0.45)
        arrow.lineTo(center_x, center_y + size * 0.65)
        arrow.closeSubpath()
        painter.drawPath(arrow)


class ThemeNameLabel(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Scroll to switch theme")

    def wheelEvent(self, event) -> None:
        window = self.window()
        delta = event.angleDelta().y()
        if delta > 0 and hasattr(window, "previous_style"):
            window.previous_style()
            event.accept()
            return
        if delta < 0 and hasattr(window, "next_style"):
            window.next_style()
            event.accept()
            return
        super().wheelEvent(event)


class ThemePreviewFrame(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = copy_theme(DEFAULT_THEMES[0])
        self.setMinimumHeight(122)

    def setTheme(self, theme: dict[str, str]) -> None:
        self.theme = copy_theme(theme)
        self.update()

    def paintEvent(self, event) -> None:
        theme = self.theme
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(theme["bg"]))

        if theme_background_enabled(theme) or theme_animation_enabled(theme):
            paint_background_layers(painter, theme, self.size(), background_shape_profile(theme["name"]), alpha_scale=0.88)

            veil = QColor(theme["bg"])
            veil.setAlpha(70 if theme_glass_enabled(theme) else 30)
            painter.fillRect(self.rect(), veil)

        border = QColor(theme["border"])
        border.setAlpha(180)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 7, 7)


class ThemeBuilderDialog(QDialog):
    def __init__(self, parent: QWidget, themes: list[dict[str, str]], active_index: int) -> None:
        super().__init__(parent)
        self.setWindowTitle("Theme Builder")
        self.setModal(True)
        self.setFont(QFont(DEFAULT_FONT_FAMILY))
        self.themes = [copy_theme(theme) for theme in themes] or [copy_theme(DEFAULT_THEMES[0])]
        self.active_index = max(0, min(active_index, len(self.themes) - 1))
        self.theme = self.themes[self.active_index]
        self.loading_theme = False
        self.saved_changes = False
        self.original_parent_opacity = parent.windowOpacity()
        self.inputs: dict[str, QLineEdit] = {}
        self.swatches: dict[str, ColorSwatchButton] = {}
        self.background_images: list[str] = []
        self.font_families: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        selector_row = QHBoxLayout()
        selector_row.setSpacing(7)
        layout.addLayout(selector_row)

        selector_label = QLabel("Edit")
        selector_label.setObjectName("FieldLabel")
        selector_row.addWidget(selector_label)

        self.theme_menu = QComboBox()
        self.theme_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.theme_menu.currentIndexChanged.connect(self._theme_selected)
        selector_row.addWidget(self.theme_menu, 1)

        self.duplicate_theme_button = IconButton("duplicate", "Duplicate selected theme")
        self.duplicate_theme_button.setScaledSize(28)
        self.duplicate_theme_button.clicked.connect(self.duplicate_current_theme)
        selector_row.addWidget(self.duplicate_theme_button)

        self.add_theme_button = IconButton("plus", "Add theme")
        self.add_theme_button.setScaledSize(28)
        self.add_theme_button.clicked.connect(self.add_new_theme)
        selector_row.addWidget(self.add_theme_button)

        self.delete_theme_button = IconButton("trash", "Delete selected theme")
        self.delete_theme_button.setScaledSize(28)
        self.delete_theme_button.clicked.connect(self.delete_current_theme)
        selector_row.addWidget(self.delete_theme_button)

        name_row = QHBoxLayout()
        name_row.setSpacing(7)
        layout.addLayout(name_row)

        name_label = QLabel("Name")
        name_label.setObjectName("FieldLabel")
        name_row.addWidget(name_label)

        self.name_input = QLineEdit()
        name_row.addWidget(self.name_input, 1)

        background_row = QHBoxLayout()
        background_row.setSpacing(7)
        layout.addLayout(background_row)

        self.background_toggle = QPushButton("Background On")
        self.background_toggle.setCheckable(True)
        self.background_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.background_toggle.clicked.connect(self._background_toggled)
        background_row.addWidget(self.background_toggle)

        self.animation_toggle = QPushButton("Animation On")
        self.animation_toggle.setCheckable(True)
        self.animation_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.animation_toggle.clicked.connect(self._animation_toggled)
        background_row.addWidget(self.animation_toggle)

        self.glass_toggle = QPushButton("Glass On")
        self.glass_toggle.setCheckable(True)
        self.glass_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.glass_toggle.clicked.connect(self._glass_toggled)
        background_row.addWidget(self.glass_toggle)

        font_row = QHBoxLayout()
        font_row.setSpacing(7)
        layout.addLayout(font_row)

        font_label = QLabel("Font")
        font_label.setObjectName("FieldLabel")
        font_row.addWidget(font_label)

        self.font_menu = QComboBox()
        self.font_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.font_menu.currentIndexChanged.connect(self._font_selected)
        font_row.addWidget(self.font_menu, 1)

        self.font_size_down_button = IconButton("chevron_left", "Smaller theme font")
        self.font_size_down_button.setScaledSize(28)
        self.font_size_down_button.clicked.connect(lambda _checked=False: self._change_font_scale(-FONT_SCALE_STEP))
        font_row.addWidget(self.font_size_down_button)

        self.font_size_label = QLabel("100%")
        self.font_size_label.setObjectName("FieldLabel")
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.font_size_label.setFixedWidth(42)
        font_row.addWidget(self.font_size_label)

        self.font_size_up_button = IconButton("chevron_right", "Larger theme font")
        self.font_size_up_button.setScaledSize(28)
        self.font_size_up_button.clicked.connect(lambda _checked=False: self._change_font_scale(FONT_SCALE_STEP))
        font_row.addWidget(self.font_size_up_button)

        image_row = QHBoxLayout()
        image_row.setSpacing(7)
        layout.addLayout(image_row)

        image_label = QLabel("Image")
        image_label.setObjectName("FieldLabel")
        image_row.addWidget(image_label)

        self.background_image_menu = QComboBox()
        self.background_image_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.background_image_menu.currentIndexChanged.connect(self._background_image_selected)
        image_row.addWidget(self.background_image_menu, 1)

        blur_row = QHBoxLayout()
        blur_row.setSpacing(7)
        layout.addLayout(blur_row)

        blur_label = QLabel("Blur")
        blur_label.setObjectName("FieldLabel")
        blur_row.addWidget(blur_label)

        self.blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_slider.setRange(0, 100)
        self.blur_slider.valueChanged.connect(self._blur_changed)
        blur_row.addWidget(self.blur_slider, 1)

        self.blur_value_label = QLabel("0")
        self.blur_value_label.setObjectName("FieldLabel")
        self.blur_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.blur_value_label.setFixedWidth(32)
        blur_row.addWidget(self.blur_value_label)

        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(7)
        layout.addLayout(opacity_row)

        opacity_label = QLabel("Opacity")
        opacity_label.setObjectName("FieldLabel")
        opacity_row.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(MIN_WINDOW_OPACITY, MAX_WINDOW_OPACITY)
        self.opacity_slider.valueChanged.connect(self._opacity_changed)
        opacity_row.addWidget(self.opacity_slider, 1)

        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setObjectName("FieldLabel")
        self.opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.opacity_value_label.setFixedWidth(42)
        opacity_row.addWidget(self.opacity_value_label)

        blur_direction_row = QHBoxLayout()
        blur_direction_row.setSpacing(7)
        layout.addLayout(blur_direction_row)

        blur_direction_label = QLabel("Direction")
        blur_direction_label.setObjectName("FieldLabel")
        blur_direction_row.addWidget(blur_direction_label)

        self.blur_direction_menu = QComboBox()
        self.blur_direction_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for direction, label in BLUR_DIRECTION_LABELS.items():
            self.blur_direction_menu.addItem(label, direction)
        self.blur_direction_menu.currentIndexChanged.connect(self._blur_direction_changed)
        blur_direction_row.addWidget(self.blur_direction_menu, 1)

        color_grid = QGridLayout()
        color_grid.setHorizontalSpacing(8)
        color_grid.setVerticalSpacing(6)
        layout.addLayout(color_grid)

        for row, (field, label_text) in enumerate(THEME_COLOR_LABELS):
            label = QLabel(label_text)
            label.setObjectName("FieldLabel")
            color_grid.addWidget(label, row, 0)

            swatch = ColorSwatchButton("#000000")
            swatch.clicked.connect(lambda _checked=False, key=field: self._pick_color(key))
            color_grid.addWidget(swatch, row, 1)
            self.swatches[field] = swatch

            input_field = QLineEdit()
            input_field.setMaxLength(7)
            input_field.editingFinished.connect(lambda key=field: self._hex_edited(key))
            color_grid.addWidget(input_field, row, 2)
            self.inputs[field] = input_field

        self.preview_panel = ThemePreviewFrame()
        self.preview_panel.setObjectName("ThemePreview")
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(7)

        self.preview_name = QLabel(self.theme["name"])
        self.preview_name.setObjectName("PreviewName")
        self.preview_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_name)

        self.preview_timer = QLabel("00:00:00")
        self.preview_timer.setObjectName("PreviewTimer")
        self.preview_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_timer)

        preview_buttons = QHBoxLayout()
        preview_buttons.setSpacing(6)
        preview_layout.addLayout(preview_buttons)

        self.preview_button = QPushButton("Button")
        self.preview_button.setObjectName("PreviewButton")
        self.preview_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        preview_buttons.addWidget(self.preview_button)

        self.preview_active_button = QPushButton("Active")
        self.preview_active_button.setObjectName("PreviewActive")
        self.preview_active_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        preview_buttons.addWidget(self.preview_active_button)

        self.preview_plus_button = IconButton("plus", "")
        self.preview_plus_button.setToolTip("")
        self.preview_plus_button.setObjectName("PreviewIconButton")
        self.preview_plus_button.setScaledSize(30, 0.58)
        preview_buttons.addWidget(self.preview_plus_button)
        layout.addWidget(self.preview_panel)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_input.textChanged.connect(self._name_edited)
        self._apply_builder_ui_font()
        self._load_theme(self.active_index)

    def _apply_builder_ui_font(self) -> None:
        default_font = QFont(DEFAULT_FONT_FAMILY)
        self.setFont(default_font)
        for widget in self.findChildren(QWidget):
            if widget is self.preview_panel or self.preview_panel.isAncestorOf(widget):
                continue
            widget.setFont(default_font)

    def _load_theme(self, index: int) -> None:
        self.loading_theme = True
        self.active_index = max(0, min(index, len(self.themes) - 1))
        self.theme = self.themes[self.active_index]

        self.theme_menu.blockSignals(True)
        self.theme_menu.clear()
        self.theme_menu.addItems([theme["name"] for theme in self.themes])
        self.theme_menu.setCurrentIndex(self.active_index)
        self.theme_menu.blockSignals(False)

        self.name_input.blockSignals(True)
        self.name_input.setText(self.theme["name"])
        self.name_input.blockSignals(False)

        for field in THEME_COLOR_FIELDS:
            self.inputs[field].blockSignals(True)
            self.inputs[field].setText(self.theme[field])
            self.inputs[field].blockSignals(False)
            self.swatches[field].setColor(self.theme[field])

        self._sync_background_controls()
        self._sync_font_controls()
        self.delete_theme_button.setEnabled(len(self.themes) > 1)
        self.loading_theme = False
        self._refresh_preview()
        self._apply_live_window_opacity()

    def _theme_selected(self, index: int) -> None:
        if self.loading_theme or index < 0 or index == self.active_index:
            return
        self._load_theme(index)

    def _name_edited(self) -> None:
        if self.loading_theme:
            return

        self.theme["name"] = theme_name(self.name_input.text(), self.theme["name"])
        self._refresh_theme_menu()
        self._refresh_preview()

    def _refresh_theme_menu(self) -> None:
        self.theme_menu.blockSignals(True)
        for index, theme in enumerate(self.themes):
            self.theme_menu.setItemText(index, theme["name"])
        self.theme_menu.setCurrentIndex(self.active_index)
        self.theme_menu.blockSignals(False)

    def _sync_font_controls(self) -> None:
        self.font_families = list_theme_fonts()
        selected_font = resolved_theme_font_family(self.theme)
        self.theme["font_family"] = selected_font

        self.font_menu.blockSignals(True)
        self.font_menu.clear()
        for family in self.font_families:
            label = "Default" if family == DEFAULT_FONT_FAMILY else family
            self.font_menu.addItem(label, family)
        self.font_menu.setCurrentIndex(max(0, self.font_menu.findData(selected_font)))
        self.font_menu.blockSignals(False)

        font_scale = theme_font_scale(self.theme)
        self.font_size_label.setText(f"{font_scale}%")
        self.font_size_down_button.setEnabled(font_scale > MIN_FONT_SCALE)
        self.font_size_up_button.setEnabled(font_scale < MAX_FONT_SCALE)

    def _sync_background_controls(self) -> None:
        selected_image = str(self.theme.get("background_image", "")).strip()
        self.background_images = list_background_images()
        if selected_image and selected_image not in self.background_images:
            self.background_images.insert(0, selected_image)

        background_on = bool_from_theme(self.theme.get("background_enabled"), True)
        animation_on = bool_from_theme(self.theme.get("animation_enabled"), True)
        glass_on = bool_from_theme(self.theme.get("glass_enabled"), True)
        blur_value = theme_background_blur(self.theme)
        blur_direction = theme_background_blur_direction(self.theme)
        opacity_value = theme_window_opacity(self.theme)
        blur_controls_enabled = background_on or animation_on

        self.background_toggle.blockSignals(True)
        self.background_toggle.setChecked(background_on)
        self.background_toggle.setText("Background On" if background_on else "Background Off")
        self.background_toggle.blockSignals(False)

        self.animation_toggle.blockSignals(True)
        self.animation_toggle.setChecked(animation_on)
        self.animation_toggle.setText("Animation On" if animation_on else "Animation Off")
        self.animation_toggle.blockSignals(False)

        self.glass_toggle.blockSignals(True)
        self.glass_toggle.setChecked(glass_on)
        self.glass_toggle.setText("Glass On" if glass_on else "Glass Off")
        self.glass_toggle.blockSignals(False)

        self.background_image_menu.blockSignals(True)
        self.background_image_menu.clear()
        self.background_image_menu.addItem("No image", "")
        for image_name in self.background_images:
            self.background_image_menu.addItem(image_name, image_name)

        selected_index = 0
        for index in range(self.background_image_menu.count()):
            if self.background_image_menu.itemData(index) == selected_image:
                selected_index = index
                break
        self.background_image_menu.setCurrentIndex(selected_index)
        self.background_image_menu.setEnabled(background_on)
        self.background_image_menu.blockSignals(False)

        self.blur_slider.blockSignals(True)
        self.blur_slider.setValue(blur_value)
        self.blur_slider.setEnabled(blur_controls_enabled)
        self.blur_slider.blockSignals(False)
        self.blur_value_label.setText(str(blur_value))
        self.blur_value_label.setEnabled(blur_controls_enabled)

        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(opacity_value)
        self.opacity_slider.blockSignals(False)
        self.opacity_value_label.setText(f"{opacity_value}%")

        direction_index = max(0, self.blur_direction_menu.findData(blur_direction))
        self.blur_direction_menu.blockSignals(True)
        self.blur_direction_menu.setCurrentIndex(direction_index)
        self.blur_direction_menu.setEnabled(blur_controls_enabled)
        self.blur_direction_menu.blockSignals(False)
        self._style_background_toggles()

    def _style_background_toggles(self) -> None:
        self._style_toggle_button(self.background_toggle, self.background_toggle.isChecked())
        self._style_toggle_button(self.animation_toggle, self.animation_toggle.isChecked())
        self._style_toggle_button(self.glass_toggle, self.glass_toggle.isChecked())

    def _style_toggle_button(self, button: QPushButton, active: bool) -> None:
        theme = self.theme
        bg = theme["primary"] if active else qss_rgba(theme["surface"], 230)
        hover = theme["accent"] if active else qss_rgba(theme["surface_lift"], 240)
        text = theme["bg"] if active else theme["muted"]
        border = theme["accent"] if active else qss_rgba(theme["border"], 180)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 6px 9px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {hover};
                color: {theme["bg"] if active else theme["text"]};
            }}
            """
        )

    def _background_toggled(self, _checked: bool = False) -> None:
        if self.loading_theme:
            return

        self.theme["background_enabled"] = self.background_toggle.isChecked()
        self._sync_background_controls()
        self._refresh_preview()

    def _animation_toggled(self, _checked: bool = False) -> None:
        if self.loading_theme:
            return

        self.theme["animation_enabled"] = self.animation_toggle.isChecked()
        self._sync_background_controls()
        self._refresh_preview()

    def _glass_toggled(self, _checked: bool = False) -> None:
        if self.loading_theme:
            return

        self.theme["glass_enabled"] = self.glass_toggle.isChecked()
        self._sync_background_controls()
        self._refresh_preview()

    def _background_image_selected(self, _index: int = -1) -> None:
        if self.loading_theme:
            return

        image_name = self.background_image_menu.currentData()
        self.theme["background_image"] = str(image_name or "")
        self._refresh_preview()

    def _font_selected(self, _index: int = -1) -> None:
        if self.loading_theme:
            return

        self.theme["font_family"] = theme_font_family({"font_family": self.font_menu.currentData()})
        self._refresh_preview()

    def _change_font_scale(self, delta: int) -> None:
        if self.loading_theme:
            return

        current_scale = theme_font_scale(self.theme)
        self.theme["font_scale"] = max(MIN_FONT_SCALE, min(MAX_FONT_SCALE, current_scale + delta))
        self._sync_font_controls()
        self._refresh_preview()

    def _blur_changed(self, value: int) -> None:
        if self.loading_theme:
            return

        blur_value = clamp_int(value, 0, 100, 28)
        self.theme["background_blur"] = blur_value
        self.blur_value_label.setText(str(blur_value))
        self._refresh_preview()

    def _opacity_changed(self, value: int) -> None:
        if self.loading_theme:
            return

        opacity_value = clamp_int(value, MIN_WINDOW_OPACITY, MAX_WINDOW_OPACITY, DEFAULT_WINDOW_OPACITY)
        self.theme["window_opacity"] = opacity_value
        self.opacity_value_label.setText(f"{opacity_value}%")
        self._refresh_preview()
        self._apply_live_window_opacity()

    def _blur_direction_changed(self, _index: int = -1) -> None:
        if self.loading_theme:
            return

        self.theme["background_blur_direction"] = normalize_blur_direction(self.blur_direction_menu.currentData())
        self._refresh_preview()

    def delete_current_theme(self) -> None:
        if len(self.themes) <= 1:
            QMessageBox.warning(self, "Keep one theme", "At least one theme has to stay.")
            return

        name = self.theme["name"]
        answer = QMessageBox.question(
            self,
            "Delete theme",
            f"Delete the theme {name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        del self.themes[self.active_index]
        self._load_theme(min(self.active_index, len(self.themes) - 1))

    def duplicate_current_theme(self) -> None:
        if not self._sync_theme_from_inputs():
            return

        duplicate = copy_theme(self.theme)
        duplicate["name"] = self._copy_theme_name(self.theme["name"])
        insert_index = self.active_index + 1
        self.themes.insert(insert_index, duplicate)
        self._load_theme(insert_index)

    def add_new_theme(self) -> None:
        if not self._sync_theme_from_inputs():
            return

        obsidian = next((theme for theme in self.themes if theme["name"].casefold() == "obsidian"), DEFAULT_THEMES[0])
        new_theme = copy_theme(obsidian)
        new_theme["name"] = self._new_theme_name()
        insert_index = self.active_index + 1
        self.themes.insert(insert_index, new_theme)
        self._load_theme(insert_index)

    def _new_theme_name(self) -> str:
        base = "New Theme"
        existing = {theme["name"].casefold() for theme in self.themes}
        if base.casefold() not in existing:
            return base

        counter = 1
        while f"{base} {counter}".casefold() in existing:
            counter += 1
        return f"{base} {counter}"

    def _copy_theme_name(self, name: str) -> str:
        clean_name = theme_name(name)
        lowered_name = clean_name.casefold()
        copy_marker = " copy "
        copy_marker_index = lowered_name.rfind(copy_marker)

        if lowered_name.endswith(" copy"):
            base = clean_name
        elif copy_marker_index >= 0 and lowered_name[copy_marker_index + len(copy_marker) :].isdigit():
            base = f"{clean_name[:copy_marker_index]} Copy"
        else:
            base = f"{clean_name} Copy"

        existing = {theme["name"].casefold() for theme in self.themes}
        if base.casefold() not in existing:
            return base

        counter = 2
        while f"{base} {counter}".casefold() in existing:
            counter += 1
        return f"{base} {counter}"

    def _pick_color(self, field: str) -> None:
        dialog = SimpleColorPickerDialog(self, self.theme[field])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._set_theme_color(field, dialog.selected_color)

    def _hex_edited(self, field: str) -> None:
        color = normalize_hex(self.inputs[field].text(), None)
        if color is None:
            self.inputs[field].setText(self.theme[field])
            return
        self._set_theme_color(field, color)

    def _set_theme_color(self, field: str, color: str) -> None:
        normalized = normalize_hex(color, self.theme[field]) or self.theme[field]
        self.theme[field] = normalized
        self.inputs[field].setText(normalized)
        self.swatches[field].setColor(normalized)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        theme = self.theme
        for button in (self.duplicate_theme_button, self.add_theme_button, self.delete_theme_button):
            button.setIconPalette(theme.get("icon", theme["muted"]), theme["bg"])
        self.preview_panel.setTheme(theme)
        surface = qss_rgba(theme["surface"], 150) if theme_glass_enabled(theme) else theme["surface"]
        surface_lift = qss_rgba(theme["surface_lift"], 166) if theme_glass_enabled(theme) else theme["surface_lift"]
        active = qss_rgba(theme["primary"], 218) if theme_glass_enabled(theme) else theme["primary"]
        icon_color = theme.get("icon", theme["muted"])
        font_family = qss_font_family(resolved_theme_font_family(theme))
        preview_timer_size = scaled_font_size(22, theme)
        preview_label_size = scaled_font_size(9, theme)
        self.preview_plus_button.setIconPalette(icon_color, theme["bg"])
        self.preview_name.setText(theme["name"])
        self.preview_panel.setStyleSheet(
            f"""
            QWidget {{
                font-family: {font_family};
            }}
            QLabel#PreviewName {{
                background: {surface};
                color: {theme["muted"]};
                border: 0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: {preview_label_size}pt;
                font-weight: 700;
            }}
            QLabel#PreviewTimer {{
                background: transparent;
                color: {theme["text"]};
                font-size: {preview_timer_size}pt;
                font-weight: 800;
            }}
            QPushButton#PreviewButton {{
                background: {surface};
                color: {theme["muted"]};
                border: 0;
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton#PreviewActive {{
                background: {active};
                color: {theme["bg"]};
                border: 0;
                border-radius: 4px;
                padding: 6px;
            }}
            QToolButton#PreviewIconButton {{
                background: {surface};
                color: {icon_color};
                border: 0;
                border-radius: 4px;
                padding: 0;
                font-weight: 800;
            }}
            QToolButton#PreviewIconButton:hover {{
                background: {surface_lift};
            }}
            """
        )

    def _apply_live_window_opacity(self) -> None:
        parent = self.parent()
        if parent is None or not hasattr(parent, "style_index"):
            return
        if self.active_index != getattr(parent, "style_index"):
            return
        parent.setWindowOpacity(theme_window_opacity(self.theme) / 100.0)

    def _restore_parent_opacity(self) -> None:
        parent = self.parent()
        if parent is not None:
            parent.setWindowOpacity(self.original_parent_opacity)

    def _sync_theme_from_inputs(self) -> bool:
        self.theme["name"] = theme_name(self.name_input.text())
        for field in THEME_COLOR_FIELDS:
            color = normalize_hex(self.inputs[field].text(), None)
            if color is None:
                QMessageBox.warning(self, "Invalid color", f"Check {field}. Use #RRGGBB.")
                return False
            self.theme[field] = color
        self.theme["background_enabled"] = self.background_toggle.isChecked()
        self.theme["animation_enabled"] = self.animation_toggle.isChecked()
        self.theme["glass_enabled"] = self.glass_toggle.isChecked()
        self.theme["font_family"] = theme_font_family({"font_family": self.font_menu.currentData()})
        self.theme["font_scale"] = theme_font_scale(self.theme)
        self.theme["background_image"] = str(self.background_image_menu.currentData() or "")
        self.theme["background_blur"] = self.blur_slider.value()
        self.theme["background_blur_direction"] = normalize_blur_direction(self.blur_direction_menu.currentData())
        self.theme["window_opacity"] = self.opacity_slider.value()
        self._refresh_theme_menu()
        self._refresh_preview()
        return True

    def accept(self) -> None:
        if not self._sync_theme_from_inputs():
            return
        self.saved_changes = True
        self._refresh_theme_menu()
        super().accept()

    def reject(self) -> None:
        if not self.saved_changes:
            self._restore_parent_opacity()
        super().reject()


class ProjectDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, name: str = "", elapsed: str = "00:00:00", show_time: bool = True) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result_value: tuple[str, int] | None = None
        self.show_time = show_time

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        self.name_input = QLineEdit(name)
        self.name_input.setMaxLength(PROJECT_NAME_MAX_LENGTH)
        self.name_input.setPlaceholderText(f"Project, max {PROJECT_NAME_MAX_LENGTH} chars")
        layout.addWidget(self.name_input)

        self.time_input = QLineEdit(elapsed)
        self.time_input.setPlaceholderText("HH:MM:SS")
        if show_time:
            layout.addWidget(self.time_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_input.selectAll()
        self.name_input.setFocus()

    def _save(self) -> None:
        name = clean_project_name(self.name_input.text())
        if not name:
            QMessageBox.warning(self, "Missing project", "Add a project name.")
            return

        try:
            seconds = parse_time_value(self.time_input.text()) if self.show_time else 0
        except ValueError as error:
            QMessageBox.warning(self, "Invalid time", str(error))
            return

        self.result_value = (name, seconds)
        self.accept()


class ProjectTimerWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        ensure_app_files()
        register_theme_fonts()
        self.store = ProjectStore(DATA_FILE, ARCHIVE_FILE)
        self.projects = self.store.load()
        self.settings = load_settings()

        self.active_index = self._saved_project_index()
        self.running = False
        self.started_at: float | None = None
        self.always_on_top = self._saved_bool_setting("always_on_top", False)
        self.last_autosave = time.monotonic()
        self.time_style = self._saved_time_style()
        self.list_mode = self._saved_bool_setting("list_mode", False)
        self.saved_window_width = self._saved_window_width()
        self.window_scale = DEFAULT_SCALE
        self.enforcing_aspect_resize = False
        self.enforced_resize_scale: float | None = None
        self.scaled_theme_radius: int | None = None
        self.project_list_rows: list[QFrame] = []
        self.project_list_row_items: list[ProjectListRowItem] = []
        self.project_list_buttons: list[IconButton] = []
        self.project_list_last_metrics: tuple[int, int, int, int, int, int, int, int, int, str] | None = None
        self.resize_quiet_until = 0.0
        self.ignore_project_file_changes_until = 0.0
        self.pending_project_file_reload = False
        self.themes = load_themes()
        self.style_index = self._saved_style_index()
        self.current_theme = self.themes[self.style_index]
        self.background_pixmap_name = ""
        self.background_pixmap = QPixmap()
        self.background_shapes = self._make_background_shapes()
        self.background_last_tick = time.monotonic()

        self.setWindowTitle(" ")
        self.setObjectName("ProjectTimerWindow")
        self.setMinimumSize(QSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT))
        self.setMaximumSize(QSize(MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT))
        empty_icon = icon_path("empty")
        self.setWindowIcon(QIcon(empty_icon) if empty_icon else QIcon())
        if self.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self._build_ui()
        self.timer_view.setVisible(not self.list_mode)
        self.list_view.setVisible(self.list_mode)
        if self.list_mode:
            self._rebuild_project_list()
        self._sync_project_menu()
        self._refresh_ui()
        self._set_window_scale(self._scale_from_width(self.saved_window_width), resize=True)
        self._restore_saved_window_position()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(250)

        self.background_timer = QTimer(self)
        self.background_timer.timeout.connect(self._animate_background)
        self.background_timer.start(50)

        self.project_file_watcher = QFileSystemWatcher(self)
        self.project_file_watcher.fileChanged.connect(self._project_file_changed)
        self._watch_project_file()

        QTimer.singleShot(50, self.change_title_bar_color)

    def _saved_style_index(self) -> int:
        saved_name = str(self.settings.get("theme_name", "")).casefold()
        if saved_name:
            for index, theme in enumerate(self.themes):
                if theme["name"].casefold() == saved_name:
                    return index

        saved_index = self.settings.get("theme_index")
        if isinstance(saved_index, int) and 0 <= saved_index < len(self.themes):
            return saved_index
        return 0

    def _saved_project_index(self) -> int:
        saved_name = str(
            self.settings.get("last_project_name", self.settings.get("project_name", ""))
        ).casefold()
        if saved_name:
            for index, project in enumerate(self.projects):
                if project.name.casefold() == saved_name:
                    return index

        saved_index = self.settings.get("last_project_index", self.settings.get("project_index"))
        if isinstance(saved_index, int) and 0 <= saved_index < len(self.projects):
            return saved_index
        return 0

    def _saved_bool_setting(self, key: str, default: bool) -> bool:
        return bool_from_theme(self.settings.get(key), default)

    def _saved_time_style(self) -> str:
        return "units" if str(self.settings.get("time_style", "")).casefold() == "units" else "clean"

    def _saved_window_width(self) -> int:
        if "window_width" in self.settings:
            return clamp_int(self.settings.get("window_width"), MIN_WINDOW_WIDTH, MAX_WINDOW_WIDTH, DEFAULT_WIDTH)

        try:
            scale = float(str(self.settings.get("window_scale", DEFAULT_SCALE)))
        except (TypeError, ValueError):
            scale = DEFAULT_SCALE
        return clamp_window_width(round(BASE_WIDTH * scale))

    def _saved_window_position(self) -> tuple[int, int] | None:
        x_value = self.settings.get("window_x")
        y_value = self.settings.get("window_y")
        if x_value is None or y_value is None:
            return None

        try:
            return int(x_value), int(y_value)
        except (TypeError, ValueError):
            return None

    def _restore_saved_window_position(self) -> None:
        saved_position = self._saved_window_position()
        if saved_position is None:
            return

        x, y = saved_position
        screen = QApplication.screenAt(QPoint(x, y)) or QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            max_x = max(available.left(), available.left() + available.width() - self.width())
            max_y = max(available.top(), available.top() + available.height() - self.height())
            x = clamp_int(x, available.left(), max_x, available.left())
            y = clamp_int(y, available.top(), max_y, available.top())

        self.move(x, y)

    def _save_app_settings(self) -> None:
        self.settings["theme_name"] = self.current_theme["name"]
        self.settings["theme_index"] = self.style_index
        if self.projects:
            self.settings["last_project_name"] = self.projects[self.active_index].name
            self.settings["last_project_index"] = self.active_index
        else:
            self.settings["last_project_name"] = ""
            self.settings["last_project_index"] = 0
        self.settings["window_width"] = clamp_window_width(self.width() or round(BASE_WIDTH * self.window_scale))
        self.settings["window_scale"] = round(self.window_scale, 4)
        self.settings["window_x"] = int(self.x())
        self.settings["window_y"] = int(self.y())
        self.settings["always_on_top"] = self.always_on_top
        self.settings["list_mode"] = self.list_mode
        self.settings["time_style"] = self.time_style
        save_settings(self.settings)

    def _save_theme_settings(self) -> None:
        self._save_app_settings()

    def _has_frosted_background(self) -> bool:
        return theme_background_enabled(self.current_theme) or self._has_background_animation()

    def _has_background_animation(self) -> bool:
        return theme_animation_enabled(self.current_theme)

    def _has_glass_layer(self) -> bool:
        return theme_glass_enabled(self.current_theme)

    def _is_resize_quiet_period(self) -> bool:
        return time.monotonic() < self.resize_quiet_until

    def _selected_background_image(self) -> QPixmap:
        path = background_image_path(self.current_theme.get("background_image", ""))
        image_name = path.name if path is not None else ""
        if image_name != self.background_pixmap_name:
            self.background_pixmap_name = image_name
            self.background_pixmap = QPixmap(str(path)) if path is not None else QPixmap()
        return self.background_pixmap

    def _make_background_shapes(self) -> list[dict[str, float | str]]:
        return [dict(shape) for shape in background_shape_profile(self.current_theme["name"])]

    def _animate_background(self) -> None:
        now = time.monotonic()
        delta = min(0.2, now - self.background_last_tick)
        self.background_last_tick = now

        if now < self.resize_quiet_until:
            return

        if not self._has_background_animation():
            return

        for shape in self.background_shapes:
            dx = float(shape["target_x"]) - float(shape["x"])
            dy = float(shape["target_y"]) - float(shape["y"])
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 0.035:
                shape["target_x"] = random.uniform(-0.24, 1.24)
                shape["target_y"] = random.uniform(-0.18, 1.18)
                continue

            step = min(float(shape["speed"]) * delta, distance)
            shape["x"] = float(shape["x"]) + dx / distance * step
            shape["y"] = float(shape["y"]) + dy / distance * step

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(self.current_theme["bg"]))

        if self._has_frosted_background():
            self._paint_frosted_background(painter)

    def _paint_frosted_background(self, painter: QPainter) -> None:
        paint_background_layers(
            painter,
            self.current_theme,
            self.size(),
            self.background_shapes,
            self._selected_background_image(),
        )

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        veil = QColor(self.current_theme["bg"])
        veil.setAlpha(66 if self._has_glass_layer() else 26)
        painter.fillRect(self.rect(), veil)

    def nativeEvent(self, event_type, message):
        if sys.platform != "win32":
            return super().nativeEvent(event_type, message)

        try:
            msg = wintypes.MSG.from_address(int(message))
        except Exception:
            return super().nativeEvent(event_type, message)

        if msg.message != WM_SIZING:
            return super().nativeEvent(event_type, message)

        try:
            rect = cast(c_void_p(msg.lParam), POINTER(wintypes.RECT)).contents
            frame_geometry = self.frameGeometry()
            client_geometry = self.geometry()
            frame_extra_width = max(0, frame_geometry.width() - client_geometry.width())
            frame_extra_height = max(0, frame_geometry.height() - client_geometry.height())
            enforce_windows_resize_rect(
                rect,
                int(msg.wParam),
                frame_extra_width,
                frame_extra_height,
                self._mode_base_height(),
            )
        except Exception:
            return super().nativeEvent(event_type, message)

        return True, 0

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not hasattr(self, "root_layout"):
            return
        self.resize_quiet_until = time.monotonic() + 0.12

        if self.enforcing_aspect_resize:
            scale = self.enforced_resize_scale if self.enforced_resize_scale is not None else self.width() / BASE_WIDTH
            self._set_window_scale(scale, resize=False, apply_constraints=False)
            return

        if sys.platform == "win32":
            # WM_SIZING owns live drag geometry on Windows; calling resize() here fights it.
            self._set_window_scale(self.width() / BASE_WIDTH, resize=False, apply_constraints=False)
            return

        target_size = ratio_size_for_resize(event.size(), event.oldSize(), self._mode_base_height())
        if target_size != event.size():
            self.enforcing_aspect_resize = True
            self.enforced_resize_scale = target_size.width() / BASE_WIDTH
            self.resize(target_size)
            self.enforced_resize_scale = None
            self.enforcing_aspect_resize = False
            return

        self._set_window_scale(self.width() / BASE_WIDTH, resize=False, apply_constraints=False)

    def _build_ui(self) -> None:
        self.root_layout = QVBoxLayout(self)

        self.top_row = QHBoxLayout()
        self.root_layout.addLayout(self.top_row)

        self.previous_style_button = IconButton("chevron_left", "Previous style")
        self.previous_style_button.clicked.connect(self.previous_style)
        self.top_row.addWidget(self.previous_style_button)

        self.style_name_label = ThemeNameLabel()
        self.style_name_label.setText(self.themes[self.style_index]["name"])
        self.style_name_label.setObjectName("StyleName")
        self.style_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_row.addWidget(self.style_name_label)

        self.next_style_button = IconButton("chevron_right", "Next style")
        self.next_style_button.clicked.connect(self.next_style)
        self.top_row.addWidget(self.next_style_button)

        self.build_button = IconButton("build", "Build current theme")
        self.build_button.clicked.connect(self.open_theme_builder)
        self.top_row.addWidget(self.build_button)

        self.list_button = IconButton("list", "Project list view")
        self.list_button.clicked.connect(self.toggle_list_view)
        self.top_row.addWidget(self.list_button)

        self.add_button = IconButton("plus", "Add project")
        self.add_button.clicked.connect(self.add_project)
        self.top_row.addWidget(self.add_button)

        self.top_button = IconButton("unlock", "Always on top")
        self.top_button.clicked.connect(self.toggle_always_on_top)
        self.top_row.addWidget(self.top_button)

        self.top_row.addStretch(1)

        self.timer_view = QWidget()
        self.timer_view_layout = QVBoxLayout(self.timer_view)
        self.timer_view_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.addWidget(self.timer_view)

        self.project_row = QHBoxLayout()
        self.timer_view_layout.addLayout(self.project_row)

        self.project_menu = ProjectComboBox()
        self.project_menu.setObjectName("ProjectMenu")
        self.project_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.project_menu.currentIndexChanged.connect(self._project_selected)
        self.project_row.addWidget(self.project_menu, 1)

        self.edit_button = IconButton("edit", "Edit project")
        self.edit_button.clicked.connect(self.edit_project)
        self.project_row.addWidget(self.edit_button)

        self.remove_button = IconButton("trash", "Remove project")
        self.remove_button.clicked.connect(self.remove_project)
        self.project_row.addWidget(self.remove_button)

        self.timer_row = QGridLayout()
        self.timer_view_layout.addLayout(self.timer_row)

        self.timer_left_spacer = QFrame()
        self.timer_row.addWidget(self.timer_left_spacer, 0, 0)

        self.time_label = QLabel("00:00:00")
        self.time_label.setObjectName("TimerText")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_row.addWidget(self.time_label, 0, 1)

        self.time_style_button = IconButton("time_style", "Switch time format")
        self.time_style_button.clicked.connect(self.toggle_time_style)
        self.timer_row.addWidget(self.time_style_button, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)
        self.timer_row.setColumnStretch(0, 0)
        self.timer_row.setColumnStretch(1, 1)
        self.timer_row.setColumnStretch(2, 0)

        self.controls_row = QHBoxLayout()
        self.timer_view_layout.addLayout(self.controls_row)

        self.toggle_button = IconButton("play", "Start or stop timer")
        self.toggle_button.clicked.connect(self.toggle_timer)
        self.controls_row.addWidget(self.toggle_button)

        self.restart_button = IconButton("reset", "Restart current project timer")
        self.restart_button.clicked.connect(self.restart_timer)
        self.controls_row.addWidget(self.restart_button)

        self.list_view = QWidget()
        self.list_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list_view_layout = QVBoxLayout(self.list_view)
        self.list_view_layout.setContentsMargins(0, 0, 0, 0)
        self.list_view_layout.setSpacing(0)

        self.project_scroll = QScrollArea()
        self.project_scroll.setObjectName("ProjectListScroll")
        self.project_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.project_scroll.setWidgetResizable(True)
        self.project_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.project_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.project_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.project_list_content = QWidget()
        self.project_list_content.setObjectName("ProjectListContent")
        self.project_list_layout = QVBoxLayout(self.project_list_content)
        self.project_list_layout.setContentsMargins(0, 0, 0, 0)
        self.project_list_layout.setSpacing(3)
        self.project_scroll.setWidget(self.project_list_content)
        self.list_view_layout.addWidget(self.project_scroll)

        self.root_layout.addWidget(self.list_view)
        self.list_view.hide()

    def _apply_theme(self) -> None:
        theme = self.current_theme
        self.setWindowOpacity(theme_window_opacity(theme) / 100.0)
        self._apply_main_window_font()
        frosted = self._has_glass_layer()
        radius = max(3, round(4 * self.window_scale))
        self.scaled_theme_radius = radius
        root_background = "transparent" if frosted else theme["bg"]
        surface = qss_rgba(theme["surface"], 128) if frosted else theme["surface"]
        surface_lift = qss_rgba(theme["surface_lift"], 166) if frosted else theme["surface_lift"]
        surface_press = qss_rgba(theme["surface_press"], 146) if frosted else theme["surface_press"]
        border = qss_rgba(theme["border"], 112) if frosted else theme["border"]
        primary = qss_rgba(theme["primary"], 218) if frosted else theme["primary"]
        accent = qss_rgba(theme["accent"], 224) if frosted else theme["accent"]
        input_surface = qss_rgba(theme["surface"], 158) if frosted else theme["surface"]
        self.project_menu.setArrowColor(theme["muted"])
        self.setStyleSheet(
            f"""
            QWidget {{
                color: {theme["text"]};
            }}
            QWidget#ProjectTimerWindow {{
                background: {root_background};
            }}
            QDialog {{
                background: {theme["bg"]};
            }}
            QLabel#TimerText {{
                color: {theme["text"]};
                font-weight: 800;
                background: transparent;
            }}
            QLabel#StyleName {{
                background: {surface};
                color: {theme["muted"]};
                border: 1px solid {border};
                border-radius: {radius}px;
                font-weight: 700;
            }}
            QScrollArea#ProjectListScroll,
            QWidget#ProjectListContent {{
                background: transparent;
                border: 0;
            }}
            QFrame#ProjectListRow {{
                background: {surface};
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
            QFrame#ProjectListRow[active="true"] {{
                background: {surface_lift};
                border: 1px solid {primary};
            }}
            QToolButton#IconButton {{
                background: {surface};
                border: 1px solid {border};
                border-radius: {radius}px;
                color: {theme["muted"]};
                font-weight: 800;
            }}
            QToolButton#IconButton:hover {{
                background: {surface_lift};
            }}
            QToolButton#IconButton:pressed {{
                background: {surface_press};
            }}
            QToolButton#IconButton[active="true"] {{
                background: {primary};
                color: {theme["bg"]};
            }}
            QToolButton#IconButton[active="true"]:hover {{
                background: {accent};
                color: {theme["bg"]};
            }}
            QToolButton#IconButton[active="true"]:pressed {{
                background: {primary};
                color: {theme["bg"]};
            }}
            QToolButton#IconButton:disabled {{
                color: {border};
                background: {surface_press};
            }}
            QComboBox#ProjectMenu {{
                background: {surface};
                color: {theme["text"]};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding-left: {max(5, round(5 * self.window_scale))}px;
                padding-right: {max(18, round(18 * self.window_scale))}px;
                selection-background-color: transparent;
                selection-color: {theme["text"]};
            }}
            QComboBox#ProjectMenu::drop-down {{
                border: 0;
                width: {max(18, round(18 * self.window_scale))}px;
            }}
            QComboBox#ProjectMenu::down-arrow {{
                image: none;
                width: 0;
                height: 0;
            }}
            QComboBox#ProjectMenu QAbstractItemView {{
                background: {input_surface};
                color: {theme["text"]};
                selection-background-color: {surface_lift};
                selection-color: {theme["text"]};
                outline: 0;
                border: 1px solid {border};
            }}
            QLineEdit {{
                background: {input_surface};
                color: {theme["text"]};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding: 8px;
            }}
            QPushButton {{
                background: {input_surface};
                color: {theme["text"]};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background: {surface_lift};
            }}
            """
        )
        self._apply_icon_palette()
        self.change_title_bar_color()

    def _apply_main_window_font(self) -> None:
        theme_font = QFont(resolved_theme_font_family(self.current_theme))
        self.setFont(theme_font)
        for widget in self.findChildren(QWidget):
            if widget.window() is self:
                widget.setFont(theme_font)

    def _apply_icon_palette(self) -> None:
        icon_color = self.current_theme.get("icon", self.current_theme["muted"])
        active_icon_color = self.current_theme["bg"]
        for button in (
            self.previous_style_button,
            self.next_style_button,
            self.build_button,
            self.list_button,
            self.add_button,
            self.edit_button,
            self.remove_button,
            self.top_button,
            self.time_style_button,
            self.toggle_button,
            self.restart_button,
            *self.project_list_buttons,
        ):
            button.setIconPalette(icon_color, active_icon_color)

    def _list_visible_count(self) -> int:
        return max(1, min(LIST_MAX_VISIBLE_PROJECTS, len(self.projects)))

    def _list_arrow_button_size(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        return max(9, round(LIST_ARROW_BASE_SIZE * scale))

    def _list_arrow_gap(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        return max(1, round(LIST_ARROW_GAP_BASE * scale))

    def _list_arrow_vertical_padding(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        return max(1, round(LIST_ARROW_VERTICAL_PADDING_BASE * scale))

    def _list_min_row_height(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        arrow_stack_height = self._list_arrow_button_size(scale) * 2 + self._list_arrow_gap(scale)
        arrow_height = arrow_stack_height + self._list_arrow_vertical_padding(scale) * 2
        return max(LIST_ROW_BASE_HEIGHT, round(LIST_ROW_BASE_HEIGHT * scale), arrow_height)

    def _list_row_height(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        return self._list_min_row_height(scale)

    def _list_scroll_height(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        row_height = self._list_row_height(scale)
        gap = max(2, round(3 * scale))
        visible_rows = self._list_visible_count()
        return visible_rows * row_height + max(0, visible_rows - 1) * gap

    def _list_available_scroll_height(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        fallback_height = self._list_scroll_height(scale)
        if not getattr(self, "list_mode", False) or self.height() <= 0:
            return fallback_height

        top_margin = round(3 * scale)
        bottom_margin = max(1, round(1 * scale))
        gap = max(2, round(3 * scale))
        top_button = round(18 * scale)
        return max(1, self.height() - top_margin - top_button - gap - bottom_margin)

    def _list_row_metrics(self, scale: float | None = None) -> tuple[int, int, int]:
        scale = self.window_scale if scale is None else scale
        visible_rows = self._list_visible_count()
        row_gap = 0
        scroll_height = self._list_available_scroll_height(scale)

        row_height = self._list_row_height(scale)
        content_height = visible_rows * row_height + max(0, visible_rows - 1) * row_gap
        if not (getattr(self, "list_mode", False) and self.height() > 0):
            scroll_height = content_height

        return row_height, row_gap, scroll_height

    def _list_base_height(self) -> int:
        base_top_margin = 3
        base_bottom_margin = 1
        base_gap = 3
        base_top_button = 18
        base_scroll_height = self._list_visible_count() * self._list_min_row_height(MIN_WINDOW_SCALE)
        return max(
            BASE_HEIGHT,
            base_top_margin + base_top_button + base_gap + base_scroll_height + base_bottom_margin,
        )

    def _list_window_height(self, scale: float | None = None) -> int:
        scale = self.window_scale if scale is None else scale
        return round(self._list_base_height() * scale)

    def _scale_from_width(self, width: int) -> float:
        return max(MIN_WINDOW_SCALE, min(MAX_WINDOW_SCALE, width / BASE_WIDTH))

    def _mode_base_height(self) -> int:
        return self._list_base_height() if getattr(self, "list_mode", False) else BASE_HEIGHT

    def _resize_current_mode_to_width(self, width: int | None = None) -> None:
        target_width_source = self.width() if width is None else width
        scale = self._scale_from_width(target_width_source)
        scale = round(BASE_WIDTH * scale) / BASE_WIDTH
        target_size = ratio_size_from_width(round(BASE_WIDTH * scale), self._mode_base_height())

        self.setMinimumSize(QSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT))
        self.setMaximumSize(QSize(MAX_WINDOW_WIDTH, self._list_window_height(MAX_WINDOW_SCALE)))
        self._set_window_scale(scale, resize=False, apply_constraints=False)
        if self.size() == target_size:
            self._apply_window_constraints()
            return

        self.enforcing_aspect_resize = True
        self.enforced_resize_scale = scale
        self.resize(target_size)
        self.enforced_resize_scale = None
        self.enforcing_aspect_resize = False
        self._apply_window_constraints()

    def _apply_window_constraints(self) -> None:
        if not hasattr(self, "list_view"):
            return

        base_height = self._mode_base_height()
        self.setMinimumSize(QSize(MIN_WINDOW_WIDTH, clamp_window_height(0, base_height)))
        self.setMaximumSize(QSize(MAX_WINDOW_WIDTH, clamp_window_height(10_000, base_height)))

    def _rescale_project_list_rows(self) -> None:
        if not hasattr(self, "project_scroll"):
            return

        scale = self.window_scale
        row_height, row_gap, _scroll_height = self._list_row_metrics(scale)
        button_size, control_gap, row_margin, arrow_button_size, arrow_gap, arrow_padding, time_width, row_font_size, arrow_ratio = self._project_list_geometry_values(row_height, scale)
        metrics = (row_height, row_gap, button_size, control_gap, row_margin, arrow_button_size, arrow_gap, arrow_padding, row_font_size, self.time_style)
        style_changed = self.project_list_last_metrics != metrics
        self.project_list_last_metrics = metrics

        self.project_scroll.setMinimumHeight(0)
        self.project_scroll.setMaximumHeight(QT_MAX_WIDGET_SIZE)
        self.project_list_layout.setSpacing(row_gap)
        self.project_list_content.setMinimumHeight(
            len(self.projects) * row_height + max(0, len(self.projects) - 1) * row_gap
        )
        for item in self.project_list_row_items:
            item.row.setFixedHeight(row_height)
            if style_changed:
                for button in (
                    item.edit_button,
                    item.remove_button,
                    item.timer_button,
                    item.reset_button,
                ):
                    button.setScaledSize(button_size, arrow_ratio)
                item.up_button.setScaledSize(arrow_button_size, 0.54)
                item.down_button.setScaledSize(arrow_button_size, 0.54)
            self._layout_project_list_item(item, row_height, button_size, control_gap, row_margin, arrow_button_size, arrow_gap, arrow_padding, time_width)

    def _project_list_geometry_values(self, row_height: int, scale: float | None = None) -> tuple[int, int, int, int, int, int, int, int, float]:
        scale = self.window_scale if scale is None else scale
        button_size = max(14, min(row_height - 4, round(row_height * 0.64)))
        control_gap = max(2, min(6, round(2 * scale)))
        row_margin = max(3, min(7, round(3 * scale)))
        arrow_gap = self._list_arrow_gap(scale)
        arrow_padding = self._list_arrow_vertical_padding(scale)
        arrow_button_size = self._list_arrow_button_size(scale)
        if arrow_button_size * 2 + arrow_gap + arrow_padding * 2 > row_height:
            arrow_button_size = max(7, (row_height - arrow_gap - arrow_padding * 2) // 2)
        time_width = max(58, round((82 if self.time_style == "units" else 58) * scale))
        row_font_size = scaled_font_size(max(10, round(row_height * 0.38)), self.current_theme)
        return button_size, control_gap, row_margin, arrow_button_size, arrow_gap, arrow_padding, time_width, row_font_size, 0.54

    def _layout_project_list_item(
        self,
        item: ProjectListRowItem,
        row_height: int | None = None,
        button_size: int | None = None,
        control_gap: int | None = None,
        row_margin: int | None = None,
        arrow_button_size: int | None = None,
        arrow_gap: int | None = None,
        arrow_padding: int | None = None,
        time_width: int | None = None,
    ) -> None:
        if (
            row_height is None
            or button_size is None
            or control_gap is None
            or row_margin is None
            or arrow_button_size is None
            or arrow_gap is None
            or arrow_padding is None
            or time_width is None
        ):
            scale = self.window_scale
            row_height, _row_gap, _scroll_height = self._list_row_metrics(scale)
            button_size, control_gap, row_margin, arrow_button_size, arrow_gap, arrow_padding, time_width, row_font_size, _arrow_ratio = self._project_list_geometry_values(row_height, scale)
        else:
            _button_size, _control_gap, _row_margin, _arrow_button_size, _arrow_gap, _arrow_padding, _time_width, row_font_size, _arrow_ratio = self._project_list_geometry_values(row_height)

        row_width = item.row.width()
        if row_width <= 0:
            return

        y = max(0, (row_height - button_size) // 2)
        x = row_margin
        for button in (item.edit_button, item.remove_button):
            button.setGeometry(x, y, button_size, button_size)
            x += button_size + control_gap

        arrow_stack_height = arrow_button_size * 2 + arrow_gap
        arrow_y = max(arrow_padding, (row_height - arrow_stack_height) // 2)
        item.up_button.setGeometry(x, arrow_y, arrow_button_size, arrow_button_size)
        item.down_button.setGeometry(x, arrow_y + arrow_button_size + arrow_gap, arrow_button_size, arrow_button_size)
        x += arrow_button_size + control_gap

        right_width = button_size * 2 + control_gap
        right_x = max(x, row_width - row_margin - right_width)
        item.timer_button.setGeometry(right_x, y, button_size, button_size)
        item.reset_button.setGeometry(right_x + button_size + control_gap, y, button_size, button_size)

        name_x = x
        time_x = max(name_x, right_x - control_gap - time_width)
        name_rect = QRectF(name_x, 0, max(1, time_x - control_gap - name_x), row_height)
        time_rect = QRectF(time_x, 0, max(1, right_x - control_gap - time_x), row_height)
        item.row.setTextGeometry(name_rect, time_rect, row_font_size)

    def _set_window_scale(self, scale: float, resize: bool = True, apply_constraints: bool = True) -> None:
        scale = max(MIN_WINDOW_SCALE, min(MAX_WINDOW_SCALE, scale))
        self.window_scale = scale

        margin = round(3 * scale)
        gap = max(2, round(3 * scale))
        top_button = round(18 * scale)
        style_width = round(72 * scale)
        project_height = round(23 * scale)
        timer_button = round(22 * scale)
        control_height = round(28 * scale)
        timer_font_size = scaled_font_size(max(24, round(24 * scale)), self.current_theme)
        combo_font_size = scaled_font_size(max(9, round(9 * scale)), self.current_theme)
        theme_font_size = scaled_font_size(max(8, round(8 * scale)), self.current_theme)

        self.root_layout.setContentsMargins(margin, margin, margin, max(1, round(1 * scale)))
        self.root_layout.setSpacing(gap)
        for layout in (self.top_row, self.project_row, self.controls_row):
            layout.setSpacing(gap)
        self.timer_row.setHorizontalSpacing(gap)
        self.timer_row.setVerticalSpacing(0)

        for button in (
            self.previous_style_button,
            self.next_style_button,
            self.build_button,
            self.list_button,
            self.add_button,
            self.top_button,
        ):
            button.setScaledSize(top_button)

        self.style_name_label.setFixedSize(QSize(style_width, top_button))
        self.style_name_label.setStyleSheet(f"font-size: {theme_font_size}pt;")

        self.project_menu.setFixedHeight(project_height)
        self.project_menu.setStyleSheet(f"font-size: {combo_font_size}pt;")
        for button in (self.edit_button, self.remove_button):
            button.setScaledSize(project_height)

        self.time_label.setStyleSheet(f"font-size: {timer_font_size}pt;")
        self.time_style_button.setScaledSize(timer_button)
        self.timer_left_spacer.setFixedSize(QSize(timer_button, timer_button))

        width = round(BASE_WIDTH * scale)
        control_width = (width - 2 * margin - gap) // 2
        for button in (self.toggle_button, self.restart_button):
            button.setFixedSize(QSize(control_width, control_height))
            button.setIconSize(QSize(max(12, round(control_height * 0.58)), max(12, round(control_height * 0.58))))

        self._rescale_project_list_rows()
        if self.scaled_theme_radius != max(3, round(4 * scale)):
            self._apply_theme()
        if apply_constraints:
            self._apply_window_constraints()

        if resize:
            self.resize(ratio_size_from_width(width, self._mode_base_height()))

    def change_title_bar_color(self) -> None:
        set_windows_title_bar_colors(self, self.current_theme["bg"], self.current_theme["text"])

    def previous_style(self) -> None:
        self.style_index = (self.style_index - 1) % len(self.themes)
        self._refresh_style_controller()

    def next_style(self) -> None:
        self.style_index = (self.style_index + 1) % len(self.themes)
        self._refresh_style_controller()

    def _refresh_style_controller(self) -> None:
        self.current_theme = self.themes[self.style_index]
        self.background_shapes = self._make_background_shapes()
        self.style_name_label.setText(self.current_theme["name"])
        self._apply_theme()
        self._refresh_current_view_layout()
        self._save_theme_settings()
        self.update()

    def _refresh_current_view_layout(self) -> None:
        if not hasattr(self, "root_layout"):
            return

        self.project_list_last_metrics = None
        self._set_window_scale(self.window_scale, resize=False, apply_constraints=True)
        if self.list_mode:
            self._resize_current_mode_to_width(self.width())
        self._refresh_ui()
        self.update()

    def toggle_list_view(self) -> None:
        current_width = self.width()
        self.list_mode = not self.list_mode
        self.timer_view.setVisible(not self.list_mode)
        self.list_view.setVisible(self.list_mode)
        if self.list_mode:
            self._rebuild_project_list()
        self._resize_current_mode_to_width(current_width)
        self._refresh_ui()
        self._save_app_settings()

    def _clear_project_list(self) -> None:
        while self.project_list_layout.count():
            item = self.project_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.project_list_rows = []
        self.project_list_row_items = []
        self.project_list_buttons = []
        self.project_list_last_metrics = None

    def _rebuild_project_list(self) -> None:
        if not hasattr(self, "project_list_layout"):
            return

        self._clear_project_list()
        icon_color = self.current_theme.get("icon", self.current_theme["muted"])
        active_icon_color = self.current_theme["bg"]

        for index, project in enumerate(self.projects):
            row = ProjectListRowFrame(self)
            row.setObjectName("ProjectListRow")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            row.mousePressEvent = lambda event, row_index=index: self._select_project_from_list(row_index)
            row.setProjectName(project.name)
            row.setTimeText(self._format_elapsed(self._elapsed_for(index)))

            edit_button = IconButton("edit", "Edit project", row)
            edit_button.clicked.connect(lambda _checked=False, row_index=index: self.edit_project(row_index))

            remove_button = IconButton("trash", "Remove project", row)
            remove_button.clicked.connect(lambda _checked=False, row_index=index: self.remove_project(row_index))

            up_button = IconButton("move_up", "Move project up", row)
            up_button.clicked.connect(lambda _checked=False, row_index=index: self.move_project(row_index, -1))

            down_button = IconButton("move_down", "Move project down", row)
            down_button.clicked.connect(lambda _checked=False, row_index=index: self.move_project(row_index, 1))

            timer_button = IconButton("play", "Start project timer", row)
            timer_button.clicked.connect(lambda _checked=False, row_index=index: self.toggle_project_timer(row_index))

            reset_button = IconButton("reset", "Restart project timer", row)
            reset_button.clicked.connect(lambda _checked=False, row_index=index: self.restart_project_timer(row_index))

            for button in (edit_button, remove_button, up_button, down_button, timer_button, reset_button):
                button.setIconPalette(icon_color, active_icon_color)
                self.project_list_buttons.append(button)

            item = ProjectListRowItem(
                row,
                edit_button,
                remove_button,
                up_button,
                down_button,
                timer_button,
                reset_button,
            )
            row.row_item = item
            self.project_list_rows.append(row)
            self.project_list_row_items.append(item)
            self.project_list_layout.addWidget(row)

        self.project_list_layout.addStretch(1)
        self._rescale_project_list_rows()
        self._refresh_project_list_state()

    def _select_project_from_list(self, index: int) -> None:
        if index < 0 or index >= len(self.projects) or index == self.active_index:
            return
        self._project_selected(index)

    def _refresh_project_list_state(self) -> None:
        if not hasattr(self, "project_list_rows"):
            return

        for index, item in enumerate(self.project_list_row_items):
            row = item.row
            active = index == self.active_index
            if row.property("active") != active:
                row.setProperty("active", active)
                row.style().unpolish(row)
                row.style().polish(row)
            row.setTimeText(self._format_elapsed(self._elapsed_for(index)))

            item.remove_button.setEnabled(len(self.projects) > 1)
            item.up_button.setEnabled(index > 0)
            item.down_button.setEnabled(index < len(self.projects) - 1)
            timer_active = self.running and index == self.active_index
            item.timer_button.setIconName("stop" if timer_active else "play")
            item.timer_button.setActive(timer_active)
            item.timer_button.setToolTip("Stop project timer" if timer_active else "Start project timer")

    def move_project(self, index: int, direction: int) -> None:
        new_index = index + direction
        if index < 0 or index >= len(self.projects) or new_index < 0 or new_index >= len(self.projects):
            return

        if self.running:
            self._commit_elapsed()
            self.started_at = time.monotonic()

        project = self.projects.pop(index)
        self.projects.insert(new_index, project)
        if self.active_index == index:
            self.active_index = new_index
        elif index < self.active_index <= new_index:
            self.active_index -= 1
        elif new_index <= self.active_index < index:
            self.active_index += 1

        self._save()
        self._sync_project_menu()
        self._rebuild_project_list()
        if self.list_mode:
            self._resize_current_mode_to_width()
        self._refresh_ui()
        self._save_app_settings()

    def toggle_project_timer(self, index: int) -> None:
        if index < 0 or index >= len(self.projects):
            return

        if self.running and index == self.active_index:
            self._commit_elapsed()
            self.running = False
            self.started_at = None
        else:
            if self.running:
                self._commit_elapsed()
            self.active_index = index
            self.running = True
            self.started_at = time.monotonic()

        self._sync_project_menu()
        self._refresh_ui()
        self._save()
        self._save_app_settings()

    def restart_project_timer(self, index: int) -> None:
        if index < 0 or index >= len(self.projects):
            return

        project = self.projects[index]
        answer = QMessageBox.question(self, "Restart timer", f"Restart the timer for {project.name}?")
        if answer != QMessageBox.StandardButton.Yes:
            return

        was_running = self.running
        restarting_active_timer = was_running and index == self.active_index
        if was_running:
            self._commit_elapsed()
        project.seconds = 0

        if restarting_active_timer:
            self.running = False
            self.started_at = None
        elif was_running:
            self.started_at = time.monotonic()

        self._refresh_ui()
        self._save()
        self._save_app_settings()

    def zoom_in(self) -> None:
        self._set_window_scale(self.window_scale + WINDOW_SCALE_STEP)

    def zoom_out(self) -> None:
        self._set_window_scale(self.window_scale - WINDOW_SCALE_STEP)

    def open_theme_builder(self) -> None:
        dialog = ThemeBuilderDialog(self, self.themes, self.style_index)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.themes = dialog.themes
        self.style_index = max(0, min(dialog.active_index, len(self.themes) - 1))
        save_themes(self.themes)
        self._refresh_style_controller()

    def toggle_time_style(self) -> None:
        self.time_style = "units" if self.time_style == "clean" else "clean"
        self._refresh_ui()
        self._save_app_settings()

    def _format_elapsed(self, seconds: float) -> str:
        if self.time_style == "units":
            return format_seconds_with_units(seconds)
        return format_seconds(seconds)

    def _sync_project_menu(self) -> None:
        self.project_menu.blockSignals(True)
        self.project_menu.clear()
        self.project_menu.addItems([project.name for project in self.projects])
        self.active_index = min(self.active_index, len(self.projects) - 1)
        self.project_menu.setCurrentIndex(self.active_index)
        self.project_menu.blockSignals(False)
        self.project_menu.clearFocus()

    def _project_selected(self, index: int) -> None:
        if index < 0 or index == self.active_index:
            self.project_menu.clearFocus()
            return

        if self.running:
            self._commit_elapsed()
            self.running = False
            self.started_at = None
        self.active_index = index
        self._refresh_ui()
        self._save()
        self._save_app_settings()
        self.project_menu.clearFocus()

    def toggle_always_on_top(self) -> None:
        self.always_on_top = not self.always_on_top
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.always_on_top)
        self.show()
        self._refresh_stateful_buttons()
        self.change_title_bar_color()
        self._save_app_settings()

    def toggle_timer(self) -> None:
        if self.running:
            self._commit_elapsed()
            self.running = False
            self.started_at = None
        else:
            self.running = True
            self.started_at = time.monotonic()

        self._refresh_ui()
        self._save()
        self._save_app_settings()

    def restart_timer(self) -> None:
        self.restart_project_timer(self.active_index)

    def add_project(self) -> None:
        dialog = ProjectDialog(self, "Add Project", show_time=False)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result_value:
            return

        name, _seconds = dialog.result_value
        if self._name_exists(name):
            QMessageBox.warning(self, "Project exists", "Choose a different project name.")
            return

        if self.running:
            self._commit_elapsed()
            self.running = False
            self.started_at = None
        self.projects.insert(0, Project(name, 0))
        self.active_index = 0
        self._save()
        self._sync_project_menu()
        self._rebuild_project_list()
        if self.list_mode:
            self._resize_current_mode_to_width()
        self._refresh_ui()
        self._save_app_settings()

    def edit_project(self, index: int | None = None) -> None:
        if isinstance(index, bool):
            index = None
        edit_index = self.active_index if index is None else index
        if edit_index < 0 or edit_index >= len(self.projects):
            return

        if self.running:
            self._commit_elapsed()

        project = self.projects[edit_index]
        dialog = ProjectDialog(self, "Edit Project", name=project.name, elapsed=format_seconds(project.seconds), show_time=True)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result_value:
            if self.running:
                self.started_at = time.monotonic()
            return

        name, seconds = dialog.result_value
        if self._name_exists(name, ignore_index=edit_index):
            QMessageBox.warning(self, "Project exists", "Choose a different project name.")
            if self.running:
                self.started_at = time.monotonic()
            return

        project.name = name
        project.seconds = seconds
        if self.running:
            self.started_at = time.monotonic()
        self._save()
        self._sync_project_menu()
        self._rebuild_project_list()
        if self.list_mode:
            self._resize_current_mode_to_width()
        self._refresh_ui()
        self._save_app_settings()

    def remove_project(self, index: int | None = None) -> None:
        if isinstance(index, bool):
            index = None
        if len(self.projects) <= 1:
            return

        remove_index = self.active_index if index is None else index
        if remove_index < 0 or remove_index >= len(self.projects):
            return

        project = self.projects[remove_index]
        answer = QMessageBox.question(self, "Remove project", f"Remove {project.name}?")
        if answer != QMessageBox.StandardButton.Yes:
            return

        if self.running:
            self._commit_elapsed()
        self.store.archive(project)
        del self.projects[remove_index]

        if remove_index == self.active_index:
            self.active_index = min(self.active_index, len(self.projects) - 1)
            self.running = False
            self.started_at = None
        else:
            if remove_index < self.active_index:
                self.active_index -= 1
            if self.running:
                self.started_at = time.monotonic()
        self._save()
        self._sync_project_menu()
        self._rebuild_project_list()
        if self.list_mode:
            self._resize_current_mode_to_width()
        self._refresh_ui()

    def _name_exists(self, name: str, ignore_index: int | None = None) -> bool:
        target = name.casefold()
        for index, project in enumerate(self.projects):
            if ignore_index is not None and index == ignore_index:
                continue
            if project.name.casefold() == target:
                return True
        return False

    def _elapsed_for(self, index: int) -> float:
        seconds = self.projects[index].seconds
        if self.running and index == self.active_index and self.started_at is not None:
            seconds += time.monotonic() - self.started_at
        return seconds

    def _commit_elapsed(self) -> None:
        if not self.running or self.started_at is None:
            return
        now = time.monotonic()
        self.projects[self.active_index].seconds += now - self.started_at
        self.started_at = now

    def _refresh_ui(self) -> None:
        if not self.projects:
            return

        project = self.projects[self.active_index]
        self.time_label.setText(self._format_elapsed(self._elapsed_for(self.active_index)))
        if self.project_menu.currentIndex() != self.active_index:
            self.project_menu.blockSignals(True)
            self.project_menu.setCurrentIndex(self.active_index)
            self.project_menu.blockSignals(False)
        self.toggle_button.setIconName("stop" if self.running else "play")
        self._refresh_stateful_buttons()
        self.remove_button.setEnabled(len(self.projects) > 1)
        if not (self.list_mode and self._is_resize_quiet_period()):
            self._refresh_project_list_state()

    def _refresh_stateful_buttons(self) -> None:
        self.list_button.setActive(self.list_mode)
        self.list_button.setToolTip("Timer view" if self.list_mode else "Project list view")

        self.top_button.setIconName("lock" if self.always_on_top else "unlock")
        self.top_button.setActive(self.always_on_top)
        self.top_button.setToolTip("Always on top is on" if self.always_on_top else "Always on top")

        units_active = self.time_style == "units"
        self.time_style_button.setActive(units_active)
        self.time_style_button.setToolTip("Time format: 00h:00m:00s" if units_active else "Time format: 00:00:00")

    def _save(self) -> None:
        self.ignore_project_file_changes_until = time.monotonic() + 0.75
        self.store.save(self.projects)
        self._watch_project_file()

    def _watch_project_file(self) -> None:
        if not hasattr(self, "project_file_watcher"):
            return

        path = str(DATA_FILE)
        watched_files = self.project_file_watcher.files()
        for watched_file in watched_files:
            if watched_file != path:
                self.project_file_watcher.removePath(watched_file)
        if DATA_FILE.exists() and path not in self.project_file_watcher.files():
            self.project_file_watcher.addPath(path)

    def _project_file_changed(self, _path: str) -> None:
        self._watch_project_file()
        if time.monotonic() < self.ignore_project_file_changes_until:
            return
        if self.pending_project_file_reload:
            return

        self.pending_project_file_reload = True
        QTimer.singleShot(150, self._reload_projects_from_file)

    def _reload_projects_from_file(self) -> None:
        self.pending_project_file_reload = False
        self._watch_project_file()
        if time.monotonic() < self.ignore_project_file_changes_until:
            return

        active_project_name = self.projects[self.active_index].name if self.projects else ""
        if self.running:
            self._commit_elapsed()
            self.running = False
            self.started_at = None

        self.ignore_project_file_changes_until = time.monotonic() + 0.75
        self.projects = self.store.load()
        self._watch_project_file()

        self.active_index = 0
        if active_project_name:
            for index, project in enumerate(self.projects):
                if project.name.casefold() == active_project_name.casefold():
                    self.active_index = index
                    break

        self._sync_project_menu()
        self._rebuild_project_list()
        if self.list_mode:
            self._resize_current_mode_to_width()
        self._refresh_ui()
        self._save_app_settings()

    def _tick(self) -> None:
        if self.running:
            if self.list_mode and self._is_resize_quiet_period():
                return
            self._refresh_ui()
            now = time.monotonic()
            if now - self.last_autosave >= 5:
                self._commit_elapsed()
                self._save()
                self.last_autosave = now

    def closeEvent(self, event) -> None:
        if self.running:
            self._commit_elapsed()
        self._save()
        self._save_app_settings()
        event.accept()


def main() -> None:
    ensure_app_files()
    if "--smoke-test" in sys.argv:
        projects = ProjectStore(DATA_FILE, ARCHIVE_FILE).load()
        themes = load_themes()
        if not projects or not themes:
            sys.exit(1)
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("Project Timer")
    app.setApplicationVersion(APP_VERSION)
    empty_icon = icon_path("empty")
    if empty_icon:
        app.setWindowIcon(QIcon(empty_icon))
    window = ProjectTimerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
