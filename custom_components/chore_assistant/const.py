"""Constants for Chore Assistant integration."""

DOMAIN = "chore_assistant"

# Storage configuration
STORAGE_VERSION = 2
STORAGE_KEY = f"{DOMAIN}_storage"

# Chore states
STATE_PENDING = "pending"
STATE_COMPLETED = "completed"
STATE_OVERDUE = "overdue"

VALID_STATES = [STATE_PENDING, STATE_COMPLETED, STATE_OVERDUE]

# Service names
SERVICE_ADD_CHORE = "add_chore"
SERVICE_REMOVE_CHORE = "remove_chore"
SERVICE_COMPLETE_CHORE = "complete_chore"
SERVICE_RESET_CHORE = "reset_chore"
SERVICE_LIST_CHORES = "list_chores"
SERVICE_UPDATE_CHORE = "update_chore"

# Service fields
ATTR_CHORE_ID = "chore_id"
ATTR_CHORE_NAME = "name"
ATTR_INTERVAL_DAYS = "interval_days"
ATTR_DUE_DATE = "due_date"
ATTR_ASSIGNED_TO = "assigned_to"
ATTR_PRIORITY = "priority"
ATTR_CATEGORY = "category"
ATTR_ESTIMATED_DURATION = "estimated_duration"
ATTR_NOTES = "notes"
ATTR_COMPLETED_BY = "completed_by"
ATTR_TAGS = "tags"
ATTR_DESCRIPTION = "description"
ATTR_REASON = "reason"

# Priority levels
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_CRITICAL = "critical"

VALID_PRIORITIES = [PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL]

# Default values
DEFAULT_INTERVAL_DAYS = 7
DEFAULT_PRIORITY = PRIORITY_MEDIUM
DEFAULT_CATEGORY = "general"
DEFAULT_ESTIMATED_DURATION = 30

# Event names
EVENT_CHORE_CREATED = f"{DOMAIN}_chore_created"
EVENT_CHORE_COMPLETED = f"{DOMAIN}_chore_completed"
EVENT_CHORE_RESET = f"{DOMAIN}_chore_reset"
EVENT_CHORE_REMOVED = f"{DOMAIN}_chore_removed"
EVENT_CHORE_OVERDUE = f"{DOMAIN}_chore_overdue"
EVENT_CHORE_UPDATED = f"{DOMAIN}_chore_updated"
EVENT_CHORE_ADDED = f"{DOMAIN}_chore_added"

# Configuration
CONF_BACKUP_COUNT = 10
CONF_BACKUP_RETENTION_DAYS = 30

# Error messages
ERROR_CHORE_NOT_FOUND = "Chore not found"
ERROR_INVALID_STATE = "Invalid state transition"
ERROR_DUPLICATE_CHORE = "Chore with this name already exists"
ERROR_INVALID_DATA = "Invalid chore data provided"
ERROR_STORAGE_FAILURE = "Storage operation failed"

# Validation limits
MIN_CHORE_NAME_LENGTH = 1
MAX_CHORE_NAME_LENGTH = 100
MIN_INTERVAL_DAYS = 1
MAX_INTERVAL_DAYS = 365
MIN_ESTIMATED_DURATION = 1
MAX_ESTIMATED_DURATION = 1440  # 24 hours in minutes

# Backup configuration
BACKUP_FILENAME_PREFIX = "chore_assistant_backup"
BACKUP_EXTENSION = ".json"
