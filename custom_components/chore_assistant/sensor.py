"""Sensor platform for Chore Tracker integration."""
import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Chore Tracker sensors from a config entry."""
    chores = hass.data[DOMAIN].get("chores", [])
    
    entities = []
    for chore in chores:
        entities.append(ChoreSensor(chore))
    
    if entities:
        async_add_entities(entities)


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
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{DOMAIN}_{self._name.lower().replace(' ', '_')}"

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
