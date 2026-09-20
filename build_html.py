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
"""

_counter = [0]


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
        # div右对齐
        if '<div style="text-align:right">' in ln:
            t = ln.replace('<div style="text-align:right">', "").replace("</div>", "").replace("<br>", "\n")
            out.append('<p class="right">' + "<br>".join(inline(x) for x in t.split("\n")) + "</p>")
            i += 1
            continue
        # 标题（内容里h1全部降为h2，页面标题已是h1）
        m = re.match(r"(#{1,3})\s+(.*)", ln)
        if m:
            lv = min(len(m.group(1)) + 1, 3)
            out.append(f"<h{lv}>" + inline(m.group(2)) + f"</h{lv}>")
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
        # 普通段落（纯英文长段加en卡片样式）
        text = ln.strip()
        if len(text) > 120 and re.search(r"[A-Za-z]{3,}", text) and not re.search(
            r"[一-鿿]", text
        ):
            out.append('<p class="en">' + inline(text) + "</p>")
        else:
            out.append("<p>" + inline(text) + "</p>")
        i += 1
    return "\n".join(out)


ORDER = ["day03", "day04", "day05-11", "day12-18", "day19-25", "day26-32", "day33-39", "day40", "sucai"]
DONEKEY = {
    "day03": "idx_01", "day04": "idx_01", "day05-11": "idx_01",
    "day12-18": "idx_12", "day19-25": "idx_19", "day26-32": "idx_26",
    "day33-39": "idx_33", "day40": "idx_40",
}


def page(title, body, back=True, name=""):
    nav = '<a class="navtop" href="index.html">← 返回计划</a>' if back else ""
    pager = ""
    done = ""
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
<div class="hero"><h1>{esc(title)}</h1><div class="sub">考研英语二背诵计划 · 进度自动保存在本机</div></div>
<div class="wrap">
{nav}
{body}{done}{pager}<script>{JS}</script></div></body></html>"""


PAGES = [
    ("Day03-道歉信.md", "Day03 道歉信"),
    ("Day04-投诉信.md", "Day04 投诉信"),
    ("Day05-Day11-小作文第二轮.md", "Day05–Day11"),
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
        "Day03-道歉信.md": "day03",
        "Day04-投诉信.md": "day04",
        "Day05-Day11-小作文第二轮.md": "day05-11",
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
        body = convert(md, names[src])
        (DST / (names[src] + ".html")).write_text(page(title, body, name=names[src]), encoding="utf-8")
        print("wrote", names[src] + ".html", len(body), "chars")
    print("skip index.html (hand-maintained)")


if __name__ == "__main__":
    main()
