# Memory Scanner SOP

内存特征搜索工具，支持 Hex（CE 风格）和字符串匹配；提供 LLM 模式便于大模型分析内存上下文。

**平台**：仅 **Windows**（kernel32.ReadProcessMemory）。macOS/Linux 不可用，需用 ptrace/proc 等替代方案时再扩展。

**依赖**：`pip install yara-python`

## 1. 快速开始

**Python 调用**（需先将 `memory` 加入 path）：

```python
import sys
sys.path.insert(0, "memory")  # 或代码根下 .. 根据 cwd 调整
from mem_scanner import scan_memory

# 示例：Hex 特征码，开启 llm_mode 获取上下文
results = scan_memory(pid, "48 8b ?? ?? 00", mode="hex", llm_mode=True)
```

**CLI**（在代码根或 memory 目录下）：

```bash
python memory/mem_scanner.py <PID> "pattern" --mode string
python memory/mem_scanner.py <PID> "pattern" --llm
```

## 2. 典型场景：结构体或关键数据定位

1. 确定目标数据的前导特征或已知常量（如 Header、Magic Number）。
2. 在目标进程中搜索：`scan_memory(pid, "4D 5A 90 00", mode="hex", llm_mode=True)`。
3. 分析返回的 JSON 中 `address`/`hex`/`ascii` 等字段。

## 3. 注意事项

- **权限**：需对目标进程具备 `PROCESS_QUERY_INFORMATION` 和 `PROCESS_VM_READ`，非强制管理员。
- **效率**：大块内存搜索时尽量用更唯一的特征码以减少误报。

## 4. CE 式差集扫描定位动态字段 (Windows)

用于定位自绘 UI 中随操作变化的内存（如当前会话标题）。核心：一次全量 scan + 多次 ReadProcessMemory 筛选。

**流程概要**：

1. 取 PID（多进程时用窗口所属进程，如 win32gui.GetWindowThreadProcessId）。
2. 状态 A → `scan_memory(pid, "关键词A", mode="string")` → 地址集 S。
3. 切到状态 B → 读 S 中全部地址 → 保留内容 ≠ "关键词A" 的 → 候选 C。
4. 切回 A → 读 C 中全部地址 → 保留内容 == "关键词A" 的 → 候选 C'。
5. 若 C'>1，再切换重复直到唯一。

**坑点**：步骤 3/4 必须用 ReadProcessMemory 读原地址集，严禁重新 scan（重新 scan 会得到新地址，动态内容已变）。提取地址时注意返回格式（默认为字符串列表，解析用 `int(r.split('\n')[0].split(':')[1], 16)` 等）。
