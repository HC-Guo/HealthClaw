# ljqCtrl 使用与坐标转换 SOP

> **must call update working ckp**：`ljqCtrl 一律使用物理坐标｜禁 pyautogui｜操作前先 gw 激活窗口`

**平台**：`memory/ljqCtrl.py` 仅支持 **Windows**。macOS/Linux 上可用 `pyautogui`（`pip install pyautogui`）做点击/按键，无 DPI 换算时坐标即物理像素。

## 0. API 快速参考 (Windows)

- `ljqCtrl.dpi_scale`: float（缩放系数 = 逻辑宽度 / 物理宽度）
- `ljqCtrl.SetCursorPos(z)`: 移动鼠标到物理坐标 z=(x, y)
- `ljqCtrl.Click(x, y=None)`: 模拟点击。支持 `Click((x, y))` 或 `Click(x, y)`
- `ljqCtrl.Press(cmd, staytime=0)`: 模拟按键。如 `Press('ctrl+c')`
- `ljqCtrl.FindBlock(fn, wrect=None, threshold=0.8)`: 找图。返回 `((center_x, center_y), is_found)`
- `ljqCtrl.MouseDClick(staytime=0.05)`: 鼠标双击

## 1. 环境载入

先将 `memory` 加入路径再导入：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# 或 code_run 时 cwd 为代码根： sys.path.insert(0, "memory")
from memory import ljqCtrl
# Windows 下需 pygetwindow 激活窗口： pip install pygetwindow
import pygetwindow as gw
```

## 2. 核心：High-DPI 物理坐标换算 (Windows)

`ljqCtrl` 的 `Click/SetCursorPos` 接收**物理像素坐标**（与截图像素一致）。从 `pygetwindow` 得到的窗口位置为逻辑坐标时，需除以 `dpi_scale`。

- **换算公式**：`物理坐标 = 逻辑坐标 / ljqCtrl.dpi_scale`
- 代码应始终用 `dpi_scale` 动态计算，不写死分辨率。

## 3. 窗口操作与点击流程 (Windows)

1. **激活窗口**：`gw.getWindowsWithTitle('标题')[0].restore(); .activate()`
2. **坐标计算**：
```python
win = gw.getWindowsWithTitle('微信')[0]
lx, ly = 150, 100   # 窗口内逻辑坐标
px = int(lx / ljqCtrl.dpi_scale)
py = int(ly / ljqCtrl.dpi_scale)
ljqCtrl.Click(px, py)
```

## 4. 避坑指南

- **一律使用物理坐标**：传给 Click/SetCursorPos 的必须是物理坐标；从 pygetwindow 来的逻辑坐标先 `/ dpi_scale`。
- **操作前必须 activate()** 目标窗口。
- **GetWindowRect 与客户区**：GetWindowRect 含标题栏/边框；点击截图内元素时用 `ClientToScreen(hwnd, (0,0))` 取客户区原点再加截图内坐标。

## 5. macOS / Linux 替代

- 使用 `pyautogui`：`import pyautogui; pyautogui.click(x, y); pyautogui.hotkey('ctrl', 'c')`。坐标通常即物理像素，无需 dpi_scale。
- 需找图时可用 `pyautogui.locateOnScreen('template.png')` 等。
