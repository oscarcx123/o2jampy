from pydub import AudioSegment
from pydub.utils import mediainfo
import os

# folder_path -> song folder path (self.song_path in OJNExtract)
# sound_filename -> "normal-hitnormal1002.ogg"
# output_filename -> "audio_1237.mp3"
def to_mp3(folder_path: str, sound_filename: str, output_filename: str):
    print(f"{sound_filename} -> {output_filename}")
    # import source audio file
    sound_ext = sound_filename.split(".")[-1]
    sound_file = os.path.join(folder_path, sound_filename)
    sound = AudioSegment.from_file((sound_file), format=sound_ext)
    
    # determine output target bitrate
    original_bitrate = mediainfo(sound_file)['bit_rate']
    mp3_bitrates = [128000, 192000, 320000]
    temp_bitrates = [x - int(original_bitrate) for x in mp3_bitrates]
    closest_result = min(temp_bitrates, key=abs)
    idx = temp_bitrates.index(closest_result)
    target_bitrate = mp3_bitrates[idx]

    # export mp3
    sound.export(os.path.join(folder_path, f"{output_filename}"), format="mp3", bitrate=str(target_bitrate))

    # TODO: Delete source audio file
    os.remove(sound_file)

# get audio length in ms
def get_audio_length(folder_path: str, sound_filename: str) -> int:
    sound_ext = sound_filename.split(".")[-1]
    sound_file = os.path.join(folder_path, sound_filename)
    sound = AudioSegment.from_file((sound_file), format=sound_ext)
    return len(sound)