import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from logger import logger


def send_email(subject, body, to_email=None):
    smtp_server = "smtp.qq.com"
    smtp_port = 465

    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = to_email or sender

    if not sender or not password:
        logger.error("缺少邮件配置: EMAIL_USER 或 EMAIL_PASS 未设置")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        logger.info(f"邮件发送成功: {subject}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def send_signin_report(counts, signin_time=None):
    if signin_time is None:
        signin_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    success = counts.get("success", 0)
    signed = counts.get("signed", 0)
    fail = counts.get("fail", 0)
    total = success + signed + fail

    if fail == 0 and success > 0:
        subject = f"贴吧签到 {signin_time[:10]} - 全部成功"
        level = "正常"
    elif fail == 0 and success == 0 and signed > 0:
        subject = f"贴吧签到 {signin_time[:10]} - 全部已签"
        level = "正常(已签过)"
    elif fail > 0:
        subject = f"贴吧签到 {signin_time[:10]} - {fail}个失败"
        level = "异常"
    else:
        subject = f"贴吧签到 {signin_time[:10]} - 无数据"
        level = "异常"

    body = f"""贴吧自动签到报告
{'=' * 35}

签到时间: {signin_time}
签到结果: {level}

总计: {total} 个贴吧
  签到成功: {success} 个
  已签过:   {signed} 个
  签到失败: {fail} 个"""

    if fail > 0:
        body += f"""

{'!' * 35}
注意: 有 {fail} 个贴吧签到失败，10:00 将自动补签。
详情: https://github.com/edawebs/tiebaSignIn/actions"""

    send_email(subject, body)


def send_alert(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"贴吧签到告警 - {now[:10]}"
    body = f"""贴吧签到系统告警
{'=' * 35}

告警时间: {now}
告警内容: {message}

请尽快检查:
https://github.com/edawebs/tiebaSignIn/actions"""
    send_email(subject, body)


def send_watchdog_alert():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"贴吧签到看门狗告警 - {now[:10]}"
    body = f"""贴吧签到系统严重告警
{'=' * 35}

告警时间: {now}
告警级别: 严重

截至中午 12:00，今天没有任何签到成功记录。
可能原因: GitHub Actions 故障 / Cookie 过期 / 百度接口变更

请立即手动检查:
1. 在手机上打开百度贴吧确认是否能正常登录
2. 查看 Actions 运行记录: https://github.com/edawebs/tiebaSignIn/actions
3. 检查 BDUSS 和 PTOKEN 是否需要更新"""
    send_email(subject, body)
