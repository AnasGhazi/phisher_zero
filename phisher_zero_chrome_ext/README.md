# Phisher Zero - Chrome Extension Frontend

AI-Powered Email Phishing Detector Chrome Extension

## 📁 Project Structure

```
phisherzero_frontend/
├── manifest.json          # Chrome Extension manifest (V3)
├── popup.html            # Main popup UI
├── popup.js              # Popup logic and UI updates
├── popup.css             # Custom styles and animations
├── options.html          # Settings page
├── options.js            # Settings page logic
├── background.js         # Service worker for background tasks
├── scripts/
│   └── api.js           # API integration and mock data
├── assets/
│   ├── icon16.png      # 16x16 icon (add your icons)
│   ├── icon48.png      # 48x48 icon
│   └── icon128.png     # 128x128 icon
└── README.md           # This file
```

## 🚀 Installation

1. **Add Extension Icons**
   - Place your icon files (16x16, 48x48, 128x128 PNG) in the `/assets` folder
   - Or use placeholder images for testing

2. **Load Extension in Chrome**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `phisherzero_frontend` folder

3. **Test the Extension**
   - Click the extension icon in the toolbar
   - The popup should open with the Phisher Zero interface
   - Click "Scan Selected Email" to test with mock data

## 🎨 Features

### Popup Interface
- **Header**: Logo and branding
- **Scan Status Box**: Shows current state (waiting, loading, safe, phishing)
- **Agent Breakdown**: Displays results from all 4 AI agents
  - NLP Agent
  - URL Agent
  - Ensemble Agent
  - Explainer Agent
- **Action Buttons**: Scan, View Logs, Settings

### Settings Page
- **Mock Mode Toggle**: Enable/disable simulated data
- **API Base URL**: Configure backend endpoint
- **Save Settings**: Persists configuration to Chrome storage

### Background Service Worker
- Handles extension lifecycle
- Manages message passing between components
- Initializes default settings

## 🔧 Configuration

### Mock Mode (Default: Enabled)
When enabled, the extension uses simulated data for testing. This allows you to:
- Test the UI without a backend
- See different result states (safe/phishing)
- Develop frontend features independently

### API Integration
To connect to your backend:
1. Open Settings (click Settings button in popup)
2. Disable "Mock Mode"
3. Enter your API Base URL (e.g., `https://api.phisherzero.com`)
4. Click "Save Settings"

## 📡 API Integration

The extension expects your backend to provide endpoints:

### POST `/api/scan`
Request body:
```json
{
  "email": {
    "subject": "Email subject",
    "body": "Email body text",
    "sender": "sender@example.com",
    "urls": ["https://example.com"]
  }
}
```

Response:
```json
{
  "nlp_agent": {
    "score": 0.15,
    "explanation": "Email content analysis..."
  },
  "url_agent": {
    "score": 0.08,
    "explanation": "URL analysis..."
  },
  "ensemble_agent": {
    "probability": 0.12,
    "confidence": 0.92
  },
  "explainer_agent": {
    "reasoning": "Overall assessment..."
  }
}
```

### GET `/api/agents/{agentName}`
Returns individual agent results (nlp, url, ensemble, explainer)

## 🎨 Design System

### Colors
- **Primary Blue**: `#1A73E8` (electric blue)
- **Safe/Green**: Emerald green variants
- **Phishing/Red**: Red variants for warnings
- **Background**: Light gray (`#F9FAFB`)

### Typography
- Font: Inter (Google Fonts)
- Headings: Bold, 600-700 weight
- Body: Regular, 400-500 weight

### Components
- Rounded corners: `rounded-lg`, `rounded-xl`
- Shadows: Soft shadows with hover effects
- Transitions: Smooth 200-300ms transitions
- Spacing: Consistent padding and margins

## 🛠️ Development

### File Descriptions

- **manifest.json**: Extension configuration, permissions, and metadata
- **popup.html/js/css**: Main user interface
- **options.html/js**: Settings and configuration page
- **background.js**: Service worker for background tasks
- **scripts/api.js**: API calls, mock data, and settings management

### Customization

To customize the UI:
1. Modify Tailwind classes in HTML files
2. Add custom styles in `popup.css`
3. Update color scheme by changing Tailwind color classes
4. Modify component layouts in HTML structure

## 📝 Next Steps

1. **Add Icons**: Create and add icon files to `/assets`
2. **Connect Backend**: Update API endpoints in `scripts/api.js`
3. **Email Integration**: Implement email extraction from Gmail/Outlook
4. **Logs Page**: Create `logs.html` for viewing scan history
5. **Error Handling**: Add comprehensive error handling
6. **Testing**: Add unit tests for core functions

## 🔒 Permissions

The extension requires:
- `activeTab`: To interact with the current tab
- `scripting`: To inject scripts if needed
- `storage`: To save user settings

## 📄 License

This is a frontend implementation for Phisher Zero. Connect it to your backend API to enable full functionality.

