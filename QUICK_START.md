# Quick Start Guide

## For Raspberry Pi Setup (Headless - No Display Needed)

### Step 1: Prepare Your Raspberry Pi

1. **Enable SSH** on your Raspberry Pi (if not already enabled)
2. **Connect Pi to your network** (WiFi or Ethernet)
3. **Find the Pi's IP address** (check your router or use `hostname -I` via SSH)

### Step 2: Transfer and Setup

From your Windows laptop:

```powershell
# Transfer files to Raspberry Pi
scp -r "c:\Users\Julius\Documents\VsCode\Capstone" pi@<PI_IP>:/home/pi/

# SSH into the Pi
ssh pi@<PI_IP>

# Run the setup script
cd /home/pi/Capstone/backend
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
```

The script will:
- ✅ Install all dependencies
- ✅ Configure auto-start on boot
- ✅ Start the server immediately

### Step 3: Access from Your Laptop

1. **Open your browser** on your laptop

2. **Go to one of these:**
   - **Best:** `http://raspberrypi.local:8000` (uses hostname - IP changes don't matter!)
   - **Alternative:** `http://<PI_IP>:8000` (e.g., `http://192.168.1.100:8000`)

3. **You'll see the initialization page:**
   - Enter `raspberrypi.local` (or Pi's IP) in the text field
   - Click "Connect to Raspberry Pi"
   - Wait for all status indicators to turn green ✓

4. **Click "Start Detection System"**
   - You'll be taken to the detection interface

5. **Click "Start Detection"** on the detection page
   - Camera feed will appear
   - Pose detection will start in real-time

### 💡 Pro Tip: Dealing with Changing IPs

**Problem:** Raspberry Pi IP might change on reboot

**Solution 1 (Easiest):** Use the hostname
- Just use `raspberrypi.local` instead of IP address
- Works automatically, no setup needed!

**Solution 2:** Set a static IP on your Pi
- See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for instructions

### Step 4: Enjoy!

Now your system is fully operational:
- ✅ Pi runs headless (no display needed)
- ✅ Server auto-starts on boot
- ✅ Control everything from your laptop
- ✅ View camera feed and detections remotely

## Daily Usage (After Setup)

Once everything is set up:

1. **Power on the Raspberry Pi** (that's it! Server starts automatically)
2. **On your laptop**, open browser: `http://raspberrypi.local:8000`
3. **Click "Connect to Raspberry Pi"** (address is saved from last time)
4. **Click "Start Detection System"**
5. **Click "Start Detection"** to begin

**💡 Remember:** Use `raspberrypi.local` so you don't worry about IP changes!

## Troubleshooting

### Can't connect from laptop?

- Check that Pi is powered on
- Verify IP address hasn't changed: `ssh pi@raspberrypi.local` then `hostname -I`
- Check firewall: `sudo ufw allow 8000`

### Check if server is running:

```bash
ssh pi@<PI_IP>
sudo systemctl status yolov8-detection.service
```

### View logs:

```bash
# Service logs
sudo journalctl -u yolov8-detection.service -f

# Startup logs
cat /home/pi/Capstone/logs/startup.log
```

### Restart the service:

```bash
sudo systemctl restart yolov8-detection.service
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR LAPTOP                                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Browser: http://192.168.1.100:8000                    │ │
│  │  - Enter Pi IP                                         │ │
│  │  - Connect and check status                            │ │
│  │  - View camera feed                                    │ │
│  │  - Control detection                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Network (WiFi/Ethernet)
                           │
┌─────────────────────────▼─────────────────────────────────────┐
│  RASPBERRY PI (Headless - No Display)                         │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  Backend Server (Auto-starts on boot)                    ││
│  │  - FastAPI on port 8000                                  ││
│  │  - YOLOv8 pose detection                                 ││
│  │  - Camera capture                                        ││
│  │  - WebSocket streaming                                   ││
│  └──────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────┐│
│  │  USB Camera                                              ││
│  └──────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
```

## Key Features

- 🔌 **Plug & Play**: Just power on the Pi, connect from laptop
- 🖥️ **Headless**: No monitor/keyboard needed on Pi
- 🌐 **Remote Access**: Control from any device on the network
- 🔄 **Auto-Start**: Server starts automatically on boot
- 💾 **Auto-Save**: Pi IP address saved in browser for quick reconnect
- 📊 **Real-Time**: Live camera feed and pose detection
- 📝 **Logging**: Detection events automatically logged

## Next Steps

- See [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for detailed setup instructions
- See [README.md](README.md) for API documentation and architecture details
