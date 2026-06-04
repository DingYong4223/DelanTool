#!/usr/bin/env python3
"""通过 pynput 向微信桌面版发消息，发完后自动回到原窗口。

用法: python3 wechat-send.py "消息内容"
前提: 微信已登录且切换到目标聊天窗口。
"""

import sys
import time
import os
import subprocess
from pynput.keyboard import Controller

def get_frontmost_app() -> str:
    """获取当前最前台应用的 bundle ID"""
    try:
        result = subprocess.run(
            ['osascript', '-e',
             'tell application "System Events" to return bundle identifier of first process whose frontmost is true'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""

def switch_to(app: str):
    """切换到指定应用"""
    try:
        subprocess.run(
            ['osascript', '-e', f'tell application id "{app}" to activate'],
            capture_output=True, timeout=5
        )
    except Exception:
        pass

def send_wechat(message: str):
    keyboard = Controller()

    # 记录当前前台应用
    prev_app = get_frontmost_app()

    # 激活微信到前台
    os.system('open -a WeChat')
    time.sleep(2)

    # 输入消息并发送
    keyboard.type(message)
    time.sleep(0.3)
    keyboard.press("\r")
    keyboard.release("\r")
    print(f"Sent: {message}")

    # 2 秒后回到原窗口
    if prev_app and prev_app != "com.tencent.xinWeChat":
        time.sleep(2)
        switch_to(prev_app)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wechat-send.py <message>")
        sys.exit(1)
    send_wechat(sys.argv[1])
