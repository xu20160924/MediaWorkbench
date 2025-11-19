import axios from 'axios';

// Test the health endpoint directly
async function testDirectHealth() {
  try {
    const response = await axios.get('http://localhost:5002/api/health');
    console.log('Direct response:', response.data);
  } catch (error) {
    console.error('Error:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
    }
  }
}

testDirectHealth();