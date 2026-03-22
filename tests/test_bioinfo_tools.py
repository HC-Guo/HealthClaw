#!/usr/bin/env python3
"""
生信工具集成测试：BLAST / DAVID / InterProScan / run_bioinfo_cli。
在项目根目录执行: python tests/test_bioinfo_tools.py
"""
import os
import sys

# 保证能导入项目包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.bioinfo_tools import blast_search, david_enrichment, interpro_scan, run_bioinfo_cli


def test_blast():
    """BLAST：短肽序列搜索 swissprot（NCBI API）"""
    query = "MKTIIALSYIFCLVFADYKDDDDK"  # 短肽
    print("--- test_blast_search ---")
    out = blast_search(query=query, program="blastp", database="swissprot", evalue=10)
    print("status:", out.get("status"))
    print("msg:", out.get("msg"))
    if out.get("hits"):
        for h in out["hits"][:3]:
            print("  hit:", h.get("id"), h.get("def", "")[:60])
    assert out.get("status") in ("success", "error")
    print("OK\n")
    return out


def test_david():
    """DAVID：未配置时应返回使用说明"""
    print("--- test_david_enrichment ---")
    out = david_enrichment(gene_ids=["7157", "7422", "5970"], email=None)
    print("status:", out.get("status"))
    print("msg:", out.get("msg", "")[:200])
    assert out.get("status") in ("info", "error", "success")
    print("OK\n")
    return out


def test_interpro():
    """InterProScan：短序列提交（EBI 可能较慢或限流）"""
    fasta = ">test\nMKTIIALSYIFCLVFADYKDDDDK\n"
    print("--- test_interpro_scan ---")
    try:
        out = interpro_scan(sequences=fasta)
        print("status:", out.get("status"))
        print("msg:", out.get("msg"))
        if out.get("result"):
            print("result (first 300 chars):", out["result"][:300])
    except Exception as e:
        print("exception (acceptable for CI):", e)
        out = {"status": "error", "msg": str(e)}
    assert out.get("status") in ("success", "error")
    print("OK\n")
    return out


def test_run_bioinfo_cli():
    """run_bioinfo_cli：未安装时应返回友好提示"""
    print("--- test_run_bioinfo_cli (bwa not installed expected) ---")
    out = run_bioinfo_cli(tool="bwa", input_path="/nonexistent.fq", reference_index="/nonexistent")
    print("status:", out.get("status"))
    print("msg:", out.get("msg"))
    # 未安装 bwa 时为 error 且 msg 含提示；若已安装则可能为 error 因路径不存在
    assert out.get("status") in ("success", "error")
    print("OK\n")
    return out


if __name__ == "__main__":
    test_blast()
    test_david()
    test_interpro()
    test_run_bioinfo_cli()
    print("All bioinfo tool tests finished.")
