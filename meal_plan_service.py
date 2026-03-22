"""
Meal planning and scheduled meal recommendation service.
"""
import copy
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timedelta

from tools import phone_control
from tools.health_data_store import HealthDataStore


DEFAULT_ADB_SERVER_SOCKET = "tcp:127.0.0.1:15037"
MEITUAN_MAIN_ACTIVITY = "com.sankuai.meituan/com.meituan.android.pt.homepage.activity.MainActivity"
MEITUAN_SEARCH_ACTIVITY = "com.sankuai.meituan/.search.home.SearchActivity"
MEITUAN_PACKAGE = "com.sankuai.meituan"
RESOLVER_ACTIVITY = "android/com.android.internal.app.MiuiResolverActivity"
UPGRADE_DIALOG_ACTIVITY = "com.meituan.android.upgrade.UpgradeDialogActivity"

LEFT_ORIGINAL_MEITUAN = (295, 1939)
UPGRADE_LATER_BUTTON = (342, 1440)
SEARCH_PAGE_FIELD = (434, 268)

SEARCH_UI_IGNORE = {
    "问小团",
    "全部",
    "外卖",
    "团购",
    "地点",
    "笔记",
    "快递",
    "点击筛选",
    "搜索结果",
    "综合排序",
    "地图搜索 按钮",
    "返回 按钮",
    "搜索",
    "清除历史记录",
}
RESULT_OCR_IGNORE = {
    "问小团",
    "全部",
    "外卖",
    "团购",
    "地点",
    "笔记",
    "快递",
    "直播中",
    "神荐",
    "品牌",
    "地图",
    "返回",
    "综合排序▼",
    "综合排序",
    "点击筛选神券搜索结果",
    "搜索结果",
    "外卖",
    "闪购",
    "24h营业",
    "买过1次",
    "最近3小时10人下单",
    "本地特色商家",
    "支持自取",
    "最近24小时16人下单",
    "虹口区面包蛋糕好评榜第4名",
    "点评推荐",
}
MERCHANT_OCR_IGNORE = {
    "首页",
    "全部商品",
    "会员",
    "推荐",
    "活动",
    "省心厨",
    "春日囤货季",
    "速食冻品",
    "新鲜蔬菜",
    "水果鲜花",
}

_OCR_ENGINE = None


def _ensure_adb_env():
    os.environ.setdefault("ADB_SERVER_SOCKET", DEFAULT_ADB_SERVER_SOCKET)


def _get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _OCR_ENGINE = RapidOCR()
    return _OCR_ENGINE


def _run_adb(*args, timeout=20):
    _ensure_adb_env()
    return phone_control._run_adb(*args, timeout=timeout)


def _current_activity():
    out, _, _ = _run_adb("shell", "dumpsys", "activity", "activities")
    for line in out.splitlines():
        if "mResumedActivity" not in line and "ResumedActivity" not in line:
            continue
        match = re.search(r"u0\s+([A-Za-z0-9._]+)/([A-Za-z0-9._$]+)", line)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return ""


def _wait_for_activity(target_keywords, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        activity = _current_activity()
        if activity and any(key in activity for key in target_keywords):
            return activity
        time.sleep(0.6)
    return _current_activity()


def _capture_screenshot(prefix):
    ts = int(time.time())
    path = os.path.join(os.path.dirname(__file__), "temp", f"{prefix}_{ts}.png")
    try:
        with open(path, "wb") as f:
            proc = phone_control.subprocess.run(
                [phone_control.ADB, "exec-out", "screencap", "-p"],
                capture_output=True,
                timeout=30,
            )
            if proc.returncode == 0 and proc.stdout:
                f.write(proc.stdout)
                return path
    except phone_control.subprocess.TimeoutExpired:
        pass

    remote_path = f"/sdcard/{prefix}_{ts}.png"
    _run_adb("shell", "screencap", "-p", remote_path, timeout=40)
    _run_adb("pull", remote_path, path, timeout=40)
    _run_adb("shell", "rm", "-f", remote_path, timeout=20)
    return path


def _ocr_boxes(image_path):
    engine = _get_ocr_engine()
    result, _ = engine(image_path)
    boxes = []
    for item in result or []:
        pts, text, score = item
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        boxes.append(
            {
                "text": str(text).strip(),
                "score": float(score),
                "left": min(xs),
                "top": min(ys),
                "right": max(xs),
                "bottom": max(ys),
                "cx": (min(xs) + max(xs)) / 2.0,
                "cy": (min(ys) + max(ys)) / 2.0,
            }
        )
    return boxes


def _tap(point):
    return phone_control.tap(point[0], point[1])


def _choose_original_meituan_if_needed():
    activity = _current_activity()
    if RESOLVER_ACTIVITY in activity:
        _tap(LEFT_ORIGINAL_MEITUAN)
        time.sleep(2.5)
    return _current_activity()


def _dismiss_upgrade_dialog_if_needed():
    activity = _current_activity()
    if UPGRADE_DIALOG_ACTIVITY in activity:
        _tap(UPGRADE_LATER_BUTTON)
        time.sleep(2.0)
    return _current_activity()


def _handle_known_overlays():
    activity = _current_activity()
    if RESOLVER_ACTIVITY in activity:
        activity = _choose_original_meituan_if_needed()
    if UPGRADE_DIALOG_ACTIVITY in activity:
        activity = _dismiss_upgrade_dialog_if_needed()
    return activity


def _phone_ready():
    _ensure_adb_env()
    ok, _info = phone_control.check_connection()
    return ok


def _open_search_page():
    _ensure_adb_env()
    phone_control.press_key("home")
    time.sleep(1)
    _run_adb("shell", "am", "start", "-W", "-n", MEITUAN_SEARCH_ACTIVITY, timeout=25)
    time.sleep(1.2)
    _handle_known_overlays()
    activity = _wait_for_activity([".search.home.SearchActivity", ".search.result.SearchResultActivity"], timeout=20)
    if UPGRADE_DIALOG_ACTIVITY in activity:
        _dismiss_upgrade_dialog_if_needed()
        activity = _wait_for_activity([".search.home.SearchActivity", ".search.result.SearchResultActivity"], timeout=10)
    return {
        "status": "ok" if (
            ".search.home.SearchActivity" in activity or ".search.result.SearchResultActivity" in activity
        ) else "error",
        "activity": activity,
    }


def _strip_search_suffix(text):
    text = re.sub(r"点击\s*可?\s*发起搜索$", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_price(text):
    match = re.search(r"[¥￥]\s*([0-9]+(?:\.[0-9]+)?)", text)
    if match:
        return match.group(1)
    return ""


def _price_to_float(text):
    value = _normalize_price(text)
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _query_terms(query):
    known_terms = ["轻食", "沙拉", "鸡胸", "鸡胸肉", "豆浆", "三明治", "便当", "减脂", "低脂", "全麦"]
    return [term for term in known_terms if term in query]


def _is_real_suggestion(text, query):
    clean = _strip_search_suffix(text)
    if not clean or clean in SEARCH_UI_IGNORE:
        return False
    if clean.endswith("按钮") or clean.startswith("复旦大学("):
        return False
    if any(token in clean for token in ["好评榜", "热销榜", "门店销量", "新客", "配送", "下单", "评分", "接受预订", "明天", "清除历史记录"]):
        return False
    if query and not any(ch in clean for ch in query if ch.strip()):
        return False
    return len(clean) >= 2


def _extract_suggestions(nodes, query, limit=6):
    results = []
    seen = set()
    for node in nodes:
        if node.get("cy", 0) < 360:
            continue
        text = _strip_search_suffix(node.get("text", ""))
        if not _is_real_suggestion(text, query) or text in seen:
            continue
        seen.add(text)
        results.append(
            {
                "store_name": "美团搜索联想",
                "item_name": text,
                "price": "",
                "delivery": "",
                "distance": "",
                "match_reason": f"来自手机美团实时搜索联想：{query}",
                "source": "meituan_phone_suggestion",
                "tap_point": (int(node.get("cx", 0)), int(node.get("cy", 0))),
            }
        )
        if len(results) >= limit:
            break
    return results


def _score_suggestion(candidate, query):
    text = candidate.get("item_name", "")
    score = 0
    for term in _query_terms(query):
        if term in text:
            score += 4
    if text == query:
        score += 1
    if any(term in text for term in ["轻食", "沙拉", "减脂", "全麦", "糙米", "豆浆", "三明治", "便当"]):
        score += 3
    score += min(len(text), 16) / 10.0
    return score


def _is_safe_item_to_add(item_name, store_name, query, item_price):
    aggregate = f"{item_name} {store_name} {query}"
    query_terms = _query_terms(query)
    if query_terms and not any(term in aggregate for term in query_terms):
        return False
    price_value = _price_to_float(item_price)
    if price_value and price_value > 50:
        return False
    return True


def _is_result_store_box(box):
    text = box["text"]
    if not text or text in RESULT_OCR_IGNORE:
        return False
    if box["top"] < 500 or box["top"] > 1700:
        return False
    if any(key in text for key in ["月售", "分钟", "km", "点评", "起送", "配送", "营业", "红包", "领券", "图片热量", "收藏", "价格", "￥", "¥", "休息"]):
        return False
    if len(text) < 4 or text.startswith("复旦大学"):
        return False
    return True


def _extract_result_cards(ocr_boxes, limit=3):
    store_boxes = []
    for box in ocr_boxes:
        if not _is_result_store_box(box):
            continue
        text = box["text"]
        looks_like_store = any(token in text for token in ["轻食", "便利店", "面包", "沙拉", "健康餐", "便当", "超市"]) or any(
            mark in text for mark in ["(店", "（", "(世界路店", "(赤峰路店", "(中原店", "店)", "店）"]
        ) or text.endswith("店")
        if not looks_like_store:
            continue
        if any(token in text for token in ["镇店之宝", "神券价", "招牌", "鸡胸肉", "牛乳", "绿豆饼"]):
            continue
        if any(card["store_name"] == text for card in store_boxes):
            continue
        store_boxes.append({"store_name": text, "bbox": box})

    cards = []
    sorted_stores = sorted(store_boxes, key=lambda item: item["bbox"]["top"])
    for idx, store in enumerate(sorted_stores):
        box = store["bbox"]
        next_top = sorted_stores[idx + 1]["bbox"]["top"] if idx + 1 < len(sorted_stores) else 2400
        related = [b for b in ocr_boxes if box["top"] <= b["top"] < next_top]
        eta = ""
        distance = ""
        for rel in related:
            rtext = rel["text"]
            if not eta and "分钟" in rtext:
                eta = rtext
            if not distance and re.search(r"\d+(\.\d+)?km", rtext):
                distance = rtext
        preview_text = " ".join(b["text"] for b in related[:20])
        cards.append(
            {
                "store_name": store["store_name"],
                "delivery": eta,
                "distance": distance,
                "tap_point": (int(box["cx"]), int(min(box["bottom"] + 120, next_top - 60))),
                "bbox": box,
                "block_text": preview_text,
            }
        )
        if len(cards) >= limit:
            break
    return cards


def _score_result_card(card, query):
    aggregate = f"{card.get('store_name', '')} {card.get('block_text', '')}"
    score = 0
    for term in _query_terms(query):
        if term in card.get("store_name", ""):
            score += 5
        if term in aggregate:
            score += 2
    if "轻食" in aggregate or "沙拉" in aggregate:
        score += 2
    if "便利店" in card.get("store_name", ""):
        score -= 2
    return score


def _extract_addable_items(ocr_boxes, limit=3):
    plus_boxes = [b for b in ocr_boxes if b["text"] == "+" and b["top"] > 1000]
    spec_boxes = [b for b in ocr_boxes if "选规格" in b["text"] and b["top"] > 1800]
    items = []
    action_boxes = [("add", box) for box in plus_boxes] + [("select_spec", box) for box in spec_boxes]
    for action_type, plus in action_boxes:
        price_boxes = [
            b for b in ocr_boxes
            if b["left"] < plus["left"]
            and abs(b["cy"] - plus["cy"]) < 120
            and _normalize_price(b["text"])
        ]
        if not price_boxes:
            continue
        price_box = sorted(price_boxes, key=lambda b: abs(b["cy"] - plus["cy"]))[0]
        title_boxes = [
            b for b in ocr_boxes
            if b["left"] > 240
            and b["right"] < plus["left"] + 20
            and b["top"] >= plus["top"] - 260
            and b["bottom"] <= price_box["top"] + 5
            and b["text"] not in MERCHANT_OCR_IGNORE
            and len(b["text"]) >= 2
        ]
        title_boxes.sort(key=lambda b: (b["top"], b["left"]))
        title_parts = []
        for box in title_boxes:
            text = box["text"]
            if text in title_parts:
                continue
            if any(token in text for token in ["保质期", "月售", "活动", "新人专享", "配送费", "起送"]):
                continue
            title_parts.append(text)
        if not title_parts:
            continue
        title = "".join(title_parts[:3])
        items.append(
            {
                "item_name": title,
                "price": _normalize_price(price_box["text"]),
                "add_button": (int(plus["cx"]), int(plus["cy"])),
                "price_box": price_box,
                "action_type": action_type,
            }
        )
        if len(items) >= limit:
            break
    return items


def _extract_cart_summary(ocr_boxes):
    total_price = ""
    cart_cta = ""
    shortage = ""
    shipping = ""
    for box in ocr_boxes:
        text = box["text"]
        if box["top"] < 2050:
            continue
        if not total_price and _normalize_price(text):
            total_price = _normalize_price(text)
        if not cart_cta and text in {"去凑单", "去结算"}:
            cart_cta = text
        if not shortage and "起送" in text and "差" in text:
            shortage = text
        if not shipping and "配送费" in text:
            shipping = text
    return {
        "total_price": total_price,
        "cart_cta": cart_cta,
        "shortage": shortage,
        "shipping_text": shipping,
    }


def _best_effort_submit_search():
    _run_adb("shell", "am", "broadcast", "-a", "ADB_EDITOR_CODE", "--ei", "code", "3", timeout=15)
    time.sleep(2.5)
    activity = _current_activity()
    if ".search.result.SearchResultActivity" not in activity:
        phone_control.press_key("enter")
        time.sleep(2.5)
        activity = _current_activity()
    return activity


def search_food_suggestions(query, limit=5):
    _ensure_adb_env()
    if not _phone_ready():
        return {"status": "error", "msg": "phone_not_ready", "candidates": []}

    search = _open_search_page()
    if search["status"] != "ok":
        return {"status": "error", "msg": f"search_page_unavailable: {search.get('activity', '')}", "candidates": []}

    _tap(SEARCH_PAGE_FIELD)
    time.sleep(0.6)
    _run_adb("shell", "am", "broadcast", "-a", "ADB_CLEAR_TEXT", timeout=10)
    phone_control.input_text(query)
    time.sleep(1.0)
    nodes, _summary = phone_control.ui_dump(clickable_only=False)
    suggestions = _extract_suggestions(nodes, query, limit=limit)

    base = {
        "status": "success" if suggestions else "partial",
        "query": query,
        "candidates": suggestions,
        "source": "meituan_phone_live_search",
        "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    result_activity = _best_effort_submit_search()
    screenshot_path = _capture_screenshot("meituan_search_result")
    return {**base, "result_activity": result_activity, "screenshot_path": screenshot_path}


def search_and_add_best_item(query, limit=5):
    base = search_food_suggestions(query, limit=limit)
    if base.get("status") == "error":
        return base

    suggestions = base.get("candidates", [])
    if suggestions:
        best_suggestion = sorted(suggestions, key=lambda item: _score_suggestion(item, query), reverse=True)[0]
        if best_suggestion.get("tap_point") != (0, 0):
            _tap(best_suggestion["tap_point"])
            time.sleep(3)
            if ".search.result.SearchResultActivity" not in _current_activity():
                _best_effort_submit_search()

    result_activity = _current_activity()
    if ".search.result.SearchResultActivity" not in result_activity:
        result_activity = _best_effort_submit_search()
    result_screenshot = _capture_screenshot("meituan_search_result")
    result_boxes = _ocr_boxes(result_screenshot) if result_screenshot and os.path.exists(result_screenshot) else []
    result_cards = _extract_result_cards(result_boxes, limit=limit)
    cart_action = {}

    if result_cards:
        ranked_cards = sorted(result_cards, key=lambda card: _score_result_card(card, query), reverse=True)
        first_card = ranked_cards[0]
        _tap(first_card["tap_point"])
        time.sleep(4)
        merchant_screenshot = _capture_screenshot("meituan_merchant_page")
        merchant_boxes = _ocr_boxes(merchant_screenshot)
        addable_items = _extract_addable_items(merchant_boxes, limit=3)
        if addable_items:
            selected = addable_items[0]
            if selected.get("action_type") == "select_spec":
                cart_action = {
                    "status": "needs_spec_selection",
                    "store_name": first_card["store_name"],
                    "item_name": selected["item_name"],
                    "item_price": selected["price"],
                    "merchant_screenshot": merchant_screenshot,
                }
            elif _is_safe_item_to_add(selected["item_name"], first_card["store_name"], query, selected["price"]):
                _tap(selected["add_button"])
                time.sleep(3)
                cart_screenshot = _capture_screenshot("meituan_cart_state")
                cart_boxes = _ocr_boxes(cart_screenshot)
                cart_summary = _extract_cart_summary(cart_boxes)
                cart_action = {
                    "status": "added",
                    "store_name": first_card["store_name"],
                    "item_name": selected["item_name"],
                    "item_price": selected["price"],
                    "merchant_screenshot": merchant_screenshot,
                    "cart_screenshot": cart_screenshot,
                    "cart_summary": cart_summary,
                }
            else:
                cart_action = {
                    "status": "skipped_safety_check",
                    "store_name": first_card["store_name"],
                    "item_name": selected["item_name"],
                    "item_price": selected["price"],
                    "merchant_screenshot": merchant_screenshot,
                }
        else:
            cart_action = {
                "status": "no_addable_item_found",
                "store_name": first_card["store_name"],
                "merchant_screenshot": merchant_screenshot,
            }
    else:
        ranked_cards = []
        cart_action = {"status": "no_result_card_found"}

    return {
        **base,
        "result_cards": ranked_cards if result_cards else [],
        "result_activity": result_activity,
        "screenshot_path": result_screenshot,
        "cart_action": cart_action,
    }


DEFAULT_MEAL_SCHEDULE = {
    "breakfast": {"meal_time": "08:00", "push_lead_minutes": 60, "label": "早餐"},
    "lunch": {"meal_time": "12:00", "push_lead_minutes": 60, "label": "午餐"},
    "dinner": {"meal_time": "18:00", "push_lead_minutes": 60, "label": "晚餐"},
}


GOAL_CONFIGS = {
    "weight_loss": {
        "label": "减脂",
        "daily_calories": 1450,
        "meal_targets": {"breakfast": (300, 380), "lunch": (450, 580), "dinner": (400, 520)},
        "focus_tags": ["high_protein", "vegetable_rich", "light", "low_sugar"],
        "avoid_tags": ["fried", "sugary", "heavy_sauce"],
        "summary": "控制总热量、优先高蛋白和高蔬菜比例，帮助稳定减脂。",
    },
    "glucose_control": {
        "label": "控糖",
        "daily_calories": 1550,
        "meal_targets": {"breakfast": (320, 400), "lunch": (480, 600), "dinner": (420, 520)},
        "focus_tags": ["low_sugar", "whole_grain", "high_fiber", "high_protein"],
        "avoid_tags": ["sugary", "refined_carb", "sweet_drink"],
        "summary": "优先低糖、粗粮和纤维，减少餐后血糖波动。",
    },
    "heart_healthy": {
        "label": "心血管友好",
        "daily_calories": 1550,
        "meal_targets": {"breakfast": (320, 400), "lunch": (470, 600), "dinner": (420, 520)},
        "focus_tags": ["low_sodium", "high_protein", "vegetable_rich", "soup"],
        "avoid_tags": ["fried", "high_sodium", "processed_meat"],
        "summary": "关注低盐、低油和稳定能量摄入，适合血压或心血管风险管理。",
    },
    "balanced": {
        "label": "均衡饮食",
        "daily_calories": 1650,
        "meal_targets": {"breakfast": (320, 420), "lunch": (500, 650), "dinner": (450, 580)},
        "focus_tags": ["balanced", "high_protein", "vegetable_rich"],
        "avoid_tags": ["fried", "heavy_sauce"],
        "summary": "以均衡、可长期坚持为主，兼顾蛋白质、蔬菜和主食结构。",
    },
}


DAY_THEME_ROTATION = [
    {"name": "高蛋白轻负担日", "extra_tags": ["high_protein", "light"], "note": "优先鸡胸肉、鱼虾、豆制品和蔬菜。"},
    {"name": "低糖稳能量日", "extra_tags": ["low_sugar", "whole_grain"], "note": "主食以全麦和粗粮为主，减少精制碳水。"},
    {"name": "高纤维蔬菜日", "extra_tags": ["high_fiber", "vegetable_rich"], "note": "增加深色蔬菜和豆类摄入。"},
    {"name": "低盐清爽日", "extra_tags": ["low_sodium", "soup"], "note": "适合控制钠摄入，避免重口味。"},
    {"name": "鱼类优先日", "extra_tags": ["seafood", "light"], "note": "用鱼虾类替代部分红肉，减轻油腻负担。"},
    {"name": "温和恢复日", "extra_tags": ["comfort", "soup"], "note": "适合忙碌后恢复，选择更好消化的组合。"},
    {"name": "规律收口日", "extra_tags": ["balanced", "vegetable_rich"], "note": "三餐保持规律，避免临睡前过量进食。"},
]


MEAL_CANDIDATE_CATALOG = [
    {
        "store_name": "轻食先生·美团优选",
        "item_name": "香煎鸡胸藜麦能量碗",
        "meal_types": ["lunch", "dinner"],
        "tags": ["high_protein", "vegetable_rich", "light", "low_sugar", "balanced"],
        "calories": 480,
        "protein_g": 35,
        "price": 32,
    },
    {
        "store_name": "谷物日记",
        "item_name": "全麦鸡蛋牛油果三明治",
        "meal_types": ["breakfast", "lunch"],
        "tags": ["whole_grain", "high_protein", "light", "balanced"],
        "calories": 360,
        "protein_g": 22,
        "price": 24,
    },
    {
        "store_name": "暖胃粥铺",
        "item_name": "杂粮鸡丝粥配水煮蛋",
        "meal_types": ["breakfast", "dinner"],
        "tags": ["comfort", "whole_grain", "light", "soup"],
        "calories": 320,
        "protein_g": 18,
        "price": 18,
    },
    {
        "store_name": "轻食先生·美团优选",
        "item_name": "三文鱼羽衣甘蓝沙拉",
        "meal_types": ["lunch", "dinner"],
        "tags": ["seafood", "high_protein", "light", "low_sugar", "vegetable_rich"],
        "calories": 430,
        "protein_g": 30,
        "price": 38,
    },
    {
        "store_name": "控糖便当实验室",
        "item_name": "糙米鸡腿蔬菜便当",
        "meal_types": ["lunch", "dinner"],
        "tags": ["whole_grain", "high_protein", "low_sugar", "vegetable_rich"],
        "calories": 520,
        "protein_g": 32,
        "price": 29,
    },
    {
        "store_name": "轻煮汤饭",
        "item_name": "番茄牛肉豆腐汤饭",
        "meal_types": ["lunch", "dinner"],
        "tags": ["soup", "high_protein", "comfort", "balanced"],
        "calories": 510,
        "protein_g": 28,
        "price": 27,
    },
    {
        "store_name": "校园清食堂",
        "item_name": "蒸鱼时蔬双拼套餐",
        "meal_types": ["lunch", "dinner"],
        "tags": ["seafood", "low_sodium", "vegetable_rich", "light"],
        "calories": 470,
        "protein_g": 31,
        "price": 33,
    },
    {
        "store_name": "蛋白研究所",
        "item_name": "嫩煎牛肉西兰花便当",
        "meal_types": ["lunch", "dinner"],
        "tags": ["high_protein", "vegetable_rich", "balanced"],
        "calories": 560,
        "protein_g": 36,
        "price": 34,
    },
    {
        "store_name": "清晨烘焙",
        "item_name": "无糖酸奶水果坚果杯",
        "meal_types": ["breakfast"],
        "tags": ["light", "low_sugar", "high_protein"],
        "calories": 280,
        "protein_g": 17,
        "price": 19,
    },
    {
        "store_name": "豆乳工坊",
        "item_name": "无糖豆浆配全麦鸡蛋卷",
        "meal_types": ["breakfast"],
        "tags": ["whole_grain", "light", "high_protein", "balanced"],
        "calories": 330,
        "protein_g": 19,
        "price": 16,
    },
    {
        "store_name": "元气沙拉站",
        "item_name": "虾仁鸡蛋蔬菜沙拉",
        "meal_types": ["lunch", "dinner"],
        "tags": ["seafood", "high_protein", "low_sugar", "vegetable_rich", "light"],
        "calories": 390,
        "protein_g": 29,
        "price": 31,
    },
    {
        "store_name": "暖胃粥铺",
        "item_name": "山药小米南瓜粥套餐",
        "meal_types": ["breakfast", "dinner"],
        "tags": ["comfort", "soup", "light", "balanced"],
        "calories": 300,
        "protein_g": 11,
        "price": 17,
    },
    {
        "store_name": "清蒸小馆",
        "item_name": "清蒸鸡胸时蔬套餐",
        "meal_types": ["lunch", "dinner"],
        "tags": ["high_protein", "low_sodium", "vegetable_rich", "light"],
        "calories": 450,
        "protein_g": 34,
        "price": 28,
    },
    {
        "store_name": "谷物日记",
        "item_name": "燕麦香蕉花生酱能量杯",
        "meal_types": ["breakfast"],
        "tags": ["whole_grain", "balanced", "high_fiber"],
        "calories": 340,
        "protein_g": 14,
        "price": 18,
    },
    {
        "store_name": "校园清食堂",
        "item_name": "番茄豆腐菌菇炖菜套餐",
        "meal_types": ["lunch", "dinner"],
        "tags": ["vegetarian", "high_fiber", "low_sodium", "comfort"],
        "calories": 430,
        "protein_g": 20,
        "price": 24,
    },
    {
        "store_name": "蛋白研究所",
        "item_name": "照烧鸡腿糙米饭",
        "meal_types": ["lunch", "dinner"],
        "tags": ["high_protein", "whole_grain", "balanced"],
        "calories": 590,
        "protein_g": 33,
        "price": 30,
    },
    {
        "store_name": "轻煮汤饭",
        "item_name": "鸡丝菌菇荞麦面",
        "meal_types": ["lunch", "dinner"],
        "tags": ["whole_grain", "high_protein", "comfort", "light"],
        "calories": 500,
        "protein_g": 27,
        "price": 26,
    },
    {
        "store_name": "清晨烘焙",
        "item_name": "金枪鱼全麦卷",
        "meal_types": ["breakfast", "lunch"],
        "tags": ["seafood", "whole_grain", "high_protein", "light"],
        "calories": 350,
        "protein_g": 24,
        "price": 22,
    },
]


CREATE_PLAN_PATTERNS = [
    r"减肥",
    r"瘦身",
    r"饮食计划",
    r"用餐计划",
    r"未来一个月.*(吃|饮食|用餐)",
    r"月.*饮食",
]
PAUSE_PLAN_PATTERNS = [r"暂停.*饮食计划", r"停止.*饮食计划", r"取消.*饮食计划"]
STATUS_PLAN_PATTERNS = [r"查看.*饮食计划", r"我的.*饮食计划", r"今天.*吃什么", r"餐食计划"]


def detect_meal_plan_action(text):
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    for pat in PAUSE_PLAN_PATTERNS:
        if re.search(pat, normalized):
            return "pause"
    for pat in STATUS_PLAN_PATTERNS:
        if re.search(pat, normalized):
            return "status"
    for pat in CREATE_PLAN_PATTERNS:
        if re.search(pat, normalized):
            return "create"
    return ""


def _default_recommendation_source():
    if os.environ.get("HEALTHCLAW_ENABLE_PHONE_MEITUAN", "0") == "1":
        return "meituan_phone_live_search"
    return "meituan_demo_catalog"


def _recommendation_source_note(source):
    if source == "meituan_phone_live_search":
        return "当前默认优先使用真实手机美团搜索链路；若手机链路暂时不可用，系统才会回退到本地候选数据。"
    if source == "meituan_demo_catalog":
        return "当前默认使用本地候选演示数据；接通手机链路后，可自动切换为真实美团搜索。"
    if source == "meituan_phone_suggestion":
        return "当前推荐来自真实手机美团搜索联想结果。"
    return f"当前推荐来源: {source}"


def _recommendation_source_label(source):
    if source == "meituan_phone_live_search":
        return "真实手机美团搜索优先"
    if source == "meituan_demo_catalog":
        return "本地候选演示数据"
    if source == "meituan_phone_suggestion":
        return "真实手机美团搜索联想"
    return source or "unknown"


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_indicator_value(indicators, key):
    if key not in indicators:
        return None
    item = indicators.get(key)
    if isinstance(item, dict):
        return item.get("value")
    return item


def _parse_clock(text, default_clock):
    text = text.strip()
    if not text:
        return default_clock
    if ":" in text:
        parts = text.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            return f"{hour:02d}:{minute:02d}"
        except (ValueError, IndexError):
            return default_clock
    match = re.match(r"(\d{1,2})点(?:(\d{1,2})分?)?(半)?", text)
    if not match:
        return default_clock
    hour = int(match.group(1))
    minute = 30 if match.group(3) else int(match.group(2) or 0)
    return f"{hour:02d}:{minute:02d}"


def _extract_meal_time(text, meal_keywords, default_clock):
    patterns = [
        rf"(?:{'|'.join(meal_keywords)})[^\d]{{0,6}}(\d{{1,2}}(?::\d{{1,2}})?点?(?:\d{{1,2}}分?)?(?:半)?)",
        rf"(\d{{1,2}}(?::\d{{1,2}})?点?(?:\d{{1,2}}分?)?(?:半)?)[^\n，。]*?(?:{'|'.join(meal_keywords)})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return _parse_clock(match.group(1), default_clock)
    return default_clock


def _compute_push_time(meal_time, lead_minutes):
    base = datetime.strptime(meal_time, "%H:%M")
    push_dt = base - timedelta(minutes=int(lead_minutes))
    return push_dt.strftime("%H:%M")


def _generate_plan_id(open_id):
    return f"meal_{open_id}_{int(time.time())}"


class MealPlanService:
    def __init__(self, store=None):
        self.store = store or HealthDataStore()

    def parse_request(self, text):
        lowered = str(text or "").lower()
        goal = "balanced"
        if any(word in lowered for word in ["减肥", "瘦身", "减脂", "控制体重"]):
            goal = "weight_loss"
        elif any(word in lowered for word in ["控糖", "血糖", "糖尿病", "少糖"]):
            goal = "glucose_control"
        elif any(word in lowered for word in ["血压", "低盐", "心脏", "心血管"]):
            goal = "heart_healthy"

        meal_schedule = copy.deepcopy(DEFAULT_MEAL_SCHEDULE)
        meal_schedule["breakfast"]["meal_time"] = _extract_meal_time(
            text, ["早餐", "早饭", "早上"], meal_schedule["breakfast"]["meal_time"]
        )
        meal_schedule["lunch"]["meal_time"] = _extract_meal_time(
            text, ["午餐", "中饭", "午饭", "中午"], meal_schedule["lunch"]["meal_time"]
        )
        meal_schedule["dinner"]["meal_time"] = _extract_meal_time(
            text, ["晚餐", "晚饭", "晚上的饭", "晚上"], meal_schedule["dinner"]["meal_time"]
        )
        for meal_key, schedule in meal_schedule.items():
            schedule["push_time"] = _compute_push_time(schedule["meal_time"], schedule["push_lead_minutes"])

        return {
            "goal": goal,
            "duration_days": 30,
            "meal_schedule": meal_schedule,
            "request_text": text.strip(),
        }

    def _derive_constraints(self, profile, indicators, text):
        constraints = {
            "focus_tags": [],
            "avoid_tags": [],
            "allergies": list(profile.get("allergies", []) or []),
            "chronic_diseases": list(profile.get("chronic_diseases", []) or []),
            "notes": [],
        }

        if constraints["allergies"]:
            constraints["notes"].append("已避开用户已知过敏原。")

        fasting_glucose = _safe_float(_normalize_indicator_value(indicators, "fasting_blood_glucose"), 0.0)
        hba1c = _safe_float(_normalize_indicator_value(indicators, "HbA1c"), 0.0)
        systolic = _safe_float(_normalize_indicator_value(indicators, "systolic_bp"), 0.0)
        diastolic = _safe_float(_normalize_indicator_value(indicators, "diastolic_bp"), 0.0)

        chronic_text = " ".join(str(x) for x in constraints["chronic_diseases"]).lower()
        if fasting_glucose >= 6.1 or hba1c >= 5.7 or any(word in chronic_text for word in ["糖尿", "diabetes"]):
            constraints["focus_tags"].extend(["low_sugar", "whole_grain"])
            constraints["avoid_tags"].extend(["sugary", "sweet_drink", "refined_carb"])
            constraints["notes"].append("结合血糖/糖代谢风险，额外强调低糖和粗粮结构。")

        if systolic >= 140 or diastolic >= 90 or any(word in chronic_text for word in ["高血压", "hypertension"]):
            constraints["focus_tags"].append("low_sodium")
            constraints["avoid_tags"].extend(["high_sodium", "heavy_sauce", "processed_meat"])
            constraints["notes"].append("结合血压风险，额外强调低盐和少加工。")

        lowered = text.lower()
        if "不吃辣" in text or "少辣" in text:
            constraints["avoid_tags"].append("spicy")
        if "素食" in text:
            constraints["focus_tags"].append("vegetarian")
        if "海鲜过敏" in text:
            constraints["avoid_tags"].append("seafood")

        constraints["focus_tags"] = sorted(set(constraints["focus_tags"]))
        constraints["avoid_tags"] = sorted(set(constraints["avoid_tags"]))
        return constraints

    def _pick_goal_config(self, parsed_request, constraints):
        goal = parsed_request["goal"]
        if goal == "balanced" and "low_sugar" in constraints["focus_tags"]:
            goal = "glucose_control"
        if goal == "balanced" and "low_sodium" in constraints["focus_tags"]:
            goal = "heart_healthy"
        return GOAL_CONFIGS[goal], goal

    def _build_day_plan(self, day_index, plan_date, goal_config, constraints):
        theme = DAY_THEME_ROTATION[day_index % len(DAY_THEME_ROTATION)]
        meals = {}
        for meal_key, label in [("breakfast", "早餐"), ("lunch", "午餐"), ("dinner", "晚餐")]:
            calorie_min, calorie_max = goal_config["meal_targets"][meal_key]
            preferred_tags = list(goal_config["focus_tags"]) + list(theme["extra_tags"])
            if meal_key == "breakfast":
                preferred_tags.extend(["breakfast", "light"])
            elif meal_key == "lunch":
                preferred_tags.extend(["lunch", "high_protein", "vegetable_rich"])
            else:
                preferred_tags.extend(["dinner", "light", "comfort"])

            for tag in constraints["focus_tags"]:
                if tag not in preferred_tags:
                    preferred_tags.append(tag)

            avoid_tags = list(goal_config["avoid_tags"]) + list(constraints["avoid_tags"])

            query = f"美团 {goal_config['label']} {label} 高蛋白 清淡"
            if "low_sugar" in preferred_tags:
                query += " 低糖"
            if "whole_grain" in preferred_tags:
                query += " 粗粮"
            phone_query = self._build_phone_search_query(goal_config["label"], meal_key, preferred_tags)
            meals[meal_key] = {
                "meal_label": label,
                "target_calories": [calorie_min, calorie_max],
                "preferred_tags": sorted(set(preferred_tags)),
                "avoid_tags": sorted(set(avoid_tags)),
                "query": query.strip(),
                "phone_query": phone_query,
                "goal_note": theme["note"],
            }
        return {
            "date": plan_date.strftime("%Y-%m-%d"),
            "theme": theme["name"],
            "meals": meals,
        }

    def _build_phone_search_query(self, goal_label, meal_key, preferred_tags):
        if meal_key == "breakfast":
            if "low_sugar" in preferred_tags:
                return "无糖豆浆 全麦三明治 早餐"
            return "高蛋白轻食早餐"
        if meal_key == "lunch":
            if "whole_grain" in preferred_tags:
                return "鸡胸肉蔬菜沙拉 糙米饭 午餐"
            if "low_sodium" in preferred_tags:
                return "清淡鸡胸肉便当 午餐"
            return "鸡胸肉蔬菜沙拉 午餐"
        if "seafood" in preferred_tags:
            return "三文鱼沙拉 晚餐"
        if "comfort" in preferred_tags:
            return "低脂鸡肉沙拉 晚餐"
        return "轻食减脂餐晚餐"

    def create_plan(self, open_id, text):
        parsed = self.parse_request(text)
        profile = self.store.load_profile()
        indicators = self.store.load_latest_indicators()
        constraints = self._derive_constraints(profile, indicators, text)
        goal_config, goal_key = self._pick_goal_config(parsed, constraints)
        start_date = datetime.now().date() + timedelta(days=1)
        duration_days = int(parsed["duration_days"])
        days = []
        for i in range(duration_days):
            plan_date = datetime.combine(start_date + timedelta(days=i), datetime.min.time())
            days.append(self._build_day_plan(i, plan_date, goal_config, constraints))

        plan = {
            "id": _generate_plan_id(open_id),
            "open_id": open_id,
            "status": "active",
            "request_text": parsed["request_text"],
            "goal": goal_key,
            "goal_label": goal_config["label"],
            "summary": goal_config["summary"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "duration_days": duration_days,
            "meal_schedule": parsed["meal_schedule"],
            "constraints": constraints,
            "profile_snapshot": {
                "basic_info": profile.get("basic_info", {}),
                "allergies": profile.get("allergies", []),
                "chronic_diseases": profile.get("chronic_diseases", []),
                "health_goals": profile.get("health_goals", []),
            },
            "indicator_snapshot": indicators,
            "days": days,
            "sent_log": {},
            "recommendation_source": _default_recommendation_source(),
        }

        # Pause previous active meal plans for the same user.
        existing = self.store.load_meal_plans()
        for item in existing:
            if item.get("open_id") == open_id and item.get("status") == "active":
                item["status"] = "superseded"
                item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing.append(plan)
        self.store.save_meal_plans(existing)

        profile_updates = []
        health_goals = list(profile.get("health_goals", []) or [])
        if goal_config["label"] not in health_goals:
            health_goals.append(goal_config["label"])
            profile["health_goals"] = health_goals
            self.store.save_profile(profile)
            profile_updates.append(goal_config["label"])

        return {
            "plan": plan,
            "profile_updates": profile_updates,
        }

    def pause_user_plans(self, open_id):
        plans = self.store.load_meal_plans()
        count = 0
        for item in plans:
            if item.get("open_id") == open_id and item.get("status") == "active":
                item["status"] = "paused"
                item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                count += 1
        if count:
            self.store.save_meal_plans(plans)
        return {"status": "success", "paused_count": count}

    def get_latest_user_plan(self, open_id):
        plans = [p for p in self.store.load_meal_plans() if p.get("open_id") == open_id]
        if not plans:
            return None
        plans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return plans[0]

    def _get_plan_day(self, plan, target_date):
        target = target_date.strftime("%Y-%m-%d")
        for day in plan.get("days", []):
            if day.get("date") == target:
                return day
        return None

    def _score_candidate(self, meal_spec, meal_key, candidate):
        score = 0
        candidate_tags = set(candidate.get("tags", []))
        preferred_tags = set(meal_spec.get("preferred_tags", []))
        avoid_tags = set(meal_spec.get("avoid_tags", []))
        if meal_key in candidate.get("meal_types", []):
            score += 6
        score += len(candidate_tags & preferred_tags) * 2
        score -= len(candidate_tags & avoid_tags) * 4
        cal_min, cal_max = meal_spec.get("target_calories", [0, 9999])
        calories = candidate.get("calories", 0)
        if cal_min <= calories <= cal_max:
            score += 4
        elif calories < cal_min:
            score += 1
        else:
            score -= 2
        protein = candidate.get("protein_g", 0)
        if "high_protein" in preferred_tags and protein >= 25:
            score += 3
        return score

    def _build_candidate_reason(self, meal_spec, item_name, store_name):
        reasons = []
        text = f"{item_name} {store_name}"
        if any(token in text for token in ["鸡胸", "牛肉", "鱼", "虾", "豆浆", "鸡蛋", "三文鱼", "豆腐"]):
            reasons.append("更偏高蛋白，符合这顿的减脂/控体重目标")
        if any(token in text for token in ["沙拉", "蔬菜", "轻食", "健康餐"]):
            reasons.append("蔬菜比例通常更高，整体负担更轻")
        if any(token in text for token in ["全麦", "糙米", "杂粮"]):
            reasons.append("主食结构更稳，更适合控制总热量和饱腹感")
        if not reasons:
            reasons.append("整体更接近今天这顿“高蛋白、清淡、少油少负担”的方向")
        return "；".join(reasons)

    def _build_display_candidates(self, meal_spec, candidates, result_cards, cart_action):
        display = []
        used_items = set()

        if cart_action.get("store_name"):
            item_name = cart_action.get("item_name") or (candidates[0]["item_name"] if candidates else meal_spec.get("phone_query", "推荐菜品"))
            display.append(
                {
                    "item_name": item_name,
                    "store_name": cart_action.get("store_name", ""),
                    "price": cart_action.get("item_price", "") or "待店内确认",
                    "reason": self._build_candidate_reason(meal_spec, item_name, cart_action.get("store_name", "")),
                }
            )
            used_items.add(item_name)

        for result_card in result_cards:
            item_name = meal_spec.get("phone_query", "推荐菜品")
            if item_name in used_items:
                continue
            store_name = result_card.get("store_name", "") or "待手机美团确认"
            display.append(
                {
                    "item_name": item_name,
                    "store_name": store_name,
                    "price": "待店内确认",
                    "reason": self._build_candidate_reason(meal_spec, item_name, store_name),
                }
            )
            used_items.add(item_name)
            if len(display) >= 3:
                return display[:3]

        for candidate in candidates:
            item_name = candidate.get("item_name", "") or meal_spec.get("phone_query", "推荐菜品")
            if item_name in used_items:
                continue
            store_name = candidate.get("store_name", "") or "待手机美团确认"
            display.append(
                {
                    "item_name": item_name,
                    "store_name": store_name,
                    "price": candidate.get("price", "") or "待店内确认",
                    "reason": self._build_candidate_reason(meal_spec, item_name, store_name),
                }
            )
            used_items.add(item_name)
            if len(display) >= 3:
                break

        return display[:3]

    def search_meituan_candidates(self, plan, meal_key, target_date=None, limit=3):
        target_date = target_date or datetime.now()
        day_plan = self._get_plan_day(plan, target_date)
        if not day_plan:
            return []
        meal_spec = day_plan["meals"][meal_key]
        if os.environ.get("HEALTHCLAW_ENABLE_PHONE_MEITUAN", "0") == "1":
            live_result = search_food_suggestions(meal_spec.get("phone_query", ""), limit=limit)
            if live_result.get("candidates"):
                return live_result["candidates"]
        ranked = []
        for candidate in MEAL_CANDIDATE_CATALOG:
            if meal_key not in candidate.get("meal_types", []):
                continue
            score = self._score_candidate(meal_spec, meal_key, candidate)
            ranked.append((score, candidate))
        ranked.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, candidate in ranked[:limit]:
            reason_bits = []
            if "high_protein" in candidate.get("tags", []):
                reason_bits.append("蛋白质更高")
            if "low_sugar" in candidate.get("tags", []):
                reason_bits.append("更适合控糖")
            if "vegetable_rich" in candidate.get("tags", []):
                reason_bits.append("蔬菜比例较高")
            if "low_sodium" in candidate.get("tags", []):
                reason_bits.append("更偏低盐")
            if "whole_grain" in candidate.get("tags", []):
                reason_bits.append("含粗粮/全麦")
            enriched = copy.deepcopy(candidate)
            enriched["match_score"] = score
            enriched["match_reason"] = "、".join(reason_bits) or "整体较符合当前这顿的目标"
            results.append(enriched)
        return results

    def prepare_live_meituan_push(self, plan, meal_key, target_date=None, limit=3, allow_fallback=True):
        target_date = target_date or datetime.now()
        day_plan = self._get_plan_day(plan, target_date)
        if not day_plan:
            return {
                "candidates": [],
                "cart_action": {},
                "result_cards": [],
                "display_candidates": [],
                "artifacts": {},
                "source": plan.get("recommendation_source", "unknown"),
                "live_status": "missing_day_plan",
                "fallback_used": False,
            }
        meal_spec = day_plan["meals"][meal_key]
        if os.environ.get("HEALTHCLAW_ENABLE_PHONE_MEITUAN", "0") != "1":
            fallback_candidates = self.search_meituan_candidates(plan, meal_key, target_date, limit=limit)
            return {
                "candidates": fallback_candidates,
                "cart_action": {},
                "result_cards": [],
                "artifacts": {},
                "display_candidates": [
                    {
                        "item_name": item.get("item_name", ""),
                        "store_name": item.get("store_name", ""),
                        "price": item.get("price", "") or "待店内确认",
                        "reason": item.get("match_reason", "整体较符合当前这顿目标"),
                    }
                    for item in fallback_candidates[:limit]
                ],
                "source": plan.get("recommendation_source", "meituan_demo_catalog"),
                "live_status": "phone_provider_disabled",
                "fallback_used": True,
            }
        live_result = search_and_add_best_item(meal_spec.get("phone_query", ""), limit=limit)
        live_candidates = live_result.get("candidates", [])
        live_result_cards = live_result.get("result_cards", [])[:limit]
        live_cart_action = live_result.get("cart_action", {})
        display_candidates = self._build_display_candidates(
            meal_spec,
            live_candidates,
            live_result_cards,
            live_cart_action,
        )
        if live_candidates or live_result_cards or live_cart_action:
            return {
                "candidates": live_candidates[:limit],
                "cart_action": live_cart_action,
                "result_cards": live_result_cards,
                "artifacts": {
                    "result_screenshot": live_result.get("screenshot_path", ""),
                    "merchant_screenshot": live_cart_action.get("merchant_screenshot", ""),
                    "cart_screenshot": live_cart_action.get("cart_screenshot", ""),
                },
                "display_candidates": display_candidates,
                "source": live_result.get("source", "meituan_phone_live_search"),
                "live_status": live_result.get("status", "success"),
                "live_message": live_result.get("msg", ""),
                "fallback_used": False,
            }
        if not allow_fallback:
            return {
                "candidates": [],
                "cart_action": live_cart_action,
                "result_cards": live_result_cards,
                "artifacts": {
                    "result_screenshot": live_result.get("screenshot_path", ""),
                    "merchant_screenshot": live_cart_action.get("merchant_screenshot", ""),
                    "cart_screenshot": live_cart_action.get("cart_screenshot", ""),
                },
                "display_candidates": [],
                "source": live_result.get("source", "meituan_phone_live_search"),
                "live_status": live_result.get("status", "error"),
                "live_message": live_result.get("msg", "real_chain_unavailable"),
                "fallback_used": False,
            }
        fallback_candidates = self.search_meituan_candidates(plan, meal_key, target_date, limit=limit)
        return {
            "candidates": fallback_candidates,
            "cart_action": live_cart_action,
            "result_cards": live_result_cards,
            "artifacts": {
                "result_screenshot": live_result.get("screenshot_path", ""),
                "merchant_screenshot": live_cart_action.get("merchant_screenshot", ""),
                "cart_screenshot": live_cart_action.get("cart_screenshot", ""),
            },
            "display_candidates": [
                {
                    "item_name": item.get("item_name", ""),
                    "store_name": item.get("store_name", ""),
                    "price": item.get("price", "") or "待店内确认",
                    "reason": item.get("match_reason", "整体较符合当前这顿目标"),
                }
                    for item in fallback_candidates[:limit]
            ],
            "source": plan.get("recommendation_source", "meituan_demo_catalog"),
            "live_status": live_result.get("status", "error"),
            "live_message": live_result.get("msg", ""),
            "fallback_used": True,
        }

    def format_plan_created_message(self, plan):
        meal_lines = []
        for meal_key in ["breakfast", "lunch", "dinner"]:
            schedule = plan["meal_schedule"][meal_key]
            meal_lines.append(
                f"- {schedule['label']}: {schedule['meal_time']} 用餐，{schedule['push_time']} 推送"
            )

        first_days = plan.get("days", [])[:3]
        preview_lines = []
        for day in first_days:
            preview_lines.append(f"- {day['date']} | {day['theme']}")

        constraint_lines = list(plan.get("constraints", {}).get("notes", []))
        if not constraint_lines:
            constraint_lines = ["- 当前按通用健康约束生成，后续可继续根据你的偏好微调。"]
        else:
            constraint_lines = [f"- {item}" for item in constraint_lines]

        return "\n".join(
            [
                "**饮食计划已创建**",
                f"目标: `{plan['goal_label']}`",
                f"周期: `{plan['start_date']}` 起连续 `{plan['duration_days']}` 天",
                f"策略: {plan['summary']}",
                "",
                "**三餐推送时间**",
                *meal_lines,
                "",
                "**系统识别到的健康约束**",
                *constraint_lines,
                "",
                "**前 3 天主题预览**",
                *preview_lines,
                "",
                f"_{_recommendation_source_note(plan.get('recommendation_source', 'unknown'))}_",
            ]
        )

    def format_plan_status_message(self, plan):
        if not plan:
            return "当前还没有激活的饮食计划。你可以直接说：我想减肥，给我未来一个月的用餐计划。"
        sent_count = len(plan.get("sent_log", {}))
        return "\n".join(
            [
                "**当前饮食计划**",
                f"状态: `{plan.get('status', 'unknown')}`",
                f"目标: `{plan.get('goal_label', '')}`",
                f"开始日期: `{plan.get('start_date', '')}`",
                f"已发送餐次: `{sent_count}`",
                f"推荐来源: `{_recommendation_source_label(plan.get('recommendation_source', 'unknown'))}`",
            ]
        )

    def collect_due_pushes(self, now=None):
        now = now or datetime.now()
        results = []
        plans = self.store.load_meal_plans()
        changed = False
        for plan in plans:
            if plan.get("status") != "active":
                continue
            start_date = datetime.strptime(plan["start_date"], "%Y-%m-%d").date()
            end_date = start_date + timedelta(days=int(plan.get("duration_days", 30)))
            if now.date() >= end_date:
                plan["status"] = "completed"
                plan["updated_at"] = now.strftime("%Y-%m-%d %H:%M")
                changed = True
                continue

            day_plan = self._get_plan_day(plan, now)
            if not day_plan:
                continue

            for meal_key in ["breakfast", "lunch", "dinner"]:
                schedule = plan["meal_schedule"][meal_key]
                due_dt = datetime.strptime(
                    f"{now.strftime('%Y-%m-%d')} {schedule['push_time']}", "%Y-%m-%d %H:%M"
                )
                lag_sec = (now - due_dt).total_seconds()
                sent_key = f"{day_plan['date']}.{meal_key}"
                if sent_key in (plan.get("sent_log") or {}):
                    continue
                if 0 <= lag_sec <= 90 * 60:
                    live_payload = self.prepare_live_meituan_push(plan, meal_key, now, limit=3)
                    results.append(
                        {
                            "plan_id": plan["id"],
                            "open_id": plan["open_id"],
                            "date": day_plan["date"],
                            "meal_key": meal_key,
                            "meal_label": schedule["label"],
                            "meal_time": schedule["meal_time"],
                            "day_plan": day_plan,
                            "meal_spec": day_plan["meals"][meal_key],
                            "candidates": live_payload["candidates"],
                            "cart_action": live_payload.get("cart_action", {}),
                            "result_cards": live_payload.get("result_cards", []),
                            "artifacts": live_payload.get("artifacts", {}),
                            "display_candidates": live_payload.get("display_candidates", []),
                            "recommendation_source": live_payload.get(
                                "source", plan.get("recommendation_source", "meituan_demo_catalog")
                            ),
                        }
                    )

        if changed:
            self.store.save_meal_plans(plans)
        return results

    def mark_push_sent(self, plan_id, date_str, meal_key, message_id=""):
        plans = self.store.load_meal_plans()
        for plan in plans:
            if plan.get("id") != plan_id:
                continue
            sent_log = plan.setdefault("sent_log", {})
            sent_log[f"{date_str}.{meal_key}"] = {
                "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "message_id": message_id,
            }
            plan["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.store.save_meal_plans(plans)
            return {"status": "success"}
        return {"status": "error", "msg": f"plan not found: {plan_id}"}

    def format_push_message(self, push):
        day_plan = push["day_plan"]
        meal_spec = push["meal_spec"]
        candidates = push.get("display_candidates") or []
        cart_action = push.get("cart_action", {})
        candidate_lines = []
        if candidates:
            for idx, item in enumerate(candidates, start=1):
                candidate_lines.extend(
                    [
                        f"{idx}. **{item['item_name']}**",
                        f"店铺：{item.get('store_name', '待手机美团确认')}",
                        f"推荐理由：{item.get('reason', '整体更接近今天这顿的健康目标')}",
                        f"价格：{item.get('price', '') or '待店内确认'}",
                    ]
                )
        else:
            candidate_lines.append("- 当前没有匹配到合适候选，建议按今天的目标关键词手动搜索。")

        cart_lines = []
        if cart_action.get("status") == "added":
            summary = cart_action.get("cart_summary", {})
            cart_lines = [
                "**已自动加入购物车**",
                f"- 商家: {cart_action.get('store_name', '')}",
                f"- 商品: {cart_action.get('item_name', '')}",
                f"- 单价: {cart_action.get('item_price', '') or summary.get('total_price', '')}",
            ]
            if summary.get("total_price"):
                cart_lines.append(f"- 当前购物车合计: {summary['total_price']}")
            if summary.get("shortage"):
                cart_lines.append(f"- 当前状态: {summary['shortage']}")
            if summary.get("shipping_text"):
                cart_lines.append(f"- 配送信息: {summary['shipping_text']}")
            if summary.get("cart_cta"):
                cart_lines.append(f"- 按钮状态: {summary['cart_cta']}")
            cart_lines.append("- 你现在可以直接去手机美团里确认并手动支付。")
        elif cart_action.get("status"):
            cart_lines = [
                "**购物车自动处理结果**",
            ]
            if cart_action.get("store_name"):
                cart_lines.append(f"- 店铺: {cart_action.get('store_name')}")
            if cart_action.get("item_name"):
                cart_lines.append(f"- 识别商品: {cart_action.get('item_name')}")
            if cart_action.get("item_price"):
                cart_lines.append(f"- 识别价格: {cart_action.get('item_price')}")
            if cart_action.get("status") == "skipped_safety_check":
                cart_lines.append("- 已为了安全起见跳过自动加购，你可以根据上面的候选自行确认。")
            if cart_action.get("status") == "needs_spec_selection":
                cart_lines.append("- 当前商品需要手动选择规格，我已经帮你定位到店铺页。")
                cart_lines.append("- 你现在可以直接在手机美团里点“选规格”，确认后再支付。")
            if cart_action.get("status") == "no_addable_item_found":
                cart_lines.append("- 已打开推荐店铺，但当前没稳定定位到可直接加购按钮。")
                cart_lines.append("- 你现在可以直接在手机美团里查看该店铺并手动选择这一餐。")
            if cart_action.get("status") == "no_result_card_found":
                cart_lines.append("- 当前没有稳定解析到商家卡片，建议你按上面的候选词手动搜索一次。")

        return "\n".join(
            [
                f"**{push['meal_label']}推荐提醒**",
                f"日期: `{push['date']}`",
                f"建议用餐时间: `{push['meal_time']}`",
                f"今日主题: `{day_plan['theme']}`",
                f"这一顿目标: {meal_spec['goal_note']}",
                f"建议搜索词: `{meal_spec['query']}`",
                "",
                "**候选餐**",
                *candidate_lines,
                "",
                *cart_lines,
            ]
        )
