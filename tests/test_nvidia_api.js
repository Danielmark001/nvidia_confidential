const axios = require('axios');
require('dotenv').config({ path: './medication-advisor-backend/.env' });

const apiKey = process.env.NVIDIA_API_KEY;
const model = process.env.LLM_MODEL || 'meta/llama-3.3-70b-instruct';
const baseUrl = process.env.LLM_BASE_URL || 'https://integrate.api.nvidia.com/v1';
const url = `${baseUrl}/chat/completions`;

console.log('Testing NVIDIA API:');
console.log('API Key exists:', !!apiKey);
console.log('Model:', model);
console.log('URL:', url);
console.log('---');

if (!apiKey) {
  console.error('No API key found!');
  process.exit(1);
}

axios.post(
  url,
  {
    model: model,
    messages: [
      {
        role: 'user',
        content: 'What is aspirin?'
      }
    ],
    max_tokens: 256,
    temperature: 0.7
  },
  {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    }
  }
)
.then(response => {
  console.log('✓ Success! Status:', response.status);
  console.log('Response:', JSON.stringify(response.data, null, 2));
})
.catch(error => {
  console.error('✗ Error:', error.message);
  if (error.response) {
    console.error('Status:', error.response.status);
    console.error('Headers:', error.response.headers);
    console.error('Data:', JSON.stringify(error.response.data, null, 2));
  } else if (error.request) {
    console.error('Request made but no response:', error.request);
  } else {
    console.error('Error details:', error);
  }
});
