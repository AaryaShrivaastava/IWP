// This script is the lightweight, privacy-first analytics tracker.
// It collects non-personally identifiable information and sends it to the backend.

(function() {
    const TRACKING_ENDPOINT = 'http://localhost:5000/track'; // The URL of your Flask backend API

    // Helper function to send data to the backend
    function sendData(data) {
        try {
            fetch(TRACKING_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                // We use keepalive to ensure the request is sent even if the page is
                // being unloaded. This is a best practice for analytics.
                keepalive: true,
            })
            .then(response => {
                if (!response.ok) {
                    console.error('Analytics tracking failed with status:', response.status);
                }
            })
            .catch(error => {
                console.error('Error sending analytics data:', error);
            });
        } catch (e) {
            console.error('Failed to send tracking request:', e);
        }
    }

    // Collect anonymous, non-PII data
    function collectData() {
        const pagePath = window.location.pathname;
        const screenWidth = window.screen.width;
        const screenHeight = window.screen.height;

        return {
            pagePath: pagePath,
            screenWidth: screenWidth,
            screenHeight: screenHeight
        };
    }

    // Main function to initialize the tracker
    function initTracker() {
        const data = collectData();
        sendData(data);
    }

    // Wait for the page to be fully loaded before starting the tracker
    if (document.readyState === 'complete') {
        initTracker();
    } else {
        window.addEventListener('load', initTracker);
    }

})();
