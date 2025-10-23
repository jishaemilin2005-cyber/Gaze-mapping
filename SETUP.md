# Setup Instructions

## Prerequisites

- Python 3.7 or higher
- Node.js (for npm scripts, optional)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Webcam or OBS Virtual Camera

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python numpy
```

### 2. Verify Installation

```bash
python3 -c "import cv2, numpy; print('✅ Dependencies installed')"
```

### 3. Test the Tracker

```bash
python3 test_tracker.py
```

This will:
- Open your camera (OBS or webcam)
- Run a 5-point calibration
- Start the tracking loop with visualization

**Controls:**
- `q`: Quit
- `r`: Reset tracker
- `c`: Recalibrate

## Running the Web Application

### Option 1: Simple HTTP Server (Python)

```bash
npm run dev
# or
python3 -m http.server 8000
```

Then open: http://localhost:8000

### Option 2: Any Static Server

The project is pure HTML/JS/CSS, so any static file server works:
```bash
# Using Node.js http-server
npx http-server -p 8000

# Using PHP
php -S localhost:8000

# Using Ruby
ruby -run -ehttpd . -p8000
```

## Project Structure

```
project/
├── index.html              # Landing page
├── study.html              # Optimized study page with preloader
├── demo_tracker.html       # Demo/documentation page
├── results.html            # Results page
├── webgazer.js            # WebGazer library
├── requirements.txt        # Python dependencies
├── test_tracker.py        # Tracker test script
├── package.json           # npm scripts
│
├── src/
│   ├── vision/            # Python eye tracker modules
│   │   ├── __init__.py
│   │   ├── eye_only_tracker.py
│   │   ├── gaze_map.py
│   │   ├── camera_capture.py
│   │   └── config.json
│   └── frontend/
│       └── composables/
│           └── usePreloadImages.ts
│
├── js/                    # JavaScript files
│   ├── calibration.js
│   ├── main.js
│   └── ...
│
├── css/                   # Stylesheets
│   ├── intro.css
│   ├── style.css
│   └── ...
│
└── data/                  # Output data (auto-created)
```

## Configuration

### Python Tracker Configuration

Edit `src/vision/config.json` to tune parameters:

```json
{
  "tracker": {
    "thresh_block": 15,      // Adaptive threshold block size
    "thresh_c": 7,           // Adaptive threshold constant
    "min_pupil_area": 80,    // Minimum pupil contour area
    "smooth_window": 5,      // Moving average window size
    "roi_half_size": 90      // ROI search box half-size
  }
}
```

### Web Application Configuration

Edit `study.html` to customize study images:

```javascript
let imageUrls = [
  'demo.jpeg',
  'calibration.jpg',
  'result.png',
  'blank.png'
];
```

## Troubleshooting

### Camera Not Opening

**Problem:** `Cannot open camera` error

**Solutions:**
1. Check if camera is in use by another application
2. Try different source: `CameraCapture(source="obs")` or `CameraCapture(source="cam")`
3. On Linux, check permissions: `sudo chmod 666 /dev/video0`
4. Verify camera device: `ls /dev/video*` (Linux) or Device Manager (Windows)

### No Pupil Detection

**Problem:** Detection rate is 0% or very low

**Solutions:**
1. Improve lighting (not too bright or dark)
2. Check camera focus
3. Adjust `thresh_block` and `thresh_c` in config.json
4. Lower `min_pupil_area` (try 40-60)
5. Disable CLAHE: `use_clahe: false`

### Poor Calibration

**Problem:** Gaze mapping is inaccurate

**Solutions:**
1. Keep head stable during calibration
2. Look directly at each target point
3. Ensure good pupil detection during calibration (>10 samples per point)
4. Recalibrate with better lighting
5. Increase calibration sample duration (edit `camera_capture.py`)

### Study Page Images Not Loading

**Problem:** Images show as broken or don't preload

**Solutions:**
1. Verify image paths in `imageUrls` array
2. Check images exist in project directory
3. Check browser console for errors
4. Ensure server is running and accessible
5. Clear browser cache and reload

### WebGazer Not Working

**Problem:** WebGazer fails to initialize or track

**Solutions:**
1. Check browser console for errors
2. Allow camera permissions when prompted
3. Use HTTPS (WebGazer requires secure context)
4. Try different browser (Chrome recommended)
5. Update WebGazer: download latest from GitHub

## Performance Optimization

### For Low-End Systems

1. Reduce frame resolution:
   ```python
   capture = CameraCapture(resize_max_h=480)
   ```

2. Increase ROI size (less full-frame searches):
   ```json
   "roi_half_size": 120
   ```

3. Reduce smoothing window:
   ```json
   "smooth_window": 3
   ```

### For High Accuracy

1. Increase smoothing:
   ```json
   "smooth_window": 10
   ```

2. Fine-tune thresholding for your lighting:
   - Run test script and adjust trackbars in real-time
   - Note optimal values
   - Update config.json

3. Use higher resolution camera

## Camera Sources

### OBS Virtual Camera

Recommended for best results:
1. Install OBS Studio
2. Add video capture device
3. Start Virtual Camera
4. Run tracker (auto-detects OBS)

### Physical Webcam

Works with any USB webcam:
```python
capture = CameraCapture(source="cam")
```

### ESP32-CAM (IP Camera)

Not directly integrated with Python tracker, but can be added:
1. Update `camera_capture.py` to support IP streams
2. Use OpenCV's VideoCapture with MJPEG URL
3. Or use the existing `rough3.py` IP camera code

## Development

### Running Tests

```bash
# Test tracker
python3 test_tracker.py

# Test web app
npm run dev
```

### Building

```bash
npm run build
```

This is a static site, so "build" just verifies files are ready.

### Adding New Features

1. **New tracker parameters:** Add to `config.json` and `EyeOnlyTracker.__init__()`
2. **New calibration points:** Edit `camera_capture.py` `calibrate_pupil_only()` method
3. **New study images:** Add to `imageUrls` array in `study.html`

## Support

For issues or questions:
1. Check IMPLEMENTATION_NOTES.md for technical details
2. Review browser/terminal console for errors
3. Verify dependencies are installed correctly
4. Test with the demo tracker page first

## License

See LICENSE file for details.
