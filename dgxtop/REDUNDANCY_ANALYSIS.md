# Code Redundancy Analysis

## Summary of Redundant Code Found

### 1. **`get_ifc.py` vs `network_monitor.py._get_available_interfaces()`** ⚠️ **HIGH PRIORITY**

**Status**: **REDUNDANT** - Nearly identical code

**Details**:
- `get_ifc.py` (lines 21-72): Function `get_connected_devices()` with 50+ lines
- `network_monitor.py` (lines 197-248): Method `_get_available_interfaces()` with identical logic
- **Difference**: `get_ifc.py` has a debug print statement on line 71: `print(f"appending Device: {device}...")`
- **Usage**: 
  - `get_ifc.py` is **NOT imported** by any production code
  - Only used as standalone script
  - `network_monitor.py` has its own implementation

**Recommendation**: 
- Remove debug print from `get_ifc.py` if keeping it as standalone utility
- Or: Have `network_monitor.py` import from `get_ifc.py` to avoid duplication
- Or: Delete `get_ifc.py` if not needed as standalone

---

### 2. **`roce_stats.py` vs `enp_stats.py`** ⚠️ **MEDIUM PRIORITY**

**Status**: **REDUNDANT** - Nearly identical files, only function name differs

**Details**:
- `roce_stats.py`: Function `get_roce_counters()`
- `enp_stats.py`: Function `get_enp_counters()` 
- **Both files are identical** except for function name (lines 4, 48)
- **Functionality**: Already integrated into `network_monitor.py._read_roce_counters()` (lines 76-107)

**Usage**:
- Used by test scripts: `get-roce-counts.py`, `get-enp-counts.py`, `get-enp.counts.py`
- Not used by main application (`main.py`)

**Recommendation**:
- Consider consolidating: Keep one file or remove if test scripts can use `network_monitor.py` directly
- Or: Keep if needed for standalone testing utilities

---

### 3. **Standalone Test Scripts** ⚠️ **LOW PRIORITY**

**Status**: **POTENTIALLY REDUNDANT** - Test utilities

**Files**:
- `get-roce-counts.py` - Uses `roce_stats.py`
- `get-enp-counts.py` - Uses `enp_stats.py`  
- `get-enp.counts.py` - Uses `roce_stats.py` (note the dot)

**Recommendation**:
- Keep if needed for manual testing/debugging
- Consider using `test_network_monitor.py` instead for testing
- Remove duplicate `get-enp.counts.py` (looks like typo version)

---

### 4. **Code Quality Issues**

#### `get_ifc.py` Line 71:
```python
print(f"appending Device: {device}, State: {state}, External: {external}")
```
**Issue**: Debug print statement should be removed or made optional

#### `roce_stats.py` and `enp_stats.py` Lines 41-46:
```python
tx_pkts = int(open(tx_pkts_file).read().strip())
```
**Issue**: Files opened but not properly closed. Should use context manager:
```python
with open(tx_pkts_file, "r") as f:
    tx_pkts = int(f.read().strip())
```
Note: This is already fixed in `network_monitor.py._read_roce_counters()`

---

## Recommended Actions

### High Priority:
1. ✅ **Consolidate interface discovery**: Use `get_ifc.py` in `network_monitor.py` or vice versa
2. ✅ **Remove debug print** from `get_ifc.py` line 71

### Medium Priority:
3. ✅ **Consolidate RoCE counter reading**: Remove `enp_stats.py` if not needed, or consolidate with `roce_stats.py`
4. ✅ **Check if `get-enp.counts.py` is a typo** and should be removed

### Low Priority:
5. ✅ **Review test scripts**: Determine if all test scripts are needed or can use `test_network_monitor.py`
6. ✅ **Fix file handle leaks** in `roce_stats.py` and `enp_stats.py` (if keeping them)

---

## Files Overview

| File | Status | Used By | Recommendation |
|------|--------|---------|----------------|
| `get_ifc.py` | Redundant | None (standalone) | Import in `network_monitor.py` or remove |
| `roce_stats.py` | Redundant | Test scripts | Keep if needed for standalone utilities |
| `enp_stats.py` | Redundant | Test scripts | Consider removing or consolidating |
| `get-roce-counts.py` | Test utility | Manual testing | Keep if needed |
| `get-enp-counts.py` | Test utility | Manual testing | Keep if needed |
| `get-enp.counts.py` | Test utility? | Unknown | Check if typo, consider removing |
