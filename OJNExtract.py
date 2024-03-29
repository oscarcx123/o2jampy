import os
import math
import copy
import struct
import audio_lib
from OJMExtract import OJMExtract

class OJNExtract():
    def __init__(self):
        self.diff_scale = ["Easy", "Normal", "Hard"]
        self.input_path = os.path.join(os.getcwd(), "input")
        self.output_path = os.path.join(os.getcwd(), "output")
        self.settings()
        self.debug = False

    def settings(self):
        '''Common Codecs
        gb18030 - Simplified Chinese
        big5 - Traditional Chinese
        euc_kr - Korean
        '''
        self.enc = "euc_kr"
        self.flag_use_mp3 = True
        self.flag_nsv = True
        self.extra_offset = -50

    # Just an example
    # More info: https://open2jam.wordpress.com/the-ojn-documentation/
    def __ojn_header_example(self):
        song_id = 1237
        ojn_version = "2.90"
        genre_text = "Etc"
        bpm = 148.0
        lvl = [20, 40, 80] # [E(asy), N(ornal), H(ard)]
        total_notes = [2178, 3496, 5855] # with background music notes
        playable_notes = [2175, 3474, 5853] # without background music notes (always use this one)
        measure_count = [99, 99, 99] # the number of measures in each section
        package_count = [664, 702, 705] # the number of packages in each level section
        title = "万華鏡" # if gibberish, try other common codecs
        artist = "senya"
        noter = "KNH**"
        ojm_name = "o2ma1237.ojm"
        cover_size = 470501 # background image size
        duration = [189, 189, 189] # song duration
        diff_offset = [300, 145360, 341296] # The first offset always starts at 300. Empty note sections have a size of 0 (if the easy section is empty, the offsets for easy and normal would be the same)
        cover_offset = 593564 # background image offset
        diff_size = [145060, 195936, 252268] # used for parse_diff

    def _ojn_header_debug(self):
        print(f"song_id = {self.song_id}")
        print(f"title = {self.title}")
        print(f"artist = {self.artist}")
        print(f"noter = {self.noter}")
        print(f"bpm = {self.bpm}")
        print(f"lvl = {self.lvl}")
        print(f"playable_notes = {self.playable_notes}")
        print(f"duration = {self.duration}")

        print(f"diff_offset = {self.diff_offset}")
        print(f"diff_size = {self.diff_size}")
        print(f"cover_offset = {self.cover_offset}")
        print(f"cover_size = {self.cover_size}")

        print(f"ojn_version = {self.ojn_version}")
        print(f"genre_text = {self.genre_text}")
        print(f"total_notes = {self.total_notes}")
        print(f"measure_count = {self.measure_count}")
        print(f"package_count = {self.package_count}")
        print(f"ojm_name = {self.ojm_name}")

    def error_log(self, msg):
        print(f"[ERROR] <{self.song_id}> {self.artist} - {self.title} ({self.noter}) [{self.curr_diff}]: {msg}")

    def warning_log(self, msg):
        print(f"[WARNING] <{self.song_id}> {self.artist} - {self.title} ({self.noter}) [{self.curr_diff}]: {msg}")

    def info_log(self, msg):
        print(f"[INFO] {msg}")

    # remove illegal filename characters on Windows
    def safe_filename(self, filename):
        illegal_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
        for c in illegal_chars:
            filename = filename.replace(c, "")
        return filename

    # remove duplicate timings
    # e.g. [[129.0, 0], [141.9, 0.0], [141.9, 0.015625]] -> [[141.9, 0.0], [141.9, 0.015625]]
    def clean_timings(self, timings):
        clean_timings_flip_dict = dict([[float(t[1]), t[0]] for t in timings])
        clean_timings_flip = [list(t) for t in clean_timings_flip_dict.items()]
        return [[t[1], float(t[0])] for t in clean_timings_flip]

    # little-endian (LE), hexdata to hexstring
    def LE(self, hexdata: list[str]) -> str:
        hexdata.reverse()
        return "".join(hexdata)

    # big-endian (BE), hexdata to hexstring
    def BE(self, hexdata: list[str]) -> str:
        return "".join(hexdata)

    # hexstring to float32
    def SingleFloat(self, hexstring: str) -> float:
        return struct.unpack("!f", bytes.fromhex(hexstring))[0]

    # Get effective section of null-terminated string (ends with x00)
    # Can't simply remove all x00 because there might also be some useless gibberish included
    # e.g. CD F2 C8 41 E7 52 00 00 11 84 D8 73 F4 03 32 00 1C 24 41 00 04 22 41 00 01 00 00 00 08 60 03 00 -> CD F2 C8 41 E7 52
    def NUL_String(self, hexdata: list[str]) -> list[str]:
        for idx in range(len(hexdata)):
            if hexdata[idx] == "00":
                return hexdata[0:idx]
        return hexdata

    # genre definition
    def get_genre_text(self, genre_num: int) -> str:
        genre_dict = {
            0: "Ballad",
            1: "Rock",
            2: "Dance",
            3: "Techno",
            4: "Hip-hop",
            5: "Soul/R&B",
            6: "Jazz",
            7: "Funk",
            8: "Classical",
            9: "Traditional",
            10: "Etc"
        }

        return genre_dict[genre_num]
       
    
    def parse_ojn_header(self, filename):
        ojn_filename = os.path.join(self.input_path, filename)
        with open(ojn_filename, "rb") as f:
            hex_raw = f.read().hex()

        self.hexdata = [hex_raw[i:i+2] for i in range(0, len(hex_raw), 2)]

        self.song_id = int(self.LE(self.hexdata[0:4]), 16)
        ojn_version_raw = self.SingleFloat(self.LE(self.hexdata[8:12]))
        self.ojn_version = f"{ojn_version_raw:.2f}"
        genre_num = int(self.LE(self.hexdata[12:16]), 16)
        self.genre_text = self.get_genre_text(genre_num)
        self.bpm = self.SingleFloat(self.LE(self.hexdata[16:20]))
        self.lvl = [
            int(self.LE(self.hexdata[20:22]), 16),
            int(self.LE(self.hexdata[22:24]), 16),
            int(self.LE(self.hexdata[24:26]), 16)
        ]
        self.total_notes = [
            int(self.LE(self.hexdata[28:32]), 16),
            int(self.LE(self.hexdata[32:36]), 16),
            int(self.LE(self.hexdata[36:40]), 16)
        ]
        self.playable_notes = [
            int(self.LE(self.hexdata[40:44]), 16),
            int(self.LE(self.hexdata[44:48]), 16),
            int(self.LE(self.hexdata[48:52]), 16)
        ]
        self.measure_count = [
            int(self.LE(self.hexdata[52:56]), 16),
            int(self.LE(self.hexdata[56:60]), 16),
            int(self.LE(self.hexdata[60:64]), 16)
        ]
        self.package_count = [
            int(self.LE(self.hexdata[64:68]), 16),
            int(self.LE(self.hexdata[68:72]), 16),
            int(self.LE(self.hexdata[72:76]), 16)
        ]

        self.title = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[108:172]))).decode(self.enc).strip(" ").rstrip("\n")
        self.artist = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[172:204]))).decode(self.enc).strip(" ").rstrip("\n")
        self.noter = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[204:236]))).decode(self.enc).strip(" ").rstrip("\n")
        self.ojm_name = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[236:268]))).decode(self.enc).strip(" ")

        self.cover_size = int(self.LE(self.hexdata[268:272]), 16)

        self.duration = [
            int(self.LE(self.hexdata[272:276]), 16),
            int(self.LE(self.hexdata[276:280]), 16),
            int(self.LE(self.hexdata[280:284]), 16)
        ]

        self.diff_offset = [
            int(self.LE(self.hexdata[284:288]), 16),
            int(self.LE(self.hexdata[288:292]), 16),
            int(self.LE(self.hexdata[292:296]), 16)
        ]
        self.cover_offset = int(self.LE(self.hexdata[296:300]), 16)

        # used for parsing notes
        self.diff_size = [
            self.diff_offset[1] - self.diff_offset[0],
            self.diff_offset[2] - self.diff_offset[1],
            self.cover_offset - self.diff_offset[2],
        ]

        # skip duplicate chart (with same diff size)
        # Sometimes diff_size are the same but playable notes are different (o2ma392 - God Knows Piano Ver by Doaz)
        self.skip_diff = [False] * 3

        if self.diff_size[0] == self.diff_size[1] and self.playable_notes[0] == self.playable_notes[1]:
            self.skip_diff[0] = True
        if self.diff_size[1] == self.diff_size[2] and self.playable_notes[1] == self.playable_notes[2]:
            self.skip_diff[1] = True
        if self.diff_size[2] == self.diff_size[0] and self.playable_notes[2] == self.playable_notes[0]:
            self.skip_diff[2] = True

        # if all diffs are the same, only extract the last one
        if self.skip_diff == [True] * 3:
            self.skip_diff[2] = False

        if self.skip_diff != [False] * 3:
            for idx in range(len(self.skip_diff)):
                if self.skip_diff[idx]: 
                    self.info_log(f"Duplicate diff: {self.diff_scale[idx]}, will skip!")


    # parse jpeg background image
    def parse_image(self):
        self.image_raw = bytes.fromhex(self.BE(self.hexdata[self.cover_offset:self.cover_offset + self.cover_size]))


    # parse all 3 diffs
    def parse_diff(self):
        '''
        channel  meaning
        0        measure fraction
        1        BPM change
        2        note on 1st lane
        3        note on 2nd lane
        4        note on 3rd lane
        5        note on 4th lane (middle button)
        6        note on 5th lane
        7        note on 6th lane
        8        note on 7th lane
        9~22     auto-play samples(?)
        '''
        self.diff_notes = {
            0: [],
            1: [],
            2: []
        }
        
        self.diff_timings = {
            0: [],
            1: [],
            2: []
        }

        # This is for channel == 0
        self.diff_frac_measure = {
            0: [],
            1: [],
            2: []
        }

        self.diff_autoplay_samples = {
            0: [],
            1: [],
            2: []
        }
        
        for diff_idx in range(len(self.diff_size)):
            # skip if duplicate
            if self.skip_diff[diff_idx]:
                continue
            
            # get current diff hexdata
            diff_start = self.diff_offset[diff_idx]
            diff_end = diff_start + self.diff_size[diff_idx]
            diff_raw = self.hexdata[diff_start:diff_end]
            self.curr_diff = f"{self.diff_scale[diff_idx]} (lvl {self.lvl[diff_idx]})"

            pos = 0

            # Initial BPM
            timings = [[self.bpm, 0]]

            # dicts in list: type, lane, sample_value, sample_volume, sample_pan, measure_start, measure_end (if ln)
            # type -> 0 = rice; 1 = ln
            # lane -> 0-6 (channel - 2)
            notes = []

            # long notes pairing list (temporary, paired ln will then be moved to notes)
            ln_notes = []

            # autoplay samples [sample_no, sample_volume, measure]
            # sample_volume -> 0-15, 0 = maximum
            autoplay_samples = []

            # channel 0 fraction measure [measure, frac]
            frac_measure = []

            # try to get divisor of the song (might not be reliable)
            temp_pos = 0
            for package_idx in range(self.package_count[diff_idx]):
                events = int(self.LE(diff_raw[temp_pos+6:temp_pos+8]), 16)
                temp_pos += 8

                if events == 1:
                    continue

                if events % 4 == 0:
                    self.divisor = 4
                    break
                if events % 3 == 0:
                    self.divisor = 3
                    break

            # get notes for each diff
            for package_idx in range(self.package_count[diff_idx]):
                # read package header
                _debug_package_header = diff_raw[pos:pos+8]
                measure = int(self.LE(diff_raw[pos:pos+4]), 16)
                channel = int(self.LE(diff_raw[pos+4:pos+6]), 16)
                events = int(self.LE(diff_raw[pos+6:pos+8]), 16)
                pos += 8

                _debug_package_content = diff_raw[pos:pos+events*4]
                

                # When the channel is 0 (fractional measure), the 4 bytes are a float, indicating how much of the measure is actually used, so if the value is 0.75, the size of this measure will be only 75% of a normal measure.
                # Looks like note's measure_start will not exceed frac_measure (e.g. frac_measure = 0.5, note measure = .125, .25, .375, .4375)
                if channel == 0:
                    frac = self.SingleFloat(self.LE(diff_raw[pos:pos+4]))
                    frac_measure.append([measure, frac])
                    #self.error_log(f"channel == 0, not implemented! frac = {frac_measure}, measure = {measure}")

                # When the channel is 1 (BPM change) these 4 bytes are a float with the new BPM.
                elif channel == 1:
                    for i in range(events):
                        new_bpm = self.SingleFloat(self.LE(diff_raw[pos+4*i:pos+4*(i+1)]))
                        if new_bpm == 0:
                            continue
                        timings.append([new_bpm, measure + i / events])

                # When channel > 1, these 4 bytes are divided like this:
                # short16 sample_value; (2 bytes)
                # half-char sample_volume; (0.5 byte)
                # half-char pan; (0.5 byte)
                # char note_type; (1 byte)

                # channel is 2-8 (playable notes)
                elif 2 <= channel <= 8:
                    for i in range(events):
                        # 0 -> ignored; other -> sample in ojm
                        sample_value = int(self.LE(diff_raw[pos+4*i:pos+4*i+2]), 16)
                        if sample_value == 0:
                            continue

                        # sample volume (0-15), 0 is maximum
                        sample_volume = int(diff_raw[pos+4*i+2][0], 16)
                        
                        # 1~7 = left -> center, 0 or 8 = center, 9~15 = center -> right
                        sample_pan = int(diff_raw[pos+4*i+2][1], 16)
                        note_type = int(self.LE([diff_raw[pos+4*i+3]]), 16)

                        # note_type = 4 -> normal note & use ogg sample
                        if note_type == 4:
                            note_type = 0
                            sample_value += 1000
                        
                        # rice
                        if note_type == 0:
                            notes.append({
                                "type": 0,
                                "lane": channel - 2,
                                "sample_value": sample_value,
                                "sample_volume": sample_volume,
                                "sample_pan": sample_pan,
                                "measure_start": measure + i / events
                            })
                        
                        # ln start (put it in ln_notes for pairing)
                        elif note_type == 2:
                            ln_notes.append({
                                "type": 1,
                                "lane": channel - 2,
                                "sample_value": sample_value,
                                "sample_volume": sample_volume,
                                "sample_pan": sample_pan,
                                "measure_start": measure + i / events
                            })
                        
                        # ln end (pair with ln start in ln_notes)
                        elif note_type == 3:
                            # find "ln start" in ln_notes with same channel
                            lane = channel - 2
                            measure_end = measure + i / events
                            match = [] # [idx, measure_start]
                            for idx in range(len(ln_notes)):
                                if lane == ln_notes[idx]["lane"]:
                                    match.append([idx, ln_notes[idx]["measure_start"]])
                            match.sort(key=lambda x: x[1], reverse=True) # higher measure comes first
                            
                            flag_paired = False

                            # pairing algorithm (always go for the longest possible ln, and remove all the extra ln heads between them)
                            # Following examples: H1 = ln head #1, T1 = ln tail #1
                            # Note: ln head always comes before ln tail in ojn raw data
                            # e.g. H1 H2 T1 -> (H1 T1), remove H2 because it's invalid ln head (If we pair H2 with T1, then there should be a T0 that comes before T1 to pair with H1, like H1 T0 H2 T1)
                            # e.g. H1 T1 H2 -> (H1 T1), keep H2 because there might be a T2 coming to pair with H2
                            if len(match) > 0:
                                if measure_end > match[-1][1]:
                                    ln_notes[match[-1][0]]["measure_end"] = measure_end
                                    notes.append(ln_notes[match[-1][0]])
                                    for idx in range(len(match)):
                                        if measure_end > match[idx][1]:
                                            ln_notes.pop(match[idx][0])
                                    flag_paired = True

                            # if there's no ln head to pair with, we can consider the ln tail invalid and safely drop it
                            if not flag_paired:
                                self.warning_log(f"Failed to pair ln notes! Usually this warning can be ignored.")
                                if self.debug:
                                    ln_tail_info = {
                                    "package_idx": package_idx,
                                    "measure": measure,
                                    "lane": lane,
                                    "measure_end": measure_end,
                                    }
                                    print(f"ln_tail_info = {ln_tail_info}")
                                    print(f"match = {match}")
                                    print(f"ln_notes = {ln_notes}")
                
                # channel is 9-22 (autoplay notes)
                # As far as I know these are usually 9-15
                else:
                    for i in range(events):
                        note_type = int(self.LE([diff_raw[pos+4*i+3]]), 16)

                        sample_value = int(self.LE(diff_raw[pos+4*i:pos+4*i+2]), 16)
                        
                        # always ignore the event when sample_value is 0
                        if sample_value == 0:
                            continue

                        # note_type = 4 -> ogg sample (sample_value > 1000)
                        # note_type = 0 -> ogg/wav sample (sample_value < 1000)
                        if note_type == 4:
                            sample_value += 1000
                        elif note_type != 0:
                            #self.warning_log(f"Unrecognized autoplay sample note_type: {diff_raw[pos+4*i:pos+4*i+4]}, events # = {events}, channel # = {channel}, note_type = {note_type}")
                            continue
                        
                        # to match the OJM sample value
                        sample_value += 1

                        # ignore the event if there's no actual hitsound file extracted from OJM to play
                        if sample_value not in self.ojm.sound_dict:
                            continue
                        
                        sample_volume = int(diff_raw[pos+4*i+2][0], 16)
                        autoplay_samples.append([sample_value, sample_volume, measure + i / events])
                        if self.debug:
                            print(f"{diff_raw[pos+4*i:pos+4*i+4]}, channel = {channel}")
                            print(f"autoplay_sample = {[sample_value, sample_volume, measure + i / events]}")

                pos += events * 4
            
            if len(ln_notes) > 0:
                self.warning_log(f"ln_notes = {ln_notes}")
            
            notes.sort(key=lambda x: x["measure_start"])
            self.diff_notes[diff_idx] = notes
            self.diff_frac_measure[diff_idx] = frac_measure
            
            # insert timing point with same bpm right after the fractional measure
            timings = self.clean_timings(timings)
            for f_idx in range(len(frac_measure)):
                for t_idx in range(len(timings)):
                    target_measure = frac_measure[f_idx][0] + 1
                    if timings[t_idx][1] == target_measure:
                        break
                    elif timings[t_idx][1] > target_measure:
                        timings.append([timings[t_idx-1][0], target_measure])
                        break
            
            timings.sort(key=lambda x: x[1])
            self.diff_timings[diff_idx] = timings
            self.diff_autoplay_samples[diff_idx] = autoplay_samples
            
        
    # generate .osu, .jpg, .mp3
    def export_osu(self):
        # generate .osu
        odhp_scale = [
            [7, 8],
            [5, 7],
            [2, 5]
        ]

        mp3_dict = {} # {duration: output_filename}
        audio_filename = "virtual"
        preview_time = "1234"
        
        for diff_idx in range(len(self.diff_size)):
            # skip if duplicate
            if self.skip_diff[diff_idx]:
                continue
            
            self.curr_diff = f"lvl {self.lvl[diff_idx]}"
            curr_mp3_remix_list = [] # [time (ms), audio_filename]

            # Dynamic hp & od
            if self.lvl[diff_idx] < 70:
                odhp = odhp_scale[0]
            elif 70 <= self.lvl[diff_idx] <= 90:
                odhp = odhp_scale[1]
            else:
                odhp = odhp_scale[2]
            
            
            # Calculate timing points (convert o2jam measure to osu offset)
            ms_previous_bpm = 60000 / self.bpm * self.divisor
            
            for t_idx in range(len(self.diff_timings[diff_idx])):
                t: list = self.diff_timings[diff_idx][t_idx] # t = [bpm, measure]
                current_bpm = t[0]
                current_measure = t[1]
                
                ms_per_measure = 60000 / current_bpm

                if ms_per_measure < 1:
                    ms_per_measure = 1
                    current_bpm = 60000
                
                frac_delta = 0
                
                if t_idx == 0:
                    offset = round(current_measure * ms_previous_bpm) # this starting offset should be 0 most of the time
                else:
                    # calculate fractional measure
                    for f_idx in range(len(self.diff_frac_measure[diff_idx])):
                        critical_measure = sum(self.diff_frac_measure[diff_idx][f_idx])
                        if previous_measure <= critical_measure < current_measure:
                            frac_delta += 1 - self.diff_frac_measure[diff_idx][f_idx][1]
                    offset = round(previous_offset + ms_previous_bpm * (current_measure - previous_measure - frac_delta))
                t.extend([offset, ms_per_measure]) # t = [bpm, measure, offset, ms_per_measure]
                ms_previous_bpm = 60000 / current_bpm * self.divisor
                previous_offset = offset
                previous_measure = current_measure

            curr_diff_timings = copy.deepcopy(self.diff_timings[diff_idx])

            curr_diff_timings.sort(key=lambda x: x[1], reverse=True) # sort by measure (reverse order)
            
            def get_note_offset(measure_val):
                offset = 0
                for t_idx in range(len(curr_diff_timings)):
                    if measure_val >= curr_diff_timings[t_idx][1]:
                        measure_delta = measure_val - curr_diff_timings[t_idx][1]
                        offset_delta = measure_delta * (60000 / curr_diff_timings[t_idx][0] * self.divisor)
                        offset = curr_diff_timings[t_idx][2] + offset_delta
                        return math.floor(offset)


            # [Event] Calculate autoplay ogg samples offset here
            ogg_volumes = [math.floor(x * 100 / 15) for x in range(16)]
            ogg_volumes.sort(reverse=True)

            for ogg in self.diff_autoplay_samples[diff_idx]:
                # ogg = [sample_id, sample_volume, measure]
                sample_id = ogg[0]
                measure = ogg[2]
                ext = self.ojm.sound_dict[sample_id] # already filtered in parse_diff(), so we can safely read from sound_dict
                ogg.extend([get_note_offset(measure), ext]) # ogg = [sample_id, sample_volume, measure, offset, ext]
            
            
            mp3_offset = 0 # If flag_use_mp3 == True, this will be a negative number
            first_autoplay_ms = 0 # first autoplay event offset
            first_note_ms = 0 # first note offset
            

            # if convert mp3, need to shift the whole chart because autoplay event doesn't start at 0ms
            if self.flag_use_mp3:
                # Get the first autoplay event offset
                for ogg in self.diff_autoplay_samples[diff_idx]:
                    # ogg = [sample_id, sample_volume, measure, offset, ext]
                    first_autoplay_ms = ogg[3]
                    break

                # Get the first note offset
                for note in self.diff_notes[diff_idx]:
                    first_note_ms = get_note_offset(note["measure_start"])
                    break

                if first_autoplay_ms < first_note_ms:
                    mp3_offset = -first_autoplay_ms

                
                # prevent negative ms notes
                if ogg[2] < self.diff_notes[diff_idx][0]['measure_start']:
                    mp3_offset += self.extra_offset
                    

                # Shift curr_diff_timings by mp3_offset
                for t in curr_diff_timings:
                    t[2] += mp3_offset
                for t in self.diff_timings[diff_idx]:
                    t[2] += mp3_offset

                # Shift all events by mp3_offset
                for ogg in self.diff_autoplay_samples[diff_idx]:
                    ogg[3] += mp3_offset
                    # minus self.extra_offset here because extra offset should only apply to chart, not the song
                    curr_mp3_remix_list.append([ogg[3] - self.extra_offset, f"normal-hitnormal{ogg[0]}.{ogg[4]}"])


            osu_file = "osu file format v14\n\n"

            osu_editor = [
                "[Editor]",
                "DistanceSpacing: 0.7",
                "BeatDivisor: 8",
                "GridSize: 8",
                "TimelineZoom: 2"
            ]

            osu_metadata = [
                "[Metadata]",
                f"Title:{self.title}",
                f"TitleUnicode:{self.title}",
                f"Artist:{self.artist}",
                f"ArtistUnicode:{self.artist}",
                f"Creator:{self.noter}",
                f"Version:{self.curr_diff}",
                f"Source:o2jam",
                f"Tags:o2jam {self.ojm_name.split('.')[0]}",
                "BeatmapID:0",
                "BeatmapSetID:-1"
            ]

            osu_difficulty = [
                "[Difficulty]",
                f"HPDrainRate:{odhp[1]}",
                "CircleSize:7",
                f"OverallDifficulty:{odhp[0]}",
                "ApproachRate:7",
                "SliderMultiplier:1",
                "SliderTickRate:1"
            ]

            osu_events = [
                "[Events]",
                "//Background and Video events",
                f"0,0,\"background_{self.song_id}.jpg\",0,0",
                "//Break Periods",
                "//Storyboard Layer 0 (Background)",
                "//Storyboard Layer 1 (Fail)",
                "//Storyboard Layer 2 (Pass)",
                "//Storyboard Layer 3 (Foreground)",
                "//Storyboard Layer 4 (Overlay)",
                "//Storyboard Sound Samples"
            ]

            if self.flag_use_mp3:
                pass
            else:
                for ogg in self.diff_autoplay_samples[diff_idx]:
                    sample_id = ogg[0]
                    sample_volume = ogg[1]
                    offset = ogg[3]
                    ext = ogg[4]
                    osu_events.append(f"5,{offset},0,\"normal-hitnormal{sample_id}.{ext}\",{ogg_volumes[sample_volume]}")

            osu_timing_points = ["[TimingPoints]"]

            # find correct starting offset when using mp3
            if self.flag_use_mp3:
                first_note_measure = self.diff_notes[diff_idx][0]['measure_start']
                timing_measure_lst = [t[1] for t in self.diff_timings[diff_idx]]
                new_start_measure = float(math.floor(first_note_measure))
                try:
                    index = timing_measure_lst.index(new_start_measure)
                except ValueError: # if not found
                    index = -1
                
                timing_remove = []
                
                if index >= 0:
                    timing_remove = list(reversed(range(index)))
                    for i in timing_remove:
                        self.diff_timings[diff_idx].pop(i)
                else:
                    if len(timing_measure_lst) == 1:
                        self.diff_timings[diff_idx][0][1] = new_start_measure
                        self.diff_timings[diff_idx][0][2] = get_note_offset(new_start_measure)
                    else:
                        for m_idx in range(len(timing_measure_lst)):
                            if timing_measure_lst[m_idx] > new_start_measure:
                                timing_remove = list(reversed(range(m_idx)))
                                bpm = self.diff_timings[diff_idx][m_idx - 1][0]
                                offset = get_note_offset(new_start_measure)
                                ms_per_measure = self.diff_timings[diff_idx][m_idx - 1][3]

                                for i in timing_remove:
                                    self.diff_timings[diff_idx].pop(i)
                                
                                self.diff_timings[diff_idx].insert(0, [bpm, new_start_measure, offset, ms_per_measure])
                                break


            for t_idx in range(len(self.diff_timings[diff_idx])):
                t: list = self.diff_timings[diff_idx][t_idx] # t = [bpm, measure, offset, ms_per_measure]
                offset = t[2]
                ms_per_measure = t[3]
                if self.flag_nsv:
                    # try to use the measure 0 (start) bpm if possible
                    if max(self.bpm, t[0]) % min(self.bpm, t[0]) == 0 and self.bpm < 60000:
                        ms_per_measure = 60000 / self.bpm

                osu_timing_points.append(f"{offset},{ms_per_measure},4,2,2,10,1,0")
                if self.flag_nsv:
                    break
           
            osu_hitobjects = ["[HitObjects]"]
            
            # populate all notes in osu format
            osu_col_coord = [math.floor((512 / 7) * (i + 0.5)) for i in range(7)]
            for n in self.diff_notes[diff_idx]:
                sample_id = n['sample_value'] + 1
                offset = get_note_offset(n['measure_start'])

                if sample_id not in self.ojm.sound_dict:
                    flag_no_keysound = True
                    ext = None
                else:
                    flag_no_keysound = False
                    ext = self.ojm.sound_dict[sample_id]
                
                
                hitsound = f"normal-hitnormal{sample_id}.{ext}"

                if self.flag_use_mp3 and not flag_no_keysound:
                    # minus self.extra_offset here because extra offset should only apply to chart, not the song
                    curr_mp3_remix_list.append([offset - self.extra_offset, hitsound])
                
                if n["type"] == 0:
                    res_str = f"1,0,0:0:0"
                else: # ln needs offset_end
                    offset_end = get_note_offset(n['measure_end'])
                    res_str = f"128,0,{offset_end}:0:0:0"
                

                if flag_no_keysound or self.flag_use_mp3:
                    osu_hitobjects.append(f"{osu_col_coord[n['lane']]},0,{offset},{res_str}:0:")
                else:
                    osu_hitobjects.append(f"{osu_col_coord[n['lane']]},0,{offset},{res_str}:100:{hitsound}")


            # Create MP3
            if self.flag_use_mp3:
                if self.duration[diff_idx] not in mp3_dict:
                    output_filename = f"audio_{self.song_id}.mp3"
                    if len(mp3_dict) > 0:
                        output_filename = f"audio_{self.song_id}_{self.diff_scale[diff_idx]}.mp3"
                    
                    if len(curr_mp3_remix_list) == 1:
                        sound_filename = curr_mp3_remix_list[0][1]
                        audio_lib.to_mp3(self.song_path, sound_filename, output_filename)
                    elif len(curr_mp3_remix_list) > 1:
                        audio_lib.merge_mp3(self.song_path, curr_mp3_remix_list, output_filename)
                    
                    audio_filename = output_filename # used by osu_general    
                    # always preview at 1/4 duration of the song
                    preview_time = math.floor(audio_lib.get_audio_length(self.song_path, audio_filename) / 4) # used by osu_general

                    mp3_dict[self.duration[diff_idx]] = output_filename
            
            
            osu_general = [
                "[General]",
                f"AudioFilename: {audio_filename}",
                "AudioLeadIn: 0",
                f"PreviewTime: {preview_time}",
                "Countdown: 0",
                "SampleSet: Soft",
                "StackLeniency: 0.7",
                "Mode: 3",
                "LetterboxInBreaks: 0",
                "SpecialStyle: 0",
                "WidescreenStoryboard: 1"
            ]
            
            sections = [
                osu_general,
                osu_editor,
                osu_metadata,
                osu_difficulty,
                osu_events,
                osu_timing_points,
                osu_hitobjects
            ]

            for idx in range(len(sections)):
                for line in sections[idx]:
                    osu_file += line + "\n"
                if idx != len(sections) - 1:
                    osu_file += "\n\n"
            
            
            osu_filename = os.path.join(self.song_path, self.safe_filename(f"{self.artist} - {self.title} ({self.noter}) [lvl {self.lvl[diff_idx]}].osu"))
            with open((osu_filename), "w", encoding="utf-8") as f:
                f.write(osu_file)

        # generate .jpg
        jpg_filename = os.path.join(self.song_path, f"background_{self.song_id}.jpg")
        if len(self.image_raw) > 0:
            with open(jpg_filename, "wb") as f:
                f.write(self.image_raw)
        else:
            self.info_log(f"Song id = {self.song_id}, no image found")

        if self.flag_use_mp3:
            audio_lib.clean_up(self.song_path)


    # use OJMExtract to extract audio files
    def parse_audio(self):
        self.ojm = OJMExtract()
        self.ojm.song_path = self.song_path
        self.ojm.enc = self.enc
        self.ojm.debug = self.debug
        self.ojm.input_path = self.input_path
        self.ojm.output_path = self.output_path
        self.ojm.dump_file(self.curr_ojn_file.replace(".ojn", ".ojm"))
    
    
    def o2jam_to_osu(self, ojn_list):
        for ojn in ojn_list:
            self.curr_ojn_file = ojn
            self.parse_ojn_header(ojn)
            if self.debug:
                self._ojn_header_debug()
            self.song_path = os.path.join(self.output_path, self.safe_filename(f"{self.artist} - {self.title} ({self.song_id})"))
            
            if os.path.exists(self.song_path):
                self.info_log(f"Song id = {self.song_id} exists, skip!")
            else:
                self.info_log(f"Song id = {self.song_id}, parsing...")
                # create directory if not exist
                # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
                os.makedirs(os.path.dirname(os.path.join(self.song_path, "cow.osu")), exist_ok=True)
                self.parse_audio()
                self.parse_image()
                self.parse_diff()
                self.export_osu()
                self.info_log(f"Song id = {self.song_id}, success!")