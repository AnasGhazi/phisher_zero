// API integration script for Phisher Zero
// This file contains placeholder functions that will be connected to the backend

// Mock data for testing
const MOCK_SAFE_RESPONSE = {
  nlp_agent: {
    score: 0.15,
    explanation: "Email content shows normal language patterns with no suspicious urgency or threats."
  },
  url_agent: {
    score: 0.08,
    explanation: "All URLs in the email point to legitimate domains with valid SSL certificates."
  },
  ensemble_agent: {
    probability: 0.12,
    confidence: 0.92
  },
  explainer_agent: {
    reasoning: "This email appears safe based on consistent analysis across all agents. No phishing indicators detected."
  }
};

const MOCK_PHISHING_RESPONSE = {
  nlp_agent: {
    score: 0.87,
    explanation: "Email contains urgent language, suspicious requests for personal information, and grammatical inconsistencies."
  },
  url_agent: {
    score: 0.92,
    explanation: "URLs redirect to suspicious domains with mismatched SSL certificates and unusual domain patterns."
  },
  ensemble_agent: {
    probability: 0.89,
    confidence: 0.95
  },
  explainer_agent: {
    reasoning: "High probability of phishing detected. Multiple red flags including suspicious URLs, urgent language, and request for sensitive information."
  }
};

/**
 * Scan an email using the backend agents
 * @param {Object} emailData - The email data to scan
 * @returns {Promise<Object>} The results from all agents
 */
async function scanEmail(emailData = null) {
  const settings = await loadSettings();
  
  if (settings.mockMode) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    const isPhishing = Math.random() > 0.5;
    return isPhishing ? MOCK_PHISHING_RESPONSE : MOCK_SAFE_RESPONSE;
  }
  
  try {
    const pageData = await getCurrentPageData();
    
    let submitText = pageData.text;
    let submitUrl = pageData.url;

    if (emailData) {
      if (emailData.email_text) submitText = emailData.email_text;
      if (emailData.url) submitUrl = emailData.url;
    }
    
    const response = await fetch(`${settings.apiBaseUrl}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email_text: submitText,
        url: submitUrl
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error calling API:', error);
    throw error;
  }
}

/**
 * Fetch results from individual agents
 * @param {string} agentName - Name of the agent (nlp, url, ensemble, explainer)
 * @returns {Promise<Object>} Agent-specific results
 */
async function fetchAgentResults(agentName) {
  const settings = await loadSettings();
  
  if (settings.mockMode) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockData = {
      nlp: MOCK_SAFE_RESPONSE.nlp_agent,
      url: MOCK_SAFE_RESPONSE.url_agent,
      ensemble: MOCK_SAFE_RESPONSE.ensemble_agent,
      explainer: MOCK_SAFE_RESPONSE.explainer_agent
    };
    
    return mockData[agentName] || {};
  }
  
  try {
    const response = await fetch(`${settings.apiBaseUrl}/api/agents/${agentName}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Error fetching ${agentName} agent results:`, error);
    throw error;
  }
}

/**
 * Update the UI with scan results
 * @param {Object} results - The results object from scanEmail
 */
function updateUI(results) {
  // This function is called from popup.js
  // The actual UI update logic is in popup.js
  console.log('Results received:', results);
}

/**
 * Save settings to Chrome storage
 * @param {Object} settings - Settings object to save
 */
async function saveSettings(settings) {
  return new Promise((resolve, reject) => {
    chrome.storage.sync.set({ settings }, () => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve();
      }
    });
  });
}

/**
 * Load settings from Chrome storage
 * @returns {Promise<Object>} Settings object
 */
async function loadSettings() {
  return new Promise((resolve, reject) => {
    chrome.storage.sync.get(['settings'], (result) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(result.settings || {
          mockMode: true,
          darkMode: false,
          apiBaseUrl: 'https://api.phisherzero.com'
        });
      }
    });
  });
}

/**
 * Get current page content from the active tab
 * @returns {Promise<Object>} Object containing text and url
 */
async function getCurrentPageData() {
  return new Promise((resolve) => {
    try {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const activeTab = tabs[0];
        if (!activeTab || !activeTab.id) {
          resolve({ text: "Unable to retrieve tab content", url: "" });
          return;
        }
        const url = activeTab.url;
        
        // Execute script to extract text
        chrome.scripting.executeScript(
          {
            target: { tabId: activeTab.id },
            func: () => document.body.innerText
          },
          (results) => {
            let text = "No text found on page.";
            if (results && results[0] && results[0].result) {
              text = results[0].result.trim().substring(0, 5000); // Limit to 5k chars
            }
            resolve({ text, url });
          }
        );
      });
    } catch (e) {
      console.error("Tab query failed, perhaps not in extension context", e);
      resolve({ text: "Error extracting content", url: "" });
    }
  });
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    scanEmail,
    fetchAgentResults,
    updateUI,
    saveSettings,
    loadSettings
  };
}

