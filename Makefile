.PHONY: test proto

# Stubs are generated from the daemon repo's .proto files.
PROTO_DIR ?= ../clusdr/proto

proto:
	python3 -m grpc_tools.protoc \
		--proto_path=$(PROTO_DIR) \
		--python_out=src \
		--grpc_python_out=src \
		--pyi_out=src \
		$(PROTO_DIR)/clusdr/v1alpha1/health.proto \
		$(PROTO_DIR)/clusdr/v1alpha1/membership.proto \
		$(PROTO_DIR)/clusdr/v1alpha1/watch.proto \
		$(PROTO_DIR)/clusdr/v1alpha1/events.proto \
		$(PROTO_DIR)/clusdr/v1alpha1/locks.proto \
		$(PROTO_DIR)/clusdr/v1alpha1/leases.proto

test:
	python3 -m pytest -q
