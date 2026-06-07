import requests
import json
import os
import re
from datetime import datetime, timezone, timedelta

# 北京时间
TZ = timezone(timedelta(hours=8))

# 用户UID与姓名
USER_LIST = [
    ("6353131515", "张桂源"),
    ("7740929779", "张函瑞"),
    ("3625607515", "王橹杰"),
    ("3448351424", "左奇函"),
    ("6320179782", "陈奕恒"),
    ("7817162132", "杨博文"),
    ("3177765082", "陈浚铭"),
]

COOKIE = os.environ.get("WEIBO_COOKIE")
if not COOKIE:
    raise RuntimeError("环境变量 WEIBO_COOKIE 未设置")

def extract_xsrf(cookie: str) -> str:
    """从 Cookie 中提取 XSRF-TOKEN"""
    match = re.search(r'XSRF-TOKEN=([^;]+)', cookie)
    return match.group(1) if match else ""

def fetch_user(uid: str, cookie: str) -> dict:
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
    else:
        raise ValueError("API 返回异常：" + json.dumps(data, ensure_ascii=False))

def main():
    # 1. 获取当前所有用户的最新数据
    current = {}
    for uid, name in USER_LIST:
        try:
            info = fetch_user(uid, COOKIE)
            current[uid] = info
            print(f"✅ {name} 数据获取成功")
        except Exception as e:
            print(f"❌ {name} 获取失败：{e}")

    if not current:
        print("未获取到任何数据，退出")
        return

    # 2. 读取旧的 data.json（若存在）
    old_data = {}
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            old_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # 3. 处理 baseline（今日0点基准数据）
    today_str = datetime.now(TZ).strftime("%Y-%m-%d")
    baseline = old_data.get("baseline", {})
    # 如果日期改变或没有基准数据，则用当前数据更新基准
    if old_data.get("date") != today_str or not baseline:
        baseline = {}
        for uid, info in current.items():
            baseline[uid] = {
                "comment": info["comment"],
                "repost": info["repost"],
                "like": info["like"],
                "total": info["total"]
            }
        print("📅 已刷新今日基准数据（新的一天）")

    # 4. 构造新的 data.json
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
