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


def already_signed_today():
    """读取上次签到状态：今日已全部签到且无失败返回 True。
    兜底模式用它短路，避免在无意义的复查中因网络抖动产生误报告警（2026-10-05）。"""
    try:
        with open("cache/signin-status.json", "r", encoding="utf-8") as f:
            status = json.load(f)
    except Exception:
        return False
    if status.get("date") != datetime.now().strftime("%Y-%m-%d"):
        return False
    if status.get("error"):
        return False
    return status.get("total", 0) > 0 and status.get("fail", 0) == 0


if __name__ == '__main__':
    workflow = os.getenv("WORKFLOW_NAME", "sign-in")
    backup_mode = "--backup" in sys.argv or os.getenv("BACKUP_MODE") == "1"
    logger.info(f"===== 工作流: {workflow} {'(兜底模式)' if backup_mode else ''} =====")

    # 兜底短路：早上已全部签到就无需再逐个复查（省时，且不会产生误报告警）
    if backup_mode and already_signed_today():
        logger.info("兜底检查: 今日已全部签到，跳过复查，不发送邮件")
        sys.exit(0)

    try:
        cookie = tieba_login.login()
        favorites = get_favorite(cookie)
        counts = tieba_signIn.sign(cookie, favorites)

        status = write_status(counts, workflow)
        logger.info(f"签到状态: {json.dumps(status, ensure_ascii=False)}")

        if backup_mode:
            # 兜底模式（14:00）：只有"有新的成功签到"(早上漏跑)或"有失败"才发邮件，全部已签则静默
            if counts.get(success_flag, 0) > 0 or counts.get(fail_flag, 0) > 0:
                notify.send_signin_report(counts)
            else:
                logger.info("兜底检查: 今天已全部签到，无需补签，不发送邮件")
        else:
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
