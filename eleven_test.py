from elevenlabs import set_api_key, Voice, VoiceSettings, generate, stream, play


set_api_key(api_key = "7617598e29194614ec09fe674baf47d8")



from elevenlabs import generate, stream

def text_stream():
    yield "ok."

audio_stream = generate(
  text=text_stream(),
  stream=True
)

stream(audio_stream)