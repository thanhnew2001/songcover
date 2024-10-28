# -*- coding: utf-8 -*-
import os
import subprocess
import json
import numpy as np
from scipy.io import wavfile
from tqdm import tqdm
from datetime import datetime, timedelta
from pydub import AudioSegment

# Separate audio using Demucs
def separate_audio(input_audio):
    command = f"demucs --two-stems=vocals {input_audio}"
    
    print("Separating audio into vocals and instruments...")
    result = subprocess.run(command.split(), stdout=subprocess.PIPE)
    print(result.stdout.decode())
    print("Audio separation completed.")

def GetTime(video_seconds):
    if video_seconds < 0:
        return "00:00:00.001"
    else:
        sec = timedelta(seconds=float(video_seconds))
        d = datetime(1, 1, 1) + sec
        return f"{str(d.hour).zfill(2)}:{str(d.minute).zfill(2)}:{str(d.second).zfill(2)}.001"

def windows(signal, window_size, step_size):
    for i_start in range(0, len(signal), step_size):
        i_end = i_start + window_size
        if i_end >= len(signal):
            break
        yield signal[i_start:i_end]

def energy(samples):
    return np.sum(np.power(samples, 2.)) / float(len(samples))

def rising_edges(binary_signal):
    previous_value = 0
    index = 0
    for x in binary_signal:
        if x and not previous_value:
            yield index
        previous_value = x
        index += 1

def split_audio(input_file, output_dir, min_silence_length=0.6, silence_threshold=1e-4, step_duration=0.003):
    os.makedirs(output_dir, exist_ok=True)

    print(f"Splitting audio file {input_file}...")
    sample_rate, samples = wavfile.read(input_file)
    max_amplitude = np.iinfo(samples.dtype).max
    max_energy = energy([max_amplitude])
    window_size = int(min_silence_length * sample_rate)
    step_size = int(step_duration * sample_rate)

    signal_windows = windows(samples, window_size, step_size)
    window_energy = (energy(w) / max_energy for w in tqdm(signal_windows))
    window_silence = (e > silence_threshold for e in window_energy)
    cut_times = (r * step_duration for r in rising_edges(window_silence))

    cut_samples = [int(t * sample_rate) for t in cut_times]
    cut_samples.append(-1)
    cut_ranges = [(i, cut_samples[i], cut_samples[i + 1]) for i in range(len(cut_samples) - 1)]

    video_sub = {str(i): [str(GetTime(cut_samples[i] / sample_rate)),
                          str(GetTime(cut_samples[i + 1] / sample_rate))]
                  for i in range(len(cut_samples) - 1)}

    for i, start, stop in tqdm(cut_ranges):
        output_file_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}_{i:03d}.wav")
        wavfile.write(output_file_path, rate=sample_rate, data=samples[start:stop])
        print(f"Written file: {output_file_path}")

    with open(os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}.json"), 'w') as output:
        json.dump(video_sub, output)

    print("Audio splitting completed.")


# Preprocessing step
def preprocess():
    print("Preprocessing for training...")
    subprocess.run(['svc', 'pre-resample'])
    subprocess.run(['svc', 'pre-config'])

    subprocess.run(['svc', 'pre-hubert', '-fm', 'dio'])

    print("Preprocessing completed.")

# Training step
def train_model():
    print("Training model...")
    subprocess.run(['svc', 'train', '--model-path', 'logs/44k'])
    print("Training completed.")

# Combine vocal and instrument
def combine_audio(vocal_file, instrument_file, output_file):
    print("Combining vocal and instrument...")
    sound1 = AudioSegment.from_file(vocal_file)
    sound2 = AudioSegment.from_file(instrument_file)
    combined = sound1.overlay(sound2)
    combined.export(output_file, format='wav')
    print(f"Combined audio saved to {output_file}")

# Main execution
if __name__ == "__main__":
    speaker_name = "trinhan"
    audio_input = "trinhan.wav"  # Replace with your MP3 path
    separate_audio(audio_input)

    output_dir = f"dataset_raw/{speaker_name}"
    split_audio(f"separated/htdemucs/{speaker_name}/vocals.wav", output_dir)

    # preprocess()  # Preprocessing for training
    train_model()  # Train the model


