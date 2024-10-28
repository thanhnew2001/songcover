# Import necessary libraries
import subprocess
from pydub import AudioSegment

song = "depacito"
# Define audio input
AUDIO_INPUT = f"{song}.wav"  # Path to the input audio file

# Separate vocals and instruments using Demucs
def separate_audio(input_audio):
    command = f"demucs --two-stems=vocals {input_audio}"
    result = subprocess.run(command.split(), stdout=subprocess.PIPE)
    print(result.stdout.decode())

# Run the separation function
separate_audio(AUDIO_INPUT)

# Inference
AUDIO = "separated/htdemucs/{song}/vocals"  # Path to the separated vocal file
MODEL = "logs/44k/G_4000.pth"  # Path to the model file
CONFIG = "logs/44k/config.json"  # Path to the configuration file

# Change according to your voice tone
PITCH = 0  # Pitch adjustment (12 = 1 octave, -12 = -1 octave)

# Run inference
def run_inference(audio, config, model, pitch):
    command = f"svc infer {audio}.wav -c {config} -m {model} -na -t {pitch}"
    subprocess.run(command.split())

run_inference(AUDIO, CONFIG, MODEL, PITCH)

# Combine vocal and instrument (song cover)
VOCAL = "separated/htdemucs/{song}/vocals.out.wav"  # Path to the vocal output
INSTRUMENT = "separated/htdemucs/{song}/no_vocals.wav"  # Path to the instrumental output

def combine_audio(vocal_file, instrument_file, output_file):
    sound1 = AudioSegment.from_file(vocal_file)
    sound2 = AudioSegment.from_file(instrument_file)
    sound1 = sound1 + (sound1.dBFS * 0.5)  # Increase by 50% of the current dBFS level

    combined = sound1.overlay(sound2)
    combined.export(output_file, format='wav')
    print(f"Combined audio saved to {output_file}")

# Run the combining function
combine_audio(VOCAL, INSTRUMENT, "giongbao_xanh50.wav")

# Optional: play the final cover audio (if using an environment that supports audio pl
