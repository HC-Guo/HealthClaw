from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional


class WearableDataStore:
    def __init__(self):
        from config import WEARABLE_CONFIG

        self.config = WEARABLE_CONFIG
        self.db_path = self.config['db_path']
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wearable_profiles (
                eid TEXT PRIMARY KEY,
                source_brand TEXT,
                source_identifier TEXT,
                member_profile_json TEXT,
                fitness_profile_json TEXT,
                extra_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wearable_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eid TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metric_type TEXT,
                heart_rate REAL,
                steps REAL,
                sleep_duration REAL,
                deep_sleep_ratio REAL,
                spo2 REAL,
                stress_level REAL,
                calories REAL,
                distance REAL,
                activity_type TEXT,
                lat REAL,
                lon REAL,
                raw_key TEXT,
                raw_value_json TEXT,
                source_brand TEXT,
                source_type TEXT,
                data_origin TEXT,
                quality_flag TEXT DEFAULT 'good',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(eid, timestamp, metric_type, source_type, data_origin)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wearable_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eid TEXT NOT NULL,
                activity_type TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_sec REAL,
                distance_m REAL,
                steps REAL,
                calories REAL,
                avg_pace_sec_per_km REAL,
                gpx_file TEXT,
                raw_payload_json TEXT,
                source_brand TEXT,
                source_type TEXT,
                data_origin TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wearable_daily_summary (
                eid TEXT NOT NULL,
                date TEXT NOT NULL,
                avg_heart_rate REAL,
                night_resting_hr REAL,
                avg_steps REAL,
                avg_sleep_hours REAL,
                avg_spo2 REAL,
                avg_stress REAL,
                total_calories REAL,
                total_distance REAL,
                exercise_sessions INTEGER,
                coverage REAL,
                quality_flag TEXT,
                sample_count INTEGER,
                baseline_7d_hr REAL,
                baseline_30d_hr REAL,
                baseline_7d_steps REAL,
                baseline_30d_steps REAL,
                baseline_7d_sleep REAL,
                baseline_30d_sleep REAL,
                delta_hr_from_baseline REAL,
                delta_steps_from_baseline REAL,
                delta_sleep_from_baseline REAL,
                anomaly_flags TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (eid, date)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wearable_import_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eid TEXT NOT NULL,
                source_type TEXT,
                source_path TEXT,
                imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                record_count INTEGER,
                session_count INTEGER,
                note TEXT
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_wearable_records_eid_ts ON wearable_records(eid, timestamp)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_wearable_sessions_eid_start ON wearable_sessions(eid, start_time)')
        conn.commit()
        conn.close()

    def store_import_result(self, eid: str, source_type: str, source_path: str, import_result: Dict) -> Dict:
        profile = import_result.get('profile') or {}
        records = import_result.get('records') or []
        sessions = import_result.get('sessions') or []
        notes = import_result.get('notes') or []

        conn = self._connect()
        cur = conn.cursor()

        if profile:
            cur.execute('''
                INSERT INTO wearable_profiles (eid, source_brand, source_identifier, member_profile_json, fitness_profile_json, extra_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(eid) DO UPDATE SET
                    source_brand=excluded.source_brand,
                    source_identifier=excluded.source_identifier,
                    member_profile_json=excluded.member_profile_json,
                    fitness_profile_json=excluded.fitness_profile_json,
                    extra_json=excluded.extra_json,
                    updated_at=CURRENT_TIMESTAMP
            ''', (
                eid,
                profile.get('source_brand') or ('xiaomi' if 'member_profile' in profile or 'fitness_profile' in profile else 'unknown'),
                profile.get('source_identifier') or (profile.get('member_profile') or {}).get('uid') or (profile.get('fitness_profile') or {}).get('uid') or '',
                json.dumps(profile.get('member_profile', {}), ensure_ascii=False),
                json.dumps(profile.get('fitness_profile', {}), ensure_ascii=False),
                json.dumps({k: v for k, v in profile.items() if k not in {'member_profile', 'fitness_profile', 'source_brand', 'source_identifier'}}, ensure_ascii=False),
            ))

        inserted_records = 0
        for record in records:
            if not record.get('timestamp'):
                continue
            cur.execute('''
                INSERT OR IGNORE INTO wearable_records (
                    eid, timestamp, metric_type, heart_rate, steps, sleep_duration, deep_sleep_ratio, spo2,
                    stress_level, calories, distance, activity_type, lat, lon, raw_key, raw_value_json,
                    source_brand, source_type, data_origin, quality_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                eid,
                record.get('timestamp'),
                record.get('metric_type'),
                record.get('heart_rate'),
                record.get('steps'),
                record.get('sleep_duration'),
                record.get('deep_sleep_ratio'),
                record.get('spo2'),
                record.get('stress_level'),
                record.get('calories'),
                record.get('distance'),
                record.get('activity_type'),
                record.get('lat'),
                record.get('lon'),
                record.get('raw_key'),
                json.dumps(record.get('raw_value_json'), ensure_ascii=False) if record.get('raw_value_json') is not None else None,
                record.get('source_brand'),
                record.get('source_type', source_type),
                record.get('data_origin'),
                record.get('quality_flag', 'good'),
            ))
            inserted_records += cur.rowcount

        inserted_sessions = 0
        for session in sessions:
            cur.execute('''
                INSERT INTO wearable_sessions (
                    eid, activity_type, start_time, end_time, duration_sec, distance_m, steps, calories,
                    avg_pace_sec_per_km, gpx_file, raw_payload_json, source_brand, source_type, data_origin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                eid,
                session.get('activity_type'),
                session.get('start_time'),
                session.get('end_time'),
                session.get('duration_sec'),
                session.get('distance_m'),
                session.get('steps'),
                session.get('calories'),
                session.get('avg_pace_sec_per_km'),
                session.get('gpx_file'),
                json.dumps(session.get('raw_payload_json'), ensure_ascii=False) if session.get('raw_payload_json') is not None else None,
                session.get('source_brand'),
                session.get('source_type', source_type),
                session.get('data_origin'),
            ))
            inserted_sessions += 1

        cur.execute('''
            INSERT INTO wearable_import_log (eid, source_type, source_path, record_count, session_count, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (eid, source_type, source_path, inserted_records, inserted_sessions, ' | '.join(notes[:5])))
        conn.commit()
        conn.close()

        self.refresh_daily_summary(eid)
        trend = self.query_trend(eid, '30d')

        return {
            'status': 'success',
            'records_imported': inserted_records,
            'sessions_imported': inserted_sessions,
            'notes': notes,
            'trend_preview': trend.get('aggregated', {}),
        }

    def refresh_daily_summary(self, eid: str):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM wearable_records WHERE eid = ? ORDER BY timestamp', (eid,))
        records = [dict(row) for row in cur.fetchall()]
        cur.execute('SELECT * FROM wearable_sessions WHERE eid = ? ORDER BY start_time', (eid,))
        sessions = [dict(row) for row in cur.fetchall()]

        by_date: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        meta: Dict[str, Dict] = defaultdict(lambda: {'samples': 0, 'quality': []})

        for record in records:
            date = self._date_key(record.get('timestamp'))
            if not date:
                continue
            meta[date]['samples'] += 1
            meta[date]['quality'].append(record.get('quality_flag') or 'good')
            if record.get('heart_rate') is not None:
                by_date[date]['heart_rate'].append(float(record['heart_rate']))
                hour = self._hour(record.get('timestamp'))
                if hour is not None and 0 <= hour < 6:
                    by_date[date]['night_hr'].append(float(record['heart_rate']))
            if record.get('steps') is not None:
                by_date[date]['steps'].append(float(record['steps']))
            if record.get('sleep_duration') is not None:
                by_date[date]['sleep_duration'].append(float(record['sleep_duration']))
            if record.get('spo2') is not None and float(record['spo2']) > 0:
                by_date[date]['spo2'].append(float(record['spo2']))
            if record.get('stress_level') is not None:
                by_date[date]['stress'].append(float(record['stress_level']))
            if record.get('calories') is not None:
                by_date[date]['calories'].append(float(record['calories']))
            if record.get('distance') is not None:
                by_date[date]['distance'].append(float(record['distance']))

        for session in sessions:
            date = self._date_key(session.get('start_time') or session.get('end_time'))
            if not date:
                continue
            by_date[date]['session_count'].append(1.0)
            if session.get('steps') is not None:
                by_date[date]['session_steps'].append(float(session['steps']))
            if session.get('calories') is not None:
                by_date[date]['session_calories'].append(float(session['calories']))
            if session.get('distance_m') is not None:
                by_date[date]['session_distance'].append(float(session['distance_m']))

        sorted_dates = sorted(by_date.keys())
        running_rows = []
        for date in sorted_dates:
            data = by_date[date]
            row = {
                'eid': eid,
                'date': date,
                'avg_heart_rate': self._avg(data.get('heart_rate')),
                'night_resting_hr': self._min_or_avg(data.get('night_hr'), data.get('heart_rate')),
                'avg_steps': self._daily_steps(data),
                'avg_sleep_hours': self._avg(data.get('sleep_duration')),
                'avg_spo2': self._avg(data.get('spo2')),
                'avg_stress': self._avg(data.get('stress')),
                'total_calories': self._sum(data.get('calories')) + self._sum(data.get('session_calories')),
                'total_distance': self._sum(data.get('distance')) + self._sum(data.get('session_distance')),
                'exercise_sessions': int(self._sum(data.get('session_count'))),
                'coverage': round(min(1.0, meta[date]['samples'] / 24.0), 3),
                'quality_flag': self._quality_flag(meta[date]['samples']),
                'sample_count': int(meta[date]['samples']),
            }
            running_rows.append(row)

        rows_with_baselines = []
        for idx, row in enumerate(running_rows):
            prev7 = running_rows[max(0, idx - 7):idx]
            prev30 = running_rows[max(0, idx - 30):idx]
            row['baseline_7d_hr'] = self._avg([r['avg_heart_rate'] for r in prev7 if r['avg_heart_rate'] is not None])
            row['baseline_30d_hr'] = self._avg([r['avg_heart_rate'] for r in prev30 if r['avg_heart_rate'] is not None])
            row['baseline_7d_steps'] = self._avg([r['avg_steps'] for r in prev7 if r['avg_steps'] is not None])
            row['baseline_30d_steps'] = self._avg([r['avg_steps'] for r in prev30 if r['avg_steps'] is not None])
            row['baseline_7d_sleep'] = self._avg([r['avg_sleep_hours'] for r in prev7 if r['avg_sleep_hours'] is not None])
            row['baseline_30d_sleep'] = self._avg([r['avg_sleep_hours'] for r in prev30 if r['avg_sleep_hours'] is not None])
            row['delta_hr_from_baseline'] = self._delta(row['avg_heart_rate'], row['baseline_30d_hr'])
            row['delta_steps_from_baseline'] = self._delta(row['avg_steps'], row['baseline_30d_steps'])
            row['delta_sleep_from_baseline'] = self._delta(row['avg_sleep_hours'], row['baseline_30d_sleep'])
            row['anomaly_flags'] = json.dumps(self._detect_flags(row), ensure_ascii=False)
            rows_with_baselines.append(row)

        cur.execute('DELETE FROM wearable_daily_summary WHERE eid = ?', (eid,))
        for row in rows_with_baselines:
            cur.execute('''
                INSERT INTO wearable_daily_summary (
                    eid, date, avg_heart_rate, night_resting_hr, avg_steps, avg_sleep_hours, avg_spo2, avg_stress,
                    total_calories, total_distance, exercise_sessions, coverage, quality_flag, sample_count,
                    baseline_7d_hr, baseline_30d_hr, baseline_7d_steps, baseline_30d_steps, baseline_7d_sleep, baseline_30d_sleep,
                    delta_hr_from_baseline, delta_steps_from_baseline, delta_sleep_from_baseline, anomaly_flags, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                row['eid'], row['date'], row['avg_heart_rate'], row['night_resting_hr'], row['avg_steps'], row['avg_sleep_hours'], row['avg_spo2'],
                row['avg_stress'], row['total_calories'], row['total_distance'], row['exercise_sessions'], row['coverage'], row['quality_flag'],
                row['sample_count'], row['baseline_7d_hr'], row['baseline_30d_hr'], row['baseline_7d_steps'], row['baseline_30d_steps'],
                row['baseline_7d_sleep'], row['baseline_30d_sleep'], row['delta_hr_from_baseline'], row['delta_steps_from_baseline'],
                row['delta_sleep_from_baseline'], row['anomaly_flags']
            ))

        conn.commit()
        conn.close()

    def query_recent_snapshot(self, eid: str) -> Dict:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM wearable_records WHERE eid = ? ORDER BY timestamp DESC LIMIT 50', (eid,))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        if not rows:
            return {'status': 'empty', 'message': f'No wearable records found for {eid}'}

        latest = rows[0]
        snapshot = {
            'latest_timestamp': latest.get('timestamp'),
            'heart_rate': self._first_not_none(rows, 'heart_rate'),
            'spo2': self._first_not_none(rows, 'spo2'),
            'stress_level': self._first_not_none(rows, 'stress_level'),
            'steps': self._first_not_none(rows, 'steps'),
        }
        return {'status': 'success', 'snapshot': snapshot}

    def query_trend(self, eid: str, period: str = '30d') -> Dict:
        days = self._period_days(period)
        start_date = (datetime.utcnow().date() - timedelta(days=max(days - 1, 0))).isoformat()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM wearable_daily_summary WHERE eid = ? AND date >= ? ORDER BY date', (eid, start_date))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()

        if not rows:
            return {'status': 'empty', 'message': f'No wearable summaries found for {eid}', 'aggregated': {}, 'daily': []}

        aggregated = {
            'avg_heart_rate': self._avg([r['avg_heart_rate'] for r in rows]),
            'night_resting_hr': self._avg([r['night_resting_hr'] for r in rows]),
            'avg_steps': self._avg([r['avg_steps'] for r in rows]),
            'avg_sleep_hours': self._avg([r['avg_sleep_hours'] for r in rows]),
            'avg_spo2': self._avg([r['avg_spo2'] for r in rows]),
            'avg_stress': self._avg([r['avg_stress'] for r in rows]),
            'total_calories': self._sum([r['total_calories'] for r in rows]),
            'total_distance': self._sum([r['total_distance'] for r in rows]),
            'exercise_sessions': int(self._sum([r['exercise_sessions'] for r in rows])),
        }
        baselines = {
            'baseline_7d_hr': self._last_not_none(rows, 'baseline_7d_hr'),
            'baseline_30d_hr': self._last_not_none(rows, 'baseline_30d_hr'),
            'baseline_7d_steps': self._last_not_none(rows, 'baseline_7d_steps'),
            'baseline_30d_steps': self._last_not_none(rows, 'baseline_30d_steps'),
            'baseline_7d_sleep': self._last_not_none(rows, 'baseline_7d_sleep'),
            'baseline_30d_sleep': self._last_not_none(rows, 'baseline_30d_sleep'),
        }
        deltas = {
            'delta_hr_from_baseline': self._safe_round(self._delta(aggregated['avg_heart_rate'], baselines['baseline_30d_hr'])),
            'delta_steps_from_baseline': self._safe_round(self._delta(aggregated['avg_steps'], baselines['baseline_30d_steps'])),
            'delta_sleep_from_baseline': self._safe_round(self._delta(aggregated['avg_sleep_hours'], baselines['baseline_30d_sleep'])),
        }
        flags = []
        for row in rows:
            try:
                flags.extend(json.loads(row.get('anomaly_flags') or '[]'))
            except json.JSONDecodeError:
                continue
        quality = {
            'coverage': self._avg([r['coverage'] for r in rows]),
            'quality_flag': 'good' if self._avg([r['coverage'] for r in rows]) >= 0.7 else 'fair',
            'sample_count': int(self._sum([r['sample_count'] for r in rows])),
            'days_available': len(rows),
        }
        sessions = self._session_summary(eid, rows[0]['date'], rows[-1]['date'])
        return {
            'status': 'success',
            'eid': eid,
            'period': period,
            'aggregated': aggregated,
            'baselines': baselines,
            'deltas': deltas,
            'quality': quality,
            'flags': sorted(set(flags)),
            'exercise_summary': sessions,
            'daily': rows,
        }

    def _session_summary(self, eid: str, start_date: str, end_date: str) -> Dict:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM wearable_sessions WHERE eid = ? AND date(start_time) >= ? AND date(start_time) <= ?', (eid, start_date, end_date))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        if not rows:
            return {'session_count': 0}
        distances = [row['distance_m'] for row in rows if row.get('distance_m') is not None]
        durations = [row['duration_sec'] for row in rows if row.get('duration_sec') is not None]
        activity_types = sorted({str(row.get('activity_type') or 'exercise') for row in rows})
        return {
            'session_count': len(rows),
            'activity_types': activity_types,
            'total_distance_m': self._sum(distances),
            'avg_duration_min': self._safe_round(self._avg(durations) / 60.0 if durations else None),
        }

    def detect_anomalies(self, eid: str, lookback_days: int = 30, sensitivity: str = "medium") -> Dict:
        thresholds = {
            "low": {"hr_delta": 14, "sleep_delta": -2.5, "steps_ratio": 0.45, "spo2": 90, "persist": 4},
            "medium": {"hr_delta": 10, "sleep_delta": -2.0, "steps_ratio": 0.60, "spo2": 92, "persist": 3},
            "high": {"hr_delta": 7, "sleep_delta": -1.5, "steps_ratio": 0.75, "spo2": 94, "persist": 2},
        }
        cfg = thresholds.get(sensitivity, thresholds["medium"])
        start_date = (datetime.utcnow().date() - timedelta(days=max(lookback_days - 1, 0))).isoformat()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM wearable_daily_summary WHERE eid = ? AND date >= ? ORDER BY date', (eid, start_date))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        if not rows:
            return {"status": "empty", "message": f"No wearable summaries found for {eid}", "anomalies": []}

        anomalies = []
        anomalies.extend(self._persistent_delta_anomalies(rows, 'avg_heart_rate', 'baseline_30d_hr', cfg['hr_delta'], cfg['persist'], 'resting_hr', 'warning', 'baseline_deviation', 'Heart rate remains above personal baseline.'))
        anomalies.extend(self._persistent_delta_anomalies(rows, 'avg_sleep_hours', 'baseline_30d_sleep', cfg['sleep_delta'], cfg['persist'], 'sleep_duration', 'warning', 'sleep_loss', 'Sleep duration remains below personal baseline.', direction='below'))
        anomalies.extend(self._persistent_ratio_anomalies(rows, 'avg_steps', 'baseline_30d_steps', cfg['steps_ratio'], cfg['persist'], 'steps', 'info', 'low_activity', 'Activity volume remains below personal baseline.'))

        for row in rows:
            spo2 = row.get('avg_spo2')
            if spo2 is not None and float(spo2) > 0 and float(spo2) < cfg['spo2']:
                anomalies.append({
                    'metric': 'spo2',
                    'severity': 'critical' if float(spo2) < 90 else 'warning',
                    'type': 'absolute_threshold',
                    'current_value': float(spo2),
                    'baseline_value': None,
                    'delta': None,
                    'duration_days': 1,
                    'confidence': 0.85,
                    'date': row.get('date'),
                    'explanation': f"Average SpO2 {float(spo2):.1f} is below the configured threshold.",
                })

        deduped = self._dedupe_anomalies(anomalies)
        return {
            'status': 'success',
            'eid': eid,
            'lookback_days': lookback_days,
            'sensitivity': sensitivity,
            'anomalies': deduped,
        }

    def _persistent_delta_anomalies(self, rows, field, baseline_field, threshold, persist_days, metric, severity, anomaly_type, explanation, direction='above'):
        streak = []
        results = []
        for row in rows:
            current = row.get(field)
            baseline = row.get(baseline_field)
            if current is None or baseline is None:
                streak = []
                continue
            delta = float(current) - float(baseline)
            hit = delta >= threshold if direction == 'above' else delta <= threshold
            if hit:
                streak.append((row, delta))
            else:
                if len(streak) >= persist_days:
                    results.append(self._build_persistent_anomaly(streak, metric, severity, anomaly_type, explanation))
                streak = []
        if len(streak) >= persist_days:
            results.append(self._build_persistent_anomaly(streak, metric, severity, anomaly_type, explanation))
        return results

    def _persistent_ratio_anomalies(self, rows, field, baseline_field, ratio_threshold, persist_days, metric, severity, anomaly_type, explanation):
        streak = []
        results = []
        for row in rows:
            current = row.get(field)
            baseline = row.get(baseline_field)
            if current is None or baseline in (None, 0):
                streak = []
                continue
            ratio = float(current) / float(baseline)
            if ratio <= ratio_threshold:
                streak.append((row, float(current) - float(baseline)))
            else:
                if len(streak) >= persist_days:
                    results.append(self._build_persistent_anomaly(streak, metric, severity, anomaly_type, explanation))
                streak = []
        if len(streak) >= persist_days:
            results.append(self._build_persistent_anomaly(streak, metric, severity, anomaly_type, explanation))
        return results

    def _build_persistent_anomaly(self, streak, metric, severity, anomaly_type, explanation):
        row, delta = streak[-1]
        baseline_field = {
            'resting_hr': 'baseline_30d_hr',
            'sleep_duration': 'baseline_30d_sleep',
            'steps': 'baseline_30d_steps',
        }.get(metric)
        current_field = {
            'resting_hr': 'avg_heart_rate',
            'sleep_duration': 'avg_sleep_hours',
            'steps': 'avg_steps',
        }.get(metric)
        return {
            'metric': metric,
            'severity': severity,
            'type': anomaly_type,
            'current_value': row.get(current_field),
            'baseline_value': row.get(baseline_field),
            'delta': round(float(delta), 2),
            'duration_days': len(streak),
            'confidence': round(min(0.95, 0.6 + 0.08 * len(streak)), 2),
            'date': row.get('date'),
            'explanation': explanation,
        }

    def _dedupe_anomalies(self, anomalies):
        seen = {}
        for item in anomalies:
            key = (item.get('metric'), item.get('type'), item.get('date'))
            if key not in seen or (item.get('duration_days', 0) > seen[key].get('duration_days', 0)):
                seen[key] = item
        return sorted(seen.values(), key=lambda x: (x.get('severity') != 'critical', x.get('metric', ''), x.get('date', '')))

    def get_profile(self, eid: str) -> Dict:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM wearable_profiles WHERE eid = ?', (eid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return {}
        row = dict(row)
        return {
            'source_brand': row.get('source_brand'),
            'source_identifier': row.get('source_identifier'),
            'member_profile': json.loads(row.get('member_profile_json') or '{}'),
            'fitness_profile': json.loads(row.get('fitness_profile_json') or '{}'),
            'extra': json.loads(row.get('extra_json') or '{}'),
        }

    def _period_days(self, period: str) -> int:
        if isinstance(period, str) and period.endswith('d'):
            try:
                return max(1, int(period[:-1]))
            except ValueError:
                return 30
        return 30

    def _date_key(self, ts: Optional[str]) -> Optional[str]:
        if not ts:
            return None
        return ts[:10]

    def _hour(self, ts: Optional[str]) -> Optional[int]:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts).hour
        except ValueError:
            return None

    def _avg(self, values: Iterable[Optional[float]]) -> Optional[float]:
        values = values or []
        clean = [float(v) for v in values if v is not None]
        if not clean:
            return None
        return round(mean(clean), 2)

    def _sum(self, values: Iterable[Optional[float]]) -> float:
        values = values or []
        return round(sum(float(v) for v in values if v is not None), 2)

    def _min_or_avg(self, preferred: Optional[List[float]], fallback: Optional[List[float]]) -> Optional[float]:
        if preferred:
            return round(min(preferred), 2)
        if fallback:
            return round(mean(fallback), 2)
        return None

    def _daily_steps(self, data: Dict[str, List[float]]) -> Optional[float]:
        step_values = data.get('steps') or []
        session_steps = data.get('session_steps') or []
        if step_values:
            return round(max(step_values), 2)
        if session_steps:
            return round(sum(session_steps), 2)
        return None

    def _quality_flag(self, sample_count: int) -> str:
        if sample_count >= 12:
            return 'good'
        if sample_count >= 4:
            return 'fair'
        return 'poor'

    def _delta(self, current: Optional[float], baseline: Optional[float]) -> Optional[float]:
        if current is None or baseline is None:
            return None
        return round(current - baseline, 2)

    def _safe_round(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return round(float(value), 2)

    def _detect_flags(self, row: Dict) -> List[str]:
        flags = []
        if row.get('delta_hr_from_baseline') is not None and row['delta_hr_from_baseline'] >= 10:
            flags.append('resting_hr_up')
        if row.get('delta_sleep_from_baseline') is not None and row['delta_sleep_from_baseline'] <= -2:
            flags.append('sleep_down')
        if row.get('avg_spo2') is not None and row['avg_spo2'] > 0 and row['avg_spo2'] < 92:
            flags.append('spo2_low')
        if row.get('avg_steps') is not None and row['avg_steps'] < 5000:
            flags.append('low_activity')
        return flags

    def _first_not_none(self, rows: List[Dict], field: str):
        for row in rows:
            if row.get(field) is not None:
                return row[field]
        return None

    def _last_not_none(self, rows: List[Dict], field: str):
        for row in reversed(rows):
            if row.get(field) is not None:
                return row[field]
        return None
