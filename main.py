import os
from OJNExtract import OJNExtract

cow = OJNExtract()
cow.debug = False

'''Common Codecs
gb18030 - Simplified Chinese
big5 - Traditional Chinese
euc_kr - Korean
'''

cow.enc = "gb18030"
cow.flag_use_mp3 = True
cow.flag_nsv = True
cow.extra_offset = 0
cow.o2jam_to_osu([x for x in os.listdir(cow.input_path) if x.endswith(".ojn")])
#cow.o2jam_to_osu(["o2ma1237.ojn"])
#cow.input_path = r"C:\Users\Oscar\Desktop\o2jam dedupe"