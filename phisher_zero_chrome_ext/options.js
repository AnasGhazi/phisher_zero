// Options page script for Phisher Zero
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved settings
  const settings = await loadSettings();
  
  // Populate form
  document.getElementById('mockModeToggle').checked = settings.mockMode || false;
  document.getElementById('apiBaseUrl').value = settings.apiBaseUrl || '';
  document.getElementById('darkModeToggleSetting').checked = settings.darkMode || false;
  
  // Apply theme
  applyTheme(settings.darkMode || false);
  
  // Event listeners
  document.getElementById('saveButton').addEventListener('click', handleSaveSettings);
  
  // Dark mode toggle in header
  document.getElementById('darkModeToggle').addEventListener('click', async () => {
    const settings = await loadSettings();
    const newDarkMode = !settings.darkMode;
    document.getElementById('darkModeToggleSetting').checked = newDarkMode;
    await saveSettings({ ...settings, darkMode: newDarkMode });
    applyTheme(newDarkMode);
  });
  
  // Dark mode toggle in settings
  document.getElementById('darkModeToggleSetting').addEventListener('change', async () => {
    const settings = await loadSettings();
    const newDarkMode = document.getElementById('darkModeToggleSetting').checked;
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
    if (darkIcon) darkIcon.classList.remove('hidden');
    if (lightIcon) lightIcon.classList.add('hidden');
  } else {
    body.classList.remove('theme-dark');
    body.classList.add('theme-light');
    if (darkIcon) darkIcon.classList.add('hidden');
    if (lightIcon) lightIcon.classList.remove('hidden');
  }
}

async function handleSaveSettings() {
  const mockMode = document.getElementById('mockModeToggle').checked;
  const apiBaseUrl = document.getElementById('apiBaseUrl').value.trim();
  const darkMode = document.getElementById('darkModeToggleSetting').checked;
  
  // Validate API URL if mock mode is disabled
  if (!mockMode && apiBaseUrl && !isValidUrl(apiBaseUrl)) {
    alert('Please enter a valid URL (e.g., https://api.example.com)');
    return;
  }
  
  // Save settings
  await saveSettings({
    mockMode,
    darkMode,
    apiBaseUrl: apiBaseUrl || 'https://api.phisherzero.com'
  });
  
  // Apply theme
  applyTheme(darkMode);
  
  // Show confirmation
  const confirmation = document.getElementById('saveConfirmation');
  confirmation.classList.remove('hidden');
  
  // Hide confirmation after 3 seconds
  setTimeout(() => {
    confirmation.classList.add('hidden');
  }, 3000);
}

function isValidUrl(string) {
  try {
    const url = new URL(string);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (_) {
    return false;
  }
}
