"""Sensor platform for the Chore Assistant."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, STATE_COMPLETED, STATE_OVERDUE, STATE_PENDING

_LOGGER = logging.getLogger(__name__)

# Keep track of existing entities to prevent duplicates
EXISTING_ENTITIES = set()


async def async_chore_updated(hass: HomeAssistant, async_add_entities: AddEntitiesCallback, event):
    """Handle chore updates."""
    # Create new sensors for any new chores
    chores = hass.data[DOMAIN]["chores"]
    
    new_entities = []
    for chore_name in chores:
        # Check if entity already exists
        unique_id = f"chore_assistant_{chore_name}"
        if unique_id not in EXISTING_ENTITIES:
            new_entities.append(ChoreSensor(hass, chore_name))
            EXISTING_ENTITIES.add(unique_id)
    
    if new_entities:
        async_add_entities(new_entities)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the Chore Assistant sensor platform."""
    # Create sensor entities for each chore
    chores = hass.data[DOMAIN]["chores"]
    entities = []
    
    for chore_name in chores:
        # Check if entity already exists
        unique_id = f"chore_assistant_{chore_name}"
        if unique_id not in EXISTING_ENTITIES:
            entities.append(ChoreSensor(hass, chore_name))
            EXISTING_ENTITIES.add(unique_id)
    
    if entities:
        async_add_entities(entities)
    
    # Set up listener for chore updates
    async def _async_chore_updated(event):
        await async_chore_updated(hass, async_add_entities, event)
    
    hass.bus.async_listen(f"{DOMAIN}_updated", _async_chore_updated)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Chore Assistant sensors from a config entry."""
    # This integration doesn't use config entries
    pass


class ChoreSensor(SensorEntity):
    """Representation of a Chore sensor."""

    def __init__(self, hass: HomeAssistant, chore_name: str) -> None:
        """Initialize the Chore sensor."""
        self.hass = hass
        self.chore_name = chore_name
        self._state = None
        self._attrs = {}

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.chore_name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"chore_assistant_{self.chore_name}"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._state == STATE_COMPLETED:
            return "mdi:check-circle"
        elif self._state == STATE_OVERDUE:
            return "mdi:alert-circle"
        else:
            return "mdi:checkbox-blank-circle-outline"

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        chores = self.hass.data[DOMAIN]["chores"]
        
        if self.chore_name in chores:
            chore_data = chores[self.chore_name]
            self._state = chore_data["state"]
            
            # Set attributes
            self._attrs = {}
            for key, value in chore_data.items():
                if key != "state":
                    self._attrs[key] = value
        else:
            # Chore was removed
            self._state = "removed"
