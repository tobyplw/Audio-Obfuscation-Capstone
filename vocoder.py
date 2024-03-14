from numpy import pi, mod, sin, sqrt, tan, linspace, clip
from scipy.signal import lfilter
import random
import numpy as np
from scipy.signal import iirfilter
from pedalboard import Compressor, NoiseGate, Gain

#Algorithm based on https://github.com/ederwander/ChannelVocoder/blob/main/EderwanderVocoderOnTheFly.py
class Vocoder:
    def __init__(self, create_random_seed = False, rate = 48000, chunk = 4096, distortion = 0.25):
        self.rate = rate
        self.create_random_seed = create_random_seed
        self.pitch_contour = 1000

        if(self.create_random_seed):
            self.pitch_contour = self.random_freq()

        self.w = 2.0*pi*self.pitch_contour/self.rate

        self.dB=10**(60/20)
        self.chunk = chunk

        self.distortion = distortion
        if(self.distortion < 0.05):
            self.distortino = 0.05
        elif(self.distortion > 0.8):
            self.distortion = 0.8

        self.phase0 = 0
        self.phase1 = 0
        self.phase2 = 0
        self.phase3 = 0
        self.phase4 = 0
        self.phase5 = 0
        self.phase6 = 0
        self.phase7 = 0

        self.r = 0.99
        self.lowpassf = [1.0, -2.0*self.r, +self.r*self.r]
        self.d = 0.41004238851988095
        self.amp=1.0

        '''33 frequencies -> Bandpass filter design coefficients'''
        self.numFreqs = 100
        self.a_freq_coeff, self.b_freq_coeff = self.generate_bandpass_coefficients()

        self.comp = Compressor(threshold_db=-15, ratio=2.5)
        self.gate = NoiseGate(threshold_db=-15, ratio=2.5, attack_ms = 0.2, release_ms = 50)
        self.gain = Gain(gain_db=10)


    def generate_bandpass_coefficients(self):
        low_cutoff = 20.0
        high_cutoff = 8000.0
        increase = 1.05

        step = (high_cutoff - low_cutoff) / self.numFreqs / 20

        a = np.empty((0, 5))
        b = np.empty((0, 5))
        i = 0
        current_low = low_cutoff
        current_high = current_low + step
        while i < self.numFreqs:
            pair = [current_low, current_high]
            b_tmp, a_tmp = iirfilter(2, pair, btype = 'bandpass', ftype = 'butter', output='ba', fs = self.rate)
            b = np.vstack((b, b_tmp))
            a = np.vstack((a, a_tmp))
            i+=1
            step = step * increase
            current_low = current_low + (step / 1.25)
            current_high = current_low + step
            # print(current_low)
            # print(current_high)
            # print("________________")
        return a, b

    


    #generate a pitching frequency between 300hz and 1200hz
    def random_freq(self):

        freq = random.randrange(400, 1200, 5)
        print(freq)
        return freq


    def carrier(self, length):

        self.phase1=0.2 * self.w * (linspace(0, length, length)) + self.phase1
        self.phase2=0.4 * self.w * (linspace(0, length, length)) + self.phase2
        self.phase3=0.5 * self.w * (linspace(0, length, length)) + self.phase3
        self.phase4=2.0 * self.w * (linspace(0, length, length)) + self.phase4
        self.phase5=sin(self.phase1) - tan(self.phase3)
        self.phase6=sin(self.phase1) + sin(self.phase4)
        self.phase7=sin(self.phase2) - sin(self.phase4)
        x = sin(self.phase5)
        y = sin(self.phase6)
        z = sin(self.phase7)
        carriersignal = self.distortion * (x + y + z + self.d)
        self.phase1 = mod(self.phase1[length-1], 2.0*pi)
        self.phase2 = mod(self.phase2[length-1], 2.0*pi)
        self.phase3 = mod(self.phase3[length-1], 2.0*pi)
        self.phase4 = mod(self.phase4[length-1], 2.0*pi)
        self.phase5 = mod(self.phase5[length-1], 2.0*pi)
        self.phase6 = mod(self.phase6[length-1], 2.0*pi)
        self.phase7 = mod(self.phase7[length-1], 2.0*pi)
        
        return carriersignal

    def transform(self, data):
        length=len(data)
        carriersignal=0
        carriersignal=self.carrier(length)
        vout=0
        data = self.gate.process(input_array = data, sample_rate = self.rate, buffer_size = self.chunk)
        for i in range(0, self.numFreqs):
            bandpasscarrier = lfilter(self.b_freq_coeff[i], self.a_freq_coeff[i], carriersignal)
            bandpassmodulator = lfilter(self.b_freq_coeff[i], self.a_freq_coeff[i], data)
            rectifiedmodulator = abs(bandpassmodulator*bandpassmodulator)/length
            envelopemodulator = sqrt(lfilter([1.0], self.lowpassf, rectifiedmodulator))
            vout+= bandpasscarrier*envelopemodulator
        vout = clip(vout*self.dB, -1, 1)
        vout = self.comp.process(input_array = vout, sample_rate = self.rate, buffer_size = self.chunk)
        vout = self.gain.process(input_array = vout, sample_rate = self.rate, buffer_size = self.chunk)
        return vout

    # from https://gist.github.com/HudsonHuang/fbdf8e9af7993fe2a91620d3fb86a182
    def float2pcm(self, sig, dtype='int16'):
        if sig.dtype.kind != 'f':
            raise TypeError("'sig' must be a float array")
        dtype = np.dtype(dtype)
        if dtype.kind not in 'iu':
            raise TypeError("'dtype' must be an integer type")

        i = np.iinfo(dtype)
        abs_max = 2 ** (i.bits - 1)
        offset = i.min + abs_max

        return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)