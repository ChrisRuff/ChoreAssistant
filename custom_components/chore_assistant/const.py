"""Constants for the Chore Tracker integration."""

DOMAIN = "chore_assistant"

# Service names
SERVICE_ADD_CHORE = "add_chore"
SERVICE_REMOVE_CHORE = "remove_chore"
SERVICE_UPDATE_CHORE = "update_chore"
SERVICE_COMPLETE_CHORE = "complete_chore"

# Configuration keys
CONF_CHORE_NAME = "name"
CONF_DUE_DATE = "due_date"
CONF_FREQUENCY = "frequency"
CONF_DESCRIPTION = "description"
CONF_ASSIGNED_TO = "assigned_to"
CONF_CHORE_TYPE = "chore_type"
CONF_MAX_DAYS = "max_days"
CONF_ADAPTIVE_WINDOW = "adaptive_window"

# Chore types
CHORE_TYPE_FIXED = "fixed"
CHORE_TYPE_ADAPTIVE = "adaptive"

# Default values
DEFAULT_FREQUENCY = "weekly"
DEFAULT_DESCRIPTION = ""
DEFAULT_ASSIGNED_TO = "household"
DEFAULT_CHORE_TYPE = CHORE_TYPE_FIXED
DEFAULT_MAX_DAYS = 3
DEFAULT_ADAPTIVE_WINDOW = 3
