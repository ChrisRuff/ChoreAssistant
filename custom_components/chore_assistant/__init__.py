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
    SERVICE_ADD_CHORE,
    SERVICE_REMOVE_CHORE,
    SERVICE_COMPLETE_CHORE,
    SERVICE_RESET_CHORE,
    SERVICE_UPDATE_CHORE,
    EVENT_CHORE_ADDED,
    EVENT_CHORE_REMOVED,
    EVENT_CHORE_COMPLETED,
    EVENT_CHORE_RESET,
    EVENT_CHORE_OVERDUE,
    EVENT_CHORE_UPDATED,
)
from .models import Chore
from .storage import ChoreStorage
from .state_manager import ChoreStateManager
from .validation import (
    ADD_CHORE_SCHEMA,
    REMOVE_CHORE_SCHEMA,
    COMPLETE_CHORE_SCHEMA,
    RESET_CHORE_SCHEMA,
    UPDATE_CHORE_SCHEMA,
    LIST_CHORES_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

# Platforms supported by this integration
PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Chore Assistant component."""
    _LOGGER.info("Setting up Chore Assistant component")

    # Initialize storage
    storage = ChoreStorage(hass)
    await storage.async_load()

    # Initialize state manager
    state_manager = ChoreStateManager(storage)

    # Store references in hass.data
    hass.data[DOMAIN] = {
        "storage": storage,
        "state_manager": state_manager,
    }

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
        DOMAIN, SERVICE_UPDATE_CHORE, async_update_chore, schema=UPDATE_CHORE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "list_chores", async_list_chores, schema=LIST_CHORES_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "check_recurring", async_check_recurring_chores, schema=LIST_CHORES_SCHEMA
    )

    # Schedule daily check for overdue chores and recurring chores
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
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    state_manager: ChoreStateManager = hass.data[DOMAIN]["state_manager"]

    name = call.data.get("chore_name")
    due_date = call.data.get("due_date")
    interval_days = call.data.get("interval_days", 7)
    assigned_to = call.data.get("assigned_to")
    description = call.data.get("description")
    priority = call.data.get("priority", "medium")
    tags = call.data.get("tags", [])

    try:
        # Create new chore
        from datetime import datetime
        from .models import ChoreMetadata
        
        chore = Chore(
            id=name.lower().replace(" ", "_"),
            name=name,
            state="pending",
            created_date=datetime.now(),
            due_date=due_date,
            interval_days=interval_days,
            assigned_to=assigned_to,
            metadata=ChoreMetadata(
                priority=priority,
                category="general",
                estimated_duration=30
            )
        )

        # Add to storage
        await storage.async_add_chore(chore)

        # Fire event
        hass.bus.async_fire(EVENT_CHORE_ADDED, {
            "chore_id": chore.id,
            "name": name,
            "due_date": due_date.isoformat() if due_date else None,
            "interval_days": interval_days,
        })

        _LOGGER.info("Added chore: %s", name)

    except Exception as err:
        _LOGGER.error("Failed to add chore '%s': %s", name, err)
        raise


async def async_remove_chore(call: ServiceCall) -> None:
    """Remove a chore."""
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    state_manager: ChoreStateManager = hass.data[DOMAIN]["state_manager"]

    chore_id = call.data.get("chore_id")

    try:
        # Get chore
        chore = await storage.async_get_chore(chore_id)
        if not chore:
            _LOGGER.warning("Chore with ID '%s' not found", chore_id)
            return

        # Remove from storage
        await storage.async_remove_chore(chore_id)

        # Remove entity if it exists
        entity_registry = async_get_entity_registry(hass)
        entity_id = f"sensor.chore_assistant_{chore_id}"
        if entity_registry.async_get(entity_id):
            entity_registry.async_remove(entity_id)

        # Fire event
        hass.bus.async_fire(EVENT_CHORE_REMOVED, {
            "chore_id": chore_id,
            "name": chore.name,
        })

        _LOGGER.info("Removed chore: %s", chore.name)

    except Exception as err:
        _LOGGER.error("Failed to remove chore '%s': %s", chore_id, err)
        raise


async def async_complete_chore(call: ServiceCall) -> None:
    """Mark a chore as completed."""
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    state_manager: ChoreStateManager = hass.data[DOMAIN]["state_manager"]

    chore_id = call.data.get("chore_id")
    completed_by = call.data.get("completed_by")
    notes = call.data.get("notes")

    try:
        # Get chore
        chore = await storage.async_get_chore(chore_id)
        if not chore:
            _LOGGER.warning("Chore with ID '%s' not found", chore_id)
            return

        # Complete the chore
        await state_manager.complete_chore(chore_id, completed_by=completed_by, notes=notes)

        # Fire event
        hass.bus.async_fire(EVENT_CHORE_COMPLETED, {
            "chore_id": chore_id,
            "name": chore.name,
            "completed_by": completed_by,
            "notes": notes,
        })

        _LOGGER.info("Completed chore: %s", chore.name)

    except Exception as err:
        _LOGGER.error("Failed to complete chore '%s': %s", chore_id, err)
        raise


async def async_reset_chore(call: ServiceCall) -> None:
    """Reset a chore to pending state."""
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    state_manager: ChoreStateManager = hass.data[DOMAIN]["state_manager"]

    chore_id = call.data.get("chore_id")
    reason = call.data.get("reason")

    try:
        # Get chore
        chore = await storage.async_get_chore(chore_id)
        if not chore:
            _LOGGER.warning("Chore with ID '%s' not found", chore_id)
            return

        # Reset the chore
        await state_manager.reset_chore(chore_id, reason=reason)

        # Fire event
        hass.bus.async_fire(EVENT_CHORE_RESET, {
            "chore_id": chore_id,
            "name": chore.name,
            "reason": reason,
        })

        _LOGGER.info("Reset chore: %s", chore.name)

    except Exception as err:
        _LOGGER.error("Failed to reset chore '%s': %s", chore_id, err)
        raise


async def async_update_chore(call: ServiceCall) -> None:
    """Update an existing chore's details."""
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    state_manager: ChoreStateManager = hass.data[DOMAIN]["state_manager"]

    chore_id = call.data.get("chore_id")
    chore_name = call.data.get("chore_name")
    interval_days = call.data.get("interval_days")
    due_date = call.data.get("due_date")
    assigned_to = call.data.get("assigned_to")
    priority = call.data.get("priority")
    category = call.data.get("category")
    estimated_duration = call.data.get("estimated_duration")

    try:
        # Get chore
        chore = await storage.async_get_chore(chore_id)
        if not chore:
            _LOGGER.warning("Chore with ID '%s' not found", chore_id)
            return

        # Update chore fields if provided
        if chore_name is not None:
            chore.name = chore_name
        if interval_days is not None:
            chore.interval_days = interval_days
        if due_date is not None:
            chore.due_date = due_date
        if assigned_to is not None:
            chore.assigned_to = assigned_to
        if priority is not None:
            chore.metadata.priority = priority
        if category is not None:
            chore.metadata.category = category
        if estimated_duration is not None:
            chore.metadata.estimated_duration = estimated_duration

        # Update in storage
        await storage.async_update_chore(chore)

        # Fire event
        hass.bus.async_fire(EVENT_CHORE_UPDATED, {
            "chore_id": chore_id,
            "name": chore.name,
            "updated_fields": list(call.data.keys()),
        })

        _LOGGER.info("Updated chore: %s", chore.name)

    except Exception as err:
        _LOGGER.error("Failed to update chore '%s': %s", chore_id, err)
        raise


async def async_list_chores(call: ServiceCall) -> None:
    """List all chores."""
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]

    try:
        chores = await storage.async_get_all_chores()
        
        _LOGGER.info("Listing all chores:")
        for chore in chores:
            _LOGGER.info("  - %s (%s): %s", chore.name, chore.id, chore.state)
            _LOGGER.info("    Due: %s, Interval: %s days", 
                        chore.due_date, chore.interval_days)
            _LOGGER.info("    History entries: %d", len(chore.history))
            _LOGGER.info("    Statistics: %s", chore.statistics.to_dict())

    except Exception as err:
        _LOGGER.error("Failed to list chores: %s", err)
        raise


async def async_check_recurring_chores(call: ServiceCall) -> None:
    """Manually check for recurring chores that need to be reset."""
    hass = call.hass
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    state_manager: ChoreStateManager = hass.data[DOMAIN]["state_manager"]

    try:
        _LOGGER.info("Manually checking for recurring chores...")
        
        # Get all chores
        chores = await storage.async_get_all_chores()
        
        # Check each chore
        for chore in chores:
            if chore.state == "completed" and chore.interval_days:
                # Check if it's time to reset
                if chore.due_date and chore.due_date <= datetime.now().date():
                    await state_manager.reset_chore(chore.id, reason="recurring")
                    _LOGGER.info("Reset recurring chore: %s", chore.name)

        _LOGGER.info("Recurring chore check completed")

    except Exception as err:
        _LOGGER.error("Failed to check recurring chores: %s", err)
        raise


async def async_check_overdue_chores(time) -> None:
    """Check for overdue chores and reset recurring chores."""
    hass = None  # This will be set by the caller
    
    # Find the Home Assistant instance
    # Note: This is called from async_track_time_change, so we need to get hass differently
    # This is a limitation of the current approach - we'll fix this in the sensor platform
    
    _LOGGER.info("Checking for overdue chores...")
    
    # This function will be properly implemented in the sensor platform
    # where we have access to the hass instance
    pass
