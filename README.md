# Chore Assistant

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
