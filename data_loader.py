import os
import pandas as pd
import streamlit as st
from config import ALL_PATH, DOMAIN_PATH, FIELD_PATH, TOPIC_PATH, DATA_ROOT


@st.cache_resource(show_spinner=False)
def load_base():
    """Load small root-level files."""
    info_df = pd.read_csv(os.path.join(DATA_ROOT, 'institutions_info.csv'))
    relationships_df = pd.read_csv(os.path.join(DATA_ROOT, 'institutions_relationships.csv'))
    topics_df = pd.read_csv(os.path.join(DATA_ROOT, 'topics.csv'))

    id_name_df = pd.read_csv(os.path.join(DATA_ROOT, 'institution_id_name.csv'))
    id_name_dict = dict(zip(id_name_df['institution_id'], id_name_df['institution_name']))

    embed_df = pd.read_csv(os.path.join(TOPIC_PATH, 'topics_embedding.csv'))

    return info_df, relationships_df, topics_df, id_name_dict, embed_df


@st.cache_resource(show_spinner=False)
def load_all():
    """Load All-granularity data."""
    rca     = pd.read_csv(os.path.join(ALL_PATH, 'RCA.csv'))
    stats   = pd.read_csv(os.path.join(ALL_PATH, 'stats.csv'))
    entropy = pd.read_csv(os.path.join(ALL_PATH, 'entropy.csv'))
    impact  = pd.read_csv(os.path.join(ALL_PATH, 'impact.csv'))
    edges   = pd.read_csv(os.path.join(ALL_PATH, 'edges.csv'))

    peers_df = pd.read_csv(os.path.join(ALL_PATH, 'peers.csv'))
    peers = {
        int(inst): set(grp['peer_id_scaled2'])
        for inst, grp in peers_df.groupby('institution_id_scaled2')
    }

    return {
        'rca': rca, 'stats': stats, 'entropy': entropy,
        'impact': impact, 'edges': edges, 'peers': peers,
    }


def _read_csv(path):
    """Read CSV, auto-detecting .gz compression."""
    if os.path.exists(path + '.gz'):
        return pd.read_csv(path + '.gz', compression='gzip')
    return pd.read_csv(path)


def _load_by_key(path, key_col):
    """Load Domain or Field level data, returning dicts keyed by domain/field id."""
    rca     = _read_csv(os.path.join(path, 'RCA.csv'))
    stats   = pd.read_csv(os.path.join(path, 'stats.csv'))
    entropy = pd.read_csv(os.path.join(path, 'entropy.csv'))
    impact  = pd.read_csv(os.path.join(path, 'impact.csv'))
    edges   = pd.read_csv(os.path.join(path, 'edges.csv'))
    peers_df = pd.read_csv(os.path.join(path, 'peers.csv'))

    def to_dict(df):
        return {
            int(k): grp.drop(columns=[key_col]).reset_index(drop=True)
            for k, grp in df.groupby(key_col)
        }

    # Peers: {key: {inst_scaled: set}}
    peers = {}
    for key, key_grp in peers_df.groupby(key_col):
        inst_dict = {}
        for inst, grp in key_grp.groupby('institution_id_scaled2'):
            inst_dict[int(inst)] = set(grp['peer_id_scaled2'].astype(int))
        peers[int(key)] = inst_dict

    return {
        'rca': to_dict(rca),
        'stats': to_dict(stats),
        'entropy': to_dict(entropy),
        'impact': to_dict(impact),
        'edges': to_dict(edges),
        'peers': peers,
    }


@st.cache_resource(show_spinner=False)
def load_domain():
    """Load Domain-granularity data."""
    return _load_by_key(DOMAIN_PATH, 'domain_id_scaled')


@st.cache_resource(show_spinner=False)
def load_field():
    """Load Field-granularity data."""
    return _load_by_key(FIELD_PATH, 'field_id_scaled')


@st.cache_resource(show_spinner=False)
def load_rca_topic():
    """Load full topic RCA."""
    return pd.read_csv(os.path.join(TOPIC_PATH, 'RCA_topic.csv.gz'), compression='gzip')


def build_scaled_maps(info_df):
    """
    institution_id_scaled2 = 0-based row index of institutions_info.
    Returns (scaled_to_real, real_to_scaled) dicts.
    """
    scaled_to_real = dict(enumerate(info_df['institution_id']))
    real_to_scaled = {v: k for k, v in scaled_to_real.items()}
    return scaled_to_real, real_to_scaled
