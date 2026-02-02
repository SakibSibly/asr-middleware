import whisper
import torch
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description="Transcribe audio using Whisper")
parser.add_argument("--language", type=str, default=None, help="Language code (e.g., 'en', 'bn', 'hi'). If not specified, language will be auto-detected.")
parser.add_argument("--audio", type=str, default="Bengali_Audio.m4a", help="Path to the audio file")
args = parser.parse_args()

# Process the audio file
audio_file = args.audio
print(f"Processing audio file: {audio_file}")
print("=" * 60)

# Check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"GPU: {gpu_name}")
    print(f"GPU Memory: {gpu_memory:.2f} GB")
print("=" * 60)

# Load Whisper model - using 'base' model for GPUs with limited memory
# Model sizes: tiny, base, small, medium, large-v3
# For 2GB GPU, base or small models are recommended
model_size = "base"  # Change to "small", "medium", or "large-v3" if you have more GPU memory
print(f"Loading Whisper {model_size} model...")
print("(This may take a while on first run as the model is downloaded)")
print("-" * 60)

try:
    model = whisper.load_model(model_size, device=device)
except torch.cuda.OutOfMemoryError:
    print(f"GPU out of memory! Falling back to CPU...")
    device = "cpu"
    model = whisper.load_model(model_size, device=device)
print("Model loaded successfully!")
print("=" * 60)

# Transcribe the audio
print(f"Transcribing audio...")
if args.language:
    print(f"Language: {args.language} (specified)")
else:
    print("Language: Auto-detect")
print("-" * 60)

result = model.transcribe(audio_file, language=args.language, verbose=True)

print("=" * 60)
print("TRANSCRIPTION RESULT:")
print("=" * 60)
print(f"Detected Language: {result['language']}")
print("-" * 60)
print("Full Text:")
print(result["text"])
print("=" * 60)
print("\nSegments with timestamps:")
print("-" * 60)
for i, segment in enumerate(result["segments"], 1):
    start = segment["start"]
    end = segment["end"]
    text = segment["text"]
    print(f"[{start:.2f}s - {end:.2f}s] {text}")
print("=" * 60)
print("Processing complete!")

# Save transcription to output.txt
output_file = "output.txt"
print(f"\nSaving transcription to {output_file}...")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"Detected Language: {result['language']}\n")
    f.write("=" * 60 + "\n\n")
    f.write("Full Transcription:\n")
    f.write(result["text"] + "\n\n")
    f.write("=" * 60 + "\n")
    f.write("Segments with timestamps:\n")
    f.write("-" * 60 + "\n")
    for i, segment in enumerate(result["segments"], 1):
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        f.write(f"[{start:.2f}s - {end:.2f}s] {text}\n")
print(f"Transcription saved to {output_file}")
