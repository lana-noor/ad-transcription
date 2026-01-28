"""
Convert Raw Transcriptions to Formatted PDFs
Reads JSON transcription files and creates nicely formatted PDFs with speaker diarization.
"""

import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_FOLDER = ""
OUTPUT_FOLDER_LOCAL = ""
STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
OUTPUT_CONTAINER = "transcription-pdf"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER_LOCAL, exist_ok=True)


def parse_transcription_json(json_path):
    """Parse the transcription JSON file and extract relevant information."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract metadata
    source = data.get("source", "Unknown")
    timestamp = data.get("timestamp", "Unknown")
    duration = data.get("duration", "Unknown")
    
    # Extract combined recognitions (with speaker info)
    combined_phrases = []
    
    if "combinedRecognizedPhrases" in data:
        for phrase in data["combinedRecognizedPhrases"]:
            combined_phrases.append({
                "channel": phrase.get("channel", 0),
                "text": phrase.get("display", phrase.get("lexical", "")),
                "speaker": phrase.get("speaker", None)
            })
    
    # Extract detailed recognized phrases with speaker diarization
    detailed_phrases = []
    
    if "recognizedPhrases" in data:
        for phrase in data["recognizedPhrases"]:
            speaker = phrase.get("speaker", None)
            channel = phrase.get("channel", 0)
            
            # Get the best result
            if phrase.get("nBest") and len(phrase["nBest"]) > 0:
                best = phrase["nBest"][0]
                text = best.get("display", best.get("lexical", ""))
                confidence = best.get("confidence", 0)
                
                # Get word-level timestamps if available
                words = best.get("words", [])
                
                detailed_phrases.append({
                    "speaker": speaker,
                    "channel": channel,
                    "text": text,
                    "confidence": confidence,
                    "offset": phrase.get("offset", 0),
                    "duration": phrase.get("duration", 0),
                    "words": words
                })
    
    return {
        "source": source,
        "timestamp": timestamp,
        "duration": duration,
        "combined_phrases": combined_phrases,
        "detailed_phrases": detailed_phrases
    }


def format_duration(duration_ticks):
    """Convert duration from ticks (100-nanosecond units) to readable format."""
    if isinstance(duration_ticks, str):
        try:
            duration_ticks = int(duration_ticks)
        except:
            return duration_ticks
    
    # Convert ticks to seconds (1 tick = 100 nanoseconds)
    seconds = duration_ticks / 10000000
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_timestamp(offset_ticks):
    """Convert offset from ticks to timestamp format."""
    if isinstance(offset_ticks, str):
        try:
            offset_ticks = int(offset_ticks)
        except:
            return offset_ticks
    
    seconds = offset_ticks / 10000000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
    else:
        return f"{minutes:02d}:{secs:05.2f}"


def create_pdf(transcription_data, output_path, source_filename):
    """Create a nicely formatted PDF from transcription data."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    speaker_style = ParagraphStyle(
        'Speaker',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2980b9'),
        fontName='Helvetica-Bold',
        spaceAfter=4
    )

    text_style = ParagraphStyle(
        'TranscriptText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        leading=14
    )

    metadata_style = ParagraphStyle(
        'Metadata',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=6
    )

    # Title
    story.append(Paragraph("Transcription Report", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Metadata section
    story.append(Paragraph("Document Information", heading_style))

    metadata_table_data = [
        ["Source File:", source_filename],
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Duration:", format_duration(transcription_data.get("duration", "Unknown"))],
    ]

    metadata_table = Table(metadata_table_data, colWidths=[1.5*inch, 4.5*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#34495e')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(metadata_table)
    story.append(Spacer(1, 0.3*inch))

    # Transcription section
    story.append(Paragraph("Transcription with Speaker Diarization", heading_style))
    story.append(Spacer(1, 0.1*inch))

    # Add detailed phrases with speaker information
    detailed_phrases = transcription_data.get("detailed_phrases", [])

    if detailed_phrases:
        current_speaker = None

        for phrase in detailed_phrases:
            speaker = phrase.get("speaker")
            text = phrase.get("text", "")
            offset = phrase.get("offset", 0)

            if not text.strip():
                continue

            # Format speaker label
            if speaker is not None:
                speaker_label = f"Speaker {speaker}"
            else:
                speaker_label = "Unknown Speaker"

            # Add timestamp
            timestamp = format_timestamp(offset)
            speaker_text = f"{speaker_label} [{timestamp}]"

            # Add speaker header if speaker changed
            if speaker != current_speaker:
                story.append(Paragraph(speaker_text, speaker_style))
                current_speaker = speaker

            # Add transcribed text
            story.append(Paragraph(text, text_style))

    else:
        # Fallback to combined phrases if detailed phrases not available
        combined_phrases = transcription_data.get("combined_phrases", [])

        for phrase in combined_phrases:
            text = phrase.get("text", "")
            speaker = phrase.get("speaker")

            if not text.strip():
                continue

            if speaker is not None:
                speaker_label = f"Speaker {speaker}"
            else:
                speaker_label = "Speaker"

            story.append(Paragraph(speaker_label, speaker_style))
            story.append(Paragraph(text, text_style))

    # Build PDF
    doc.build(story)
    print(f"✓ PDF created: {output_path}")


def upload_to_blob(local_path, blob_name):
    """Upload PDF to Azure Blob Storage."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=OUTPUT_CONTAINER, blob=blob_name)

        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        print(f"✓ Uploaded to blob storage: {blob_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to upload to blob storage: {str(e)}")
        return False


def process_transcription_file(json_filename):
    """Process a single transcription JSON file and convert to PDF."""
    print(f"\n{'='*60}")
    print(f"Processing: {json_filename}")
    print(f"{'='*60}")

    json_path = os.path.join(INPUT_FOLDER, json_filename)

    # Parse transcription
    print("Parsing transcription data...")
    transcription_data = parse_transcription_json(json_path)

    # Create PDF filename
    base_name = os.path.splitext(json_filename)[0]
    pdf_filename = f"{base_name}.pdf"
    pdf_path = os.path.join(OUTPUT_FOLDER_LOCAL, pdf_filename)

    # Generate PDF
    print("Generating PDF...")
    create_pdf(transcription_data, pdf_path, json_filename)

    # Upload to blob storage
    print("Uploading to blob storage...")
    upload_to_blob(pdf_path, pdf_filename)

    return pdf_filename


def main():
    """Main function to convert all transcription files to PDFs."""
    print("Transcription to PDF Converter")
    print("=" * 60)
    print(f"Input Folder: {INPUT_FOLDER}")
    print(f"Output Folder (Local): {OUTPUT_FOLDER_LOCAL}")
    print(f"Output Container (Blob): {OUTPUT_CONTAINER}")
    print("=" * 60)

    # List all JSON files in input folder
    json_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.json')]

    if not json_files:
        print("\nNo JSON transcription files found in input folder.")
        return

    print(f"\nFound {len(json_files)} transcription file(s):")
    for i, filename in enumerate(json_files, 1):
        print(f"  {i}. {filename}")

    # Process each file
    results = []
    for json_file in json_files:
        try:
            pdf_file = process_transcription_file(json_file)
            results.append({"input": json_file, "output": pdf_file, "status": "success"})
        except Exception as e:
            print(f"✗ Error processing {json_file}: {str(e)}")
            results.append({"input": json_file, "output": None, "status": "failed", "error": str(e)})

    # Summary
    print(f"\n{'='*60}")
    print("CONVERSION SUMMARY")
    print(f"{'='*60}")
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if successful > 0:
        print(f"\nPDFs saved to:")
        print(f"  Local: {OUTPUT_FOLDER_LOCAL}")
        print(f"  Blob: {OUTPUT_CONTAINER}")


if __name__ == "__main__":
    main()

