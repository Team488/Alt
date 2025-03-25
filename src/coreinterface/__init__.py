"""
Core Interface Package - Data structures for inter-component communication

This package defines the key data structures used for communication between
different components of the system. It provides serializable packet classes
that enable structured data exchange across process and network boundaries.

Key components include:
- FramePacket: For transmitting camera frames with metadata
- DetectionPacket: For sharing object detection results
- ReefPacket: For communicating reef tracking information

Each packet type implements serialization and deserialization methods to
convert between in-memory object representations and binary formats suitable
for network transmission. The packet formats are designed to be efficient
while carrying all necessary information for the receiving components.
"""