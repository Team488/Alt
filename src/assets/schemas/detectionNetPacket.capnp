@0xa58f964fa384ee24;

struct DataPacket {
    message @0 :Text;                     # String message
    timestamp @1 :Float64;                 # Timestamp for the frame
    detections @2 :List(Detection);                  # List of detections
}

struct Detection {
    id @0 :Int8;                          # Deep sort local id
    coordinates @1 :XYZ;                  # Tuple of integers for detection coordinates
    confidence @2 :Float64;                      # detection confidence
    isRobot @3 :Bool;                          # is robot detection flag
    features @4 :DataArray;                    # NumPy-like array for extracted features
}

struct XYZ {
    x @0 :Int16;                         # x component
    y @1 :Int16;                       # y component
    z @2 :Int16;                        # z component
}

struct DataArray {
    length @0 :Int16;                      # Length of the data
    data @1 :List(Float64);                   # Raw data as a list of signed 8-bit integers
}
