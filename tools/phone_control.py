# tools/phone_control.py - Android 手机控制模块 (ADB)
# 跨平台：macOS / Linux / Windows 均可使用
# 依赖：adb (Android Debug Bridge)，可选 uiautomator2
import subprocess, shutil, os, re, time, base64, json
import xml.etree.ElementTree as ET

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SHARED_HOME = str(os.environ.get("HEALTHCLAW_SHARED_HOME", "") or "").strip()
_EXTRA_ADB_PATHS = [
    os.path.join(_SHARED_HOME, ".localdeps", "android", "platform-tools", "adb") if _SHARED_HOME else "",
    os.path.join(os.path.abspath(os.path.join(_ROOT_DIR, "..", "openclaw")), ".localdeps", "android", "platform-tools", "adb"),
    os.path.join(_ROOT_DIR, ".localdeps", "android", "platform-tools", "adb"),
    os.path.expanduser("~/Downloads/platform-tools/adb"),
    os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
    "/opt/homebrew/bin/adb",
    "/usr/local/bin/adb",
]
ADB = shutil.which("adb")
if not ADB:
    for p in _EXTRA_ADB_PATHS:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            ADB = p
            break
if not ADB:
    ADB = "adb"
_TEMP_DIR = os.path.join(_ROOT_DIR, "temp")
os.makedirs(_TEMP_DIR, exist_ok=True)

# 常用 App 包名（名称/别名 → 包名）
KNOWN_PACKAGES = {
    "美团": "com.sankuai.meituan",
    "美团外卖": "com.sankuai.meituan",
    "meituan": "com.sankuai.meituan",
    "饿了么": "me.ele",
    "eleme": "me.ele",
    "淘宝": "com.taobao.taobao",
    "taobao": "com.taobao.taobao",
    "支付宝": "com.eg.android.AlipayGphone",
    "alipay": "com.eg.android.AlipayGphone",
    "微信": "com.tencent.mm",
    "wechat": "com.tencent.mm",
    "keep": "com.gotokeep.keep",
    "华为健康": "com.huawei.health",
    "华为运动健康": "com.huawei.health",
    "小米运动健康": "com.mi.health",
    "小米健康": "com.mi.health",
    "小米穿戴": "com.xiaomi.wearable",
    "settings": "com.android.settings",
    "chrome": "com.android.chrome",
    "高德地图": "com.autonavi.minimap",
    "百度地图": "com.baidu.BaiduMap",
    "滴滴出行": "com.sdu.didi.psnger",
}

def _run_adb(*args, timeout=15):
    """执行 adb 命令，返回 (stdout, stderr, returncode)"""
    cmd = [ADB] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding='utf-8')
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "ADB command timed out", -1
    except FileNotFoundError:
        return "", "adb not found. Install: brew install android-platform-tools", -1
    except UnicodeDecodeError:
        # 如果utf-8解码失败，尝试使用gbk解码
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        try:
            stdout = r.stdout.decode('gbk').strip()
            stderr = r.stderr.decode('gbk').strip()
            return stdout, stderr, r.returncode
        except UnicodeDecodeError:
            # 如果gbk也解码失败，返回原始字节
            return "", "Encoding error", -1


def check_connection():
    """检查 ADB 连接状态，返回 (connected: bool, device_info: str)"""
    out, err, code = _run_adb("devices")
    if code != 0:
        return False, f"ADB error: {err}"
    lines = [l for l in out.split("\n") if l.strip() and "List of" not in l]
    devices = [l for l in lines if "device" in l and "offline" not in l and "unauthorized" not in l]
    if not devices:
        unauthorized = [l for l in lines if "unauthorized" in l]
        if unauthorized:
            return False, "手机已连接但未授权。请在手机上点击'允许USB调试'。"
        return False, "未检测到手机。请确认：\n1. USB线已连接\n2. 手机已开启USB调试(设置→开发者选项)\n3. 已安装adb: brew install android-platform-tools"
    device_id = devices[0].split("\t")[0]
    model, _, _ = _run_adb("shell", "getprop", "ro.product.model")
    brand, _, _ = _run_adb("shell", "getprop", "ro.product.brand")
    resolution, _, _ = _run_adb("shell", "wm", "size")
    return True, f"已连接: {brand} {model} ({device_id})\n分辨率: {resolution}"


def screenshot(save_path=None):
    """截取手机屏幕，返回 (base64_str, local_path)"""
    if save_path is None:
        save_path = os.path.join(_TEMP_DIR, "phone_screen.png")
    remote_path = "/sdcard/seda_screen.png"
    _run_adb("shell", "screencap", "-p", remote_path)
    out, err, code = _run_adb("pull", remote_path, save_path)
    _run_adb("shell", "rm", "-f", remote_path)
    if code != 0 or not os.path.exists(save_path):
        return None, f"截图失败: {err}"
    with open(save_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return b64, save_path


def tap(x, y):
    """点击屏幕坐标"""
    out, err, code = _run_adb("shell", "input", "tap", str(int(x)), str(int(y)))
    return code == 0, f"tap({x},{y})" if code == 0 else f"tap failed: {err}"


def swipe(x1, y1, x2, y2, duration_ms=300):
    """滑动手势"""
    out, err, code = _run_adb("shell", "input", "swipe",
                               str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(duration_ms))
    return code == 0, f"swipe({x1},{y1}→{x2},{y2})" if code == 0 else f"swipe failed: {err}"


def input_text(text):
    """输入文字（使用ADB键盘广播命令）"""
    try:
        # 使用ADB键盘广播命令输入文本
        out, err, code = _run_adb("shell", "am", "broadcast", "-a", "ADB_INPUT_TEXT", "--es", "msg", text)
        if code == 0:
            return True, f"input_text('{text}') via ADBKeyboard"
        else:
            # 如果ADB键盘失败，尝试使用input text命令
            safe = text.replace(" ", "%s").replace("&", "\\&").replace("|", "\\|")
            out, err, code = _run_adb("shell", "input", "text", safe)
            return code == 0, f"input_text('{text}') via input text" if code == 0 else f"input failed: {err}"
    except Exception as e:
        return False, f"input failed: {e}"


def press_key(key):
    """按键: back/home/recent/enter/delete/power/volume_up/volume_down"""
    keymap = {
        "back": "4", "home": "3", "recent": "187", "enter": "66",
        "delete": "67", "power": "26", "volume_up": "24", "volume_down": "25",
        "menu": "82", "tab": "61", "space": "62",
    }
    keycode = keymap.get(key.lower(), key)
    out, err, code = _run_adb("shell", "input", "keyevent", str(keycode))
    return code == 0, f"press_key({key})" if code == 0 else f"key failed: {err}"


def launch_app(name_or_package):
    """启动App（支持中文名/英文名/包名）。失败时仅返回本机已安装列表，由 Agent 根据用户描述自行匹配选包重试；若无相关包则由 Agent 停止任务并建议用户。"""
    package = KNOWN_PACKAGES.get(name_or_package, name_or_package)
    out, err, code = _run_adb("shell", "monkey", "-p", package, "-c",
                               "android.intent.category.LAUNCHER", "1")
    if code == 0 and "No activities found" not in err:
        return True, f"已启动: {package}"
    out2, err2, code2 = _run_adb("shell", "am", "start",
                                  "-n", f"{package}/.MainActivity")
    if code2 == 0:
        return True, f"已启动: {package}"
    all_pkgs = list_installed_apps(keyword=None)
    if isinstance(all_pkgs, str):
        return False, f"启动失败: {package}。获取本机应用列表失败: {all_pkgs}"
    user_said = name_or_package.strip()
    max_show = 80
    shown = all_pkgs[:max_show]
    parts = [
        f"启动失败: {package}。",
        "本机已安装应用（共{}个，以下前{}个）: ".format(len(all_pkgs), len(shown)) + ", ".join(shown),
    ]
    if len(all_pkgs) > max_show:
        parts.append("完整列表可用 list_apps() 查看。")
    parts.append("请根据用户描述「" + user_said + "」与上述列表**自行做关键词/语义匹配**，选出最可能的目标包名并用 launch_app(app=\"包名\") 重试；若列表中无相关包则停止任务并向用户说明或建议其说出具体应用名称。")
    return False, "\n".join(parts)


def get_current_app():
    """获取当前前台App信息"""
    out, _, _ = _run_adb("shell", "dumpsys", "window", "windows")
    for line in out.split("\n"):
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            m = re.search(r'([\w.]+)/([\w.]+)', line)
            if m:
                return {"package": m.group(1), "activity": m.group(2)}
    return {"package": "unknown", "activity": "unknown"}


def _dump_ui_u2():
    """用 uiautomator2 dump UI（不受 idle 限制，适合动画密集 App）"""
    try:
        import uiautomator2 as u2
        d = u2.connect()
        xml_str = d.dump_hierarchy()
        if xml_str and len(xml_str) > 100:
            return xml_str
    except Exception as e:
        print(f"[u2 fallback] {e}")
    return None


def _dump_ui_native():
    """原生 uiautomator dump"""
    _run_adb("shell", "rm", "-f", "/sdcard/ui.xml")
    out, err, code = _run_adb("shell", "uiautomator", "dump", "--compressed", "/sdcard/ui.xml")
    if "dumped" not in (out + err).lower():
        return None
    local_xml = os.path.join(_TEMP_DIR, "phone_ui.xml")
    _run_adb("pull", "/sdcard/ui.xml", local_xml)
    if not os.path.exists(local_xml):
        return None
    with open(local_xml, "r", encoding="utf-8") as f:
        return f.read()


def _parse_ui_xml(xml_str, keyword=None, clickable_only=False):
    """解析 UI XML 为结构化节点列表"""
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return []
    nodes = []
    for n in root.iter("node"):
        text = n.get("text", "")
        desc = n.get("content-desc", "")
        bounds = n.get("bounds", "")
        click = n.get("clickable") == "true"
        cls = n.get("class", "").split(".")[-1]
        rid = n.get("resource-id", "")
        # 不跳过没有label的元素，因为搜索栏可能没有文本标签
        if clickable_only and not click:
            continue
        if keyword:
            # 搜索关键词时，检查text、desc和rid
            if keyword.lower() not in (text.lower() or desc.lower() or rid.lower()):
                continue
        cx, cy = 0, 0
        if bounds:
            m = re.findall(r'\[(\d+),(\d+)\]', bounds)
            if len(m) == 2:
                cx = (int(m[0][0]) + int(m[1][0])) // 2
                cy = (int(m[0][1]) + int(m[1][1])) // 2
        nodes.append({
            "text": text, "description": desc, "clickable": click,
            "bounds": bounds, "cx": cx, "cy": cy,
            "class": cls, "id": rid
        })
    return nodes


def ui_dump(keyword=None, clickable_only=False):
    """获取手机当前界面的 UI 元素列表
    返回: (nodes_list, summary_text)
    """
    xml_str = _dump_ui_u2() or _dump_ui_native()
    if not xml_str:
        return [], "UI dump 失败（uiautomator2 和原生方式均失败）"
    nodes = _parse_ui_xml(xml_str, keyword, clickable_only)
    lines = []
    for n in nodes:
        flag = "✓" if n["clickable"] else " "
        coord = f"({n['cx']},{n['cy']})" if n['cx'] else ""
        # 处理没有text的元素
        text = n['text'] or n['description'] or n['id'] or n['class'] or "[无文本]"
        lines.append(f"[{flag}] {text}  {coord}  {n['bounds']}")
    summary = "\n".join(lines) + f"\n\n共 {len(nodes)} 个元素"
    if keyword:
        summary = f"(过滤: '{keyword}')\n" + summary
    return nodes, summary


def scroll_down():
    """向下滚动一屏"""
    res, _, _ = _run_adb("shell", "wm", "size")
    m = re.search(r'(\d+)x(\d+)', res)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        return swipe(w // 2, h * 3 // 4, w // 2, h // 4, 500)
    return swipe(540, 1600, 540, 400, 500)


def scroll_up():
    """向上滚动一屏"""
    res, _, _ = _run_adb("shell", "wm", "size")
    m = re.search(r'(\d+)x(\d+)', res)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        return swipe(w // 2, h // 4, w // 2, h * 3 // 4, 500)
    return swipe(540, 400, 540, 1600, 500)


def analyze_screen(llm_session, question="描述当前手机屏幕上的内容，列出可操作的按钮和文字"):
    """截图 + 调用 LLM 视觉分析手机屏幕
    llm_session: sidercall.LLMSession 实例
    返回: (analysis_text, screenshot_path)
    """
    b64, path = screenshot()
    if b64 is None:
        return f"截图失败: {path}", None
    prompt = (
        "你是一个手机屏幕分析助手。请仔细分析这张 Android 手机截图，回答以下问题：\n"
        f"{question}\n\n"
        "请列出：\n"
        "1. 当前是什么App/页面\n"
        "2. 屏幕上的主要文字内容\n"
        "3. 可以点击的按钮/链接及其大致坐标位置(上/中/下, 左/中/右)\n"
        "4. 建议的下一步操作"
    )
    try:
        analysis = llm_session.ask(prompt, image_base64=b64)
        return analysis, path
    except Exception as e:
        return f"视觉分析失败: {e}\n截图已保存到: {path}", path


def list_installed_apps(keyword=None):
    """列出手机上已安装的App"""
    out, err, code = _run_adb("shell", "pm", "list", "packages", "-3")
    if code != 0:
        return f"获取App列表失败: {err}"
    packages = [l.replace("package:", "").strip() for l in out.split("\n") if l.strip()]
    if keyword:
        packages = [p for p in packages if keyword.lower() in p.lower()]
    return packages


def set_clipboard(text):
    """设置设备剪贴板内容
    
    Args:
        text: 要设置的剪贴板内容
    """
    try:
        # 方法1: 使用ADB键盘广播命令 (推荐，因为用户已启用ADB键盘)
        print("尝试方法1: ADB键盘广播")
        out, err, code = _run_adb("shell", "am", "broadcast", "-a", "ADB_INPUT_TEXT", "--es", "msg", text)
        if code == 0:
            print("剪贴板已设置成功")
            return True, "剪贴板已设置成功"
        
        # 方法2: 使用content provider (适用于部分设备)
        print("尝试方法2: content provider")
        # 处理包含换行符和特殊字符的文本
        safe_text = text.replace("\n", "\\n").replace("'", "\\'").replace("(", "\\(").replace(")", "\\)")
        out, err, code = _run_adb("shell", "content", "insert", "--uri", "content://clipboard", "--bind", f"text:s:{safe_text}")
        if code == 0:
            print("剪贴板已设置成功")
            return True, "剪贴板已设置成功"
        
        # 方法3: 使用广播 (适用于部分设备)
        print("尝试方法3: broadcast")
        out, err, code = _run_adb("shell", "am", "broadcast", "-a", "android.intent.action.CLIPBOARD_CHANGED", "--es", "text", text)
        if code == 0:
            print("剪贴板已设置成功")
            return True, "剪贴板已设置成功"
        
        # 所有方法都失败
        print(f"设置剪贴板失败: {err}")
        return False, f"设置剪贴板失败: {err}"
    except Exception as e:
        print(f"设置剪贴板失败: {e}")
        return False, f"设置剪贴板失败: {e}"


def get_clipboard():
    """获取设备剪贴板内容
    
    Returns:
        剪贴板内容，如果获取失败则返回空字符串
    """
    try:
        # 使用content provider获取剪贴板
        out, err, code = _run_adb("shell", "content", "query", "--uri", "content://clipboard")
        if code == 0:
            # 解析输出
            if "text:" in out:
                # 提取文本内容
                text = out.split("text:")[1].strip()
                print(f"剪贴板内容: {text}")
                return text, None
            else:
                print("剪贴板为空")
                return "", "剪贴板为空"
        else:
            print(f"获取剪贴板失败: {err}")
            return "", f"获取剪贴板失败: {err}"
    except Exception as e:
        print(f"获取剪贴板失败: {e}")
        return "", f"获取剪贴板失败: {e}"


def get_location_coordinates():
    """通过adb shell dumpsys location命令获取设备的经纬度坐标
    
    Returns:
        (latitude, longitude) - 经纬度坐标，如果获取失败则返回(None, None)
    """
    try:
        # 执行dumpsys location命令
        out, err, code = _run_adb("shell", "dumpsys", "location")
        if code != 0:
            print(f"执行命令失败: {err}")
            return None, None
        
        # 解析输出，提取经纬度
        import re
        # 查找location信息，格式如：Location[network 31.2345,114.6789 ...]
        location_match = re.search(r'Location\[\w+\s+([\d\.\*]+),([\d\.\*]+)', out)
        if location_match:
            latitude = location_match.group(1)
            longitude = location_match.group(2)
            # 替换可能的星号（如果坐标被隐藏）
            latitude = latitude.replace('*', '')
            longitude = longitude.replace('*', '')
            
            # 转换为浮点数
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                print(f"获取到经纬度: {latitude}, {longitude}")
                return latitude, longitude
            except ValueError:
                print(f"经纬度格式错误: {latitude}, {longitude}")
                return None, None
        else:
            print("未找到位置信息")
            return None, None
    except Exception as e:
        print(f"获取位置坐标失败: {e}")
        return None, None


def press_home():
    """按Home键"""
    return press_key("home")


if __name__ == "__main__":
    ok, info = check_connection()
    print(f"Connected: {ok}\n{info}")
    if ok:
        nodes, summary = ui_dump()
        print(summary)
