@0x9d88d53810bc5894;

struct DataPacket {
    message @0 :Text;                     # String message
    frame @1 :FrameData;                  # FrameData type to hold the frame
    timestamp @2 :Float64;                 # Timestamp for the frame
}


struct FrameData {
    width @0 :Int16;                       # Width of the frame
    height @1 :Int16;                      # Height of the frame
    channels @2 :UInt8;                    # Number of color channels (3 for RGB)
    data @3 :List(UInt8);                   # Raw pixel data as a list of
}
