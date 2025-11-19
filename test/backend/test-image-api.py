import requests

# Test image list API
url = "http://localhost:5002/api/images?page=1&per_page=20"
response = requests.get(url)
print(f"Image list API response (Status: {response.status_code})")
print(f"Response headers: {dict(response.headers)}")
print(f"Response content: {response.content[:500]}...")

# Test image details API
# url = "http://localhost:5002/api/images/1"
# response = requests.get(url)
# print(f"Image details API response (Status: {response.status_code})")
# print(f"Response content: {response.content[:500]}...")

# Test base-paths API
url = "http://localhost:5002/api/images/base-paths"
response = requests.get(url)
print(f"Base paths API response (Status: {response.status_code})")
print(f"Response content: {response.content[:500]}...")