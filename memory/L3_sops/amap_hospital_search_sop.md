# 高德地图 - 医院搜索 SOP (Amap Hospital Search)

> **must call update working ckp**：`手机操控用phone_control工具｜操作前先check_connection｜每步操作后截图确认`

## 0. 前置条件
- Android 手机已通过 USB 连接电脑，或在同一 WiFi 下通过 `adb connect <ip>:5555` 连接
- 手机已开启 USB 调试（设置 → 开发者选项 → USB调试）
- 电脑已安装 adb：`brew install android-platform-tools`（macOS）
- 手机已安装高德地图应用

## 1. 搜索附近医院流程

### 关键避坑（本次实测验证）
- 若当前停在某家医院的“详情页/路线页”，**不要**直接在该页继续找附近医院；应先 `press_key(back)` 返回到**高德主界面**，再从顶部搜索框搜索“附近医院”，否则容易反复困在单家医院上下文。
- 进入搜索页后，若出现联想词/快捷词 **“附近医院”**，可直接点击该词进入结果页；不必强依赖 `input_text("附近医院") + enter`。
- 结果页常混有**口腔/眼科/妇产/门诊/校医院**等机构；给用户汇报时要明确类型，**不要把专科机构默认当综合医院推荐**。
- 每次关键点击（返回主界面、进入搜索页、进入结果页、进入目标医院详情）后，都应 `ui_dump` 或截图核验，避免页面未切换却继续误操作。

### Step 1: 检查连接
```
phone_control(action="check_connection")
```
确认手机已连接、型号、分辨率。

### Step 2: 启动高德地图
```
phone_control(action="launch_app", app="高德地图")
```
启动高德地图应用。

### Step 3: 查找搜索框
```
phone_control(action="ui_dump", keyword="搜索")
```
找到搜索框位置。

### Step 4: 点击搜索框
```
phone_control(action="tap", x=搜索框坐标, y=搜索框y坐标)
```
点击搜索框，激活输入。

### Step 5: 输入搜索内容
```
phone_control(action="input_text", text="附近医院")
```
输入"附近医院"作为搜索内容。

### Step 6: 执行搜索
```
phone_control(action="press_key", key="enter")
```
按回车键执行搜索。

### Step 7: 查看搜索结果
```
# 获取所有 UI 元素
nodes, summary = phone_control(action="ui_dump")

# 筛选真正的医院，排除分类标签
def is_hospital(text):
    """判断是否为真正的医院，排除分类标签"""
    # 检查是否为分类标签（完全匹配）
    category_tags = ["口腔医院", "综合医院", "专科医院", "中医院", "妇幼保健院", "儿童医院", "眼科医院", "耳鼻喉医院", "皮肤病医院", "精神卫生中心", "传染病医院", "肿瘤医院", "康复医院", "老年医院", "职业病医院", "口腔诊所", "医疗美容医院", "三甲医院"]
    # 完全匹配才认为是分类标签
    if text.strip() in category_tags:
        return False
    
    # 使用简单的规则判断
    # 检查是否包含距离信息
    if any(term in text for term in ["公里", "米"]):
        return True
    # 检查是否包含具体医院特征词
    hospital_keywords = ["市", "区", "大学", "医学院", "附属", "中心", "人民", "第一", "第二", "第三", "人民医院", "中医院", "妇幼保健院", "儿童医院"]
    if any(keyword in text for keyword in hospital_keywords):
        return True
    return False

hospital_nodes = []
for node in nodes:
    text = node.get("text", "").strip()
    # 筛选真正的医院
    if text and "医院" in text and is_hospital(text):
        hospital_nodes.append(node)

# 打印筛选结果
print(f"找到 {len(hospital_nodes)} 家医院")
for i, hospital in enumerate(hospital_nodes[:5]):  # 只显示前5个
    print(f"{i+1}. {hospital.get('text', '')}")
```
查看搜索结果，使用更全面的规则筛选出真正的医院，排除分类标签。

### Step 8: 选择医院
```
# 1. 获取所有医院元素
nodes, summary = phone_control(action="ui_dump")

# 2. 筛选医院元素并按距离排序
def is_hospital(text):
    """判断是否为真正的医院，排除分类标签"""
    # 检查是否为分类标签（完全匹配）
    category_tags = ["口腔医院", "综合医院", "专科医院", "中医院", "妇幼保健院", "儿童医院", "眼科医院", "耳鼻喉医院", "皮肤病医院", "精神卫生中心", "传染病医院", "肿瘤医院", "康复医院", "老年医院", "职业病医院", "口腔诊所", "医疗美容医院", "三甲医院"]
    # 完全匹配才认为是分类标签
    if text.strip() in category_tags:
        return False
    
    # 使用简单的规则判断
    # 检查是否包含距离信息
    if any(term in text for term in ["公里", "米"]):
        return True
    # 检查是否包含具体医院特征词
    hospital_keywords = ["市", "区", "大学", "医学院", "附属", "中心", "人民", "第一", "第二", "第三", "人民医院", "中医院", "妇幼保健院", "儿童医院"]
    if any(keyword in text for keyword in hospital_keywords):
        return True
    return False

hospital_elements = []
for node in nodes:
    text = node.get("text", "")
    # 筛选真正的医院且包含距离信息的元素
    if "医院" in text and ("米" in text or "公里" in text) and is_hospital(text):
        # 提取距离信息
        distance = float('inf')
        if "公里" in text:
            # 提取公里数
            match = re.search(r'([0-9.]+)公里', text)
            if match:
                distance = float(match.group(1)) * 1000  # 转换为米
        elif "米" in text:
            # 提取米数
            match = re.search(r'([0-9.]+)米', text)
            if match:
                distance = float(match.group(1))
        
        # 添加到医院列表
        hospital_elements.append((distance, node))

# 3. 按距离排序，选择最近的医院
if hospital_elements:
    hospital_elements.sort(key=lambda x: x[0])  # 按距离升序排序
    nearest_hospital = hospital_elements[0][1]  # 选择距离最近的医院
    # 点击选择该医院
    phone_control(action="tap", x=nearest_hospital["cx"], y=nearest_hospital["cy"])
else:
    # 如果没有找到带距离信息的医院，选择第一个真正的医院
    hospital_nodes = [node for node in nodes if "医院" in node.get("text", "") and is_hospital(node.get("text", ""))]
    if hospital_nodes:
        first_hospital = hospital_nodes[0]
        phone_control(action="tap", x=first_hospital["cx"], y=first_hospital["cy"])
    else:
        print("未找到医院")
```
当搜索到多家医院时，优先选择距离最近的医院。如果没有距离信息，则选择第一个真正的医院（排除分类标签）。

## 2. 规划路线流程

### Step 1: 查找路线按钮
```
phone_control(action="ui_dump", keyword="路线")
```
找到路线按钮位置。

### Step 2: 点击路线按钮
```
phone_control(action="tap", x=路线按钮坐标, y=路线按钮y坐标)
```
点击路线按钮，进入路线规划界面。

### Step 3: 选择出行方式
```
phone_control(action="ui_dump", keyword="驾车")
phone_control(action="tap", x=驾车按钮坐标, y=驾车按钮y坐标)
```
选择出行方式，如驾车、打车、公交地铁或步行。

### Step 4: 查看路线规划
```
phone_control(action="ui_dump")
```
查看路线规划结果。

## 3. 示例：搜索医院并规划路线

```
1. phone_control(action="check_connection")          # 确认连接
2. phone_control(action="launch_app", app="高德地图")  # 打开高德地图
3. phone_control(action="ui_dump", keyword="搜索")    # 找到搜索框
4. phone_control(action="tap", x=搜索框坐标, y=搜索框y坐标)  # 点击搜索框
5. phone_control(action="input_text", text="附近医院")  # 输入搜索内容
6. phone_control(action="press_key", key="enter")     # 执行搜索
7. # 查看搜索结果并筛选医院
   nodes, summary = phone_control(action="ui_dump")
   
   def is_hospital(text):
       """判断是否为真正的医院，排除分类标签"""
       # 检查是否为分类标签（完全匹配）
       category_tags = ["口腔医院", "综合医院", "专科医院", "中医院", "妇幼保健院", "儿童医院", "眼科医院", "耳鼻喉医院", "皮肤病医院", "精神卫生中心", "传染病医院", "肿瘤医院", "康复医院", "老年医院", "职业病医院", "口腔诊所", "医疗美容医院", "三甲医院"]
       # 完全匹配才认为是分类标签
       if text.strip() in category_tags:
           return False
       # 检查是否包含距离信息
       if any(term in text for term in ["公里", "米"]):
           return True
       # 检查是否包含具体医院特征词
       hospital_keywords = ["市", "区", "大学", "医学院", "附属", "中心", "人民", "第一", "第二", "第三", "人民医院", "中医院", "妇幼保健院", "儿童医院"]
       if any(keyword in text for keyword in hospital_keywords):
           return True
       return False
   
   hospital_nodes = []
   for node in nodes:
       text = node.get("text", "").strip()
       if text and "医院" in text and is_hospital(text):
           hospital_nodes.append(node)
   
   print(f"找到 {len(hospital_nodes)} 家医院")
   for i, hospital in enumerate(hospital_nodes[:5]):
       print(f"{i+1}. {hospital.get('text', '')}")
8. # 选择距离最近的医院
   import re
   nodes, summary = phone_control(action="ui_dump")
   
   def is_hospital(text):
       """判断是否为真正的医院，排除分类标签"""
       # 检查是否为分类标签（完全匹配）
       category_tags = ["口腔医院", "综合医院", "专科医院", "中医院", "妇幼保健院", "儿童医院", "眼科医院", "耳鼻喉医院", "皮肤病医院", "精神卫生中心", "传染病医院", "肿瘤医院", "康复医院", "老年医院", "职业病医院", "口腔诊所", "医疗美容医院", "三甲医院"]
       # 完全匹配才认为是分类标签
       if text.strip() in category_tags:
           return False
       # 检查是否包含距离信息
       if any(term in text for term in ["公里", "米"]):
           return True
       # 检查是否包含具体医院特征词
       hospital_keywords = ["市", "区", "大学", "医学院", "附属", "中心", "人民", "第一", "第二", "第三", "人民医院", "中医院", "妇幼保健院", "儿童医院"]
       if any(keyword in text for keyword in hospital_keywords):
           return True
       return False
   
   hospital_elements = []
   for node in nodes:
       text = node.get("text", "")
       if "医院" in text and ("米" in text or "公里" in text) and is_hospital(text):
           distance = float('inf')
           if "公里" in text:
               match = re.search(r'([0-9.]+)公里', text)
               if match:
                   distance = float(match.group(1)) * 1000
           elif "米" in text:
               match = re.search(r'([0-9.]+)米', text)
               if match:
                   distance = float(match.group(1))
           hospital_elements.append((distance, node))
   
   if hospital_elements:
       hospital_elements.sort(key=lambda x: x[0])
       nearest_hospital = hospital_elements[0][1]
       phone_control(action="tap", x=nearest_hospital["cx"], y=nearest_hospital["cy"])
   else:
       hospital_nodes = [node for node in nodes if "医院" in node.get("text", "") and is_hospital(node.get("text", ""))]
       if hospital_nodes:
           first_hospital = hospital_nodes[0]
           phone_control(action="tap", x=first_hospital["cx"], y=first_hospital["cy"])
       else:
           print("未找到医院")
9. phone_control(action="ui_dump", keyword="路线")    # 找到路线按钮
10. phone_control(action="tap", x=路线按钮坐标, y=路线按钮y坐标)  # 点击路线按钮
11. phone_control(action="ui_dump", keyword="驾车")   # 找到驾车按钮
12. phone_control(action="tap", x=驾车按钮坐标, y=驾车按钮y坐标)  # 选择驾车
13. phone_control(action="ui_dump")                    # 查看路线规划
```

## 4. 避坑指南
- **等待加载**：地图应用启动和搜索需要时间，操作后请等待 3-5 秒
- **定位权限**：确保高德地图已获得定位权限
- **网络连接**：确保手机有网络连接，否则搜索会失败
- **坐标系统**：tap 使用手机的物理像素坐标（即截图上的坐标）
- **连接断开**：长时间操作可能断开，定期 check_connection