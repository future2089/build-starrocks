#!/bin/bash
# apply_patches.sh — Apply StarRocks patches for per-catalog Kerberos + HDFS HA.
#
# Usage:
#   cd /path/to/starrocks-3.3.17
#   bash /path/to/patches/apply_patches.sh
#
# Scope: FE only. There is NO BE (C++) patch anymore -- see obsolete/WHY_OBSOLETE.md
# for why the old starrocks-be.patch was proven ineffective and retired.
#
# What gets applied:
#   1. starrocks-fe.patch  -> HiveMetaClient / HDFSCloudConfigurationProvider / HDFSCloudCredential
#   2. HadoopExt.java      -> copied to TWO locations (NOT part of the .patch file)
#
# The HadoopExt.java copy is the single most important step. It carries
# getHDFSUGI() / getOrCreateKeytabUGI() / canSkipKrb5Swap(), which is what
# actually makes multi-realm isolation work on both FE and BE. Applying only
# the .patch file will silently produce a build that still shares one global
# Kerberos identity across all catalogs.
#
# Tested on StarRocks 3.3.17 (3eac4a9).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_ROOT="$PWD"
SRC_FE="$SRC_ROOT/fe/fe-core/src/main/java/com/starrocks"
SRC_EXT="$SRC_ROOT/java-extensions/hadoop-ext/src/main/java/com/starrocks"

if [ ! -d "$SRC_FE" ] || [ ! -d "$SRC_EXT" ]; then
    echo "ERROR: not a StarRocks source root."
    echo "       Expected to find:"
    echo "         $SRC_FE"
    echo "         $SRC_EXT"
    echo "       cd into the starrocks-3.3.17 directory first."
    exit 1
fi

echo "=== [1/2] Applying FE patch ==="
git apply "$SCRIPT_DIR/starrocks-fe.patch" || {
    echo "ERROR: failed to apply starrocks-fe.patch"
    echo "       If you are NOT on 3.3.x, expect conflicts in HiveMetaClient.java"
    echo "       (upstream added an HMS connection pool in 3.4+)."
    echo "       See docs/patch_migration_assessment.md."
    exit 1
}
echo "  [OK] starrocks-fe.patch"

echo ""
echo "=== [2/2] Installing HadoopExt.java (per-catalog UGI isolation) ==="
cp "$SCRIPT_DIR/HadoopExt.java" "$SRC_FE/connector/hadoop/HadoopExt.java"
echo "  [OK] -> fe/fe-core     (used by FE, packaged into starrocks-fe.jar)"

cp "$SCRIPT_DIR/HadoopExt.java" "$SRC_EXT/connector/hadoop/HadoopExt.java"
echo "  [OK] -> java-extensions (used by BE, packaged into starrocks-hadoop-ext.jar)"

echo ""
echo "=== Verifying installed sources ==="
for f in "$SRC_FE/connector/hadoop/HadoopExt.java" "$SRC_EXT/connector/hadoop/HadoopExt.java"; do
    for kw in getHDFSUGI getOrCreateKeytabUGI loginUserFromKeytabAndReturnUGI; do
        grep -q "$kw" "$f" || { echo "  [FAIL] $kw missing in $f"; exit 1; }
    done
done
echo "  [OK] all three key methods present in both copies"

echo ""
echo "=== Done ==="
echo ""
echo "Build:"
echo "  FE: cd fe && mvn package -DskipTests -Dcheckstyle.skip=true"
echo "  BE: ./build.sh --be -j 2       # cc1plus ~4GB/proc, add swap first"
echo ""
echo "Already have a running cluster? Skip the full rebuild and use"
echo "the hot-patch path instead (~5 minutes, FE + BE jars in place):"
echo "  deploy/hotpatch_hadoop_ext.sh"
