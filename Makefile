.PHONY: test proto

# Stubs from buf.build/clusdr/api (join/heartbeat are buf.build/clusdr/internal).
PROTO_DIR ?= ../clusdr/proto/api
BSR_MODULE ?= buf.build/clusdr/api
PROTO_REF ?= main
GIT_PROTO ?= https://github.com/clusdr/clusdr.git#branch=$(PROTO_REF),subdir=proto/api
STAGED := .proto

proto:
	@command -v buf >/dev/null || { echo "buf is required: https://buf.build/docs/cli/installation"; exit 1; }
	rm -rf $(STAGED)
	@if [ -d "$(PROTO_DIR)/clusdr/v1alpha1" ]; then \
		buf export "$(PROTO_DIR)" -o $(STAGED); \
	elif buf build "$(BSR_MODULE):$(PROTO_REF)" >/dev/null 2>&1; then \
		buf export "$(BSR_MODULE):$(PROTO_REF)" -o $(STAGED); \
	else \
		buf export "$(GIT_PROTO)" -o $(STAGED); \
	fi
	python3 -m grpc_tools.protoc \
		--proto_path=$(STAGED) \
		--python_out=src \
		--grpc_python_out=src \
		--pyi_out=src \
		$(STAGED)/clusdr/v1alpha1/health.proto \
		$(STAGED)/clusdr/v1alpha1/membership.proto \
		$(STAGED)/clusdr/v1alpha1/watch.proto \
		$(STAGED)/clusdr/v1alpha1/events.proto \
		$(STAGED)/clusdr/v1alpha1/locks.proto \
		$(STAGED)/clusdr/v1alpha1/leases.proto
	rm -rf $(STAGED)

test:
	python3 -m pytest -q
