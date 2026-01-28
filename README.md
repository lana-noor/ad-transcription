# Azure AI Speech Batch Transcription with Diarization

This project provides Python scripts to transcribe audio files from Azure Blob Storage using Azure AI Speech Service with speaker diarization, and convert the transcriptions to formatted PDFs.

## Features

- **Batch Transcription**: Automatically transcribe all `.wav` files from Azure Blob Storage
- **Speaker Diarization**: Identify and label different speakers in the audio
- **Word-level Timestamps**: Precise timing information for each word
- **PDF Generation**: Convert raw JSON transcriptions to nicely formatted PDFs
- **Automatic Upload**: PDFs are saved locally and uploaded to Azure Blob Storage

## Prerequisites

- Python 3.8 or higher
- Azure Speech Service subscription or Microsoft Foundry Project Resource 
   - For Foundry Project resource, navigate to the Azure Portal, navigate to your Foundry project, and under "Resource Management", navigate to "Keys and Endpoint", under "AI Services", copy "KEY 1" and the "Speech to Text (Standard)" endpoint to use the Azure AI Speech APIs 
- Azure Storage Account with blob containers

## Installation and Setup

Follow these steps to set up your environment and run the transcription scripts:

### Step 1: Create a Virtual Environment

Create a Python virtual environment to isolate project dependencies:

```powershell
python -m venv venv
```

### Step 2: Activate the Virtual Environment

Activate the virtual environment (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

> **Note**: If you encounter an execution policy error, run PowerShell as Administrator and execute:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

For other shells:
- **Command Prompt (Windows)**: `venv\Scripts\activate.bat`
- **Bash (Linux/Mac)**: `source venv/bin/activate`

### Step 3: Authenticate with Azure

Log in to your Azure account using Azure Developer CLI:

```powershell
azd auth login
```

This will open a browser window for you to authenticate. Make sure you're logged into the correct Azure subscription that contains your Speech Service and Storage Account.

### Step 4: Install Python Dependencies

Install all required Python packages:

```powershell
pip install -r requirements.txt
```

This will install:
- `azure-storage-blob` - For Azure Blob Storage operations
- `azure-cognitiveservices-speech` - For Azure Speech Service
- `requests` - For HTTP API calls
- `reportlab` - For PDF generation
- `python-dotenv` - For environment variable management

### Step 5: Configure Environment Variables

Your `.env` file is already configured with Azure credentials. Verify it contains:

```env
AZURE_SPEECH_KEY=your_speech_key
AZURE_SPEECH_REGION=swedencentral
SPEECH_TO_TEXT_ENDPOINT=https://swedencentral.stt.speech.microsoft.com
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_SAS_TOKEN=your_sas_token
```

## Project Structure

```
TranscriptionCode/
├── batch_transcription.py      # Main transcription script
├── convert_to_pdf.py           # PDF conversion script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (configured)
├── .env.example               # Example environment file
├── outputRawTranscription/    # Raw JSON transcriptions
├── outputPDF/                 # Generated PDF files
└── demodata/                  # Sample audio files
```

## Usage

Now that your environment is set up, you can run the transcription and PDF conversion scripts.

> **Important**: Make sure your virtual environment is activated before running the scripts:
> ```powershell
> .\venv\Scripts\Activate.ps1
> ```

### Step 1: Transcribe Audio Files

Run the batch transcription script to process all `.wav` files from the `input-wavfiles` container:

```powershell
python batch_transcription.py
```

This script will:
1. List all `.wav` files in the Azure Blob Storage container
2. Create a batch transcription job for each file with diarization enabled
3. Wait for transcription to complete
4. Download the results as JSON files to `outputRawTranscription/`

**Note**: Transcription can take several minutes depending on audio length.

### Step 2: Convert to PDF

Run the PDF conversion script to convert all JSON transcriptions to formatted PDFs:

```powershell
python convert_to_pdf.py
```

This script will:
1. Read all JSON files from `outputRawTranscription/`
2. Parse the transcription data with speaker information
3. Generate nicely formatted PDFs with:
   - Document metadata (source file, duration, timestamp)
   - Speaker-labeled transcription
   - Timestamps for each speaker segment
4. Save PDFs to `outputPDF/` locally
5. Upload PDFs to the `transcription-pdf` blob container

## Configuration

### Azure Blob Storage Containers

- **Input**: `input-wavfiles` - Upload your `.wav` files here
- **Output**: `transcription-pdf` - PDFs are automatically uploaded here

### Speech Service Settings

The transcription is configured with:
- **Locale**: en-US (English - United States)
- **Diarization**: Enabled (identifies different speakers)
- **Word-level Timestamps**: Enabled
- **Punctuation**: Automatic
- **Profanity Filter**: Masked

## Output Format

### Raw Transcription (JSON)
Contains detailed information including:
- Speaker identification
- Word-level timestamps
- Confidence scores
- Multiple recognition alternatives

### PDF Format
Formatted document with:
- Title and metadata section
- Speaker-labeled transcription
- Timestamps for each segment
- Professional styling and layout

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your Azure credentials in `.env`
2. **No files found**: Ensure `.wav` files are uploaded to the correct container
3. **Transcription timeout**: Increase `max_wait_minutes` in `batch_transcription.py`
4. **PDF generation fails**: Check that JSON files exist in `outputRawTranscription/`

### Checking Logs

Both scripts provide detailed console output showing:
- Files being processed
- Progress updates
- Success/failure status
- Summary statistics

## Quick Reference

### Complete Setup and Run Commands

Here's the complete sequence of commands to set up and run the project:

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Authenticate with Azure
azd auth login

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run transcription
python batch_transcription.py

# 6. Convert to PDF
python convert_to_pdf.py
```

### Subsequent Runs

After initial setup, you only need:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the scripts
python batch_transcription.py
python convert_to_pdf.py
```

## API References

- [Azure Speech Batch Transcription](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/batch-transcription)
- [Batch Transcription REST API](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/batch-transcription-get?pivots=rest-api)

## Support

For issues or questions, refer to the Azure AI Speech Service documentation or check the error messages in the console output.

