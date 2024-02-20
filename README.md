# Audio-Obfuscation-Capstone

## Dependency List
- Socket
- PyAudio
- Threading (pip install thread6)

## Usage
1. Create three terminal windows
2. Run server.py first then client.py on the next two
3. Speak and listen

## Notes
- The implementation of threads allows for full-duplex - both clients should be able to talk and listen at the same time.
- The only way to end the program is to terminate with CTRL-C. 
- I added a note in server.py for where the data manipulation should occur.

## TO DO
- Add a bind for the user to end communication.