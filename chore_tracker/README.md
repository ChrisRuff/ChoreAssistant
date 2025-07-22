# Chore Tracker Integration for Home Assistant

A comprehensive chore tracking system that supports both fixed-interval and adaptive scheduling for household tasks.

## Overview

This integration provides a flexible chore management system with two distinct chore types:

1. **Fixed Chores**: Traditional recurring chores with set intervals (daily, weekly, monthly, etc.)
2. **Adaptive Chores**: Smart chores that adjust their next due date based on when they're completed

## Chore Types

### Fixed Chores
- **Description**: Chores with predetermined schedules
- **Use Case**: Regular cleaning, trash day, bill payments
- **Behavior**: Due dates follow a fixed pattern regardless of completion time
- **Example**: "Clean Kitchen" every Monday, "Pay Bills" on the 1st of each month

### Adaptive Chores
- **Description**: Chores that must be completed within a maximum timeframe but adapt their next due date
- **Use Case**: Tasks that can be flexible but have deadlines
- **Behavior**: 
  - Must be completed within `max_days` (default: 3 days)
  - If completed early (within `adaptive_window`), next due date is set to `adaptive_window` days from completion
  - If completed late, next due date is set to `max_days` from completion
- **Example**: "Water Plants" - must be done within 3 days, but if done in 2 days, next due is 3 days from completion

## Services

### chore_tracker.add_chore
Add a new chore to track.

**Fields:**
- `name` (required): Chore name
- `due_date` (required): Initial due date (YYYY-MM-DD)
- `frequency`: For fixed chores - daily, weekly, biweekly, monthly, quarterly, yearly (default: weekly)
- `chore_type`: "fixed" or "adaptive" (default: fixed)
- `max_days`: Maximum days to complete (adaptive type, default: 3)
- `adaptive_window`: Days until next due when completed early (adaptive type, default: 3)
- `description`: Additional details
- `assigned_to`: Person responsible (default: household)

### chore_tracker.remove_chore
Remove a chore from tracking.

**Fields:**
- `name` (required): Chore name to remove

### chore_tracker.update_chore
Update an existing chore's properties.

**Fields:**
- `name` (required): Chore name to update
- `due_date`: New due date
- `frequency`: New frequency (fixed type)
- `chore_type`: Change chore type
- `max_days`: New max days (adaptive type)
- `adaptive_window`: New adaptive window (adaptive type)
- `description`: New description
- `assigned_to`: New assignee

### chore_tracker.complete_chore
Mark a chore as completed and automatically update its next due date based on chore type.

**Fields:**
- `name` (required): Chore name to complete

## Usage Examples

### Adding a Fixed Chore
```yaml
service: chore_tracker.add_chore
data:
  name: "Clean Kitchen"
  due_date: "2024-07-29"
  frequency: "weekly"
  chore_type: "fixed"
  description: "Clean all surfaces and appliances"
  assigned_to: "household"
```

### Adding an Adaptive Chore
```yaml
service: chore_tracker.add_chore
data:
  name: "Water Plants"
  due_date: "2024-07-25"
  chore_type: "adaptive"
  max_days: 3
  adaptive_window: 3
  description: "Water all indoor plants"
  assigned_to: "John"
```

### Completing a Chore
```yaml
service: chore_tracker.complete_chore
data:
  name: "Water Plants"
```

## Sensor Attributes

Each chore creates a sensor with these attributes:
- `description`: Chore description
- `frequency`: For fixed chores
- `assigned_to`: Person responsible
- `due_date`: Current due date
- `chore_type`: "fixed" or "adaptive"
- `max_days`: Maximum completion window (adaptive)
- `adaptive_window`: Early completion window (adaptive)
- `last_completed`: Date last completed
- `days_until_due`: Days until due

## State Values

### Fixed Chores
- `pending`: Chore is scheduled but not due yet
- `due`: Chore is due within 1 day
- `overdue`: Chore is past due

### Adaptive Chores
- `scheduled`: Chore is scheduled beyond the max_days window
- `due_in_X_days`: Chore is due in X days (where X is 1-3)
- `due_today`: Chore is due today
- `due_tomorrow`: Chore is due tomorrow
- `overdue`: Chore is past due

## Migration

Existing chores without a `chore_type` will default to "fixed" type, maintaining backward compatibility.
