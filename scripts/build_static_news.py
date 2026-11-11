#!/usr/bin/env python3
"""Rebuild readable static news cards from saved editorial and RSS snapshots.
The browser enhances this fallback with Ollie's filters, comments and expand buttons.
No source facts are generated here.
"""
import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

root=Path(__file__).resolve().parents[1]
data=json.loads((root/"news.json").read_text(encoding="utf-8"))
editorial=json.loads((root/"editorial.json").read_text(encoding="utf-8"))
src=(root/"index.html").read_text(encoding="utf-8")
esc=lambda x: html.escape(str(x or ""),quote=True)
articles=[]
for x in editorial.get("items",[]):
    if str(x.get("url","")).startswith("https://"): articles.append((x,True))
for x in data.get("items",[]):
    if str(x.get("url","")).startswith("https://"): articles.append((x,False))
cards=[]
for x,is_editorial in articles:
    title=str(x.get("title",""))
    body=str(x.get("body",""))
    published=str(x.get("date") or x.get("published",""))[:10]
    category=str(x.get("category") or x.get("source") or "NEWS")
    # The visible date is the original source date, not the date this edition was assembled.
    intro=body
    if len(body)>235:
        intro=body[:235].rsplit(" ",1)[0]+"…"
    extra=''
    if len(body)>235:
        extra='<details class="static-expand"><summary>＋ Expand</summary><p>'+esc(body)+'</p></details>'
    link=esc(x.get("url"))
    more=''
    if x.get("full_url"):
        more='<a class="news-full-link" href="'+esc(x["full_url"])+'">Read full post ↗</a>'
    source=esc(x.get("source","linked reporting"))
    byline=esc(x.get("byline") or "UI News Desk")
    cards.append('<article class="card"><div class="tag">'+esc(category)+' · '+esc(published)+'</div><h2><a href="'+link+'">'+esc(title)+'</a></h2>'+('<p>'+esc(intro)+'</p>'+extra if body else '')+'<small>— '+byline+' · Source: '+source+'</small>'+more+'</article>')
block=''.join(cards) or '<div class="empty">No saved headlines available.</div>'
start='<!-- NEWS_SNAPSHOT_START -->'
end='<!-- NEWS_SNAPSHOT_END -->'
if src.count(start)!=1 or src.count(end)!=1:raise RuntimeError("Missing unique news snapshot markers")
src=re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda _: start+block+end,src,flags=re.S)
built=data.get("updated_at")
if built:
    try:
        when=dt.datetime.fromisoformat(built.replace("Z","+00:00")).astimezone(ZoneInfo("America/Chicago"))
        label="Last automatic build: "+when.strftime("%b %-d, %Y · %-I:%M %p Central")
    except (ValueError,TypeError): label="Automatic build timestamp unavailable"
else: label="No successful automatic build yet"
label+=" · Editorial edition: "+str(editorial.get("edition","not dated"))
src=re.sub(r'(<span id="updated">).*?(</span>)',lambda m:m.group(1)+esc(label)+m.group(2),src,count=1,flags=re.S)
src=re.sub(r'(<span id="count">).*?(</span>)',lambda m:m.group(1)+str(len(articles))+' source-linked stories'+m.group(2),src,count=1,flags=re.S)
(root/"index.html").write_text(src,encoding="utf-8")
print("Saved readable HTML snapshot:",len(cards),"cards; ",label)
