# Audio-Obfuscation-Capstone

## Dependency List
- Socket
- PyAudio
- Threading (pip install thread6)

## Usage
1. Create two terminal windows
2. Run server.py first then client.py
3. Speak and listen

## Notes
- The current implementation is the client's audio data is constantly read and sent to the server and the server then plays it.
- Threading will need to be implemented in order to support full-duplex. 