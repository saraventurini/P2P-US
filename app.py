"""
app.py — P2P: Pears to Peers — Benchmarking among equals
Streamlit dashboard for US research institution benchmarking.
"""

import os
import streamlit as st
import pandas as pd

from config import PALETTE, DOMAIN_COLORS, PERIOD_LABELS
from data_loader import (
    load_base, load_all, load_domain, load_field,
    load_rca_topic, build_scaled_maps,
)
from resolver import get_slice, get_peer_real_ids
import charts

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title='P2P — Pears to Peers',
    page_icon='🍐',
    layout='wide',
    initial_sidebar_state='expanded',
)

# Inject CSS
css_path = os.path.join(os.path.dirname(__file__), 'styles.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load base data (always eager)
# ---------------------------------------------------------------------------
with st.spinner('Loading data…'):
    info_df, relationships_df, topics_df, id_name_dict, embed_df = load_base()
    all_data = load_all()

scaled_to_real, real_to_scaled = build_scaled_maps(info_df)

inst_options = sorted(info_df['institution_name'].dropna().tolist())
inst_name_to_id = dict(zip(info_df['institution_name'], info_df['institution_id']))
PLACEHOLDER = '— Select an institution —'
select_options = [PLACEHOLDER] + inst_options

# ---------------------------------------------------------------------------
# Session state for institution selection
# ---------------------------------------------------------------------------
if 'inst_name' not in st.session_state:
    st.session_state.inst_name = PLACEHOLDER

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metric_card(label, value, delta=None, delta_num=None):
    """Clean metric card: no box, just label + value."""
    delta_html = ''
    if delta is not None:
        positive = (delta_num >= 0) if delta_num is not None else True
        arrow = '▲' if positive else '▼'
        color = '#2A8A5E' if positive else '#B03A2E'
        delta_html = (
            f'<div style="font-size:0.78rem;color:{color};margin-top:3px;'
            f'font-family:Arial,sans-serif;">{arrow}&nbsp;{delta}</div>'
        )
    else:
        delta_html = '<div style="font-size:0.78rem;visibility:hidden;margin-top:3px;">–</div>'
    return (
        f'<div style="padding:0.5rem 0 0.8rem 0;border-bottom:1px solid #E8E8E8;">'
        f'<div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;'
        f'color:#999999;font-family:Arial,sans-serif;">{label}</div>'
        f'<div style="font-size:1.75rem;font-weight:700;font-family:Arial,sans-serif;'
        f'color:#223F73;line-height:1.1;margin-top:4px;">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def _section_title(text):
    return (
        f"<p style='font-size:19px;font-weight:700;color:#111;"
        f"margin:28px 0 8px 0;letter-spacing:-0.01em;font-family:Arial,sans-serif;"
        f"border-bottom:2px solid #223F73;padding-bottom:5px;'>{text}</p>"
    )


def _sub_label(text):
    return (
        f"<p style='font-size:13px;font-weight:600;color:#555;"
        f"text-align:center;margin:4px 0 2px 0;font-family:Arial,sans-serif;'>{text}</p>"
    )


# ---------------------------------------------------------------------------
# SIDEBAR (only shown when institution is selected)
# ---------------------------------------------------------------------------
granularity      = 'All'
domain_id_scaled = None
field_id_scaled  = None
context_label    = 'All fields'
selected_period  = 3

with st.sidebar:
    st.markdown(
        '<div style="border-bottom:2px solid #223F73;padding-bottom:0.6rem;margin-bottom:1rem;">'
        '<span style="font-size:1.3rem;font-weight:700;font-family:Arial,sans-serif;">P2P</span><br>'
        '<span style="font-size:0.8rem;color:#666;font-style:italic;font-family:Georgia,serif;">'
        'Pears to Peers: Benchmarking among equals</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;'
        'color:#888;margin-bottom:4px;">Institution</div>',
        unsafe_allow_html=True,
    )
    sidebar_idx = select_options.index(st.session_state.inst_name)
    selected_name_sidebar = st.selectbox(
        'Select institution', select_options, index=sidebar_idx,
        label_visibility='collapsed', key='sidebar_inst'
    )
    if selected_name_sidebar != st.session_state.inst_name:
        st.session_state.inst_name = selected_name_sidebar
        st.rerun()

    selected_name = st.session_state.inst_name

    st.divider()

    if selected_name != PLACEHOLDER:
        st.markdown(
            '<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;'
            'color:#888;margin-bottom:4px;">Granularity</div>',
            unsafe_allow_html=True,
        )
        granularity = st.radio('View', ['All', 'Domain', 'Field'], label_visibility='collapsed')

        if granularity == 'Domain':
            domain_opts = (
                topics_df[['domain_id_scaled', 'domain_name']]
                .drop_duplicates()
                .sort_values('domain_id_scaled')
            )
            domain_map = dict(zip(domain_opts['domain_name'], domain_opts['domain_id_scaled']))
            selected_domain = st.selectbox('Domain', list(domain_map.keys()))
            domain_id_scaled = domain_map[selected_domain]
            context_label = f'Domain: {selected_domain}'

        elif granularity == 'Field':
            all_field_opts = (
                topics_df[['field_id_scaled', 'field_name', 'domain_name']]
                .drop_duplicates()
                .sort_values(['domain_name', 'field_name'])
            )
            domain_names = all_field_opts['domain_name'].unique().tolist()
            selected_domain_for_field = st.selectbox('Domain', sorted(domain_names), key='field_domain_filter')
            field_opts = all_field_opts[all_field_opts['domain_name'] == selected_domain_for_field]
            field_labels = field_opts['field_name'].tolist()
            field_ids    = field_opts['field_id_scaled'].tolist()
            field_label_to_id = dict(zip(field_labels, field_ids))
            selected_field_label = st.selectbox('Field', field_labels)
            field_id_scaled = field_label_to_id[selected_field_label]
            context_label = f'Field: {selected_field_label}'

        st.divider()

        st.markdown(
            '<div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.1em;'
            'color:#888;margin-bottom:4px;">Period</div>',
            unsafe_allow_html=True,
        )
        selected_period = st.select_slider(
            'Period',
            options=[0, 1, 2, 3],
            value=3,
            format_func=lambda x: PERIOD_LABELS[x],
            label_visibility='collapsed',
        )
        st.divider()

    st.caption(
        'Data: OpenAlex · Coverage: United States\n'
        'MOBS Lab, Network Science Institute\nNortheastern University'
    )

# ---------------------------------------------------------------------------
# LANDING PAGE (no institution selected)
# ---------------------------------------------------------------------------
if st.session_state.inst_name == PLACEHOLDER:
    # Hide sidebar entirely on landing page
    st.markdown(
        '<style>'
        'section[data-testid="stSidebar"] { display: none !important; }'
        '[data-testid="collapsedControl"] { display: none !important; }'
        '.block-container { padding-left: 3rem !important; padding-right: 3rem !important; }'
        'html, body, [class*="css"], .stApp { background-color: #F2F4F8 !important; }'
        '</style>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="max-width:760px;margin-top:3.5rem;">'
        '<div style="border-bottom:3px solid #223F73;padding-bottom:0.8rem;margin-bottom:1.5rem;">'
        '<h1 style="font-size:3rem;font-weight:700;font-family:Arial,sans-serif;'
        'color:#111;margin:0;letter-spacing:-0.03em;">P2P</h1>'
        '<div style="font-size:1.15rem;color:#555;font-style:italic;font-family:Georgia,serif;'
        'margin-top:0.4rem;">Pears to Peers: Benchmarking among equals</div>'
        '</div>'
        '<p style="font-size:1rem;line-height:1.8;color:#333;margin-bottom:0.5rem;">'
        'A <em>pears-to-peers</em> comparison ensures that performance, quality, and outcomes '
        'are evaluated among institutions operating under similar conditions, scales, and contexts.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    n_inst    = len(info_df)
    n_r1      = int((info_df['research_level'] == 'R1').sum())
    n_topics  = len(topics_df['topic_id'].unique()) if 'topic_id' in topics_df.columns else '—'
    n_domains = topics_df['domain_name'].nunique()

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(_metric_card('Institutions', f'{n_inst:,}'), unsafe_allow_html=True)
    with c2: st.markdown(_metric_card('R1 Universities', f'{n_r1:,}'), unsafe_allow_html=True)
    with c3: st.markdown(_metric_card('Research Topics', f'{n_topics:,}'), unsafe_allow_html=True)
    with c4: st.markdown(_metric_card('Domains', str(n_domains)), unsafe_allow_html=True)

    st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)

    # Prominent institution selector
    st.markdown(
        '<p style="font-size:0.9rem;color:#555;font-family:Georgia,serif;margin-bottom:4px;">'
        'Select an institution from the sidebar to explore its research portfolio, peer landscape, '
        'impact trajectory, and topic specialization.</p>',
        unsafe_allow_html=True,
    )
    col_sel, _ = st.columns([4, 8])
    with col_sel:
        chosen = st.selectbox(
            'Select an institution to begin',
            select_options,
            index=0,
            label_visibility='collapsed',
            key='landing_inst',
        )
    if chosen != PLACEHOLDER:
        st.session_state.inst_name = chosen
        st.rerun()

    st.markdown('<div style="height:2.5rem"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.78rem;color:#AAAAAA;font-family:Georgia,serif;">'
        'Data: OpenAlex · Coverage: United States · Periods: 1990–2024<br>'
        'MOBS Lab, Network Science Institute, Northeastern University'
        '</p>',
        unsafe_allow_html=True,
    )
    st.stop()

# ---------------------------------------------------------------------------
# Institution selected — resolve all data
# ---------------------------------------------------------------------------
selected_name = st.session_state.inst_name
institution_id = inst_name_to_id[selected_name]
institution_id_scaled = real_to_scaled.get(institution_id, 0)

if granularity == 'Domain':
    with st.spinner('Loading domain-level data…'):
        load_domain()
elif granularity == 'Field':
    with st.spinner('Loading field-level data (first time may take ~15 s)…'):
        load_field()

data_slice = get_slice(
    granularity, domain_id_scaled, field_id_scaled,
    institution_id, institution_id_scaled,
    scaled_to_real, info_df,
)

info_row = info_df[info_df['institution_id'] == institution_id].iloc[0]
peer_real_ids = get_peer_real_ids(data_slice['peers_scaled'], scaled_to_real)

if granularity == 'Domain':
    _full_stats = load_domain()['stats'].get(domain_id_scaled, pd.DataFrame())
elif granularity == 'Field':
    _full_stats = load_field()['stats'].get(field_id_scaled, pd.DataFrame())
else:
    _full_stats = all_data['stats']

peer_stats_df = (
    _full_stats[_full_stats['institution_id'].isin(peer_real_ids)]
    if peer_real_ids and not _full_stats.empty else pd.DataFrame()
)

# Domain color index for portfolio charts (0–3); None = all domains
if granularity == 'Domain':
    active_domain_idx = int(domain_id_scaled)
elif granularity == 'Field':
    _frows = topics_df[topics_df['field_id_scaled'] == field_id_scaled]
    active_domain_idx = int(_frows['domain_id_scaled'].iloc[0]) if not _frows.empty else None
else:
    active_domain_idx = None

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
research_level = info_row.get('research_level', None)
has_rl = pd.notna(research_level) and research_level

rl_badge = ''
if has_rl:
    rl_badge = (
        f'<span style="background:#223F73;color:white;font-size:0.68rem;'
        f'text-transform:uppercase;letter-spacing:0.1em;padding:2px 10px;'
        f'border-radius:3px;font-family:Arial,sans-serif;">{research_level}</span>'
    )

st.markdown(
    f'<div style="border-bottom:2px solid #223F73;padding-bottom:0.5rem;margin-bottom:1rem;">'
    f'<h1 style="font-size:2rem;font-weight:700;font-family:Arial,sans-serif;'
    f'color:#111;margin:0;letter-spacing:-0.02em;">{selected_name}</h1>'
    f'<div style="margin-top:6px;">{rl_badge}'
    f'<span style="font-size:0.82rem;color:#888;margin-left:10px;font-family:Georgia,serif;">'
    f'{context_label}</span></div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# ROW 1 — Metric Cards (NYT style)
# ---------------------------------------------------------------------------
inst_stats_all = data_slice['stats']
latest_year = int(inst_stats_all['year'].max()) if not inst_stats_all.empty else None

if latest_year:
    latest_stats = inst_stats_all[inst_stats_all['year'] == latest_year]
    prev_stats   = inst_stats_all[inst_stats_all['year'] == latest_year - 1]
    n_works      = int(latest_stats['n_works'].iloc[0])   if not latest_stats.empty else None
    n_authors    = int(latest_stats['n_authors'].iloc[0]) if not latest_stats.empty else None
    prev_works   = int(prev_stats['n_works'].iloc[0])     if not prev_stats.empty else None
    prev_authors = int(prev_stats['n_authors'].iloc[0])   if not prev_stats.empty else None
else:
    n_works = n_authors = prev_works = prev_authors = None

entropy_df = data_slice['entropy']
if entropy_df is not None and not entropy_df.empty:
    latest_entropy = entropy_df[entropy_df['period_id'] == entropy_df['period_id'].max()]
    prev_entropy   = entropy_df[entropy_df['period_id'] == entropy_df['period_id'].max() - 1]
    disorder_val  = round(float(latest_entropy['disorder_index'].iloc[0]), 3) if not latest_entropy.empty else None
    prev_disorder = round(float(prev_entropy['disorder_index'].iloc[0]), 3)   if not prev_entropy.empty else None
else:
    disorder_val = prev_disorder = None

# Build card list dynamically (skip Research Level if not available)
cards = []

pub_label = f'Publications ({latest_year})' if latest_year else 'Publications'
pub_val   = f'{n_works:,}' if n_works is not None else 'N/A'
pub_dnum  = (n_works - prev_works) if (n_works and prev_works) else None
pub_dstr  = f'{pub_dnum:+,}' if pub_dnum is not None else None
cards.append((pub_label, pub_val, pub_dstr, pub_dnum))

aut_label = f'Authors ({latest_year})' if latest_year else 'Authors'
aut_val   = f'{n_authors:,}' if n_authors is not None else 'N/A'
aut_dnum  = (n_authors - prev_authors) if (n_authors and prev_authors) else None
aut_dstr  = f'{aut_dnum:+,}' if aut_dnum is not None else None
cards.append((aut_label, aut_val, aut_dstr, aut_dnum))

dis_val   = f'{disorder_val:.3f}' if disorder_val is not None else 'N/A'
dis_dnum  = round(disorder_val - prev_disorder, 3) if (disorder_val and prev_disorder) else None
dis_dstr  = f'{dis_dnum:+.3f}' if dis_dnum is not None else None
cards.append(('Disorder Index', dis_val, dis_dstr, dis_dnum))

if has_rl:
    cards.append(('Research Level', research_level, None, None))

cols = st.columns(len(cards))
for col, (lbl, val, dstr, dnum) in zip(cols, cards):
    with col:
        st.markdown(_metric_card(lbl, val, dstr, dnum), unsafe_allow_html=True)

st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ROW 2 — Map + Peers
# ---------------------------------------------------------------------------
st.markdown(_section_title('Location &amp; Peers'), unsafe_allow_html=True)
col_map, col_peers = st.columns([4, 8])

with col_map:
    peer_info_df = info_df[info_df['institution_id'].isin(peer_real_ids)] if peer_real_ids else pd.DataFrame()
    st.plotly_chart(charts.make_map(info_row, peer_info_df), use_container_width=True)
    lat = info_row.get('latitude')
    lon = info_row.get('longitude')
    if pd.notna(lat) and pd.notna(lon):
        st.caption(f'{info_row.get("country_name","")}\u2002·\u2002{lat:.2f}°N, {abs(float(lon)):.2f}°W')

with col_peers:
    st.plotly_chart(charts.make_peers_chart(data_slice['peers']), use_container_width=True)

# ---------------------------------------------------------------------------
# ROW 3 — Portfolio Composition
# ---------------------------------------------------------------------------
st.markdown(_section_title('Research Portfolio'), unsafe_allow_html=True)

st.plotly_chart(
    charts.make_portfolio_chart(data_slice['rca'], selected_period, granularity, active_domain_idx),
    use_container_width=True,
)

with st.expander('Portfolio composition by domain — all periods', expanded=False):
    st.plotly_chart(
        charts.make_portfolio_evolution(data_slice['rca'], granularity, data_slice['entropy'], active_domain_idx),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# ROW 4 — Trends: 3-column layout
# ---------------------------------------------------------------------------
st.markdown(_section_title('Trends &amp; Diversity'), unsafe_allow_html=True)

col_works, col_authors = st.columns(2)

_all_stats_comparison = all_data['stats'] if granularity != 'All' else None

with col_works:
    st.markdown(_sub_label('Publications over Time'), unsafe_allow_html=True)
    st.plotly_chart(
        charts.make_works_chart(data_slice['stats'], institution_id, peer_stats_df, _all_stats_comparison),
        use_container_width=True,
    )

with col_authors:
    st.markdown(_sub_label('Authors over Time'), unsafe_allow_html=True)
    st.plotly_chart(
        charts.make_authors_chart(data_slice['stats'], institution_id, peer_stats_df, _all_stats_comparison),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# ROW 5 — Topic Landscape
# ---------------------------------------------------------------------------
st.markdown(_section_title('Topic Landscape'), unsafe_allow_html=True)

topic_domain_filter = None
topic_field_filter  = None
if granularity == 'Domain':
    topic_domain_filter = domain_id_scaled
elif granularity == 'Field':
    topic_domain_filter = int(
        topics_df[topics_df['field_id_scaled'] == field_id_scaled]['domain_id_scaled'].iloc[0]
    ) if not topics_df[topics_df['field_id_scaled'] == field_id_scaled].empty else None
    topic_field_filter = selected_field_label

with st.spinner('Loading topic data…'):
    rca_topic = load_rca_topic()
_, _tleft, _ = st.columns([1, 20, 1])
with _tleft:
    st.plotly_chart(
        charts.make_topic_landscape(institution_id, rca_topic, embed_df, topics_df,
                                    topic_domain_filter, topic_field_filter),
        use_container_width=True,
    )

st.caption(
    'Faint points = all research topics · Colored = institution specializations · '
    'Larger / deeper color = stronger specialization'
)

# ---------------------------------------------------------------------------
# ROW 6 — Impact (full width, stacked to give more horizontal room)
# ---------------------------------------------------------------------------
st.markdown(_section_title('Impact Analysis'), unsafe_allow_html=True)

st.markdown(_sub_label('Relative Impact Ranking among Peers'), unsafe_allow_html=True)
st.plotly_chart(
    charts.make_impact_ranking(
        data_slice['peers'], all_data['impact'], institution_id, info_df
    ),
    use_container_width=True,
)
st.caption('Rank 1 = highest relative impact within the peer group.')

with st.expander('Relative Impact vs. Impact Uniformity', expanded=False):
    st.plotly_chart(
        charts.make_impact_bubble(
            institution_id, data_slice['peers'], all_data['impact'], info_df
        ),
        use_container_width=True,
    )
    st.caption('Each bubble = one year · Size encodes impact uniformity · Grey = peers.')

# ---------------------------------------------------------------------------
# ROW 7 — Child Institutions
# ---------------------------------------------------------------------------
st.markdown(_section_title('Affiliated Units'), unsafe_allow_html=True)

children_ids = (
    relationships_df[relationships_df['institution_id'] == institution_id]['child'].tolist()
    if 'institution_id' in relationships_df.columns else []
)
if not children_ids and 'instituion_id' in relationships_df.columns:
    children_ids = relationships_df[
        relationships_df['instituion_id'] == institution_id
    ]['child'].tolist()

if children_ids:
    col_key = 'institution_id' if 'institution_id' in relationships_df.columns else 'instituion_id'
    children_names = sorted(
        relationships_df[relationships_df[col_key] == institution_id]['child_name'].dropna().tolist()
    )
    if children_names:
        with st.expander(f'Child / affiliated institutions  ({len(children_names)})', expanded=False):
            for name in children_names:
                st.markdown(f'- {name}')
    else:
        with st.expander('Child / affiliated institutions  (0)', expanded=False):
            st.caption('No resolvable child institutions found.')
else:
    with st.expander('Child / affiliated institutions  (0)', expanded=False):
        st.caption('No child institutions recorded for this entry.')

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)
st.markdown(
    '<hr style="border:none;border-top:1px solid #E8E8E8;">'
    '<p style="font-size:0.72rem;color:#AAAAAA;text-align:center;font-family:Georgia,serif;">'
    'Data: OpenAlex · Coverage: United States<br>MOBS Lab, Network Science Institute, Northeastern University'
    '</p>',
    unsafe_allow_html=True,
)
