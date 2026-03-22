# 微信 - 滴滴出行打车 SOP (WeChat Didi Taxi Service)

> **must call update working ckp**：`手机操控用phone_control工具｜操作前先check_connection｜每步操作后截图确认`

## 0. 前置条件
- Android 手机已通过 USB 连接电脑，或在同一 WiFi 下通过 `adb connect <ip>:5555` 连接
- 手机已开启 USB 调试（设置 → 开发者选项 → USB调试）
- 电脑已安装 adb：`brew install android-platform-tools`（macOS）
- 手机已安装微信应用
- 微信已登录并绑定滴滴出行账号

## 1. 微信打车流程

### Step 1: 检查连接
```
phone_control(action="check_connection")
```
确认手机已连接、型号、分辨率。

### Step 2: 启动微信
```
phone_control(action="launch_app", app="微信")
```
启动微信应用。

### Step 3: 查找并点击“我”
```
phone_control(action="ui_dump", keyword="我")
phone_control(action="tap", x=我按钮坐标, y=我按钮y坐标)
```
在微信主界面下方找到“我”按钮并点击。

### Step 4: 查找并点击“服务”
```
phone_control(action="ui_dump", keyword="服务")
phone_control(action="tap", x=服务按钮坐标, y=服务按钮y坐标)
```
在“我”界面找到“服务”并点击。

### Step 5: 查找并点击“滴滴出行”
```
phone_control(action="ui_dump", keyword="滴滴出行")
# 如果找不到，向下滚动页面
if 滴滴出行按钮未找到:
    phone_control(action="scroll_down")
    phone_control(action="ui_dump", keyword="滴滴出行")
phone_control(action="tap", x=滴滴出行按钮坐标, y=滴滴出行按钮y坐标)
```
在“服务”界面找到“滴滴出行”并点击，如果找不到可以向下滚动页面。

### Step 6: 关闭广告（如果有）
```
phone_control(action="ui_dump", keyword="关闭")
or
phone_control(action="ui_dump", keyword="×")
if 广告关闭按钮找到:
    phone_control(action="tap", x=关闭按钮坐标, y=关闭按钮y坐标)
```
如果有弹出的广告，点击叉号关掉广告。

### Step 7: 查找并点击搜索框
```
phone_control(action="ui_dump", keyword="搜索")
or
phone_control(action="ui_dump", keyword="目的地")
phone_control(action="tap", x=搜索框坐标, y=搜索框y坐标)
```
进入滴滴出行页面后，找到并点击搜索框。

### Step 8: 输入目的地并回车
```
phone_control(action="input_text", text="目的地名称")
phone_control(action="press_key", key="enter")
```
在搜索框中输入目的地并回车。

## 2. 示例：通过微信打车

```
1. phone_control(action="check_connection")          # 确认连接
2. phone_control(action="launch_app", app="微信")     # 打开微信
3. phone_control(action="ui_dump", keyword="我")      # 找到“我”
4. phone_control(action="tap", x=我按钮坐标, y=我按钮y坐标)  # 点击“我”
5. phone_control(action="ui_dump", keyword="服务")    # 找到“服务”
6. phone_control(action="tap", x=服务按钮坐标, y=服务按钮y坐标)  # 点击“服务”
7. phone_control(action="ui_dump", keyword="滴滴出行")  # 找到“滴滴出行”
8. phone_control(action="tap", x=滴滴出行按钮坐标, y=滴滴出行按钮y坐标)  # 点击“滴滴出行”
9. phone_control(action="ui_dump", keyword="关闭")    # 检查是否有广告
10. phone_control(action="tap", x=关闭按钮坐标, y=关闭按钮y坐标)  # 关闭广告
11. phone_control(action="ui_dump", keyword="搜索")    # 找到搜索框
12. phone_control(action="tap", x=搜索框坐标, y=搜索框y坐标)  # 点击搜索框
13. phone_control(action="input_text", text="北京大学第三医院")  # 输入目的地
14. phone_control(action="press_key", key="enter")     # 执行搜索
```

## 3. 避坑指南
- **等待加载**：微信应用启动和页面加载需要时间，操作后请等待 2-3 秒
- **登录状态**：确保微信已登录，否则无法进入滴滴出行
- **网络连接**：确保手机有网络连接，否则无法加载滴滴出行页面和搜索目的地
- **坐标系统**：tap 使用手机的物理像素坐标（即截图上的坐标）
- **连接断开**：长时间操作可能断开，定期 check_connection
- **滴滴出行入口**：如果在服务页面找不到滴滴出行，可以尝试向下滚动页面或在搜索框中搜索
- **广告处理**：滴滴出行页面可能会有广告弹出，需要及时关闭
- **目的地输入**：输入目的地时，确保输入准确的地址，以获得准确的路线和叫车结果