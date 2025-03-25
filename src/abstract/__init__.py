"""
Abstract Package - Core interfaces and base classes for system components

This package contains the foundational abstract base classes that define the core
interfaces for the entire system. These abstract classes establish the contracts
that concrete implementations must fulfill, ensuring consistent behavior across
the system.

Key components include:
- Agent: Base interface for all agent components
- AlignmentProvider: Interface for systems that provide alignment data
- BaseDemo: Foundation for demonstration applications
- Capture: Interface for camera and sensor capture systems
- Order: Base interface for command objects dispatched to agents
- depthCamera: Interface for depth-sensing camera systems
- inferencerBackend: Base for ML inference engine implementations

These abstractions allow for:
- Component interchangeability through common interfaces
- Clear separation of concerns between system modules
- Extension points for new implementations
- Testability through mock implementations
"""