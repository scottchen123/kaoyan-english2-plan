#!/usr/bin/env python3
"""把英语2的md转成每天一页的html。只处理本仓库9个文件的固定格式。"""
import html
import re
import sys
from pathlib import Path

SRC = Path(__file__).parent
DST = SRC / "docs"
DST.mkdir(exist_ok=True)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:#f4f6fa;color:#1f2937;line-height:1.8}
.hero{background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff;padding:24px 20px 20px}
.hero h1{font-size:1.25em;margin-bottom:4px}
.hero .sub{opacity:.85;font-size:.85em}
.wrap{max-width:760px;margin:0 auto;padding:16px 14px 40px}
h2{font-size:1.15em;margin:22px 0 10px;padding:10px 14px;background:#fff;border-radius:10px;border-left:5px solid #3b82f6;box-shadow:0 1px 3px rgba(0,0,0,.08)}
h3{font-size:1em;margin:16px 0 8px;color:#1e40af}
p{margin:8px 0}
.en{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;font-family:Georgia,"Times New Roman",serif;line-height:1.9;box-shadow:0 1px 3px rgba(0,0,0,.06)}
blockquote{border-left:3px solid #93c5fd;margin:10px 0;padding:8px 14px;color:#374151;background:#eff6ff;border-radius:0 8px 8px 0}
details{border:1px solid #bfdbfe;border-radius:10px;margin:12px 0;padding:8px 12px;background:#eff6ff}
details details{background:#fff;border-color:#ddd}
summary{cursor:pointer;font-weight:bold;color:#1e40af;padding:4px 0}
code{background:#eef2ff;padding:1px 6px;border-radius:4px;font-size:.92em}
pre{background:#1f2937;color:#f8f8f2;padding:12px;border-radius:10px;overflow-x:auto}
pre code{background:none;color:inherit}.right{text-align:right;color:#6b7280}
.task{display:flex;gap:10px;align-items:flex-start;background:#fff;border-radius:10px;padding:12px 14px;margin:8px 0;box-shadow:0 1px 3px rgba(0,0,0,.06);cursor:pointer}
.task input{width:20px;height:20px;margin-top:4px;flex-shrink:0;accent-color:#16a34a}
.navtop{display:block;text-align:center;background:#fff;border-radius:10px;padding:12px;margin-bottom:6px;text-decoration:none;color:#1e40af;font-weight:bold;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.pager{display:flex;gap:10px;margin-top:24px}
.pager a{flex:1;text-align:center;background:#fff;border-radius:10px;padding:12px;text-decoration:none;color:#1e40af;font-weight:bold;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.pager a.empty{visibility:hidden}
.toc{background:#fff;border-radius:10px;padding:12px 14px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.toc .t{font-weight:bold;margin-bottom:6px;color:#1e40af}
.toc a{display:inline-block;margin:3px 6px 3px 0;padding:4px 12px;background:#eff6ff;border-radius:16px;text-decoration:none;color:#1e40af;font-size:.88em}
.letter{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.letter .lhead{font-weight:bold}
.opt{display:block;width:100%;text-align:left;background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:10px 14px;margin:8px 0;cursor:pointer;font-size:.95em;line-height:1.7;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.opt b{color:#1e40af;margin-right:4px}
.opt.right{border-color:#16a34a;background:#f0fdf4}
.opt.right b{color:#16a34a}
.opt.wrong{border-color:#dc2626;background:#fef2f2}
.opt.wrong b{color:#dc2626}
.grp{display:flex;justify-content:space-between;align-items:center;background:#fff;border-radius:10px;padding:10px 14px;margin:14px 0 8px;font-weight:bold;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.grp .fold{border:1px solid #bfdbfe;background:#eff6ff;color:#1e40af;border-radius:16px;padding:2px 14px;cursor:pointer;font-size:.85em}
details.enwrap{background:#fff;border-color:#e5e7eb}
details.enwrap summary{color:#374151;font-weight:normal}
.fab{position:fixed;right:14px;width:44px;height:44px;border-radius:50%;border:none;background:#1e40af;color:#fff;font-size:18px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25);display:none;z-index:99}
#fabTop{bottom:70px}#fabBot{bottom:16px}
.donebtn{display:block;width:100%;border:none;background:linear-gradient(135deg,#16a34a,#22c55e);color:#fff;font-size:1.05em;font-weight:bold;border-radius:12px;padding:14px;margin-top:20px;cursor:pointer;box-shadow:0 2px 6px rgba(22,163,74,.35)}
.donebtn.done{background:#9ca3af;box-shadow:none}
table{border-collapse:collapse;width:100%;margin:10px 0;background:#fff;border-radius:8px;overflow:hidden}
td,th{border:1px solid #e5e7eb;padding:8px 10px;text-align:left}
"""

JS = """
document.querySelectorAll('input[type=checkbox][data-k]').forEach(function(b){
  var k='kx_'+b.getAttribute('data-k');
  if(localStorage.getItem(k)==='1'){b.checked=true;}
  b.addEventListener('change',function(){
    localStorage.setItem(k,b.checked?'1':'0');
  });
});
document.querySelectorAll('[data-complete]').forEach(function(b){
  var k='kx_'+b.getAttribute('data-complete');
  function sync(){if(localStorage.getItem(k)==='1'){b.classList.add('done');b.textContent='已完成 ✓ 打卡成功';}}
  sync();
  b.addEventListener('click',function(){localStorage.setItem(k,'1');sync();});
});
window.addEventListener('scroll',function(){
  var y=window.scrollY||document.documentElement.scrollTop;
  var show=y>400;
  var t=document.getElementById('fabTop'),b=document.getElementById('fabBot');
  if(!t||!b)return;
  t.style.display=show?'block':'none';
  if(show){
    var nearBot=(window.innerHeight+y)>=(document.body.scrollHeight-120);
    b.style.display=nearBot?'none':'block';
  }else{b.style.display='none';}
});
function goTop(){window.scrollTo({top:0,behavior:'smooth'});}
function goBot(){window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});}
function toggleGrp(btn){
  var g=btn.closest('.grp');
  var hide=g.classList.toggle('off');
  btn.textContent=hide?'展开':'收起';
  var el=g.nextElementSibling;
  while(el&&!el.classList.contains('grp')&&el.tagName!=='H2'&&el.tagName!=='HR'){
    el.style.display=hide?'none':'';
    el=el.nextElementSibling;
  }
}
document.querySelectorAll('button.opt').forEach(function(b){
  b.addEventListener('click',function(){
    var q=b.getAttribute('data-q');
    var parts=q.split('-q');
    var qnum=parts[1];
    var ans=b.getAttribute('data-ans')||'';
    if(!ans){
      var re=new RegExp('(?:^|\\s)'+qnum+'\\.\\s*([ABCD])');
      var details=document.querySelectorAll('details');
      for(var i=0;i<details.length;i++){
        var t=details[i].textContent||'';
        var mm=t.match(re);
        if(mm){ans=mm[1];break;}
      }
    }
    document.querySelectorAll('button.opt[data-q="'+q+'"]').forEach(function(o){o.classList.remove('right','wrong');});
    if(ans&&b.getAttribute('data-o')===ans){b.classList.add('right');}
    else if(ans){b.classList.add('wrong');}
    else{b.classList.add('right');}
    try{localStorage.setItem('kx_'+q+'_'+b.getAttribute('data-o'),'1');}catch(e){}
  });
});
(function(){
  var boxes=document.querySelectorAll('input[type=checkbox][data-k]');
  var sub=document.getElementById('heroSub');
  function count(){
    var n=0;boxes.forEach(function(b){if(b.checked)n++;});
    if(sub&&boxes.length){sub.textContent=sub.getAttribute('data-base')+' · 本页 '+n+'/'+boxes.length;}
  }
  if(sub){sub.setAttribute('data-base',sub.textContent);}
  boxes.forEach(function(b){b.addEventListener('change',count);});
  count();
})();
"""

_counter = [0]
TOC = [[]]
ENBUF = [[]]
LETBUF = [[]]
INLETTER = [False]
QIDS = [0]
GIDS = [0]


def esc(t):
    return html.escape(t)


def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def convert(md_text, page):
    lines = md_text.split("\n")
    out = []
    i = 0
    n = len(lines)
    in_code = False
    code_buf = []
    seen_h1 = False
    while i < n:
        ln = lines[i]
        text = ln.strip()
        if ln.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + esc("\n".join(code_buf)) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(ln)
            i += 1
            continue
        # NOTE折叠块（body递归转，支持嵌套NOTE；递归层已剥>，故两种开头都接受；
        # body收到下一个同级标题/分隔线/文件尾为止，避免内层body非>行被截断）
        m = re.match(r"(?:>\s*)?\[!NOTE\]-(.*)", ln)
        if m and (ln.startswith(">") or ln.startswith("[!NOTE]-")):
            title = m.group(1).strip() or "展开"
            body = []
            i += 1
            while i < n:
                cur = lines[i]
                if re.match(r"#{1,3}\s+", cur) or cur.strip() == "---":
                    break
                if cur.startswith(">"):
                    body.append(re.sub(r"^>\s?", "", cur, count=1))
                else:
                    body.append(cur)
                i += 1
            inner = convert("\n".join(body), page) if body else ""
            out.append("<details><summary>" + esc(title) + "</summary>" + inner + "</details>")
            continue
        # 普通引用块（内容递归转，支持嵌套NOTE：只剥一层>）
        if ln.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i], count=1))
                i += 1
            inner = convert("\n".join(buf), page)
            # 递归结果若全是段落则包回引用，否则直接展开（details不嵌套在引用里）
            if "<details>" in inner or "<h" in inner:
                out.append(inner)
            else:
                out.append("<blockquote>" + inner + "</blockquote>")
            continue
        # div右对齐（信件内落款由信件分支处理，这里跳过）
        if '<div style="text-align:right">' in ln and not INLETTER[0]:
            t = ln.replace('<div style="text-align:right">', "").replace("</div>", "").replace("<br>", "\n")
            out.append('<p class="right">' + "<br>".join(inline(x) for x in t.split("\n")) + "</p>")
            i += 1
            continue
        # 标题（内容里h1全部降为h2，页面标题已是h1；h2收进目录）
        m = re.match(r"(#{1,3})\s+(.*)", ln)
        if m:
            lv = min(len(m.group(1)) + 1, 3)
            text = m.group(2).strip()
            if lv == 2:
                aid = f"{page}-s{len(TOC[0])}"
                TOC[0].append((aid, text))
                out.append(f'<h2 id="{aid}">' + inline(text) + "</h2>")
            else:
                out.append(f"<h{lv}>" + inline(text) + f"</h{lv}>")
            i += 1
            continue
        # 表格
        if ln.startswith("|") and i + 1 < n and re.match(r"\|[\s:\-|]+\|", lines[i + 1]):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            t = ["<table>"]
            for r_i, r in enumerate(rows):
                if r_i == 1:
                    continue
                tag = "th" if r_i == 0 else "td"
                t.append("<tr>" + "".join(f"<{tag}>" + inline(c) + f"</{tag}>" for c in r) + "</tr>")
            t.append("</table>")
            out.append("".join(t))
            continue
        # 任务复选
        m = re.match(r"\s*-\s*\[ \]\s*(.*)", ln)
        if m:
            _counter[0] += 1
            out.append(
                '<label class="task"><input type="checkbox" data-k="'
                + page + "_" + str(_counter[0])
                + '"><span>' + inline(m.group(1)) + "</span></label>"
            )
            i += 1
            continue
        # 无序列表
        m = re.match(r"\s*-\s+(.*)", ln)
        if m:
            buf = []
            while i < n:
                mm = re.match(r"\s*-\s+(.*)", lines[i])
                if not mm:
                    break
                buf.append("<li>" + inline(mm.group(1)) + "</li>")
                i += 1
            out.append("<ul>" + "".join(buf) + "</ul>")
            continue
        # 分隔线
        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        # 空行
        if not ln.strip():
            i += 1
            continue
        # 信件成篇：Dear开头收到落款div，包成letter卡
        if re.match(r"Dear\s", text) and not INLETTER[0]:
            INLETTER[0] = True
            LETBUF[0] = [f'<p class="lhead">{inline(text)}</p>']
            i += 1
            continue
        if INLETTER[0]:
            if 'text-align:right' in ln:
                t = ln.replace('<div style="text-align:right">', "").replace("</div>", "").replace("<br>", "\n")
                LETBUF[0].append('<p class="right">' + "<br>".join(inline(x) for x in t.split("\n")) + "</p>")
                out.append('<div class="letter">' + "".join(LETBUF[0]) + "</div>")
                LETBUF[0] = []
                INLETTER[0] = False
            elif text:
                LETBUF[0].append(f"<p>{inline(text)}</p>")
            i += 1
            continue
        # 题目选项A：题干行(数字开头)+下一行四选项连写（题干尾? X自带答案则剥离）
        mopt = re.match(r"(\d+)\.\s+(.*)", text)
        if mopt and i + 1 < n and re.search(r"\bA\.\s", lines[i + 1]) and re.search(r"\sB\.\s", lines[i + 1]):
            qnum = mopt.group(1)
            stem = mopt.group(2)
            given = ""
            mg = re.match(r"(.*\?)\s+([ABCD])\s*$", stem)
            if mg:
                stem, given = mg.group(1), mg.group(2)
            oline = lines[i + 1].strip()
            parts = re.split(r"\s(?=[ABCD]\.\s)", oline)
            opts = [p for p in parts if re.match(r"[ABCD]\.\s", p)]
            out.append(f"<p><strong>{qnum}. {inline(stem)}</strong></p>")
            for o in opts:
                extra = f' data-ans="{given}"' if given else ""
                out.append(
                    f'<button class="opt" data-q="{page}-q{qnum}" data-o="{o[0]}"{extra}><b>{o[0]}.</b> {inline(o[3:].strip())}</button>'
                )
            i += 2
            continue
        # 题目选项B：一行内题干+四选项连写
        if mopt and re.search(r"\bA\.\s", text) and re.search(r"\sB\.\s", text):
            qnum = mopt.group(1)
            rest = mopt.group(2)
            parts = re.split(r"\s(?=[ABCD]\.\s)", rest)
            stem = parts[0] if not re.match(r"[ABCD]\.\s", parts[0]) else ""
            opts = [p for p in parts if re.match(r"[ABCD]\.\s", p)]
            if stem:
                out.append(f"<p><strong>{qnum}. {inline(stem)}</strong></p>")
            else:
                out.append(f"<p><strong>{qnum}.</strong></p>")
            for o in opts:
                out.append(
                    f'<button class="opt" data-q="{page}-q{qnum}" data-o="{o[0]}"><b>{o[0]}.</b> {inline(o[3:].strip())}</button>'
                )
            i += 1
            continue
        # 题目选项C：题干行+下面四行各一个选项(4空格缩进)
        if mopt and i + 1 < n and re.match(r"\s{2,}A\.\s", lines[i + 1]):
            qnum = mopt.group(1)
            stem = mopt.group(2)
            out.append(f"<p><strong>{qnum}. {inline(stem)}</strong></p>")
            i += 1
            while i < n:
                mom = re.match(r"\s{2,}([ABCD])\.\s*(.*)", lines[i])
                if not mom:
                    break
                out.append(
                    f'<button class="opt" data-q="{page}-q{qnum}" data-o="{mom.group(1)}"><b>{mom.group(1)}.</b> {inline(mom.group(2).strip())}</button>'
                )
                i += 1
            continue
        # 分组标题：**原文：**/**5题：**等独占一行，转成分组头（可收起下属内容）
        mgrp = re.match(r"\*\*(.+：)\*\*\s*$", text)
        if mgrp:
            GIDS[0] += 1
            out.append(
                f'<div class="grp" data-grp="{page}-g{GIDS[0]}"><span>{esc(mgrp.group(1))}</span>'
                f'<button class="fold" onclick="toggleGrp(this)">收起</button></div>'
            )
            i += 1
            continue
        # 普通段落：纯英文长段暂存，连续英文段合并成一篇en卡片
        if len(text) > 120 and re.search(r"[A-Za-z]{3,}", text) and not re.search(
            r"[一-鿿]", text
        ):
            ENBUF[0].append(inline(text))
            i += 1
            continue
        if ENBUF[0]:
            out.append('<div class="en">' + "".join(f"<p>{p}</p>" for p in ENBUF[0]) + "</div>")
            ENBUF[0] = []
        if not text:
            i += 1
            continue
        out.append("<p>" + inline(text) + "</p>")
        i += 1
    if ENBUF[0]:
        out.append('<div class="en">' + "".join(f"<p>{p}</p>" for p in ENBUF[0]) + "</div>")
        ENBUF[0] = []
    return "\n".join(out)


ORDER = ["day01-11", "day12-18", "day19-25", "day26-32", "day33-39", "day40", "sucai"]
DONEKEY = {
    "day01-11": "idx_01",
    "day12-18": "idx_12", "day19-25": "idx_19", "day26-32": "idx_26",
    "day33-39": "idx_33", "day40": "idx_40",
}


SUBS = {
    "day01-11": "小作文上旬 · 建议到备忘录 + 2019–2021 阅读",
    "day12-18": "小作文下旬 + 图表入门 + 翻译",
    "day19-25": "2022–2023 阅读 + 大作文 + 翻译",
    "day26-32": "2024–2025 阅读 + 大作文 + 翻译",
    "day33-39": "模考 + 总复盘",
    "day40": "补课 · 两篇阅读",
    "sucai": "15 种范文 + 万能模板 + 理由库",
}


def page(title, body, back=True, name=""):
    nav = '<a class="navtop" href="index.html">← 返回计划</a>' if back else ""
    pager = ""
    done = ""
    toc = ""
    if TOC[0]:
        links = "".join(f'<a href="#{a}">{esc(t[:14])}</a>' for a, t in TOC[0])
        toc = f'<div class="toc"><div class="t">本页目录</div>{links}</div>'
    if name in ORDER:
        k = ORDER.index(name)
        prev = (
            f'<a href="{ORDER[k-1]}.html">← 上一个</a>' if k > 0 else '<a class="empty"></a>'
        )
        nxt = (
            f'<a href="{ORDER[k+1]}.html">下一个 →</a>'
            if k < len(ORDER) - 1
            else '<a class="empty"></a>'
        )
        pager = f'<div class="pager">{prev}{nxt}</div>'
        if name in DONEKEY:
            done = f'<button class="donebtn" data-complete="{DONEKEY[name]}">本阶段完成，打卡</button>'
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head><body>
<div class="hero"><h1>{esc(title)}</h1><div class="sub" id="heroSub">{esc(SUBS.get(name, "考研英语二背诵计划 · 进度自动保存在本机"))}</div></div>
<div class="wrap">
{nav}
{toc}
{body}{done}{pager}<button class="fab" id="fabTop" onclick="goTop()">↑</button><button class="fab" id="fabBot" onclick="goBot()">↓</button><script>{JS}</script></div></body></html>"""


PAGES = [
    ("Day01-Day11-小作文第一轮.md", "Day01–Day11"),
    ("Day12-Day18-小作文第三轮.md", "Day12–Day18"),
    ("Day19-Day25-阅读大作文翻译.md", "Day19–Day25"),
    ("Day26-Day32-阅读大作文翻译.md", "Day26–Day32"),
    ("Day33-Day39-收尾模考总复盘.md", "Day33–Day39"),
    ("Day40-补齐2020T1与2021T1.md", "Day40 补课"),
    ("考研英语范文.md", "作文素材与模板"),
]

INDEX_BODY = """
<p>每天 1 小时（模考日 2 小时），2019–2025 英语二真题全覆盖。阅读 28 篇、大作文 5 套数据、翻译 7 篇、小作文 15 种类型。勾选进度会自动保存在本机浏览器。</p>
<h2>按顺序做</h2>
<ul>
<li><a href="day03.html">Day03 道歉信</a> — 道歉信 + 2019-T1</li>
<li><a href="day04.html">Day04 投诉信</a> — 投诉信 + 2019-T2</li>
<li><a href="day05-11.html">Day05–Day11</a> — 祝贺/求职/推荐/告示/咨询/备忘录 + 2019-T3/T4、2020-T2/T3/T4、2021-T2</li>
<li><a href="day12-18.html">Day12–Day18</a> — 倡议/致编辑/辞职/失物 + 2021-T3/T4、2022-T1/T2 + 大作文×2 + 翻译×1</li>
<li><a href="day19-25.html">Day19–Day25</a> — 2022-T3/T4、2023-T1–T4 + 健康大作文 + 翻译×3</li>
<li><a href="day26-32.html">Day26–Day32</a> — 2024-T1–T4、2025-T1/T2 + 劳动/休闲大作文 + 翻译×3</li>
<li><a href="day33-39.html">Day33–Day39</a> — 2025-T3/T4 + 2019/2024全套模考 + 总复盘</li>
<li><a href="day40.html">Day40 补课</a> — 2020-T1机器鼠、2021-T1再培训</li>
<li><a href="sucai.html">作文素材与模板</a> — 15种小作文范文 + 大作文万能模板 + 理由库</li>
</ul>
<h2>答案速查（28 篇阅读）</h2>
<ul>
<li>2019：T1 D C A C A / T2 B B D C A / T3 C D B A B / T4 B B D D C</li>
<li>2020：T1 A D B C D / T2 C D B D A / T3 D D A D B / T4 D C D B B</li>
<li>2021：T1 B A D C B / T2 B C C A B / T3 A B C C A / T4 B A A D B</li>
<li>2022：T1 D C C B A / T2 D A C D A / T3 C D B B B / T4 A B D C C</li>
<li>2023：T1 A B B C D / T2 D A C B D / T3 C D A A B / T4 A C D B A</li>
<li>2024：T1 C C D A D / T2 A A B D C / T3 C D B B B / T4 A A D B D</li>
<li>2025：T1 B C A D A / T2 B C C B C / T3 A B A B D / T4 C D A D D</li>
</ul>
"""


def main():
    only = sys.argv[1:] or None
    names = {
        "Day01-Day11-小作文第一轮.md": "day01-11",
        "Day12-Day18-小作文第三轮.md": "day12-18",
        "Day19-Day25-阅读大作文翻译.md": "day19-25",
        "Day26-Day32-阅读大作文翻译.md": "day26-32",
        "Day33-Day39-收尾模考总复盘.md": "day33-39",
        "Day40-补齐2020T1与2021T1.md": "day40",
        "考研英语范文.md": "sucai",
    }
    for src, title in PAGES:
        if only and src not in only:
            continue
        md = (SRC / src).read_text(encoding="utf-8")
        TOC[0] = []
        ENBUF[0] = []
        LETBUF[0] = []
        INLETTER[0] = False
        body = convert(md, names[src])
        (DST / (names[src] + ".html")).write_text(page(title, body, name=names[src]), encoding="utf-8")
        print("wrote", names[src] + ".html", len(body), "chars")
    print("skip index.html (hand-maintained)")


if __name__ == "__main__":
    main()
