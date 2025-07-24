"""Sensor platform for the Chore Assistant."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, STATE_COMPLETED, STATE_OVERDUE, STATE_PENDING

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Loading Chore Assistant sensor platform module")


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the Chore Assistant sensor platform."""
    _LOGGER.info("Setting up Chore Assistant sensor platform")
    
    # Store the add_entities callback for later use
    hass.data[DOMAIN]["add_entities"] = async_add_entities
    hass.data[DOMAIN]["existing_entities"] = set()
    
    # Create sensor entities for each existing chore
    chores = hass.data[DOMAIN]["chores"]
    entities = []
    
    for chore_name in chores:
        _LOGGER.info("Creating sensor for chore: %s", chore_name)
        entities.append(ChoreSensor(hass, chore_name))
        hass.data[DOMAIN]["existing_entities"].add(chore_name)
    
    if entities:
        _LOGGER.info("Adding %d chore sensors", len(entities))
        async_add_entities(entities)
    else:
        _LOGGER.info("No chores to create sensors for")

    # Listen for updates to create new entities
    async def handle_chore_update(event):
        """Handle chore update events to create new entities."""
        _LOGGER.info("Handling chore update event")
        current_chores = set(hass.data[DOMAIN]["chores"].keys())
        existing_entities = hass.data[DOMAIN]["existing_entities"]
        
        # Find new chores that don't have entities yet
        new_chores = current_chores - existing_entities
        
        if new_chores:
            new_entities = []
            for chore_name in new_chores:
                _LOGGER.info("Creating new sensor for chore: %s", chore_name)
                new_entities.append(ChoreSensor(hass, chore_name))
                existing_entities.add(chore_name)
            
            if new_entities:
                _LOGGER.info("Adding %d new chore sensors", len(new_entities))
                async_add_entities(new_entities)
    
    # Register event listener
    hass.bus.async_listen(f"{DOMAIN}_updated", handle_chore_update)


class ChoreSensor(SensorEntity):
    """Representation of a Chore sensor."""

    def __init__(self, hass: HomeAssistant, chore_name: str) -> None:
        """Initialize the Chore sensor."""
        self.hass = hass
        self.chore_name = chore_name
        self._state = None
        self._attrs = {}
        
        # Initialize state from chore data
        self._update_from_chore_data()
        
        # Set up automatic updates when chores change
        self._setup_update_listener()

    def _update_from_chore_data(self) -> None:
        """Update sensor state from chore data."""
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

    def _setup_update_listener(self) -> None:
        """Set up listener for chore updates."""
        async def handle_update(event):
            """Handle chore update events."""
            await self.async_update()
            self.async_schedule_update_ha_state()
        
        self.hass.bus.async_listen(f"{DOMAIN}_updated", handle_update)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.chore_name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"chore_assistant_{self.chore_name.lower().replace(' ', '_')}"

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
        self._update_from_chore_data()
