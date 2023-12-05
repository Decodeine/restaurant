function handleLoginResponse() {
  // Retrieve the token from the session
  const token = sessionStorage.getItem('auth_token');

  if (token) {
    authToken = token;
    console.log('Authentication token:', authToken);
  } else {
    console.log('User not authenticated');
  }
}


function getAuthToken() {
  return authToken;
}

async function fetchData(endpoint) {
  const authToken = getAuthToken();

  if (!authToken) {
    console.log('User not authenticated');
    return;
  }

  try {
    const response = await fetch(endpoint, {
      headers: {
        Authorization: `Token ${authToken}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Data:', data);
    } else {
      console.error('Request failed:', response.status);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

