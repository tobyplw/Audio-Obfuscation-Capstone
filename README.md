# Audio-Obfuscation-Capstone

Dependencies List:
Note: Use Pip to install
- numpy
- pyaudio
- scipy.io

To use:
1. Test_data holds ~8 instances of various people saying "This is an Audio Test"
2. Run 'python3 create_test.py', this will combine all Test Data into a single Audio File
3. Run 'python3 Vocoder_File_to_File.py), this will use the vocoding algorithm to obfuscare the test file and generate a new obfuscated file
4. If you would like to hear your voice obfuscated in real time, run 'python3 Vocoder_Input_to_Output', which will take your input microphone and output to your system output. Make sure you are using headphones or it will echo. 


