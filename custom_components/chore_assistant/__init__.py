"""Chore Tracker integration for Home Assistant"""
import logging
import os
import yaml
from datetime import datetime, timedelta

import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    SERVICE_ADD_CHORE,
    SERVICE_REMOVE_CHORE,
    SERVICE_UPDATE_CHORE,
    SERVICE_COMPLETE_CHORE,
    CONF_CHORE_NAME,
    CONF_DUE_DATE,
    CONF_FREQUENCY,
    CONF_DESCRIPTION,
    CONF_ASSIGNED_TO,
    CONF_CHORE_TYPE,
    CONF_MAX_DAYS,
    CONF_ADAPTIVE_WINDOW,
    CHORE_TYPE_FIXED,
    CHORE_TYPE_ADAPTIVE,
    DEFAULT_FREQUENCY,
    DEFAULT_DESCRIPTION,
    DEFAULT_ASSIGNED_TO,
    DEFAULT_CHORE_TYPE,
    DEFAULT_MAX_DAYS,
    DEFAULT_ADAPTIVE_WINDOW,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Chore Tracker integration."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chore Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Initialize chore storage
    chore_dir = hass.config.path("custom_components", "chore_assistant")
    chore_file = os.path.join(chore_dir, "chores.yaml")
    
    # Ensure directory exists
    os.makedirs(chore_dir, exist_ok=True)
    
    # Load existing chores
    chores = []
    if os.path.exists(chore_file):
        try:
            with open(chore_file, "r", encoding="utf-8") as file:
                chores = yaml.safe_load(file) or []
                if not isinstance(chores, list):
                    _LOGGER.warning("Invalid chores format, resetting to empty list")
                    chores = []
        except Exception as e:
            _LOGGER.error("Error loading chores: %s", e)
            chores = []
    
    # Store chores in hass data
    hass.data[DOMAIN]["chores"] = chores
    hass.data[DOMAIN]["chore_file"] = chore_file
    
    # Register services
    await _register_services(hass, entry)
    
    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def _register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register services for managing chores."""
    
    async def add_chore(call: ServiceCall) -> None:
        """Add a new chore."""
        try:
            name = call.data[CONF_CHORE_NAME]
            due_date = call.data[CONF_DUE_DATE]
            frequency = call.data.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
            description = call.data.get(CONF_DESCRIPTION, DEFAULT_DESCRIPTION)
            assigned_to = call.data.get(CONF_ASSIGNED_TO, DEFAULT_ASSIGNED_TO)
            chore_type = call.data.get(CONF_CHORE_TYPE, DEFAULT_CHORE_TYPE)
            max_days = call.data.get(CONF_MAX_DAYS, DEFAULT_MAX_DAYS)
            adaptive_window = call.data.get(CONF_ADAPTIVE_WINDOW, DEFAULT_ADAPTIVE_WINDOW)
            
            # Validate chore doesn't already exist
            existing_names = {chore["name"] for chore in hass.data[DOMAIN]["chores"]}
            if name in existing_names:
                _LOGGER.error("Chore '%s' already exists", name)
                return
            
            # Format due_date as string if it's a date object
            if hasattr(due_date, 'strftime'):
                due_date_str = due_date.strftime("%Y-%m-%d")
            else:
                due_date_str = str(due_date)
            
            new_chore = {
                "name": name,
                "due_date": due_date_str,
                "frequency": frequency,
                "description": description,
                "assigned_to": assigned_to,
                "chore_type": chore_type,
                "max_days": max_days,
                "adaptive_window": adaptive_window,
                "last_completed": None,
            }
            
            # Add to storage
            hass.data[DOMAIN]["chores"].append(new_chore)
            _save_chores(hass)
            
            # Create sensor - reload the platform to pick up new entities
            try:
                await hass.config_entries.async_reload(entry.entry_id)
            except Exception as e:
                _LOGGER.warning("Failed to reload platform for new chore '%s': %s", name, e)
            
            _LOGGER.info("Added chore: %s", name)
            
        except Exception as e:
            _LOGGER.error("Error adding chore: %s", e)
            raise
        try:
            name = call.data[CONF_CHORE_NAME]
            
            # Check if chore exists
            chore_exists = any(chore["name"] == name for chore in hass.data[DOMAIN]["chores"])
            if not chore_exists:
                _LOGGER.warning("Chore '%s' not found for removal", name)
                return
            
            # Remove from storage
            hass.data[DOMAIN]["chores"] = [
                chore for chore in hass.data[DOMAIN]["chores"]
                if chore["name"] != name
            ]
            _save_chores(hass)
            
            _LOGGER.info("Removed chore: %s", name)
            
        except Exception as e:
            _LOGGER.error("Error removing chore: %s", e)
            raise

    async def remove_chore(call: ServiceCall) -> None:
        """Remove an existing chore."""
        try:
            name = call.data[CONF_CHORE_NAME]

            # Check if chore exists
            chore_exists = any(chore["name"] == name for chore in hass.data[DOMAIN]["chores"])
            if not chore_exists:
                _LOGGER.warning("Chore '%s' not found for removal", name)
                return

            # Remove from storage
            hass.data[DOMAIN]["chores"] = [
                chore for chore in hass.data[DOMAIN]["chores"]
                if chore["name"] != name
            ]
            _save_chores(hass)

            _LOGGER.info("Removed chore: %s", name)

        except Exception as e:
            _LOGGER.error("Error removing chore: %s", e)
            raise
    
    async def update_chore(call: ServiceCall) -> None:
        """Update an existing chore."""
        try:
            name = call.data[CONF_CHORE_NAME]
            
            # Find chore
            chore = None
            for c in hass.data[DOMAIN]["chores"]:
                if c["name"] == name:
                    chore = c
                    break
            
            if not chore:
                _LOGGER.error("Chore '%s' not found for update", name)
                return
            
            # Update fields
            if CONF_DUE_DATE in call.data:
                due_date = call.data[CONF_DUE_DATE]
                if hasattr(due_date, 'strftime'):
                    chore["due_date"] = due_date.strftime("%Y-%m-%d")
                else:
                    chore["due_date"] = str(due_date)
            if CONF_FREQUENCY in call.data:
                chore["frequency"] = call.data[CONF_FREQUENCY]
            if CONF_DESCRIPTION in call.data:
                chore["description"] = call.data[CONF_DESCRIPTION]
            if CONF_ASSIGNED_TO in call.data:
                chore["assigned_to"] = call.data[CONF_ASSIGNED_TO]
            if CONF_CHORE_TYPE in call.data:
                chore["chore_type"] = call.data[CONF_CHORE_TYPE]
            if CONF_MAX_DAYS in call.data:
                chore["max_days"] = call.data[CONF_MAX_DAYS]
            if CONF_ADAPTIVE_WINDOW in call.data:
                chore["adaptive_window"] = call.data[CONF_ADAPTIVE_WINDOW]
            
            _save_chores(hass)
            _LOGGER.info("Updated chore: %s", name)
            
        except Exception as e:
            _LOGGER.error("Error updating chore: %s", e)
            raise

    async def complete_chore(call: ServiceCall) -> None:
        """Mark a chore as completed and update due date."""
        try:
            name = call.data[CONF_CHORE_NAME]
            
            # Find chore
            chore = None
            for c in hass.data[DOMAIN]["chores"]:
                if c["name"] == name:
                    chore = c
                    break
            
            if not chore:
                _LOGGER.error("Chore '%s' not found for completion", name)
                return
            
            now = datetime.now()
            chore["last_completed"] = now.strftime("%Y-%m-%d")
            
            if chore["chore_type"] == CHORE_TYPE_ADAPTIVE:
                # For adaptive chores, calculate new due date based on completion time
                try:
                    current_due = datetime.strptime(chore["due_date"], "%Y-%m-%d")
                    days_since_due = (now - current_due).days
                    
                    if days_since_due <= 0:
                        # Completed on time or early - use adaptive window
                        new_due_date = now + timedelta(days=chore["adaptive_window"])
                    else:
                        # Completed late - extend the window
                        new_due_date = now + timedelta(days=chore["max_days"])
                    
                    chore["due_date"] = new_due_date.strftime("%Y-%m-%d")
                except ValueError as e:
                    _LOGGER.error("Error parsing due date for chore '%s': %s", name, e)
                    return
            else:
                # For fixed chores, use frequency to calculate next due date
                try:
                    current_due = datetime.strptime(chore["due_date"], "%Y-%m-%d")
                    
                    if chore["frequency"] == "daily":
                        new_due_date = current_due + timedelta(days=1)
                    elif chore["frequency"] == "weekly":
                        new_due_date = current_due + timedelta(weeks=1)
                    elif chore["frequency"] == "biweekly":
                        new_due_date = current_due + timedelta(weeks=2)
                    elif chore["frequency"] == "monthly":
                        new_due_date = current_due + timedelta(days=30)
                    elif chore["frequency"] == "quarterly":
                        new_due_date = current_due + timedelta(days=90)
                    elif chore["frequency"] == "yearly":
                        new_due_date = current_due + timedelta(days=365)
                    else:
                        new_due_date = current_due + timedelta(weeks=1)
                    
                    chore["due_date"] = new_due_date.strftime("%Y-%m-%d")
                except ValueError as e:
                    _LOGGER.error("Error parsing due date for chore '%s': %s", name, e)
                    return
            
            _save_chores(hass)
            _LOGGER.info("Completed chore: %s", name)
            
        except Exception as e:
            _LOGGER.error("Error completing chore: %s", e)
            raise
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CHORE,
        add_chore,
        schema=vol.Schema({
            vol.Required(CONF_CHORE_NAME): cv.string,
            vol.Required(CONF_DUE_DATE): cv.date,
            vol.Optional(CONF_FREQUENCY, default=DEFAULT_FREQUENCY): cv.string,
            vol.Optional(CONF_DESCRIPTION, default=DEFAULT_DESCRIPTION): cv.string,
            vol.Optional(CONF_ASSIGNED_TO, default=DEFAULT_ASSIGNED_TO): cv.string,
            vol.Optional(CONF_CHORE_TYPE, default=DEFAULT_CHORE_TYPE): vol.In([CHORE_TYPE_FIXED, CHORE_TYPE_ADAPTIVE]),
            vol.Optional(CONF_MAX_DAYS, default=DEFAULT_MAX_DAYS): vol.Range(min=1, max=30),
            vol.Optional(CONF_ADAPTIVE_WINDOW, default=DEFAULT_ADAPTIVE_WINDOW): vol.Range(min=1, max=30),
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_CHORE,
        remove_chore,
        schema=vol.Schema({
            vol.Required(CONF_CHORE_NAME): cv.string,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_CHORE,
        update_chore,
        schema=vol.Schema({
            vol.Required(CONF_CHORE_NAME): cv.string,
            vol.Optional(CONF_DUE_DATE): cv.date,
            vol.Optional(CONF_FREQUENCY): cv.string,
            vol.Optional(CONF_DESCRIPTION): cv.string,
            vol.Optional(CONF_ASSIGNED_TO): cv.string,
            vol.Optional(CONF_CHORE_TYPE): vol.In([CHORE_TYPE_FIXED, CHORE_TYPE_ADAPTIVE]),
            vol.Optional(CONF_MAX_DAYS): vol.Range(min=1, max=30),
            vol.Optional(CONF_ADAPTIVE_WINDOW): vol.Range(min=1, max=30),
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_CHORE,
        complete_chore,
        schema=vol.Schema({
            vol.Required(CONF_CHORE_NAME): cv.string,
        }),
    )

def _save_chores(hass: HomeAssistant) -> None:
    """Save chores to YAML file."""
    try:
        chore_file = hass.data[DOMAIN]["chore_file"]
        with open(chore_file, "w", encoding="utf-8") as file:
            yaml.dump(
                hass.data[DOMAIN]["chores"], 
                file, 
                default_flow_style=False,
                allow_unicode=True
            )
    except Exception as e:
        _LOGGER.error("Error saving chores: %s", e)
        raise
