# 📱 Troubleshooting Phone Access

## Step 1: Verify Server is Running

### Check Frontend Server
```bash
cd frontend
npm run dev
```

**Look for these lines in the output:**
```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:3777/
➜  Network: http://192.168.x.x:3777/
➜  press h to show help
```

**Important:** You should see a "Network:" line with your actual IP address!

If you DON'T see the "Network:" line, the server isn't binding to 0.0.0.0 properly.

---

## Step 2: Find Your Mac's IP Address

Run this command:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Example output:
```
```

Your IP is: **192.168.1.100**

Or check in System Preferences:
1. Go to **System Preferences > Network**
2. Select your WiFi connection
3. Note the IP address shown

---

## Step 3: Verify Both Servers are Running

### Terminal 1 - Backend (should be running)
```bash
cd backend
python app.py
```

Should show:
```
* Running on http://0.0.0.0:5001
```

### Terminal 2 - Frontend (should be running)
```bash
cd frontend
npm run dev
```

Should show network URL with your IP.

---

## Step 4: Test from Your Computer First

Before trying phone, test locally:

### Test Backend:
```bash
curl http://localhost:5001/api/health
```

Should return: `{"status": "ok"}`

### Test Frontend in Browser:
1. Open: `http://localhost:3777`
2. Should load the app

---

## Step 5: Check Firewall Settings

### Option A: Allow Incoming Connections
```bash
# Check if firewall is on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# If it says "enabled", you need to allow Node
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/node
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/bin/node
```

### Option B: Temporarily Disable Firewall (Testing Only)
1. System Preferences > Security & Privacy
2. Firewall tab
3. Click lock to make changes
4. Turn off firewall temporarily
5. Test phone access
6. Turn firewall back on after testing

---

## Step 6: Verify Phone is on Same WiFi

**On your phone:**
1. Go to WiFi settings
2. Verify connected to **same network** as your Mac
3. Note the IP range (should be similar to Mac's IP)

Example:
- Mac: 192.168.1.100
- Phone: 192.168.1.XXX (same first 3 numbers)

---

## Step 7: Try Accessing from Phone

### In phone browser:
```
http://YOUR_MAC_IP:3777
```

Example:
```
http://192.168.1.100:3777
```

---

## Common Issues & Solutions

### Issue 1: "Network:" URL not showing in Vite output
**Solution:** Vite config might not be loaded. Try:
```bash
cd frontend
rm -rf node_modules/.vite
npm run dev
```

### Issue 2: Connection refused
**Causes:**
- Backend not running (frontend needs backend for API calls)
- Firewall blocking
- Wrong IP address

**Solution:**
```bash
# Make sure both servers are running
# Terminal 1
cd backend && python app.py

# Terminal 2  
cd frontend && npm run dev
```

### Issue 3: Phone shows "Can't connect"
**Solutions:**
1. Verify IP address is correct
2. Try http:// not https://
3. Make sure both devices on same WiFi
4. Restart phone WiFi
5. Check firewall settings

### Issue 4: Page loads but images/API don't work
**Cause:** Backend not accessible

**Solution:** 
Backend must also bind to 0.0.0.0 (already configured in app.py)
```python
app.run(debug=False, host='0.0.0.0', port=5001)
```

---

## Quick Test Script

Save this as `test_connection.sh` and run it:

```bash
#!/bin/bash

echo "=== Testing LAN Access ==="
echo ""

# Get IP
echo "1. Your Mac's IP address:"
ifconfig | grep "inet " | grep -v 127.0.0.1
echo ""

# Test backend
echo "2. Testing backend (port 5001):"
curl -s http://localhost:5001/api/health || echo "❌ Backend not responding"
echo ""

# Check if frontend is running
echo "3. Testing frontend (port 3777):"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3777 || echo "❌ Frontend not responding"
echo ""

# Check firewall
echo "4. Firewall status:"
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
echo ""

echo "=== Instructions ==="
echo "If all tests pass:"
echo "1. Note your IP address from step 1"
echo "2. On your phone, visit: http://YOUR_IP:3777"
echo ""
echo "If tests fail:"
echo "- Start backend: cd backend && python app.py"
echo "- Start frontend: cd frontend && npm run dev"
```

Run with:
```bash
chmod +x test_connection.sh
./test_connection.sh
```

---

## Manual Verification Checklist

- [ ] Backend running on 0.0.0.0:5001
- [ ] Frontend running on 0.0.0.0:3777
- [ ] Vite shows "Network:" URL in output
- [ ] Mac and phone on same WiFi network
- [ ] Firewall allows connections or is temporarily disabled
- [ ] Using correct IP address (not localhost)
- [ ] Using http:// (not https://)
- [ ] Backend API responding to http://localhost:5001/api/health

---

## Still Not Working?

### Try these commands:

```bash
# Kill any existing processes on these ports
lsof -ti:3777 | xargs kill -9
lsof -ti:5001 | xargs kill -9

# Restart both servers
cd backend && python app.py &
cd frontend && npm run dev
```

### Check what's listening:
```bash
netstat -an | grep LISTEN | grep -E '3777|5001'
```

Should show:
```
tcp4  0  0  *.3777   *.*   LISTEN
tcp4  0  0  *.5001   *.*   LISTEN
```

The `*` means it's bound to all interfaces (0.0.0.0) ✅

If you see `127.0.0.1` instead of `*`, the server is only listening locally ❌

---

## Contact Info

If still having issues, provide:
1. Output of `npm run dev`
2. Output of `ifconfig | grep inet`
3. Phone's WiFi network name
4. Mac's WiFi network name
5. Firewall status

Good luck! 🍀
