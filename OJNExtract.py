import os
import math
import struct
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
        self.enc = "gb18030"

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
        print(f"[ERROR] <{self.song_id}> {self.artist} - {self.title} ({self.noter}) [{self.curr_diff}]")
        print(msg)

    # remove illegal filename characters on Windows
    def safe_filename(self, filename):
        illegal_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
        for c in illegal_chars:
            filename = filename.replace(c, "")
        return filename

    # remove duplicate timings (keep larger bpm)
    # e.g. [[129.0, 0], [141.9, 0.0], [141.9, 0.015625]] -> [[141.9, 0.0], [141.9, 0.015625]]
    def validate_timings(self, timings):
        clean_timings_rev_dict = dict([[float(t[1]), t[0]] for t in timings])
        clean_timings_rev = [list(t) for t in clean_timings_rev_dict.items()]
        return [[t[1], float(t[0])] for t in clean_timings_rev]

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

        self.title = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[108:172]))).decode(self.enc)
        self.artist = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[172:204]))).decode(self.enc)
        self.noter = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[204:236]))).decode(self.enc)
        self.ojm_name = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[236:268]))).decode(self.enc)

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

        self.diff_ogg_samples = {
            0: [],
            1: [],
            2: []
        }
        
        for diff_idx in range(len(self.diff_size)):
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

            # ogg samples [sample_no, sample_volume, measure]
            # sample_volume -> 0-15, 0 = maximum
            ogg_samples = []

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
                if channel == 0:
                    frac_measure = self.SingleFloat(self.LE(diff_raw[pos:pos+4]))
                    print("channel == 0, not implemented!")

                # When the channel is 1 (BPM change) these 4 bytes are a float with the new BPM.
                elif channel == 1:
                    for i in range(events):
                        new_bpm = self.SingleFloat(self.LE(diff_raw[pos+4*i:pos+4*(i+1)]))
                        if new_bpm == 0:
                            continue
                        timings.append([new_bpm, measure + i / events])

                # When the channel is 2-8 (notes) these 4 bytes are divided like this.               
                # short16 sample_value; (2 bytes)
                # half-char sample_volume; (0.5 byte)
                # half-char pan; (0.5 byte)
                # char note_type; (1 byte)  
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
                            sample_value += 1000 # TODO
                        
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

                            paired = False

                            # incase len(match) > 1
                            for idx in range(len(match)):
                                # find shortest possible paired ln to avoid stacked notes
                                if measure_end > match[idx][1]:
                                    ln_notes[match[idx][0]]["measure_end"] = measure_end
                                    notes.append(ln_notes[match[idx][0]])
                                    ln_notes.pop(match[idx][0])
                                    paired = True
                                    break

                            if not paired:
                                error_info = {
                                    "package_idx": package_idx,
                                    "measure": measure,
                                    "channel": channel,
                                    "events": events,
                                    "ln_notes": ln_notes,
                                    "match": match,
                                    "lane": lane,
                                    "measure_end": measure_end,
                                }
                                self.error_log(f"Failed to pair ln notes! {error_info}")
                # channel is 9-22
                else:
                    for i in range(events):
                        note_type = int(self.LE([diff_raw[pos+4*i+3]]), 16)

                        sample_value = int(self.LE(diff_raw[pos+4*i:pos+4*i+2]), 16)
                        
                        # note_type = 4 -> normal note & use ogg sample
                        if note_type != 4:
                            continue                    
                        
                        sample_volume = int(diff_raw[pos+4*i+2][0], 16)
                        ogg_samples.append([sample_value, sample_volume, measure + i / events])
                        if self.debug:
                            print(f"{diff_raw[pos+4*i:pos+4*i+4]}, channel = {channel}")
                            print(f"ogg_sample = {[sample_value, sample_volume, measure + i / events]}")

                pos += events * 4
            
            notes.sort(key=lambda x: x["measure_start"])
            self.diff_notes[diff_idx] = notes
            self.diff_timings[diff_idx] = self.validate_timings(timings)
            self.diff_ogg_samples[diff_idx] = ogg_samples
        
    # generate .osu, .jpg, .mp3
    def export_osu(self):
        # generate .osu
        odhp_scale = [
            [7, 8],
            [5, 7],
            [2, 5]
        ]
        for diff_idx in range(len(self.diff_size)):
            self.curr_diff = f"lvl {self.lvl[diff_idx]}"
            
            # Dynamic hp & od
            if self.lvl[diff_idx] < 70:
                odhp = odhp_scale[0]
            elif 70 <= self.lvl[diff_idx] <= 90:
                odhp = odhp_scale[1]
            else:
                odhp = odhp_scale[2]
            
            osu_file = "osu file format v14\n\n"
            
            osu_general = [
                "[General]",
                "AudioFilename: virtual",
                "AudioLeadIn: 0",
                "PreviewTime: 1234",
                "Countdown: 0",
                "SampleSet: Soft",
                "StackLeniency: 0.7",
                "Mode: 3",
                "LetterboxInBreaks: 0",
                "SpecialStyle: 0",
                "WidescreenStoryboard: 1"
            ]

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

            osu_timing_points = ["[TimingPoints]"]

            ms_previous_bpm = 60000 / self.bpm * self.divisor
            
            for t_idx in range(len(self.diff_timings[diff_idx])):
                t: list = self.diff_timings[diff_idx][t_idx] # t = [bpm, measure]
                ms_per_measure = 60000 / t[0]
                if ms_per_measure < 0.001:
                    ms_per_measure = 0.001
                    self.error_log(f"Abnormal timing points! TimingPoints = {self.diff_timings[diff_idx]}; bpm = {t[0]}")
                
                if t_idx == 0:
                    offset = round(t[1]*ms_previous_bpm)
                    osu_timing_points.append(f"{offset},{ms_per_measure},4,2,2,10,1,0")
                else:
                    offset = round(previous_offset + ms_previous_bpm * (t[1] - previous_measure))
                    osu_timing_points.append(f"{offset},{ms_per_measure},4,2,2,10,1,0")
                t.append(offset) # t = [bpm, measure, offset]
                ms_previous_bpm = 60000 / t[0] * self.divisor
                previous_offset = offset
                previous_measure = t[1]
            
            osu_hitobjects = ["[HitObjects]"]

            osu_col_coord = [math.floor((512 / 7) * (i + 0.5)) for i in range(7)]

            self.diff_timings[diff_idx].sort(key=lambda x: x[1], reverse=True)
            
            def get_note_offset(measure_val):
                offset = 0
                for t_idx in range(len(self.diff_timings[diff_idx])):
                    if measure_val > self.diff_timings[diff_idx][t_idx][1]:
                        measure_delta = measure_val - self.diff_timings[diff_idx][t_idx][1]
                        offset_delta = measure_delta * (60000 / self.diff_timings[diff_idx][t_idx][0] * self.divisor)
                        offset = self.diff_timings[diff_idx][t_idx][2] + offset_delta
                        return math.floor(offset)

            for n in self.diff_notes[diff_idx]:
                # rice
                if n["type"] == 0:
                    offset = get_note_offset(n['measure_start'])
                    osu_hitobjects.append(f"{osu_col_coord[n['lane']]},0,{offset},1,0,0:0:0:{n['sample_volume']}:normal-hitnormal{n['sample_value']}.ogg")
                else:
                    offset_start = get_note_offset(n['measure_start'])
                    offset_end = get_note_offset(n['measure_end'])
                    osu_hitobjects.append(f"{osu_col_coord[n['lane']]},0,{offset_start},128,0,{offset_end}:0:0:0:{n['sample_volume']}:normal-hitnormal{n['sample_value']}.ogg")

            # Calculate ogg samples here
            ogg_volumes = [math.floor(x * 100 / 15) for x in range(15)]
            ogg_volumes.sort(reverse=True)

            for ogg in self.diff_ogg_samples[diff_idx]:
                sample_id = "1" + str(ogg[0]).zfill(3)
                osu_events.append(f"5,{get_note_offset(ogg[2])},0,\"normal-hitnormal{sample_id}.ogg\",{ogg_volumes[ogg[1]]}")

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
            # create directory if not exist
            # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
            os.makedirs(os.path.dirname(osu_filename), exist_ok=True)

            with open((osu_filename), "w", encoding="utf-8") as f:
                f.write(osu_file)

        # generate .jpg
        jpg_filename = os.path.join(self.song_path, f"background_{self.song_id}.jpg")
        if len(self.image_raw) > 0:
            with open(jpg_filename, "wb") as f:
                f.write(self.image_raw)
        else:
            print(f"Song id = {self.song_id}, no image found")

    # use OJMExtract to extract audio files
    def parse_audio(self):
        ojm = OJMExtract()
        ojm.song_path = self.song_path
        ojm.enc = self.enc
        ojm.dump_file(self.ojm_name)
    
    
    def o2jam_to_osu(self, ojn_list):
        for ojn in ojn_list:
            self.parse_ojn_header(ojn)
            if self.debug:
                self._ojn_header_debug()
            self.song_path = os.path.join(self.output_path, self.safe_filename(f"{self.song_id} {self.artist} - {self.title}"))
            
            if os.path.exists(self.song_path):
                print(f"Song id = {self.song_id} exists, skip!")
            else:
                print(f"Song id = {self.song_id}, parsing...")
                self.parse_image()
                self.parse_diff()
                self.export_osu()
                self.parse_audio()
                print(f"Song id = {self.song_id}, success!")