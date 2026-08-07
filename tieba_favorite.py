import hashlib
import json
import time
import random
import requests

from logger import logger

# 签名密钥（移动端 API）
SIGN_KEY = "tiebaclient!!!"


def _encode_data(data: dict) -> dict:
    """为移动端 API 生成签名"""
    s = ""
    for key in sorted(data.keys()):
        s += f"{key}={data[key]}"
    sign = hashlib.md5((s + SIGN_KEY).encode("utf-8")).hexdigest().upper()
    data["sign"] = sign
    return data


def get_favorite(cookie):
    """通过移动端 API 获取关注贴吧列表"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; MI 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://tieba.baidu.com/",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    like_url = "https://c.tieba.baidu.com/c/f/forum/like"
    favorites = []
    page_no = 1

    while True:
        data = {
            "BDUSS": cookie.get("BDUSS", ""),
            "_client_type": "2",
            "_client_id": "wappc_" + str(int(time.time() * 1000)) + "_" + str(random.randint(100, 999)),
            "_client_version": "9.7.8.0",
            "_phone_imei": "000000000000000",
            "from": "1008621y",
            "page_no": str(page_no),
            "page_size": "200",
            "model": "MI+9",
            "net_type": "1",
            "timestamp": str(int(time.time())),
            "vcode_tag": "11",
        }
        data = _encode_data(data)

        try:
            time.sleep(random.uniform(0.5, 1.5))
            resp = requests.post(like_url, headers=headers, cookies=cookie, data=data, timeout=15)
            res = resp.json()

            if "forum_list" not in res:
                logger.warning(f"第{page_no}页无贴吧数据: {res}")
                break

            forum_list = res["forum_list"]
            page_forums = []

            # 非名人堂和名人堂贴吧
            for forum_type in ["non-gconforum", "gconforum"]:
                if forum_type in forum_list:
                    items = forum_list[forum_type]
                    if isinstance(items, list):
                        for item in items:
                            name = item.get("name", "")
                            if name:
                                page_forums.append(name)
                                favorites.append(name)
                    elif isinstance(items, dict):
                        name = items.get("name", "")
                        if name:
                            page_forums.append(name)
                            favorites.append(name)

            logger.info(f"第{page_no}页获取到: {page_forums}")

            if res.get("has_more") != "1":
                break

            page_no += 1
        except Exception as e:
            logger.error(f"获取关注列表第{page_no}页失败: {e}")
            break

    logger.info(f"共获取到 {len(favorites)} 个关注的贴吧")
    return favorites
