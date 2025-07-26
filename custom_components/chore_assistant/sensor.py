"""Sensor platform for the Chore Assistant."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, STATE_COMPLETED, STATE_OVERDUE, STATE_PENDING
from .storage import ChoreStorage
from .models import Chore

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the Chore Assistant sensor platform."""
    _LOGGER.info("Setting up Chore Assistant sensor platform")
    
    storage: ChoreStorage = hass.data[DOMAIN]["storage"]
    
    # Create sensor entities for each existing chore
    chores = await storage.async_get_all_chores()
    entities = []
    
    for chore in chores:
        _LOGGER.info("Creating sensor for chore: %s", chore.name)
        entities.append(ChoreSensor(hass, chore))
    
    if entities:
        _LOGGER.info("Adding %d chore sensors", len(entities))
        async_add_entities(entities)
    else:
        _LOGGER.info("No chores to create sensors for")

    # Set up listener for chore updates
    async def handle_chore_update(event):
        """Handle chore update events to create/update entities."""
        _LOGGER.info("Handling chore update event")
        
        # Get current chores
        current_chores = await storage.async_get_all_chores()
        current_chore_ids = {chore.id for chore in current_chores}
        
        # Get existing entity IDs
        existing_entity_ids = {entity.unique_id for entity in hass.data[DOMAIN].get("entities", set())}
        
        # Find new chores
        new_chores = [chore for chore in current_chores
                     if f"chore_assistant_{chore.id}" not in existing_entity_ids]
        
        if new_chores:
            new_entities = [ChoreSensor(hass, chore) for chore in new_chores]
            _LOGGER.info("Adding %d new chore sensors", len(new_entities))
            async_add_entities(new_entities)
    
    # Register event listener
    hass.bus.async_listen(f"{DOMAIN}_updated", handle_chore_update)


class ChoreSensor(SensorEntity):
    """Representation of a Chore sensor."""

    def __init__(self, hass: HomeAssistant, chore: Chore) -> None:
        """Initialize the Chore sensor."""
        self.hass = hass
        self._chore = chore
        self._storage: ChoreStorage = hass.data[DOMAIN]["storage"]
        
        # Set entity properties
        self._attr_unique_id = f"chore_assistant_{chore.id}"
        self._attr_name = chore.name
        self._attr_icon = self._get_icon()
        
        # Track entity in hass.data
        if "entities" not in hass.data[DOMAIN]:
            hass.data[DOMAIN]["entities"] = set()
        hass.data[DOMAIN]["entities"].add(self)

    def _get_icon(self) -> str:
        """Return the icon based on chore state."""
        if self._chore.state == STATE_COMPLETED:
            return "mdi:check-circle"
        elif self._chore.state == STATE_OVERDUE:
            return "mdi:alert-circle"
        else:
            return "mdi:checkbox-blank-circle-outline"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._chore.state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "id": self._chore.id,
            "name": self._chore.name,
            "state": self._chore.state,
            "created_date": self._chore.created_date.isoformat() if self._chore.created_date else None,
            "due_date": self._chore.due_date.isoformat() if self._chore.due_date else None,
            "interval_days": self._chore.interval_days,
            "assigned_to": self._chore.assigned_to,
            "priority": self._chore.metadata.priority,
            "category": self._chore.metadata.category,
            "estimated_duration": self._chore.metadata.estimated_duration,
            "history_count": len(self._chore.history),
            "statistics": {
                "total_completions": self._chore.statistics.total_completions,
                "last_completed": self._chore.statistics.last_completed.isoformat() if self._chore.statistics.last_completed else None,
                "average_completion_time": self._chore.statistics.average_completion_time,
                "completion_streak": self._chore.statistics.completion_streak,
            }
        }
        
        # Add recent history
        if self._chore.history:
            recent_history = self._chore.history[-5:]  # Last 5 entries
            attrs["recent_history"] = [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "action": entry.action,
                    "previous_state": entry.previous_state,
                    "new_state": entry.new_state,
                    "notes": entry.notes,
                }
                for entry in recent_history
            ]
        
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        try:
            # Refresh chore data from storage
            updated_chore = await self._storage.async_get_chore(self._chore.id)
            if updated_chore:
                self._chore = updated_chore
                self._attr_icon = self._get_icon()
            else:
                # Chore was removed
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Error updating chore sensor %s: %s", self._chore.id, err)
