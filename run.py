import json
import os
import sys
from datetime import datetime

import tieba_login
import tieba_signIn
from tieba_favorite import get_favorite
from constant import success_flag, signed_flag, fail_flag
from logger import logger
import notify


def write_status(counts, workflow_name, error=None):
    """写入签到状态到缓存文件"""
    os.makedirs("cache", exist_ok=True)
    status = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workflow": workflow_name,
        "total": sum(counts.values()) if error is None else 0,
        "success": counts.get(success_flag, 0) if error is None else 0,
        "signed": counts.get(signed_flag, 0) if error is None else 0,
        "fail": counts.get(fail_flag, 0) if error is None else -1,
    }
    if error:
        status["error"] = str(error)[:200]

    with open("cache/signin-status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    return status


if __name__ == '__main__':
    workflow = os.getenv("WORKFLOW_NAME", "sign-in")
    logger.info(f"===== 工作流: {workflow} =====")

    try:
        cookie = tieba_login.login()
        favorites = get_favorite(cookie)
        counts = tieba_signIn.sign(cookie, favorites)

        status = write_status(counts, workflow)
        logger.info(f"签到状态: {json.dumps(status, ensure_ascii=False)}")

        notify.send_signin_report(counts)

        if counts.get(fail_flag, 0) > 0:
            logger.warning(f"{counts[fail_flag]} 个贴吧签到失败，10:00 将自动补签")
            sys.exit(1)

    except Exception as e:
        logger.error(f"签到流程异常: {e}")
        counts = {success_flag: 0, signed_flag: 0, fail_flag: -1}
        write_status(counts, workflow, error=e)
        notify.send_alert(f"签到流程异常终止: {e}")
        sys.exit(1)
