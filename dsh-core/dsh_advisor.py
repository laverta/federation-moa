# -*- coding: utf-8 -*-
import sys
import os
import argparse
from pathlib import Path

REPO_ROOT = Path(os.environ.get('FEDERATION_ROOT', Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsh_llm

def main():
    parser = argparse.ArgumentParser(description="DeepSeek Resident Advisor")
    parser.add_argument("--critique", type=str, help="红队挑刺找死穴 (Critique)")
    parser.add_argument("--t1-observe", type=str, help="T-1 偏航与范式观测打标签 (Observe)")
    parser.add_argument("--consult", type=str, help="快速征询第二意见 (Consult)")
    parser.add_argument("--prompt", type=str, help="通用深度推演")
    
    args = parser.parse_args()
    
    if args.critique:
        system_msg = "你是一个冷酷、专业的分布式与多Agent系统红队审核员。请用极其犀利、严密的视角，指出以下方案或代码中的逻辑死穴、安全漏洞、并发死锁与工程不严谨之处。结论先行，直奔要害。"
        resp = dsh_llm.chat(args.critique, history=[{"role": "system", "content": system_msg}])
        print(resp)
    elif args.t1_observe:
        system_msg = "你是一个冷静的中立会话范式观察者。请评估以下输入是否存在目标偏离或上下文漂移 (Context Drift)。严格按照 T-1 语法打上状态标签并提出一句话纠偏建议。"
        resp = dsh_llm.chat(args.t1_observe, history=[{"role": "system", "content": system_msg}])
        print(resp)
    elif args.consult:
        system_msg = "你是一个资深的第二意见技术顾问。请基于以下问题给出简洁有力的独立技术研判。"
        resp = dsh_llm.chat(args.consult, history=[{"role": "system", "content": system_msg}])
        print(resp)
    elif args.prompt:
        resp = dsh_llm.chat(args.prompt)
        print(resp)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
