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
    chore_file = hass.config.path("custom_components", "chore_tracker", "chores.yaml")
    
    # Load existing chores
    chores = []
    if os.path.exists(chore_file):
        try:
            with open(chore_file, "r") as file:
                chores = yaml.safe_load(file) or []
        except Exception as e:
            _LOGGER.error("Error loading chores: %s", e)
            chores = []
    
    # Store chores in hass data
    hass.data[DOMAIN]["chores"] = chores
    hass.data[DOMAIN]["chore_file"] = chore_file
    
    # Register services
    await _register_services(hass)
    
    # Create sensors for existing chores
    for chore in chores:
        hass.async_create_task(
            hass.helpers.entity_platform.async_add_entities([ChoreSensor(chore)])
        )
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True

async def _register_services(hass: HomeAssistant) -> None:
    """Register services for managing chores."""
    
    async def add_chore(call: ServiceCall) -> None:
        """Add a new chore."""
        name = call.data[CONF_CHORE_NAME]
        due_date = call.data[CONF_DUE_DATE]
        frequency = call.data.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
        description = call.data.get(CONF_DESCRIPTION, DEFAULT_DESCRIPTION)
        assigned_to = call.data.get(CONF_ASSIGNED_TO, DEFAULT_ASSIGNED_TO)
        chore_type = call.data.get(CONF_CHORE_TYPE, DEFAULT_CHORE_TYPE)
        max_days = call.data.get(CONF_MAX_DAYS, DEFAULT_MAX_DAYS)
        adaptive_window = call.data.get(CONF_ADAPTIVE_WINDOW, DEFAULT_ADAPTIVE_WINDOW)
        
        new_chore = {
            "name": name,
            "due_date": due_date,
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
        
        # Create sensor
        hass.async_create_task(
            hass.helpers.entity_platform.async_add_entities([ChoreSensor(new_chore)])
        )
        
        _LOGGER.info("Added chore: %s", name)
    
    async def remove_chore(call: ServiceCall) -> None:
        """Remove a chore."""
        name = call.data[CONF_CHORE_NAME]
        
        # Remove from storage
        hass.data[DOMAIN]["chores"] = [
            chore for chore in hass.data[DOMAIN]["chores"]
            if chore["name"] != name
        ]
        _save_chores(hass)
        
        _LOGGER.info("Removed chore: %s", name)
    
    async def update_chore(call: ServiceCall) -> None:
        """Update an existing chore."""
        name = call.data[CONF_CHORE_NAME]
        
        # Find and update chore
        for chore in hass.data[DOMAIN]["chores"]:
            if chore["name"] == name:
                if CONF_DUE_DATE in call.data:
                    chore["due_date"] = call.data[CONF_DUE_DATE]
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
                break
        
        _save_chores(hass)
        _LOGGER.info("Updated chore: %s", name)

    async def complete_chore(call: ServiceCall) -> None:
        """Mark a chore as completed and update due date."""
        name = call.data[CONF_CHORE_NAME]
        
        # Find and update chore
        for chore in hass.data[DOMAIN]["chores"]:
            if chore["name"] == name:
                now = datetime.now()
                chore["last_completed"] = now.strftime("%Y-%m-%d")
                
                if chore["chore_type"] == CHORE_TYPE_ADAPTIVE:
                    # For adaptive chores, calculate new due date based on completion time
                    days_since_due = (now - datetime.strptime(chore["due_date"], "%Y-%m-%d")).days
                    
                    if days_since_due <= 0:
                        # Completed on time or early - use adaptive window
                        new_due_date = now + timedelta(days=chore["adaptive_window"])
                    else:
                        # Completed late - extend the window
                        new_due_date = now + timedelta(days=chore["max_days"])
                    
                    chore["due_date"] = new_due_date.strftime("%Y-%m-%d")
                else:
                    # For fixed chores, use frequency to calculate next due date
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
                
                break
        
        _save_chores(hass)
        _LOGGER.info("Completed chore: %s", name)
    
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
        with open(chore_file, "w") as file:
            yaml.dump(hass.data[DOMAIN]["chores"], file, default_flow_style=False)
    except Exception as e:
        _LOGGER.error("Error saving chores: %s", e)

class ChoreSensor(SensorEntity):
    """Sensor to track chore states."""

    def __init__(self, chore_data):
        """Initialize the sensor."""
        self._name = chore_data["name"]
        self._due_date = datetime.strptime(chore_data["due_date"], "%Y-%m-%d")
        self._frequency = chore_data.get("frequency", DEFAULT_FREQUENCY)
        self._description = chore_data.get("description", DEFAULT_DESCRIPTION)
        self._assigned_to = chore_data.get("assigned_to", DEFAULT_ASSIGNED_TO)
        self._chore_type = chore_data.get("chore_type", DEFAULT_CHORE_TYPE)
        self._max_days = chore_data.get("max_days", DEFAULT_MAX_DAYS)
        self._adaptive_window = chore_data.get("adaptive_window", DEFAULT_ADAPTIVE_WINDOW)
        self._last_completed = chore_data.get("last_completed")
        self._state = STATE_UNKNOWN
        self._icon = "mdi:check-circle-outline"
        self._unit = "days"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Chore {self._name}"

    @property
    def state(self):
        """Return the current state of the chore."""
        now = datetime.now()
        if self._state == STATE_UNKNOWN:
            self._state = self._calculate_state(now)
        
        return self._state

    @property
    def icon(self):
        """Return the icon for the sensor."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "description": self._description,
            "frequency": self._frequency,
            "assigned_to": self._assigned_to,
            "due_date": self._due_date.strftime("%Y-%m-%d"),
            "chore_type": self._chore_type,
            "max_days": self._max_days,
            "adaptive_window": self._adaptive_window,
            "last_completed": self._last_completed,
            "days_until_due": (self._due_date - datetime.now()).days,
        }

    def _calculate_state(self, now):
        """Calculate the state of the chore."""
        days_until_due = (self._due_date - now).days
        
        if self._chore_type == CHORE_TYPE_ADAPTIVE:
            # For adaptive chores, show more detailed states
            if days_until_due < 0:
                return "overdue"
            elif days_until_due == 0:
                return "due_today"
            elif days_until_due == 1:
                return "due_tomorrow"
            elif days_until_due <= self._max_days:
                return f"due_in_{days_until_due}_days"
            else:
                return "scheduled"
        else:
            # For fixed chores, use simpler states
            if days_until_due <= 1:
                return "due"
            elif days_until_due < 0:
                return "overdue"
            else:
                return "pending"

    async def async_set_state(self, state):
        """Set the state of the chore."""
        self._state = state
        self.async_schedule_update_ha_state()

    async def async_added_to_hass(self):
        """Handle when the entity is added to Home Assistant."""
        self.async_update_ha_state()
