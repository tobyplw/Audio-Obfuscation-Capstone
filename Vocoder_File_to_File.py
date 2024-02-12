from numpy import pi, mod, sin, sqrt, tan, frombuffer, float32, linspace, finfo, clip, array
from scipy.io.wavfile import write, read
import os
from vocoder import Vocoder


output_file_name = "./output.wav"
input_file_name = "./Test_Audio_Input.wav"
#Remove output file from system first
try:
    os.remove(output_file_name)
except FileNotFoundError:
    pass

# Initialize Vocoder Class
voc = Vocoder(create_random_seed = False, rate = 48000, chunk = 4096)

print("\nCreating Obfuscated audio <" + output_file_name + "> from <" + input_file_name + ">\n")
rate, in_data = read(input_file_name)
in_data=voc.transform(in_data)
write(output_file_name, voc.rate, in_data)
print("Complete\n")


