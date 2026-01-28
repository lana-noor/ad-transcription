"""
Azure AI Speech Batch Transcription Script
Transcribes .wav files from Azure Blob Storage with speaker diarization enabled.
"""

import os
import time
import json
import requests
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "swedencentral")
SPEECH_ENDPOINT = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/speechtotext/v3.2/transcriptions"

STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
INPUT_CONTAINER = "adic-input-wavfiles"
OUTPUT_FOLDER = r"C:\Users\lananoor\OneDrive - Microsoft\ADIC\TranscriptionCode\outputRawTranscription"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_blob_sas_url(blob_name):
    """Generate SAS URL for a blob in the input container."""
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
    
    # Construct the blob URL with SAS token
    blob_url = f"https://{storage_account_name}.blob.core.windows.net/{INPUT_CONTAINER}/{blob_name}?{sas_token}"
    return blob_url


def list_wav_files():
    """List all .wav files in the input container."""
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(INPUT_CONTAINER)
    
    wav_files = []
    blobs = container_client.list_blobs()
    for blob in blobs:
        if blob.name.lower().endswith('.wav'):
            wav_files.append(blob.name)
    
    return wav_files


def create_transcription(audio_url, display_name):
    """Create a batch transcription job with diarization enabled."""
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "application/json"
    }
    
    # Transcription configuration with diarization
    transcription_config = {
        "contentUrls": [audio_url],
        "locale": "en-US",
        "displayName": display_name,
        "properties": {
            "diarizationEnabled": True,
            "wordLevelTimestampsEnabled": True,
            "punctuationMode": "DictatedAndAutomatic",
            "profanityFilterMode": "Masked"
        }
    }
    
    response = requests.post(SPEECH_ENDPOINT, headers=headers, json=transcription_config)
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create transcription: {response.status_code} - {response.text}")


def get_transcription_status(transcription_url):
    """Check the status of a transcription job."""
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }
    
    response = requests.get(transcription_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get transcription status: {response.status_code} - {response.text}")


def get_transcription_files(transcription_url):
    """Get the files associated with a completed transcription."""
    files_url = f"{transcription_url}/files"
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }
    
    response = requests.get(files_url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get transcription files: {response.status_code} - {response.text}")


def download_transcription_result(content_url, output_filename):
    """Download and save the transcription result."""
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }
    
    response = requests.get(content_url, headers=headers)
    
    if response.status_code == 200:
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, indent=2, ensure_ascii=False)
        print(f"✓ Transcription saved to: {output_path}")
        return output_path
    else:
        raise Exception(f"Failed to download transcription: {response.status_code} - {response.text}")


def wait_for_transcription(transcription_url, max_wait_minutes=30):
    """Wait for transcription to complete."""
    print("Waiting for transcription to complete...")
    max_iterations = max_wait_minutes * 6  # Check every 10 seconds
    
    for i in range(max_iterations):
        status_data = get_transcription_status(transcription_url)
        status = status_data.get("status")
        
        print(f"  Status: {status} ({i*10}s elapsed)")
        
        if status == "Succeeded":
            return True
        elif status == "Failed":
            error = status_data.get("properties", {}).get("error", {})
            raise Exception(f"Transcription failed: {error}")
        
        time.sleep(10)
    
    raise Exception(f"Transcription timed out after {max_wait_minutes} minutes")


def process_wav_file(wav_filename):
    """Process a single .wav file through batch transcription."""
    print(f"\n{'='*60}")
    print(f"Processing: {wav_filename}")
    print(f"{'='*60}")
    
    # Get blob URL with SAS token
    audio_url = get_blob_sas_url(wav_filename)
    
    # Create transcription job
    display_name = f"Transcription_{wav_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating transcription job: {display_name}")
    transcription_data = create_transcription(audio_url, display_name)
    transcription_url = transcription_data.get("self")
    print(f"✓ Transcription job created: {transcription_url}")
    
    # Wait for completion
    wait_for_transcription(transcription_url)

    # Get transcription files
    print("Retrieving transcription results...")
    files_data = get_transcription_files(transcription_url)

    # Find and download the transcription result file
    for file_info in files_data.get("values", []):
        if file_info.get("kind") == "Transcription":
            content_url = file_info.get("links", {}).get("contentUrl")
            if content_url:
                # Create output filename
                base_name = os.path.splitext(wav_filename)[0]
                output_filename = f"{base_name}_transcription.json"
                download_transcription_result(content_url, output_filename)
                return output_filename

    raise Exception("No transcription result file found")


def main():
    """Main function to process all .wav files in the container."""
    print("Azure AI Speech Batch Transcription")
    print("=" * 60)
    print(f"Input Container: {INPUT_CONTAINER}")
    print(f"Output Folder: {OUTPUT_FOLDER}")
    print(f"Speech Region: {SPEECH_REGION}")
    print("=" * 60)

    # List all .wav files
    print("\nListing .wav files in container...")
    wav_files = list_wav_files()

    if not wav_files:
        print("No .wav files found in the container.")
        return

    print(f"Found {len(wav_files)} .wav file(s):")
    for i, filename in enumerate(wav_files, 1):
        print(f"  {i}. {filename}")

    # Process each file
    results = []
    for wav_file in wav_files:
        try:
            output_file = process_wav_file(wav_file)
            results.append({"input": wav_file, "output": output_file, "status": "success"})
        except Exception as e:
            print(f"✗ Error processing {wav_file}: {str(e)}")
            results.append({"input": wav_file, "output": None, "status": "failed", "error": str(e)})

    # Summary
    print(f"\n{'='*60}")
    print("TRANSCRIPTION SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if successful > 0:
        print(f"\nTranscriptions saved to: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()

