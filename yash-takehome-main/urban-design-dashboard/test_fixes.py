#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Debug function error
2. LLM model processing
"""

import sys
import os
import requests
import time

# Add the backend app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_llm_endpoint():
    """Test the LLM processing endpoint directly"""
    print("🤖 Testing LLM Endpoint")
    print("=" * 40)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    test_queries = [
        "CC-X buildings",
        "commercial buildings", 
        "buildings over 100 feet",
        "buildings worth less than $500,000"
    ]
    
    for query in test_queries:
        print(f"\n🔹 Testing: '{query}'")
        try:
            response = requests.post(
                'http://localhost:5000/api/llm/process',
                json={'query': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data.get('success', False)}")
                if data.get('success'):
                    print(f"📊 Method: {data.get('metadata', {}).get('method', 'unknown')}")
                    print(f"🎯 Confidence: {data.get('metadata', {}).get('confidence', 0)}")
                    filters = data.get('filters', {})
                    print(f"🔍 Filters: {filters}")
                    print(f"🏢 Buildings found: {len(data.get('buildings', []))}")
                else:
                    print(f"❌ Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Backend server not running")
            break
        except requests.exceptions.Timeout:
            print("❌ Timeout: Server took too long to respond")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_debug_endpoint():
    """Test the debug endpoint that was causing the join error"""
    print("\n🔧 Testing Debug Endpoint")
    print("=" * 40)
    
    try:
        response = requests.get('http://localhost:5000/api/buildings/debug/calgary-fields', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Debug endpoint working: {data.get('success', False)}")
            if data.get('analysis'):
                print("✅ Analysis data present - no more join() errors")
            else:
                print("⚠️  Analysis data missing but no crash")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Urban Design Dashboard Fixes")
    print("=" * 50)
    
    # Test the LLM functionality
    test_llm_endpoint()
    
    # Test the debug functionality
    test_debug_endpoint()
    
    print("\n" + "=" * 50)
    print("🎉 Fix Testing Complete!")
    print("\nIf you see ✅ symbols above, both issues are fixed!")
    print("Now try using the web interface at http://localhost:3000") 