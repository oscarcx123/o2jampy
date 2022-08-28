from pydub import AudioSegment
from pydub.utils import mediainfo
import os

# load sound and return AudioSegment object
# folder_path -> song folder path (self.song_path in OJNExtract)
# sound_filename -> "normal-hitnormal1002.ogg"
def load_sound(folder_path: str, sound_filename: str):
    sound_ext = sound_filename.split(".")[-1]
    sound_file = os.path.join(folder_path, sound_filename)
    sound = AudioSegment.from_file((sound_file), format=sound_ext)
    return sound

# Calculate target bitrate
# sound_file -> full filepath
def get_target_bitrate(sound_file: str):
    original_bitrate = mediainfo(sound_file)['bit_rate']
    mp3_bitrates = [128000, 192000, 320000]
    temp_bitrates = [x - int(original_bitrate) for x in mp3_bitrates]
    closest_result = min(temp_bitrates, key=abs)
    idx = temp_bitrates.index(closest_result)
    target_bitrate = mp3_bitrates[idx]
    return target_bitrate

# convert a single file to mp3
# folder_path -> song folder path (self.song_path in OJNExtract)
# sound_filename -> "normal-hitnormal1002.ogg"
# output_filename -> "audio_1237.mp3"
def to_mp3(folder_path: str, sound_filename: str, output_filename: str):
    print(f"{sound_filename} -> {output_filename}")
    sound_file = os.path.join(folder_path, sound_filename)

    # import source audio file
    sound = load_sound(folder_path, sound_filename)
    
    # determine output target bitrate
    target_bitrate = get_target_bitrate(sound_file)

    # export mp3
    sound.export(os.path.join(folder_path, f"{output_filename}"), format="mp3", bitrate=str(target_bitrate))

# get audio length in ms
def get_audio_length(folder_path: str, sound_filename: str) -> int:
    return len(load_sound(folder_path, sound_filename))

# use curr_mp3_remix_list from OJNExtract to merge mp3
# folder_path -> song folder path (self.song_path in OJNExtract)
# remix_list -> [time (ms), sound_filename ("normal-hitnormal1002.ogg")]
# output_filename -> "audio_1237.mp3"
def merge_mp3(folder_path: str, remix_list: list, output_filename: str):
    print(f"All hitsounds -> {output_filename}, this might take a while...")
    for snd in remix_list:
        start_time = snd[0]
        sound_filename = snd[1]
        duration = get_audio_length(folder_path, sound_filename)
        end_time = start_time + duration
        snd.extend([end_time, duration]) # snd -> [start_time, sound_filename, end_time, duration]
    
    mp3_duration = max([snd[2] for snd in remix_list])
    mp3 = AudioSegment.silent(duration=mp3_duration)

    for snd in remix_list:
        sound = load_sound(folder_path, snd[1])
        mp3 = mp3.overlay(sound, position=snd[0])

    remix_list.sort(key=lambda x: x[3])
    sound_filename = remix_list[-1][1]
    sound_file = os.path.join(folder_path, sound_filename)
    target_bitrate = get_target_bitrate(sound_file)
    
    mp3.export(os.path.join(folder_path, f"{output_filename}"), format="mp3", bitrate=str(target_bitrate))


def clean_up(folder_path: str):
    snd_files = [x for x in os.listdir(folder_path) if x.endswith(".ogg") or x.endswith(".wav")]
    for f in snd_files:
        os.remove(os.path.join(folder_path, f))
    print("All .ogg and .wav deleted")