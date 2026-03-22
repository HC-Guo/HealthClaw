# 滴滴出行 - 叫车服务 SOP (Didi Taxi Service)

> **must call update working ckp**：`手机操控用phone_control工具｜操作前先check_connection｜每步操作后截图确认`

## 0. 前置条件
- Android 手机已通过 USB 连接电脑，或在同一 WiFi 下通过 `adb connect <ip>:5555` 连接
- 手机已开启 USB 调试（设置 → 开发者选项 → USB调试）
- 电脑已安装 adb：`brew install android-platform-tools`（macOS）
- 手机已安装滴滴出行应用

## 1. 叫车服务流程

### Step 1: 检查连接
```
phone_control(action="check_connection")
```
确认手机已连接、型号、分辨率。

### Step 2: 启动滴滴出行
```
phone_control(action="launch_app", app="滴滴出行")
```
启动滴滴出行应用。

### Step 3: 查找目的地输入框
```
phone_control(action="ui_dump", keyword="目的地")
```
找到目的地输入框位置。

### Step 4: 点击目的地输入框
```
phone_control(action="tap", x=目的地输入框坐标, y=目的地输入框y坐标)
```
点击目的地输入框，激活输入。

### Step 5: 输入目的地
```
phone_control(action="input_text", text="医院名称")
```
输入医院名称作为目的地。

### Step 6: 执行搜索
```
phone_control(action="press_key", key="enter")
```
按回车键执行搜索。

### Step 7: 选择目的地
```
phone_control(action="tap", x=目的地选项坐标, y=目的地选项y坐标)
```
点击选择正确的目的地。

### Step 8: 查找叫车按钮
```
phone_control(action="ui_dump", keyword="叫车")
```
找到叫车按钮位置。

### Step 9: 点击叫车
```
phone_control(action="tap", x=叫车按钮坐标, y=叫车按钮y坐标)
```
点击叫车按钮，发起叫车请求。

## 2. 示例：叫车去医院

```
1. phone_control(action="check_connection")          # 确认连接
2. phone_control(action="launch_app", app="滴滴出行")  # 打开滴滴出行
3. phone_control(action="ui_dump", keyword="目的地")  # 找到目的地输入框
4. phone_control(action="tap", x=目的地输入框坐标, y=目的地输入框y坐标)  # 点击输入框
5. phone_control(action="input_text", text="北京大学第三医院")  # 输入医院名称
6. phone_control(action="press_key", key="enter")     # 执行搜索
7. phone_control(action="tap", x=目的地选项坐标, y=目的地选项y坐标)  # 选择目的地
8. phone_control(action="ui_dump", keyword="叫车")    # 找到叫车按钮
9. phone_control(action="tap", x=叫车按钮坐标, y=叫车按钮y坐标)  # 点击叫车
```

## 3. 避坑指南
- **等待加载**：滴滴出行应用启动和页面加载需要时间，操作后请等待 2-3 秒
- **定位权限**：确保滴滴出行已获得定位权限，否则无法获取当前位置
- **网络连接**：确保手机有网络连接，否则无法叫车
- **坐标系统**：tap 使用手机的物理像素坐标（即截图上的坐标）
- **连接断开**：长时间操作可能断开，定期 check_connection
- **支付确认**：涉及支付操作时必须先用 ask_user 确认