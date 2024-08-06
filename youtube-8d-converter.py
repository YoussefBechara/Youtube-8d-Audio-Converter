import os
import requests
from yt_dlp import YoutubeDL
from pydub import AudioSegment
import numpy as np
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from mutagen.id3 import ID3
from mutagen.id3 import ID3, APIC

def download_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'writeinfojson': True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        thumbnail_url = info_dict.get('thumbnail')
        return thumbnail_url

def apply_8d_effect(audio_file, output_file):
    # Load the audio file
    audio = AudioSegment.from_file(audio_file)
    
    # Convert audio to stereo if it's not
    if audio.channels == 1:
        audio = audio.set_channels(2)
    
    # Split into left and right channels
    left_channel = audio.split_to_mono()[0]
    right_channel = audio.split_to_mono()[1]

    # Apply dynamic panning effect
    samples_left = np.array(left_channel.get_array_of_samples())
    samples_right = np.array(right_channel.get_array_of_samples())
    
    length = len(samples_left)
    t = np.linspace(0, 1, length)
    # Increase the frequency for faster panning
    pan = 0.5 * (np.sin(2 * np.pi * 3.0 * t) + 1)  # Increased frequency to 3.0 Hz
    
    # Create panned samples
    samples_left_panned = samples_left * (1 - pan)
    samples_right_panned = samples_right * pan
    
    # Combine panned samples
    combined_left = np.clip(samples_left_panned + samples_right * (1 - pan), -32768, 32767)
    combined_right = np.clip(samples_right_panned + samples_left * pan, -32768, 32767)
    
    left_channel = AudioSegment(
        combined_left.astype(np.int16).tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=1
    )
    
    right_channel = AudioSegment(
        combined_right.astype(np.int16).tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=1
    )

    # Combine channels back into stereo
    stereo_audio = AudioSegment.from_mono_audiosegments(left_channel, right_channel)
    
    # Export the final 8D audio
    stereo_audio.export(output_file, format="mp3")

def add_thumbnail_to_mp3(mp3_file, thumbnail_url):
    # Download the thumbnail
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        with open('thumbnail.jpg', 'wb') as f:
            f.write(response.content)
    
    # Add thumbnail to MP3
    try:
        audio = ID3(mp3_file)
    except ID3NoHeaderError:
        audio = ID3()
    
    with open('thumbnail.jpg', 'rb') as f:
        audio['APIC'] = APIC(
            encoding=3,  # 3 is for ID3v2.3
            mime='image/jpeg',
            type=3,  # 3 is for the cover image
            desc='Cover',
            data=f.read()
        )
    
    audio.save(mp3_file)
    
    # Clean up the thumbnail file
    os.remove('thumbnail.jpg')

def main(youtube_url, output_audio_path):
    temp_audio_path = 'temp_audio'
    
    thumbnail_url = download_audio(youtube_url, f'{temp_audio_path}')
    apply_8d_effect(f'{temp_audio_path}.mp3', f'{output_audio_path}.mp3')
    
    add_thumbnail_to_mp3(f'{output_audio_path}.mp3', thumbnail_url)
    
    # Clean up temporary files
    os.remove(f'{temp_audio_path}.mp3')
    
    print(f'8D audio saved as {output_audio_path}.mp3 with cover image')

if __name__ == "__main__":
    youtube_url = input("Paste the YouTube video URL: ")
    outpath = input("Output path/Name the audio: ")
    main(youtube_url, outpath)
