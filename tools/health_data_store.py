"""
HealthClaw 个人健康数据统一存取层
所有用户数据以 JSON 文件存储在 memory/user_data/ 下
"""
import os, json, time
from datetime import datetime


class HealthDataStore:
    """个人健康数据的统一存取层"""

    def __init__(self, base_dir='memory/user_data'):
        self.base_dir = base_dir
        self._ensure_dirs()

    def _ensure_dirs(self):
        for sub in ['', 'checkups', 'wearable_imports', 'diet_exercise_log']:
            p = os.path.join(self.base_dir, sub)
            os.makedirs(p, exist_ok=True)

    def _path(self, *parts):
        return os.path.join(self.base_dir, *parts)

    # ==================== 用户画像 ====================

    def load_profile(self) -> dict:
        path = self._path('profile.json')
        if not os.path.exists(path):
            default = {
                "basic_info": {},
                "family_history": [],
                "allergies": [],
                "chronic_diseases": [],
                "medications": [],
                "health_goals": [],
                "preferences": {},
                "created_at": datetime.now().strftime('%Y-%m-%d'),
                "updated_at": datetime.now().strftime('%Y-%m-%d'),
            }
            self.save_profile(default)
            return default
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_profile(self, data: dict):
        data['updated_at'] = datetime.now().strftime('%Y-%m-%d')
        path = self._path('profile.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_profile_field(self, field: str, action: str, data) -> dict:
        """更新画像字段: action=set/append/remove"""
        profile = self.load_profile()
        if field not in profile:
            return {"status": "error", "msg": f"未知字段: {field}"}

        if action == 'set':
            profile[field] = data
        elif action == 'append':
            if isinstance(profile[field], list):
                if isinstance(data, list):
                    profile[field].extend(data)
                else:
                    profile[field].append(data)
            elif isinstance(profile[field], dict):
                profile[field].update(data)
            else:
                profile[field] = data
        elif action == 'remove':
            if isinstance(profile[field], list):
                profile[field] = [x for x in profile[field]
                                  if x != data and (not isinstance(x, dict) or x.get('name') != data)]
            else:
                return {"status": "error", "msg": f"remove 仅支持列表字段"}
        else:
            return {"status": "error", "msg": f"未知操作: {action}"}

        self.save_profile(profile)
        return {"status": "success", "field": field, "action": action}

    # ==================== 体检数据 ====================

    def append_checkup(self, date: str, data: dict, hospital: str = ""):
        """保存一次体检的结构化数据"""
        record = {
            "date": date,
            "hospital": hospital,
            "indicators": data,
            "saved_at": datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        path = self._path('checkups', f'{date}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        self._update_latest_indicators(data, date)
        return path

    def get_checkup_history(self) -> list:
        """获取所有体检记录，按日期排序"""
        checkup_dir = self._path('checkups')
        records = []
        for fname in sorted(os.listdir(checkup_dir)):
            if fname.endswith('.json'):
                with open(os.path.join(checkup_dir, fname), 'r', encoding='utf-8') as f:
                    records.append(json.load(f))
        return records

    def get_indicator_trend(self, indicator: str, period: str = 'all') -> list:
        """获取某个指标的历史趋势"""
        history = self.get_checkup_history()
        trend = []
        for rec in history:
            indicators = rec.get('indicators', {})
            if indicator in indicators:
                trend.append({
                    "date": rec['date'],
                    "value": indicators[indicator].get('value') if isinstance(indicators[indicator], dict) else indicators[indicator],
                })
        return trend

    def _update_latest_indicators(self, indicators: dict, date: str):
        """更新最新指标快照"""
        path = self._path('latest_indicators.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                latest = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            latest = {}

        for name, val in indicators.items():
            old = latest.get(name, {})
            old_val = old.get('value')
            if isinstance(val, dict):
                new_entry = {"value": val.get('value'), "unit": val.get('unit', ''), "date": date}
            else:
                new_entry = {"value": val, "unit": "", "date": date}
            if old_val is not None and new_entry['value'] is not None:
                try:
                    diff = float(new_entry['value']) - float(old_val)
                    new_entry['trend'] = '↑' if diff > 0 else ('↓' if diff < 0 else '→')
                except (ValueError, TypeError):
                    new_entry['trend'] = '?'
            latest[name] = new_entry

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(latest, f, indent=2, ensure_ascii=False)

    def load_latest_indicators(self) -> dict:
        path = self._path('latest_indicators.json')
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ==================== 用药管理 ====================

    def load_medications(self) -> list:
        path = self._path('medications.json')
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_medications(self, meds: list):
        path = self._path('medications.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(meds, f, indent=2, ensure_ascii=False)

    def add_medication(self, drug_name, dosage='', frequency='', reason=''):
        meds = self.load_medications()
        meds.append({
            "drug_name": drug_name, "dosage": dosage,
            "frequency": frequency, "reason": reason,
            "start_date": datetime.now().strftime('%Y-%m-%d'),
            "active": True,
        })
        self.save_medications(meds)
        return {"status": "success", "msg": f"已添加用药: {drug_name}"}

    def stop_medication(self, drug_name, reason=''):
        meds = self.load_medications()
        found = False
        for m in meds:
            if m['drug_name'] == drug_name and m.get('active', True):
                m['active'] = False
                m['stop_date'] = datetime.now().strftime('%Y-%m-%d')
                m['stop_reason'] = reason
                found = True
        if found:
            self.save_medications(meds)
            return {"status": "success", "msg": f"已停用: {drug_name}"}
        return {"status": "error", "msg": f"未找到正在使用的药物: {drug_name}"}

    # ==================== 提醒管理 ====================

    def load_reminders(self) -> list:
        path = self._path('reminders.json')
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_reminders(self, reminders: list):
        path = self._path('reminders.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)

    def add_reminder(self, rtype, title, schedule, note=''):
        reminders = self.load_reminders()
        reminders.append({
            "id": f"rem_{int(time.time())}",
            "type": rtype, "title": title, "schedule": schedule,
            "note": note, "status": "pending",
            "created_at": datetime.now().strftime('%Y-%m-%d'),
        })
        self.save_reminders(reminders)
        return {"status": "success", "msg": f"已设置提醒: {title}"}

    # ==================== 生活方式日志 ====================

    def append_lifestyle_log(self, category, data, timestamp=None):
        path = self._path('lifestyle_log.jsonl')
        record = {
            "category": category,
            "data": data,
            "timestamp": timestamp or datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        return {"status": "success"}

    def read_lifestyle_log(self, category=None, days=7) -> list:
        path = self._path('lifestyle_log.jsonl')
        if not os.path.exists(path):
            return []
        records = []
        cutoff = None
        if days:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if category and rec.get('category') != category:
                    continue
                if cutoff and rec.get('timestamp', '') < cutoff:
                    continue
                records.append(rec)
        return records

    # ==================== 对话历史持久化 ====================

    def append_conversation_log(self, user_query, agent_summary, turn_count):
        path = self._path('conversation_log.jsonl')
        record = {
            "time": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "user_query": user_query[:300],
            "agent_summary": agent_summary[:500],
            "turns": turn_count,
        }
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    # ==================== 饮食计划 ====================

    def load_meal_plans(self) -> list:
        path = self._path('meal_plans.json')
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_meal_plans(self, plans: list):
        path = self._path('meal_plans.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(plans, f, indent=2, ensure_ascii=False)

    def upsert_meal_plan(self, plan: dict):
        plans = self.load_meal_plans()
        plan_id = str(plan.get('id', '') or '')
        if not plan_id:
            raise ValueError("meal plan id is required")
        updated = False
        for idx, item in enumerate(plans):
            if str(item.get('id')) == plan_id:
                plans[idx] = plan
                updated = True
                break
        if not updated:
            plans.append(plan)
        self.save_meal_plans(plans)
        return {"status": "success", "id": plan_id, "updated": updated}

    def get_active_meal_plans(self) -> list:
        plans = self.load_meal_plans()
        return [p for p in plans if p.get('status', 'active') == 'active']

    def update_meal_plan_status(self, plan_id: str, status: str):
        plans = self.load_meal_plans()
        found = False
        for item in plans:
            if str(item.get('id')) == str(plan_id):
                item['status'] = status
                item['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                found = True
                break
        if found:
            self.save_meal_plans(plans)
            return {"status": "success", "id": plan_id, "plan_status": status}
        return {"status": "error", "msg": f"meal plan not found: {plan_id}"}
