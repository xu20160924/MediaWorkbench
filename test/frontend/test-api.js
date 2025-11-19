import axios from 'axios';

// Simulate the frontend API configuration
const API_ENDPOINT = 'http://localhost:5002/api';

// Create axios instance
const request = axios.create({
  baseURL: API_ENDPOINT,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Test the health endpoint
async function testHealth() {
  try {
    const response = await request.get('/health');
    console.log('Response:', response.data);
  } catch (error) {
    console.error('Error:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
      console.error('Response headers:', error.response.headers);
    }
  }
}

testHealth();