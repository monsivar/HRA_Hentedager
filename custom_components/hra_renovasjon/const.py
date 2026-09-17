"""Constants for HRA renovasjon."""

DOMAIN = "hra_renovasjon"
NAME = "HRA renovasjon"
MANUFACTURER = "HRA"
API_BASE_URL = "https://api.hra.no"

CONF_ADDRESS = "address"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 24
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 168

ATTR_ADDRESS = "address"
ATTR_AGREEMENT_GUID = "agreement_guid"
ATTR_DAYS_UNTIL = "days_until"
ATTR_NEXT_COLLECTION = "next_collection"
ATTR_UPCOMING = "upcoming"
ATTR_WASTE_TYPE = "waste_type"

ICON = "mdi:trash-can-outline"
CALENDAR_NAME = "HRA hentedager"
WASTE_EMOJIS = {
    "Restavfall": "🗑️",
    "Matavfall": "🍎",
    "Plastemballasje": "🧴",
    "Papir, papp og kartong": "📄",
    "Glass- og metallemballasje": "🥫",
}

ASSET_BASE_URL = "/api/hra_renovasjon/assets"
CARD_URL = "/api/hra_renovasjon/hra-renovasjon-card.js"
CARD_VERSION = "0.2.0"
ASSET_FILES = {
    "Restavfall": "waste-new.png",
    "Matavfall": "organic-new.png",
    "Plastemballasje": "plastic-new.png",
    "Papir, papp og kartong": "paper_carton.png",
    "Glass- og metallemballasje": "glass_metal.png",
}
FALLBACK_ICONS = {
    "Restavfall": "mdi:trash-can-outline",
    "Matavfall": "mdi:food-apple-outline",
    "Plastemballasje": "mdi:bottle-soda-outline",
    "Papir, papp og kartong": "mdi:file-document-outline",
    "Glass- og metallemballasje": "mdi:glass-fragile",
}
