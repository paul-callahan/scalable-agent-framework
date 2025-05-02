.PHONY: proto-gen proto-lint proto-clean proto-check install-deps

# Generate Python code from protobuf definitions
proto-gen:
	buf generate protos/

# Lint protobuf files for style and consistency
proto-lint:
	buf lint protos/

# Clean generated files
proto-clean:
	find services/standalone-py -name "*_pb2.py" -delete
	find services/standalone-py -name "*_pb2.pyi" -delete
	find services/standalone-py -name "*_grpc.py" -delete
	find services/standalone-py -name "*_grpc.pyi" -delete

# Validate protobuf definitions and check for breaking changes
proto-check:
	buf check protos/

# Install required tools (Buf, protoc plugins)
install-deps:
	# Install Buf
	curl -sSL \
		"https://github.com/bufbuild/buf/releases/latest/download/buf-$(uname -s)-$(uname -m)" \
		-o "buf" && \
	chmod +x "buf" && \
	sudo mv "buf" /usr/local/bin/
	
	# Install Python protobuf compiler
	pip install grpcio-tools

# Default target
all: proto-gen 