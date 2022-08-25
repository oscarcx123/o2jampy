import os
from OJNExtract import OJNExtract

cow = OJNExtract()
cow.debug = False
cow.o2jam_to_osu([x for x in os.listdir(cow.input_path) if x.endswith(".ojn")])
#cow.o2jam_to_osu(["o2ma1237.ojn"])