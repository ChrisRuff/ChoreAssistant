"""Persistent storage for Chore Assistant integration."""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .models import Chore
from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    BACKUP_FILENAME_PREFIX,
    BACKUP_EXTENSION,
    CONF_BACKUP_RETENTION_DAYS,
)

_LOGGER = logging.getLogger(__name__)


class ChoreStorage:
    """Manages persistent storage for chores."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the storage manager."""
        self._hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: Dict[str, Any] = {}
        self._chores: Dict[str, Chore] = {}
        self._lock = asyncio.Lock()
    
    async def async_load(self) -> None:
        """Load data from storage."""
        async with self._lock:
            try:
                stored_data = await self._store.async_load()
                if stored_data is None:
                    _LOGGER.info("No stored data found, initializing empty storage")
                    self._data = {"chores": {}, "metadata": {"version": STORAGE_VERSION}}
                    self._chores = {}
                else:
                    self._data = stored_data
                    self._chores = {}
                    
                    # Migrate data if needed
                    await self._migrate_data()
                    
                    # Load chores
                    for chore_id, chore_data in self._data.get("chores", {}).items():
                        try:
                            chore = Chore.from_dict(chore_data)
                            self._chores[chore_id] = chore
                        except Exception as err:
                            _LOGGER.error("Error loading chore %s: %s", chore_id, err)
                
                _LOGGER.info("Loaded %d chores from storage", len(self._chores))
                
            except Exception as err:
                _LOGGER.error("Error loading storage: %s", err)
                # Initialize empty storage on error
                self._data = {"chores": {}, "metadata": {"version": STORAGE_VERSION}}
                self._chores = {}
    
    async def _migrate_data(self) -> None:
        """Migrate data from older versions."""
        current_version = self._data.get("metadata", {}).get("version", 1)
        
        if current_version < STORAGE_VERSION:
            _LOGGER.info("Migrating storage from version %d to %d", current_version, STORAGE_VERSION)
            
            # Add migration logic here as needed
            self._data["metadata"]["version"] = STORAGE_VERSION
            
            # Save migrated data
            await self._store.async_save(self._data)
    
    async def async_save(self) -> None:
        """Save data to storage."""
        async with self._lock:
            try:
                # Update data structure
                self._data["chores"] = {
                    chore_id: chore.to_dict()
                    for chore_id, chore in self._chores.items()
                }
                
                await self._store.async_save(self._data)
                _LOGGER.debug("Saved %d chores to storage", len(self._chores))
                
            except Exception as err:
                _LOGGER.error("Error saving storage: %s", err)
                raise
    
    async def async_add_chore(self, chore: Chore) -> None:
        """Add a new chore."""
        async with self._lock:
            if chore.id in self._chores:
                raise ValueError(f"Chore with ID {chore.id} already exists")
            
            self._chores[chore.id] = chore
            await self.async_save()
    
    async def async_get_chore(self, chore_id: str) -> Optional[Chore]:
        """Get a chore by ID."""
        return self._chores.get(chore_id)
    
    async def async_get_all_chores(self) -> List[Chore]:
        """Get all chores."""
        return list(self._chores.values())
    
    async def async_update_chore(self, chore: Chore) -> None:
        """Update an existing chore."""
        async with self._lock:
            if chore.id not in self._chores:
                raise ValueError(f"Chore with ID {chore.id} not found")
            
            self._chores[chore.id] = chore
            await self.async_save()
    
    async def async_remove_chore(self, chore_id: str) -> bool:
        """Remove a chore."""
        async with self._lock:
            if chore_id not in self._chores:
                return False
            
            del self._chores[chore_id]
            await self.async_save()
            return True
    
    async def async_create_backup(self) -> str:
        """Create a backup of the current data."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{BACKUP_FILENAME_PREFIX}_{timestamp}{BACKUP_EXTENSION}"
            backup_path = os.path.join(self._hass.config.config_dir, backup_filename)
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "version": STORAGE_VERSION,
                "chores": {
                    chore_id: chore.to_dict()
                    for chore_id, chore in self._chores.items()
                }
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            _LOGGER.info("Created backup: %s", backup_filename)
            return backup_filename
            
        except Exception as err:
            _LOGGER.error("Error creating backup: %s", err)
            raise
    
    async def async_restore_backup(self, backup_filename: str) -> bool:
        """Restore from a backup file."""
        try:
            backup_path = os.path.join(self._hass.config.config_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                _LOGGER.error("Backup file not found: %s", backup_filename)
                return False
            
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            # Validate backup data
            if "chores" not in backup_data:
                _LOGGER.error("Invalid backup format")
                return False
            
            # Load chores from backup
            restored_chores = {}
            for chore_id, chore_data in backup_data["chores"].items():
                try:
                    chore = Chore.from_dict(chore_data)
                    restored_chores[chore_id] = chore
                except Exception as err:
                    _LOGGER.error("Error restoring chore %s: %s", chore_id, err)
            
            # Replace current data
            async with self._lock:
                self._chores = restored_chores
                await self.async_save()
            
            _LOGGER.info("Restored %d chores from backup: %s", len(restored_chores), backup_filename)
            return True
            
        except Exception as err:
            _LOGGER.error("Error restoring backup: %s", err)
            return False
    
    async def async_cleanup_old_backups(self, retention_days: int = CONF_BACKUP_RETENTION_DAYS) -> int:
        """Clean up old backup files."""
        try:
            backup_dir = self._hass.config.config_dir
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            removed_count = 0
            for filename in os.listdir(backup_dir):
                if filename.startswith(BACKUP_FILENAME_PREFIX) and filename.endswith(BACKUP_EXTENSION):
                    file_path = os.path.join(backup_dir, filename)
                    
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            removed_count += 1
                    except Exception as err:
                        _LOGGER.error("Error processing backup file %s: %s", filename, err)
            
            if removed_count > 0:
                _LOGGER.info("Cleaned up %d old backup files", removed_count)
            
            return removed_count
            
        except Exception as err:
            _LOGGER.error("Error cleaning up backups: %s", err)
            return 0
    
    async def async_get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "total_chores": len(self._chores),
            "storage_version": self._data.get("metadata", {}).get("version", STORAGE_VERSION),
            "last_updated": datetime.now().isoformat(),
        }