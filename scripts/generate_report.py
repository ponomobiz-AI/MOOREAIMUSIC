"""
DR DB KUSH 2.0 — Full Daily Intelligence Suite
Runs via GitHub Actions at 7 AM Denver time.

3-tab dashboard:
  Tab 1 — My Channel Summary  (stats, growth, health)
  Tab 2 — My Last 5 Videos    (AI audit: title, ideation, description, scripting, editing)
  Tab 3 — Competitor Intel    (last 24h uploads, outliers, breakout scores, recreate recs)
"""

import os, json, pathlib
import anthropic
from datetime import datetime
from dateutil import tz

# ── Config ─────────────────────────────────────────────────────────────────────
MY_CHANNEL_ID = os.environ.get("MY_CHANNEL_ID", "UCbkLhZ5uUnOejyQmtK5GOOw")
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
DENVER_TZ     = tz.gettz("America/Denver")
NOW_DENVER    = datetime.now(DENVER_TZ)
DATE_STR      = NOW_DENVER.strftime("%A, %B %-d %Y")
DATE_FILE     = NOW_DENVER.strftime("%Y-%m-%d")

COMPETITOR_IDS = [
    "@ATPmusic",
    "UCQHqRnIatHGQlxfgXKz5JpQ",
    "UCbwChnjsZXrD7GcWMiR_lBA",
    "UCBZwQbwEAw_cIeWDHVz7Azg",
    "UCLeVJzaHumte98Le_5rOvCQ",
    "UCocdLZMk9veRGuN5JxixAeQ",
]

VIDIQ_MCP_URL = "https://mcp.vidiq.com/mcp"

SYSTEM_PROMPT = f"""
You are a YouTube growth strategist for DR DB KUSH 2.0 — a Hip-hop / R&B / Soul / Gospel Trap artist channel.
Today is {DATE_STR}. Use the vidIQ MCP tools to gather live data, then return ONE JSON report.

STEP 1 — MY CHANNEL DATA
- Call vidiq_channel_stats for {MY_CHANNEL_ID}
- Call vidiq_channel_videos for {MY_CHANNEL_ID} (popular=false, long format) — take the 5 most recent
- Call vidiq_video_stats for each of those 5 videos (daily granularity)
- Call vidiq_channel_performance_trends for {MY_CHANNEL_ID}

STEP 2 — COMPETITOR DATA
- Call vidiq_channel_videos (popular=false, long) on competitor channels for last 24h uploads
- Call vidiq_outliers on competitor channels: publishedWithin=thisWeek, sort=breakoutScore, limit=8
- Call vidiq_channel_performance_trends on top 2 most active competitors

STEP 3 — ANALYSIS
For each of my 5 videos, provide a detailed audit of all 5 areas:
  - title: score 1-10, specific issue with THIS title, better rewrite
  - ideation: score 1-10, what concept/angle is weak or missing, stronger direction
  - description: score 1-10, what's missing, write an optimized 2-3 sentence description + relevant hashtags
  - scripting: score 1-10, what hook/structure is missing for this genre, specific fix
  - editing: score 1-10, what editing style/elements competitors use that are likely missing, specific suggestions

Return ONLY this JSON (no markdown fences):

{{
  "generated_at": "ISO timestamp",

  "my_channel": {{
    "subscribers": 0,
    "total_views": 0,
    "videos_published": 0,
    "subs_gained_30d": 0,
    "views_gained_30d": 0,
    "avg_views_per_video": 0,
    "channel_health": "growing|flat|declining",
    "health_note": "one sentence"
  }},

  "my_videos": [
    {{
      "video_id": "yt_id",
      "title": "exact title",
      "thumbnail": "url",
      "published_at": "ISO",
      "total_views": 0,
      "peak_vph": 0.0,
      "current_vph": 0.0,
      "likes": 0,
      "comments": 0,
      "vs_channel_avg": "above|at|below",
      "audit": {{
        "title":       {{"score":0,"issue":"","rewrite":""}},
        "ideation":    {{"score":0,"issue":"","suggestion":""}},
        "description": {{"score":0,"issue":"","rewrite":""}},
        "scripting":   {{"score":0,"issue":"","suggestion":""}},
        "editing":     {{"score":0,"issue":"","suggestion":""}}
      }}
    }}
  ],

  "competitor_summary": "2-3 sentences",

  "uploads_24h": [
    {{"channel":"","title":"","video_id":"","thumbnail":"","published_at":"","views":0,"vph":0.0,"breakout_score":0.0,"status":"hot|rising|normal"}}
  ],

  "top_outliers": [
    {{"channel":"","title":"","video_id":"","thumbnail":"","views":0,"vph":0.0,"breakout_score":0.0,"engagement_rate":0.0,"tags":[],"why_it_worked":""}}
  ],

  "recreate_recommendations": [
    {{"priority":"high|medium|low","concept":"","reason":"","inspired_by":"","suggested_tags":[]}}
  ],

  "watch_out": "one sentence warning or empty string",
  "daily_action": "single most important thing to do TODAY"
}}
""".strip()

USER_PROMPT = f"Generate the full daily report for {DATE_STR}. Competitor IDs: {json.dumps(COMPETITOR_IDS)}"


# ── API call ────────────────────────────────────────────────────────────────────
def fetch_report_data() -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    print(f"[{DATE_STR}] Calling Claude + vidIQ MCP...")
    response = client.beta.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT}],
        mcp_servers=[{"type": "url", "url": VIDIQ_MCP_URL, "name": "vidiq"}],
        betas=["mcp-client-2025-04-04"],
    )
    for block in reversed(response.content):
        if hasattr(block, "text") and block.text.strip().startswith("{"):
            return json.loads(block.text.strip())
    raise ValueError("No valid JSON in Claude response")


# ── Helpers ─────────────────────────────────────────────────────────────────────
def fmt(n):
    try: return f"{int(n):,}"
    except: return "—"

def score_styles(s):
    s = int(s)
    if s >= 8: return "#EAF3DE", "#0F6E56"
    if s >= 5: return "#FAEEDA", "#BA7517"
    return "#FAECE7", "#993C1D"

def health_badge(h):
    cfg = {"growing":("#EAF3DE","#0F6E56","↑ Growing"),"flat":("#FAEEDA","#BA7517","→ Flat"),"declining":("#FAECE7","#993C1D","↓ Declining")}
    bg, fg, lbl = cfg.get(h, cfg["flat"])
    return f'<span style="font-size:12px;padding:3px 12px;border-radius:20px;font-weight:600;background:{bg};color:{fg};">{lbl}</span>'

def status_badge(s):
    cfg = {"hot":("🔥","#FAECE7","#993C1D"),"rising":("↑","#EAF3DE","#3B6D11"),"normal":("—","#F1EFE8","#5F5E5A")}
    icon, bg, fg = cfg.get(s, cfg["normal"])
    return f'<span style="font-size:11px;padding:2px 8px;border-radius:6px;font-weight:600;background:{bg};color:{fg};">{icon} {s.title()}</span>'

def priority_badge(p):
    cfg = {"high":("#FAECE7","#993C1D"),"medium":("#FAEEDA","#854F0B"),"low":("#F1EFE8","#5F5E5A")}
    bg, fg = cfg.get(p, cfg["low"])
    return f'<span style="font-size:11px;padding:2px 8px;border-radius:6px;font-weight:600;background:{bg};color:{fg};">{p.upper()}</span>'

def yt(vid): return f"https://youtube.com/watch?v={vid}" if vid else "#"


# ── HTML renderer ───────────────────────────────────────────────────────────────
def render_html(data: dict) -> str:
    ch   = data.get("my_channel", {})
    vids = data.get("my_videos", [])
    uploads  = data.get("uploads_24h", [])
    outliers = data.get("top_outliers", [])
    recs     = data.get("recreate_recommendations", [])

    # --- Tab 1 ---
    vs_colors = {"above":("#EAF3DE","#0F6E56","↑ Above avg"),"at":("#F1EFE8","#5F5E5A","→ At avg"),"below":("#FAECE7","#993C1D","↓ Below avg")}

    tab1 = f"""
    <p class="section-label">📊 Channel overview — last 30 days</p>
    <div class="metrics">
      <div class="metric"><p class="ml">Subscribers</p><p class="mv">{fmt(ch.get('subscribers'))}</p><p class="ms">+{fmt(ch.get('subs_gained_30d'))} this month</p></div>
      <div class="metric"><p class="ml">Total views</p><p class="mv">{fmt(ch.get('total_views'))}</p><p class="ms">+{fmt(ch.get('views_gained_30d'))} this month</p></div>
      <div class="metric"><p class="ml">Videos published</p><p class="mv">{fmt(ch.get('videos_published'))}</p><p class="ms">All time</p></div>
      <div class="metric"><p class="ml">Avg views / video</p><p class="mv">{fmt(ch.get('avg_views_per_video'))}</p><p class="ms">30-day window</p></div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      {health_badge(ch.get('channel_health','flat'))}
      <p style="font-size:13px;color:#555;margin:0;">{ch.get('health_note','')}</p>
    </div>"""

    # --- Tab 2 ---
    AUDITS = [
        ("title",       "🏷", "Title",       "rewrite"),
        ("ideation",    "💡", "Ideation",    "suggestion"),
        ("description", "📝", "Description", "rewrite"),
        ("scripting",   "🎙", "Scripting",   "suggestion"),
        ("editing",     "✂️", "Editing",     "suggestion"),
    ]

    tab2 = '<p class="section-label">🎬 Last 5 videos — AI audit</p>'
    tab2 += '<p style="font-size:13px;color:#555;margin-bottom:1rem;">Scores 1–10. Red = needs work, amber = room to improve, green = solid.</p>'

    for v in vids[:5]:
        audit = v.get("audit", {})
        vbg, vfg, vlbl = vs_colors.get(v.get("vs_channel_avg","at"), vs_colors["at"])

        rows = ""
        for key, icon, label, fix_key in AUDITS:
            a = audit.get(key, {})
            score = int(a.get("score", 5))
            sbg, sfg = score_styles(score)
            issue = a.get("issue","")
            fix   = a.get(fix_key,"")
            rows += f"""
            <div style="border-top:0.5px solid #f0f0ec;padding:11px 0;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                <span style="font-size:13px;font-weight:600;">{icon} {label}</span>
                <span style="font-size:12px;font-weight:700;font-family:'Space Mono',monospace;background:{sbg};color:{sfg};padding:2px 10px;border-radius:20px;">{score}/10</span>
              </div>
              {f'<p style="font-size:12px;color:#993C1D;margin:0 0 5px;">⚠ {issue}</p>' if issue else ""}
              {f'<p style="font-size:12px;color:#0F6E56;background:#EAF3DE;padding:7px 9px;border-radius:6px;margin:0;line-height:1.5;">✓ {fix}</p>' if fix else ""}
            </div>"""

        tab2 += f"""
        <div style="background:#fff;border:0.5px solid #e5e5e0;border-radius:14px;padding:16px;margin-bottom:14px;">
          <div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:4px;">
            <a href="{yt(v.get('video_id',''))}" target="_blank" style="flex-shrink:0;">
              <img src="{v.get('thumbnail','')}" style="width:100px;height:56px;border-radius:6px;object-fit:cover;" onerror="this.style.display='none'" />
            </a>
            <div style="flex:1;min-width:0;">
              <a href="{yt(v.get('video_id',''))}" target="_blank" style="font-size:13px;font-weight:600;color:#1a1a18;text-decoration:none;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{v.get('title','')}</a>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;font-size:11px;color:#888;align-items:center;">
                <span>👁 {fmt(v.get('total_views',0))}</span>
                <span>⚡ {float(v.get('current_vph',0)):.2f} VPH</span>
                <span>👍 {fmt(v.get('likes',0))}</span>
                <span style="padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;background:{vbg};color:{vfg};">{vlbl}</span>
              </div>
            </div>
          </div>
          {rows}
        </div>"""

    # --- Tab 3 ---
    upload_html = ""
    for v in uploads:
        bs = v.get("breakout_score", 0)
        upload_html += f"""
        <div style="background:#fff;border:0.5px solid #e5e5e0;border-radius:12px;padding:14px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start;">
          {"" if not v.get("thumbnail") else '<a href="' + yt(v.get("video_id","")) + '" target="_blank"><img src="' + v.get("thumbnail","") + '" style="width:80px;height:46px;border-radius:4px;object-fit:cover;flex-shrink:0;" /></a>'}
          <div style="flex:1;min-width:0;">
            <a href="{yt(v.get('video_id',''))}" target="_blank" style="font-size:13px;font-weight:600;color:#1a1a18;text-decoration:none;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{v.get('title','')}</a>
            <p style="font-size:12px;color:#888;margin:3px 0 6px;">{v.get('channel','')}</p>
            <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:#888;align-items:center;">
              <span>👁 {fmt(v.get('views',0))}</span><span>⚡ {float(v.get('vph',0)):.1f} VPH</span>
              {f'<span>📈 {float(bs):.1f}×</span>' if bs else ""}
              {status_badge(v.get("status","normal"))}
            </div>
          </div>
        </div>"""

    outlier_html = ""
    for v in outliers:
        bs = float(v.get("breakout_score", 0))
        bw = min(int(bs / 20 * 100), 100)
        bc = "#D85A30" if bs >= 10 else "#BA7517"
        tags = " ".join([f'<span style="background:#f0f0ec;color:#555;font-size:10px;padding:2px 6px;border-radius:4px;">{t}</span>' for t in v.get("tags",[])[:5]])
        outlier_html += f"""
        <div style="background:#fff;border:0.5px solid #e5e5e0;border-radius:12px;padding:14px;margin-bottom:10px;">
          <div style="display:flex;gap:12px;align-items:flex-start;">
{"" if not v.get("thumbnail") else '<a href="' + yt(v.get("video_id","")) + '" target="_blank"><img src="' + v.get("thumbnail","") + '" style="width:80px;height:46px;border-radius:4px;object-fit:cover;flex-shrink:0;" /></a>'}
            <div style="flex:1;min-width:0;">
              <a href="{yt(v.get('video_id',''))}" target="_blank" style="font-size:13px;font-weight:600;color:#1a1a18;text-decoration:none;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{v.get('title','')}</a>
              <p style="font-size:12px;color:#888;margin:3px 0 6px;">{v.get('channel','')}</p>
              <div style="font-size:11px;color:#888;">👁 {fmt(v.get('views',0))} · ⚡ {float(v.get('vph',0)):.1f} VPH · 💬 {float(v.get('engagement_rate',0))*100:.1f}%</div>
            </div>
          </div>
          <div style="margin:10px 0 6px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;margin-bottom:3px;"><span>Breakout score</span><span style="font-weight:700;color:{bc};">{bs:.1f}×</span></div>
            <div style="background:#f0f0ec;border-radius:4px;height:7px;"><div style="width:{bw}%;background:{bc};height:100%;border-radius:4px;"></div></div>
          </div>
          {f'<p style="font-size:12px;color:#555;font-style:italic;margin:6px 0;">&ldquo;{v.get("why_it_worked","")}&rdquo;</p>' if v.get("why_it_worked") else ""}
          <div style="display:flex;gap:4px;flex-wrap:wrap;">{tags}</div>
        </div>"""

    rec_html = ""
    for r in recs:
        tags = " ".join([f'<span style="background:#e6f1fb;color:#185FA5;font-size:10px;padding:2px 6px;border-radius:4px;">{t}</span>' for t in r.get("suggested_tags",[])[:5]])
        rec_html += f"""
        <div style="background:#fff;border:0.5px solid #e5e5e0;border-left:3px solid #0F6E56;border-radius:0 12px 12px 0;padding:14px;margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px;">
            <p style="font-size:14px;font-weight:600;margin:0;">{r.get('concept','')}</p>
            {priority_badge(r.get('priority','low'))}
          </div>
          <p style="font-size:12px;color:#555;margin:0 0 5px;">{r.get('reason','')}</p>
          <p style="font-size:11px;color:#888;margin:0 0 8px;">Inspired by: <em>{r.get('inspired_by','')}</em></p>
          <div style="display:flex;gap:4px;flex-wrap:wrap;">{tags}</div>
        </div>"""

    tab3 = f"""
    {f'<p style="font-size:13px;color:#555;margin-bottom:1rem;">{data.get("competitor_summary","")}</p>' if data.get("competitor_summary") else ""}
    {f'<div class="warn-box"><p class="warn-label">⚠ Watch out</p><p class="warn-text">{data.get("watch_out","")}</p></div>' if data.get("watch_out") else ""}
    <p class="section-label">🕐 Last 24 hours — competitor uploads</p>
    {upload_html or '<p style="font-size:13px;color:#888;">No competitor uploads detected in the last 24h.</p>'}
    <p class="section-label" style="margin-top:1.5rem;">🔥 This week\'s top outliers</p>
    {outlier_html or '<p style="font-size:13px;color:#888;">No outlier data available.</p>'}
    <p class="section-label" style="margin-top:1.5rem;">✦ Should you recreate?</p>
    {rec_html or '<p style="font-size:13px;color:#888;">No recreate recommendations today.</p>'}"""

    action = data.get("daily_action","")
    archive_href = f"archive/{DATE_FILE}.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>DR DB KUSH 2.0 — Daily Intel · {DATE_STR}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet"/>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'DM Sans',sans-serif;background:#f8f7f4;color:#1a1a18;min-height:100vh;}}
    .topbar{{background:#1a1a18;color:#f8f7f4;padding:12px 24px;display:flex;justify-content:space-between;align-items:center;font-family:'Space Mono',monospace;font-size:11px;position:sticky;top:0;z-index:100;}}
    .topbar-logo{{font-weight:700;letter-spacing:0.05em;}}
    .container{{max-width:780px;margin:0 auto;padding:1.5rem 1.25rem 4rem;}}
    .action-box{{background:#1a1a18;color:#f8f7f4;border-radius:12px;padding:16px 18px;margin-bottom:1.5rem;}}
    .action-label{{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:0.1em;color:#888;margin-bottom:6px;text-transform:uppercase;}}
    .action-text{{font-size:14px;font-weight:500;line-height:1.5;}}
    .nav-tabs{{display:flex;gap:2px;background:#ebebea;border-radius:10px;padding:3px;margin-bottom:1.5rem;}}
    .nav-tab{{flex:1;padding:9px 8px;font-size:13px;font-weight:500;text-align:center;cursor:pointer;border-radius:8px;border:none;background:transparent;color:#888;font-family:'DM Sans',sans-serif;transition:all 0.15s;}}
    .nav-tab.active{{background:#fff;color:#1a1a18;box-shadow:0 1px 3px rgba(0,0,0,0.1);}}
    .tab-section{{display:none;}}
    .tab-section.active{{display:block;}}
    .section-label{{font-family:'Space Mono',monospace;font-size:10px;letter-spacing:0.1em;color:#888;text-transform:uppercase;margin-bottom:12px;padding-bottom:6px;border-bottom:0.5px solid #e5e5e0;}}
    .metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:1.25rem;}}
    .metric{{background:#fff;border:0.5px solid #e5e5e0;border-radius:10px;padding:14px;}}
    .ml{{font-size:11px;color:#888;margin-bottom:4px;}}
    .mv{{font-size:22px;font-weight:600;color:#1a1a18;font-family:'Space Mono',monospace;line-height:1;}}
    .ms{{font-size:11px;color:#aaa;margin-top:4px;}}
    .warn-box{{background:#FAEEDA;border-left:3px solid #BA7517;border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:1rem;}}
    .warn-label{{font-size:10px;font-weight:700;color:#854F0B;margin-bottom:4px;font-family:'Space Mono',monospace;letter-spacing:0.05em;text-transform:uppercase;}}
    .warn-text{{font-size:13px;color:#633806;}}
    .footer{{font-size:11px;color:#aaa;text-align:center;margin-top:3rem;font-family:'Space Mono',monospace;line-height:2;}}
    @media(max-width:480px){{.container{{padding:1rem 0.85rem 3rem;}} .nav-tab{{font-size:12px;padding:8px 4px;}}}}
  </style>
</head>
<body>
<div class="topbar">
  <span class="topbar-logo">DR DB KUSH 2.0 // INTEL</span>
  <span style="display:flex;gap:16px;align-items:center;color:#888;">
    <span>{DATE_STR} · 7 AM MT</span>
    <a href="{archive_href}" style="color:#639922;text-decoration:none;font-size:11px;">Archive →</a>
  </span>
</div>
<div class="container">
  {f'<div class="action-box"><p class="action-label">⚡ Today\'s #1 action</p><p class="action-text">{action}</p></div>' if action else ""}
  <div class="nav-tabs">
    <button class="nav-tab active" onclick="showTab(this,'my-channel')">My Channel</button>
    <button class="nav-tab" onclick="showTab(this,'my-videos')">My Videos</button>
    <button class="nav-tab" onclick="showTab(this,'competitors')">Competitors</button>
  </div>
  <div class="tab-section active" id="tab-my-channel">{tab1}</div>
  <div class="tab-section" id="tab-my-videos">{tab2}</div>
  <div class="tab-section" id="tab-competitors">{tab3}</div>
  <div class="footer">
    <p>Auto-generated by Claude + vidIQ · <a href="{archive_href}" style="color:#185FA5;">Archived version</a></p>
    <p>Runs daily at 7:00 AM Mountain Time via GitHub Actions</p>
  </div>
</div>
<script>
function showTab(btn, name) {{
  document.querySelectorAll('.tab-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}}
</script>
</body>
</html>"""


# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    data = fetch_report_data()
    html = render_html(data)

    docs    = pathlib.Path("docs")
    archive = docs / "archive"
    docs.mkdir(exist_ok=True)
    archive.mkdir(exist_ok=True)

    (docs / "index.html").write_text(html, encoding="utf-8")
    (archive / f"{DATE_FILE}.html").write_text(html, encoding="utf-8")
    (archive / f"{DATE_FILE}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Report written → docs/index.html + docs/archive/{DATE_FILE}.html")

if __name__ == "__main__":
    main()
