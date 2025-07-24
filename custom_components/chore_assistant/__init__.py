"""The Chore Assistant integration."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.discovery import async_load_platform

from .const import (
    DOMAIN,
    STATE_COMPLETED,
    STATE_OVERDUE,
    STATE_PENDING,
    SERVICE_ADD_CHORE,
    SERVICE_REMOVE_CHORE,
    SERVICE_COMPLETE_CHORE,
)

_LOGGER = logging.getLogger(__name__)

# Storage for chores
CHORES = {}

# Mapping from entity IDs to chore names
ENTITY_ID_TO_CHORE_NAME = {}

# Home Assistant instance
_HASS = None

# Service schemas
ADD_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("due_date"): cv.date,
        vol.Optional("assigned_to"): cv.string,
    }
)

REMOVE_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.entity_domain("sensor"),
    }
)

COMPLETE_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.entity_domain("sensor"),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Chore Assistant component."""
    global _HASS
    _LOGGER.info("Setting up Chore Assistant component")

    # Store Home Assistant instance
    _HASS = hass

    # Initialize chores storage
    hass.data[DOMAIN] = {"chores": CHORES}

    # Populate entity ID to chore name mapping for existing chores
    for chore_name in CHORES:
        entity_id = f"sensor.chore_assistant_{chore_name.lower()}"
        ENTITY_ID_TO_CHORE_NAME[entity_id] = chore_name

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_CHORE, async_add_chore, schema=ADD_CHORE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_CHORE, async_remove_chore, schema=REMOVE_CHORE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_COMPLETE_CHORE, async_complete_chore, schema=COMPLETE_CHORE_SCHEMA
    )

    # Schedule daily check for overdue chores
    async def async_check_overdue_chores(time):
        """Check for overdue chores."""
        now = datetime.now().date()
        for chore_name, chore_data in CHORES.items():
            if chore_data["state"] != STATE_COMPLETED and "due_date" in chore_data:
                if chore_data["due_date"] < now:
                    CHORES[chore_name]["state"] = STATE_OVERDUE
                    _LOGGER.info("Chore '%s' is now overdue", chore_name)

    # Check for overdue chores every day at midnight
    async_track_time_change(
        hass, async_check_overdue_chores, hour=0, minute=0, second=0
    )

    # Forward setup to sensor platform
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True


async def async_add_chore(call: ServiceCall) -> None:
    """Add a new chore."""
    global _HASS
    name = call.data.get("name")
    due_date = call.data.get("due_date")
    assigned_to = call.data.get("assigned_to")

    # Create chore data
    chore_data = {
        "name": name,
        "state": STATE_PENDING,
        "created_date": datetime.now().date(),
    }

    if due_date:
        chore_data["due_date"] = due_date
        # Check if already overdue
        if due_date < datetime.now().date():
            chore_data["state"] = STATE_OVERDUE

    if assigned_to:
        chore_data["assigned_to"] = assigned_to

    # Add to storage
    CHORES[name] = chore_data

    # Add to entity ID mapping
    entity_id = f"sensor.chore_assistant_{name.lower()}"
    ENTITY_ID_TO_CHORE_NAME[entity_id] = name

    _LOGGER.info("Added chore: %s", name)

    # Notify entities to update
    _HASS.bus.async_fire(f"{DOMAIN}_updated")


async def async_remove_chore(call: ServiceCall) -> None:
    """Remove a chore."""
    global _HASS
    entity_id = call.data.get("name")
    
    # Get chore name from entity ID mapping
    if entity_id in ENTITY_ID_TO_CHORE_NAME:
        name = ENTITY_ID_TO_CHORE_NAME[entity_id]
    else:
        _LOGGER.warning("Chore with entity ID '%s' not found", entity_id)
        return

    if name in CHORES:
        del CHORES[name]
        # Remove from entity ID mapping
        if entity_id in ENTITY_ID_TO_CHORE_NAME:
            del ENTITY_ID_TO_CHORE_NAME[entity_id]
        _LOGGER.info("Removed chore: %s", name)
        
        # Remove entity if it exists
        entity_registry = async_get_entity_registry(_HASS)
        if entity_registry.async_get(entity_id):
            entity_registry.async_remove(entity_id)
    else:
        _LOGGER.warning("Chore '%s' not found", name)

    # Notify entities to update
    _HASS.bus.async_fire(f"{DOMAIN}_updated")


async def async_complete_chore(call: ServiceCall) -> None:
    """Mark a chore as completed."""
    global _HASS
    entity_id = call.data.get("name")
    
    # Get chore name from entity ID mapping
    if entity_id in ENTITY_ID_TO_CHORE_NAME:
        name = ENTITY_ID_TO_CHORE_NAME[entity_id]
    else:
        _LOGGER.warning("Chore with entity ID '%s' not found", entity_id)
        return

    if name in CHORES:
        CHORES[name]["state"] = STATE_COMPLETED
        CHORES[name]["completed_date"] = datetime.now().date()
        _LOGGER.info("Completed chore: %s", name)
    else:
        _LOGGER.warning("Chore '%s' not found", name)

    # Notify entities to update
    _HASS.bus.async_fire(f"{DOMAIN}_updated")
