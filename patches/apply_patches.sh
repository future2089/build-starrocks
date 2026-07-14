#!/bin/bash
# apply_patches.sh — Apply StarRocks source patches for HDFS HA + Kerberos isolation
# Usage: cd /path/to/starrocks-3.3.17 && bash /path/to/apply_patches.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_FE_FE="$PWD/fe/fe-core/src/main/java/com/starrocks"
SRC_EXT="$PWD/java-extensions/hadoop-ext/src/main/java/com/starrocks"

echo "Applying patches..."

# 1. HDFSCloudCredential.java
cp "$SCRIPT_DIR/HDFSCloudCredential.java" \
   "$SRC_FE_FE/credential/hdfs/HDFSCloudCredential.java"
echo "  [OK] HDFSCloudCredential.java"

# 2. HadoopExt.java (FE version)
cp "$SCRIPT_DIR/HadoopExt.java" \
   "$SRC_FE_FE/connector/hadoop/HadoopExt.java"
echo "  [OK] HadoopExt.java (FE)"

# 3. HadoopExt.java (java-extensions version)
cp "$SCRIPT_DIR/HadoopExt.java" \
   "$SRC_EXT/connector/hadoop/HadoopExt.java"
echo "  [OK] HadoopExt.java (java-extensions)"

# 4. HiveMetaClient.java
cp "$SCRIPT_DIR/HiveMetaClient.java" \
   "$SRC_FE_FE/connector/hive/HiveMetaClient.java"
echo "  [OK] HiveMetaClient.java"

echo ""
echo "All patches applied. Proceed with:"
echo "  FE: mvn package -Dcheckstyle.skip=true"
echo "  BE: ./build.sh --be"
