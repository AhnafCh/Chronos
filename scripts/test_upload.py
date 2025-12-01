# scripts/test_upload.py
"""
Test script for the file upload endpoint
Usage: python scripts/test_upload.py <file_path>
"""
import sys
import requests

def upload_file(file_path: str, base_url: str = "http://localhost:8026"):
    """Upload a file to the Chronos API"""
    
    endpoint = f"{base_url}/api/upload"
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("\\")[-1], f)}
            response = requests.post(endpoint, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload Successful!")
            print(f"   Filename: {result['filename']}")
            print(f"   Documents Processed: {result['documents_processed']}")
            print(f"   Index: {result['index']}")
        else:
            print(f"❌ Upload Failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.json()}")
    
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {base_url}. Is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

def upload_multiple_files(file_paths: list, base_url: str = "http://localhost:8026"):
    """Upload multiple files to the Chronos API"""
    
    endpoint = f"{base_url}/api/upload/batch"
    
    try:
        files = []
        for file_path in file_paths:
            f = open(file_path, "rb")
            files.append(("files", (file_path.split("\\")[-1], f)))
        
        response = requests.post(endpoint, files=files)
        
        # Close all file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Batch Upload Successful!")
            print(f"   Total Documents Ingested: {result['total_documents_ingested']}")
            print(f"   Index: {result['index']}")
            print("\n   File Details:")
            for file_result in result['files']:
                status = "✅" if file_result['status'] == 'processed' else "❌"
                print(f"   {status} {file_result['filename']}: {file_result.get('documents_extracted', 'N/A')} docs")
        else:
            print(f"❌ Upload Failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.json()}")
    
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {base_url}. Is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_upload.py <file_path> [file_path2] [file_path3] ...")
        print("\nExample (single file):")
        print("  python scripts/test_upload.py document.pdf")
        print("\nExample (multiple files):")
        print("  python scripts/test_upload.py doc1.pdf doc2.txt doc3.md")
        sys.exit(1)
    
    file_paths = sys.argv[1:]
    
    if len(file_paths) == 1:
        print(f"📤 Uploading: {file_paths[0]}")
        upload_file(file_paths[0])
    else:
        print(f"📤 Uploading {len(file_paths)} files...")
        upload_multiple_files(file_paths)
