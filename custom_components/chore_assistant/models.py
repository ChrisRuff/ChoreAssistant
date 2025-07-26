"""Data models and validation schemas for Chore Assistant."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import voluptuous as vol
from homeassistant.util import dt as dt_util

# Validation schemas
CHORE_ID_SCHEMA = vol.Schema({
    vol.Required("id"): str,
})

CHORE_NAME_SCHEMA = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1, max=100)),
})

CHORE_INTERVAL_SCHEMA = vol.Schema({
    vol.Optional("interval_days", default=7): vol.All(int, vol.Range(min=1, max=365)),
})

CHORE_DUE_DATE_SCHEMA = vol.Schema({
    vol.Optional("due_date"): vol.Any(
        None,
        vol.Datetime(format="%Y-%m-%d")
    ),
})

CHORE_ASSIGNED_SCHEMA = vol.Schema({
    vol.Optional("assigned_to", default=""): vol.All(str, vol.Length(max=50)),
})

CHORE_METADATA_SCHEMA = vol.Schema({
    vol.Optional("priority", default="medium"): vol.In(["low", "medium", "high"]),
    vol.Optional("category", default="general"): vol.All(str, vol.Length(max=50)),
    vol.Optional("estimated_duration", default=30): vol.All(int, vol.Range(min=1, max=480)),
})

CHORE_CREATE_SCHEMA = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1, max=100)),
    vol.Optional("interval_days", default=7): vol.All(int, vol.Range(min=1, max=365)),
    vol.Optional("due_date"): vol.Any(
        None,
        vol.Datetime(format="%Y-%m-%d")
    ),
    vol.Optional("assigned_to", default=""): vol.All(str, vol.Length(max=50)),
    vol.Optional("priority", default="medium"): vol.In(["low", "medium", "high"]),
    vol.Optional("category", default="general"): vol.All(str, vol.Length(max=50)),
    vol.Optional("estimated_duration", default=30): vol.All(int, vol.Range(min=1, max=480)),
})

CHORE_UPDATE_SCHEMA = vol.Schema({
    vol.Optional("name"): vol.All(str, vol.Length(min=1, max=100)),
    vol.Optional("interval_days"): vol.All(int, vol.Range(min=1, max=365)),
    vol.Optional("due_date"): vol.Any(
        None,
        vol.Datetime(format="%Y-%m-%d")
    ),
    vol.Optional("assigned_to"): vol.All(str, vol.Length(max=50)),
    vol.Optional("priority"): vol.In(["low", "medium", "high"]),
    vol.Optional("category"): vol.All(str, vol.Length(max=50)),
    vol.Optional("estimated_duration"): vol.All(int, vol.Range(min=1, max=480)),
})

@dataclass
class ChoreHistoryEntry:
    """Represents a single entry in chore history."""
    timestamp: datetime
    action: str  # "created", "completed", "reset", "overdue", "updated"
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChoreHistoryEntry":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            action=data["action"],
            previous_state=data.get("previous_state"),
            new_state=data.get("new_state"),
            notes=data.get("notes"),
        )

@dataclass
class ChoreStatistics:
    """Statistics for a chore."""
    total_completions: int = 0
    average_completion_time: Optional[float] = None  # days
    last_completed: Optional[datetime] = None
    completion_streak: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "total_completions": self.total_completions,
            "average_completion_time": self.average_completion_time,
            "last_completed": self.last_completed.isoformat() if self.last_completed else None,
            "completion_streak": self.completion_streak,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChoreStatistics":
        """Create from dictionary."""
        last_completed = None
        if data.get("last_completed"):
            last_completed = datetime.fromisoformat(data["last_completed"])
        
        return cls(
            total_completions=data.get("total_completions", 0),
            average_completion_time=data.get("average_completion_time"),
            last_completed=last_completed,
            completion_streak=data.get("completion_streak", 0),
        )

@dataclass
class ChoreMetadata:
    """Metadata for a chore."""
    priority: str = "medium"  # low, medium, high
    category: str = "general"
    estimated_duration: int = 30  # minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "priority": self.priority,
            "category": self.category,
            "estimated_duration": self.estimated_duration,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChoreMetadata":
        """Create from dictionary."""
        return cls(
            priority=data.get("priority", "medium"),
            category=data.get("category", "general"),
            estimated_duration=data.get("estimated_duration", 30),
        )

@dataclass
class Chore:
    """Represents a chore with all its data."""
    id: str
    name: str
    state: str  # "pending", "completed", "overdue"
    created_date: datetime
    due_date: Optional[datetime] = None
    interval_days: int = 7
    assigned_to: str = ""
    metadata: ChoreMetadata = field(default_factory=ChoreMetadata)
    history: List[ChoreHistoryEntry] = field(default_factory=list)
    statistics: ChoreStatistics = field(default_factory=ChoreStatistics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "created_date": self.created_date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "interval_days": self.interval_days,
            "assigned_to": self.assigned_to,
            "metadata": self.metadata.to_dict(),
            "history": [entry.to_dict() for entry in self.history],
            "statistics": self.statistics.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chore":
        """Create from dictionary."""
        due_date = None
        if data.get("due_date"):
            due_date = datetime.fromisoformat(data["due_date"])
        
        return cls(
            id=data["id"],
            name=data["name"],
            state=data["state"],
            created_date=datetime.fromisoformat(data["created_date"]),
            due_date=due_date,
            interval_days=data.get("interval_days", 7),
            assigned_to=data.get("assigned_to", ""),
            metadata=ChoreMetadata.from_dict(data.get("metadata", {})),
            history=[ChoreHistoryEntry.from_dict(entry) for entry in data.get("history", [])],
            statistics=ChoreStatistics.from_dict(data.get("statistics", {})),
        )
    
    def add_history_entry(self, action: str, previous_state: Optional[str] = None, 
                         new_state: Optional[str] = None, notes: Optional[str] = None) -> None:
        """Add a history entry."""
        entry = ChoreHistoryEntry(
            timestamp=dt_util.utcnow(),
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            notes=notes,
        )
        self.history.append(entry)
    
    def update_statistics_on_completion(self) -> None:
        """Update statistics when chore is completed."""
        self.statistics.total_completions += 1
        self.statistics.last_completed = dt_util.utcnow()
        
        # Calculate average completion time
        if len(self.history) >= 2:
            completion_times = []
            for i in range(1, len(self.history)):
                if self.history[i].action == "completed":
                    # Find previous completion or creation
                    for j in range(i-1, -1, -1):
                        if self.history[j].action in ["created", "reset", "completed"]:
                            time_diff = (self.history[i].timestamp - self.history[j].timestamp).total_seconds() / 86400
                            completion_times.append(time_diff)
                            break
            
            if completion_times:
                self.statistics.average_completion_time = sum(completion_times) / len(completion_times)
        
        # Update completion streak
        if self.statistics.last_completed:
            days_since_last = (dt_util.utcnow() - self.statistics.last_completed).total_seconds() / 86400
            if days_since_last <= self.interval_days + 1:
                self.statistics.completion_streak += 1
            else:
                self.statistics.completion_streak = 1
    
    def is_overdue(self) -> bool:
        """Check if chore is overdue."""
        if self.state == "completed":
            return False
        
        if not self.due_date:
            return False
        
        return dt_util.utcnow() > self.due_date
    
    def get_next_due_date(self) -> Optional[datetime]:
        """Calculate next due date for recurring chores."""
        if self.state != "completed":
            return self.due_date
        
        if not self.statistics.last_completed:
            return self.due_date
        
        return self.statistics.last_completed + timedelta(days=self.interval_days)
    
    def validate_state_transition(self, new_state: str) -> bool:
        """Validate if state transition is allowed."""
        valid_transitions = {
            "pending": ["completed", "overdue"],
            "completed": ["pending"],
            "overdue": ["completed", "pending"],
        }
        
        return new_state in valid_transitions.get(self.state, [])