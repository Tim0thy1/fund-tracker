#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过 Server酱(ServerChan) 推送基金盈亏到微信
============================================
读取 data/funds.json，计算每只基金当日盈亏与累计盈亏，推送到微信。
需要 GitHub Secret: SERVERCHAN_KEY（Server酱 SendKey）

用法：SERVERCHAN_KEY=xxx python3 scripts/notify_wechat.py
"""
import json, os, datetime, urllib.request, urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "funds.json")


def main():
    sendkey = os.environ.get("SERVERCHAN_KEY", "").strip()
    if not sendkey:
        print("[跳过] 未配置 SERVERCHAN_KEY，跳过微信通知")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    funds = data["funds"]

    today = datetime.date.today().strftime("%m月%d日")
    lines = []
    total_day_pnl = 0.0
    total_pnl = 0.0
    total_cost = 0.0

    for fund in funds:
        shares = float(fund["shares"])
        cost = float(fund["cost"])
        nav = float(fund["nav"])
        prev_nav = fund.get("prev_nav")

        market_value = shares * nav
        cost_value = shares * cost
        pnl = market_value - cost_value
        pnl_pct = pnl / cost_value * 100 if cost_value else 0.0
        total_pnl += pnl
        total_cost += cost_value

        if prev_nav:
            prev_nav = float(prev_nav)
            day_pnl = shares * (nav - prev_nav)
            day_pct = (nav - prev_nav) / prev_nav * 100
            total_day_pnl += day_pnl
            day_str = f"当日 **{day_pnl:+.2f}** 元（{day_pct:+.2f}%）"
        else:
            day_str = "当日暂无对比数据"

        lines.append(f"### {fund['name']}（{fund['code']}）")
        lines.append(f"- 净值 {nav}（{fund.get('nav_date', '')}）")
        lines.append(f"- {day_str}")
        lines.append(f"- 累计 **{pnl:+.2f}** 元（{pnl_pct:+.2f}%）")
        lines.append("")

    total_pnl_pct = total_pnl / total_cost * 100 if total_cost else 0.0
    title = f"基金日报 {today}｜合计 {total_pnl:+.2f} 元（{total_pnl_pct:+.2f}%）"
    desp = "\n".join(lines)
    desp += f"---\n**当日合计：{total_day_pnl:+.2f} 元**\n**累计合计：{total_pnl:+.2f} 元（{total_pnl_pct:+.2f}%）**"

    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    payload = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read().decode("utf-8"))
    if resp.get("code") == 0:
        print(f"[成功] 微信通知已发送：{title}")
    else:
        print(f"[失败] Server酱返回：{resp.get('message', resp)}")


if __name__ == "__main__":
    main()
