#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实盘基金净值自动同步脚本
========================
从天天基金拉取持仓基金的最新净值，更新 data/funds.json。
QDII 基金净值 T+1/T+2 更新，无盘中实时估值。

用法：python3 scripts/sync_funds.py
"""
import json, os, sys, datetime, urllib.request, urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "funds.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://fund.eastmoney.com/",
}


def fetch_fund(code):
    """通过天天基金搜索接口获取基金基本信息与最新净值"""
    url = "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?" + urllib.parse.urlencode(
        {"m": 1, "key": code}
    )
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not data.get("Datas"):
        raise RuntimeError(f"基金 {code} 未找到")
    info = data["Datas"][0]["FundBaseInfo"]
    return {
        "code": info["FCODE"],
        "name": info["SHORTNAME"],
        "type": info.get("FTYPE", ""),
        "company": info.get("JJGS", ""),
        "manager": info.get("JJJL", ""),
        "nav": info.get("DWJZ"),
        "nav_date": info.get("FSRQ"),
    }


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    for fund in data["funds"]:
        code = fund["code"]
        try:
            info = fetch_fund(code)
            nav = info["nav"]
            nav_date = info["nav_date"]
            if nav is None:
                print(f"[跳过] {code} {info['name']}：无净值数据")
                continue
            old_nav = fund.get("nav")
            if old_nav != nav or fund.get("nav_date") != nav_date:
                fund["nav"] = nav
                fund["nav_date"] = nav_date
                fund["name"] = info["name"]
                fund["type"] = info["type"]
                fund["company"] = info["company"]
                fund["manager"] = info["manager"]
                changed = True
                print(f"[更新] {code} {info['name']} 净值 {old_nav} -> {nav} ({nav_date})")
            else:
                print(f"[不变] {code} {info['name']} 净值 {nav} ({nav_date})")
        except Exception as e:
            print(f"[错误] {code}: {e}")

    if changed:
        data["synced_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n已更新: {DATA_FILE}")
    else:
        print("\n净值无变化，无需写入")


if __name__ == "__main__":
    main()
