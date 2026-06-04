#!/usr/bin/env python3
"""通过 pynput 向微信桌面版发消息，自动按回车发送。

用法: python3 wechat-send.py "消息内容"
前提: 微信已登录且切换到目标聊天窗口。
"""

import sys
import time
import os
from pynput.keyboard import Controller

def send_wechat(message: str):
    keyboard = Controller()

    # 激活微信到前台
    os.system('open -a WeChat')
    time.sleep(2)

    # 输入消息
    keyboard.type(message)
    time.sleep(0.3)

    # 按回车发送
    keyboard.press("\r")
    keyboard.release("\r")
    print(f"Sent: {message}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wechat-send.py <message>")
        sys.exit(1)
    send_wechat(sys.argv[1])
