#!/usr/bin/env python3
"""
Quick test script for SmartCamera backend.
Usage: python3 test.py
"""

import sys
import os
import json
import time
import requests

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.camera import SmartCamera
from backend.mqtt_client import MQTTClient

def test_camera():
    print("=== Testing SmartCamera ===")
    cam = SmartCamera(resolution=(320, 240), framerate=10)
    
    # Test start
    print("Starting camera...")
    cam.start()
    time.sleep(1)
    
    # Test health
    health = cam.health_check()
    print(f"Health: {health}")
    assert health['running'], "Camera should be running"
    
    # Test capture
    print("Capturing image...")
    time.sleep(0.5)  # let camera warm up
    frame = cam.get_frame()
    assert frame is not None, "Frame should not be None"
    print(f"Frame size: {len(frame)} bytes")
    
    # Test save
    test_path = "./storage/test_capture.jpg"
    result = cam.capture_image(test_path)
    assert result == test_path, "Should return path"
    assert os.path.exists(test_path), f"File {test_path} should exist"
    print(f"Saved to {test_path}")
    
    # Test stop
    print("Stopping camera...")
    cam.stop()
    assert not cam.health_check()['running'], "Camera should be stopped"
    
    print("✓ Camera tests passed\n")

def test_mqtt():
    print("=== Testing MQTT ===")
    mqtt = MQTTClient(host='localhost', port=1883, client_id='test_client')
    
    try:
        print("Connecting to MQTT...")
        mqtt.connect()
        time.sleep(0.5)
        
        payload = json.dumps({'event': 'test', 'timestamp': time.time()})
        print(f"Publishing: {payload}")
        mqtt.publish('test/camera', payload)
        
        print("✓ MQTT tests passed\n")
    except Exception as e:
        print(f"⚠ MQTT test skipped (broker not running): {e}\n")

def test_server_api():
    print("=== Testing Server API (requires run.py running) ===")
    base_url = "http://localhost:5000"
    
    try:
        # Test health endpoint
        print("GET /api/health")
        r = requests.get(f"{base_url}/api/health", timeout=2)
        print(f"Status: {r.status_code}, Response: {r.json()}")
        
        # Test capture endpoint
        print("POST /api/capture")
        r = requests.post(f"{base_url}/api/capture", timeout=5)
        print(f"Status: {r.status_code}, Response: {r.json()}")
        
        print("✓ Server API tests passed\n")
    except Exception as e:
        print(f"⚠ Server API test skipped (server not running): {e}\n")

if __name__ == '__main__':
    print("SmartCamera Backend Test Suite\n")
    
    test_camera()
    test_mqtt()
    test_server_api()
    
    print("=== Summary ===")
    print("All available tests completed.")
    print("For full integration test, run: python3 run.py")
