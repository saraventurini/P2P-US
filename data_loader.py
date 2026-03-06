import os
import pickle
import pandas as pd
import streamlit as st
from config import ALL_PATH, DOMAIN_PATH, FIELD_PATH, TOPIC_PATH, DATA_ROOT, EDGE_TYPE


@st.cache_resource(show_spinner=False)
def load_base():
    """Load small root-level files. ~5 MB. Always eager."""
    info_df = pd.read_csv(
        os.path.join(DATA_ROOT, 'institutions_info_df_selected.csv.gz'),
        compression='gzip',
    )
    relationships_df = pd.read_csv(
        os.path.join(DATA_ROOT, 'institutions_relationships_df_selected.csv.gz'),
        compression='gzip',
    )
    topics_df = pd.read_csv(
        os.path.join(DATA_ROOT, 'df_topics.csv.gz'),
        compression='gzip',
    )
    id_name_dict = pickle.load(
        open(os.path.join(DATA_ROOT, 'dict_institution_id_name.pkl'), 'rb')
    )
    relationships_df['child_name'] = relationships_df['child'].map(id_name_dict)
    embed_df = (
        pd.read_csv(os.path.join(TOPIC_PATH, 'topics_embedding_reduced_weighted_df.csv.zip'))
        .reset_index()
        .rename(columns={'index': 'topic_id_scaled'})
    )
    return info_df, relationships_df, topics_df, id_name_dict, embed_df


@st.cache_resource(show_spinner=False)
def load_all():
    """Load All-granularity data. ~10 MB. Always eager."""
    rca = pd.read_csv(os.path.join(ALL_PATH, 'RCA_df_selected.csv.gz'), compression='gzip')
    stats = pd.read_csv(os.path.join(ALL_PATH, 'institutions_stats_selected.csv.gz'), compression='gzip')
    stats_periods = pd.read_csv(os.path.join(ALL_PATH, 'institutions_stats_periods_selected.csv.gz'), compression='gzip')
    entropy = pd.read_csv(os.path.join(ALL_PATH, 'entropy_df_selected.csv.gz'), compression='gzip')
    impact = pd.read_csv(os.path.join(ALL_PATH, 'institutions_impact_rev_selected.csv.gz'), compression='gzip')
    edges_dict = pickle.load(open(os.path.join(ALL_PATH, 'edges_df_selected_dict.pkl'), 'rb'))
    edges = edges_dict[EDGE_TYPE]
    peers_dict = pickle.load(open(os.path.join(ALL_PATH, 'institution_peers_selected_dict.pkl'), 'rb'))
    peers = peers_dict[EDGE_TYPE]
    return {
        'rca': rca,
        'stats': stats,
        'stats_periods': stats_periods,
        'entropy': entropy,
        'impact': impact,
        'edges': edges,
        'peers': peers,
    }


@st.cache_resource(show_spinner=False)
def load_domain():
    """Load Domain-granularity data. ~25 MB. Lazy on first domain selection."""
    rca = pickle.load(open(os.path.join(DOMAIN_PATH, 'RCA_df_selected_bydomain_dict.pkl'), 'rb'))
    stats = pickle.load(open(os.path.join(DOMAIN_PATH, 'institutions_stats_selected_bydomain_dict.pkl'), 'rb'))
    stats_periods = pickle.load(open(os.path.join(DOMAIN_PATH, 'institutions_stats_periods_selected_bydomain_dict.pkl'), 'rb'))
    entropy = pickle.load(open(os.path.join(DOMAIN_PATH, 'entropy_df_selected_bydomain_dict.pkl'), 'rb'))
    impact = pickle.load(open(os.path.join(DOMAIN_PATH, 'institutions_impact_rev_selected_bydomain_dict.pkl'), 'rb'))
    edges_dict = pickle.load(open(os.path.join(DOMAIN_PATH, 'edges_df_selected_bydomain_dict.pkl'), 'rb'))
    edges = edges_dict[EDGE_TYPE]
    peers_dict = pickle.load(open(os.path.join(DOMAIN_PATH, 'institution_peers_selected_bydomain_dict.pkl'), 'rb'))
    peers = peers_dict[EDGE_TYPE]
    return {
        'rca': rca,
        'stats': stats,
        'stats_periods': stats_periods,
        'entropy': entropy,
        'impact': impact,
        'edges': edges,
        'peers': peers,
    }


@st.cache_resource(show_spinner=False)
def load_field():
    """Load Field-granularity data. ~180 MB. Lazy with spinner."""
    rca = pickle.load(open(os.path.join(FIELD_PATH, 'RCA_df_selected_byfield_dict.pkl'), 'rb'))
    stats = pickle.load(open(os.path.join(FIELD_PATH, 'institutions_stats_selected_byfield_dict.pkl'), 'rb'))
    stats_periods = pickle.load(open(os.path.join(FIELD_PATH, 'institutions_stats_periods_selected_byfield_dict.pkl'), 'rb'))
    entropy = pickle.load(open(os.path.join(FIELD_PATH, 'entropy_df_selected_byfield_dict.pkl'), 'rb'))
    impact = pickle.load(open(os.path.join(FIELD_PATH, 'institutions_impact_rev_selected_byfield_dict.pkl'), 'rb'))
    edges_dict = pickle.load(open(os.path.join(FIELD_PATH, 'edges_df_selected_byfield_dict.pkl'), 'rb'))
    edges = edges_dict[EDGE_TYPE]
    peers_dict = pickle.load(open(os.path.join(FIELD_PATH, 'institution_peers_selected_byfield_dict.pkl'), 'rb'))
    peers = peers_dict[EDGE_TYPE]
    return {
        'rca': rca,
        'stats': stats,
        'stats_periods': stats_periods,
        'entropy': entropy,
        'impact': impact,
        'edges': edges,
        'peers': peers,
    }


@st.cache_resource(show_spinner=False)
def load_rca_topic():
    """Load full topic RCA. 44 MB compressed. Filter per institution at render time."""
    return pd.read_csv(
        os.path.join(TOPIC_PATH, 'RCA_topic_df_selected.csv.gz'),
        compression='gzip',
    )


def build_scaled_maps(info_df):
    """
    institution_id_scaled2 = 0-based row index of institutions_info_df_selected.
    Returns (scaled_to_real, real_to_scaled) dicts.
    """
    scaled_to_real = dict(enumerate(info_df['institution_id']))
    real_to_scaled = {v: k for k, v in scaled_to_real.items()}
    return scaled_to_real, real_to_scaled
