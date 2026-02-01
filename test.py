import whisper
import torch

# Process the test_aud.mp3 file
audio_file = "Mix_Audio.m4a"
print(f"Processing audio file: {audio_file}")
print("=" * 60)

# Check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
print("=" * 60)

# Load Whisper model
print("Loading Whisper large-v3 model...")
print("(This may take a while on first run as the model is downloaded)")
print("-" * 60)

model = whisper.load_model("large-v3", device=device)
print("Model loaded successfully!")
print("=" * 60)

# Transcribe the audio
print(f"Transcribing audio...")
print("-" * 60)

result = model.transcribe(audio_file, language=None, verbose=True)

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
