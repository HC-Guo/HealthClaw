# -*- coding: utf-8 -*-
"""tools/one_click_health 路径与写保护策略单测"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import one_click_health as och


def test_main_sop_path_detected():
    p = och.main_sop_abs_path(ROOT)
    assert os.path.isfile(p), p
    assert och.is_protected_one_click_main_sop(p)


def test_patch_allowed_only_with_whitelist():
    p = och.main_sop_abs_path(ROOT)
    ok, err = och.check_one_click_main_sop_file_patch_allowed(p, allow_registry_edit=False)
    assert ok is False and err
    ok2, err2 = och.check_one_click_main_sop_file_patch_allowed(p, allow_registry_edit=True)
    assert ok2 is True and err2 is None


def test_file_write_always_denied_on_main_sop():
    p = och.main_sop_abs_path(ROOT)
    ok, err = och.check_one_click_main_sop_file_write_allowed(p)
    assert ok is False and err


def test_unrelated_path_allowed():
    other = str((ROOT / "ga.py").resolve())
    assert och.check_one_click_main_sop_file_patch_allowed(other, False) == (True, None)
    assert och.check_one_click_main_sop_file_write_allowed(other) == (True, None)


def test_sop_learn_block_modes():
    assert och.is_one_click_query_blocked_for_sop_learn("mode=one_click_health_analysis\nx")
    assert och.is_one_click_query_blocked_for_sop_learn("mode=one_click_registry_update")
    assert och.is_one_click_query_blocked_for_sop_learn("[一键健康分析指令]\n")
    assert not och.is_one_click_query_blocked_for_sop_learn("普通问诊")


def test_skip_autosave_main_slug():
    skip, _ = och.should_skip_autosave_sop("One Click Health Analysis SOP", "hello")
    assert skip
    skip2, _ = och.should_skip_autosave_sop("其它标题", "mode=one_click_health_analysis")
    assert skip2
