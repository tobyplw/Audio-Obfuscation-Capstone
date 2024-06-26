import struct

# create the RTP header for each packet
# inputs: Sequence number for the packet, timestamp, and payload_type to determine packet content
def create_rtp_header(sequence_number, timestamp, ssrc, payload_type):
    version = 2  # RTP version
    padding = 0
    extension = 0
    csrc_count = 0 
    marker = 0
    #if payload_type = 0, AUDIO DATA
    #if payload_type = 1, TRANSCRIPTIONS
    #if payload_type = 2, HANGUP    
    payload_type = payload_type 
    #pack the header with all that info
    header = struct.pack('!BBHII', (version << 6) | (padding << 5) | (extension << 4) | csrc_count,
                         (marker << 7) | payload_type, sequence_number, timestamp, ssrc)
    return header

# Parse the RTP header into a map
# input: byte data
def parse_rtp_header(data):
    #extract information based on location in data. Lots of byte manipulation!
    version = (data[0] & 0xC0) >> 6
    padding = (data[0] & 0x20) >> 5
    extension = (data[0] & 0x10) >> 4
    csrc_count = data[0] & 0x0F
    marker = (data[1] & 0x80) >> 7
    payload_type = data[1] & 0x7F
    sequence_number = struct.unpack('!H', data[2:4])[0]
    timestamp = struct.unpack('!I', data[4:8])[0]
    ssrc = struct.unpack('!I', data[8:12])[0]

    #create a map from extracted data
    return {
        "version": version,
        "padding": padding,
        "extension": extension,
        "csrc_count": csrc_count,
        "marker": marker,
        "payload_type": payload_type,
        "sequence_number": sequence_number,
        "timestamp": timestamp,
        "ssrc": ssrc
    }

#print rtp header for debugging purposes
def print_header(header, elapsed_time):
    print("__________________________")
    print("RTP Header:")
    print("Version:", header["version"])
    print("Padding:", header["padding"])
    print("Extension:", header["extension"])
    print("CSRC Count:", header["csrc_count"])
    print("Marker:", header["marker"])
    print("Payload Type:", header["payload_type"])
    print("Sequence Number:", header["sequence_number"])
    print("Timestamp:", header["timestamp"])
    print("Time Delta: " + str(elapsed_time) + " ms")
    print("SSRC:", header["ssrc"])
    print("__________________________")
    print()