#Storage Utilization Monitor

## Overview

PMC Storage Utilization Monitor is a web application designed to monitor and display storage utilization across networked volumes. This tool provides real-time visualization of storage metrics including used space, free space, and utilization percentages across different storage categories.

**Created without prior coding experience using AI assistance (ChatGPT 4.0 and Claude 3.7 Sonnet)**

## Key Features

- **Real-time Storage Monitoring**: Track storage utilization across multiple mounted volumes
- **Categorized Storage Views**: Separate views for general, critical, RaySync, LucidLink, Curator, and defunct volumes
- **Critical Utilization Alerts**: Highlight storage volumes reaching critical capacity (>90%)
- **Filterable Data**: Filter storage information by mountpoint 
- **Auto-refresh Capability**: Toggle automatic page refreshes for real-time updates
- **Data Export**: Download storage utilization data as CSV
- **Volume Mount Refresh**: Authenticated users can refresh SMB mounts directly from the interface

## Technologies Used

- **Backend**: Python with Flask framework
- **Frontend**: HTML, CSS, JavaScript
- **Storage Analysis**: psutil Python library
- **Data Presentation**: jQuery DataTables
- **Authentication**: Basic credential verification for admin functions
- **Networking**: SMB mount integration via shell scripts

## System Requirements

- Python 3.6+
- Flask
- psutil
- Linux-based OS (for SMB mounting functionality)
- Network access to SMB shares

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/pmc-storage-monitor.git
cd pmc-storage-monitor
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install flask psutil
```

### 4. Configure SMB credentials

Create a credentials file at `/path-to-your/smb_credentials` (or modify the path in `auto_mount_smb.sh`):

```
username=your_smb_username
password=your_smb_password
domain=your_domain
```

Ensure this file has appropriate permissions:

```bash
chmod 600 /path-to-your/smb_credentials
```

### 5. Run the application

```bash
python storagemonitor.py
```

By default, the application runs on port 7443. Access it at http://localhost:7443

## Project Structure

- `storagemonitor.py` - Main Flask application with storage monitoring logic
- `auto_mount_smb.sh` - Shell script to refresh SMB mounts
- `templates/index.html` - Frontend template for the web interface
- `static/` - (Not included in provided files) Directory for static assets

## How It Works

1. The Flask application collects storage data using the psutil library
2. Storage volumes are categorized based on their mount points and utilization
3. The web interface displays this data in organized, sortable tables
4. Users can filter data, export to CSV, or refresh mounts with proper authentication

## Customization

### Modifying Storage Categories

In `storagemonitor.py`, the `categorize_storage_data` function sorts volumes into categories based on mount point naming. Modify the categorization logic to suit your storage naming conventions:

```python
def categorize_storage_data(storage_data):
    # Example: volumes with mount points starting with "DATA" 
    data_volumes = [d for d in storage_data if d['mountpoint'].split('/')[-1].startswith("DATA")]
    
    # Add your custom categories here
```

### Changing Authentication

Update the credentials check in the `refresh_mounts` function to use your preferred authentication method:

```python
if username != "your_username" or password != "your_password":
    return {"success": False, "message": "Invalid credentials"}, 401
```

## Security Considerations

- **Credentials**: The current implementation includes hardcoded credentials in the Python file. For production use, implement proper authentication systems.
- **Permissions**: Ensure appropriate file permissions for scripts that handle credentials.
- **Network Access**: Limit access to the application through proper firewall rules.

## Future Enhancements

- Email alerts for critical storage utilization
- Historical usage tracking and trends analysis
- User authentication system with role-based access
- Additional storage metrics (I/O performance, access frequency)
- Dark mode interface option

## License

## Acknowledgments

- This project was created with assistance from AI tools (ChatGPT 4.0 and Claude 3.7 Sonnet)
- Built with zero prior coding experience as a learning project
- Special thanks to Flask, psutil, and DataTables projects for their excellent libraries

---

*Note: This project is for educational purposes and demonstrates how AI assistants can help non-programmers create functional software solutions.*
