"""
Protobuf generated code package.

This package contains the generated Python protobuf classes for the agentic framework.
These are generated from the .proto files in the proto/ directory.
"""

# Import generated protobuf modules
try:
    from . import common_pb2
    from . import task_pb2
    from . import plan_pb2
    from . import services_pb2
    
    # Import gRPC service modules
    from . import common_pb2_grpc
    from . import task_pb2_grpc
    from . import plan_pb2_grpc
    from . import services_pb2_grpc
    
    __all__ = [
        "common_pb2",
        "task_pb2", 
        "plan_pb2",
        "services_pb2",
        "common_pb2_grpc",
        "task_pb2_grpc",
        "plan_pb2_grpc", 
        "services_pb2_grpc",
    ]
except ImportError:
    # Protobuf files not yet generated
    __all__ = [] 