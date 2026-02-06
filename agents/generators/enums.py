"""Enums that define settings for customizing the README file."""

from enum import Enum


class BadgeStyles(str, Enum):
    """
    Badge icon styles for the project README.
    """

    DEFAULT = "default"
    FLAT = "flat"
    FLAT_SQUARE = "flat-square"
    FOR_THE_BADGE = "for-the-badge"
    PLASTIC = "plastic"
    SKILLS = "skills"
    SKILLS_LIGHT = "skills-light"
    SOCIAL = "social"


class CustomLogos(str, Enum):
    """
    Options for custom/external project logo files.
    """

    CUSTOM = "CUSTOM"
    LLM = "LLM"


class DefaultLogos(str, Enum):
    """
    Predefined SVG project logo options.
    """

    ANIMATED = "agents/assets/logos/animated.svg"
    AURORA = "agents/assets/logos/aurora.svg"
    BLUE = "agents/assets/logos/blue.svg"
    GREEN = "agents/assets/logos/green.svg"
    ICE = "agents/assets/logos/ice.svg"
    METALLIC = "agents/assets/logos/metallic.svg"
    MIDNIGHT = "agents/assets/logos/midnight.svg"
    ORANGE = "agents/assets/logos/orange.svg"
    PURPLE = "agents/assets/logos/purple.svg"
    RAINBOW = "agents/assets/logos/rainbow.svg"
    TERMINAL = "agents/assets/logos/terminal.svg"


class EmojiThemes(str, Enum):
    """
    Emoji theme 'packs' for customizing header section titles.
    """

    # -- Core
    DEFAULT = "default"
    MINIMAL = "minimal"
    # OSS = "oss"

    # -- Development
    # API = "api"
    # GAME = "game"
    # MOBILE = "mobile"
    # WEB = "web"

    # -- Infrastructure
    # CLOUD = "cloud"
    # CYBER = "cyber"
    # IOT = "iot"

    # -- Data and AI
    # DATA = "data"
    # ML = "ml"

    # -- Geometric and Abstract
    ASCENSION = "ascension"
    FIBONACCI = "fibonacci"
    HARMONY = "harmony"
    PRISM = "prism"
    QUANTUM = "quantum"

    # -- Monochrome and Unicode
    MONOCHROME = "monochrome"
    UNICODE = "unicode"

    # -- Nature and Elements
    ATOMIC = "atomic"
    COSMIC = "cosmic"
    CRYSTAL = "crystal"
    EARTH = "earth"
    FIRE = "fire"
    FOREST = "forest"
    NATURE = "nature"
    RAINBOW = "rainbow"
    SOLAR = "solar"
    WATER = "water"

    # -- Miscellaneous
    FUN = "fun"
    VINTAGE = "vintage"
    ZEN = "zen"

    # -- Random
    RANDOM = "random"


class HeaderStyles(str, Enum):
    """
    Header style template options for the README file.
    """

    ASCII = "ascii"
    ASCII_BOX = "ascii_box"
    BANNER = "banner"
    CLASSIC = "classic"
    CLEAN = "clean"
    COMPACT = "compact"
    CONSOLE = "console"
    MODERN = "modern"


class NavigationStyles(str, Enum):
    """
    Navigation menu styles for the README file.
    """

    ACCORDION = "accordion"
    BULLET = "bullet"
    NUMBER = "number"
    ROMAN = "roman"
