// Popup script for Phisher Zero
document.addEventListener('DOMContentLoaded', async () => {
  // Initialize UI state
  updateScanStatus('waiting');
  
  // Load settings and apply theme
  const settings = await loadSettings();
  applyTheme(settings.darkMode || false);
  
  // Event listeners
  document.getElementById('scanButton').addEventListener('click', handleScanEmail);
  document.getElementById('settingsButton').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
  
  // Dark mode toggle
  document.getElementById('darkModeToggle').addEventListener('click', async () => {
    const settings = await loadSettings();
    const newDarkMode = !settings.darkMode;
    await saveSettings({ ...settings, darkMode: newDarkMode });
    applyTheme(newDarkMode);
  });
});

function applyTheme(isDark) {
  const body = document.body;
  const darkIcon = document.getElementById('darkIcon');
  const lightIcon = document.getElementById('lightIcon');
  
  if (isDark) {
    body.classList.remove('theme-light');
    body.classList.add('theme-dark');
    darkIcon.classList.remove('hidden');
    lightIcon.classList.add('hidden');
  } else {
    body.classList.remove('theme-dark');
    body.classList.add('theme-light');
    darkIcon.classList.add('hidden');
    lightIcon.classList.remove('hidden');
  }
}

async function handleScanEmail() {
  const scanButton = document.getElementById('scanButton');
  const originalText = scanButton.innerHTML;
  
  // Disable button and show loading
  scanButton.disabled = true;
  scanButton.innerHTML = `
    <svg class="w-5 h-5 spinner" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
    </svg>
    Analyzing...
  `;
  
  // Update status to loading
  updateScanStatus('loading');
  
  try {
    const manualEmail = document.getElementById('manualEmail')?.value || "";
    const manualUrl = document.getElementById('manualUrl')?.value || "";
    
    let payload = null;
    if (manualEmail.trim() !== "" || manualUrl.trim() !== "") {
      payload = {
        email_text: manualEmail.trim(),
        url: manualUrl.trim()
      };
    }

    // Simulate scanning email
    const results = await scanEmail(payload);
    
    // Update UI with results
    updateUI(results);
    
    // Update status based on results
    const isPhishing = results.analysis?.ensemble?.verdict === 'phishing' || results.analysis?.ensemble?.verdict === 'suspicious';
    updateScanStatus(isPhishing ? 'phishing' : 'safe', results);
    
  } catch (error) {
    console.error('Error scanning email:', error);
    updateScanStatus('error', { error: error.message });
  } finally {
    // Re-enable button
    scanButton.disabled = false;
    scanButton.innerHTML = originalText;
  }
}

function updateScanStatus(state, data = {}) {
  const statusBox = document.getElementById('scanStatus');
  const statusIcon = document.getElementById('statusIcon');
  const statusText = document.getElementById('statusText');
  const statusSubtext = document.getElementById('statusSubtext');
  
  // Reset classes
  statusBox.className = 'bg-card rounded-3xl shadow-lg p-6 mb-6 border transition-all duration-300 fade-in backdrop-blur-sm';
  statusIcon.innerHTML = '';
  
  switch (state) {
    case 'waiting':
      statusBox.classList.add('border-border');
      statusIcon.className = 'w-14 h-14 rounded-2xl bg-status-waiting flex items-center justify-center shadow-sm border border-border';
      statusIcon.innerHTML = `
        <svg class="w-7 h-7 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      `;
      statusText.textContent = 'Waiting to scan email';
      statusSubtext.textContent = 'Select an email to begin analysis';
      break;
      
    case 'loading':
      statusBox.classList.add('border-secondary/30');
      statusIcon.className = 'w-14 h-14 rounded-2xl bg-status-loading flex items-center justify-center shadow-sm border border-secondary/30';
      statusIcon.innerHTML = `
        <svg class="w-7 h-7 text-secondary spinner" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
      `;
      statusText.textContent = 'Analyzing with AI Agents…';
      statusSubtext.textContent = 'This may take a few seconds';
      break;
      
    case 'safe':
      statusBox.classList.add('border-safe/50', 'bg-status-safe');
      statusIcon.className = 'w-14 h-14 rounded-2xl bg-safe/20 flex items-center justify-center shadow-sm border border-safe/50';
      statusIcon.innerHTML = `
        <svg class="w-8 h-8 text-safe" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
      `;
      statusText.textContent = 'Result: Safe';
      statusSubtext.textContent = 'This email appears to be legitimate';
      break;
      
    case 'phishing':
      statusBox.classList.add('border-danger/50', 'bg-status-danger');
      statusIcon.className = 'w-14 h-14 rounded-2xl bg-danger/20 flex items-center justify-center shadow-sm border border-danger/50';
      statusIcon.innerHTML = `
        <svg class="w-8 h-8 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
      `;
      statusText.textContent = 'Result: Phishing Detected';
      statusSubtext.textContent = 'Warning: This email may be a phishing attempt';
      break;
      
    case 'error':
      statusBox.classList.add('border-danger/50', 'bg-status-danger');
      statusIcon.className = 'w-14 h-14 rounded-2xl bg-danger/20 flex items-center justify-center shadow-sm border border-danger/50';
      statusIcon.innerHTML = `
        <svg class="w-8 h-8 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      `;
      statusText.textContent = 'Error';
      statusSubtext.textContent = data.error || 'An error occurred while scanning';
      break;
  }
}

function updateUI(results) {
  // Show agent breakdown
  const agentBreakdown = document.getElementById('agentBreakdown');
  agentBreakdown.classList.remove('hidden');
  agentBreakdown.classList.add('fade-in');
  
  const analysis = results.analysis || {};
  const explanation = results.explanation || {};
  
  // Update NLP Agent
  if (analysis.nlp) {
    document.getElementById('nlpScore').textContent = `${(analysis.nlp.nlp_score * 100).toFixed(1)}%`;
    document.getElementById('nlpScore').className = `text-sm font-bold px-2 py-1 rounded-lg ${
      analysis.nlp.nlp_score > 0.5 ? 'text-danger bg-danger/20' : 'text-safe bg-safe/20'
    }`;
    document.getElementById('nlpExplanation').textContent = `Spam/Phishing Confidence: ${(analysis.nlp.nlp_score * 100).toFixed(1)}%`;
  }
  
  // Update URL Agent
  if (analysis.url) {
    document.getElementById('urlScore').textContent = `${(analysis.url.url_risk_score * 100).toFixed(1)}%`;
    document.getElementById('urlScore').className = `text-sm font-bold px-2 py-1 rounded-lg ${
      analysis.url.url_risk_score > 0.5 ? 'text-danger bg-danger/20' : 'text-safe bg-safe/20'
    }`;
    document.getElementById('urlExplanation').textContent = 
      analysis.url.virustotal?.virustotal_match ? 'VirusTotal Hit: Yes' : 'VirusTotal Hit: No';
  }
  
  // Update Ensemble Agent
  if (analysis.ensemble) {
    const probability = analysis.ensemble.final_score;
    document.getElementById('ensembleScore').textContent = `${(probability * 100).toFixed(1)}%`;
    document.getElementById('ensembleScore').className = `text-sm font-bold px-2 py-1 rounded-lg ${
      probability > 0.5 ? 'text-danger bg-danger/20' : 'text-safe bg-safe/20'
    }`;
    document.getElementById('ensembleExplanation').textContent = 
      `Final verdict: ${analysis.ensemble.verdict.toUpperCase()}`;
  }
  
  // Update Explainer Agent
  if (explanation) {
    const summaryText = explanation.summary || 'No reasoning available';
    const actionText = explanation.recommended_action ? `\n\nAction: ${explanation.recommended_action}` : '';
    document.getElementById('explainerReasoning').textContent = summaryText + actionText;
  }
}
