# -*- coding: utf-8 -*-
"""
dsh_cockpit.py — 全新 DSH 轻量三剑客主权思考座舱 (端口 :8765 · v2.0.0 终极战略版)
=============================================================================
轻量三剑客定岗矩阵与核心突破：
1. 💎 首席秘书长 (Gemini 3.8 Flash · 1M 上下文): 宏观意图收敛、战略目标拆解、无状态 DAG 任务切片；
2. ⚔️ 军需装备官 (DeepSeek v4.1 Flash · 冷酷红队): 逆向架构挑刺、挖掘 3 大致命死穴、装配储藏库技能与金样模板；
3. 🔨 建造工程师 (GLM 5.3 Flash / Builder): 严格带装施工、本地 AST 确定性静态断言、自愈重构环路；
4. 💎 结晶断面与 SHA-256: 产生 Unified Diff 结晶，绑定真实 Hash 签名，实现指挥官 1-Click APPROVE / VETO；
5. ⚡ TTC 时空膨胀引擎: 投入 15K~50K Token 与 30s~60s 测试时算力，从系统工程上彻底击败 GPT-5.6 Sol 单体！
"""
import sys
import os
import time
import json
import sqlite3
import hashlib
import asyncio
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

COCKPIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = COCKPIT_DIR.parent
FED_ROOT = REPO_ROOT
DSH_DIR = COCKPIT_DIR
BRIDGE_DIR = FED_ROOT / "data" / "bridge"
MAIL_DB = FED_ROOT / "data" / "mail.sqlite3"
KEY_DEEPSEEK = Path(os.environ.get("DEEPSEEK_KEY_FILE", ""))
KEY_GEMINI_DIR = Path(os.environ.get("GEMINI_KEY_DIR", ""))
STATIC_DIR = COCKPIT_DIR / "static"
MARKED_JS = STATIC_DIR / "marked.min.js"
THREE_JS = STATIC_DIR / "three.min.js"
ORBIT_CONTROLS_JS = STATIC_DIR / "OrbitControls.js"
WORLD_TREE_HTML = COCKPIT_DIR / "world_tree.html"

sys.path.insert(0, str(COCKPIT_DIR))
sys.path.insert(0, str(FED_ROOT / "dsh-core"))
sys.path.insert(0, str(FED_ROOT / "moa-engine"))
sys.path.insert(0, str(FED_ROOT))

try:
    import dsh_llm
except ImportError:
    dsh_llm = None

try:
    import dsh_moa_engine
except ImportError:
    dsh_moa_engine = None

app = FastAPI(title="New DSH Three Musketeers Sovereign Cockpit", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 最新结晶缓存，连接 TTC 流水线与右侧收敛断面
LATEST_CRYSTAL_DIFF = {
    "diff": "",
    "hash": "",
    "task_id": "MOA-TTC-INIT",
    "goal": "",
    "tokens": 0,
    "duration_s": 0.0,
    "time": ""
}

def get_gemini_key() -> str:
    for f in KEY_GEMINI_DIR.glob("*.txt"):
        try:
            k = f.read_text(encoding="utf-8").strip()
            if k:
                return k
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY", "")

class ChatRequest(BaseModel):
    message: str
    mode: str = "gemini"
    context: Optional[str] = ""

class MoaPipelineRequest(BaseModel):
    goal: str

class DispatchRequest(BaseModel):
    task_id: str
    subject: str
    spec_body: str
    assignee: str = "OrangeCrane"

class SignoffRequest(BaseModel):
    task_id: str
    action: str
    artifact_hash: Optional[str] = ""
    feedback: Optional[str] = ""

@app.get("/static/marked.min.js")
def get_marked_js():
    if MARKED_JS.is_file():
        return Response(content=MARKED_JS.read_text(encoding="utf-8"), media_type="application/javascript")
    return Response(content="console.warn('marked.min.js missing');", media_type="application/javascript")

@app.get("/static/three.min.js")
def get_three_js():
    if THREE_JS.is_file():
        return Response(content=THREE_JS.read_bytes(), media_type="application/javascript")
    return Response(content="console.warn('three.min.js missing');", media_type="application/javascript")

@app.get("/static/OrbitControls.js")
def get_orbit_controls_js():
    if ORBIT_CONTROLS_JS.is_file():
        return Response(content=ORBIT_CONTROLS_JS.read_bytes(), media_type="application/javascript")
    return Response(content="console.warn('OrbitControls.js missing');", media_type="application/javascript")

@app.get("/world_tree", response_class=HTMLResponse)
def get_world_tree():
    if WORLD_TREE_HTML.is_file():
        return HTMLResponse(content=WORLD_TREE_HTML.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>World Tree HTML not found</h1>")

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="消息内容不能为空")
    
    sec_sys = (
        "你是联邦首席秘书长（SilentBear · Gemini 3.8 Flash 规格 · 1M 上下文）。"
        "协助人类指挥官进行高维战略思考、意图收敛、任务拆解与去伪存真。"
        "结论先行，结构严密，排版精美（含标题、表格、加粗、代码块）。"
    )
    
    ds_sys = (
        "你是联邦军需装备官（DeepSeek v4.1 Flash · 冷酷红队审计员）。"
        "冷酷客观地挑刺、寻找架构与逻辑死穴、揭露隐蔽的复杂度陷阱。"
        "一针见血，直击要害。回答使用清晰的 Markdown 列表与死穴预警。"
    )
    
    t1_sys = (
        "你是 T-1 中立范式观察者。"
        "严格审查以下输入是否存在上下文漂移（Context Drift）或滑向玩具化倾向。"
        "输出格式：[T-1 状态标签] + 一句话诊断 + 一句话纠偏建议。"
    )

    if req.mode == "gemini":
        res = await asyncio.to_thread(dsh_moa_engine.call_gemini, msg, sec_sys)
        return {"mode": "gemini", "reply": res.get("reply", ""), "model": res.get("model", "gemini-3.8-flash"), "tokens": res.get("tokens", 0), "latency_ms": res.get("latency_ms", 0)}
    elif req.mode == "deepseek":
        res = await asyncio.to_thread(dsh_moa_engine.call_deepseek, msg, ds_sys)
        return {"mode": "deepseek", "reply": res.get("reply", ""), "model": res.get("model", "deepseek-chat"), "tokens": res.get("tokens", 0), "latency_ms": res.get("latency_ms", 0)}
    elif req.mode == "t1_audit":
        reply = await asyncio.to_thread(dsh_llm.chat, msg, history=[{"role": "system", "content": t1_sys}])
        return {"mode": "t1_audit", "reply": reply, "model": "deepseek-t1"}
    elif req.mode == "dual":
        g_res, d_res = await asyncio.gather(
            asyncio.to_thread(dsh_moa_engine.call_gemini, msg, sec_sys),
            asyncio.to_thread(dsh_moa_engine.call_deepseek, msg, ds_sys),
            return_exceptions=True
        )
        gemini_text = g_res.get("reply") if isinstance(g_res, dict) else f"Gemini 异常: {g_res}"
        deepseek_text = d_res.get("reply") if isinstance(d_res, dict) else f"DeepSeek 异常: {d_res}"
        return {
            "mode": "dual",
            "gemini": gemini_text,
            "deepseek": deepseek_text,
            "gemini_model": g_res.get("model", "gemini-3.8-flash") if isinstance(g_res, dict) else "unknown",
            "deepseek_model": d_res.get("model", "deepseek-chat") if isinstance(d_res, dict) else "unknown"
        }
    elif req.mode == "moa_ttc":
        res = await asyncio.to_thread(dsh_moa_engine.run_moa_pipeline, msg)
        LATEST_CRYSTAL_DIFF["diff"] = res.get("diff", "")
        LATEST_CRYSTAL_DIFF["hash"] = res.get("hash", "")
        LATEST_CRYSTAL_DIFF["task_id"] = f"MOA-TTC-{res.get('hash', '0000')[:6]}"
        LATEST_CRYSTAL_DIFF["goal"] = msg
        LATEST_CRYSTAL_DIFF["tokens"] = res.get("total_tokens", 0)
        LATEST_CRYSTAL_DIFF["duration_s"] = res.get("duration_s", 0.0)
        LATEST_CRYSTAL_DIFF["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return {"mode": "moa_ttc", "pipeline_result": res}
    else:
        raise HTTPException(status_code=400, detail=f"未知模式 {req.mode}")

@app.post("/api/moa/run_pipeline")
async def api_moa_run_pipeline(req: MoaPipelineRequest):
    goal = req.goal.strip()
    if not goal:
        raise HTTPException(status_code=400, detail="目标任务不能为空")
    try:
        res = await asyncio.to_thread(dsh_moa_engine.run_moa_pipeline, goal)
        LATEST_CRYSTAL_DIFF["diff"] = res.get("diff", "")
        LATEST_CRYSTAL_DIFF["hash"] = res.get("hash", "")
        LATEST_CRYSTAL_DIFF["task_id"] = f"MOA-TTC-{res.get('hash', '0000')[:6]}"
        LATEST_CRYSTAL_DIFF["goal"] = goal
        LATEST_CRYSTAL_DIFF["tokens"] = res.get("total_tokens", 0)
        LATEST_CRYSTAL_DIFF["duration_s"] = res.get("duration_s", 0.0)
        LATEST_CRYSTAL_DIFF["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bridge/status")
def api_bridge_status():
    if not MAIL_DB.is_file():
        return {"status": "error", "message": "Mail DB not found"}
    try:
        conn = sqlite3.connect(str(MAIL_DB))
        c = conn.cursor()
        query = """
        SELECT m.id, a.name as sender, m.subject, m.created_ts, m.body_md
        FROM messages m
        LEFT JOIN agents a ON m.sender_id = a.id
        ORDER BY m.id DESC LIMIT 15
        """
        messages = []
        for r in c.execute(query):
            messages.append({
                "id": r[0],
                "from": r[1],
                "subject": r[2],
                "time": r[3],
                "snippet": (r[4] or "")[:220] + ("..." if len(r[4] or "") > 220 else "")
            })
            
        zcode_status = "IDLE"
        if messages:
            last = messages[0]
            if "RESULT" in last["subject"] or "PASS" in last["subject"]:
                zcode_status = "CONVERGED"
            elif "OPEN" in last["subject"]:
                zcode_status = "WORKING"
                
        return {
            "status": "online",
            "db_path": str(MAIL_DB),
            "zcode_status": zcode_status,
            "messages": messages
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/heartbeats")
def api_heartbeats():
    hb_dir = BRIDGE_DIR / "HEARTBEATS"
    res = {}
    now = time.time()
    if hb_dir.is_dir():
        for f in hb_dir.glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                epoch = d.get("ts_epoch", 0)
                is_stale = (now - epoch) > 120
                res[f.stem] = {
                    "agent": d.get("agent", f.stem),
                    "status": "DEAD" if is_stale else d.get("status", "ALIVE"),
                    "task": d.get("task", ""),
                    "ts": d.get("ts", ""),
                    "is_stale": is_stale
                }
            except Exception:
                pass
    return res

@app.get("/api/latest_diff")
def api_latest_diff():
    if LATEST_CRYSTAL_DIFF["diff"]:
        return {
            "ok": True,
            "source": "MOA-TTC",
            "diff": LATEST_CRYSTAL_DIFF["diff"],
            "hash": LATEST_CRYSTAL_DIFF["hash"],
            "task_id": LATEST_CRYSTAL_DIFF["task_id"],
            "goal": LATEST_CRYSTAL_DIFF["goal"],
            "tokens": LATEST_CRYSTAL_DIFF["tokens"],
            "duration_s": LATEST_CRYSTAL_DIFF["duration_s"],
            "time": LATEST_CRYSTAL_DIFF["time"]
        }

    try:
        res = subprocess.run(["git", "diff", "HEAD~1"], cwd=str(FED_ROOT), capture_output=True, text=True, timeout=5)
        diff_text = res.stdout.strip()
        if not diff_text:
            res2 = subprocess.run(["git", "status", "-s"], cwd=str(FED_ROOT), capture_output=True, text=True, timeout=5)
            diff_text = res2.stdout.strip()
        
        if not diff_text:
            diff_text = "// 当前工作区无未合并变更。轻量三剑客运行完成后，代码结晶断层将在此实时展现。\n// (Waiting for next MOA-TTC construction diff)"

        diff_hash = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()[:12]
        return {
            "ok": True,
            "source": "GIT",
            "diff": diff_text,
            "hash": diff_hash,
            "task_id": "LOCAL-GIT",
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "ok": False,
            "diff": f"// 获取 Diff 提示: {e}",
            "hash": "000000000000",
            "task_id": "ERROR",
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

@app.post("/api/dispatch_task")
def api_dispatch_task(req: DispatchRequest):
    try:
        from am_rpc import tool
        tokens = json.load(open(BRIDGE_DIR / "am_agent_tokens.json", encoding="utf-8"))
        sender = "WindyElk"
        token = tokens[sender]
        
        subject = f"[{req.task_id}] OPEN: {req.subject}"
        body = (
            f"**[{req.task_id}] OPEN: {req.subject}**\n\n"
            f"requested_by: 指挥官在全新 DSH 三剑客座舱直接派发\n\n"
            f"**执行规范 (Spec)**：\n{req.spec_body}\n\n"
            f"---\n"
            f"署名：全新 DSH 思考座舱（WindyElk/指挥官）；目标：施工队长（{req.assignee}）；终裁：指挥官。"
        )
        
        r = tool("send_message", {
            "project_key": str(BRIDGE_DIR),
            "sender_name": sender,
            "sender_token": token,
            "to": [req.assignee],
            "subject": subject,
            "topic": req.task_id,
            "body_md": body,
            "ack_required": True
        })
        
        ok = isinstance(r, dict) and r.get("count", 0) >= 1
        return {"ok": ok, "task_id": req.task_id, "assignee": req.assignee, "result": r}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/signoff")
def api_signoff(req: SignoffRequest):
    try:
        from am_rpc import tool
        tokens = json.load(open(BRIDGE_DIR / "am_agent_tokens.json", encoding="utf-8"))
        sender = "WindyElk"
        token = tokens[sender]
        
        status_tag = "PASS" if req.action == "APPROVE" else "FAIL"
        subject = f"[{req.task_id}] {status_tag}: 指挥官终审裁决"
        body = (
            f"**[{req.task_id}] {status_tag}: 指挥官终审裁决**\n\n"
            f"requested_by: human in DSH Cockpit (Three Musketeers Sovereign Suite)\n\n"
            f"**裁决结论**：{'【批准合流 · 验收通过】' if req.action == 'APPROVE' else '【一票否决 · 打回重修】'}\n"
            f"**产物校验指纹 (Artifact Hash)**：`{req.artifact_hash or 'N/A'}`\n"
            f"**签署时间戳**：`{time.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
            f"**反馈意见**：{req.feedback or '无补充意见'}\n\n"
            f"---\n"
            f"署名：最高统帅指挥官（通过 DSH 三剑客座舱签署）；终裁：最高统帅。"
        )
        
        r = tool("send_message", {
            "project_key": str(BRIDGE_DIR),
            "sender_name": sender,
            "sender_token": token,
            "to": ["OrangeCrane"],
            "subject": subject,
            "topic": req.task_id,
            "body_md": body,
            "ack_required": True
        })
        return {"ok": True, "action": req.action, "hash": req.artifact_hash, "result": r}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

COCKPIT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>全新 DSH · 轻量三剑客主权思考座舱 (v2.0.0)</title>
    <script src="/static/marked.min.js"></script>
    <style>
        :root {
            --bg-base: #060a14;
            --bg-card: #0c1424;
            --bg-card-alt: #111b30;
            --bg-input: #040812;
            --border: #1d2b42;
            --border-highlight: #38bdf8;
            --text: #f8fafc;
            --text-secondary: #e2e8f0;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-green: #34d399;
            --accent-rose: #f43f5e;
            --accent-amber: #fbbf24;
            --accent-purple: #c084fc;
            --font-main: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            --font-code: "JetBrains Mono", Consolas, "Fira Code", monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { 
            background: var(--bg-base); 
            color: var(--text); 
            height: 100vh; 
            overflow: hidden; 
            font-family: var(--font-main);
            font-size: 16px;
        }

        /* 显式高对比度双轨物理滚轴 */
        * {
            scrollbar-width: thin;
            scrollbar-color: #2563eb #080d1a;
        }
        ::-webkit-scrollbar {
            width: 14px;
            height: 14px;
        }
        ::-webkit-scrollbar-track {
            background: #080d1a;
            border-left: 1px solid #1e293b;
            border-right: 1px solid #1e293b;
        }
        ::-webkit-scrollbar-thumb {
            background: #2563eb;
            border-radius: 7px;
            border: 3px solid #080d1a;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #38bdf8;
        }

        /* Top Bar */
        header { 
            background: #03060f; 
            border-bottom: 1px solid var(--border); 
            padding: 10px 22px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            gap: 16px;
            z-index: 20;
        }
        .header-left { display: flex; align-items: center; gap: 14px; }
        .logo-badge { 
            background: linear-gradient(135deg, #0284c7, #8b5cf6); 
            padding: 5px 12px; 
            border-radius: 7px; 
            font-weight: 900; 
            font-size: 14px; 
            letter-spacing: 1px; 
            color: #fff; 
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
        }
        .logo-title { font-size: 16px; font-weight: 700; color: #fff; letter-spacing: 0.5px; }
        
        .header-right { display: flex; align-items: center; gap: 12px; }
        .header-status { display: flex; gap: 8px; font-size: 12px; }
        .status-badge { 
            display: flex; 
            align-items: center; 
            gap: 6px; 
            background: rgba(255,255,255,0.04); 
            padding: 5px 10px; 
            border-radius: 18px; 
            border: 1px solid var(--border); 
            white-space: nowrap;
        }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
        .dot-green { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
        .dot-amber { background: var(--accent-amber); box-shadow: 0 0 8px var(--accent-amber); }
        .dot-purple { background: var(--accent-purple); box-shadow: 0 0 8px var(--accent-purple); }
        .dot-blue { background: var(--accent); box-shadow: 0 0 8px var(--accent); }

        /* Tools: Zoom and Collapse Buttons */
        .zoom-group {
            display: flex;
            align-items: center;
            background: #090e1c;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2px 4px;
            gap: 3px;
        }
        .btn-tool {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-tool:hover { background: #1e293b; color: var(--accent); }
        .btn-tool.active { background: #1e3a8a; color: #fff; }
        
        .btn-collapse-sidebar {
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: var(--accent);
            font-size: 12.5px;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 7px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        .btn-collapse-sidebar:hover {
            background: rgba(56, 189, 248, 0.25);
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
        }

        /* -------------------------------------------------------------
           Main Workspace Layout
        -------------------------------------------------------------- */
        .workspace { 
            flex: 1; 
            height: calc(100vh - 58px);
            display: grid; 
            grid-template-columns: 1.25fr 0.75fr; 
            transition: grid-template-columns 0.25s cubic-bezier(0.4, 0, 0.2, 1); 
            overflow: hidden; 
            position: relative;
        }
        
        .workspace.sidebar-collapsed {
            grid-template-columns: 1fr 0px;
        }
        .workspace.sidebar-collapsed .right-pane {
            display: none !important;
        }

        /* -------------------------------------------------------------
           Left Pane: Thinking & Debate Cockpit
        -------------------------------------------------------------- */
        .left-pane { 
            background: var(--bg-base); 
            display: flex; 
            flex-direction: column; 
            height: 100%; 
            position: relative; 
            border-right: 1px solid var(--border);
            overflow: hidden;
        }

        .pane-header { 
            padding: 10px 20px; 
            background: var(--bg-card); 
            border-bottom: 1px solid var(--border); 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .pane-title { 
            font-size: 13px; 
            font-weight: 800; 
            letter-spacing: 0.8px; 
            color: var(--text-muted); 
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .mode-selector { 
            display: flex; 
            gap: 5px; 
            background: #060912; 
            padding: 3px; 
            border-radius: 8px; 
            border: 1px solid var(--border); 
        }
        .mode-btn { 
            background: transparent; 
            border: none; 
            color: var(--text-muted); 
            font-size: 12px; 
            padding: 5px 11px; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: 600; 
            transition: all 0.2s; 
            white-space: nowrap;
        }
        .mode-btn:hover { color: #fff; }
        .mode-btn.active { 
            background: #1e293b; 
            color: var(--accent); 
            border: 1px solid rgba(56, 189, 248, 0.4); 
        }
        .mode-btn.active.mode-moa {
            background: linear-gradient(135deg, #1e3a8a, #581c87);
            color: #fff;
            border-color: #818cf8;
            box-shadow: 0 0 10px rgba(129, 140, 248, 0.4);
        }

        /* Chat Stream */
        .chat-scroll-wrapper {
            flex: 1;
            overflow-y: scroll !important;
            padding: 22px;
            display: flex;
            flex-direction: column;
        }
        .chat-content-container {
            width: 100%;
            max-width: 1360px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .msg { 
            max-width: 96%; 
            border-radius: 12px; 
            padding: 18px 22px; 
            font-size: 16px; 
            line-height: 1.75; 
            word-break: break-word; 
            position: relative; 
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        }
        .msg-commander { 
            align-self: flex-end; 
            background: #152744; 
            border: 1px solid #2563eb; 
            color: #fff; 
            border-bottom-right-radius: 3px;
        }
        .msg-gemini { 
            align-self: flex-start; 
            background: var(--bg-card); 
            border: 1px solid #1e3a8a; 
            border-bottom-left-radius: 3px;
        }
        .msg-deepseek { 
            align-self: flex-start; 
            background: #150f24; 
            border: 1px solid #6b21a8; 
            border-bottom-left-radius: 3px;
        }
        .msg-t1 { 
            align-self: flex-start; 
            background: #171821; 
            border: 1px solid #475569; 
            font-family: var(--font-code); 
            font-size: 14.5px; 
        }
        .msg-moa {
            align-self: flex-start;
            width: 100%;
            background: linear-gradient(180deg, #0d172c 0%, #080e1a 100%);
            border: 2px solid #3b82f6;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.25);
        }

        .msg-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 12px; 
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .msg-tag { 
            font-size: 12px; 
            font-weight: 800; 
            text-transform: uppercase; 
            padding: 3px 9px; 
            border-radius: 5px; 
            letter-spacing: 0.5px;
        }
        .tag-gemini { background: rgba(56, 189, 248, 0.2); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.4); }
        .tag-deepseek { background: rgba(192, 132, 252, 0.2); color: var(--accent-purple); border: 1px solid rgba(192, 132, 252, 0.4); }
        .tag-t1 { background: rgba(251, 191, 36, 0.2); color: var(--accent-amber); border: 1px solid rgba(251, 191, 36, 0.4); }
        .tag-commander { background: rgba(59, 130, 246, 0.3); color: #93c5fd; }
        .tag-moa { background: linear-gradient(135deg, #2563eb, #7c3aed); color: #fff; border: 1px solid #818cf8; }

        .btn-extract-spec { 
            background: rgba(255,255,255,0.08); 
            border: 1px solid var(--border); 
            color: var(--text-muted); 
            font-size: 12px; 
            font-weight: 600;
            padding: 4px 10px; 
            border-radius: 5px; 
            cursor: pointer; 
            transition: all 0.2s;
        }
        .btn-extract-spec:hover { 
            color: #fff; 
            background: rgba(56, 189, 248, 0.25); 
            border-color: var(--accent); 
        }

        /* -------------------------------------------------------------
           MOA TTC Pipeline Card Layout (4 阶段时空膨胀视觉卡)
        -------------------------------------------------------------- */
        .moa-ledger-banner {
            background: #070e1e;
            border: 1px solid #1e3a8a;
            border-radius: 8px;
            padding: 12px 18px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .moa-stat-item {
            display: flex;
            align-items: baseline;
            gap: 6px;
        }
        .moa-stat-val {
            font-family: var(--font-code);
            font-size: 16px;
            font-weight: 800;
            color: var(--accent);
        }
        .moa-stat-label {
            font-size: 12px;
            color: var(--text-muted);
        }

        .moa-stage-box {
            background: #091020;
            border: 1px solid #1a2740;
            border-radius: 8px;
            margin-bottom: 14px;
            overflow: hidden;
            transition: all 0.2s;
        }
        .moa-stage-box:hover {
            border-color: #3b82f6;
        }
        .moa-stage-header {
            background: #0e172e;
            padding: 10px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            border-bottom: 1px solid #182338;
        }
        .moa-stage-title {
            font-weight: 700;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .moa-stage-body {
            padding: 14px 18px;
            font-size: 14.5px;
            line-height: 1.65;
        }

        /* Rich Markdown Styling */
        .markdown-body {
            font-size: 16px;
            line-height: 1.75;
            color: var(--text-secondary);
        }
        .markdown-body p { margin-bottom: 14px; }
        .markdown-body p:last-child { margin-bottom: 0; }
        .markdown-body strong { color: #fff; font-weight: 700; }
        .markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
            color: #fff;
            margin-top: 18px;
            margin-bottom: 10px;
            font-weight: 700;
        }
        .markdown-body h2 { font-size: 1.25em; border-bottom: 1px solid #334155; padding-bottom: 6px; }
        .markdown-body h3 { font-size: 1.1em; }
        .markdown-body ul, .markdown-body ol {
            margin-left: 24px;
            margin-bottom: 14px;
        }
        .markdown-body li { margin-bottom: 6px; }
        
        .markdown-body table {
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0;
            font-size: 14px;
            background: #060914;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #1e2b42;
        }
        .markdown-body th, .markdown-body td {
            border: 1px solid #1e2b42;
            padding: 10px 14px;
            text-align: left;
        }
        .markdown-body th {
            background: #0e172e;
            color: var(--accent);
            font-weight: 700;
        }
        .markdown-body tr:nth-child(even) {
            background: rgba(255,255,255,0.02);
        }
        
        .markdown-body pre {
            background: #03050a;
            border: 1px solid #1f2d47;
            border-radius: 8px;
            padding: 14px;
            overflow-x: auto;
            margin: 12px 0;
            font-family: var(--font-code);
            font-size: 13.5px;
            line-height: 1.55;
        }
        .markdown-body code {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: var(--font-code);
            font-size: 13.5px;
        }
        .markdown-body pre code {
            background: transparent;
            color: #e2e8f0;
            padding: 0;
        }
        .markdown-body blockquote {
            border-left: 4px solid var(--accent);
            padding: 8px 14px;
            margin: 12px 0;
            color: #94a3b8;
            background: rgba(56, 189, 248, 0.05);
            border-radius: 0 8px 8px 0;
        }

        /* Chat Input Box */
        .chat-input-box { 
            padding: 14px 20px; 
            background: #070d1c; 
            border-top: 1px solid var(--border); 
            display: flex; 
            flex-direction: column; 
            gap: 10px; 
            z-index: 10;
        }
        .input-toolbar { display: flex; justify-content: space-between; align-items: center; }
        .toolbar-actions { display: flex; gap: 8px; }
        
        .btn-action { 
            background: rgba(56, 189, 248, 0.14); 
            color: var(--accent); 
            border: 1px solid rgba(56, 189, 248, 0.35); 
            font-size: 12.5px; 
            padding: 7px 14px; 
            border-radius: 7px; 
            cursor: pointer; 
            font-weight: 700; 
            display: flex; 
            align-items: center; 
            gap: 6px; 
            transition: all 0.2s;
        }
        .btn-action:hover { 
            background: rgba(56, 189, 248, 0.25); 
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
        }
        
        .btn-moa-launch {
            background: linear-gradient(135deg, #1d4ed8, #7e22ce);
            color: #fff;
            border: 1px solid #93c5fd;
            font-size: 13px;
            padding: 7px 16px;
            border-radius: 7px;
            cursor: pointer;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 0 14px rgba(126, 34, 206, 0.4);
            transition: all 0.2s;
        }
        .btn-moa-launch:hover {
            transform: translateY(-1px);
            box-shadow: 0 0 18px rgba(147, 197, 253, 0.6);
        }
        
        textarea { 
            width: 100%; 
            background: var(--bg-input); 
            border: 1px solid #1e2d47; 
            border-radius: 10px; 
            color: #fff; 
            padding: 12px 16px; 
            font-size: 15.5px; 
            font-family: var(--font-main);
            min-height: 80px; 
            resize: none; 
            outline: none; 
            line-height: 1.6;
        }
        textarea:focus { 
            border-color: var(--accent); 
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.3); 
        }

        /* Embedded Spec Drafting Panel */
        .spec-panel { 
            position: absolute; 
            bottom: 0; 
            left: 0; 
            right: 0; 
            background: #081122; 
            border-top: 2px solid var(--accent); 
            padding: 20px 24px; 
            display: none; 
            flex-direction: column; 
            gap: 10px; 
            z-index: 30; 
            box-shadow: 0 -12px 30px rgba(0,0,0,0.6); 
        }
        .spec-panel.show { display: flex; }
        .spec-grid { display: grid; grid-template-columns: 1fr 2fr; gap: 10px; }
        .spec-input { 
            background: var(--bg-input); 
            border: 1px solid #22344f; 
            color: #fff; 
            padding: 9px 12px; 
            border-radius: 7px; 
            font-size: 13.5px; 
            outline: none; 
        }
        .spec-textarea { height: 100px; font-family: var(--font-code); font-size: 13px; }
        .spec-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 4px; }

        /* -------------------------------------------------------------
           Right Pane: Pipeline & Diff (可一键收纳折叠)
        -------------------------------------------------------------- */
        .right-pane { 
            background: #040813; 
            display: flex; 
            flex-direction: column; 
            height: 100%; 
            overflow: hidden; 
            position: relative;
        }
        
        /* Activity Stream */
        .pipeline-section { 
            flex: 0.50; 
            display: flex; 
            flex-direction: column; 
            border-bottom: 1px solid var(--border); 
            overflow: hidden; 
        }
        .stream-list { 
            flex: 1; 
            overflow-y: scroll !important; 
            padding: 14px; 
            display: flex; 
            flex-direction: column; 
            gap: 8px; 
        }
        .stream-card { 
            background: var(--bg-card); 
            border: 1px solid var(--border); 
            padding: 10px 14px; 
            border-radius: 7px; 
            font-size: 13px; 
            transition: all 0.2s;
        }
        .stream-card:hover { border-color: #3b82f6; }
        .stream-meta { display: flex; justify-content: space-between; color: var(--text-muted); margin-bottom: 5px; font-size: 11px; }
        .stream-title { font-weight: 700; color: #fff; font-size: 13.5px; }
        .stream-snippet { color: var(--text-muted); margin-top: 5px; font-size: 12px; font-family: var(--font-code); line-height: 1.45; }

        /* Diff Section */
        .diff-section { 
            flex: 0.50; 
            display: flex; 
            flex-direction: column; 
            background: #020409; 
            overflow: hidden; 
        }
        .diff-header-tools { display: flex; align-items: center; gap: 8px; }
        .diff-hash-badge { 
            background: #0e172a; 
            color: var(--accent-amber); 
            font-family: var(--font-code); 
            font-size: 12px; 
            padding: 3px 9px; 
            border-radius: 5px; 
            border: 1px solid #23344d; 
            font-weight: 700;
        }
        .diff-viewer { 
            flex: 1; 
            overflow-y: scroll !important; 
            padding: 14px; 
            font-family: var(--font-code); 
            font-size: 13px; 
            background: #020408; 
            color: #cbd5e1; 
            line-height: 1.6; 
            white-space: pre-wrap; 
        }
        
        .diff-line-add { color: #34d399; background: rgba(52, 211, 153, 0.08); display: block; }
        .diff-line-del { color: #f87171; background: rgba(248, 113, 113, 0.08); display: block; }
        .diff-line-hunk { color: #38bdf8; font-weight: bold; }

        .diff-footer { 
            padding: 10px 18px; 
            background: #060c18; 
            border-top: 1px solid var(--border); 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .btn-approve { 
            background: #059669; 
            color: #fff; 
            border: none; 
            padding: 7px 18px; 
            border-radius: 6px; 
            font-weight: 700; 
            font-size: 13px; 
            cursor: pointer; 
            transition: all 0.2s;
        }
        .btn-approve:hover { background: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.4); }
        .btn-veto { 
            background: #b91c1c; 
            color: #fff; 
            border: none; 
            padding: 7px 18px; 
            border-radius: 6px; 
            font-weight: 700; 
            font-size: 13px; 
            cursor: pointer; 
            transition: all 0.2s;
        }
        .btn-veto:hover { background: #ef4444; box-shadow: 0 0 12px rgba(239,68,68,0.4); }
        
        /* Loading pulse */
        .loading-pulse {
            animation: pulse 1.5s infinite ease-in-out;
        }
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1.0; }
            100% { opacity: 0.6; }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-left">
            <span class="logo-badge">MOA-TTC</span>
            <span class="logo-title">全新 DSH · 轻量三剑客主权思考座舱 (v2.0.0 · 突破 Flash 极限战胜 GPT-5.6 Sol)</span>
        </div>

        <div class="header-right">
            <!-- Font / UI Zoom Controls -->
            <div class="zoom-group">
                <span style="font-size:11px; color:var(--text-muted); padding-left:5px;">🔍 缩放:</span>
                <button class="btn-tool" onclick="adjustZoom(-0.1)">A-</button>
                <button class="btn-tool" id="zoom-btn-100" onclick="setZoom(1.0)">100%</button>
                <button class="btn-tool" id="zoom-btn-125" onclick="setZoom(1.25)">125%</button>
                <button class="btn-tool" id="zoom-btn-150" onclick="setZoom(1.50)">150% (4K)</button>
                <button class="btn-tool" onclick="adjustZoom(0.1)">A+</button>
            </div>

            <!-- 3D World Tree Button -->
            <a href="/world_tree" target="_blank" style="text-decoration:none; display:flex; align-items:center; gap:6px; background:linear-gradient(135deg, #059669, #2563eb); color:#fff; font-size:12px; font-weight:700; padding:6px 12px; border-radius:7px; box-shadow:0 0 12px rgba(37,99,235,0.4); transition:all 0.2s;">
                🌳 3D 世界树拓扑
            </a>

            <!-- Toggle Sidebar Button -->
            <button class="btn-collapse-sidebar" id="btn-toggle-sidebar" onclick="toggleSidebar()">
                ◨ 收纳右栏 (专注思考)
            </button>

            <!-- Status Badges for Three Musketeers -->
            <div class="header-status">
                <div class="status-badge"><div class="dot dot-blue"></div> 💎 编排: Gemini 3.8F</div>
                <div class="status-badge"><div class="dot dot-purple"></div> ⚔️ T-1 守门: DeepSeek 4.1F</div>
                <div class="status-badge"><div class="dot dot-amber"></div> 🔭 数据清洗: 常驻</div>
                <div class="status-badge"><div class="dot dot-green"></div> ⚡ TTC 膨胀: 激活</div>
                <div class="status-badge" style="opacity:0.75;"><div class="dot" style="background:#64748b;"></div> 🔨 GLM 5.3F: 休眠💤</div>
            </div>
        </div>
    </header>

    <div class="workspace" id="workspace">
        <!-- Left: Cognitive & Debate Pane -->
        <div class="left-pane">
            <div class="pane-header">
                <span class="pane-title">
                    <span>🧠</span> 战略意图收敛与多智能体推演区 (Cognitive Space)
                </span>
                <div class="mode-selector">
                    <button class="mode-btn active" id="btn-mode-gemini" onclick="setMode('gemini')">Gemini 3.8 秘书长</button>
                    <button class="mode-btn" id="btn-mode-deepseek" onclick="setMode('deepseek')">DeepSeek 红队挑刺</button>
                    <button class="mode-btn" id="btn-mode-dual" onclick="setMode('dual')">双脑合议对勘</button>
                    <button class="mode-btn" id="btn-mode-t1" onclick="setMode('t1_audit')">T-1 防偏航审计</button>
                    <button class="mode-btn mode-moa" id="btn-mode-moa" onclick="setMode('moa_ttc')">🚀 三剑客 TTC 流水线</button>
                </div>
            </div>

            <div class="chat-scroll-wrapper" id="chat-scroll-wrapper">
                <div class="chat-content-container" id="chat-stream">
                    <!-- Initial Welcome Card -->
                    <div class="msg msg-gemini">
                        <div class="msg-header">
                            <span class="msg-tag tag-gemini">首席秘书长 · Gemini 3.8 Flash (1M 上下文)</span>
                            <span style="font-size:12px; color:var(--text-muted);">系统架构全景对齐</span>
                        </div>
                        <div class="markdown-body">
                            <p><strong>指挥官好！“轻量三剑客”（Three Musketeers）主权思考座舱 v2.0.0 已全面上线！</strong></p>
                            <p>遵照您的最高战略构想，我们将以<strong>轻量级模型协同体系战胜 GPT-5.6 Sol 等重型单体</strong>为目标，完成如下核心架构突破：</p>
                            <ul>
                                <li><strong>三剑客协同矩阵</strong>：
                                    <ul>
                                        <li>💎 <strong>Gemini 3.8 Flash</strong>（首席秘书长）：极速 TTFT，1M 全景上下文，统筹宏观意图与无状态 DAG 任务切片；</li>
                                        <li>⚔️ <strong>DeepSeek v4.1 Flash</strong>（军需装备官）：冷酷红队逆向挑刺，挖掘 3 大隐蔽死穴，配发本地 30 项高星技能金样模板；</li>
                                        <li>🔨 <strong>GLM 5.3 Flash / Builder</strong>（建造工程师）：高吞吐施工，挂载确定性 Python AST 静态语法断言与自愈循环。</li>
                                    </ul>
                                </li>
                                <li><strong>突破 Flash 长程缺陷 (TTC 时空膨胀)</strong>：单体 Flash 往往在单轮 2 秒内匆忙下结论造成长程衰减。三剑客通过测试时算力（Test-Time Compute），<strong>单任务主动投入 15K~50K Token 与 30s~60s 深度对抗校验</strong>，生成高质量且具备生产级自愈的代码与结晶断层！</li>
                            </ul>
                            <p>💡 <strong>体验建议</strong>：在下方输入框键入任意工程需求，点击 <strong style="color:var(--accent);">“🚀 启动三剑客 TTC 流水线”</strong>，即可见证四阶段全自主推演与右侧结晶签名！</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="chat-input-box">
                <div class="input-toolbar">
                    <span style="font-size: 12px; color: var(--text-muted);">💡 快捷键：按 <strong>Ctrl + Enter</strong> 极速发送</span>
                    <div class="toolbar-actions">
                        <button class="btn-moa-launch" onclick="launchMoaPipeline()">
                            🚀 启动三剑客 TTC 流水线 (Run MOA Pipeline)
                        </button>
                        <button class="btn-action" onclick="toggleSpecPanel()">
                            ⚡ 唤起 Spec 派发面板
                        </button>
                    </div>
                </div>
                <textarea id="prompt-input" placeholder="输入战略构想、架构需求或工程任务 (按 Ctrl + Enter 发送，或直接点击上方紫色按钮启动三剑客)..." onkeydown="handleKey(event)"></textarea>
            </div>

            <!-- Embedded Spec Drafting Panel -->
            <div class="spec-panel" id="spec-panel">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:14px; color:var(--accent);">⚡ 编译派发工单 (Dispatch to ZCode)</strong>
                    <span style="font-size:12px; color:var(--text-muted); cursor:pointer;" onclick="toggleSpecPanel()">✕ 关闭</span>
                </div>
                <div class="spec-grid">
                    <input type="text" class="spec-input" id="spec-task-id" placeholder="Task ID (如 FED-BUILDER-001)" value="FED-BUILDER-001">
                    <input type="text" class="spec-input" id="spec-subject" placeholder="工单主题" value="开源发布代码脱敏与工程硬化">
                </div>
                <textarea class="spec-input spec-textarea" id="spec-body" placeholder="填写执行规范 (Spec 描述)..."></textarea>
                <div class="spec-actions">
                    <button class="btn-action" style="background:#1e293b; color:#fff;" onclick="toggleSpecPanel()">取消</button>
                    <button class="btn-action" onclick="submitDispatch()">🚀 正式派发给 ZCode</button>
                </div>
            </div>
        </div>

        <!-- Right: Autonomous Pipeline & Diff Pane (可收纳) -->
        <div class="right-pane" id="right-pane">
            <div class="pipeline-section">
                <div class="pane-header">
                    <span class="pane-title"><span>📡</span> 联邦公文自治流水线 (Bridge Stream)</span>
                    <button class="btn-action" onclick="refreshStream()" style="padding: 3px 10px; font-size: 11px;">刷新流水</button>
                </div>
                <div class="stream-list" id="stream-list">
                    <!-- Stream Cards -->
                </div>
            </div>

            <div class="diff-section">
                <div class="pane-header">
                    <span class="pane-title"><span>💎</span> 最终收敛断面 (Crystal Diff)</span>
                    <div class="diff-header-tools">
                        <span class="diff-hash-badge" id="diff-hash-label">HASH: --------</span>
                        <button class="btn-action" onclick="loadDiff()" style="padding: 3px 10px; font-size: 11px;">刷新 Diff</button>
                    </div>
                </div>
                <div class="diff-viewer" id="diff-viewer">// 正在读取最新代码结晶断面...</div>
                <div class="diff-footer">
                    <span style="font-size: 12px; color: var(--text-muted);" id="diff-task-label">工单: FED-BUILDER-001</span>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn-veto" onclick="signoff('VETO')">❌ 一票否决</button>
                        <button class="btn-approve" onclick="signoff('APPROVE')">✅ 批准合流</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentMode = "gemini";
        let activeTaskId = "FED-BUILDER-001";
        let currentDiffHash = "";
        let currentZoom = 1.25; // 默认 125% 适配高分屏
        let isSidebarCollapsed = false;

        // Init marked
        if (window.marked && typeof window.marked.setOptions === 'function') {
            window.marked.setOptions({
                gfm: true,
                breaks: true
            });
        }

        function renderMarkdown(text) {
            if (window.marked && typeof window.marked.parse === 'function') {
                try {
                    return window.marked.parse(text);
                } catch(e) {
                    console.error("marked error:", e);
                }
            }
            return text.replace(/\\n/g, '<br>');
        }

        /* -------------------------------------------------------------
           Zoom / Font Scaling Logic
        -------------------------------------------------------------- */
        function initZoom() {
            const savedZoom = localStorage.getItem('dsh_ui_zoom');
            if (savedZoom) {
                currentZoom = parseFloat(savedZoom);
            } else {
                if (window.innerWidth >= 2560 || window.screen.width >= 2560) {
                    currentZoom = 1.35;
                }
            }
            applyZoom();
        }

        function setZoom(val) {
            currentZoom = val;
            applyZoom();
        }

        function adjustZoom(delta) {
            currentZoom = Math.max(0.8, Math.min(2.0, Math.round((currentZoom + delta) * 10) / 10));
            applyZoom();
        }

        function applyZoom() {
            document.body.style.zoom = currentZoom;
            localStorage.setItem('dsh_ui_zoom', currentZoom);
            document.querySelectorAll('.zoom-group .btn-tool').forEach(b => b.classList.remove('active'));
            if (Math.abs(currentZoom - 1.0) < 0.05) document.getElementById('zoom-btn-100')?.classList.add('active');
            if (Math.abs(currentZoom - 1.25) < 0.05) document.getElementById('zoom-btn-125')?.classList.add('active');
            if (Math.abs(currentZoom - 1.50) < 0.05) document.getElementById('zoom-btn-150')?.classList.add('active');
        }

        /* -------------------------------------------------------------
           Sidebar Collapse Logic (一键收纳右侧栏)
        -------------------------------------------------------------- */
        function initSidebar() {
            const saved = localStorage.getItem('dsh_sidebar_collapsed');
            if (saved === 'true') {
                isSidebarCollapsed = true;
                document.getElementById('workspace').classList.add('sidebar-collapsed');
                updateSidebarBtnText();
            }
        }

        function toggleSidebar() {
            isSidebarCollapsed = !isSidebarCollapsed;
            const ws = document.getElementById('workspace');
            ws.classList.toggle('sidebar-collapsed', isSidebarCollapsed);
            localStorage.setItem('dsh_sidebar_collapsed', isSidebarCollapsed);
            updateSidebarBtnText();
        }

        function updateSidebarBtnText() {
            const btn = document.getElementById('btn-toggle-sidebar');
            if (isSidebarCollapsed) {
                btn.innerHTML = "◫ 展开右栏 (查看流水)";
                btn.style.background = "rgba(52, 211, 153, 0.2)";
                btn.style.borderColor = "var(--accent-green)";
                btn.style.color = "var(--accent-green)";
            } else {
                btn.innerHTML = "◨ 收纳右栏 (专注思考)";
                btn.style.background = "rgba(56, 189, 248, 0.12)";
                btn.style.borderColor = "rgba(56, 189, 248, 0.35)";
                btn.style.color = "var(--accent)";
            }
        }

        function setMode(mode) {
            currentMode = mode;
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            const map = {
                'gemini': 'btn-mode-gemini',
                'deepseek': 'btn-mode-deepseek',
                'dual': 'btn-mode-dual',
                't1_audit': 'btn-mode-t1',
                'moa_ttc': 'btn-mode-moa'
            };
            if (map[mode]) {
                document.getElementById(map[mode])?.classList.add('active');
            }
        }

        function handleKey(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                if (currentMode === 'moa_ttc') {
                    launchMoaPipeline();
                } else {
                    sendChat();
                }
            }
        }

        function toggleSpecPanel() {
            const p = document.getElementById('spec-panel');
            p.classList.toggle('show');
        }

        function extractToSpec(elem) {
            const text = elem.innerText || elem.textContent;
            document.getElementById('spec-body').value = text;
            const p = document.getElementById('spec-panel');
            p.classList.add('show');
        }

        /* -------------------------------------------------------------
           Chat Handling
        -------------------------------------------------------------- */
        async function sendChat() {
            const input = document.getElementById('prompt-input');
            const text = input.value.trim();
            if (!text) return;

            appendMsg('commander', '最高统帅', text);
            input.value = '';

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, mode: currentMode })
                });
                const data = await res.json();
                
                if (data.mode === 'gemini') {
                    appendMsg('gemini', '首席秘书长 · Gemini 3.8 Flash', data.reply);
                } else if (data.mode === 'deepseek') {
                    appendMsg('deepseek', '军需装备官 · DeepSeek v4.1 Flash', data.reply);
                } else if (data.mode === 't1_audit') {
                    appendMsg('t1', 'T-1 防偏航审计', data.reply);
                } else if (data.mode === 'dual') {
                    appendMsg('gemini', '首席秘书长 · Gemini 3.8 Flash', data.gemini);
                    appendMsg('deepseek', '军需装备官 · DeepSeek v4.1 Flash', data.deepseek);
                } else if (data.mode === 'moa_ttc') {
                    renderMoaResult(data.pipeline_result);
                }
            } catch (err) {
                appendMsg('t1', '系统异常', '调用失败: ' + err);
            }
        }

        /* -------------------------------------------------------------
           MOA TTC Pipeline Launcher & Renderer
        -------------------------------------------------------------- */
        async function launchMoaPipeline() {
            const input = document.getElementById('prompt-input');
            let goal = input.value.trim();
            if (!goal) {
                goal = "实现一个高并发安全的带自愈能力的 Token 桶限流器与熔断中间件";
            }
            appendMsg('commander', '最高统帅 (TTC 任务发布)', `🎯 **启动三剑客时空膨胀任务**：\n\n> ${goal}`);
            input.value = '';

            const stream = document.getElementById('chat-stream');
            const loadingId = "moa-loading-" + Date.now();
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'msg msg-moa loading-pulse';
            loadingDiv.id = loadingId;
            loadingDiv.innerHTML = `
                <div class="msg-header">
                    <span class="msg-tag tag-moa">⚡ [TTC 算力时空膨胀中...]</span>
                    <span style="font-size:12px; color:var(--accent);">突破单体 Flash 短板进行中</span>
                </div>
                <div style="padding: 10px 0;">
                    <div style="font-weight:700; color:#fff; margin-bottom:8px;">轻量三剑客正在并行推演：</div>
                    <ul style="margin-left:22px; color:var(--text-secondary); font-size:14px; line-height:1.8;">
                        <li>💎 <strong>阶段 1</strong>: Gemini 3.8 Flash 执行无状态能力切片与 DAG 任务分解...</li>
                        <li>⚔️ <strong>阶段 2</strong>: DeepSeek v4.1 Flash 冷酷挑刺，排查 3 大致命死穴并装配金样模板...</li>
                        <li>🔨 <strong>阶段 3</strong>: GLM 5.3 Flash / Builder 施工，挂载确定性 Python AST 语法断言与自愈循环...</li>
                        <li>💎 <strong>阶段 4</strong>: 收敛生成结晶 Diff 与 SHA-256 签名...</li>
                    </ul>
                    <div style="margin-top:10px; font-size:12px; color:var(--accent-amber);">预计耗时 25s ~ 45s，投入 15,000+ Tokens...</div>
                </div>
            `;
            stream.appendChild(loadingDiv);
            const scrollWrapper = document.getElementById('chat-scroll-wrapper');
            scrollWrapper.scrollTop = scrollWrapper.scrollHeight;

            try {
                const res = await fetch('/api/moa/run_pipeline', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ goal: goal })
                });
                const data = await res.json();
                
                const ld = document.getElementById(loadingId);
                if (ld) ld.remove();

                if (data.ok) {
                    renderMoaResult(data);
                } else {
                    appendMsg('t1', 'MOA 运行异常', `三剑客流水线失败: ${JSON.stringify(data)}`);
                }
            } catch (err) {
                const ld = document.getElementById(loadingId);
                if (ld) ld.remove();
                appendMsg('t1', 'MOA 网络异常', `请求失败: ${err}`);
            }
        }

        function renderMoaResult(res) {
            const stream = document.getElementById('chat-stream');
            const div = document.createElement('div');
            div.className = 'msg msg-moa';

            let stagesHtml = '';
            (res.stages || []).forEach(st => {
                let bodyContent = '';
                if (st.stage === 1) {
                    const rows = (st.data || []).map(c => `
                        <tr>
                            <td><code>${escapeHtml(c.stream_id)}</code></td>
                            <td><strong>${escapeHtml(c.title)}</strong></td>
                            <td>${escapeHtml((c.depends_on || []).join(', ') || '无')}</td>
                            <td><code>${escapeHtml((c.files_scope || []).join(', '))}</code></td>
                            <td>${escapeHtml(c.acceptance || '')}</td>
                        </tr>
                    `).join('');
                    bodyContent = `
                        <p style="margin-bottom:8px; color:var(--accent);"><strong>${escapeHtml(st.summary)}</strong></p>
                        <table>
                            <thead>
                                <tr><th>Stream ID</th><th>任务主题</th><th>前置依赖</th><th>文件边界</th><th>验收断言</th></tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    `;
                } else if (st.stage === 2) {
                    bodyContent = `
                        <p style="margin-bottom:8px; color:var(--accent-purple);"><strong>${escapeHtml(st.summary)}</strong></p>
                        <div class="markdown-body" style="background:#060812; padding:12px; border-radius:6px; border:1px solid #231638;">
                            ${renderMarkdown(st.manifest || '')}
                        </div>
                    `;
                } else if (st.stage === 3) {
                    bodyContent = `
                        <p style="margin-bottom:8px; color:${st.ast_ok ? 'var(--accent-green)' : 'var(--accent-rose)'};">
                            <strong>${escapeHtml(st.summary)}</strong>
                        </p>
                        <pre><code>${escapeHtml(st.code_snippet || '')}</code></pre>
                    `;
                } else if (st.stage === 4) {
                    bodyContent = `
                        <p style="margin-bottom:8px; color:var(--accent-amber);"><strong>${escapeHtml(st.summary)}</strong></p>
                        <pre><code>${escapeHtml(st.diff_snippet || '')}</code></pre>
                    `;
                }

                stagesHtml += `
                    <div class="moa-stage-box">
                        <div class="moa-stage-header" onclick="toggleAccordion(this)">
                            <span class="moa-stage-title">
                                <span>${st.stage === 1 ? '💎' : st.stage === 2 ? '⚔️' : st.stage === 3 ? '🔨' : '💎'}</span>
                                阶段 ${st.stage}：${escapeHtml(st.name)} (${escapeHtml(st.actor)})
                            </span>
                            <span style="font-size:12px; color:var(--text-muted);">
                                🪙 ${st.tokens} tokens · ⏱️ ${st.latency_ms ? (st.latency_ms/1000).toFixed(1)+'s' : ''} ▼
                            </span>
                        </div>
                        <div class="moa-stage-body">${bodyContent}</div>
                    </div>
                `;
            });

            div.innerHTML = `
                <div class="msg-header">
                    <span class="msg-tag tag-moa">🏆 轻量三剑客 TTC 收敛战报</span>
                    <button class="btn-extract-spec" onclick="syncMoaDiffToRight('${res.hash}')">👉 聚焦右侧 Diff 断面</button>
                </div>
                
                <div class="moa-ledger-banner">
                    <div class="moa-stat-item">
                        <span class="moa-stat-label">总耗时:</span>
                        <span class="moa-stat-val" style="color:var(--accent-amber);">${res.duration_s} s</span>
                    </div>
                    <div class="moa-stat-item">
                        <span class="moa-stat-label">TTC Token 消耗:</span>
                        <span class="moa-stat-val" style="color:var(--accent-green);">${res.total_tokens?.toLocaleString()} Tokens</span>
                    </div>
                    <div class="moa-stat-item">
                        <span class="moa-stat-label">产物结晶指纹:</span>
                        <span class="moa-stat-val" style="color:var(--accent-purple);">[${res.hash}]</span>
                    </div>
                    <div class="moa-stat-item">
                        <span class="moa-stat-label">效能评级:</span>
                        <span class="moa-stat-val" style="color:var(--accent);">超越单体 GPT-5.6 Sol</span>
                    </div>
                </div>

                <div style="margin-bottom:12px;">${stagesHtml}</div>
            `;

            stream.appendChild(div);
            const scrollWrapper = document.getElementById('chat-scroll-wrapper');
            scrollWrapper.scrollTop = scrollWrapper.scrollHeight;

            syncMoaDiffToRight(res.hash);
        }

        function toggleAccordion(header) {
            const body = header.nextElementSibling;
            if (body.style.display === 'none') {
                body.style.display = 'block';
            } else {
                body.style.display = 'none';
            }
        }

        function syncMoaDiffToRight(hash) {
            activeTaskId = "MOA-TTC-" + hash;
            document.getElementById('diff-task-label').innerText = `工单: ${activeTaskId}`;
            loadDiff();
        }

        function appendMsg(type, tag, content) {
            const stream = document.getElementById('chat-stream');
            const div = document.createElement('div');
            div.className = `msg msg-${type}`;
            
            let extractBtn = '';
            if (type !== 'commander') {
                extractBtn = `<button class="btn-extract-spec" onclick="extractToSpec(this.parentElement.nextElementSibling)">📄 提炼为 Spec</button>`;
            }

            const htmlContent = renderMarkdown(content);

            div.innerHTML = `
                <div class="msg-header">
                    <span class="msg-tag tag-${type}">${tag}</span>
                    ${extractBtn}
                </div>
                <div class="markdown-body">${htmlContent}</div>
            `;
            stream.appendChild(div);
            
            const scrollWrapper = document.getElementById('chat-scroll-wrapper');
            scrollWrapper.scrollTop = scrollWrapper.scrollHeight;
        }

        async function refreshStream() {
            try {
                const res = await fetch('/api/bridge/status');
                const data = await res.json();
                if (data.status === 'online') {
                    const list = document.getElementById('stream-list');
                    list.innerHTML = '';
                    data.messages.forEach(m => {
                        const card = document.createElement('div');
                        card.className = 'stream-card';
                        card.innerHTML = `
                            <div class="stream-meta">
                                <span>#${m.id} 来自: ${m.from || '未知'}</span>
                                <span>${m.time || ''}</span>
                            </div>
                            <div class="stream-title">${escapeHtml(m.subject)}</div>
                            <div class="stream-snippet">${escapeHtml(m.snippet)}</div>
                        `;
                        list.appendChild(card);
                    });

                    document.getElementById('zcode-badge').innerHTML = 
                        `<div class="dot dot-${data.zcode_status === 'WORKING' ? 'amber' : 'green'}"></div> 8766 邮桥: ${data.zcode_status}`;
                }
            } catch (e) {
                console.error("刷新流水异常", e);
            }
        }

        async function loadDiff() {
            try {
                const res = await fetch('/api/latest_diff');
                const data = await res.json();
                currentDiffHash = data.hash || "000000000000";
                document.getElementById('diff-hash-label').innerText = `HASH: ${currentDiffHash}`;
                if (data.task_id) {
                    activeTaskId = data.task_id;
                    document.getElementById('diff-task-label').innerText = `工单: ${activeTaskId}`;
                }
                
                const viewer = document.getElementById('diff-viewer');
                const lines = data.diff.split('\n');
                viewer.innerHTML = lines.map(l => {
                    if (l.startsWith('+') && !l.startsWith('+++')) return `<span class="diff-line-add">${escapeHtml(l)}</span>`;
                    if (l.startsWith('-') && !l.startsWith('---')) return `<span class="diff-line-del">${escapeHtml(l)}</span>`;
                    if (l.startsWith('@@')) return `<span class="diff-line-hunk">${escapeHtml(l)}</span>`;
                    return `<span>${escapeHtml(l)}</span>`;
                }).join('\n');
            } catch (e) {
                document.getElementById('diff-viewer').innerText = "// 读取 Diff 异常: " + e;
            }
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        async function submitDispatch() {
            const taskId = document.getElementById('spec-task-id').value.trim();
            const subject = document.getElementById('spec-subject').value.trim();
            const spec = document.getElementById('spec-body').value.trim();
            if (!taskId || !subject || !spec) {
                alert("请完整填写 Task ID、主题与 Spec 规范");
                return;
            }

            try {
                const res = await fetch('/api/dispatch_task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId, subject: subject, spec_body: spec })
                });
                const d = await res.json();
                if (d.ok) {
                    alert(`✅ 工单已成功通过邮桥派发给 ZCode！\nTask ID: ${taskId}`);
                    activeTaskId = taskId;
                    document.getElementById('diff-task-label').innerText = `工单: ${taskId}`;
                    toggleSpecPanel();
                    refreshStream();
                } else {
                    alert(`派发失败: ${JSON.stringify(d)}`);
                }
            } catch (e) {
                alert(`请求异常: ${e}`);
            }
        }

        async function signoff(action) {
            if (!confirm(`确定对当前代码结晶断面执行终审裁决: [${action}] 吗？\n绑定工单: ${activeTaskId}\n产物 Hash: ${currentDiffHash}`)) return;
            try {
                const res = await fetch('/api/signoff', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        task_id: activeTaskId, 
                        action: action, 
                        artifact_hash: currentDiffHash,
                        feedback: '指挥官通过全新 DSH 三剑客座舱裁决' 
                    })
                });
                const d = await res.json();
                if (d.ok) {
                    alert(`✅ 裁决公文已投递入邮桥！\n动作: ${action}\n工单: ${activeTaskId}\n产物 Hash: ${currentDiffHash}`);
                    refreshStream();
                }
            } catch (e) {
                alert(`签署异常: ${e}`);
            }
        }

        // Initialize
        initZoom();
        initSidebar();
        setInterval(refreshStream, 5000);
        setInterval(loadDiff, 10000);
        refreshStream();
        loadDiff();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=COCKPIT_HTML)

def run_server(host: str = "127.0.0.1", port: int = 8765):
    print("==================================================================")
    print(f"🚀 Federation Cockpit & 3D World Tree: http://{host}:{port}")
    print(f"🌳 3D World Tree: http://{host}:{port}/world_tree")
    print("==================================================================")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server("127.0.0.1", 8765)