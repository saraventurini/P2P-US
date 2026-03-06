import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import pickle
import pydeck as pdk
import numpy as np
import plotly.express as px
import networkx as nx

st.markdown(
    """
    <style>
    /* Page background */
    body {
        background-color: lightgoldenrodyellow;
    }

    /* Selectbox main container */
    div.stSelectbox > div[data-baseweb] > div {
        border-color: #000066 !important;  /* border color */
    }

    /* Selectbox dropdown list */
    div.stSelectbox > div[data-baseweb] ul {
        background-color: red !important;  /* dropdown background */
        color: white !important;           /* text color */
    }
    
    /* Reduce top padding and margin */
    .block-container {
        padding-top: 2.1rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Remove top margin from first element */
    .main > div:first-child {
        padding-top: 0 !important;
    }
    
    /* Reduce header spacing */
    h1 {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)




# ----------------------------
# FUNCTIONS
# ----------------------------
def get_hover_font_color(r, g, b):
    brightness = (299*r + 587*g + 114*b)/1000
    return 'white' if brightness < 128 else 'black'
def institutions_map_fun(G_z, pos, node_labels, cluster_labels_dict, clusters_colors_dict, institution_peers_dict, highlight_node=None):
    G_nodes = G_z.nodes()

    if highlight_node != None:
        highlight_nodes = {highlight_node}  # single highlight node
        neighbors = institution_peers_dict[highlight_node]
    else:
         highlight_nodes = {}
         neighbors = {}

    # --- Edges ---
    edge_x, edge_y = [], []
    highlight_edge_x, highlight_edge_y = [], []

    for edge in G_z.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        # if (edge[0] in highlight_nodes or edge[1] in highlight_nodes):
        if (edge[0] in highlight_nodes and edge[1] in neighbors) or (edge[1] in highlight_nodes and edge[0] in neighbors):
            highlight_edge_x.extend([x0, x1, None])
            highlight_edge_y.extend([y0, y1, None])
        else:
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.4, color='lightgray'),
        hoverinfo='none', mode='lines'
    )

    if highlight_node != None:
        highlight_edge_trace = go.Scatter(
            x=highlight_edge_x, y=highlight_edge_y,
            line=dict(width=1, color='black'),
            hoverinfo='none', mode='lines'
        )

        # # --- Neighbors ---
        # neighbors = set()
        # for n in highlight_nodes:
        #     neighbors.update(G_z.neighbors(n))
        # neighbors -= highlight_nodes
        # neighbors = institution_peers_dict[highlight_node]
    # else:
    #     neighbors = {}

    # --- Nodes ---
    node_x, node_y, node_color, node_hover = [], [], [], []
    neighbor_x, neighbor_y, neighbor_color, neighbor_hover = [], [], [], []
    if highlight_node != None:
        highlight_x, highlight_y, highlight_color, highlight_hover = [], [], [], []

    normal_nodes_list = []
    neighbor_nodes_list = []
    highlight_nodes_list = []
    for i in G_nodes:
        x, y = pos[i]
        r, g, b, a = clusters_colors_dict[cluster_labels_dict[i]]
        rgba_str = f'rgba({r},{g},{b},{a})'
        #hover = f"{node_labels[i]}<br>community {cluster_labels_dict[i]}"
        hover = f"{node_labels[i]}"

        if i in highlight_nodes:
            rgba_highlight = f'rgba({r},{g},{b},1.0)'
            highlight_x.append(x)
            highlight_y.append(y)
            highlight_color.append(rgba_highlight)
            highlight_hover.append(hover)
            highlight_nodes_list.append(i)
        elif i in neighbors:
            rgba_neighbor = f'rgba({r},{g},{b},0.9)'
            neighbor_x.append(x)
            neighbor_y.append(y)
            neighbor_color.append(rgba_neighbor)
            neighbor_hover.append(hover)
            neighbor_nodes_list.append(i)
        else:
            node_x.append(x)
            node_y.append(y)
            node_color.append(rgba_str)
            node_hover.append(hover)
            normal_nodes_list.append(i)

    # --- Traces ---
    # --- normal nodes ---
    normal_hover_colors = [
        get_hover_font_color(r, g, b) 
        for r, g, b, a in [clusters_colors_dict[cluster_labels_dict[i]] for i in normal_nodes_list]
    ]

    normal_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers',
        hoverinfo='text', text=node_hover,
        marker=dict(color=node_color, size=7, line=dict(width=0.5, color='white')),
        hoverlabel=dict(
            bgcolor=node_color,
            font=dict(color=normal_hover_colors, size=16)
        )
    )

    # --- neighbors ---
    neighbor_hover_colors = [
        get_hover_font_color(r, g, b) 
        for r, g, b, a in [clusters_colors_dict[cluster_labels_dict[i]] for i in neighbor_nodes_list]
    ]

    neighbor_trace = go.Scatter(
        x=neighbor_x, y=neighbor_y, mode='markers',
        hoverinfo='text', text=neighbor_hover,
        marker=dict(color=neighbor_color, size=8, line=dict(width=2, color='gray')),
        hoverlabel=dict(
            bgcolor=neighbor_color,
            font=dict(color=neighbor_hover_colors, size=16)
        )
    )

    # --- highlight ---
    if highlight_node is not None:
        highlight_hover_colors = [
            get_hover_font_color(r, g, b) 
            for r, g, b, a in [clusters_colors_dict[cluster_labels_dict[i]] for i in highlight_nodes]
        ]

        highlight_trace = go.Scatter(
            x=highlight_x, y=highlight_y,
            hoverinfo='text', text=highlight_hover,
            textposition='top center',
            marker=dict(color=highlight_color, size=15, line=dict(width=2, color='black')),
            hoverlabel=dict(
                bgcolor=highlight_color,
                font=dict(color=highlight_hover_colors, size=16)
            )
        )

        # --- Figure ---
        fig = go.Figure(
            data=[edge_trace, highlight_edge_trace, normal_trace, neighbor_trace, highlight_trace],
            layout=go.Layout(
                width=600, height=600,
                showlegend=False, hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                plot_bgcolor='white', paper_bgcolor='white',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )

        # --- Dynamic zoom centered on the highlighted node ---
        hx, hy = pos[highlight_node]

        # Compute spread of graph coordinates
        x_vals = np.array([p[0] for p in pos.values()])
        y_vals = np.array([p[1] for p in pos.values()])
        x_span = x_vals.max() - x_vals.min()
        y_span = y_vals.max() - y_vals.min()

        # Zoom factor relative to graph size
        zoom_fraction = 0.5  # 15% of graph width/height
        x_half = (x_span * zoom_fraction) / 2
        y_half = (y_span * zoom_fraction) / 2

        x_range = [hx - x_half, hx + x_half]
        y_range = [hy - y_half, hy + y_half]

        fig.update_layout(
            xaxis=dict(range=x_range, showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=y_range, showgrid=False, zeroline=False, showticklabels=False,
                       scaleanchor="x", scaleratio=1)
        )

    else:
        # --- Figure ---
        fig = go.Figure(
            data=[edge_trace, normal_trace, neighbor_trace],
            layout=go.Layout(
                width=550, height=550,
                showlegend=False, hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=0),
                plot_bgcolor='white', paper_bgcolor='white',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )   

    return fig


def topics_embedding_fun(RCA_topic_row, topics_embedding_reduced_df, topics_set, pos, unique_comms, domain_partition, domain_id_name_dict, domain_base_colors, marker_styles):
    
    color_column = 'value'
    temp = RCA_topic_row.copy()
    topics_embedding_reduced_df = topics_embedding_reduced_df.copy().merge(temp.drop(columns='institution_id'), on=['topic_id'])
    
    fig = go.Figure()
    
    # Function to get hover font color based on brightness
    def get_hover_font_color(r, g, b):
        brightness = (299*r + 587*g + 114*b)/1000
        return 'black' if brightness < 128 else 'white'  # Black for light, white for dark
    
    # Collect all data first
    all_data = []
    for comm_id in unique_comms:
        shape = marker_styles[comm_id % len(marker_styles)]
        label = domain_id_name_dict[comm_id]
        
        # Filter nodes in this community
        nodes = [node for node in topics_set if domain_partition[node] == comm_id]
        
        for node in nodes:
            x = pos[node][0]
            y = pos[node][1]
            color_value = topics_embedding_reduced_df.loc[topics_embedding_reduced_df['topic_id'] == node, color_column].values[0]
            
            all_data.append({
                'x': x,
                'y': y,
                'color_value': color_value,
                'node': node,
                'comm_id': comm_id,
                'shape': shape,
                'label': label
            })
    
    # Apply log scale to color values (add small constant to avoid log(0))
    all_color_values = np.array([d['color_value'] for d in all_data])
    all_color_values_log = np.log1p(all_color_values)  # log1p = log(1 + x), handles zeros
    min_val = all_color_values_log.min()
    max_val = all_color_values_log.max()
    
    # Sort all data by color_value in descending order (highest last = drawn on top)
    all_data.sort(key=lambda d: d['color_value'])
    
    # Now plot by community, but in the sorted order
    plotted_communities = set()
    
    for item in all_data:
        comm_id = item['comm_id']
        label = item['label']
        
        # Get base color for this community
        base_color = domain_base_colors[comm_id]
        
        # Apply log transform to this value and normalize
        color_value_log = np.log1p(item['color_value'])
        norm_value = (color_value_log - min_val) / (max_val - min_val + 1e-9)
        
        # Get blended color as RGB tuple
        color_rgb = blend_white_to_color(norm_value, base_color)
        
        # Format color properly - check if it's already a string or tuple
        if isinstance(color_rgb, str):
            color_str = color_rgb
            hover_font_color = "black"  # default for unknown colors
        else:
            r, g, b = int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2])
            color_str = f'rgb({r}, {g}, {b})'
            hover_font_color = get_hover_font_color(r, g, b)
        
        # Add data point
        fig.add_trace(go.Scatter(
            x=[item['x']],
            y=[item['y']],
            mode='markers',
            marker=dict(
                symbol=item['shape'],
                size=10,
                color=color_str,
                line=dict(width=0.3, color='lightgray'),
            ),
            hoverinfo='text',
            text=f'{topic_id_name_dict[item["node"]]}<br>{color_column}: {item["color_value"]:.1f}',
            hoverlabel=dict(
                bgcolor=color_str,
                font_size=14,
                font_color=hover_font_color  # Dynamic: black on light, white on dark
            ),
            showlegend=False,
            legendgroup=label
        ))
        
        # Add legend entry only once per community
        if comm_id not in plotted_communities:
            base_color_str = f'rgb({base_color[0]}, {base_color[1]}, {base_color[2]})'
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                name=label,
                marker=dict(
                    symbol=item['shape'],
                    size=40,
                    color=base_color_str,
                    line=dict(width=0.3, color='white'),
                ),
                showlegend=True,
                legendgroup=label
            ))
            plotted_communities.add(comm_id)
    
    fig.update_layout(
        width=1000,
        height=600,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='white',
        legend=dict(
            title_text="Domain",
            font=dict(size=16,color='black'),
            title_font=dict(size=18,color='black')
        ),
        margin=dict(l=20, r=200, t=10, b=20)
    )

    return fig

def line_rank_fun(temp, highlight_institution):
    hover_dict = {
        'year': True,
        'relative_impact': True,
        'rank_relative_impact': True,
    }
    
    fig = go.Figure()
    
    # Plot all lines as gray
    for inst_name, df_inst in temp.groupby("institution_name"):
        fig.add_trace(
            go.Scatter(
                x=df_inst["year"],
                y=df_inst["rank_relative_impact"],
                mode="lines+markers",
                line=dict(color='rgba(200, 200, 200, 0.5)', width=3),
                marker=dict(size=10, color="rgba(200, 200, 200, 0.5)"),
                name=inst_name,
                customdata=df_inst[["relative_impact"]],
                hovertemplate=(
                    f"<b>{inst_name}</b><br>"
                    "Year: %{x}<br>"
                    "Rank: %{y}<br>"
                    "Relative Impact: %{customdata[0]:.2f}<extra></extra>"
                ),
                hoverlabel=dict(
                    bgcolor="rgba(200, 200, 200, 0.9)",
                    font_size=14,
                    font_color="black"
                ),
                showlegend=False
            )
        )
    
    # Highlight one institution if given
    if highlight_institution and highlight_institution in temp["institution_name"].unique():
        df_high = temp[temp["institution_name"] == highlight_institution]
        
        # Add the line and markers with text inside
        fig.add_trace(
            go.Scatter(
                x=df_high["year"],
                y=df_high["rank_relative_impact"],
                mode="lines+markers+text",
                line=dict(color="#000066", width=6),
                marker=dict(size=30, color="#000066"),
                text=df_high["rank_relative_impact"],
                textposition="middle center",
                textfont=dict(
                    color="white",
                    size=15,
                    family="Arial Black",
                ),
                name=highlight_institution,
                customdata=df_high[["relative_impact"]],
                hovertemplate=(
                    f"<b>{highlight_institution}</b><br>"
                    "Year: %{x}<br>"
                    "Rank: %{y}<br>"
                    "Relative Impact: %{customdata[0]:.2f}<extra></extra>"
                ),
                hoverlabel=dict(
                    bgcolor="#000066",
                    font_size=16,
                    font_color="white"
                ),
                showlegend=False
            )
        )
    
    # Layout styling
    fig.update_yaxes(
        autorange='reversed',
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        title=None,
    )
    
    fig.update_xaxes(
        tickfont=dict(size=20,color='black')
    )
    
    fig.update_layout(
        height=500,
        width=1500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        font=dict(color="black"),
        margin=dict(l=20, r=10, t=10, b=20)
    )
    
    return fig


def jitter_impact_fun(temp, highlight_institution):
    np.random.seed(42)
    jitter_strength = 0.2
    temp['year_jitter'] = temp['year'] + np.random.uniform(-jitter_strength, jitter_strength, size=len(temp))
    size_scale = 30
    
    fig = go.Figure()
    
    # Plot all other institutions in gray
    for inst_name, df_inst in temp.groupby("institution_name"):
        if inst_name != highlight_institution:
            fig.add_trace(
                go.Scatter(
                    x=df_inst['relative_impact'],
                    y=df_inst['year_jitter'],
                    mode='markers',
                    marker=dict(
                        size=df_inst['impact_uniformity']*size_scale,
                        color='rgba(200, 200, 200, 0.5)',
                        line=dict(width=0.5, color='black')
                    ),
                    hovertemplate=(
                        f"<b>{inst_name}</b><br>"
                        "Year: %{y:.0f}<br>"
                        "Relative Impact: %{x:.2f}<br>"
                        "Impact Uniformity: %{marker.size:.1f}<br>"
                        "<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor="rgba(200, 200, 200, 0.9)",
                        font_size=14,
                        font_color="white"
                    ),
                    showlegend=False
                )
            )
    
    # Highlighted institution in blue
    if highlight_institution in temp['institution_name'].unique():
        df_high = temp[temp['institution_name'] == highlight_institution]
        fig.add_trace(
            go.Scatter(
                x=df_high['relative_impact'],
                y=df_high['year_jitter'],
                mode='markers',
                marker=dict(
                    size=df_high['impact_uniformity']*size_scale,
                    color='#000066',
                    line=dict(width=1, color='black')
                ),
                hovertemplate=(
                    f"<b>{highlight_institution}</b><br>"
                    "Year: %{y:.0f}<br>"
                    "Relative Impact: %{x:.2f}<br>"
                    "Impact Uniformity: %{marker.size:.1f}<br>"
                    "<extra></extra>"
                ),
                hoverlabel=dict(
                    bgcolor="#000066",
                    font_size=16,
                    font_color="white"
                ),
                showlegend=False
            )
        )
    
    # --- Add marker size legend only ---
    # Pick representative impact_uniformity values (min, median, max)
    impact_vals = temp['impact_uniformity']
    size_legend_values = [impact_vals.min(), (impact_vals.max()-impact_vals.min())/2, impact_vals.max()]
    
    for val in size_legend_values:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],  # not plotted
                mode='markers',
                marker=dict(
                    size=val*size_scale,
                    color='gray',
                    line=dict(width=0.5, color='black')
                ),
                name=f'Impact Uniformity = {val:.2f}',
                showlegend=True
            )
        )
    
    # Layout
    fig.update_layout(
        xaxis_title="Relative Impact",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=600,
        #margin=dict(r=250),  # Add right margin for legend
        margin=dict(l=20, r=250, t=10, b=20),
        legend=dict(
            title=dict(text="Marker Size", font=dict(size=18,color='black')),
            font=dict(size=16,color='black'),
            yanchor="top", 
            y=0.99, 
            xanchor="left", 
            x=1.02  # Position legend outside on the right
        ),
    )
    
    fig.update_xaxes(
        title_font=dict(size=22,color='black'),  # X-axis title bigger
        tickfont=dict(size=20,color='black')
    )
    
    years = list(set(temp.year))
    years.sort()
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=False,
        linecolor='black',
        tickvals=years,
        ticktext=[str(y) for y in years],
        tickfont=dict(size=20,color='black')  # Y-axis labels bigger
    )
    
    return fig


def plot_time_fun(df, col1, col2, min_, max_):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[col1],
            y=df[col2],
            mode='lines+markers',
            line=dict(color='#000066', width=2),  # Thinner line (was 4)
            marker=dict(size=8, color='#000066'),  # Smaller markers (was 12)
            hovertemplate=(
                "Period: %{x}<br>"
                "Number of Works: %{y}<br>"
                "<extra></extra>"
            ),
            hoverlabel=dict(
                bgcolor="#000066",
                font_size=16,
                font_color="white"
            )
        )
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=10),
        height=250,  # Less high (was 500)
        font=dict(size=14)
    )
    # Define x-axis ticks and labels with rotation
    if col2=='disorder_index':
        fig.update_xaxes(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black'),
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=False,
            side='bottom',
            tickvals=[0, 1, 2, 3],  # Positions where ticks appear
            ticktext=["1990-1999", "2000-2009", "2010-2019", "2020-2024"],  # Labels to show
            tickangle=-45  # Rotate labels 45 degrees
        )
        fig.update_yaxes(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black'),
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=False,
            side='left',
            #tickvals=[-5,-4,-3,-2,-1,0,1,1.5], 
            #range=[-5.5, 1.5],
        )
    else:
        fig.update_xaxes(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black'),
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=False,
            side='bottom',
            tickvals=list(range(2014, 2025)),  # Positions where ticks appear
            tickangle=-45 
        )       
        fig.update_yaxes(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black'),
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=False,
            side='left',
            range=[0, df[col2].max() * 1.1]
        )

    return fig



# ----------------------------
# STREAMLIT PAGE
# ----------------------------
st.set_page_config(layout="wide")

# Load datasets
institutions_info_df_selected = pd.read_csv("institutions_info_df_selected.csv.gz", compression="gzip")
institutions_selected = sorted(institutions_info_df_selected['institution_name'].unique())
institutions_selected.sort()
n_institutions_selected = len(institutions_selected)
dict_institution_name_id_selected = institutions_info_df_selected[['institution_id','institution_name']].set_index('institution_name').to_dict()['institution_id']
dict_institution_id_name_selected = institutions_info_df_selected[['institution_id','institution_name']].set_index('institution_id').to_dict()['institution_name']
dict_institution_id_institution_id_scaled2_selected = institutions_info_df_selected[['institution_id']].reset_index().set_index('institution_id').to_dict()['index']
with open(f'dict_institution_id_name.pkl', "rb") as f:
    dict_institution_id_name = pickle.load(f)

with open(f'network_data_k{10}_period{3}.pkl', "rb") as f:
    [G_all, pos_all, node_labels_all, community_labels_dict_all, community_colors_dict_all] = pickle.load(f)
network_data_bydomain_dict = pickle.load(open(f'network_data_k{10}_period{3}_bydomain_dict.pkl', "rb"))

#institutions_stats_periods_selected = pd.read_csv("institutions_stats_periods_selected.csv.gz", compression="gzip")
institutions_stats_selected_all = pd.read_csv("institutions_stats_selected.csv.gz", compression="gzip")
institutions_stats_selected_bydomain_dict = pickle.load(open(f'institutions_stats_selected_bydomain_dict.pkl', "rb"))

institutions_relationships_df_selected = pd.read_csv("institutions_relationships_df_selected.csv.gz", compression="gzip")
edges_df_selected_all = pd.read_csv("edges_df_selected.csv.gz", compression="gzip")
edges_df_selected_all['institution_name_neighbor'] = edges_df_selected_all['institution_id_neighbor'].map(dict_institution_id_name_selected)
edges_df_selected_all['institution_id_scaled2'] = edges_df_selected_all['institution_id'].map(dict_institution_id_institution_id_scaled2_selected)
edges_df_selected_all['institution_id_scaled2_neighbor'] = edges_df_selected_all['institution_id_neighbor'].map(dict_institution_id_institution_id_scaled2_selected)
institution_peers_dict_all = edges_df_selected_all.groupby(['institution_id_scaled2']).institution_id_scaled2_neighbor.apply(set).to_dict()
edges_df_selected_bydomain_dict = pickle.load(open(f'edges_df_selected_bydomain_dict.pkl', "rb"))
institution_peers_dict_bydomain_dict = pickle.load(open(f'institution_peers_dict_bydomain_dict.pkl', "rb"))

RCA_df_selected_all = pd.read_csv("RCA_df_selected.csv.gz", compression="gzip") 
entropy_df_selected_all = pd.read_csv("entropy_df_selected.csv.gz", compression="gzip") 
#entropy_min_all, entropy_max_all = entropy_df_selected_all.disorder_index.min(),entropy_df_selected_all.disorder_index.max()
RCA_df_selected_bydomain_dict = pickle.load(open(f'RCA_df_selected_bydomain_dict.pkl', "rb"))
entropy_df_selected_bydomain_dict = pickle.load(open(f'entropy_df_selected_bydomain_dict.pkl', "rb"))

RCA_topic_df_selected_all = pd.read_csv("RCA_topic_df_selected.csv.gz", compression="gzip") 
#RCA_topic_df_selected_bydomain_dict = pickle.load(open(f'RCA_topic_df_selected_bydomain_dict.pkl', "rb")) 
df_topics = pd.read_csv(f'df_topics.csv.gz', compression='gzip')
topic_id_name_dict = df_topics[['topic_id','topic_name']].set_index('topic_id').to_dict()['topic_name']
domain_id_name_dict = df_topics[['domain_id','domain_name']].drop_duplicates().set_index('domain_id').to_dict()['domain_name']
topics_embedding_reduced_df = pd.read_csv(f'topics_embedding_reduced_weighted_df.csv.zip').reset_index().rename(columns={'index':'topic_id_scaled'})
topics_set = list(topics_embedding_reduced_df.topic_id)
pos_topics = {row["topic_id"]: (row["feature_0"], row["feature_1"]) for _, row in topics_embedding_reduced_df.iterrows()}
pos_topics = {int(k): v for k, v in pos_topics.items()}
pos_topics = {node: (x, -y) for node, (x, y) in pos_topics.items()}
domain_partition = dict(zip(list(df_topics.topic_id),list(df_topics.domain_id)))
marker_styles = ['diamond', 'square', 'circle', 'pentagon']
G_nodes_only = nx.Graph()
G_nodes_only.add_nodes_from(list(df_topics.topic_id))
unique_comms = sorted(set(domain_partition.values()))
domain_base_colors = {
    1: (147,207,189),   
    2: (98,168,183),   
    3: (81,128,177),    
    4: (34,63,115),  
}
def blend_white_to_color(intensity, base_rgb):
    # intensity: float 0 to 1, base_rgb: tuple RGB 0-255
    # Blend white (255,255,255) and base color by intensity (0 = white, 1 = base color)
    # Non-linear scaling (sqrt) for better visibility
    intensity = intensity ** 0.5
    r = 255 - intensity * (255 - base_rgb[0])
    g = 255 - intensity * (255 - base_rgb[1])
    b = 255 - intensity * (255 - base_rgb[2])
    return f'rgb({int(r)}, {int(g)}, {int(b)})'

institutions_impact_weighted_selected_all = pd.read_csv("institutions_impact_weighted_selected.csv.gz", compression="gzip")
institutions_impact_weighted_selected_bydomain_dict = pickle.load(open(f'institutions_impact_weighted_selected_bydomain_dict.pkl', "rb"))

domain_color_map = {
    "Health Sciences": "rgba(34,63,115,1)",
    "Life Sciences": "rgba(147,207,189,1)",
    "Physical Sciences": "rgba(81,128,177,1)",
    "Social Sciences": "rgba(98,168,183,1)"
}

## default all domains
RCA_df_selected, entropy_df_selected = RCA_df_selected_all, entropy_df_selected_all
entropy_min, entropy_max = entropy_df_selected.disorder_index.min(),entropy_df_selected.disorder_index.max()
[G, pos, node_labels, community_labels_dict, community_colors_dict] = [G_all, pos_all, node_labels_all, community_labels_dict_all, community_colors_dict_all]
edges_df_selected, institution_peers_dict = edges_df_selected_all, institution_peers_dict_all
institutions_impact_weighted_selected = institutions_impact_weighted_selected_all
institutions_impact_weighted_selected['institution_name'] = institutions_impact_weighted_selected['institution_id'].map(dict_institution_id_name_selected)
institutions_stats_selected = institutions_stats_selected_all
RCA_topic_df_selected = RCA_topic_df_selected_all

# ----------------------------
# CENTERED TITLE
# ----------------------------
st.markdown(
    "<h1 style='text-align: center; color: #000066; margin-top: 0;'>A2A - Apples to Apples: Benchmarking among equals</h1>",
    unsafe_allow_html=True
)

# ----------------------------
# BIGGER CURTAIN
# ----------------------------
st.markdown("""
    <style>
    div[data-baseweb="select"] > div {
        font-size: 22px !important;
        height: 50px;
    }
    </style>
""", unsafe_allow_html=True)

institution_name = st.selectbox(
    "Select an Institution",
    options=[""] + institutions_selected,
    format_func=lambda x: "Select..." if x == "" else x,
)

# ----------------------------
# SHOW PLOT ONLY WHEN NO SELECTION
# ----------------------------
if institution_name == "":
    fig = institutions_map_fun(G, pos, node_labels, community_labels_dict, community_colors_dict, institution_peers_dict, highlight_node=None)
    col1, col2, col3 = st.columns([1.3, 2, 1]) ## center
    with col2:
        st.plotly_chart(fig, use_container_width=False)
else:

    institution_id = dict_institution_name_id_selected[institution_name]
    institution_id_scaled2 = dict_institution_id_institution_id_scaled2_selected[institution_id]

    info_row = institutions_info_df_selected[institutions_info_df_selected.institution_id==institution_id]
    #stats_row = institutions_stats_periods_selected[institutions_stats_periods_selected.institution_id==institution_id]
    stats_row = institutions_stats_selected[institutions_stats_selected.institution_id==institution_id]
    relationships_row = institutions_relationships_df_selected[institutions_relationships_df_selected.institution_id==institution_id]
    edges_df_row = edges_df_selected[edges_df_selected.institution_id==institution_id]
    peers_df_row = edges_df_row[['institution_id_neighbor','institution_name_neighbor','similarity_score']].sort_values(by='similarity_score',ascending=False).head(20).copy().sort_values('similarity_score', ascending=False)

    RCA_df_row = RCA_df_selected[(RCA_df_selected.institution_id==institution_id) & (RCA_df_selected.period_id==3)]
    entropy_df_row = entropy_df_selected[entropy_df_selected.institution_id==institution_id]
    RCA_topic_row = RCA_topic_df_selected[RCA_topic_df_selected.institution_id==institution_id]
    impact_row = institutions_impact_weighted_selected[institutions_impact_weighted_selected.institution_id.isin(set(peers_df_row.institution_id_neighbor).union({institution_id}))]

    ## name
    st.markdown(
        f"<h2 style='text-align: center; font-size: 28px; color: black; margin-bottom: 10px;'>{institution_name}</h2>",
        unsafe_allow_html=True
    )

    # if not relationships_row.empty:
    stats_row_current = stats_row[stats_row.year==2024]
    if not stats_row_current.empty:
        n_works = int(stats_row_current.iloc[0]['n_works'])
        n_authors = int(stats_row_current.iloc[0]['n_authors'])
    
    col1, col2, col3 = st.columns([0.6, 0.1, 0.8])  # adjust widths as needed
    
    with col1:
        ## map
        if not info_row.empty:
            lat = info_row.iloc[0]['latitude']
            lon = info_row.iloc[0]['longitude']

            if pd.notnull(lat) and pd.notnull(lon):
                map_df = pd.DataFrame({
                    'lat': [lat],
                    'lon': [lon]
                })
                st.map(map_df, color='#000066')

    with col3:

        # if not info_row.empty:
        #     type = info_row.iloc[0]['type'] 
        #     if not pd.isna(type):
        #         st.markdown(f"""
        #         <div style="
        #             padding: 20px;
        #             border-radius: 10px;
        #             background-color: #000066;
        #             text-align: center;
        #             display: flex;
        #             flex-direction: column;
        #             justify-content: center;
        #             align-items: center;
        #             min-height: 120px;
        #             margin-bottom: 20px;
        #         ">
        #             <h4 style="color: white; margin: 0 0 10px 0; font-size: 20px;">Type</h4>
        #             <p style="color: white; font-size: 36px; margin: 0; font-weight: bold;">{type}</p>
        #         </div>
        #         """, unsafe_allow_html=True)
        if not info_row.empty:
            research_level = info_row.iloc[0]['research_level'] 
            if not pd.isna(research_level):
                st.markdown(f"""
                <div style="
                    padding: 20px;
                    border-radius: 10px;
                    background-color: #000066;
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 120px;
                    margin-bottom: 20px;
                ">
                    <h4 style="color: white; margin: 0 0 10px 0; font-size: 20px;">Research Level</h4>
                    <p style="color: white; font-size: 36px; margin: 0; font-weight: bold;">{research_level}</p>
                </div>
                """, unsafe_allow_html=True)

        # Works and Authors cards
        if not stats_row_current.empty:
            st.markdown(f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                <div style="
                    padding: 30px 20px;
                    border-radius: 10px;
                    background-color: #000066;
                    flex: 1;
                    text-align: center;
                ">
                    <h4 style="color: white; margin: 0 auto 15px auto; font-size: 20px; display: block;">Works</h4>
                    <p style="color: white; font-size: 36px; margin: 0 auto; font-weight: bold; line-height: 1; display: block;">{n_works}</p>
                </div>
                <div style="
                    padding: 30px 20px;
                    border-radius: 10px;
                    background-color: #000066;
                    flex: 1;
                    text-align: center;
                ">
                    <h4 style="color: white; margin: 0 auto 15px auto; font-size: 20px; display: block;">Authors</h4>
                    <p style="color: white; font-size: 36px; margin: 0 auto; font-weight: bold; line-height: 1; display: block;">{n_authors}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        ## aggregation
        if not relationships_row.empty:
            children_list = list(relationships_row['child'].map(dict_institution_id_name))
            children_list.sort()
            st.markdown(f"<p style='font-size: 18px; font-weight: bold; margin-bottom: 10px;'>Child Institutions</p>", unsafe_allow_html=True)
            
            # If more than 6 children, display in two columns
            if len(children_list) > 6:
                # Split the list in half
                mid = (len(children_list) + 1) // 2
                left_children = children_list[:mid]
                right_children = children_list[mid:]
                
                # Create two-column layout using Streamlit columns
                col_child1, col_child2 = st.columns(2)
                
                with col_child1:
                    for child in left_children:
                        st.markdown(f"<div style='font-size: 16px; margin-left: 20px; margin-bottom: 5px;'>• {child}</div>", unsafe_allow_html=True)
                
                with col_child2:
                    for child in right_children:
                        st.markdown(f"<div style='font-size: 16px; margin-left: 20px; margin-bottom: 5px;'>• {child}</div>", unsafe_allow_html=True)
            else:
                # Display in single column if 6 or fewer
                for child in children_list:
                    st.markdown(f"<div style='font-size: 16px; margin-left: 20px; margin-bottom: 5px;'>• {child}</div>", unsafe_allow_html=True)


    # Create the selection dropdown
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    view_option = st.selectbox(
        "Select a domain",
        options=["All", "Health Sciences", "Life Sciences", "Physical Sciences", "Social Sciences"],
        index=0  # Default to "All"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if view_option != 'All':
        if view_option == "Life Sciences":
            d = 0
        elif view_option == "Social Sciences":
            d = 1
        elif view_option == "Physical Sciences":
            d = 2
        elif view_option == "Health Sciences":
            d = 3
        institutions_stats_selected = institutions_stats_selected_bydomain_dict[d]
        stats_row = institutions_stats_selected[institutions_stats_selected.institution_id==institution_id]
        RCA_df_selected, entropy_df_selected = RCA_df_selected_bydomain_dict[d], entropy_df_selected_bydomain_dict[d]
        RCA_df_row = RCA_df_selected[(RCA_df_selected.institution_id==institution_id) & (RCA_df_selected.period_id==3)]
        entropy_df_row = entropy_df_selected[entropy_df_selected.institution_id==institution_id]
        entropy_min, entropy_max = entropy_df_selected.disorder_index.min(),entropy_df_selected.disorder_index.max()
        [G, pos, node_labels, community_labels_dict, community_colors_dict] = network_data_bydomain_dict[d]
        edges_df_selected, institution_peers_dict = edges_df_selected_bydomain_dict[d], institution_peers_dict_bydomain_dict[d]
        edges_df_selected['institution_name_neighbor'] = edges_df_selected['institution_id_neighbor'].map(dict_institution_id_name_selected)
        edges_df_selected['institution_id_scaled2'] = edges_df_selected['institution_id'].map(dict_institution_id_institution_id_scaled2_selected)
        edges_df_selected['institution_id_scaled2_neighbor'] = edges_df_selected['institution_id_neighbor'].map(dict_institution_id_institution_id_scaled2_selected)
        edges_df_row = edges_df_selected[edges_df_selected.institution_id==institution_id]
        peers_df_row = edges_df_row[['institution_id_neighbor','institution_name_neighbor','similarity_score']].sort_values(by='similarity_score',ascending=False).head(20).copy().sort_values('similarity_score', ascending=False)
        institutions_impact_weighted_selected = institutions_impact_weighted_selected_bydomain_dict[d]
        institutions_impact_weighted_selected['institution_name'] = institutions_impact_weighted_selected['institution_id'].map(dict_institution_id_name_selected)
        impact_row = institutions_impact_weighted_selected[institutions_impact_weighted_selected.institution_id.isin(set(peers_df_row.institution_id_neighbor).union({institution_id}))]
        #RCA_topic_df_selected = RCA_topic_df_selected_bydomain_dict[d]
        RCA_topic_df_selected = RCA_topic_df_selected_all
        RCA_topic_df_selected['value'] = (RCA_topic_df_selected.groupby(['institution_id','domain_id_scaled'])['count_specialized_topic'].transform(lambda x: x / x.max()))*100
        RCA_topic_df_selected.loc[RCA_topic_df_selected.domain_id_scaled!=d,'value'] = 0.0
        RCA_topic_row = RCA_topic_df_selected[RCA_topic_df_selected.institution_id==institution_id]
    else:
        institutions_stats_selected = institutions_stats_selected_all
        stats_row = institutions_stats_selected[institutions_stats_selected.institution_id==institution_id]
        RCA_df_selected, entropy_df_selected = RCA_df_selected_all, entropy_df_selected_all
        RCA_df_row = RCA_df_selected[(RCA_df_selected.institution_id==institution_id) & (RCA_df_selected.period_id==3)]
        entropy_df_row = entropy_df_selected[entropy_df_selected.institution_id==institution_id]
        entropy_min, entropy_max = entropy_df_selected.disorder_index.min(),entropy_df_selected.disorder_index.max()
        [G, pos, node_labels, community_labels_dict, community_colors_dict] = [G_all, pos_all, node_labels_all, community_labels_dict_all, community_colors_dict_all]
        edges_df_selected, institution_peers_dict = edges_df_selected_all, institution_peers_dict_all
        edges_df_selected['institution_name_neighbor'] = edges_df_selected['institution_id_neighbor'].map(dict_institution_id_name_selected)
        edges_df_selected['institution_id_scaled2'] = edges_df_selected['institution_id'].map(dict_institution_id_institution_id_scaled2_selected)
        edges_df_selected['institution_id_scaled2_neighbor'] = edges_df_selected['institution_id_neighbor'].map(dict_institution_id_institution_id_scaled2_selected)
        edges_df_row = edges_df_selected[edges_df_selected.institution_id==institution_id]
        peers_df_row = edges_df_row[['institution_id_neighbor','institution_name_neighbor','similarity_score']].sort_values(by='similarity_score',ascending=False).head(20).copy().sort_values('similarity_score', ascending=False)
        institutions_impact_weighted_selected = institutions_impact_weighted_selected_all
        institutions_impact_weighted_selected['institution_name'] = institutions_impact_weighted_selected['institution_id'].map(dict_institution_id_name_selected)
        impact_row = institutions_impact_weighted_selected[institutions_impact_weighted_selected.institution_id.isin(set(peers_df_row.institution_id_neighbor).union({institution_id}))]
        RCA_topic_df_selected = RCA_topic_df_selected_all
        RCA_topic_row = RCA_topic_df_selected[RCA_topic_df_selected.institution_id==institution_id]

    # Network visualization section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1_map, col2_map, col3_map = st.columns([0.8, 0.1, 0.8])
    
    with col3_map:
        fig = institutions_map_fun(G, pos, node_labels, community_labels_dict, community_colors_dict, institution_peers_dict, highlight_node=institution_id_scaled2)
        st.plotly_chart(fig, use_container_width=False)
    with col1_map:
        if not edges_df_row.empty:
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Peers</p>", unsafe_allow_html=True)

        # Create horizontal bar chart
        fig_similarity = go.Figure()
        institutions = peers_df_row['institution_name_neighbor'].tolist()
        scores = peers_df_row['similarity_score'].tolist()

        # Create color gradient based on scores (normalize to 0-1 for opacity)
        max_score = max(scores) if scores else 1
        #colors = [f'rgba(0, 0, 255, {score/max_score})' for score in scores]

        fig_similarity.add_trace(go.Bar(
            y=institutions,
            x=scores,
            orientation='h',
            marker=dict(
                color='#000066', #colors,
                line=dict(color='#000066', width=1)
            ),
            text=[f'{score:.2f}' for score in scores],
            textposition='auto',
            textfont=dict(color='white', size=15, family='Arial Black'),
            hovertemplate='<b>%{y}</b><br>Similarity: %{x:.3f}<extra></extra>',
            hoverlabel=dict(
                bgcolor='#000066',           # Blue background
                font_size=14,            # Optional: adjust font size
                font_color='white'       # Optional: white text for contrast
            )
        ))

        fig_similarity.update_layout(
            height=max(500, len(institutions) * 30),
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                title='Similarity Score',
                title_font=dict(size=16, color='black'),
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(size=16, color='black'),
            ),
            yaxis=dict(
                title='',
                autorange='reversed',
                tickfont=dict(size=16, color='black'),
            ),
            font=dict(size=10)
        )

        st.plotly_chart(fig_similarity, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    entropy_df_row_current = entropy_df_row[entropy_df_row.period_id==3]
    if not entropy_df_row_current.empty:
        entropy = entropy_df_row_current.iloc[0]['disorder_index']
        st.markdown(f"""
            <div style="
                padding: 20px;
                border-radius: 10px;
                background-color: #000066;
                text-align: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 120px;
                margin-bottom: 20px;
            ">
                <h4 style="color: white; margin: 0 0 10px 0; font-size: 20px;">Disorder Index</h4>
                <p style="color: white; font-size: 36px; margin: 0; font-weight: bold;">{entropy:.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    if not RCA_df_row.empty:
        st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Portfolio Composition</p>", unsafe_allow_html=True)
        fig = px.bar(
            RCA_df_row,
            x='field_name',
            y='portfolio_composition',
            color='domain_name',
            labels={
                'field_name': '',
                'portfolio_composition': '',
                'domain_name': 'Domain'
            },
            color_discrete_map=domain_color_map
            # color_discrete_sequence=[
            #     "rgba(147,207,189,1)",
            #     "rgba(98,168,183,1)",
            #     "rgba(81,128,177,1)",
            #     "rgba(34,63,115,1)"
            # ]
        )

        # Update each trace to have hoverlabel matching its bar color and custom text
        for trace in fig.data:
            trace.hoverlabel = dict(
                bgcolor=trace.marker.color,
                font_size=14,
                font_color='white'
            )
            trace.hovertemplate = '<b>%{fullData.name}</b><br>%{x}<br>%{y:.2f}<extra></extra>'

        fig.update_layout(
            height=600,
            xaxis_tickangle=-45,
            xaxis=dict(
                tickfont=dict(size=16,color='black'),
                showgrid=False,
            ),
            yaxis=dict(
                tickfont=dict(size=16,color='black'),
                title_font=dict(size=18,color='black'),
                showgrid=False,
            ),
            legend=dict(
                font=dict(size=16,color='black'),
                title_font=dict(size=18,color='black')
            ),
            font=dict(size=14)
        )

        st.plotly_chart(fig, use_container_width=True)


        ## embedding
        if (not RCA_topic_row.empty): # and (view_option == 'All'):
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Topic Space</p>", unsafe_allow_html=True)
            fig_topics = topics_embedding_fun(RCA_topic_row,topics_embedding_reduced_df,topics_set,pos_topics,unique_comms,domain_partition,domain_id_name_dict,domain_base_colors,marker_styles)
            col1, col2, col3 = st.columns([1, 5, 1])
            with col2:
                st.plotly_chart(fig_topics, use_container_width=True)

        ## impact
        if not impact_row.empty:
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Relative Impact</p>", unsafe_allow_html=True)
            impact_row['rank_relative_impact'] = impact_row.groupby('year')['relative_impact'].rank(ascending=False).astype(int)
            impact_row = impact_row.sort_values(by=['year','rank_relative_impact'])
            fig_rank = line_rank_fun(impact_row,institution_name)
            st.plotly_chart(fig_rank, use_container_width=False)
        st.markdown("<br>", unsafe_allow_html=True)
        if not impact_row.empty:
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Relative Impact vs Impact Uniformity</p>", unsafe_allow_html=True)
            fig_jitter = jitter_impact_fun(impact_row[impact_row.year.isin({2014,2016,2018,2020,2022,2024})],institution_name)
            st.plotly_chart(fig_jitter, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ## in time
        st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Historical data</p>", unsafe_allow_html=True)
        col1_time, col2_time, col3_time = st.columns([1, 1, 1])  # adjust widths as needed
        with col1_time:
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Works</p>", unsafe_allow_html=True)
            works_max = stats_row['n_works'].max()
            fig_time1 = plot_time_fun(stats_row,'year','n_works',0,works_max)
            st.plotly_chart(fig_time1, use_container_width=False)
        with col2_time:
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Authors</p>", unsafe_allow_html=True)
            authors_max = stats_row['n_authors'].max()
            fig_time1 = plot_time_fun(stats_row,'year','n_authors',0,authors_max)
            st.plotly_chart(fig_time1, use_container_width=False)
        with col3_time:
            st.markdown("<p style='font-size: 22px;text-align: center; font-weight: bold; margin-bottom: 10px; margin-top: 20px;'>Disorder Index</p>", unsafe_allow_html=True)
            fig_time1 = plot_time_fun(entropy_df_row,'period_id','disorder_index',entropy_min, entropy_max)
            st.plotly_chart(fig_time1, use_container_width=False)                