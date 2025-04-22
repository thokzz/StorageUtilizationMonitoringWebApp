# Technical Deep Dive: Storage Utilization Monitor

This document provides a technical explanation of how the Storage Utilization Monitor works. Created by a non-programmer with AI assistance, the system demonstrates how modern AI tools can help bridge the technical knowledge gap.

## System Architecture

The application follows a simple client-server architecture:

```
┌─────────────┐     HTTP     ┌─────────────┐    Python    ┌─────────────┐
│   Browser   │ ──────────── │  Flask App  │ ──────────── │ File System │
└─────────────┘              └─────────────┘              └─────────────┘
                                    │                            │
                                    │                            │
                                    ▼                            ▼
                             ┌─────────────┐            ┌─────────────┐
                             │    CSV      │            │ SMB Shares  │
                             │   Export    │            │             │
                             └─────────────┘            └─────────────┘
```

## Backend Components

### 1. Flask Web Application (`storagemonitor.py`)

The core of the system is a Python Flask application that handles:

- HTTP request routing
- Storage data collection and processing
- Template rendering
- Authentication for admin functions
- CSV generation

#### Key Functions

- **`get_storage_data()`**: Collects raw storage metrics using the psutil library
- **`categorize_storage_data()`**: Organizes storage volumes into logical categories
- **`refresh_mounts()`**: Handles authenticated requests to refresh network mounts
- **`index()`**: Main route that renders the dashboard with all storage data
- **`download_csv()`**: Generates and serves CSV exports of storage data

### 2. Network Mount Script (`auto_mount_smb.sh`)

A Bash script that manages SMB/CIFS network mounts:

- Unmounts existing volumes
- Cleans up stale mount entries
- Fetches available SMB shares
- Creates mount points
- Updates /etc/fstab with mount information
- Mounts all available shares

#### Security Considerations

- Uses a separate credentials file
- Requires authentication before execution
- Implements proper error handling
- Uses secure file permissions

## Frontend Components

### 1. Main Dashboard (`index.html`)

The dashboard is built with modern HTML5, CSS3, and JavaScript:

- Responsive design that works on various screen sizes
- Tab-based interface for categorized storage data
- DataTables integration for sortable, filterable tables
- Auto-refresh functionality with countdown timer
- Modal-based authentication for admin functions

### 2. Storage Visualization

Storage utilization is visualized through:

- Color-coded table rows based on utilization percentage
- Utilization badges with consistent color indicators
- Tooltips for long device/mount paths
- Summary statistics at the top of the dashboard

### 3. JavaScript Features

- Tab switching with state persistence (localStorage)
- Authentication modal handling
- Auto-refresh toggle with countdown
- DataTables initialization and configuration
- Mount refresh AJAX request handling

## Data Flow

1. **Data Collection**: The Flask application uses psutil to gather storage information
2. **Data Processing**: 
   - Raw storage data is transformed into TB measurements
   - Volumes are categorized based on mount point naming patterns
   - Utilization percentages are calculated
   - Critical volumes (>90% utilized) are identified
3. **Data Presentation**:
   - Jinja2 templates render the processed data
   - JavaScript enhances the UI with interactivity
   - DataTables provides sorting and filtering capabilities
4. **User Interaction**:
   - Users can filter data by mount point
   - Users can download data as CSV
   - Authenticated users can refresh network mounts

## Code Highlights

### Storage Data Collection

```python
def get_storage_data():
    storage_info = []
    for partition in psutil.disk_partitions(all=True):
        if not partition.mountpoint.startswith("/mnt/"):
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            # Use decimal TB (1 TB = 1000^4 bytes)
            total_tb = usage.total / (1000**4)
            used_tb = usage.used / (1000**4)
            free_tb = usage.free / (1000**4)
            utilization = (used_tb / total_tb) * 100 if total_tb > 0 else 0
            storage_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "total_tb": total_tb,
                "used_tb": used_tb,
                "free_tb": free_tb,
                "utilization": utilization
            })
        except PermissionError:
            continue
    storage_info.sort(key=lambda x: x["mountpoint"])
    return storage_info
```

### Storage Categorization

```python
def categorize_storage_data(storage_data):
    curator_data = [d for d in storage_data if d['mountpoint'].split('/')[-1].startswith("AMS")]
    raysync_data = [d for d in storage_data if d['mountpoint'].split('/')[-1].startswith("PMC_RAYSYNC_") and "PMC_RAYSYNC_ROOT" not in d['mountpoint']]
    lucid_data = [d for d in storage_data if d['mountpoint'].split('/')[-1].startswith("LUCID") and "LUCID_ROOT" not in d['mountpoint']]
    defunct_data = [d for d in storage_data if d['mountpoint'].split('/')[-1].startswith("DEFUNCT")]

    grouped_mounts = {d['mountpoint'] for d in curator_data + raysync_data + lucid_data}
    general_data = [d for d in storage_data if d['mountpoint'] not in grouped_mounts]

    critical_data = sorted(
        [d for d in general_data if d['utilization'] >= 91],
        key=lambda x: x['utilization'],
        reverse=True
    )

    general_data.sort(key=lambda x: x['mountpoint'])

    return {
        'curator_data': curator_data,
        'raysync_data': raysync_data,
        'lucid_data': lucid_data,
        'defunct_data': defunct_data,
        'general_data': general_data,
        'critical_data': critical_data
    }
```

### Authentication for Mount Refresh

```python
@app.route('/refresh_mounts', methods=['POST'])
def refresh_mounts():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return {"success": False, "message": "Missing username or password"}, 400

        username = data['username']
        password = data['password']

        if username != "<YOURUSER>" or password != "<YOURPASSWORD>":
            return {"success": False, "message": "Invalid credentials"}, 401

        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write(f"{password}\n")
            temp_path = temp.name

        try:
            cmd = f"cd /scripts && cat {temp_path} | sudo -S ./auto_mount_smb.sh"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
        finally:
            os.unlink(temp_path)

        if process.returncode != 0:
            return {"success": False, "message": f"Error refreshing mounts: {stderr.decode()}"}, 500

        return {"success": True, "message": "Volume mounts refreshed successfully"}, 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Error: {str(e)}"}, 500
```

## Technical Implementation Details

### Decimal TB Calculation

The application uses decimal terabytes (1 TB = 1000^4 bytes) rather than binary terabytes (1 TiB = 1024^4 bytes) for consistency with how storage hardware is typically marketed.

```python
total_tb = usage.total / (1000**4)
used_tb = usage.used / (1000**4)
free_tb = usage.free / (1000**4)
```

### Auto-Refresh Implementation

The auto-refresh functionality uses two approaches:

1. A meta refresh tag for actual page reloading:
```javascript
refreshMetaTag = document.createElement('meta');
refreshMetaTag.setAttribute('http-equiv', 'refresh');
refreshMetaTag.setAttribute('content', '15');
document.head.appendChild(refreshMetaTag);
```

2. A JavaScript interval for the countdown display:
```javascript
refreshTimer = setInterval(() => {
    countdown--;
    if (countdown <= 0) countdown = 15;
    if (refreshToggle.checked) {
        refreshStatus.textContent = `Auto-refresh is enabled (${countdown}s)`;
    }
}, 1000);
```

### SMB Share Discovery

Rather than hardcoding mount points, the system dynamically discovers available SMB shares:

```bash
SHARES=$(smbclient -L "$SERVER" -A "$CREDENTIALS_FILE" --option='client max protocol=SMB3' 2>/dev/null | awk '/Disk/ {print $1}')
```

### Mount Point Creation and Management

The system handles mounting by:

1. Removing existing mounts
2. Cleaning fstab entries
3. Creating needed mount points
4. Adding to fstab
5. Remounting everything

```bash
# Prepare mount point
SAFE_SHARE=$(echo "$SHARE" | tr ' ' '_')
MOUNT_POINT="${MOUNT_ROOT}/${SAFE_SHARE}"

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    sudo mkdir -p "$MOUNT_POINT"
    echo "Created mount point: $MOUNT_POINT"
fi

# Add to /etc/fstab
echo "//${SERVER}/${SHARE} $MOUNT_POINT cifs credentials=$CREDENTIALS_FILE,uid=1000,gid=1000,vers=3.0 0 0" | sudo tee -a /etc/fstab
```

## Security Analysis

### Current Security Measures

- **Authentication**: Basic username/password for mount refresh
- **Credential Handling**: External credential file for SMB shares
- **Error Handling**: Proper exception handling and error reporting
- **Input Validation**: Basic validation on incoming data

### Security Improvement Opportunities

- **HTTPS**: Add TLS/SSL for encrypted communication
- **Stronger Authentication**: Implement proper session-based authentication
- **Parameter Sanitization**: Add more robust input validation
- **Secrets Management**: Move credentials to environment variables or secrets manager
- **Audit Logging**: Add logging for security-relevant events

## Performance Considerations

- The application is lightweight and should perform well on modest hardware
- Auto-refresh interval (15s) provides a balance between freshness and server load
- No database is required, reducing complexity and resource requirements
- DataTables handles client-side sorting and filtering efficiently

## AI Development Methodology

As a non-programmer creating this application with AI assistance:

1. **Problem Definition**: Clearly defined the storage monitoring requirements
2. **Component Planning**: Broke down the system into manageable parts
3. **Iterative Development**: Built each component with AI guidance
4. **Learning Focus**: Asked for explanations of code and concepts
5. **Integration**: Combined components into a cohesive application
6. **Testing**: Verified functionality with real-world data
7. **Refinement**: Improved the application based on testing results

## Conclusion

The Storage Utilization Monitor demonstrates that complex, practical applications can be developed by non-programmers with AI assistance. By understanding the problem domain and breaking it into manageable components, it's possible to build sophisticated solutions that address real-world needs.

---

*This technical documentation was created by a non-programmer with assistance from AI tools (ChatGPT 4.0 and Claude 3.7 Sonnet).*
