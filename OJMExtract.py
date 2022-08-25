import copy
import os
import math
import struct

# a python implementation of the ojm dumper based on information from open2jam
class OJMExtract():
    def __init__(self):   
        # the xor mask used in the M30 format
        # ["6E", "61", "6D", "69"] = ["n", "a", "m", "i"], hence the name
        # Further explanation: hex(ord("n")) = '0x6e'
        self.nami = ["6E", "61", "6D", "69"]

        # the M30 signature", "M30\0" in little endian
        self.M30_SIGNATURE = "0030334D"

        # the OMC signature", "OMC\0" in little endian
        self.OMC_SIGNATURE = "00434D4F"

        # the OJM signature", "OJM\0" in little endian
        self.OJM_SIGNATURE = "004D4A4F"

        # this is a dump from debugging notetool
        self.REARRANGE_TABLE = [
            "10", "0E", "02", "09", "04", "00", "07", "01",
            "06", "08", "0F", "0A", "05", "0C", "03", "0D",
            "0B", "07", "02", "0A", "0B", "03", "05", "0D",
            "08", "04", "00", "0C", "06", "0F", "0E", "10",
            "01", "09", "0C", "0D", "03", "00", "06", "09",
            "0A", "01", "07", "08", "10", "02", "0B", "0E",
            "04", "0F", "05", "08", "03", "04", "0D", "06",
            "05", "0B", "10", "02", "0C", "07", "09", "0A",
            "0F", "0E", "00", "01", "0F", "02", "0C", "0D",
            "00", "04", "01", "05", "07", "03", "09", "10",
            "06", "0B", "0A", "08", "0E", "00", "04", "0B",
            "10", "0F", "0D", "0C", "06", "05", "07", "01",
            "02", "03", "08", "09", "0A", "0E", "03", "10",
            "08", "07", "06", "09", "0E", "0D", "00", "0A",
            "0B", "04", "05", "0C", "02", "01", "0F", "04",
            "0E", "10", "0F", "05", "08", "07", "0B", "00",
            "01", "06", "02", "0C", "09", "03", "0A", "0D",
            "06", "0D", "0E", "07", "10", "0A", "0B", "00",
            "01", "0C", "0F", "02", "03", "08", "09", "04",
            "05", "0A", "0C", "00", "08", "09", "0D", "03",
            "04", "05", "10", "0E", "0F", "01", "02", "0B",
            "06", "07", "05", "06", "0C", "04", "0D", "0F",
            "07", "0E", "08", "01", "09", "02", "10", "0A",
            "0B", "00", "03", "0B", "0F", "04", "0E", "03",
            "01", "00", "02", "0D", "0C", "06", "07", "05",
            "10", "09", "08", "0A", "03", "02", "01", "00",
            "04", "0C", "0D", "0B", "10", "05", "06", "0F",
            "0E", "07", "09", "0A", "08", "09", "0A", "00",
            "07", "08", "06", "10", "03", "04", "01", "02",
            "05", "0B", "0E", "0F", "0D", "0C", "0A", "06",
            "09", "0C", "0B", "10", "07", "08", "00", "0F",
            "03", "01", "02", "05", "0D", "0E", "04", "0D",
            "00", "01", "0E", "02", "03", "08", "0B", "07",
            "0C", "09", "05", "0A", "0F", "04", "06", "10",
            "01", "0E", "02", "03", "0D", "0B", "07", "00",
            "08", "0C", "09", "06", "0F", "10", "05", "0A",
            "04", "00"
        ]

        self.input_path = os.path.join(os.getcwd(), "input")
        self.output_path = os.path.join(os.getcwd(), "output")

        # These two will be passed from OJNExtract
        self.enc = None
        self.song_path = None
        # This will be passed when dump_file() is called
        self.filename = None
    
    # little-endian (LE), hexdata to hexstring
    def LE(self, hexdata: list[str]) -> str:
        hexdata.reverse()
        return "".join(hexdata).upper()

    # big-endian (BE), hexdata to hexstring
    def BE(self, hexdata: list[str]) -> str:
        return "".join(hexdata).upper()

    # hexstring to float32
    def SingleFloat(self, hexstring: str) -> float:
        return struct.unpack("!f", bytes.fromhex(hexstring))[0]

    # Get effective section of null-terminated string (ends with x00)
    def NUL_String(self, hexdata: list[str]) -> list[str]:
        for idx in range(len(hexdata)):
            if hexdata[idx] == "00":
                return hexdata[0:idx]
        return hexdata

    # convert text to hex
    # e.g. "RIFF" -> ['52', '49', '46', '46']
    def text_to_hex(self, text: str) -> list[str]:
        return [hex(ord(x))[2:] for x in text]

    # convert int to hex
    # e.g. 132336 -> '0x204f0' -> ['F0', '04', '02', '00']
    def int_to_hex(self, num: int, fill=8, LE=True) -> list[str]:
        hex_raw = hex(num)[2:].zfill(fill)
        hexdata = [hex_raw[i:i+2] for i in range(0, len(hex_raw), 2)]
        if LE:
            hexdata.reverse()
        return hexdata

    # nami decryption for M30 format
    def nami_xor(self, hexdata):
        for i in range(0, len(hexdata) - 3, 4):
            hexdata[i+0] = hex(int(hexdata[i+0], 16) ^ int(self.nami[0], 16))[2:].zfill(2)
            hexdata[i+1] = hex(int(hexdata[i+1], 16) ^ int(self.nami[1], 16))[2:].zfill(2)
            hexdata[i+2] = hex(int(hexdata[i+2], 16) ^ int(self.nami[2], 16))[2:].zfill(2)
            hexdata[i+3] = hex(int(hexdata[i+3], 16) ^ int(self.nami[3], 16))[2:].zfill(2)
    
    
    # 1st decryption for OMC_WAV
    def rearrange(self, buf_encoded):
        length = len(buf_encoded)
        key = ((length % 17) << 4) + (length % 17)

        block_size = int(length / 17)

        # Let's fill the buffer
        buf_plain = copy.deepcopy(buf_encoded)

        # loopy loop
        for block in range(17):
            # Where is the start of the enconded block
            block_start_encoded = block_size * block
            # Where the final plain block will be
            block_start_plain = block_size * int(self.REARRANGE_TABLE[key], 16)
            buf_plain[block_start_plain:block_start_plain + block_size] = buf_encoded[block_start_encoded:block_start_encoded + block_size]
            key += 1
        
        return buf_plain

    # 2nd decryption for OMC_WAV
    def acc_xor(self, buf):
        acc_keybyte = 0xFF
        acc_counter = 0
        temp = 0
        this_byte = 0

        for i in range(len(buf)):
            temp = this_byte = int(buf[i], 16)

            if ((acc_keybyte << acc_counter) & 0x80) != 0:
                this_byte = 255 - this_byte

            buf[i] = hex(this_byte)[2:].upper().zfill(2)
            acc_counter += 1
            if acc_counter > 7:
                acc_counter = 0
                acc_keybyte = temp
        return buf

    def dump_file(self, filename):
        self.filename = filename # useful for debug
        # Compare signature (M30, OMC, OJM)
        ojn_filename = os.path.join(self.input_path, filename)
        with open(ojn_filename, "rb") as f:
            hex_raw = f.read().hex()

        self.hexdata = [hex_raw[i:i+2] for i in range(0, len(hex_raw), 2)]

        signature = self.LE(self.hexdata[0:4])

        if signature == self.M30_SIGNATURE:
            print("Extract M30 format audio files...")
            self.parse_M30()
        # OMC and OJM can be parsed by the same scheme
        elif signature == self.OMC_SIGNATURE or signature == self.OJM_SIGNATURE:
            print("Extract OMC/OJM format audio files...")
            self.parse_OMC()
        else:
            print("Unknown Signature!")

    def parse_M30(self):
        # M30_header (28 bytes)
        file_format_version = int(self.LE(self.hexdata[4:8]), 16)
        encryption_flag = int(self.LE(self.hexdata[8:12]), 16)
        sample_count = int(self.LE(self.hexdata[12:16]), 16) # Do not use this because it might not be accurate
        samples_offset = int(self.LE(self.hexdata[16:20]), 16)
        payload_size = int(self.LE(self.hexdata[20:24]), 16)
        padding = int(self.LE(self.hexdata[24:28]), 16)

        pos = 28
        
        # TODO: need to test if this is correct?
        # ogg data section
        for i in range(sample_count):
            # reached the end of the file before the samples_count
            if len(self.hexdata) - pos < 52:
                print(f"Wrong number of samples on OJM header: {self.filename}")
                break
            
            # M30_OGG_header (sample header, 52 bytes)
            # sample_name = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[pos:pos+32]))).decode(self.enc)
            sample_size = int(self.LE(self.hexdata[pos+32:pos+36]), 16)
            codec_code = int(self.LE(self.hexdata[pos+36:pos+38]), 16)
            unk_fixed = int(self.LE(self.hexdata[pos+38:pos+40]), 16)
            music_flag = int(self.LE(self.hexdata[pos+40:pos+44]), 16)
            ref = int(self.LE(self.hexdata[pos+44:pos+46]), 16)
            unk_zero = int(self.LE(self.hexdata[pos+46:pos+48]), 16)
            pcm_samples = int(self.LE(self.hexdata[pos+48:pos+52]), 16)
            pos += 52

            # ogg_data
            ogg_data = self.hexdata[pos:pos+sample_size]
            pos += sample_size

            # check encryption flag
            # 16 - nami
            if encryption_flag == 16:
                self.nami_xor(ogg_data)
            # flag > 16 should be plain ogg according to documentation
            elif encryption_flag > 16:
                pass
            # 1 - scramble1; 2 - scramble2; 4 - decode; 8 - decrypt; 
            else:
                print(f"Unknown encryption flag {encryption_flag}, skipping!")
                break

            # 0 - background sound; 5 - normal sound
            if codec_code == 0:
                ref += 1000
            elif codec_code != 5:
                print(f"Unknown sample id type {codec_code} on OJM: {self.filename}")

            ogg_bytes = bytes.fromhex(self.BE(ogg_data))

            ogg_filename = os.path.join(self.song_path, f"normal-hitnormal{ref}.ogg")
            if len(ogg_bytes) > 0:
                with open(ogg_filename, "wb") as f:
                    f.write(ogg_bytes)
            else:
                print(f"Failed normal-hitnormal{ref}.ogg")
            
    
    def parse_OMC(self):
        # OMC_header (20 bytes)
        wav_count = int(self.LE(self.hexdata[4:6]), 16)
        ogg_count = int(self.LE(self.hexdata[6:8]), 16)
        wav_start = int(self.LE(self.hexdata[8:12]), 16)
        ogg_start = int(self.LE(self.hexdata[12:16]), 16)
        filesize = int(self.LE(self.hexdata[16:20]), 16)

        pos = 20
        sample_id = 0 # wav samples use id 0~999

        # reset global variables (TODO: Maybe Remove)
        acc_keybyte = "FF"
        acc_counter = 0

        # wav data section
        while pos < ogg_start:
            # OMC_WAV_header (sample header, 56 bytes)
            # sample_name = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[pos:pos+32]))).decode(self.enc)
            audio_format = int(self.LE(self.hexdata[pos+32:pos+34]), 16)
            num_channels = int(self.LE(self.hexdata[pos+34:pos+36]), 16)
            sample_rate = int(self.LE(self.hexdata[pos+36:pos+40]), 16)
            bit_rate = int(self.LE(self.hexdata[pos+40:pos+44]), 16)
            block_align = int(self.LE(self.hexdata[pos+44:pos+46]), 16)
            bits_per_sample = int(self.LE(self.hexdata[pos+46:pos+48]), 16)
            data = int(self.LE(self.hexdata[pos+48:pos+52]), 16)
            chunk_size = int(self.LE(self.hexdata[pos+52:pos+56]), 16)
            pos += 56

            # skip empty chunk
            if chunk_size == 0:
                sample_id += 1
                continue

            # wav_data
            wav_data = self.rearrange(self.hexdata[pos:pos+chunk_size])
            wav_data = self.acc_xor(wav_data)
            pos += chunk_size

            # wav_header
            # https://stackoverflow.com/questions/28137559/can-someone-explain-wavwave-file-headers
            out_buffer = []
            out_buffer += self.text_to_hex("RIFF")
            out_buffer += self.int_to_hex(chunk_size+36)
            out_buffer += self.text_to_hex("WAVE")
            out_buffer += self.text_to_hex("fmt ")
            out_buffer += self.int_to_hex(16)
            out_buffer += self.int_to_hex(audio_format, fill=4)
            out_buffer += self.int_to_hex(num_channels, fill=4)
            out_buffer += self.int_to_hex(sample_rate)
            out_buffer += self.int_to_hex(bit_rate)
            out_buffer += self.int_to_hex(block_align, fill=4)
            out_buffer += self.int_to_hex(bits_per_sample, fill=4)
            out_buffer += self.text_to_hex("data")
            out_buffer += self.int_to_hex(chunk_size)
            out_buffer += wav_data

            out_buffer_bytes = bytes.fromhex(self.BE(out_buffer))

            wav_filename = os.path.join(self.song_path, f"normal-hitnormal{sample_id}.wav")
            if len(out_buffer_bytes) > 0:
                with open(wav_filename, "wb") as f:
                    f.write(out_buffer_bytes)
            else:
                print(f"Failed normal-hitnormal{sample_id}.wav")
            
            sample_id += 1

        # ogg data section
        sample_id = 1001
        while pos < filesize:
            # OMC_OGG_header (sample header, 36 bytes)
            # sample_name = bytes.fromhex(self.BE(self.NUL_String(self.hexdata[pos:pos+32]))).decode(self.enc)
            sample_size = int(self.LE(self.hexdata[pos+32:pos+36]), 16)
            pos += 36

            # skip empty sample
            if sample_size == 0:
                sample_id += 1
                continue

                
            ogg_data = self.hexdata[pos:pos+sample_size]
            ogg_bytes = bytes.fromhex(self.BE(ogg_data))
            pos += sample_size

            ogg_filename = os.path.join(self.song_path, f"normal-hitnormal{sample_id}.ogg")
            if len(ogg_bytes) > 0:
                with open(ogg_filename, "wb") as f:
                    f.write(ogg_bytes)
            else:
                print(f"Failed normal-hitnormal{sample_id}.ogg")
            
            sample_id += 1