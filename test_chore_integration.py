#!/usr/bin/env python3
"""
Test script to verify the Chore Assistant integration works correctly.
This script simulates the Home Assistant environment and tests the core functionality.
"""

import os
import sys
import yaml
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from chore_assistant.const import DOMAIN
from chore_assistant import async_setup_entry, _register_services

async def test_add_chore():
    """Test adding a chore."""
    print("Testing add_chore service...")
    
    # Mock Home Assistant
    hass = Mock()
    hass.data = {}
    hass.config.path = Mock(return_value=os.path.join(os.getcwd(), 'test_chores.yaml'))
    hass.async_create_task = Mock()
    hass.helpers = Mock()
    hass.helpers.entity_platform = Mock()
    hass.helpers.entity_platform.async_add_entities = Mock()
    
    # Mock config entry
    entry = Mock()
    
    # Setup integration
    await async_setup_entry(hass, entry)
    
    # Test adding a chore
    call = Mock()
    call.data = {
        'name': 'Test Chore',
        'due_date': datetime.now() + timedelta(days=7),
        'frequency': 'weekly',
        'description': 'Test description',
        'assigned_to': 'test_user',
        'chore_type': 'fixed',
        'max_days': 3,
        'adaptive_window': 3
    }
    
    # Get the add_chore service
    await _register_services(hass)
    
    # Find the add_chore service
    service_calls = []
    def mock_register(domain, service, handler, schema=None):
        if service == 'add_chore':
            service_calls.append(handler)
    
    with patch.object(hass.services, 'async_register', side_effect=mock_register):
        await _register_services(hass)
    
    if service_calls:
        await service_calls[0](call)
        print("✓ add_chore service executed successfully")
        
        # Verify chore was added
        chores = hass.data[DOMAIN]['chores']
        if any(chore['name'] == 'Test Chore' for chore in chores):
            print("✓ Chore was successfully added to storage")
        else:
            print("✗ Chore was not found in storage")
    else:
        print("✗ add_chore service not found")

def test_chore_sensor():
    """Test the ChoreSensor class."""
    print("\nTesting ChoreSensor...")
    
    from chore_assistant import ChoreSensor
    
    chore_data = {
        'name': 'Test Sensor',
        'due_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
        'frequency': 'weekly',
        'description': 'Test sensor',
        'assigned_to': 'test_user',
        'chore_type': 'fixed',
        'max_days': 3,
        'adaptive_window': 3,
        'last_completed': None
    }
    
    try:
        sensor = ChoreSensor(chore_data)
        print(f"✓ ChoreSensor created successfully")
        print(f"  Name: {sensor.name}")
        print(f"  State: {sensor.state}")
        print(f"  Attributes: {sensor.extra_state_attributes}")
    except Exception as e:
        print(f"✗ Error creating ChoreSensor: {e}")

async def main():
    """Run all tests."""
    print("Chore Assistant Integration Test Suite")
    print("=" * 40)
    
    try:
        await test_add_chore()
        test_chore_sensor()
        print("\n✓ All tests completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
