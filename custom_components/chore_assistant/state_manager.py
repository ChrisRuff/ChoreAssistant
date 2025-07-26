"""State management for Chore Assistant integration."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .models import Chore, ChoreHistoryEntry
from .storage import ChoreStorage
from .const import (
    STATE_PENDING,
    STATE_COMPLETED,
    STATE_OVERDUE,
    EVENT_CHORE_COMPLETED,
    EVENT_CHORE_OVERDUE,
)

_LOGGER = logging.getLogger(__name__)


class ChoreStateManager:
    """Manages chore state transitions and validation."""
    
    def __init__(self, storage: ChoreStorage):
        """Initialize the state manager."""
        self._storage = storage
        self._state_transitions = {
            STATE_PENDING: [STATE_COMPLETED, STATE_OVERDUE],
            STATE_COMPLETED: [STATE_PENDING],
            STATE_OVERDUE: [STATE_COMPLETED, STATE_PENDING],
        }
    
    async def transition_state(
        self,
        chore_id: str,
        new_state: str,
        reason: Optional[str] = None,
        completed_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Transition a chore to a new state."""
        try:
            chore = await self._storage.get_chore(chore_id)
            if not chore:
                _LOGGER.error("Chore %s not found", chore_id)
                return False
            
            current_state = chore.state
            if new_state == current_state:
                _LOGGER.debug("Chore %s already in state %s", chore_id, new_state)
                return True
            
            # Validate state transition
            if not self._is_valid_transition(current_state, new_state):
                _LOGGER.error(
                    "Invalid state transition from %s to %s for chore %s",
                    current_state,
                    new_state,
                    chore_id,
                )
                return False
            
            # Update chore state
            old_state = chore.state
            chore.state = new_state
            
            # Update timestamps based on new state
            if new_state == STATE_COMPLETED:
                chore.completed_date = datetime.now().date()
                chore.last_completed = datetime.now()
                if completed_by:
                    chore.completed_by = completed_by
            elif new_state == STATE_PENDING and old_state == STATE_COMPLETED:
                # Reset from completed to pending
                chore.completed_date = None
                chore.completed_by = None
            
            # Add history entry
            history_entry = ChoreHistoryEntry(
                timestamp=datetime.now(),
                action=f"state_change_{new_state}",
                old_state=old_state,
                new_state=new_state,
                reason=reason,
                notes=notes,
            )
            chore.history.append(history_entry)
            
            # Update statistics
            await self._update_statistics(chore, new_state, old_state)
            
            # Save changes
            await self._storage.update_chore(chore)
            
            # Fire events
            await self._fire_state_change_event(chore, old_state, new_state, reason)
            
            return True
            
        except Exception as err:
            _LOGGER.error("Error transitioning chore %s to %s: %s", chore_id, new_state, err)
            return False
    
    def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Check if a state transition is valid."""
        valid_transitions = self._state_transitions.get(current_state, [])
        return new_state in valid_transitions
    
    async def _update_statistics(
        self,
        chore: Chore,
        new_state: str,
        old_state: str,
    ) -> None:
        """Update chore statistics based on state change."""
        try:
            if new_state == STATE_COMPLETED:
                chore.statistics.total_completions += 1
                chore.statistics.last_completed = datetime.now()
                
                # Calculate completion time
                if chore.due_date:
                    days_overdue = (datetime.now().date() - chore.due_date).days
                    if days_overdue > 0:
                        chore.statistics.total_overdue_days += days_overdue
                        chore.statistics.overdue_completions += 1
                    else:
                        chore.statistics.on_time_completions += 1
            
            elif new_state == STATE_OVERDUE and old_state == STATE_PENDING:
                chore.statistics.total_overdue_count += 1
                
        except Exception as err:
            _LOGGER.error("Error updating statistics for chore %s: %s", chore.id, err)
    
    async def _fire_state_change_event(
        self,
        chore: Chore,
        old_state: str,
        new_state: str,
        reason: Optional[str] = None,
    ) -> None:
        """Fire Home Assistant event for state change."""
        try:
            event_data = {
                "chore_id": chore.id,
                "name": chore.name,
                "old_state": old_state,
                "new_state": new_state,
                "timestamp": datetime.now().isoformat(),
            }
            
            if reason:
                event_data["reason"] = reason
            
            # Fire generic state change event
            # Note: This will need to be called from the integration level with hass reference
            # The actual event firing will be handled by the integration
            
        except Exception as err:
            _LOGGER.error("Error preparing state change event: %s", err)
    
    async def check_overdue_chores(self) -> List[str]:
        """Check for overdue chores and update their state."""
        overdue_chores = []
        try:
            all_chores = await self._storage.get_all_chores()
            
            for chore in all_chores:
                if chore.state == STATE_PENDING and chore.due_date:
                    if datetime.now().date() > chore.due_date:
                        success = await self.transition_state(
                            chore.id,
                            STATE_OVERDUE,
                            reason="Automatically marked overdue",
                        )
                        if success:
                            overdue_chores.append(chore.id)
            
            if overdue_chores:
                _LOGGER.info("Marked %d chores as overdue", len(overdue_chores))
            
            return overdue_chores
            
        except Exception as err:
            _LOGGER.error("Error checking overdue chores: %s", err)
            return []
    
    async def reset_chore(
        self,
        chore_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Reset a chore to pending state."""
        return await self.transition_state(
            chore_id,
            STATE_PENDING,
            reason=reason or "Manually reset",
        )
    
    async def complete_chore(
        self,
        chore_id: str,
        completed_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Complete a chore."""
        return await self.transition_state(
            chore_id,
            STATE_COMPLETED,
            completed_by=completed_by,
            notes=notes,
        )
    
    async def get_chore_state(self, chore_id: str) -> Optional[str]:
        """Get the current state of a chore."""
        try:
            chore = await self._storage.get_chore(chore_id)
            return chore.state if chore else None
        except Exception as err:
            _LOGGER.error("Error getting state for chore %s: %s", chore_id, err)
            return None
    
    async def get_chore_statistics(self, chore_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a chore."""
        try:
            chore = await self._storage.get_chore(chore_id)
            if not chore:
                return None
            
            return {
                "total_completions": chore.statistics.total_completions,
                "on_time_completions": chore.statistics.on_time_completions,
                "overdue_completions": chore.statistics.overdue_completions,
                "total_overdue_days": chore.statistics.total_overdue_days,
                "total_overdue_count": chore.statistics.total_overdue_count,
                "last_completed": chore.statistics.last_completed.isoformat() if chore.statistics.last_completed else None,
                "average_completion_time": chore.statistics.average_completion_time,
            }
        except Exception as err:
            _LOGGER.error("Error getting statistics for chore %s: %s", chore_id, err)
            return None