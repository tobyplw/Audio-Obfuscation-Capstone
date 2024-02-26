import numpy as np
from struct import pack
import pyaudio
from vocoder import Vocoder
import noisereduce



# Initialize Vocoder Class
voc = Vocoder(create_random_seed = False, rate = 24000, chunk = 512, distortion = 0.10)

# Initialize PyAudio
pyaud = pyaudio.PyAudio()

# Open stream 
stream = pyaud.open(format =  pyaudio.paFloat32,
               channels = 1,
               rate = voc.rate,
               input = True,
               output = True, frames_per_buffer=voc.chunk)


stream.start_stream()
print("listening...")
print("Input Latency: " + str(stream.get_input_latency()))
print("Output Latency: " + str(stream.get_output_latency()))


print("Listening Now")
while True:
    try:
        raw_data = stream.read(voc.chunk, exception_on_overflow=False)
        data = np.frombuffer(raw_data, dtype=np.float32)
        data = voc.transform(data) 
        out = pack("%df"%len(data), *data)
        stream.write(out)
    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        pyaud.terminate()
