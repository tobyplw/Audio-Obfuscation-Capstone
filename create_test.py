import wave
import glob
import random
import numpy as np

from scipy.io.wavfile import write, read

infiles = glob.glob('./Test_data/*.wav')
random.shuffle(infiles)
print("FILES FOR TESTING")
print(infiles)

outfile = 'Test_Audio_Input.wav'

all = np.array([], dtype = np.float32)

rate = 0
for wav_path in infiles:
    rate, in_data = read(wav_path)
    in_data = in_data.astype(np.float32, order = 'C') / 32768.0
    all = np.append(all, in_data)

write(outfile, rate, all.astype(np.float32))

