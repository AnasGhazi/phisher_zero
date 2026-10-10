// Background service worker for Phisher Zero
chrome.runtime.onInstalled.addListener(() => {
  console.log('Phisher Zero extension installed');
  
  // Set default settings
  chrome.storage.sync.get(['settings'], (result) => {
    if (!result.settings) {
      chrome.storage.sync.set({
        settings: {
          mockMode: false,
          apiBaseUrl: 'http://localhost:8000'
        }
      });
    }
  });
});

// Listen for messages from popup/content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scanEmail') {
    // Handle email scanning request
    handleEmailScan(request.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep message channel open for async response
  }
});

async function handleEmailScan(emailData) {
  // This will be connected to the actual backend later
  // For now, return a placeholder response
  return {
    status: 'processed',
    timestamp: new Date().toISOString()
  };
}

