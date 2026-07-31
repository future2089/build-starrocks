#!/bin/bash
set -euo pipefail

SRC_DIR="/Bigdata1/starrocks-src"
PATCH_DIR="/Bigdata1/build-starrocks/patches"
BUILD_IMAGE="starrocks/dev-env-centos7:3.3.17"
CONTAINER_NAME="sr-arm-build"
START_TIME=$(date +%s)

log() { echo "[$(date +%H:%M:%S)] $*"; }

# 1. Extract source if needed
if [ -f "/Bigdata1/starrocks-3.3.tar.gz" ] && [ ! -f "$SRC_DIR/build.sh" ]; then
    log "Extracting source tarball..."
    mkdir -p "$SRC_DIR"
    cd /Bigdata1

    # Handle different tarball top-level dir names
    tar xzf starrocks-3.3.tar.gz -C /Bigdata1/tmp_extract 2>/dev/null || mkdir -p /Bigdata1/tmp_extract
    cd /Bigdata1/tmp_extract
    EXTRACTED_DIR=$(ls -d */ 2>/dev/null | head -1)
    if [ -n "$EXTRACTED_DIR" ]; then
        rm -rf "$SRC_DIR" 2>/dev/null || true
        mv "$EXTRACTED_DIR" "$SRC_DIR"
    fi
    rm -rf /Bigdata1/tmp_extract
    log "Source extracted to $SRC_DIR"
fi

if [ ! -f "$SRC_DIR/build.sh" ]; then
    log "ERROR: Source build.sh not found at $SRC_DIR"
    ls -la "$SRC_DIR/" 2>/dev/null | head -20
    exit 1
fi

# 2. Start build container
log "Starting build container..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
docker run -d --name "$CONTAINER_NAME" \
    --network host \
    -v "$SRC_DIR:/data/starrocks-src" \
    -v "$PATCH_DIR:/data/patches" \
    "$BUILD_IMAGE" sleep infinity
log "Container $CONTAINER_NAME started"

# 3. Fix Python patch scripts paths (use double-quotes inside sed)
docker exec "$CONTAINER_NAME" bash -c "sed -i \"s|/data/starrocks-build/starrocks-3.3.17|/data/starrocks-src|g\" /data/patches/modify_hdfs_cache.py"
docker exec "$CONTAINER_NAME" bash -c "sed -i \"s|/data/starrocks-build/starrocks-3.3.17|/data/starrocks-src|g\" /data/patches/modify_toThrift.py"
docker exec "$CONTAINER_NAME" bash -c "sed -i \"s|/data/starrocks-build/starrocks-3.3.17|/data/starrocks-src|g\" /data/patches/modify_hdfs_provider.py"
log "Patch paths fixed"

# 4. Apply FE patches
log "Applying FE patches..."
docker exec "$CONTAINER_NAME" bash -c "
    cd /data/starrocks-src
    python3 /data/patches/modify_toThrift.py
    patch -p1 < /data/patches/starrocks-fixes.patch || echo 'fe-fixes patch may already be applied (ok)'
    echo 'FE patches done'
"
log "FE patches applied"

# 5. Apply BE patches
log "Applying BE patches..."
docker exec "$CONTAINER_NAME" bash -c "
    cd /data/starrocks-src
    python3 /data/patches/modify_hdfs_cache.py
    python3 /data/patches/modify_hdfs_provider.py
    echo 'BE patches done'
"
log "BE patches applied"

# 6. Build BE (this takes the longest)
log "========== Building BE =========="
docker exec "$CONTAINER_NAME" bash -c "
    cd /data/starrocks-src
    ./build.sh --be --clean -j \$(nproc) 2>&1
" && log "BE build SUCCEEDED" || log "BE build FAILED"

# 7. Build FE
log "========== Building FE =========="
docker exec "$CONTAINER_NAME" bash -c "
    cd /data/starrocks-src
    mvn package -Dcheckstyle.skip=true -DskipTests 2>&1
" && log "FE build SUCCEEDED" || log "FE build FAILED"

END_TIME=$(date +%s)
DURATION=$(( (END_TIME - START_TIME) / 60 ))
log "Total build time: ${DURATION} minutes"
log "Build complete!"
