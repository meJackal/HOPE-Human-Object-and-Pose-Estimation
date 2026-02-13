# Raspberry Pi Auto-Start Setup Instructions

This guide will help you set up the YOLOv8 Pose Detection System to automatically start when your Raspberry Pi boots up, without needing a display.

## How It Works

1. **Raspberry Pi powers on** → Server automatically starts in the background (no display needed)
2. **On your laptop**, open a browser and go to the Pi's IP address
3. **Frontend connects** to the Raspberry Pi and checks system status
4. **Start detection** remotely from your laptop - view the camera feed and detections in real-time

**No HDMI cable or monitor needed for the Raspberry Pi!**

## Setup Steps

### Initial Note: Dealing with Changing IP Addresses

Raspberry Pi IP addresses can change if using DHCP. Here are two solutions:

**Option 1: Use Hostname (Easiest - Recommended)**
- Instead of IP address, use: **`raspberrypi.local`**
- Works automatically with mDNS/Bonjour
- No setup needed - just use `raspberrypi.local:8000` in your browser
- Works even when IP changes!

**Option 2: Set Static IP (More Reliable)**
- See the "Setting Static IP" section below
- Guarantees the same IP every time
- Better for production environments

### 1. Transfer Files to Raspberry Pi

Transfer your entire project folder to the Raspberry Pi. The recommended location is:
```bash
/home/pi/Capstone
```

You can use SCP, SFTP, or a USB drive to transfer the files.

### 2. Install Dependencies

SSH into your Raspberry Pi and run:

```bash
cd /home/pi/Capstone/backend

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip3 install -r requirements.txt

# Install uvicorn if not already included
pip3 install uvicorn
```

### 3. Make the Startup Script Executable

```bash
chmod +x /home/pi/Capstone/backend/start_server.sh
```

### 4. Test the Script Manually

Before setting up auto-start, test if the script works:

```bash
cd /home/pi/Capstone/backend
./start_server.sh
```

The server should start, and you should see output showing the IP address. Press `Ctrl+C` to stop it.

### 5. Install the Systemd Service

Copy the service file to the systemd directory:

```bash
sudo cp /home/pi/Capstone/backend/yolov8-detection.service /etc/systemd/system/
```

### 6. Adjust Paths in Service File (if needed)

If your project is NOT in `/home/pi/Capstone`, edit the service file:

```bash
sudo nano /etc/systemd/system/yolov8-detection.service
```

Update the paths in `WorkingDirectory` and `ExecStart` to match your actual project location.

### 7. Enable and Start the Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable yolov8-detection.service

# Start the service now
sudo systemctl start yolov8-detection.service
```

### 8. Check Service Status

```bash
# Check if the service is running
sudo systemctl status yolov8-detection.service

# View live logs
sudo journalctl -u yolov8-detection.service -f

# View startup logs
cat /home/pi/Capstone/logs/startup.log
```

## Setting Static IP (Optional but Recommended)

To prevent IP address changes, set a static IP on your Raspberry Pi:

### Method 1: Using DHCP Reservation (Easiest)

1. Log into your router's admin panel
2. Find the Raspberry Pi in connected devices
3. Set a DHCP reservation for its MAC address
4. This ensures it always gets the same IP

### Method 2: Static IP on Raspberry Pi

Edit the dhcpcd configuration:

```bash
sudo nano /etc/dhcpcd.conf
```

Add these lines at the end (adjust values for your network):

```bash
# Static IP configuration
interface eth0  # or wlan0 for WiFi
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

**Important values to check:**
- `ip_address`: Choose an IP outside your router's DHCP range
- `routers`: Your router's IP (usually 192.168.1.1 or 192.168.0.1)
- `domain_name_servers`: Your router's IP and/or Google DNS (8.8.8.8)

Save (Ctrl+X, Y, Enter) and reboot:

```bash
sudo reboot
```

After reboot, verify:

```bash
ip addr show eth0  # or wlan0
```

### Method 3: Using mDNS Hostname (No Configuration Needed!)

Raspberry Pi OS has Avahi (mDNS) enabled by default. Simply use:
- **`raspberrypi.local`** instead of the IP address

This works from:
- ✅ Windows 10/11 (built-in support)
- ✅ macOS (built-in support)
- ✅ Linux (with avahi-daemon)
- ✅ Android/iOS devices

**Advantage:** Works even when IP changes!

## Accessing the System

### From Your Laptop or Any Device on the Same Network

1. **Open a web browser on your laptop**

2. **Navigate to one of these addresses:**
   
   **Option A: Using Hostname (Recommended)**
   ```
   http://raspberrypi.local:8000
   ```
   ✅ Works even if IP changes
   ✅ No setup needed
   ✅ Easy to remember

   **Option B: Using IP Address**
   ```
   http://192.168.1.100:8000
   ```
   (Replace with your Pi's actual IP - find it with `hostname -I` on the Pi)

3. **Enter the Raspberry Pi address and connect:**
   - Type `raspberrypi.local` (or the IP address) in the input field
   - Click "Connect to Raspberry Pi"
   - Wait for all status checks to turn green ✓

4. **Start the detection system:**
   - Click "Start Detection System" button
   - You'll be taken to the detection interface
   - Click "Start Detection" to begin real-time pose detection

**Important:** The address is saved in your browser, so you only need to enter it once!

### From the Raspberry Pi Itself (if you have a display)

If you have a display connected to the Pi:
- Open a browser and go to: `http://localhost:8000`

## Managing the Service

### Stop the Service
```bash
sudo systemctl stop yolov8-detection.service
```

### Restart the Service
```bash
sudo systemctl restart yolov8-detection.service
```

### Disable Auto-Start
```bash
sudo systemctl disable yolov8-detection.service
```

### View Logs
```bash
# Service logs
sudo journalctl -u yolov8-detection.service -n 100

# Startup script logs
cat /home/pi/Capstone/logs/startup.log

# Error logs
cat /home/pi/Capstone/logs/service_error.log
```

## Troubleshooting

### raspberrypi.local Not Working

**If the hostname doesn't resolve:**

1. **Check mDNS is enabled on Pi:**
   ```bash
   sudo systemctl status avahi-daemon
   ```
   If not running:
   ```bash
   sudo systemctl start avahi-daemon
   sudo systemctl enable avahi-daemon
   ```

2. **Windows 10/11 issues:**
   - Ensure "Bonjour Service" or "mDNS" is not blocked by firewall
   - Try installing iTunes (includes Bonjour) or [Bonjour Print Services](https://support.apple.com/kb/DL999)
   - Or simply use the IP address instead

3. **Find the actual IP as fallback:**
   ```bash
   ssh pi@raspberrypi.local
   hostname -I
   ```
   Then use that IP in your browser

### IP Address Changed

If your Pi's IP address changed and you can't connect:

1. **Best solution: Use hostname instead**
   - Use `raspberrypi.local:8000` in your browser
   - This won't have IP change problems!

2. **Or set static IP** (see "Setting Static IP" section above)

3. **Or find the new IP:**
   ```bash
   # If you can still SSH using hostname
   ssh pi@raspberrypi.local
   hostname -I
   
   # Or check your router's connected devices list
   # Or use IP scanner app (Fing, Advanced IP Scanner, etc.)
   ```

4. **Clear saved address in browser:**
   - Open browser console (F12)
   - Type: `localStorage.removeItem('piIpAddress')`
   - Refresh page and enter new address

### Service Won't Start

1. Check logs for errors:
   ```bash
   sudo journalctl -u yolov8-detection.service -n 50
   ```

2. Verify Python dependencies:
   ```bash
   cd /home/pi/Capstone/backend
   source venv/bin/activate
   python3 -c "import fastapi, cv2, torch, ultralytics"
   ```

3. Check camera permissions:
   ```bash
   groups pi | grep video
   ```
   If not in video group, add it:
   ```bash
   sudo usermod -a -G video pi
   ```

### Camera Not Working

1. Check if camera is detected:
   ```bash
   ls /dev/video*
   ```

2. Test camera with:
   ```bash
   vcgencmd get_camera
   ```

3. Enable camera in raspi-config:
   ```bash
   sudo raspi-config
   # Navigate to Interface Options > Camera > Enable
   ```

### Can't Access from Other Devices

1. Check firewall settings:
   ```bash
   sudo ufw status
   ```

2. Ensure port 8000 is open:
   ```bash
   sudo ufw allow 8000
   ```

3. Verify the Raspberry Pi's IP hasn't changed:
   ```bash
   hostname -I
   ```

## File Structure

After setup, your file structure should look like:

```
/home/pi/Capstone/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── start_server.sh          (executable)
│   ├── yolov8-detection.service
│   ├── yolov8n-pose.pt
│   └── venv/                    (virtual environment)
├── frontend/
│   ├── home.html                (initialization page)
│   └── detection.html           (detection interface)
└── logs/
    ├── detections.json
    ├── startup.log
    ├── service.log
    └── service_error.log
```

## Notes

- The system will automatically restart if it crashes (configured in the service file)
- Logs are automatically rotated by systemd
- The initialization page checks system status before allowing access to detection
- The WebSocket connection automatically uses the correct IP address
- No display is required - access via network from any device
