"""
app.py — Tech News Summarizer
A beautiful Streamlit app that fetches live tech news from free public APIs
(Hacker News, Dev.to, TechCrunch, Ars Technica, The Verge, Wired)
and displays clean extractive summaries, keyword tags, and reading metrics.

Run locally:  streamlit run app.py
Deploy:       Push to GitHub → connect to Streamlit Community Cloud
"""

import streamlit as st
from utils.news_fetcher import fetch_all, RSS_SOURCES
from utils.summarizer import summarize, bullet_points, reading_time, extract_keywords

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TechPulse — Tech News Summarizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About":    "TechPulse – Live tech news from HN, Dev.to & top RSS feeds.",
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  (injected once)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Gradient hero header ── */
.hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%);
    border-radius: 20px;
    padding: 2.5rem 2rem 2rem 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(108,99,255,0.3);
    box-shadow: 0 8px 32px rgba(108,99,255,0.15);
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #6C63FF, #a78bfa, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem 0;
}
.hero p {
    color: #94a3b8;
    font-size: 1rem;
    margin: 0;
}

/* ── Metric pill ── */
.metric-row {
    display: flex;
    gap: 1rem;
    margin-top: 1.2rem;
    flex-wrap: wrap;
}
.metric-pill {
    background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.4);
    border-radius: 30px;
    padding: 0.35rem 1rem;
    font-size: 0.82rem;
    color: #a78bfa;
    font-weight: 600;
    letter-spacing: 0.03em;
}

/* ── News card ── */
.news-card {
    background: linear-gradient(145deg, #1a1d2e, #151827);
    border: 1px solid rgba(108,99,255,0.18);
    border-radius: 16px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1.2rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    position: relative;
    overflow: hidden;
}
.news-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(108,99,255,0.2);
    border-color: rgba(108,99,255,0.45);
}
.news-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6C63FF, #38bdf8);
    border-radius: 16px 16px 0 0;
}

/* ── Source badge ── */
.source-badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    margin-right: 0.5rem;
    margin-bottom: 0.6rem;
}
.badge-hn   { background:#ff6600;  color:#fff; }
.badge-devto{ background:#3b49df;  color:#fff; }
.badge-tc   { background:#0a8940;  color:#fff; }
.badge-ars  { background:#d63a3a;  color:#fff; }
.badge-verge{ background:#f01;     color:#fff; }
.badge-wired{ background:#2c2c2c;  color:#fff; border:1px solid #555; }
.badge-other{ background:#334155;  color:#94a3b8; }

/* ── Tag chips ── */
.tag-chip {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.18rem 0.55rem;
    border-radius: 20px;
    margin-right: 0.3rem;
    margin-top: 0.15rem;
    background: rgba(56,189,248,0.12);
    color: #38bdf8;
    border: 1px solid rgba(56,189,248,0.3);
}

/* ── Article title ── */
.article-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1.45;
    margin: 0.2rem 0 0.6rem 0;
    text-decoration: none;
}
.article-title a {
    color: inherit;
    text-decoration: none;
}
.article-title a:hover {
    color: #a78bfa;
}

/* ── Snippet text ── */
.snippet {
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.6;
    margin-bottom: 0.7rem;
}

/* ── Meta row ── */
.meta-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.78rem;
    color: #64748b;
    flex-wrap: wrap;
}
.meta-row span { display: flex; align-items: center; gap: 0.25rem; }

/* ── Summary box ── */
.summary-box {
    background: rgba(108,99,255,0.08);
    border-left: 3px solid #6C63FF;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0 0.4rem 0;
    font-size: 0.86rem;
    color: #c4b5fd;
    line-height: 1.65;
}

/* ── Bullet list ── */
.bullet-list {
    margin: 0;
    padding-left: 1.2rem;
    font-size: 0.85rem;
    color: #94a3b8;
    line-height: 1.8;
}

/* ── Keyword pills ── */
.kw-pill {
    display: inline-block;
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 4px;
    padding: 0.12rem 0.45rem;
    font-size: 0.72rem;
    color: #7dd3fc;
    margin: 0.15rem 0.15rem 0 0;
    font-family: 'Courier New', monospace;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #121520 100%);
    border-right: 1px solid rgba(108,99,255,0.15);
}

/* ── Refresh / buttons ── */
.stButton button {
    background: linear-gradient(135deg, #6C63FF, #a78bfa) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
.stButton button:hover { opacity: 0.85 !important; }

/* ── Scrollable feed container ── */
.feed-container {
    max-height: 80vh;
    overflow-y: auto;
    padding-right: 0.4rem;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #475569;
}
.empty-state .icon { font-size: 3.5rem; }
.empty-state p     { margin-top: 0.7rem; font-size: 1rem; }

/* ── Divider ── */
hr { border-color: rgba(108,99,255,0.12) !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks: list[dict] = []
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_BADGE_CLASS = {
    "Hacker News":  "badge-hn",
    "Dev.to":       "badge-devto",
    "TechCrunch":   "badge-tc",
    "Ars Technica": "badge-ars",
    "The Verge":    "badge-verge",
    "Wired":        "badge-wired",
}


def source_badge(source: str) -> str:
    cls = SOURCE_BADGE_CLASS.get(source, "badge-other")
    return f'<span class="source-badge {cls}">{source}</span>'


def tag_chips(tags: list[str]) -> str:
    return "".join(f'<span class="tag-chip">{t}</span>' for t in tags)


def kw_pills(kws: list[str]) -> str:
    return "".join(f'<span class="kw-pill">{k}</span>' for k in kws)


def is_bookmarked(url: str) -> bool:
    return any(b["url"] == url for b in st.session_state.bookmarks)


def toggle_bookmark(article: dict) -> None:
    if is_bookmarked(article["url"]):
        st.session_state.bookmarks = [
            b for b in st.session_state.bookmarks if b["url"] != article["url"]
        ]
    else:
        st.session_state.bookmarks.append(article)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        "<h2 style='color:#a78bfa;font-weight:800;margin-bottom:0.2rem;'>⚡ TechPulse</h2>"
        "<p style='color:#475569;font-size:0.8rem;margin-top:0;'>Your live tech news hub</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Category
    st.markdown("**📂 Category**")
    category = st.selectbox(
        "Category",
        ["All", "AI / ML", "Web Dev", "Cybersecurity", "Hardware", "Startups", "Open Source"],
        label_visibility="collapsed",
    )

    st.markdown("**🔍 Search Keywords**")
    search_query = st.text_input("Search", placeholder="e.g. rust, llm, security…",
                                 label_visibility="collapsed")

    st.markdown("**📡 Sources**")
    all_sources = ["Hacker News", "Dev.to"] + list(RSS_SOURCES.keys())
    selected_sources = st.multiselect(
        "Sources",
        all_sources,
        default=all_sources,
        label_visibility="collapsed",
    )

    st.markdown("**📊 Articles per fetch**")
    limit = st.slider("Limit", min_value=5, max_value=50, value=20, step=5,
                      label_visibility="collapsed")

    st.divider()

    if st.button("🔄  Refresh Feed", use_container_width=True):
        st.cache_data.clear()
        st.session_state.refresh_key += 1
        st.rerun()

    st.divider()

    # Bookmarks
    bk_count = len(st.session_state.bookmarks)
    st.markdown(
        f"<p style='color:#a78bfa;font-weight:700;margin-bottom:0.5rem;'>"
        f"🔖 Saved Articles  <span style='color:#64748b;font-size:0.8rem;'>({bk_count})</span></p>",
        unsafe_allow_html=True,
    )
    if bk_count == 0:
        st.markdown(
            "<p style='color:#475569;font-size:0.78rem;'>No bookmarks yet — click 🔖 on any article.</p>",
            unsafe_allow_html=True,
        )
    else:
        for bk in st.session_state.bookmarks:
            st.markdown(
                f"<a href='{bk['url']}' target='_blank' style='color:#94a3b8;"
                f"font-size:0.78rem;text-decoration:none;line-height:1.5;'>"
                f"▸ {bk['title'][:50]}…</a>",
                unsafe_allow_html=True,
            )
        if st.button("🗑️ Clear All Bookmarks", use_container_width=True):
            st.session_state.bookmarks = []
            st.rerun()

    st.divider()
    st.markdown(
        "<p style='color:#334155;font-size:0.72rem;text-align:center;'>"
        "Data from Hacker News · Dev.to · TechCrunch<br>Ars Technica · The Verge · Wired<br>"
        "No API keys required · Updates every 5 min</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="hero">
  <h1>⚡ TechPulse</h1>
  <p>Live tech news from Hacker News, Dev.to, TechCrunch, Ars Technica, The Verge &amp; Wired —
     intelligently summarized, zero API keys required.</p>
  <div class="metric-row" id="metric-row-placeholder"></div>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────────────────────────────────────

with st.spinner("⚡ Fetching latest tech news…"):
    _ = st.session_state.refresh_key  # trigger re-fetch on refresh
    articles = fetch_all(
        query=search_query,
        category=category,
        sources=selected_sources if selected_sources else None,
        limit=limit,
    )

# ─────────────────────────────────────────────────────────────────────────────
# METRICS BAR
# ─────────────────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
col1.metric("📰 Articles Loaded",  len(articles))
col2.metric("📡 Active Sources", len(set(a["source"] for a in articles)))
col3.metric("🏷️ Category Filter", category)
col4.metric("🔍 Search Term",     search_query or "—")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

if not articles:
    st.markdown(
        """
<div class="empty-state">
  <div class="icon">🔭</div>
  <p>No articles found. Try broadening your search or selecting more sources.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# NEWS FEED
# ─────────────────────────────────────────────────────────────────────────────

for idx, art in enumerate(articles):
    title    = art["title"]
    url      = art["url"]
    snippet  = art["snippet"]
    source   = art["source"]
    author   = art["author"]
    pub_date = art["published"]
    score    = art["score"]
    comments = art["comments"]
    tags     = art["tags"]
    image    = art.get("image")

    # ── Smart summary
    full_text  = snippet or title
    summary    = summarize(full_text, title=title, num_sentences=2)
    bullets    = bullet_points(full_text, title=title, n=3)
    read_time  = reading_time(full_text)
    keywords   = extract_keywords(full_text, title=title, top_n=5)

    # ── Card open
    st.markdown('<div class="news-card">', unsafe_allow_html=True)

    # ── Layout: image left (if any) + content right
    if image:
        img_col, txt_col = st.columns([1, 3])
        with img_col:
            try:
                st.image(image, use_container_width=True)
            except Exception:
                pass
        content_ctx = txt_col
    else:
        content_ctx = st.container()

    with content_ctx:
        # Source badge + tags
        st.markdown(
            source_badge(source) + tag_chips(tags),
            unsafe_allow_html=True,
        )

        # Title as clickable link
        st.markdown(
            f'<div class="article-title"><a href="{url}" target="_blank">{title}</a></div>',
            unsafe_allow_html=True,
        )

        # Snippet / snippet summary
        if snippet:
            display_text = summary if len(summary) > 30 else snippet[:280]
            st.markdown(
                f'<div class="snippet">{display_text}</div>',
                unsafe_allow_html=True,
            )

        # Meta row
        score_html   = f"▲ {score}" if score else ""
        comment_html = f"💬 {comments}" if comments else ""
        st.markdown(
            f"""<div class="meta-row">
                <span>👤 {author}</span>
                <span>📅 {pub_date}</span>
                <span>⏱️ {read_time}</span>
                {'<span>' + score_html + '</span>' if score_html else ''}
                {'<span>' + comment_html + '</span>' if comment_html else ''}
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Expander: Full AI Summary
    with st.expander("✨ Smart Summary & Key Takeaways"):
        if summary and len(summary) > 40:
            st.markdown(
                f'<div class="summary-box">{summary}</div>',
                unsafe_allow_html=True,
            )

        if bullets:
            st.markdown(
                "<p style='color:#64748b;font-size:0.8rem;font-weight:600;"
                "margin:0.7rem 0 0.3rem 0;letter-spacing:0.05em;'>KEY TAKEAWAYS</p>",
                unsafe_allow_html=True,
            )
            bullet_html = "\n".join(f"<li>{b}</li>" for b in bullets)
            st.markdown(
                f'<ul class="bullet-list">{bullet_html}</ul>',
                unsafe_allow_html=True,
            )

        if keywords:
            st.markdown(
                "<p style='color:#64748b;font-size:0.8rem;font-weight:600;"
                "margin:0.8rem 0 0.25rem 0;letter-spacing:0.05em;'>KEYWORDS</p>",
                unsafe_allow_html=True,
            )
            st.markdown(kw_pills(keywords), unsafe_allow_html=True)

        # Quick actions row
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            bk_label = "🔖 Remove Bookmark" if is_bookmarked(url) else "🔖 Save for Later"
            if st.button(bk_label, key=f"bk_{idx}"):
                toggle_bookmark(art)
                st.rerun()
        with act_col2:
            st.link_button("🔗 Read Full Article", url)

    # ── Card close
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    "<p style='text-align:center;color:#334155;font-size:0.78rem;'>"
    "⚡ TechPulse — Built with Streamlit · Free public APIs only · "
    "No data stored · Refreshes every 5 minutes</p>",
    unsafe_allow_html=True,
)
