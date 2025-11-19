#!/usr/bin/env python3
"""
Test script to verify the API response structure for images
"""

import requests
import json
import sys

def test_list_images_api():
    """Test the /api/images endpoint to see the actual response structure"""
    
    base_url = "http://localhost:5000"
    endpoint = f"{base_url}/api/images"
    
    print(f"Testing API endpoint: {endpoint}")
    
    try:
        # Test with different parameters
        params_list = [
            {"page": 1, "per_page": 5},
            {"image_type": "general", "page": 1, "per_page": 5},
        ]
        
        for params in params_list:
            print(f"\n{'='*60}")
            print(f"Testing with params: {params}")
            
            response = requests.get(endpoint, params=params)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response success: {data.get('success')}")
                print(f"Response message: {data.get('message')}")
                
                if 'data' in data:
                    response_data = data['data']
                    print(f"Total items: {response_data.get('total')}")
                    print(f"Current page: {response_data.get('page')}")
                    print(f"Items per page: {response_data.get('per_page')}")
                    print(f"Total pages: {response_data.get('pages')}")
                    
                    items = response_data.get('items', [])
                    print(f"Items in response: {len(items)}")
                    
                    if items:
                        print("\nFirst item structure:")
                        first_item = items[0]
                        for key, value in first_item.items():
                            if key == 'variables':
                                print(f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}")
                            else:
                                print(f"  {key}: {value}")
                        
                        # Check if any general images with participated=false exist
                        general_images = [item for item in items if item.get('image_type') == 'general']
                        print(f"\nGeneral images found: {len(general_images)}")
                        
                        if general_images:
                            not_participated = [img for img in general_images if not img.get('participated', False)]
                            print(f"General images with participated=false: {len(not_participated)}")
                            
                            if not_participated:
                                print("\nSample general images with participated=false:")
                                for img in not_participated[:3]:
                                    print(f"  ID: {img.get('id')}, Filename: {img.get('filename')}, Participated: {img.get('participated')}")
                    else:
                        print("No items in response")
                else:
                    print("No data field in response")
            else:
                print(f"Error response: {response.text}")
                
    except Exception as e:
        print(f"Error testing API: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting API response test...")
    success = test_list_images_api()
    
    if success:
        print("\n✅ API test completed successfully")
    else:
        print("\n❌ API test failed")
        sys.exit(1)