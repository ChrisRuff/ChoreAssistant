# Chore Assistant

A Home Assistant custom integration for tracking recurring chores with automatic reset functionality.

## Features

- **Recurring Chores**: Set up chores with intervals (in days) that automatically reset when due
- **Automatic State Management**: Chores automatically transition between pending, overdue, and completed states
- **Dynamic Entity Creation**: Sensor entities are created automatically when you add new chores
- **Rich Attributes**: Each chore sensor includes due date, interval, assigned person, and other metadata

## Installation

1. Copy the `custom_components/chore_assistant` folder to your Home Assistant `config/custom_components/` directory
2. Add `chore_assistant:` to your `configuration.yaml`
3. Restart Home Assistant

## Usage

### Adding a Chore

Use the `chore_assistant.add_chore` service:

```yaml
service: chore_assistant.add_chore
data:
  name: "Take out trash"
  due_date: "2025-07-25"
  interval: 7  # Reset every 7 days
  assigned_to: "John"  # Optional
```

### Completing a Chore

Use the `chore_assistant.complete_chore` service:

```yaml
service: chore_assistant.complete_chore
data:
  name: "sensor.chore_assistant_take_out_trash"
```

When completed, the chore will automatically calculate the next due date based on the interval.

### Other Services

- `chore_assistant.remove_chore` - Remove a chore
- `chore_assistant.list_chores` - List all chores (logs to Home Assistant log)
- `chore_assistant.check_recurring` - Manually trigger check for recurring chores

## How It Works

1. **Daily Check**: Every day at midnight, the integration checks:
   - If pending chores are overdue (moves them to "overdue" state)
   - If completed chores are due again (resets them to "pending" with new due date)

2. **Entity IDs**: Each chore creates a sensor with ID `sensor.chore_assistant_{chore_name}` (spaces replaced with underscores)

3. **Display Names**: Sensor display names are just the chore name (e.g., "Take out trash")

4. **States**: 
   - `pending` - Chore is due but not completed
   - `overdue` - Chore is past due
   - `completed` - Chore is completed (will reset automatically based on interval)

## Example Automation

```yaml
automation:
  - alias: "Notify when chore is overdue"
    trigger:
      - platform: state
        entity_id: sensor.chore_assistant_take_out_trash
        to: "overdue"
    action:
      - service: notify.persistent_notification
        data:
          title: "Overdue Chore"
          message: "{{ trigger.to_state.name }} is overdue!"
```

A Home Assistant integration for tracking chores with three states: completed, overdue, and pending.

## Features

- Track chores with due dates
- Assign chores to specific people
- Three chore states: completed, overdue, and pending
- Automatic overdue detection
- Services for adding, removing, and completing chores
- Sensor entities to display chore status in Home Assistant

## Installation

1. Copy the `custom_components/chore_assistant` folder to your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.
3. The integration will be automatically available.

## Services

### Add Chore

Adds a new chore to track.

**Service:** `chore_assistant.add_chore`

**Fields:**
- `name` (required): The name of the chore
- `due_date` (optional): The date when the chore is due
- `assigned_to` (optional): Person assigned to the chore

### Remove Chore

Removes a chore from tracking.

**Service:** `chore_assistant.remove_chore`

**Fields:**
- `name` (required): The name of the chore to remove

### Complete Chore

Marks a chore as completed.

**Service:** `chore_assistant.complete_chore`

**Fields:**
- `name` (required): The name of the chore to complete

## Sensors

Each chore is represented as a sensor entity in Home Assistant with the following attributes:
- State: completed, overdue, or pending
- Created date
- Due date (if set)
- Assigned to (if set)
- Completed date (if completed)

## Automation Examples

### Notify when a chore is overdue

```yaml
- alias: "Chore Overdue Notification"
  trigger:
    - platform: state
      entity_id: sensor.chore_your_chore_name
      to: "overdue"
  action:
    - service: notify.mobile_app_your_device
      data:
        message: "Chore '{{ trigger.to_state.name }}' is overdue!"
```

### Reset chores weekly

```yaml
- alias: "Reset Weekly Chores"
  trigger:
    - platform: time
      at: "00:00:00"
  condition:
    - condition: time
      weekday:
        - mon
  action:
    - service: chore_assistant.add_chore
      data:
        name: "Weekly Chore"
```

## Contributing

Feel free to fork this repository and submit pull requests for improvements or bug fixes.
