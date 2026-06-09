import json
import time
import urllib.request
import urllib.error

GRAFANA_URL = "http://127.0.0.1:3001"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic YWRtaW46YWRtaW4="  # admin:admin base64 encoded
}

def wait_for_grafana():
    print("Waiting for Grafana to be ready...")
    for _ in range(30):
        try:
            req = urllib.request.Request(f"{GRAFANA_URL}/api/health", headers=HEADERS)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    print(f"Grafana is ready! Version: {data.get('version')}")
                    return True
        except Exception:
            pass
        time.sleep(1)
    print("Grafana is not responding. Exiting.")
    return False

def setup_datasource():
    print("Setting up PostgreSQL DataSource...")
    datasource = {
        "name": "PostgreSQL",
        "type": "postgres",
        "access": "proxy",
        "url": "host.docker.internal:5432",
        "user": "postgres",
        "database": "thc_api",
        "basicAuth": False,
        "isDefault": True,
        "jsonData": {
            "sslmode": "disable"
        },
        "secureJsonData": {
            "password": "system"
        },
        "uid": "afodoaxjtubr4e"
    }
    
    # Check if datasource already exists
    try:
        req = urllib.request.Request(f"{GRAFANA_URL}/api/datasources/uid/afodoaxjtubr4e", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print("DataSource afodoaxjtubr4e already exists. Updating it...")
                req_update = urllib.request.Request(
                    f"{GRAFANA_URL}/api/datasources/uid/afodoaxjtubr4e",
                    data=json.dumps(datasource).encode('utf-8'),
                    headers=HEADERS,
                    method="PUT"
                )
                with urllib.request.urlopen(req_update) as resp_update:
                    print("DataSource updated successfully!")
                    return
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"Error checking datasource: {e}")
            raise
    except Exception as e:
        print(f"Error checking datasource: {e}")
        raise

    # Create new datasource
    req_create = urllib.request.Request(
        f"{GRAFANA_URL}/api/datasources",
        data=json.dumps(datasource).encode('utf-8'),
        headers=HEADERS,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req_create) as resp:
            print("DataSource created successfully!")
    except urllib.error.HTTPError as e:
        print(f"Failed to create DataSource: {e.read().decode('utf-8')}")
        raise

def import_dashboard():
    print("Importing Dashboard v2...")
    with open("docs/grafana_dashboard_thc_hunter_v2.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # The file is in Kubernetes resources format
    # Extract the dashboard spec and metadata
    spec = raw_data.get("spec", {})
    metadata = raw_data.get("metadata", {})
    
    dashboard_model = spec.copy()
    dashboard_model["uid"] = metadata.get("uid", "76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e")
    
    payload = {
        "dashboard": dashboard_model,
        "overwrite": True
    }
    
    req = urllib.request.Request(
        f"{GRAFANA_URL}/api/dashboards/db",
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"Dashboard imported successfully! Status: {result.get('status')}, URL: {result.get('url')}")
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"Failed to import dashboard: {error_msg}")
        
        # Fallback: try importing the entire raw JSON if Grafana parses it directly
        print("Retrying by posting the entire JSON with forced UID...")
        raw_data["metadata"]["name"] = "76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e"
        raw_data["metadata"]["uid"] = "76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e"
        payload_fallback = {
            "dashboard": raw_data,
            "overwrite": True
        }
        req_fallback = urllib.request.Request(
            f"{GRAFANA_URL}/api/dashboards/db",
            data=json.dumps(payload_fallback).encode('utf-8'),
            headers=HEADERS,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req_fallback) as resp_fb:
                result_fb = json.loads(resp_fb.read().decode('utf-8'))
                print(f"Dashboard imported with fallback! Status: {result_fb.get('status')}, URL: {result_fb.get('url')}")
        except urllib.error.HTTPError as e_fb:
            print(f"Fallback import also failed: {e_fb.read().decode('utf-8')}")
            raise e_fb

if __name__ == "__main__":
    if wait_for_grafana():
        setup_datasource()
        import_dashboard()
        print("Grafana provisioning completed successfully!")
