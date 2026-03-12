import os

DATA_ROOT   = os.path.join(os.path.dirname(__file__), 'Data_Tables')
ALL_PATH    = os.path.join(DATA_ROOT, 'All')
DOMAIN_PATH = os.path.join(DATA_ROOT, 'Domain')
FIELD_PATH  = os.path.join(DATA_ROOT, 'Field')
TOPIC_PATH  = os.path.join(DATA_ROOT, 'Topic')

PALETTE = {
    'light_green': 'rgb(147,207,189)',
    'teal':        'rgb(98,168,183)',
    'medium_blue': 'rgb(81,128,177)',
    'dark_blue':   'rgb(34,63,115)',
    'bg':          '#FAFAFA',
    'grid':        '#E8E8E8',
    'text':        '#1a1a1a',
}

# 4 domains keyed by domain_id_scaled (0–3)
DOMAIN_COLORS = {
    0: 'rgb(147,207,189)',
    1: 'rgb(98,168,183)',
    2: 'rgb(81,128,177)',
    3: 'rgb(34,63,115)',
}

DOMAIN_COLORS_HEX = {
    0: '#93CFBD',
    1: '#62A8B7',
    2: '#5180B1',
    3: '#223F73',
}

PERIOD_LABELS = {
    0: '1990–1999',
    1: '2000–2009',
    2: '2010–2019',
    3: '2020–2024',
}

# Shared Plotly layout for NYT style
NYT_LAYOUT = dict(
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FFFFFF',
    font=dict(
        family='Arial, sans-serif',
        color='#1a1a1a',
        size=11,
    ),
    xaxis=dict(
        showgrid=True,
        gridcolor='#E8E8E8',
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=10, color='#666666'),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#E8E8E8',
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=10, color='#666666'),
    ),
    margin=dict(l=40, r=20, t=40, b=40),
    showlegend=True,
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        borderwidth=0,
        font=dict(size=10),
    ),
)
