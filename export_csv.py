import os
import shutil
from OJNExtract import OJNExtract

def remove_sep(text):
    return text.replace(",", "_")

cow = OJNExtract()
cow.debug = False

'''Common Codecs
gb18030 - Simplified Chinese
big5 - Traditional Chinese
euc_kr - Korean
'''

cow.enc = "gb18030"
cow.input_path = r"C:\Users\Oscar\Desktop\o2jam dedupe v1"
corrupt_path = r"C:\Users\Oscar\Desktop\corrupt"
#cow.input_path = r"C:\Users\Oscar\Desktop\temp"

ojn_list = [x for x in os.listdir(cow.input_path) if x.endswith(".ojn")]

ojn_dict = {}

for idx in range(len(ojn_list)):
    server = ojn_list[idx].split("_")[0]
    song_id = int(ojn_list[idx].split('.')[0].split('_')[1].replace("o2ma", ""))
    if server not in ojn_dict:
        ojn_dict[server] = []
    ojn_dict[server].append(song_id)

ojn_list = []

ojn_dict = dict(sorted(ojn_dict.items()))

for key, value in ojn_dict.items():
    value.sort()
    for v in value:
        ojn_list.append(key + "_o2ma" + str(v) + ".ojn")


with open("database.csv", "w", encoding="utf-8-sig") as f:
    f.write("server, filename, song_id, title, artist, noter, bpm, lvl_E, lvl_N, lvl_H, total_notes_E, total_notes_N, total_notes_H, playable_notes_E, playable_notes_N, playable_notes_H, measure_count_E, measure_count_N, measure_count_H, package_count_E, package_count_N, package_count_H, duration_E, duration_N, duration_H, diff_offset_E, diff_offset_N, diff_offset_H, diff_size_E, diff_size_N, diff_size_H, cover_offset, genre_text, ojn_version\n")

gb_list = ['unk1','Venus','io2pf','Pepsi','OtakuJam','O2max','O2Jupiter','O2Hypoxia', '17MG']

for idx in range(len(ojn_list)):
    server = ojn_list[idx].split("_")[0]
    if server in gb_list:
        cow.enc = "gb18030"
    else:
        cow.enc = "euc_kr"
    try:
        cow.parse_ojn_header(ojn_list[idx])
    except UnicodeDecodeError:
        try:
            cow.enc = "gb18030"
            cow.parse_ojn_header(ojn_list[idx])
        except UnicodeDecodeError:
            try:
                cow.enc = "euc_kr"
                cow.parse_ojn_header(ojn_list[idx])
            except UnicodeDecodeError:
                shutil.move(os.path.join(cow.input_path, ojn_list[idx]), os.path.join(corrupt_path, ojn_list[idx]))
                shutil.move(os.path.join(cow.input_path, ojn_list[idx].replace(".ojn", ".ojm")), os.path.join(corrupt_path, ojn_list[idx].replace(".ojn", ".ojm")))
                print(f"can't decode {ojn_list[idx]}!")
                continue
    with open("database.csv", "a", encoding="utf-8-sig") as f:
        f.write(f"{server}, {ojn_list[idx]}, {cow.song_id}, {remove_sep(cow.title)}, {remove_sep(cow.artist)}, {remove_sep(cow.noter)}, {cow.bpm}, {cow.lvl[0]}, {cow.lvl[1]}, {cow.lvl[2]}, {cow.total_notes[0]}, {cow.total_notes[1]}, {cow.total_notes[2]}, {cow.playable_notes[0]}, {cow.playable_notes[1]}, {cow.playable_notes[2]}, {cow.measure_count[0]}, {cow.measure_count[1]}, {cow.measure_count[2]}, {cow.package_count[0]}, {cow.package_count[1]}, {cow.package_count[2]}, {cow.duration[0]}, {cow.duration[1]}, {cow.duration[2]}, {cow.diff_offset[0]}, {cow.diff_offset[1]}, {cow.diff_offset[2]}, {cow.diff_size[0]}, {cow.diff_size[1]}, {cow.diff_size[2]}, {cow.cover_offset}, {cow.genre_text}, {cow.ojn_version}\n")
    
    print(f"{100*idx/len(ojn_list):.1f}% ({idx}/{len(ojn_list)}, {ojn_list[idx]}, {cow.enc})")