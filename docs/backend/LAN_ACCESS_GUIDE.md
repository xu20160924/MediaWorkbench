# 📱 LAN Access Guide - Access from Phone

## 🎯 Quick Setup

### 1. Start the Servers

**Backend (Terminal 1):**
```bash
cd backend
python app.py
```
✅ Backend will run on: `http://0.0.0.0:5001`

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```
✅ Frontend will run on: `http://0.0.0.0:3777`

### 2. Find Your Computer's IP Address

**On Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Or go to: **System Preferences > Network** and look for your IP address.

Example: `192.168.1.100`

### 3. Access from Phone

Make sure your phone is on the **same WiFi network** as your computer.

**Open in phone browser:**
```
http://YOUR_COMPUTER_IP:3777
```

Example: `http://192.168.1.100:3777`

---

## 📸 Mobile Features

### ✅ Optimized for Phone:

1. **Touch-Friendly Buttons**
   - All buttons are minimum 44px height
   - Easy to tap with fingers

2. **Responsive Layouts**
   - Image grid adapts to screen size
   - 2 columns on portrait phones
   - 3-4 columns on tablets

3. **Mobile Image Upload**
   - Take photos directly with camera
   - Upload from gallery
   - Drag and drop support
   - **Auto-save to default directory**: Images are automatically copied to the default directory configured for their type

4. **Image Preview**
   - Full-screen preview modal
   - Pinch to zoom
   - Swipe friendly controls

5. **Auto-Save to Default Locations**
   - When you upload/paste an image, it's automatically:
     - ✅ Saved to the upload folder (`/upload/images/`)
     - ✅ **Copied to the default directory** (if configured for that image type)
     - ✅ Stored in database with both paths
   - Example: Upload a "广告规则" image → Auto-copied to your configured directory

### 📱 Screen Breakpoints:

- **Phone (Portrait):** < 480px - 2 column grid
- **Phone (Landscape) / Small Tablet:** 480px - 768px - 3-4 column grid  
- **Tablet:** 768px - 1024px - Optimized layouts
- **Desktop:** > 1024px - Full features

---

## 🔧 Troubleshooting

### Phone Can't Connect?

1. **Check same WiFi network**
   - Computer and phone must be on same network
   - Not cellular data

2. **Check firewall**
   ```bash
   # Mac: Allow incoming connections
   System Preferences > Security & Privacy > Firewall > Firewall Options
   ```

3. **Verify servers are running**
   - Backend on port 5001
   - Frontend on port 3777

4. **Try accessing from computer first**
   ```
   http://localhost:3777
   ```

### Upload Not Working?

- Check backend server logs
- Verify upload directory permissions
- Ensure file size within limits

---

## 🌐 Configuration Files Modified

### Frontend: `vite.config.ts`
```typescript
server: {
  host: '0.0.0.0',  // Allow LAN access
  port: 3777,
  proxy: {
    '^/api': {
      target: 'http://127.0.0.1:5001',
      changeOrigin: true,
    }
  }
}
```

### Backend: `app.py`
```python
if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(debug=False, host='0.0.0.0', port=port)
```

---

## 🎨 Mobile UI Improvements

### ImageManagement.vue
- 2-column grid on small phones
- Touch-friendly controls
- Responsive filters
- Full-width buttons on mobile

### ParticipationProcess.vue
- Adaptive step indicator
- Mobile-optimized image preview
- Touch-friendly edit buttons
- Full-width action buttons

### Image Preview Modal
- 90vw × 90vh size
- Stacked controls on mobile
- Easy zoom and rotate
- Swipe to close

---

## 📲 Recommended Phone Browsers

- **iOS:** Safari (best compatibility)
- **Android:** Chrome (best compatibility)
- Both support modern web features

---

## 🔒 Security Note

This setup allows access from your local network only. The servers are bound to `0.0.0.0` which means:
- ✅ Accessible from LAN devices
- ❌ NOT accessible from internet
- ✅ Firewall protected

For internet access, you would need additional configuration (port forwarding, HTTPS, authentication).

---

## 💡 Tips

1. **Add to Home Screen**
   - iOS: Safari > Share > Add to Home Screen
   - Android: Chrome > Menu > Add to Home Screen
   - Creates app-like experience!

2. **Keep Computer Awake**
   ```bash
   # Mac: Prevent sleep while servers running
   caffeinate -u -t 36000
   ```

3. **Bookmark the URL**
   - Save `http://YOUR_IP:3777` for quick access

---

## 📞 Quick Reference

| Item | Value |
|------|-------|
| Frontend Port | 3777 |
| Backend Port | 5001 |
| Access URL | http://YOUR_IP:3777 |
| Network | Same WiFi/LAN |
| Mobile Optimized | ✅ Yes |

---

**Last Updated:** 2025-01-17
**Status:** ✅ Ready for Mobile Access
