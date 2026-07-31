#!/bin/bash
# Build StarRocks 3.3.17 on ARM64 with per-catalog Kerberos + HA patches
set -euo pipefail

SRC_DIR="/Bigdata1/starrocks-src"
PATCH_DIR="/Bigdata1/build-starrocks/patches"
BUILD_IMAGE="starrocks/dev-env-centos7:3.3.17"
CONTAINER_NAME="sr-arm-build"

# Check source exists
if [ ! -d "$SRC_DIR" ] || [ ! -f "$SRC_DIR/build.sh" ]; then
    echo "ERROR: StarRocks source not found at $SRC_DIR"
    exit 1
fi

# Start build container if not running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    docker run -d --name "$CONTAINER_NAME" \
        --network host \
        -v "$SRC_DIR:/data/starrocks-src" \
        -v "$PATCH_DIR:/data/patches" \
        "$BUILD_IMAGE" sleep infinity
    echo "Container $CONTAINER_NAME started"
fi

echo "=== Applying patches ==="
# Apply FE patches
docker exec "$CONTAINER_NAME" bash -c '
    cd /data/starrocks-src
    echo "Apply HDFSCloudCredential.java (toThrift)"
    python3 /data/patches/modify_toThrift.py

    echo "Apply HiveMetaClient.java + HadoopExt.java"
    patch -p1 < /data/patches/starrocks-fixes.patch

    echo "Apply BE per-catalog Kerberos patch"
    patch -p1 < /data/patches/starrocks-be-per-catalog-kerberos.patch
'

echo "=== BE Build ==="
docker exec "$CONTAINER_NAME" bash -c '
    cd /data/starrocks-src
    ./build.sh --be --clean -j $(nproc) 2>&1
' | tee /tmp/be_build.log

echo "=== FE Build ==="
docker exec "$CONTAINER_NAME" bash -c '
    cd /data/starrocks-src
    mvn package -Dcheckstyle.skip=true -DskipTests 2>&1
' | tee /tmp/fe_build.log

echo "=== Build Complete ==="
