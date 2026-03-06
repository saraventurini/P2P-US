"""
charts.py — All Plotly chart functions for the P2P dashboard.
Design inspired by the example dashboard: large typography, dark blue accents,
color-gradient topic landscape, numbered impact ranking, jitter bubble chart.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config import PALETTE, DOMAIN_COLORS, PERIOD_LABELS

# Domain base colors as RGB tuples (for blend_white_to_color)
DOMAIN_BASE_RGB = {
    0: (147, 207, 189),   # Life Sciences
    1: (98,  168, 183),   # Social Sciences
    2: (81,  128, 177),   # Physical Sciences
    3: (34,  63,  115),   # Health Sciences
}

def _domain_shade(d_idx, t):
    """Return hex color: blend of white→domain base. t in [0,1], 1=full color."""
    r, g, b = DOMAIN_BASE_RGB.get(d_idx, (34, 63, 115))
    r2 = int(255 + (r - 255) * t)
    g2 = int(255 + (g - 255) * t)
    b2 = int(255 + (b - 255) * t)
    return f'#{r2:02X}{g2:02X}{b2:02X}'

DARK_BLUE = '#223F73'

# Shared plot / paper background
_BG = dict(plot_bgcolor='white', paper_bgcolor='white')

def _base_layout(**kw):
    """Minimal shared layout: white bg, clean axes, 14px font."""
    d = dict(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='#111111', size=14),
        margin=dict(l=40, r=20, t=40, b=40),
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0, font=dict(size=13)),
    )
    d.update(kw)
    return d


def _clean_axis(**kw):
    d = dict(showgrid=False, zeroline=False, showline=True,
             linecolor='#CCCCCC', linewidth=1,
             tickfont=dict(size=13, color='#333333'))
    d.update(kw)
    return d


def _section_title(text):
    """Return HTML for a section title matching the example style."""
    return (
        f"<p style='font-size:22px;text-align:center;"
        f"font-weight:bold;margin-bottom:10px;margin-top:20px;"
        f"color:#111111;'>{text}</p>"
    )


# ---------------------------------------------------------------------------
# Colour utility (from example dashboard)
# ---------------------------------------------------------------------------

def _blend_white_to_color(intensity, base_rgb):
    """
    Blend from white (intensity=0) to base_rgb (intensity=1).
    Non-linear (sqrt) for better visual spread.
    """
    intensity = max(0.0, min(1.0, float(intensity))) ** 0.5
    r = int(255 - intensity * (255 - base_rgb[0]))
    g = int(255 - intensity * (255 - base_rgb[1]))
    b = int(255 - intensity * (255 - base_rgb[2]))
    return f'rgb({r},{g},{b})'


# ---------------------------------------------------------------------------
# 1. MAP
# ---------------------------------------------------------------------------

def make_map(info_row, peer_info_df=None):
    name = info_row.get('institution_name', '')
    lat  = info_row.get('latitude')
    lon  = info_row.get('longitude')

    fig = go.Figure()

    # Peer dots (smaller, lighter)
    if peer_info_df is not None and not peer_info_df.empty:
        peers = peer_info_df.dropna(subset=['latitude', 'longitude'])
        if not peers.empty:
            peer_names = peers['institution_name'].str.replace(r'\s*\(US\)\s*$', '', regex=False)
            fig.add_trace(go.Scattergeo(
                lon=peers['longitude'], lat=peers['latitude'],
                text=peer_names,
                mode='markers',
                marker=dict(size=8, color='rgba(34,63,115,0.45)', symbol='circle',
                            line=dict(width=1, color='white')),
                hovertemplate='<b>%{text}</b><extra></extra>',
                hoverlabel=dict(bgcolor='#5180B1', font_size=13, font_color='white'),
                showlegend=False,
            ))

    # Focal institution dot (on top)
    fig.add_trace(go.Scattergeo(
        lon=[lon], lat=[lat], text=[name],
        mode='markers',
        marker=dict(size=16, color=DARK_BLUE, symbol='circle',
                    line=dict(width=2, color='white')),
        hovertemplate='<b>%{text}</b><extra></extra>',
        hoverlabel=dict(bgcolor=DARK_BLUE, font_size=14, font_color='white'),
        showlegend=False,
    ))
    fig.update_geos(
        scope='usa', projection_type='albers usa',
        showland=True, landcolor='#D6E4F0',
        showlakes=True, lakecolor='#D9EAF5',
        showcoastlines=True, coastlinecolor='#CCCCCC',
        showsubunits=True, subunitcolor='white',
        bgcolor='white',
    )
    fig.update_layout(
        height=260, margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='white', paper_bgcolor='white',
        geo=dict(bgcolor='white'),
    )
    return fig


# ---------------------------------------------------------------------------
# 2. PEERS — horizontal bar, large font
# ---------------------------------------------------------------------------

def make_peers_chart(peer_df):
    if peer_df is None or peer_df.empty:
        fig = go.Figure()
        fig.add_annotation(text='No peer data available', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=300))
        return fig

    df = peer_df.sort_values('similarity_score', ascending=False).head(20).copy()
    df['short_name'] = (
        df['institution_name']
        .str.replace(r'\s*\(US\)\s*$', '', regex=True)
        .str[:48]
    )

    fig = go.Figure(go.Bar(
        y=df['short_name'],
        x=df['similarity_score'],
        orientation='h',
        marker=dict(color=DARK_BLUE, line=dict(width=0)),
        text=[f'{s:.2f}' for s in df['similarity_score']],
        textposition='inside',
        textfont=dict(color='white', size=14, family='Arial Black'),
        hovertemplate='<b>%{y}</b><br>Similarity: %{x:.4f}<extra></extra>',
        hoverlabel=dict(bgcolor=DARK_BLUE, font_size=14, font_color='white'),
    ))
    fig.update_layout(
        **_base_layout(
            showlegend=False,
            height=max(400, len(df) * 30 + 60),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title='Similarity Score', title_font=dict(size=15),
                       showgrid=True, gridcolor='#EEEEEE',
                       zeroline=False, showline=False,
                       tickfont=dict(size=13, color='#333')),
            yaxis=dict(title=None, autorange='reversed',
                       showgrid=False, zeroline=False, showline=False,
                       tickfont=dict(size=14, color='#111')),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 3. PORTFOLIO — vertical bar, domain colors
# ---------------------------------------------------------------------------

def make_portfolio_chart(rca_df, period, granularity='All', color_domain_idx=None):
    if rca_df is None or rca_df.empty:
        fig = go.Figure()
        fig.add_annotation(text='No portfolio data', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=400))
        return fig

    df = rca_df[rca_df['period_id'] == period].copy()
    if df.empty:
        df = rca_df.copy()

    name_col = ('subfield_name' if ('subfield_name' in df.columns and granularity == 'Field')
                else 'field_name' if 'field_name' in df.columns else df.columns[2])

    if 'domain_id' in df.columns:
        df['_d'] = (df['domain_id'] - 1).clip(0, 3).astype(int)
    elif 'domain_id_scaled' in df.columns:
        df['_d'] = df['domain_id_scaled'].clip(0, 3).astype(int)
    elif color_domain_idx is not None:
        df['_d'] = int(color_domain_idx)
    else:
        df['_d'] = 0

    df = df.sort_values(['_d', name_col])

    # Build per-item shade
    df['_color'] = ''
    for d_idx, grp_idx in df.groupby('_d').groups.items():
        if granularity == 'All':
            grp = df.loc[grp_idx].sort_values('portfolio_composition', ascending=False)
            n = len(grp)
            for i, idx in enumerate(grp.index):
                t = 0.45 + 0.55 * (i / max(n - 1, 1)) if n > 1 else 1.0
                df.at[idx, '_color'] = _domain_shade(int(d_idx), round(1.0 - t + 0.45, 3))
        else:
            grp = df.loc[grp_idx].sort_values(name_col)
            for i, idx in enumerate(grp.index):
                t = 0.72 if i % 2 == 0 else 0.38
                df.at[idx, '_color'] = _domain_shade(int(d_idx), t)

    # Domain color for hover (use base domain color)
    domain_color_map = {
        row.get('domain_name', f'Domain {int(row["_d"])}'): DOMAIN_COLORS[int(row['_d'])]
        for _, row in df.iterrows()
    }

    df['_full_name'] = df[name_col]
    fig = px.bar(
        df,
        x=name_col,
        y='portfolio_composition',
        color=name_col,
        color_discrete_map=dict(zip(df[name_col], df['_color'])),
        custom_data=['_full_name', 'domain_name'],
        labels={name_col: '', 'portfolio_composition': '', 'domain_name': 'Domain'},
    )
    for trace in fig.data:
        dom = df[df[name_col] == trace.name]['domain_name'].iloc[0] if trace.name in df[name_col].values else ''
        c = domain_color_map.get(dom, DARK_BLUE)
        trace.hoverlabel = dict(bgcolor=c, font_size=14, font_color='white')
        trace.hovertemplate = '<b>%{customdata[1]}</b><br>%{customdata[0]}<br>%{y:.1%}<extra></extra>'
        trace.showlegend = False

    # Add dummy traces for domain legend
    seen_domains = {}
    for _, row in df.drop_duplicates('_d').iterrows():
        dname = row.get('domain_name', f'Domain {int(row["_d"])}')
        c = DOMAIN_COLORS[int(row['_d'])]
        fig.add_trace(go.Bar(x=[None], y=[None], name=dname,
                             marker_color=c, showlegend=True))

    all_labels = df[name_col].tolist()
    short_labels = [
        l if len(l) <= 22 else l[:20] + '…'
        for l in all_labels
    ]
    fig.update_layout(
        **_base_layout(
            height=400,
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=11, color='#111'),
                tickmode='array',
                tickvals=all_labels,
                ticktext=short_labels,
                automargin=True,
                showgrid=False, showline=True, linecolor='#CCCCCC',
            ),
            yaxis=dict(tickfont=dict(size=13, color='#111'), showgrid=False,
                       showline=True, linecolor='#CCCCCC', title=None,
                       tickformat='.0%',
                       range=[0, df['portfolio_composition'].max() * 1.12]),
            legend=dict(font=dict(size=14), title=dict(text='Domain', font=dict(size=15))),
            margin=dict(b=160),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 4. DISORDER INDEX — single line chart
# ---------------------------------------------------------------------------

def make_disorder_chart(entropy_df):
    if entropy_df is None or entropy_df.empty:
        fig = go.Figure()
        fig.add_annotation(text='No disorder data', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=260))
        return fig

    df = entropy_df.sort_values('period_id').copy()
    labels = [PERIOD_LABELS.get(p, str(p)) for p in df['period_id']]

    fig = go.Figure(go.Scatter(
        x=df['period_id'], y=df['disorder_index'],
        mode='lines+markers',
        line=dict(color=DARK_BLUE, width=2),
        marker=dict(size=8, color=DARK_BLUE),
        hovertemplate='Period: %{x}<br>Disorder: %{y:.4f}<extra></extra>',
        hoverlabel=dict(bgcolor=DARK_BLUE, font_size=14, font_color='white'),
        showlegend=False,
    ))
    fig.update_layout(
        **_base_layout(
            showlegend=False,
            height=260,
            margin=dict(t=10),
            xaxis=dict(
                tickvals=[0, 1, 2, 3],
                ticktext=['1990–1999', '2000–2009', '2010–2019', '2020–2024'],
                tickangle=-45, tickfont=dict(size=13, color='#111'),
                showgrid=False, showline=True, linecolor='#CCCCCC',
            ),
            yaxis=dict(
                tickfont=dict(size=13, color='#111'),
                showgrid=False, showline=True, linecolor='#CCCCCC', title=None,
            ),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 5. TOPIC LANDSCAPE — blend_white_to_color per-topic coloring
# ---------------------------------------------------------------------------

# Example: marker_styles = ['diamond','square','circle','pentagon'], comm_id%4
# domain_id(1-4) → scaled(0-3): 1→square, 2→circle, 3→pentagon, 4→diamond
DOMAIN_SYMBOLS = {0: 'square', 1: 'circle', 2: 'pentagon', 3: 'diamond'}


def make_topic_landscape(institution_id, rca_topic_df, embed_df, topics_df, domain_filter=None, field_filter=None):
    """Direct copy of topics_embedding_fun from dashboard_example.py."""

    # --- exact copy of blend_white_to_color from example ---
    def blend_white_to_color(intensity, base_rgb):
        intensity = intensity ** 3
        r = 255 - intensity * (255 - base_rgb[0])
        g = 255 - intensity * (255 - base_rgb[1])
        b = 255 - intensity * (255 - base_rgb[2])
        return f'rgb({int(r)}, {int(g)}, {int(b)})'

    def get_hover_font_color(r, g, b):
        brightness = (299*r + 587*g + 114*b)/1000
        return 'white' if brightness < 128 else 'black'

    # domain_base_colors keyed by domain_id (1-based), exact from example
    domain_base_colors = {
        1: (147, 207, 189),
        2: (98,  168, 183),
        3: (81,  128, 177),
        4: (34,  63,  115),
    }
    marker_styles = ['diamond', 'square', 'circle', 'pentagon']

    # Build lookup structures from topics_df
    topic_meta = topics_df[
        ['topic_id', 'topic_name', 'domain_name', 'field_name', 'domain_id', 'domain_id_scaled']
    ].drop_duplicates('topic_id')
    topic_meta = topic_meta.copy()
    topic_meta['topic_id']  = topic_meta['topic_id'].astype(int)
    topic_meta['domain_id'] = topic_meta['domain_id'].astype(int)

    topic_id_name_dict  = dict(zip(topic_meta['topic_id'], topic_meta['topic_name']))
    domain_id_name_dict = (
        topic_meta[['domain_id', 'domain_name']].drop_duplicates()
        .set_index('domain_id')['domain_name'].to_dict()
    )
    domain_partition = dict(zip(topic_meta['topic_id'], topic_meta['domain_id']))

    unique_comms = sorted(set(domain_partition.values()))
    topics_set   = [int(t) for t in embed_df['topic_id'].tolist()]

    # pos: topic_id → (x, -y)  — y-flipped as in example
    pos = {int(row['topic_id']): (row['feature_0'], -row['feature_1'])
           for _, row in embed_df.iterrows()}

    # Apply domain / field filters
    if domain_filter is not None:
        filtered_did = domain_filter + 1   # domain_id_scaled → domain_id
        unique_comms = [c for c in unique_comms if c == filtered_did]
        if field_filter is not None:
            keep = set(topic_meta[topic_meta['field_name'] == field_filter]['topic_id'])
        else:
            keep = set(topic_meta[topic_meta['domain_id'] == filtered_did]['topic_id'])
        topics_set = [t for t in topics_set if t in keep]

    # Recompute value as in example: (count_specialized_topic / max_per_domain) * 100
    # The CSV 'value' is a global linear scaling (value = count * constant),
    # which gives much less within-institution contrast than the example's normalization.
    inst_rca = rca_topic_df[rca_topic_df['institution_id'] == institution_id].copy()
    inst_rca['topic_id'] = inst_rca['topic_id'].astype(int)
    inst_rca['value'] = (
        inst_rca.groupby('domain_id_scaled')['count_specialized_topic']
        .transform(lambda x: x / x.max())
    ) * 100
    inst_rca['value'] = inst_rca['value'].fillna(0.0)
    value_dict = dict(zip(inst_rca['topic_id'], inst_rca['value']))

    if not topics_set:
        fig = go.Figure()
        fig.add_annotation(text='No topic data for selected filters', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        _ax = dict(showgrid=False, zeroline=False, showline=False, showticklabels=False, title=None)
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                          xaxis=_ax, yaxis=_ax)
        return fig

    # --- collect all data (exact logic from example) ---
    all_data = []
    for comm_id in unique_comms:
        shape = marker_styles[comm_id % len(marker_styles)]
        label = domain_id_name_dict.get(comm_id, f'Domain {comm_id}')
        nodes = [n for n in topics_set if domain_partition.get(n) == comm_id]
        for node in nodes:
            if node not in pos:
                continue
            x, y = pos[node]
            all_data.append({
                'x': x, 'y': y,
                'color_value': float(value_dict.get(node, 0.0)),
                'node': node,
                'comm_id': comm_id,
                'shape': shape,
                'label': label,
            })

    if not all_data:
        fig = go.Figure()
        fig.add_annotation(text='No topic data for selected filters', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        _ax = dict(showgrid=False, zeroline=False, showline=False, showticklabels=False, title=None)
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                          xaxis=_ax, yaxis=_ax)
        return fig

    # --- log scale + normalise ---
    all_color_values     = np.array([d['color_value'] for d in all_data])
    all_color_values_log = np.log1p(all_color_values)
    min_val = all_color_values_log.min()
    max_val = all_color_values_log.max()

    # sort ascending so highest-RCA dots are drawn last (on top)
    all_data.sort(key=lambda d: d['color_value'])

    # precompute per-point visuals
    for item in all_data:
        base_color = domain_base_colors[item['comm_id']]
        log_v      = np.log1p(item['color_value'])
        norm_v     = (log_v - min_val) / (max_val - min_val + 1e-9)
        intensity  = norm_v ** 3
        r = int(255 - intensity * (255 - base_color[0]))
        g = int(255 - intensity * (255 - base_color[1]))
        b = int(255 - intensity * (255 - base_color[2]))
        item['color_str']   = blend_white_to_color(norm_v, base_color)
        item['dot_size']    = 3 + (norm_v ** 2.5) * 15
        item['hover_color'] = f'rgb({r},{g},{b})'
        item['font_color']  = get_hover_font_color(r, g, b)
        item['hover_text']  = (
            f"{topic_id_name_dict.get(item['node'], str(item['node']))}"
            f"<br>{item['color_value']:.1f}"
        )

    fig = go.Figure()

    # Single trace for all points — globally sorted ascending so highest-RCA on top
    fig.add_trace(go.Scatter(
        x=[d['x'] for d in all_data],
        y=[d['y'] for d in all_data],
        mode='markers',
        marker=dict(
            symbol=[d['shape'] for d in all_data],
            size=[d['dot_size'] for d in all_data],
            color=[d['color_str'] for d in all_data],
            line=dict(width=0.3, color='lightgray'),
        ),
        text=[d['hover_text'] for d in all_data],
        hoverinfo='text',
        hoverlabel=dict(
            bgcolor=[d['hover_color'] for d in all_data],
            font_size=14,
            font_color=[d['font_color'] for d in all_data],
        ),
        showlegend=False,
    ))

    # Legend entries (one per domain, invisible data)
    for comm_id in unique_comms:
        base_color = domain_base_colors[comm_id]
        label      = domain_id_name_dict.get(comm_id, f'Domain {comm_id}')
        shape      = marker_styles[comm_id % len(marker_styles)]
        base_color_str = f'rgb({base_color[0]}, {base_color[1]}, {base_color[2]})'
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            name=label,
            marker=dict(symbol=shape, size=40, color=base_color_str,
                        line=dict(width=0.3, color='white')),
            showlegend=True,
        ))

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='black', size=14),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        legend=dict(
            title_text='Domain',
            font=dict(size=16, color='black'),
            title_font=dict(size=18, color='black'),
        ),
        margin=dict(l=20, r=200, t=10, b=20),
        showlegend=True,
    )
    return fig


# ---------------------------------------------------------------------------
# 6. IMPACT RANKING — numbered circles (from example)
# ---------------------------------------------------------------------------

def make_impact_ranking(peer_df, impact_all, institution_id, info_df):
    """
    Bump chart: rank per year within {focal + peers}.
    Peers = grey thin lines. Focal = dark blue thick line with rank number inside each marker.
    """
    if peer_df is None or peer_df.empty or impact_all is None or impact_all.empty:
        fig = go.Figure()
        fig.add_annotation(text='No impact ranking data', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=400))
        return fig

    peer_ids = peer_df['institution_id'].dropna().tolist()
    all_ids  = list(set([institution_id] + peer_ids))

    subset = impact_all[
        (impact_all['institution_id'].isin(all_ids)) & (impact_all['year'] <= 2023)
    ].copy()
    if subset.empty:
        fig = go.Figure()
        fig.add_annotation(text='No impact data for this institution', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=400))
        return fig

    subset['rank'] = (
        subset.groupby('year')['relative_impact']
        .rank(ascending=False, method='min')
        .astype(int)
    )

    focal_name_s = info_df[info_df['institution_id'] == institution_id]['institution_name']
    focal_name = focal_name_s.iloc[0] if not focal_name_s.empty else str(institution_id)
    short_focal = focal_name.replace(' (US)', '')[:35]

    fig = go.Figure()

    # Individual peer lines — very faint, with name label at last year
    last_year = subset['year'].max()
    for pid, grp in subset[subset['institution_id'] != institution_id].groupby('institution_id'):
        pname_s = info_df[info_df['institution_id'] == pid]['institution_name']
        pname = (pname_s.iloc[0].replace(' (US)', '') if not pname_s.empty else str(pid))[:28]
        grp_s = grp.sort_values('year')
        last_row = grp_s[grp_s['year'] == last_year]
        fig.add_trace(go.Scatter(
            x=grp_s['year'], y=grp_s['rank'],
            mode='lines+markers',
            marker=dict(size=8, color='rgba(190,190,190,0.5)'),
            line=dict(color='rgba(190,190,190,0.25)', width=2.5),
            name=pname, showlegend=False,
            customdata=grp_s[['relative_impact']].values,
            hovertemplate=(
                f'<b>{pname}</b><br>Year: %{{x}}<br>'
                'Rank: %{y}<br>Relative Impact: %{customdata[0]:.2f}<extra></extra>'
            ),
            hoverlabel=dict(bgcolor='rgba(180,180,180,0.95)', font_size=13, font_color='black'),
        ))

    # Focal institution — dark blue, large numbered circles
    focal = subset[subset['institution_id'] == institution_id].sort_values('year')
    if not focal.empty:
        fig.add_trace(go.Scatter(
            x=focal['year'], y=focal['rank'],
            mode='lines+markers+text',
            line=dict(color=DARK_BLUE, width=4),
            marker=dict(size=22, color=DARK_BLUE),
            text=focal['rank'].astype(str),
            textposition='middle center',
            textfont=dict(color='white', size=12, family='Arial Black'),
            name=short_focal,
            customdata=focal[['relative_impact']].values,
            hovertemplate=(
                f'<b>{short_focal}</b><br>Year: %{{x}}<br>'
                'Rank: %{y}<br>Relative Impact: %{customdata[0]:.2f}<extra></extra>'
            ),
            hoverlabel=dict(bgcolor=DARK_BLUE, font_size=16, font_color='white'),
            showlegend=False,
        ))

    n_peers = len(peer_ids) + 1
    all_years = sorted(subset['year'].unique())
    first_year = all_years[0]
    fig.update_yaxes(
        range=[n_peers + 0.5, -0.7],
        tickvals=[t for t in [1, 5, 10, 15, 20] if t <= n_peers],
        showticklabels=True,
        tickfont=dict(size=12, color='rgba(150,150,150,0.8)'),
        showgrid=True,
        gridcolor='rgba(220,220,220,0.5)',
        gridwidth=1,
        zeroline=False, title=None,
    )
    fig.update_xaxes(
        range=[first_year - 0.5, last_year + 0.5],
        tickvals=all_years,
        ticktext=[str(y) for y in all_years],
        tickangle=-45,
        tickfont=dict(size=13, color='black'),
        showgrid=False, showline=False,
    )
    fig.update_layout(
        **_base_layout(
            height=360,
            showlegend=False,
            font=dict(color='black'),
            margin=dict(l=20, r=20, t=10, b=40),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 7. IMPACT BUBBLE — jitter chart (from example: jitter_impact_fun)
# ---------------------------------------------------------------------------

def make_impact_bubble(institution_id, peer_df, impact_all, info_df,
                       selected_years=(2014, 2016, 2018, 2020, 2022, 2023)):
    """
    Jitter bubble chart:
    x = relative_impact
    y = year + small jitter
    bubble size = impact_uniformity * size_scale
    Grey bubbles = peers; Dark blue = focal institution.
    Size legend shown on right.
    """
    if impact_all is None or impact_all.empty:
        fig = go.Figure()
        fig.add_annotation(text='No impact data', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=400))
        return fig

    peer_ids  = peer_df['institution_id'].dropna().tolist() if peer_df is not None and not peer_df.empty else []
    all_ids   = list(set([institution_id] + peer_ids))
    avail     = sorted(impact_all['year'].unique())
    years_use = [y for y in selected_years if y in avail] or avail[-6:]

    subset = impact_all[
        (impact_all['institution_id'].isin(all_ids)) &
        (impact_all['year'].isin(years_use))
    ].dropna(subset=['relative_impact', 'impact_uniformity']).copy()

    if subset.empty:
        fig = go.Figure()
        fig.add_annotation(text='No impact data for selected years', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=400))
        return fig

    np.random.seed(42)
    subset['year_j'] = subset['year'] + np.random.uniform(-0.18, 0.18, size=len(subset))
    size_scale = 28

    focal_name_s = info_df[info_df['institution_id'] == institution_id]['institution_name']
    focal_name = focal_name_s.iloc[0] if not focal_name_s.empty else str(institution_id)
    short_focal = focal_name.replace(' (US)', '')[:30]

    fig = go.Figure()

    # All peers — single combined trace (no per-institution loop)
    peers_d = subset[subset['institution_id'] != institution_id].copy()
    if not peers_d.empty:
        name_map = info_df.set_index('institution_id')['institution_name'].str.replace(' (US)', '', regex=False)
        peers_d['_pname'] = peers_d['institution_id'].map(name_map).fillna('Peer')
        fig.add_trace(go.Scatter(
            x=peers_d['relative_impact'], y=peers_d['year_j'],
            mode='markers',
            marker=dict(
                size=peers_d['impact_uniformity'] * size_scale,
                color='rgba(180,180,180,0.35)',
                line=dict(width=1, color='rgba(80,80,80,0.5)'),
            ),
            customdata=peers_d[['year', 'impact_uniformity', '_pname']].values,
            hovertemplate=(
                '<b>%{customdata[2]}</b><br>Year: %{customdata[0]:.0f}<br>'
                'Relative Impact: %{x:.2f}<br>'
                'Uniformity: %{customdata[1]:.2f}<extra></extra>'
            ),
            hoverlabel=dict(bgcolor='rgba(200,200,200,0.9)', font_size=14, font_color='black'),
            showlegend=False,
        ))

    # Reference line at x=1 (peer average baseline)
    fig.add_vline(x=1.0, line=dict(color='#CCCCCC', width=1, dash='dot'))

    # Focal institution (dark blue)
    focal_d = subset[subset['institution_id'] == institution_id]
    if not focal_d.empty:
        fig.add_trace(go.Scatter(
            x=focal_d['relative_impact'], y=focal_d['year_j'],
            mode='markers',
            marker=dict(
                size=focal_d['impact_uniformity'] * size_scale,
                color=DARK_BLUE,
                line=dict(width=1, color='white'),
            ),
            customdata=focal_d[['year', 'impact_uniformity']].values,
            hovertemplate=(
                f'<b>{short_focal}</b><br>'
                'Year: %{customdata[0]:.0f}<br>'
                'Relative Impact: %{x:.2f}<br>'
                'Uniformity: %{customdata[1]:.2f}<extra></extra>'
            ),
            hoverlabel=dict(bgcolor=DARK_BLUE, font_size=16, font_color='white'),
            showlegend=False,
        ))

    fig.update_xaxes(
        title='Relative Impact',
        title_font=dict(size=16, color='black'),
        tickfont=dict(size=14, color='black'),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor='lightgray',
        showline=False,
        tickvals=years_use,
        ticktext=[str(y) for y in years_use],
        tickfont=dict(size=14, color='black'),
    )
    fig.update_layout(
        **_base_layout(
            height=360,
            showlegend=False,
            margin=dict(l=20, r=20, t=10, b=20),
        )
    )
    return fig


# ---------------------------------------------------------------------------
# 8a. SINGLE LINE — works, authors, or disorder (for 3-column layout)
# ---------------------------------------------------------------------------

def make_single_line(df, x_col, y_col, title,
                     x_tickvals=None, x_ticktext=None, x_tickangle=-45,
                     peer_df=None, all_df=None, show_legend=None):
    """Generic line chart for historical data. Optional peer_df adds a grey avg line.
    Optional all_df adds a dashed comparison line for the full dataset."""
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(text='No data', showarrow=False,
                           x=0.5, y=0.5, xref='paper', yref='paper',
                           font=dict(size=14, color='#999'))
        fig.update_layout(**_base_layout(height=260))
        return fig

    df = df.dropna(subset=[x_col, y_col])
    has_peers = peer_df is not None and not peer_df.empty and y_col in peer_df.columns
    has_all = all_df is not None and not all_df.empty and y_col in all_df.columns
    display_legend = show_legend if show_legend is not None else (has_peers or has_all)

    fig = go.Figure()

    # Full-dataset comparison line (behind everything)
    if has_all:
        all_df_c = all_df.dropna(subset=[x_col, y_col]).sort_values(x_col)
        fig.add_trace(go.Scatter(
            x=all_df_c[x_col], y=all_df_c[y_col],
            mode='lines+markers',
            line=dict(color='rgba(34,63,115,0.35)', width=1.5),
            marker=dict(size=6, color='rgba(34,63,115,0.35)'),
            name='All fields',
            hovertemplate=f'All fields: %{{y:,.0f}}<extra></extra>',
            hoverlabel=dict(bgcolor='rgba(100,100,150,0.9)', font_size=13, font_color='white'),
            showlegend=True,
        ))

    # Peer average line (behind focal)
    if has_peers:
        peer_mean = (
            peer_df.dropna(subset=[x_col, y_col])
            .groupby(x_col)[y_col].mean()
            .reset_index()
            .sort_values(x_col)
        )
        fig.add_trace(go.Scatter(
            x=peer_mean[x_col], y=peer_mean[y_col],
            mode='lines',
            line=dict(color='rgba(150,150,150,0.6)', width=1.5, dash='dot'),
            name='Peers (avg)',
            hovertemplate='Peers avg: %{y:,.0f}<extra></extra>',
            hoverlabel=dict(bgcolor='rgba(200,200,200,0.9)', font_size=13, font_color='black'),
            showlegend=True,
        ))

    # Focal institution line
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode='lines+markers',
        line=dict(color=DARK_BLUE, width=2),
        marker=dict(size=8, color=DARK_BLUE),
        hovertemplate=f'{title}: %{{y:,.0f}}<extra></extra>',
        hoverlabel=dict(bgcolor=DARK_BLUE, font_size=14, font_color='white'),
        showlegend=False,
    ))

    xaxis = dict(
        title_font=dict(size=16, color='black'),
        tickfont=dict(size=14, color='black'),
        showgrid=False, showline=True, linecolor='#CCCCCC',
        tickangle=x_tickangle,
    )
    if x_tickvals is not None:
        xaxis['tickvals'] = x_tickvals
        xaxis['ticktext'] = x_ticktext

    all_vals = list(df[y_col])
    if has_peers:
        all_vals += list(peer_mean[y_col])
    if has_all:
        all_vals += list(all_df.dropna(subset=[y_col])[y_col])
    y_max = max(all_vals) * 1.12 if all_vals else None

    fig.update_layout(
        **_base_layout(
            showlegend=display_legend,
            height=260,
            margin=dict(t=10, r=20, b=60),
            xaxis=xaxis,
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                showgrid=False, showline=True, linecolor='#CCCCCC',
                range=[0, y_max] if y_max else None,
                title=None,
            ),
            legend=dict(
                bgcolor='rgba(0,0,0,0)', borderwidth=0,
                font=dict(size=12), orientation='h',
                yanchor='top', y=-0.28,
                xanchor='center', x=0.5,
            ),
        )
    )
    return fig


def make_works_chart(stats_df, institution_id, peer_stats_df=None, all_stats_df=None):
    df = stats_df[stats_df['institution_id'] == institution_id].sort_values('year') if stats_df is not None and not stats_df.empty else pd.DataFrame()
    all_df = all_stats_df[all_stats_df['institution_id'] == institution_id].sort_values('year') if all_stats_df is not None and not all_stats_df.empty else None
    return make_single_line(df, 'year', 'n_works', 'Works',
                            x_tickvals=list(range(2014, 2025)),
                            peer_df=peer_stats_df, all_df=all_df, show_legend=None)


def make_authors_chart(stats_df, institution_id, peer_stats_df=None, all_stats_df=None):
    df = stats_df[stats_df['institution_id'] == institution_id].sort_values('year') if stats_df is not None and not stats_df.empty else pd.DataFrame()
    all_df = all_stats_df[all_stats_df['institution_id'] == institution_id].sort_values('year') if all_stats_df is not None and not all_stats_df.empty else None
    return make_single_line(df, 'year', 'n_authors', 'Authors',
                            x_tickvals=list(range(2014, 2025)),
                            peer_df=peer_stats_df, all_df=all_df, show_legend=None)


# ---------------------------------------------------------------------------
# 9. PORTFOLIO EVOLUTION — domain shares across periods
# ---------------------------------------------------------------------------

def make_portfolio_evolution(rca_df, granularity='All', entropy_df=None, color_domain_idx=None):
    if rca_df is None or rca_df.empty:
        fig = go.Figure()
        fig.update_layout(**_base_layout(height=220))
        return fig

    if 'domain_id' in rca_df.columns:
        rca_df = rca_df.copy()
        rca_df['_d'] = (rca_df['domain_id'] - 1).clip(0, 3).astype(int)
    elif 'domain_id_scaled' in rca_df.columns:
        rca_df = rca_df.copy()
        rca_df['_d'] = rca_df['domain_id_scaled'].clip(0, 3).astype(int)
    elif color_domain_idx is not None:
        rca_df = rca_df.copy()
        rca_df['_d'] = int(color_domain_idx)
    else:
        rca_df = rca_df.copy()
        rca_df['_d'] = 0

    if granularity == 'Field' and 'subfield_name' in rca_df.columns:
        group_col = 'subfield_name'
    elif granularity in ('Domain', 'Field') and 'field_name' in rca_df.columns:
        group_col = 'field_name'
    else:
        group_col = 'domain_name'
    use_fields = group_col != 'domain_name'
    agg = rca_df.groupby(['period_id', '_d', group_col])['portfolio_composition'].sum().reset_index()
    periods = sorted(agg['period_id'].unique())

    # Build disorder index lookup {period_id: value}
    disorder_map = {}
    if entropy_df is not None and not entropy_df.empty:
        for _, row in entropy_df.iterrows():
            disorder_map[int(row['period_id'])] = float(row['disorder_index'])

    fig = go.Figure()
    if use_fields:
        # Per-field shades within each domain
        items = agg[['_d', group_col]].drop_duplicates().sort_values(['_d', group_col])
        domain_field_count = items.groupby('_d')[group_col].count().to_dict()
        domain_field_idx = {d: 0 for d in items['_d'].unique()}
        for _, row in items.iterrows():
            d = int(row['_d'])
            n = domain_field_count[d]
            i = domain_field_idx[d]
            if granularity == 'All':
                t = 0.4 + 0.6 * (i / max(n - 1, 1)) if n > 1 else 0.85
            else:
                t = 0.72 if i % 2 == 0 else 0.38
            color = _domain_shade(d, t)
            base_color = DOMAIN_COLORS.get(d, PALETTE['teal'])
            fname = row[group_col]
            grp = agg[agg[group_col] == fname]
            fig.add_trace(go.Bar(
                name=fname,
                x=[PERIOD_LABELS.get(p, str(p)) for p in periods],
                y=[grp[grp['period_id'] == p]['portfolio_composition'].sum() for p in periods],
                marker_color=color,
                marker_line=dict(width=1.5, color='white'),
                hovertemplate=f'<b>{fname}</b><br>%{{x}}<br>%{{y:.1%}}<extra></extra>',
                hoverlabel=dict(bgcolor=base_color, font_color='white', font_size=14),
                showlegend=True,
            ))
            domain_field_idx[d] += 1
    else:
        for d in sorted(agg['_d'].unique()):
            d = int(d)
            color = DOMAIN_COLORS.get(d, PALETTE['teal'])
            grp = agg[agg['_d'] == d]
            dom_name = grp['domain_name'].iloc[0] if not grp.empty else f'Domain {d}'
            fig.add_trace(go.Bar(
                name=dom_name,
                x=[PERIOD_LABELS.get(p, str(p)) for p in periods],
                y=[grp[grp['period_id'] == p]['portfolio_composition'].sum() for p in periods],
                marker_color=color, marker_line_width=0,
                hovertemplate=f'<b>{dom_name}</b><br>%{{x}}<br>%{{y:.1%}}<extra></extra>',
                hoverlabel=dict(bgcolor=color, font_color='white', font_size=14),
            ))

    # Annotate disorder index above each stacked bar
    if disorder_map:
        for p in periods:
            if p in disorder_map:
                total = agg[agg['period_id'] == p]['portfolio_composition'].sum()
                fig.add_annotation(
                    x=PERIOD_LABELS.get(p, str(p)),
                    y=total,
                    text=f'<b>DI: {disorder_map[p]:.3f}</b>',
                    showarrow=False,
                    yanchor='bottom',
                    yshift=6,
                    font=dict(size=12, color='#444444', family='Arial, sans-serif'),
                )

    fig.update_layout(
        **_base_layout(
            barmode='stack', height=280,
            xaxis=dict(showgrid=False, showline=True, linecolor='#CCCCCC',
                       tickfont=dict(size=14)),
            yaxis=dict(tickformat='.0%', showgrid=False, showline=True,
                       linecolor='#CCCCCC', tickfont=dict(size=13), title=None),
            legend=dict(font=dict(size=13), orientation='h',
                        yanchor='bottom', y=1.02, xanchor='left', x=0),
        )
    )
    return fig
