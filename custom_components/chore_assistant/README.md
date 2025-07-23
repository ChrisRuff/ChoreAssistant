# Chore Assistant - Home Assistant Integration

A comprehensive chore tracking integration for Home Assistant that allows you to manage household chores through the UI and services.

## Features

- **UI Configuration**: Add and manage chores through Home Assistant's UI
- **Service-based Management**: Use Home Assistant services to add, update, remove, and complete chores
- **Flexible Chore Types**: Support for both fixed-schedule and adaptive chores
- **Detailed Tracking**: Track due dates, completion history, and assignment
- **Smart Scheduling**: Adaptive chores adjust their schedule based on completion patterns

## Installation

1. Copy the `custom_components/chore_assistant` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration through Configuration > Integrations > Add Integration > Chore Assistant

## Usage

### Adding Chores via Services

You can add chores using the `chore_assistant.add_chore` service:

```yaml
service: chore_assistant.add_chore
data:
  name: "Clean Kitchen"
  due_date: "2025-07-25"
  frequency: "weekly"
  description: "Clean kitchen counters, appliances, and floor"
  assigned_to: "household"
  chore_type: "fixed"
  max_days: 7
  adaptive_window: 3
```

### Service Reference

#### `chore_assistant.add_chore`
Add a new chore to track.

| Parameter         | Type    | Required | Description                                                                      |
| ----------------- | ------- | -------- | -------------------------------------------------------------------------------- |
| `name`            | string  | Yes      | Name of the chore                                                                |
| `due_date`        | date    | Yes      | Due date (YYYY-MM-DD format)                                                     |
| `frequency`       | string  | No       | Frequency: daily, weekly, biweekly, monthly, quarterly, yearly (default: weekly) |
| `description`     | string  | No       | Description of the chore                                                         |
| `assigned_to`     | string  | No       | Person or group assigned to the chore (default: household)                       |
| `chore_type`      | string  | No       | Type: fixed or adaptive (default: fixed)                                         |
| `max_days`        | integer | No       | Maximum days for adaptive chores (1-30, default: 7)                              |
| `adaptive_window` | integer | No       | Adaptive window for adaptive chores (1-30, default: 3)                           |

#### `chore_assistant.remove_chore`
Remove a chore.

| Parameter | Type   | Required | Description                 |
| --------- | ------ | -------- | --------------------------- |
| `name`    | string | Yes      | Name of the chore to remove |

#### `chore_assistant.update_chore`
Update an existing chore.

| Parameter         | Type    | Required | Description                 |
| ----------------- | ------- | -------- | --------------------------- |
| `name`            | string  | Yes      | Name of the chore to update |
| `due_date`        | date    | No       | New due date                |
| `frequency`       | string  | No       | New frequency               |
| `description`     | string  | No       | New description             |
| `assigned_to`     | string  | No       | New assigned person/group   |
| `chore_type`      | string  | No       | New chore type              |
| `max_days`        | integer | No       | New max days                |
| `adaptive_window` | integer | No       | New adaptive window         |

#### `chore_assistant.complete_chore`
Mark a chore as completed and update its due date.

| Parameter | Type   | Required | Description                   |
| --------- | ------ | -------- | ----------------------------- |
| `name`    | string | Yes      | Name of the chore to complete |

### Chore Types

#### Fixed Chores
- Follow a strict schedule based on frequency
- Due dates are calculated from the original due date
- Good for regular maintenance tasks

#### Adaptive Chores
- Adjust their schedule based on when they're completed
- If completed early, the next due date is closer
- If completed late, the next due date is extended
- Good for tasks that can be flexible

### Automation Examples

#### Daily Chore Reminder
```yaml
automation:
  - alias: "Daily Chore Reminder"
    trigger:
      platform: time
      at: "09:00:00"
    condition:
      condition: template
      value_template: "{{ states('sensor.chore_take_out_trash') == 'due' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Don't forget to take out the trash today!"
```

#### Chore Completion Automation
```yaml
automation:
  - alias: "Complete Chore via Button"
    trigger:
      platform: state
      entity_id: input_button.complete_kitchen_cleaning
    action:
      - service: chore_assistant.complete_chore
        data:
          name: "Clean Kitchen"
```

## Configuration File

The integration stores chores in `chore_assistant_chores.yaml` in your Home Assistant configuration directory. You can manually edit this file, but it's recommended to use the services for consistency.

## Troubleshooting

### Common Issues

1. **Chores not appearing**: Ensure the integration is properly configured and restart Home Assistant
2. **Service errors**: Check the Home Assistant logs for detailed error messages
3. **YAML syntax errors**: If editing the chores.yaml file manually, ensure proper YAML formatting

### Logs
Check the Home Assistant logs for any errors related to the chore_assistant integration.

## Development

To contribute or modify this integration:

1. The main integration logic is in `__init__.py`
2. Sensor definitions are in `sensor.py`
3. Configuration flow is in `config_flow.py`
4. Constants are defined in `const.py`
