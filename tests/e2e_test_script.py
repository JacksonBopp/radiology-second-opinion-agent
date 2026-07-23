import httpx
import sys

API_BASE = "http://localhost:8000"
API_KEY = "dev-local-key"
DICOM_FILE_PATH = "data/raw/CT_small.dcm"

def run_e2e_test():
    print("Starting End-to-End Test...")
    headers = {"X-API-Key": API_KEY}
    
    # 1. Upload Scan
    print(f"\n1. Uploading {DICOM_FILE_PATH} to {API_BASE}/scans...")
    try:
        with open(DICOM_FILE_PATH, "rb") as f:
            files = {"file": ("CT_small.dcm", f, "application/dicom")}
            resp = httpx.post(f"{API_BASE}/scans", files=files, headers=headers, timeout=30.0)
    except FileNotFoundError:
        print(f"ERROR: {DICOM_FILE_PATH} not found. Please extract the test DICOM file first.")
        sys.exit(1)
        
    if resp.status_code != 200:
        print(f"Upload failed: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    upload_data = resp.json()
    print("Upload successful! Vision models completed analysis.")
    
    findings = upload_data.get("findings", [])
    metadata = upload_data.get("metadata", {})
    scan_id = "test-e2e-scan-001"
    
    # 2. Trigger Orchestrator Analysis
    print(f"\n2. Triggering agentic reasoning (Orchestrator) at {API_BASE}/analyze...")
    payload = {
        "scan_id": scan_id,
        "findings": findings,
        "metadata": metadata
    }
    
    analyze_resp = httpx.post(f"{API_BASE}/analyze", json=payload, headers=headers, timeout=60.0)
    
    if analyze_resp.status_code != 200:
        print(f"Analysis failed: {analyze_resp.status_code} - {analyze_resp.text}")
        sys.exit(1)
        
    analyze_data = analyze_resp.json()
    print("Analysis successful!")
    print("\n--- Generated Report ---")
    
    report = analyze_data.get("result", {})
    print(f"Agent State Keys: {list(report.keys())}")
    
    if "final_report" in report:
        print(f"\nReport snippet: {str(report['final_report'])[:200]}...")
    
    print("\nEnd-to-End Test Completed Successfully!")

if __name__ == "__main__":
    run_e2e_test()
