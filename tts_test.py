
from TTS.api import TTS

#tts = TTS().list_models()
#print(TTS().list_models())
#tts = TTS()
#tts = TTS(TTS.list_models()[0])

#tts.tts("This is a test of TTS")
print(TTS().list_models())

device = "cpu"

# Init TTS with the target model name
tts = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC", progress_bar=False).to(device)

# Run TTS
tts.tts(text="Ich bin eine Testnachricht.")