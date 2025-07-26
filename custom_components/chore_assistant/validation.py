"""Validation schemas for Chore Assistant integration."""
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from datetime import datetime, date

from .const import (
    ATTR_CHORE_ID,
    ATTR_CHORE_NAME,
    ATTR_INTERVAL_DAYS,
    ATTR_DUE_DATE,
    ATTR_ASSIGNED_TO,
    ATTR_PRIORITY,
    ATTR_CATEGORY,
    ATTR_ESTIMATED_DURATION,
    ATTR_NOTES,
    MIN_CHORE_NAME_LENGTH,
    MAX_CHORE_NAME_LENGTH,
    MIN_INTERVAL_DAYS,
    MAX_INTERVAL_DAYS,
    MIN_ESTIMATED_DURATION,
    MAX_ESTIMATED_DURATION,
    VALID_PRIORITIES,
)

# Base validation schemas
def validate_chore_name(value):
    """Validate chore name."""
    if not isinstance(value, str):
        raise vol.Invalid("Chore name must be a string")
    value = value.strip()
    if len(value) < MIN_CHORE_NAME_LENGTH:
        raise vol.Invalid(f"Chore name must be at least {MIN_CHORE_NAME_LENGTH} character")
    if len(value) > MAX_CHORE_NAME_LENGTH:
        raise vol.Invalid(f"Chore name must be no more than {MAX_CHORE_NAME_LENGTH} characters")
    return value

def validate_interval_days(value):
    """Validate interval days."""
    try:
        value = int(value)
    except (ValueError, TypeError):
        raise vol.Invalid("Interval days must be an integer")
    
    if value < MIN_INTERVAL_DAYS or value > MAX_INTERVAL_DAYS:
        raise vol.Invalid(f"Interval days must be between {MIN_INTERVAL_DAYS} and {MAX_INTERVAL_DAYS}")
    return value

def validate_estimated_duration(value):
    """Validate estimated duration."""
    try:
        value = int(value)
    except (ValueError, TypeError):
        raise vol.Invalid("Estimated duration must be an integer")
    
    if value < MIN_ESTIMATED_DURATION or value > MAX_ESTIMATED_DURATION:
        raise vol.Invalid(f"Estimated duration must be between {MIN_ESTIMATED_DURATION} and {MAX_ESTIMATED_DURATION} minutes")
    return value

def validate_priority(value):
    """Validate priority."""
    if value not in VALID_PRIORITIES:
        raise vol.Invalid(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")
    return value

def validate_due_date(value):
    """Validate due date."""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise vol.Invalid("Due date must be in YYYY-MM-DD format")
    elif isinstance(value, datetime):
        value = value.date()
    elif not isinstance(value, date):
        raise vol.Invalid("Due date must be a date")
    
    return value

# Service schemas
ADD_CHORE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CHORE_NAME): validate_chore_name,
    vol.Optional(ATTR_INTERVAL_DAYS, default=7): validate_interval_days,
    vol.Optional(ATTR_DUE_DATE): validate_due_date,
    vol.Optional(ATTR_ASSIGNED_TO, default=""): cv.string,
    vol.Optional(ATTR_PRIORITY, default="medium"): validate_priority,
    vol.Optional(ATTR_CATEGORY, default="general"): cv.string,
    vol.Optional(ATTR_ESTIMATED_DURATION, default=30): validate_estimated_duration,
})

REMOVE_CHORE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CHORE_ID): cv.string,
})

COMPLETE_CHORE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CHORE_ID): cv.string,
    vol.Optional(ATTR_NOTES): cv.string,
})

RESET_CHORE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CHORE_ID): cv.string,
    vol.Optional(ATTR_NOTES): cv.string,
})

UPDATE_CHORE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CHORE_ID): cv.string,
    vol.Optional(ATTR_CHORE_NAME): validate_chore_name,
    vol.Optional(ATTR_INTERVAL_DAYS): validate_interval_days,
    vol.Optional(ATTR_DUE_DATE): validate_due_date,
    vol.Optional(ATTR_ASSIGNED_TO): cv.string,
    vol.Optional(ATTR_PRIORITY): validate_priority,
    vol.Optional(ATTR_CATEGORY): cv.string,
    vol.Optional(ATTR_ESTIMATED_DURATION): validate_estimated_duration,
})

GET_CHORE_SCHEMA = vol.Schema({
    vol.Required(ATTR_CHORE_ID): cv.string,
})

LIST_CHORES_SCHEMA = vol.Schema({})

CHECK_OVERDUE_SCHEMA = vol.Schema({})