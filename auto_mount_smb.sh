postit@monitoringserver01:/scripts$ cat auto_mount_smb.sh
#!/bin/bash
# Server and authentication details
SERVER="<IP OF YOUR SERVER>"
CREDENTIALS_FILE="/path-to-your/smb_credentials"
MOUNT_ROOT="/mnt"

echo "====================="
echo "Starting SMB Automount"
echo "====================="

# 1. Unmount all volumes under /mnt/ using the direct approach
echo "Unmounting all volumes under /mnt/..."
sudo umount -f ${MOUNT_ROOT}/* 2>/dev/null || true
echo "Unmount process complete."

# 2. Clear existing SMB-related entries in /etc/fstab
echo "Clearing existing SMB mount entries from /etc/fstab..."
sudo sed -i '/cifs/d' /etc/fstab
echo "All SMB mount entries cleared from /etc/fstab."

# 3. Fetch the list of SMB shares
echo "Fetching available shares from $SERVER..."
SHARES=$(smbclient -L "$SERVER" -A "$CREDENTIALS_FILE" --option='client max protocol=SMB3' 2>/dev/null | awk '/Disk/ {print $1}')
if [ -z "$SHARES" ]; then
    echo "No SMB shares found or access denied!"
    exit 1
fi

# Display available shares for debugging
echo "Available shares from server:"
for SHARE in $SHARES; do
    echo "- $SHARE"
done

# 4. Process each available share
echo "Processing available SMB shares..."
# Backup /etc/fstab before adding new entries
sudo cp /etc/fstab /etc/fstab.bak

for SHARE in $SHARES; do
    # Skip admin/hidden shares (ending with $)
    if [[ "$SHARE" =~ .*\$$ ]]; then
        echo "Skipping hidden/admin share: $SHARE"
        continue
    fi

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
    echo "Added $SHARE to /etc/fstab."
done

# 5. Mount everything in fstab
echo "Mounting all SMB shares listed in /etc/fstab..."
sudo mount -a

# 6. Final cleanup of any stray mounts
echo "Performing final cleanup of any stray mounts..."
# Check for any admin shares that might have been mounted
for MOUNT_POINT in $(mount | grep cifs | awk '{print $2}' | grep '\$'); do
    if [[ "$MOUNT_POINT" == "$MOUNT_ROOT"* ]]; then
        echo "Force unmounting admin share at $MOUNT_POINT..."
        sudo umount -f "$MOUNT_POINT"
    fi
done

# 7. Show results
echo
echo "Currently mounted SMB shares:"
df -h | grep "$MOUNT_ROOT"
echo
echo "====================="
echo "All SMB shares processed!"
echo "====================="
