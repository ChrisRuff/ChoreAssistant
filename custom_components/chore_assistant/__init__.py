"""The Chore Assistant integration."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

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

# Service schemas
ADD_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("due_date"): cv.date,
        vol.Optional("assigned_to"): cv.string,
    }
)

REMOVE_CHORE_SCHEMA = vol.Schema({vol.Required("name"): cv.string})

COMPLETE_CHORE_SCHEMA = vol.Schema({vol.Required("name"): cv.string})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Chore Assistant component."""
    _LOGGER.info("Setting up Chore Assistant component")

    # Initialize chores storage
    hass.data[DOMAIN] = {"chores": CHORES}

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
        # Trigger entity updates
        await hass.helpers.entity_component.async_update_entity_component(DOMAIN)

    # Check for overdue chores every day at midnight
    hass.helpers.event.async_track_time_change(
        async_check_overdue_chores, hour=0, minute=0, second=0
    )

    return True


async def async_add_chore(call: ServiceCall) -> None:
    """Add a new chore."""
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

    _LOGGER.info("Added chore: %s", name)

    # Notify entities to update
    hass.bus.async_fire(f"{DOMAIN}_updated")


async def async_remove_chore(call: ServiceCall) -> None:
    """Remove a chore."""
    name = call.data.get("name")

    if name in CHORES:
        del CHORES[name]
        _LOGGER.info("Removed chore: %s", name)
        
        # Remove entity if it exists
        entity_registry = async_get_entity_registry(hass)
        entity_id = f"sensor.chore_{name.lower().replace(' ', '_')}"
        if entity_registry.async_get(entity_id):
            entity_registry.async_remove(entity_id)
    else:
        _LOGGER.warning("Chore '%s' not found", name)

    # Notify entities to update
    hass.bus.async_fire(f"{DOMAIN}_updated")


async def async_complete_chore(call: ServiceCall) -> None:
    """Mark a chore as completed."""
    name = call.data.get("name")

    if name in CHORES:
        CHORES[name]["state"] = STATE_COMPLETED
        CHORES[name]["completed_date"] = datetime.now().date()
        _LOGGER.info("Completed chore: %s", name)
    else:
        _LOGGER.warning("Chore '%s' not found", name)

    # Notify entities to update
    hass.bus.async_fire(f"{DOMAIN}_updated")
