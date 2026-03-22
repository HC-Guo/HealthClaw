"""
生信工具后端：BLAST / DAVID / InterProScan API 封装 + CLI 统一调用。
供 Agent 通过 blast_search、david_enrichment、interpro_scan、run_bioinfo_cli 使用。
"""
import os
import re
import time
import json
import subprocess
import tempfile
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# 可选：有 requests 时用 requests，否则用 urllib
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ---------- BLAST (NCBI URL API) ----------
BLAST_API_BASE = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"


def blast_search(query, program="blastp", database="swissprot", evalue=1e-5,
                 email="agent@local", tool_name="SEDA-bioinfo", max_wait_seconds=120):
    """
    使用 NCBI BLAST 常见 URL API 提交搜索并轮询结果。
    query: 序列字符串或单条 FASTA（可含 >id 行）
    program: blastn, blastp, blastx, tblastn, tblastx
    database: nr, swissprot, nt 等
    返回: {"status": "success"|"error", "hits": [...], "raw_xml": "...", "msg": "..."}
    """
    # 清理 query：保留单条序列
    q = (query or "").strip()
    if q.startswith(">"):
        lines = q.split("\n")
        seq = "".join(l for l in lines[1:] if l.strip()).replace(" ", "")
    else:
        seq = re.sub(r"\s+", "", q)
    if not seq or len(seq) < 10:
        return {"status": "error", "msg": "query 序列过短或为空"}

    params_put = {
        "CMD": "Put",
        "PROGRAM": program,
        "DATABASE": database,
        "QUERY": seq,
        "EXPECT": str(evalue),
        "EMAIL": email,
        "TOOL": tool_name,
    }
    url_put = BLAST_API_BASE + "?" + urlencode(params_put)

    try:
        if _HAS_REQUESTS:
            r = requests.get(url_put, timeout=30)
            body = r.text
        else:
            req = Request(url_put, headers={"User-Agent": "SEDA-bioinfo/1.0"})
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, OSError) as e:
        return {"status": "error", "msg": f"BLAST 提交失败: {e}"}

    # 解析 RID 和 RTOE
    rid = re.search(r"RID\s*=\s*(\S+)", body)
    rtoe = re.search(r"RTOE\s*=\s*(\d+)", body)
    if not rid:
        return {"status": "error", "msg": "BLAST 未返回 RID", "raw": body[:500]}
    rid = rid.group(1).strip()
    wait_max = min(max_wait_seconds, int(rtoe.group(1)) + 10 if rtoe else 120)

    # 轮询结果（NCBI 建议至少间隔 10 秒）
    params_get = {"CMD": "Get", "RID": rid, "FORMAT_TYPE": "XML", "ALIGNMENTS": 50}
    url_get = BLAST_API_BASE + "?" + urlencode(params_get)
    start = time.time()
    last_status = ""

    while time.time() - start < wait_max:
        time.sleep(max(10, 1))  # 至少 10 秒再查
        try:
            if _HAS_REQUESTS:
                r = requests.get(url_get, timeout=60)
                body = r.text
            else:
                req = Request(url_get, headers={"User-Agent": "SEDA-bioinfo/1.0"})
                with urlopen(req, timeout=60) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            last_status = str(e)
            continue

        if "Status=" in body:
            status = re.search(r"Status=(\w+)", body)
            if status and status.group(1) == "READY":
                # 解析简单 hit 列表（从 XML 中摘取）
                hits = []
                for hit in re.finditer(r"<Hit_id>([^<]+)</Hit_id>\s*<Hit_def>([^<]*)</Hit_def>", body):
                    hits.append({"id": hit.group(1), "def": hit.group(2)})
                for hit in re.finditer(r"<Hsp_evalue>([^<]+)</Hsp_evalue>\s*<Hsp_identity>([^<]+)</Hsp_identity>", body):
                    pass  # 可与 hits 合并
                return {
                    "status": "success",
                    "rid": rid,
                    "hits": hits[:20],
                    "raw_xml": body[:8000],
                    "msg": f"找到 {len(hits)} 个 hit(s)"
                }
            last_status = status.group(1) if status else "UNKNOWN"
        if "Error" in body or "error" in body.lower():
            return {"status": "error", "msg": "BLAST 返回错误", "raw": body[:1000]}

    return {"status": "error", "msg": f"BLAST 超时(>{wait_max}s)，最后状态: {last_status}", "rid": rid}


# ---------- DAVID 富集（需邮箱注册，此处返回说明 + 占位） ----------
def david_enrichment(gene_ids, id_type="ENTREZ_GENE_ID", species="human",
                     categories=None, email=None):
    """
    DAVID 富集分析。官方需 Web Service 注册与 API key。
    若未配置 email/key，返回使用说明；否则可扩展为真实 HTTP 调用。
    """
    if not gene_ids:
        return {"status": "error", "msg": "gene_ids 不能为空"}
    categories = categories or ["GOTERM_BP_FAT", "KEGG_PATHWAY"]
    if not email:
        return {
            "status": "info",
            "msg": "DAVID 需在 https://david.ncifcrf.gov 用邮箱注册后使用 Web Service API。",
            "usage": "将基因 ID 列表上传至 DAVID 网站，或使用 R 包 RDAVIDWebService 在 code_run 中调用。",
            "gene_count": len(gene_ids),
            "suggested_categories": categories,
        }
    # 占位：后续可接 DAVID API
    return {"status": "info", "msg": "DAVID API 未配置，请用 browse_and_learn 或 code_run(R) 完成富集。", "gene_count": len(gene_ids)}


# ---------- InterProScan (EBI REST) ----------
# EBI 示例: POST https://www.ebi.ac.uk/Tools/services/rest/iprscan5/run  (序列)
# 然后 GET .../status/{jobId}, .../result/{jobId}
INTERPRO_REST = "https://www.ebi.ac.uk/Tools/services/rest/iprscan5"


def interpro_scan(sequences, appl=None, email="agent@local"):
    """
    提交蛋白序列到 EBI InterProScan 5。sequences: FASTA 字符串或序列列表。
    email: EBI 要求提供联系邮箱。
    返回: {"status": "success"|"error", "job_id": "...", "result": "...", "msg": "..."}
    """
    if isinstance(sequences, list):
        fasta = "\n".join(f">seq{i}\n{s}" for i, s in enumerate(sequences))
    else:
        fasta = (sequences or "").strip()
    if not fasta or ">" not in fasta:
        return {"status": "error", "msg": "请提供 FASTA 格式序列（含 >id 行）"}

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"sequence": fasta, "email": email or "agent@local"}
    if appl:
        data["appl"] = appl

    try:
        if _HAS_REQUESTS:
            r = requests.post(f"{INTERPRO_REST}/run", data=data, headers=headers, timeout=60)
            body = r.text.strip()
        else:
            req = Request(
                f"{INTERPRO_REST}/run",
                data=urlencode(data).encode(),
                method="POST",
                headers={**headers, "User-Agent": "SEDA-bioinfo/1.0"}
            )
            with urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8", errors="replace").strip()
    except Exception as e:
        return {"status": "error", "msg": f"InterProScan 提交失败: {e}"}

    if not body or len(body) > 100:
        return {"status": "error", "msg": f"异常返回: {body[:200]}"}
    job_id = body

    # 轮询状态
    for _ in range(60):
        time.sleep(5)
        try:
            if _HAS_REQUESTS:
                r = requests.get(f"{INTERPRO_REST}/status/{job_id}", timeout=30)
                status = r.text.strip()
            else:
                req = Request(f"{INTERPRO_REST}/status/{job_id}", headers={"User-Agent": "SEDA-bioinfo/1.0"})
                with urlopen(req, timeout=30) as resp:
                    status = resp.read().decode("utf-8", errors="replace").strip()
        except Exception as e:
            return {"status": "error", "msg": f"状态查询失败: {e}", "job_id": job_id}
        if status == "RUNNING" or status == "PENDING":
            continue
        if status == "FINISHED":
            try:
                if _HAS_REQUESTS:
                    r = requests.get(f"{INTERPRO_REST}/result/{job_id}/tsv", timeout=60)
                    result = r.text
                else:
                    req = Request(f"{INTERPRO_REST}/result/{job_id}/tsv", headers={"User-Agent": "SEDA-bioinfo/1.0"})
                    with urlopen(req, timeout=60) as resp:
                        result = resp.read().decode("utf-8", errors="replace")
            except Exception as e:
                return {"status": "error", "msg": f"结果获取失败: {e}", "job_id": job_id}
            return {"status": "success", "job_id": job_id, "result": result[:15000], "msg": "InterProScan 完成"}
        return {"status": "error", "msg": f"Job 状态异常: {status}", "job_id": job_id}

    return {"status": "error", "msg": "InterProScan 超时", "job_id": job_id}


# ---------- CLI 统一入口 ----------
BIOINFO_CLI = {
    "bwa": {"cmd": "bwa", "check": "bwa mem", "hint": "请安装 BWA 并配置 PATH"},
    "hisat2": {"cmd": "hisat2", "check": "hisat2", "hint": "请安装 HISAT2 并配置 PATH"},
    "star": {"cmd": "STAR", "check": "STAR", "hint": "请安装 STAR 并配置 PATH"},
    "gatk": {"cmd": "gatk", "check": "gatk", "hint": "请安装 GATK 并配置 PATH"},
    "prokka": {"cmd": "prokka", "check": "prokka", "hint": "请安装 Prokka 并配置 PATH"},
    "spades": {"cmd": "spades.py", "check": "spades.py", "hint": "请安装 SPAdes 并配置 PATH"},
    "deseq2": {"cmd": "Rscript", "check": "Rscript", "hint": "请安装 R 并安装 DESeq2；或通过 code_run 执行 R 脚本"},
    "alphafold": {"cmd": "python", "check": "python", "hint": "AlphaFold 需单独环境与 GPU，建议用 code_run 按官方文档执行"},
}


def run_bioinfo_cli(tool, input_path=None, input_path2=None, output_dir=None,
                    extra_args=None, reference_index=None, timeout=3600):
    """
    统一调用生信 CLI。tool: bwa|hisat2|star|gatk|prokka|spades|deseq2|alphafold。
    input_path: 主输入（FASTA/FQ 等）；input_path2: 双端时第二端。
    output_dir: 输出目录；extra_args: 额外参数字符串或列表。
    reference_index: 比对类工具所需参考索引前缀。
    返回: {"status": "success"|"error", "stdout": "", "stderr": "", "msg": ""}
    """
    tool = (tool or "").strip().lower()
    if tool not in BIOINFO_CLI:
        return {"status": "error", "msg": f"未知工具 {tool}，可选: {list(BIOINFO_CLI.keys())}"}

    info = BIOINFO_CLI[tool]
    cmd_base = info["cmd"]
    try:
        subprocess.run([cmd_base, "--version"] if cmd_base != "python" else [cmd_base, "-c", "print(1)"],
                      capture_output=True, timeout=5, check=False)
    except FileNotFoundError:
        return {"status": "error", "msg": info["hint"]}
    except subprocess.TimeoutExpired:
        pass

    out_dir = output_dir or tempfile.mkdtemp(prefix="bioinfo_")
    os.makedirs(out_dir, exist_ok=True)
    extra = extra_args if isinstance(extra_args, list) else ([extra_args] if extra_args else [])

    if tool == "bwa":
        if not reference_index or not input_path:
            return {"status": "error", "msg": "bwa 需要 reference_index 与 input_path"}
        cmd = ["bwa", "mem", reference_index, input_path]
        if input_path2:
            cmd.append(input_path2)
        cmd.extend(extra)
    elif tool == "hisat2":
        if not reference_index or not input_path:
            return {"status": "error", "msg": "hisat2 需要 reference_index 与 input_path"}
        cmd = ["hisat2", "-x", reference_index, "-1", input_path]
        if input_path2:
            cmd.append("-2")
            cmd.append(input_path2)
        cmd.extend(["-S", os.path.join(out_dir, "aligned.sam")])
        cmd.extend(extra)
    elif tool == "star":
        if not reference_index or not input_path:
            return {"status": "error", "msg": "STAR 需要 reference_index 与 input_path"}
        cmd = ["STAR", "--genomeDir", reference_index, "--readFilesIn", input_path]
        if input_path2:
            cmd[cmd.index("--readFilesIn") + 1] += "," + input_path2
        cmd.extend(["--outFileNamePrefix", os.path.join(out_dir, "")])
        cmd.extend(extra)
    elif tool == "prokka":
        if not input_path:
            return {"status": "error", "msg": "prokka 需要 input_path (基因组 FASTA)"}
        cmd = ["prokka", "--outdir", out_dir, input_path] + extra
    elif tool == "spades":
        if not input_path:
            return {"status": "error", "msg": "spades 需要 input_path (-1/-2 或 -s)"}
        cmd = ["spades.py", "-o", out_dir, "-1", input_path]
        if input_path2:
            cmd.extend(["-2", input_path2])
        cmd.extend(extra)
    else:
        return {"status": "error", "msg": f"{tool} 需在 code_run 中按 L3 SOP 手动构造命令；本接口仅支持 bwa/hisat2/star/prokka/spades"}

    try:
        result = subprocess.run(
            cmd,
            cwd=out_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = (result.stdout or "")[:8000]
        stderr = (result.stderr or "")[:4000]
        ok = result.returncode == 0
        return {
            "status": "success" if ok else "error",
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode,
            "output_dir": out_dir,
            "msg": "完成" if ok else f"退出码 {result.returncode}",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "msg": f"执行超时({timeout}s)", "output_dir": out_dir}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
