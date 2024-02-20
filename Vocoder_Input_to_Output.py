from numpy import frombuffer, float32
from struct import pack
import pyaudio
from vocoder import Vocoder



# Initialize Vocoder Class
voc = Vocoder(create_random_seed = False, rate = 48000, chunk = 4096, distortion = 0.1)

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

while True:
    try:
        raw_data = stream.read(voc.chunk, exception_on_overflow=False)
        data = frombuffer(raw_data, dtype=float32)
        data = voc.transform(data)
        out = pack("%df"%len(data), *data)
        stream.write(out)
    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        pyaud.terminate()
