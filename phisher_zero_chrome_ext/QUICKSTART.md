# 🚀 Quick Start Guide

## Step 1: Generate Icons (Optional but Recommended)

1. Open `assets/generate-icons.html` in your browser
2. Click "Generate Icons" 
3. Click "Download All" to save the three icon files
4. Move `icon16.png`, `icon48.png`, and `icon128.png` to the `assets/` folder

## Step 2: Load Extension in Chrome

1. Open Chrome browser
2. Navigate to `chrome://extensions/`
3. Enable **Developer mode** (toggle in top-right corner)
4. Click **"Load unpacked"**
5. Select the `phisherzero_frontend` folder
6. The extension should now appear in your extensions list

## Step 3: Test the Extension

1. Click the Phisher Zero icon in your Chrome toolbar
2. The popup should open showing:
   - Header with logo and branding
   - "Waiting to scan email" status
   - "Scan Selected Email" button
3. Click **"Scan Selected Email"** to test with mock data
4. You should see:
   - Loading animation
   - Agent breakdown with results
   - Status update (Safe or Phishing Detected)

## Step 4: Configure Settings

1. Click the **"Settings"** button in the popup
2. Or right-click the extension icon → **Options**
3. Configure:
   - **Mock Mode**: Toggle on/off (default: ON for testing)
   - **API Base URL**: Enter your backend URL when ready
4. Click **"Save Settings"**

## 🎯 Testing Features

### Mock Mode (Default)
- ✅ Works immediately without backend
- ✅ Shows random safe/phishing results
- ✅ Perfect for UI testing

### Real API Mode
1. Disable Mock Mode in settings
2. Enter your API Base URL
3. Save settings
4. The extension will call your actual backend

## 📁 File Structure

```
phisherzero_frontend/
├── manifest.json          # Extension configuration
├── popup.html/js/css      # Main UI
├── options.html/js        # Settings page
├── background.js          # Service worker
├── scripts/api.js         # API & mock data
└── assets/               # Icons folder
```

## 🔧 Next Steps

1. **Connect Backend**: Update API endpoints in `scripts/api.js`
2. **Email Integration**: Implement email extraction logic
3. **Add Logs Page**: Create `logs.html` for scan history
4. **Customize UI**: Modify Tailwind classes in HTML files

## ❓ Troubleshooting

**Extension not loading?**
- Check that all files are in the correct folders
- Verify `manifest.json` is valid JSON
- Check Chrome's error console (`chrome://extensions/` → Details → Errors)

**Icons not showing?**
- Add icon files to `assets/` folder (use generate-icons.html)
- Or ignore for now - extension works without icons

**Mock mode not working?**
- Check browser console for errors (F12)
- Verify `scripts/api.js` is loading correctly

## 🎨 UI Customization

All styling uses TailwindCSS classes. To customize:
- Colors: Change `bg-blue-600` to your preferred color
- Spacing: Adjust `p-6`, `mb-4` etc.
- Fonts: Already using Inter from Google Fonts

---

**Ready to go!** Your Phisher Zero extension is fully functional with mock data. Connect your backend when ready! 🛡️

