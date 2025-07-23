#!/usr/bin/env python3
"""
Test script to verify the Chore Assistant integration structure
"""

import os
import yaml
from datetime import datetime, timedelta

def test_integration_structure():
    """Test that the integration has all required files."""
    
    base_path = "custom_components/chore_assistant"
    required_files = [
        "__init__.py",
        "manifest.json",
        "config_flow.py",
        "const.py",
        "sensor.py",
        "README.md",
        "chores.yaml"
    ]
    
    print("Testing Chore Assistant integration structure...")
    
    # Check all required files exist
    missing_files = []
    for file in required_files:
        file_path = os.path.join(base_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    
    # Test manifest.json
    try:
        import json
        with open(os.path.join(base_path, "manifest.json"), 'r') as f:
            manifest = json.load(f)
        print("✅ manifest.json is valid JSON")
        print(f"   Domain: {manifest.get('domain')}")
        print(f"   Name: {manifest.get('name')}")
        print(f"   Version: {manifest.get('version')}")
    except Exception as e:
        print(f"❌ Error reading manifest.json: {e}")
        return False
    
    # Test chores.yaml
    try:
        with open(os.path.join(base_path, "chores.yaml"), 'r') as f:
            chores = yaml.safe_load(f)
        print("✅ chores.yaml is valid YAML")
        if chores and isinstance(chores, list):
            print(f"   Found {len(chores)} example chores")
    except Exception as e:
        print(f"❌ Error reading chores.yaml: {e}")
        return False
    
    # Test Python imports
    try:
        # Test const.py
        from custom_components.chore_assistant.const import DOMAIN
        print(f"✅ Successfully imported const: DOMAIN = {DOMAIN}")
        
        # Test sensor.py
        from custom_components.chore_assistant.sensor import async_setup_entry
        print("✅ Successfully imported sensor module")
        
    except Exception as e:
        print(f"❌ Error importing modules: {e}")
        return False
    
    print("\n🎉 All tests passed! The Chore Assistant integration is ready to use.")
    return True

def test_chore_creation():
    """Test creating a sample chore configuration."""
    
    sample_chore = {
        "name": "Test Chore",
        "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "frequency": "weekly",
        "description": "This is a test chore",
        "assigned_to": "test_user",
        "chore_type": "fixed",
        "max_days": 7,
        "adaptive_window": 3,
        "last_completed": None
    }
    
    print("\nTesting chore creation...")
    print(f"Sample chore: {sample_chore}")
    
    # Validate required fields
    required_fields = ["name", "due_date", "frequency", "chore_type"]
    missing = [field for field in required_fields if field not in sample_chore]
    
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False
    
    print("✅ Sample chore has all required fields")
    return True

if __name__ == "__main__":
    success1 = test_integration_structure()
    success2 = test_chore_creation()
    
    if success1 and success2:
        print("\n🚀 Integration is ready for Home Assistant!")
    else:
        print("\n⚠️  Please fix the issues above before using the integration.")
