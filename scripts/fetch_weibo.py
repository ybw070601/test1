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
        
        def to_int(value):
            if value is None:
                return 0
            if isinstance(value, int):
                return value
            # 去除逗号（千位分隔符）并转换为整数
            return int(str(value).replace(',', ''))
        
        return {
            "comment": to_int(counter.get("comment_cnt")),
            "repost": to_int(counter.get("repost_cnt")),
            "like": to_int(counter.get("like_cnt")),
            "total": to_int(counter.get("total_cnt")),
            "followers": to_int(user.get("followers_count"))
        }
    else:
        raise ValueError("API 返回异常：" + json.dumps(data, ensure_ascii=False))
