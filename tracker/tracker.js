// This self-contained script is designed to be a lightweight, privacy-first analytics tracker.
// It collects only non-personally identifiable information and sends it to a backend API.
// To use, simply include this file on your website.

(function() {
  function sendTrackingData() {
    try {
      const data = {
        // Collect anonymous data
        path: window.location.pathname,
        resolution: `${window.screen.width}x${window.screen.height}`
      };

      // Define the API endpoint URL
      const apiEndpoint = 'https://YOUR_FLASK_APP_URL/track'; // REPLACE WITH YOUR DEPLOYED FLASK URL

      // Send the data using a simple, non-blocking fetch request
      fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        // Use keepalive to ensure the request is sent even if the page unloads
        keepalive: true,
      })
      .then(response => {
        if (!response.ok) {
          console.warn('Analytics tracking failed:', response.statusText);
        }
      })
      .catch(error => {
        console.error('Analytics tracking failed:', error);
      });
    } catch (e) {
      console.error('An error occurred during tracking:', e);
    }
  }

  // Send data when the page loads
  if (document.readyState === 'complete') {
    sendTrackingData();
  } else {
    window.addEventListener('load', sendTrackingData);
  }
})();
