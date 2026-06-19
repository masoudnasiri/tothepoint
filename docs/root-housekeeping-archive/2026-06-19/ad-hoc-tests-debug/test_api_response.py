#!/usr/bin/env python3
"""
Test script to check what the procurement API actually returns
"""
import requests
import json

# Test the procurement options API
try:
    # Get a token first (you'll need to login via the frontend and get the token)
    print("Testing procurement options API...")
    
    # This would need a real token, but let's check the database directly
    print("Checking database directly...")
    
except Exception as e:
    print(f"Error: {e}")
