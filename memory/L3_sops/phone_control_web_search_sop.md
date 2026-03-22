# 手机控制 - 网络搜索 SOP (Phone Control - Web Search)

> **must call update working ckp**：`手机操控用phone_control工具｜操作前先check_connection｜每步操作后截图确认`

## 0. 前置条件
- Android 手机已通过 USB 连接电脑，或在同一 WiFi 下通过 `adb connect <ip>:5555` 连接
- 手机已开启 USB 调试（设置 → 开发者选项 → USB调试）
- 电脑已安装 adb：`brew install android-platform-tools`（macOS）

## 1. 网络搜索流程

### Step 1: 检查连接
```
phone_control(action="check_connection")
```
确认手机已连接、型号、分辨率。

### Step 2: 启动浏览器
```
phone_control(action="launch_app", app="QQ浏览器")
```
启动 QQ浏览器。也可以把QQ浏览器换成其他浏览器，如 Edge、夸克 等。

### Step 3: 输入搜索内容
```
phone_control(action="ui_dump", keyword="搜索")
phone_control(action="tap", x=搜索框坐标, y=搜索框y坐标)
# 清除搜索框中的残留内容
phone_control(action="ui_dump")
# 检测搜索框是否有内容，有则清除
for _ in range(3):  # 最多尝试3次
    # 按20次delete键
    for _ in range(20):
        phone_control(action="press_key", key="delete")
        time.sleep(0.1)
    # 再次检查是否清空
    phone_control(action="ui_dump")
    # 如果搜索框已清空，退出循环
    # 这里需要根据实际情况判断搜索框是否为空
phone_control(action="input_text", text="搜索关键词")
phone_control(action="press_key", key="enter")
```
输入搜索关键词并执行搜索。

### Step 4: 查看搜索结果
```
phone_control(action="ui_dump")
```
查看搜索结果，找到相关信息。

### Step 5: 点击查看详情
```
phone_control(action="tap", x=搜索结果坐标, y=搜索结果y坐标)
```
点击搜索结果查看详情。

## 2. 示例：搜索地图定位方法

```
1. phone_control(action="check_connection")          # 确认连接
2. phone_control(action="launch_app", app="chrome")  # 打开浏览器
3. phone_control(action="ui_dump", keyword="搜索")    # 找到搜索框
4. phone_control(action="tap", x=搜索框坐标, y=搜索框y坐标)  # 点击搜索框
5. # 清除搜索框中的残留内容
6. for _ in range(3):  # 最多尝试3次
7.     # 按20次delete键
8.     for _ in range(20):
9.         phone_control(action="press_key", key="delete")
10.         time.sleep(0.1)
11.     # 再次检查是否清空
12.     phone_control(action="ui_dump")
13. phone_control(action="input_text", text="高德地图如何获取当前位置")  # 输入搜索内容
14. phone_control(action="press_key", key="enter")     # 执行搜索
15. phone_control(action="ui_dump")                    # 查看搜索结果
16. phone_control(action="tap", x=搜索结果坐标, y=搜索结果y坐标)  # 点击查看详情
```

## 3. 避坑指南
- **等待加载**：浏览器页面加载需要时间，操作后请等待 3-5 秒
- **网络连接**：确保手机有网络连接，否则搜索会失败
- **输入中文**：需要安装 ADBKeyboard，否则只能输入英文/数字
- **坐标系统**：tap 使用手机的物理像素坐标（即截图上的坐标）
- **连接断开**：长时间操作可能断开，定期 check_connection