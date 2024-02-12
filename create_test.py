import wave
import glob
import random

infiles = glob.glob('./Test_data/*.wav')
random.shuffle(infiles)
print(infiles)

outfile = 'test2.wav'


with wave.open(outfile, 'wb') as wav_out:
    wav_out.setnchannels(1)
    wav_out.setsampwidth(4)
    wav_out.setframerate(22000)

    for wav_path in infiles:
        with wave.open(wav_path, 'rb') as wav_in:
            if not wav_out.getnframes():
                wav_out.setparams(wav_in.getparams())
            wav_out.writeframes(wav_in.readframes(wav_in.getnframes()))