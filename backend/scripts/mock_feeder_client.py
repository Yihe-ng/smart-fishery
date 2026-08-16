"""模拟投喂机 WebSocket 客户端。

连接后端 /ws/feeding/{feeder_id}，接收「投喂指令帧」，打印并模拟执行。
用于答辩演示「点击即控制」：前端 AI 预览 → 确认 → 执行后，本脚本控制台
会打印后端下发的真实指令帧。

演示步骤：
    1. 启动后端（uvicorn app.main:app --host 0.0.0.0 --port 8000）
    2. 本终端：python scripts/mock_feeder_client.py --auto-ack
    3. 前端投喂页 → AI 助手「生成手动投喂预览」→ 确认执行
    4. 观察本脚本打印指令帧与执行状态

参数：
    --host      后端地址，默认 127.0.0.1
    --port      后端端口，默认 8000
    --feeder-id 投喂机编号，默认 feeder-001（与后端预览快照默认一致）
    --auto-ack  收到 feed 指令后自动回送 feeding_status / feeding_complete
"""

import argparse
import json
import sys
import time
from datetime import datetime


def log(msg: str) -> None:
    print(msg, flush=True)


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main() -> int:
    parser = argparse.ArgumentParser(description="模拟投喂机 WebSocket 客户端")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--feeder-id", default="feeder-001")
    parser.add_argument("--auto-ack", action="store_true", help="收到 feed 后自动回送执行状态")
    args = parser.parse_args()

    url = f"ws://{args.host}:{args.port}/ws/feeding/{args.feeder_id}"
    log(f"[{now()}] 模拟投喂机启动，正在连接 {url} ...")

    from websockets.sync.client import connect

    try:
        with connect(url) as ws:
            log(f"[{now()}] ✅ 已上线：feeder_id={args.feeder_id}（等待后端下发指令）")
            while True:
                raw = ws.recv()
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    log(f"[{now()}] 收到非 JSON 消息: {raw!r}")
                    continue

                log(f"[{now()}] 收到指令帧: {json.dumps(message, ensure_ascii=False)}")

                if message.get("type") == "command" and message.get("command") == "feed":
                    data = message.get("data") or {}
                    amount = data.get("amount", 0)
                    duration = data.get("duration", 0)
                    log(f"[{now()}] 🔧 模拟执行：投喂 {amount}g，持续 {duration} 秒")
                    if args.auto_ack:
                        ws.send(
                            json.dumps(
                                {
                                    "type": "feeding_status",
                                    "data": {
                                        "feeder_id": args.feeder_id,
                                        "status": "feeding",
                                        "amount": amount,
                                    },
                                },
                                ensure_ascii=False,
                            )
                        )
                        time.sleep(min(duration, 2))  # 演示不真实等待
                        ws.send(
                            json.dumps(
                                {
                                    "type": "feeding_complete",
                                    "data": {
                                        "feeder_id": args.feeder_id,
                                        "amount": amount,
                                        "status": "completed",
                                    },
                                },
                                ensure_ascii=False,
                            )
                        )
                        log(f"[{now()}] ✅ 已回送 feeding_complete（前端可收到执行结果）")
    except KeyboardInterrupt:
        log(f"\n[{now()}] 已退出")
    except Exception as exc:
        log(f"[{now()}] ❌ 连接或运行出错: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
