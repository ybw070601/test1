import requests
import json
import os
import re
from datetime import datetime, timezone, timedelta

# 北京时间时区
TZ = timezone(timedelta(hours=8))

USER_LIST = [
    ("6353131515", "张桂源"),
    ("7740929779", "张函瑞"),
    ("3625607515", "王橹杰"),
    ("3448351424", "左奇函"),
    ("6320179782", "陈奕恒"),
    ("7817162132", "杨博文"),
    ("3177765082", "陈浚铭"),
]

COOKIE = os.environ.get("WEIBO_COOKIE", "")
if not COOKIE:
    raise ValueError("未设置 WEIBO_COOKIE 环境变量")

def extract_xsrf(cookie):
    match = re.search(r'XSRF-TOKEN=([^;]+)', cookie)
    return match.group(1) if match else ""

def fetch_user(uid, cookie):
    url = f"https://weibo.com/ajax/profile/info?uid={uid}&scene=profile"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Cookie": cookie,
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": extract_xsrf(cookie),
        "Referer": f"https://weibo.com/u/{uid}?tabtype=superTopic",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("ok") == 1 and "user" in data.get("data", {}):
        user = data["data"]["user"]
        counter = user.get("status_total_counter", {})
        return {
            "comment": int(counter.get("comment_cnt", 0)),
            "repost": int(counter.get("repost_cnt", 0)),
            "like": int(counter.get("like_cnt", 0)),
            "total": int(counter.get("total_cnt", 0)),
            "followers": int(user.get("followers_count", 0))
        }
    return None

def main():
    current = {}
    for uid, name in USER_LIST:
        try:
            info = fetch_user(uid, COOKIE)
            if info:
                current[uid] = info
                print(f"✅ {name} 获取成功")
        except Exception as e:
            print(f"❌ {name} 失败: {e}")

    # 读取现有 data.json
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            old_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        old_data = {}

    # 判断是否需要更新 baseline（如果日期改变或不存在）
    today_str = datetime.now(TZ).strftime("%Y-%m-%d")
    baseline = old_data.get("baseline", {})
    if old_data.get("date") != today_str or not baseline:
        # 新的一天，用当前数据作为基准
        baseline = {uid: {k: v for k, v in info.items() if k != "followers"} for uid, info in current.items()}
        print("📅 已更新今日基准数据")

    new_data = {
        "date": today_str,
        "baseline": baseline,
        "current": current,
        "update_time": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print("💾 数据已保存到 data.json")

if __name__ == "__main__":
    main()
