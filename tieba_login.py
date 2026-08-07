import os
import json
import time
import random
import requests

from logger import logger


def login():
    """验证 BDUSS 有效性并返回 Cookie"""
    bduss = os.getenv("BDUSS")
    ptoken = os.getenv("PTOKEN")
    if not bduss or not ptoken:
        logger.error("缺少必要的环境变量 BDUSS 或 PTOKEN")
        exit(1)

    login_cookie = {
        "BDUSS": bduss.strip(),
        "PTOKEN": ptoken.strip(),
    }

    # 直接通过 TBS 接口验证登录状态（不依赖桌面版首页）
    tbs_url = "https://tieba.baidu.com/dc/common/tbs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://tieba.baidu.com/",
    }

    for attempt in range(3):
        try:
            time.sleep(random.uniform(0.5, 1.5))
            resp = requests.get(tbs_url, headers=headers, cookies=login_cookie, timeout=15)
            data = resp.json()
            if data.get("is_login") == 1:
                logger.info(f"登录验证成功，tbs={data.get('tbs')}")
                return login_cookie
            else:
                logger.warning(f"第{attempt + 1}次验证: BDUSS 可能已过期，返回: {data}")
        except Exception as e:
            logger.warning(f"第{attempt + 1}次请求异常: {e}")

        if attempt < 2:
            time.sleep((attempt + 1) * 3)

    logger.error("登录验证失败：BDUSS 可能已过期，请重新获取")
    exit(1)
