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
    SERVICE_RESET_CHORE,
)

_LOGGER = logging.getLogger(__name__)

# Storage for chores
CHORES = {}

# Mapping from entity IDs to chore names
ENTITY_ID_TO_CHORE_NAME = {}

# Home Assistant instance
_HASS = None

# Platforms supported by this integration
PLATFORMS = ["sensor"]

# Service schemas
ADD_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("due_date"): cv.date,
        vol.Required("interval"): vol.All(vol.Coerce(int), vol.Range(min=1)),
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

RESET_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.entity_domain("sensor"),
    }
)

LIST_CHORES_SCHEMA = vol.Schema({})


async def async_check_overdue_chores(time):
    """Check for overdue chores and reset recurring chores."""
    global _HASS
    now = datetime.now().date()
    for chore_name, chore_data in CHORES.items():
        # Check if pending chores are overdue
        if chore_data["state"] == STATE_PENDING and "due_date" in chore_data:
            if chore_data["due_date"] < now:
                CHORES[chore_name]["state"] = STATE_OVERDUE
                _LOGGER.info("Chore '%s' is now overdue", chore_name)
        
        # Check if completed chores should be reset to pending
        elif chore_data["state"] == STATE_COMPLETED and "next_due_date" in chore_data:
            if chore_data["next_due_date"] <= now:
                # Reset the chore to pending with new due date
                CHORES[chore_name]["state"] = STATE_PENDING
                CHORES[chore_name]["due_date"] = chore_data["next_due_date"]
                
                # Remove completed_date and next_due_date as they're no longer relevant
                if "completed_date" in CHORES[chore_name]:
                    del CHORES[chore_name]["completed_date"]
                if "next_due_date" in CHORES[chore_name]:
                    del CHORES[chore_name]["next_due_date"]
                
                _LOGGER.info("Chore '%s' reset to pending, due: %s", chore_name, chore_data["next_due_date"])
    
    # Notify entities to update
    if _HASS:
        _HASS.bus.async_fire(f"{DOMAIN}_updated")


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
        entity_id = f"sensor.chore_assistant_{chore_name.lower().replace(' ', '_')}"
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
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_CHORE, async_reset_chore, schema=RESET_CHORE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "list_chores", async_list_chores, schema=LIST_CHORES_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "check_recurring", async_check_recurring_chores, schema=LIST_CHORES_SCHEMA
    )

    # Schedule daily check for overdue chores and recurring chores
    # Check for overdue chores and reset recurring chores every day at midnight
    async_track_time_change(
        hass, async_check_overdue_chores, hour=0, minute=0, second=0
    )

    # Forward setup to sensor platform
    _LOGGER.info("Loading sensor platform")
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    _LOGGER.info("Chore Assistant component setup complete")

    return True


async def async_add_chore(call: ServiceCall) -> None:
    """Add a new chore."""
    global _HASS
    name = call.data.get("name")
    due_date = call.data.get("due_date")  # Now required
    interval = call.data.get("interval")  # Now required (in days)
    assigned_to = call.data.get("assigned_to")

    # Create chore data
    chore_data = {
        "name": name,
        "state": STATE_PENDING,
        "created_date": datetime.now().date(),
        "due_date": due_date,
        "interval": interval,
    }

    # Check if already overdue
    if due_date < datetime.now().date():
        chore_data["state"] = STATE_OVERDUE

    if assigned_to:
        chore_data["assigned_to"] = assigned_to

    # Add to storage
    CHORES[name] = chore_data

    # Add to entity ID mapping
    entity_id = f"sensor.chore_assistant_{name.lower().replace(' ', '_')}"
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
        
        # Calculate next due date based on interval
        current_due_date = CHORES[name]["due_date"]
        interval = CHORES[name]["interval"]
        next_due_date = current_due_date + timedelta(days=interval)
        CHORES[name]["next_due_date"] = next_due_date
        
        _LOGGER.info("Completed chore: %s, next due: %s", name, next_due_date)
    else:
        _LOGGER.warning("Chore '%s' not found", name)

    # Notify entities to update
    _HASS.bus.async_fire(f"{DOMAIN}_updated")


async def async_reset_chore(call: ServiceCall) -> None:
    """Reset a chore to pending state."""
    global _HASS
    entity_id = call.data.get("name")
    
    # Get chore name from entity ID mapping
    if entity_id in ENTITY_ID_TO_CHORE_NAME:
        name = ENTITY_ID_TO_CHORE_NAME[entity_id]
    else:
        _LOGGER.warning("Chore with entity ID '%s' not found", entity_id)
        return

    if name in CHORES:
        current_state = CHORES[name]["state"]
        CHORES[name]["state"] = STATE_PENDING
        
        # Remove completed-related fields if they exist
        if "completed_date" in CHORES[name]:
            del CHORES[name]["completed_date"]
        if "next_due_date" in CHORES[name]:
            del CHORES[name]["next_due_date"]
        
        # Check if the chore should be overdue based on current due date
        if "due_date" in CHORES[name] and CHORES[name]["due_date"] < datetime.now().date():
            CHORES[name]["state"] = STATE_OVERDUE
            _LOGGER.info("Reset chore '%s' to overdue (due date has passed)", name)
        else:
            _LOGGER.info("Reset chore '%s' from %s to pending", name, current_state)
    else:
        _LOGGER.warning("Chore '%s' not found", name)

    # Notify entities to update
    _HASS.bus.async_fire(f"{DOMAIN}_updated")


async def async_list_chores(call: ServiceCall) -> None:
    """List all chores."""
    global _HASS
    _LOGGER.info("Listing all chores:")
    for chore_name, chore_data in CHORES.items():
        _LOGGER.info("  - %s: %s", chore_name, chore_data)
    
    # List entity ID mapping
    _LOGGER.info("Entity ID mapping:")
    for entity_id, chore_name in ENTITY_ID_TO_CHORE_NAME.items():
        _LOGGER.info("  - %s -> %s", entity_id, chore_name)


async def async_check_recurring_chores(call: ServiceCall) -> None:
    """Manually check for recurring chores that need to be reset."""
    global _HASS
    _LOGGER.info("Manually checking for recurring chores...")
    await async_check_overdue_chores(None)
    _LOGGER.info("Recurring chore check completed")
