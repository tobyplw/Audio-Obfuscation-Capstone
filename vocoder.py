from numpy import pi, mod, sin, sqrt, tan, linspace, clip
from scipy.signal import lfilter
import random
import numpy as np


class Vocoder:
    def __init__(self, create_random_seed = False, rate = 48000, chunk = 4096, distortion = 0.25):
        
        self.rate = rate
        self.create_random_seed = create_random_seed
        self.pitch_contour = 600

        if(self.create_random_seed):
            self.pitch_contour = self.random_freq()

        self.w = 2.0*pi*self.pitch_contour/self.rate

        self.dB=10**(60/20)
        self.chunk = chunk

        self.distortion = distortion
        if(self.distortion < 0.1):
            self.distortino = 0.1
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
        self.a_freq_coeff = [
            [1,	-3.99975599432850,	5.99927319549360,	-3.99927840737790,	0.999761206219333],
            [1,	-3.99969087479883,	5.99908089886356,	-3.99908917207623,	0.999699148027989],
            [1	-3.99960783242349,	5.99883663242320,	-3.99884976505012,	0.999620965091944],
            [1,	-3.99950162319079,	5.99852572084418,	-3.99854656702148,	0.999522469472722],
            [1,	-3.99936529624421,	5.99812898911301,	-3.99816207919623,	0.999398386591067],
            [1,	-3.99918954838096,	5.99762119086212,	-3.99767371571456,	0.999242073897684],
            [1,	-3.99896179230423,	5.99696879242825,	-3.99705216552381,	0.999045167073510],
            [1,	-3.99866479474709,	5.99612680715249,	-3.99625914349455,	0.998797135306096],
            [1,	-3.99827466248870,	5.99503421446511,	-3.99524426396985,	0.998484722617774],
            [1,	-3.99775783209982,	5.99360724998732,	-3.99394063771490,	0.998091246593493],
            [1,	-3.99706652768996,	5.99172946648071,	-3.99225859033826,	0.997595718976056],
            [1,	-3.99613185013489,	5.98923686336783,	-3.99007658764110,	0.996971744260045],
            [1,	-3.99485318855908,	5.98589544431097,	-3.98722797037749,	0.996186142439803],
            [1,	-3.99308190186349,	5.98136710272466,	-3.98348135377444,	0.995197230334171],
            [1,	-3.99059605102152,	5.97515747320379,	-3.97851139167541,	0.993952682453192],
            [1,	-3.98706113267000,	5.96653590681851,	-3.97185482190872,	0.992386877515924],
            [1,	-3.98196890312390,	5.95441243992289,	-3.96284396965905,	0.990417621333426],
            [1,	-3.97454193106546,	5.93714875785070,	-3.95050570870629,	0.987942122629232],
            [1,	-3.96358465094425,	5.91226887379876,	-3.93340759291814,	0.984832088850899],
            [1,	-3.94725123836206,	5.87602016123001,	-3.90942359895478,	0.980927810114349],
            [1,	-3.92268507313800,	5.82271809701412,	-3.87537871287358,	0.976031121355393],
            [1,	-3.88546228104775,	5.74379634972886,	-3.82651390292709,	0.969897192591698],
            [1,	-3.82874219179635,	5.62650200982447,	-3.75569214621489,	0.962225222699710],
            [1,	-3.74199398552012,	5.45228903999113,	-3.65224899613469,	0.952648347632671],
            [1,	-3.60914741639923,	5.19532970510166,	-3.50039918643988,	0.940723488871680],
            [1,	-3.40605615180314,	4.82253055457138,	-3.27720061176920,	0.925922567908390],
            [1,	-3.09739763001925,	4.29865336456317,	-2.95038375754678,	0.907627654519980],
            [1,	-2.63388305596713,	3.60440511182782,	-2.47717214208704,	0.885134424906144],
            [1,	-1.95260897719969,	2.78102389972874,	-1.80711132908444,	0.857671089645940],
            [1,	-0.987821704356849,	2.01302475585146,	-0.895725041038555,	0.824444128755633],
            [1,	0.292204692740340,	1.71579119867574,	0.258147856757345,	0.784728343490888],
            [1,	1.79567000881120,	2.42888468072076,	1.53417945578454,	0.738028006232103],
            [1,	3.14391651047433,	4.05911136375890,	2.57181632513949,	0.684351098394969]
        ]

        self.b_freq_coeff = [
            [1.71790337413308e-08,	0,	-3.43580674826616e-08,	 0,	     1.71790337413308e-08],
            [2.72392949892633e-08,	0,	-5.44785899785266e-08,	 0,	     2.72392949892633e-08],
            [4.33202037600520e-08,	0,	-8.66404075201039e-08,	 0,	     4.33202037600520e-08],
            [6.87019970842440e-08,	0,	-1.37403994168488e-07,	 0,	     6.87019970842440e-08],
            [1.09076437679077e-07,	0,	-2.18152875358153e-07,	 0,	     1.09076437679077e-07],
            [1.73127013142121e-07,	0,	-3.46254026284243e-07,	 0,	     1.73127013142121e-07],
            [2.74802658915039e-07,	0,	-5.49605317830078e-07,	 0,	     2.74802658915039e-07],
            [4.36167681516868e-07,	0,	-8.72335363033737e-07,	 0,	     4.36167681516868e-07],
            [6.92263017611530e-07,	0,	-1.38452603522306e-06,	 0,	     6.92263017611530e-07],
            [1.09868242572049e-06,	0,	-2.19736485144099e-06,	 0,	     1.09868242572049e-06],
            [1.74361621177647e-06,	0,	-3.48723242355294e-06,	 0,	     1.74361621177647e-06],
            [2.76695320840727e-06,	0,	-5.53390641681454e-06,	 0,	     2.76695320840727e-06],
            [4.39053611412317e-06,	0,	-8.78107222824634e-06,	 0,	     4.39053611412317e-06],
            [6.96608739369304e-06,	0,	-1.39321747873861e-05,	 0,	     6.96608739369304e-06],
            [1.10510729592236e-05,	0,	-2.21021459184473e-05,	 0,	     1.10510729592236e-05],
            [1.75286996737880e-05,	0,	-3.50573993475760e-05,	 0,	     1.75286996737880e-05],
            [2.77975505699513e-05,	0,	-5.55951011399026e-05,	 0,	     2.77975505699513e-05],
            [4.40709217599428e-05,	0,	-8.81418435198856e-05,	 0,	     4.40709217599428e-05],
            [6.98486316325863e-05,	0,	-0.000139697263265173,	 0,	     6.98486316325863e-05],
            [0.000110659311323076,	0,	-0.000221318622646152,	 0,	     0.000110659311323076],
            [0.000175225540477838,	0,	-0.000350451080955677,	 0,	     0.000175225540477838],
            [0.000277287390711482,	0,	-0.000554574781422964,	 0,	     0.000277287390711482],
            [0.000438446036225742,	0,	-0.000876892072451484,	 0,	     0.000438446036225742],
            [0.000692577807844958,	0,	-0.00138515561568992,	 0,	     0.000692577807844958],
            [0.00109264697016785,	0,	-0.00218529394033570,	 0,	     0.00109264697016785],
            [0.00172114638070978,	0,	-0.00344229276141955,	 0,	     0.00172114638070978],
            [0.00270595858002333,	0,	-0.00541191716004666,	 0,	     0.00270595858002333],
            [0.00424419670029157,	0,	-0.00848839340058314,	 0,	     0.00424419670029157],
            [0.00663759117688310,	0,	-0.0132751823537662,	 0,	     0.00663759117688310],
            [0.0103442686624309,    0,	-0.0206885373248617,	 0,	      0.0103442686624309],
            [0.0160534029877771,    0,	-0.0321068059755541,	 0,	      0.0160534029877771],
            [0.0247915230726592,    0,	-0.0495830461453185,	 0,	      0.0247915230726592],
            [0.0380733762023088,    0,	-0.0761467524046175,	 0,	      0.0380733762023088]
        ]



    #generate a pitching frequency between 300hz and 1200hz
    def random_freq(self):

        freq = random.randrange(300, 1200, 5)
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
        for i in range(0, 33):
            bandpasscarrier = lfilter(self.b_freq_coeff[i], self.a_freq_coeff[i], carriersignal)
            bandpassmodulator = lfilter(self.b_freq_coeff[i], self.a_freq_coeff[i], data)
            rectifiedmodulator = abs(bandpassmodulator*bandpassmodulator)/length
            envelopemodulator = sqrt(lfilter([1.0], self.lowpassf, rectifiedmodulator))
            vout+= bandpasscarrier*envelopemodulator
        vout = clip(vout*self.dB, -1, 1)
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
