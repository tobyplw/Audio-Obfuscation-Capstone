from numpy import pi, mod, sin, sqrt, tan, linspace, clip
from scipy.signal import lfilter
import random
import numpy as np
import math
from scipy.signal import iirfilter
from pedalboard import Pedalboard, Compressor, NoiseGate, Gain, PitchShift, Distortion, Phaser, Reverb

#Algorithm based on https://github.com/ederwander/ChannelVocoder/blob/main/EderwanderVocoderOnTheFly.py
#this class is used to create the "Obfuscated Voice"
#Two options were implemented. 
# Either use the Transform() function to use the Vocoder functionality with frequency band mapping
# Or use Audio_effect() to just shift the pitch down on the voice
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
        
        #limit distortion amount
        self.distortion = distortion
        if(self.distortion < 0.05):
            self.distortion = 0.05
        elif(self.distortion > 0.8):
            self.distortion = 0.8

        #start phases for carrier signal
        self.phase0 = 0
        self.phase1 = 0
        self.phase2 = 0
        self.phase3 = 0
        self.phase4 = 0
        self.phase5 = 0
        self.phase6 = 0
        self.phase7 = 0

        #set initial audio parameters
        self.r = 0.99
        self.lowpassf = [1.0, -2.0*self.r, +self.r*self.r]
        self.d = 0.41004238851988095
        self.amp=1.0

        #frequencies -> Bandpass filter design coefficients
        self.numFreqs = 20
        self.a_freq_coeff, self.b_freq_coeff = self.generate_bandpass_coefficients()

        #pitchShift variable
        self.pitch = PitchShift(semitones=-2)


        #Create a Pedalboard with audio effects. This is not currently being sued
        self.pedalboard = Pedalboard([
            
            Compressor(threshold_db=-5, ratio=2.5), #compress audio
            Gain(gain_db=5), #add Gain
            NoiseGate(threshold_db=-100, ratio=10, attack_ms = 1.0, release_ms = 100), #noisegate to eliminate background noise
            Distortion(drive_db = 35), #add small amount of distortion
            PitchShift(semitones=2),  # Shift pitch down by 3 semitones
            Phaser(rate_hz=20, depth=2, feedback=1, mix = .5),  # Add Phaser effect
            Reverb(wet_level = .33, room_size = 1) #add small reverb effect
            
        ])


        # Example usage
        self.sin_sample_rate = 44100  # Sample rate in samples per second (Hz)
        self.sin_frequency = 440  # Frequency of the sine wave in Hertz (Hz)
        self.sin_amplitude = 2 / math.pi  # Adjusted amplitude to scale output between -2 and 2


    #Generates the bandpass frequency bands for the Vocoder Class
    def generate_bandpass_coefficients(self):
        low_cutoff = 20.0
        high_cutoff = 8000.0
        increase = 1.26
        
        #calculate the step size
        step = (high_cutoff - low_cutoff) / self.numFreqs / 20

        a = np.empty((0, 5))
        b = np.empty((0, 5))
        i = 0
        current_low = low_cutoff
        current_high = current_low + step
        #iterate over the number of frequencies you want
        while i < self.numFreqs:
            pair = [current_low, current_high]
            #run through bandpass butter filter
            b_tmp, a_tmp = iirfilter(2, pair, btype = 'bandpass', ftype = 'butter', output='ba', fs = self.rate)
            b = np.vstack((b, b_tmp))
            a = np.vstack((a, a_tmp))
            i+=1
            step = step * increase
            #set parameters for next band
            current_low = current_low + (step / 1.25)
            current_high = current_low + step
            #print(current_low)
            # print(current_high)
            # print("________________")
        return a, b

    #generate a pitching frequency between 300hz and 1200hz
    def random_freq(self):

        freq = random.randrange(400, 1200, 5)
        print(freq)
        return freq

    # create the dynamic carrier signals for the Vocoder
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

    # Input is a Float32 numpy array
    # Outputs a Float32 numpy array that has been ran through the Vocoding Formula
    def transform(self, data):
        length=len(data)
        carriersignal=0
        carriersignal=self.carrier(length)
        vout=0
        # for each frequency band, apply the filters and mapping of original data to frequency band
        for i in range(0, self.numFreqs):
            bandpasscarrier = lfilter(self.b_freq_coeff[i], self.a_freq_coeff[i], carriersignal)
            bandpassmodulator = lfilter(self.b_freq_coeff[i], self.a_freq_coeff[i], data)
            rectifiedmodulator = abs(bandpassmodulator*bandpassmodulator)/length
            envelopemodulator = sqrt(lfilter([1.0], self.lowpassf, rectifiedmodulator))
            vout+= bandpasscarrier*envelopemodulator
        #insure output is clipped according to decibel limit
        vout = clip(vout*self.dB, -1, 1)
        return vout

    # Takes in Float32 Audio data and outputs "obfuscated" Float32 audio Data
    # Currently only changes the pitch.
    def audio_effects(self, data):
        #settling on Pitch for now...
        data = self.pitch.process(input_array = data, sample_rate = self.rate, buffer_size = self.chunk)

        #tried to get the pedalboard object to work with multiple effects. Sounds good with local testing, but horrible over network
        #data = self.pedalboard.process(input_array = data, sample_rate = self.rate, buffer_size = self.chunk)
        return data


    # from https://gist.github.com/HudsonHuang/fbdf8e9af7993fe2a91620d3fb86a182
    # this function takes in Float32 data (sig) and converts it into int16 data using fancy math
    def float2pcm(self, sig, dtype='int16'):
        if sig.dtype.kind != 'f':
            raise TypeError("'sig' must be a float array")
        dtype = np.dtype(dtype)
        if dtype.kind not in 'iu':
            raise TypeError("'dtype' must be an integer type")

        #fancy math to transorm data type
        i = np.iinfo(dtype)
        abs_max = 2 ** (i.bits - 1)
        offset = i.min + abs_max

        return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)