APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg-main: #f4efe7;
  --surface: rgba(255, 251, 245, 0.88);
  --surface-strong: rgba(255, 247, 236, 0.98);
  --ink: #1d1a16;
  --muted: #6c6256;
  --accent: #006d5b;
  --accent-2: #d76f30;
  --border: rgba(29, 26, 22, 0.08);
  --shadow: 0 20px 45px rgba(102, 76, 46, 0.14);
}

.stApp {
  background:
    radial-gradient(circle at top left, rgba(0, 109, 91, 0.18), transparent 32%),
    radial-gradient(circle at top right, rgba(215, 111, 48, 0.14), transparent 24%),
    linear-gradient(180deg, #f7f1e8 0%, #efe5d9 100%);
  color: var(--ink);
  font-family: 'Space Grotesk', 'Avenir Next', sans-serif;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(24, 88, 76, 0.98) 0%, rgba(17, 54, 48, 0.98) 100%);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption {
  color: #f7f1e8 !important;
  font-family: 'Space Grotesk', 'Avenir Next', sans-serif;
}

[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stDateInput input,
[data-testid="stSidebar"] .stMultiSelect input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] [role="textbox"],
[data-testid="stSidebar"] [role="combobox"],
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="base-input"] input,
[data-testid="stSidebar"] [data-baseweb="textarea"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="tag"] span,
[data-testid="stSidebar"] [data-baseweb="select"] span {
  color: #1d1a16 !important;
  -webkit-text-fill-color: #1d1a16 !important;
  caret-color: #1d1a16 !important;
  opacity: 1 !important;
}

[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-baseweb="textarea"],
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: rgba(255, 251, 245, 0.98) !important;
}

[data-testid="stSidebar"] [data-baseweb="input"] *,
[data-testid="stSidebar"] [data-baseweb="base-input"] *,
[data-testid="stSidebar"] [data-baseweb="textarea"] *,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] .stTextArea *,
[data-testid="stSidebar"] .stDateInput *,
[data-testid="stSidebar"] .stMultiSelect *,
[data-testid="stSidebar"] [data-testid="stDateInput"] *,
[data-testid="stSidebar"] [data-testid="stTextArea"] * {
  color: #1d1a16 !important;
  -webkit-text-fill-color: #1d1a16 !important;
  caret-color: #1d1a16 !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] > div,
[data-testid="stSidebar"] [data-testid="stTextArea"] > div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] > div {
  background: transparent !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  border-radius: 14px !important;
  box-shadow: inset 0 0 0 1px rgba(29, 26, 22, 0.12) !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] svg,
[data-testid="stSidebar"] [data-testid="stTextArea"] svg,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] svg {
  fill: #1d1a16 !important;
}

[data-testid="stSidebar"] textarea::placeholder,
[data-testid="stSidebar"] input::placeholder {
  color: #6c6256 !important;
  -webkit-text-fill-color: #6c6256 !important;
}

.hero-card, .panel-card, .metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
}

.hero-card {
  padding: 1.6rem 1.8rem;
  margin-bottom: 1rem;
}

.hero-kicker {
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--accent);
  font-size: 0.76rem;
}

.hero-title {
  font-size: 2.4rem;
  line-height: 1;
  margin: 0.55rem 0 0.8rem 0;
}

.hero-subtitle {
  color: var(--muted);
  margin: 0;
  max-width: 48rem;
}

.metric-card {
  padding: 1rem 1.1rem;
  min-height: 120px;
}

.metric-label {
  font-family: 'IBM Plex Mono', monospace;
  color: var(--muted);
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.1em;
}

.metric-value {
  font-size: 1.9rem;
  font-weight: 700;
  margin: 0.4rem 0 0.2rem 0;
}

.metric-caption {
  color: var(--muted);
  font-size: 0.9rem;
}

.panel-card {
  padding: 1.1rem 1.2rem 0.7rem 1.2rem;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.section-copy {
  color: var(--muted);
  margin-bottom: 0.75rem;
}
</style>
"""
