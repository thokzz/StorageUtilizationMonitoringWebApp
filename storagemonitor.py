from flask import Flask, render_template, Response, request
import csv
import io
import psutil
import subprocess
import tempfile
import os
from datetime import datetime

app = Flask(__name__)

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

@app.route('/refresh_mounts', methods=['POST'])
def refresh_mounts():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return {"success": False, "message": "Missing username or password"}, 400

        username = data['username']
        password = data['password']

        print(f"Received credentials: {username}, {password}")

        if username != "<YOURUSERNAME>" or password != "<YOURPASSWORD>":
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

@app.route('/')
def index():
    storage_data = get_storage_data()
    categorized_data = categorize_storage_data(storage_data)

    mountpoint_filter = request.args.get('filter', '').strip()

    if mountpoint_filter:
        for key in categorized_data:
            categorized_data[key] = [
                d for d in categorized_data[key]
                if mountpoint_filter.lower() in d['mountpoint'].lower()
            ]

    total_used_tb = sum(d['used_tb'] for d in categorized_data['general_data'])
    total_capacity_tb = 2304.763289
    percent_utilized = (total_used_tb / total_capacity_tb) * 100 if total_capacity_tb > 0 else 0
    today = datetime.now().strftime("%B %d, %Y")

    return render_template(
        "index.html",
        critical_data=categorized_data['critical_data'],
        general_data=categorized_data['general_data'],
        curator_data=categorized_data['curator_data'],
        raysync_data=categorized_data['raysync_data'],
        lucid_data=categorized_data['lucid_data'],
        defunct_data=categorized_data['defunct_data'],
        total_used_tb=total_used_tb,
        percent_utilized=percent_utilized,
        today=today,
        current_filter=mountpoint_filter
    )

@app.route('/download')
def download_csv():
    storage_data = get_storage_data()
    categorized_data = categorize_storage_data(storage_data)

    mountpoint_filter = request.args.get('filter', '').strip()
    general_data = categorized_data['general_data']
    if mountpoint_filter:
        general_data = [
            d for d in general_data
            if mountpoint_filter.lower() in d['mountpoint'].lower()
        ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Device', 'Mountpoint', 'Quota (TB)', 'Used (TB)', 'Free (TB)', 'Utilization (%)'])

    for data in general_data:
        writer.writerow([
            data['device'],
            data['mountpoint'],
            f"{data['total_tb']:.5f}",
            f"{data['used_tb']:.5f}",
            f"{data['free_tb']:.5f}",
            f"{data['utilization']:.2f}"
        ])

    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=general_storage_utilization.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7443, debug=True)
