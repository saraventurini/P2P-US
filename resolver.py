"""
resolver.py — Granularity switcher.

get_slice() returns a uniform dict of DataFrames for the selected institution
and granularity context. All downstream charts receive the same structure
regardless of whether we are at All / Domain / Field level.
"""

import pandas as pd
from data_loader import load_all, load_domain, load_field


def _resolve_peers_with_scores(peer_scaled_set, edges_df, focal_scaled_id, info_df, scaled_to_real, top_n=20):
    """
    Convert a set of peer scaled IDs → DataFrame(institution_id, institution_name, similarity_score).
    Joins with the edges DataFrame to get similarity scores.
    """
    if not peer_scaled_set or edges_df is None or edges_df.empty:
        return pd.DataFrame(columns=['institution_id', 'institution_name', 'similarity_score'])

    focal_edges = edges_df[edges_df['institution_id_scaled2'] == focal_scaled_id].copy()
    focal_edges = focal_edges[focal_edges['institution_id_scaled2_neighbor'].isin(peer_scaled_set)]
    focal_edges = focal_edges.sort_values('similarity_score', ascending=False).head(top_n)

    focal_edges = focal_edges.copy()
    focal_edges['peer_institution_id'] = focal_edges['institution_id_scaled2_neighbor'].map(scaled_to_real)
    name_map = dict(zip(info_df['institution_id'], info_df['institution_name']))
    focal_edges['institution_name'] = focal_edges['peer_institution_id'].map(name_map).fillna(
        focal_edges['peer_institution_id'].astype(str)
    )
    result = focal_edges[['peer_institution_id', 'institution_name', 'similarity_score']].copy()
    result = result.rename(columns={'peer_institution_id': 'institution_id'})
    return result.reset_index(drop=True)


def get_slice(
    granularity,
    domain_id_scaled,
    field_id_scaled,
    institution_id,
    institution_id_scaled,
    scaled_to_real,
    info_df,
):
    """
    Returns a unified dict with keys:
      rca, peers (DataFrame), entropy, impact, stats, stats_periods,
      peers_scaled_set (set of ints), edges (DataFrame)

    granularity: 'All' | 'Domain' | 'Field'
    domain_id_scaled: int (0–3), only used when granularity='Domain'
    field_id_scaled:  int,        only used when granularity='Field'
    """
    if granularity == 'All':
        d = load_all()
        rca          = d['rca'][d['rca']['institution_id'] == institution_id]
        peers_scaled = d['peers'].get(institution_id_scaled, set())
        edges        = d['edges']
        entropy      = d['entropy'][d['entropy']['institution_id'] == institution_id]
        impact       = d['impact'][d['impact']['institution_id'] == institution_id]
        stats        = d['stats'][d['stats']['institution_id'] == institution_id]
        stats_periods = d['stats_periods'][d['stats_periods']['institution_id'] == institution_id]

    elif granularity == 'Domain':
        d = load_domain()
        key = domain_id_scaled
        rca_dict   = d['rca'].get(key, pd.DataFrame())
        rca        = rca_dict[rca_dict['institution_id'] == institution_id] if not isinstance(rca_dict, pd.DataFrame) or not rca_dict.empty else rca_dict
        # peers: dict[domain_id_scaled][inst_scaled] → set
        peers_scaled = d['peers'].get(key, {}).get(institution_id_scaled, set())
        edges        = d['edges'].get(key, pd.DataFrame())
        entropy_d    = d['entropy'].get(key, pd.DataFrame())
        entropy      = entropy_d[entropy_d['institution_id'] == institution_id] if not entropy_d.empty else entropy_d
        impact_d     = d['impact'].get(key, pd.DataFrame())
        impact       = impact_d[impact_d['institution_id'] == institution_id] if not impact_d.empty else impact_d
        stats_d      = d['stats'].get(key, pd.DataFrame())
        stats        = stats_d[stats_d['institution_id'] == institution_id] if not stats_d.empty else stats_d
        stats_p_d    = d['stats_periods'].get(key, pd.DataFrame())
        stats_periods = stats_p_d[stats_p_d['institution_id'] == institution_id] if not stats_p_d.empty else stats_p_d

    elif granularity == 'Field':
        d = load_field()
        key = field_id_scaled
        rca_dict   = d['rca'].get(key, pd.DataFrame())
        rca        = rca_dict[rca_dict['institution_id'] == institution_id] if not isinstance(rca_dict, pd.DataFrame) or not rca_dict.empty else rca_dict
        peers_scaled = d['peers'].get(key, {}).get(institution_id_scaled, set())
        edges        = d['edges'].get(key, pd.DataFrame())
        entropy_d    = d['entropy'].get(key, pd.DataFrame())
        entropy      = entropy_d[entropy_d['institution_id'] == institution_id] if not entropy_d.empty else entropy_d
        impact_d     = d['impact'].get(key, pd.DataFrame())
        impact       = impact_d[impact_d['institution_id'] == institution_id] if not impact_d.empty else impact_d
        stats_d      = d['stats'].get(key, pd.DataFrame())
        stats        = stats_d[stats_d['institution_id'] == institution_id] if not stats_d.empty else stats_d
        stats_p_d    = d['stats_periods'].get(key, pd.DataFrame())
        stats_periods = stats_p_d[stats_p_d['institution_id'] == institution_id] if not stats_p_d.empty else stats_p_d
    else:
        raise ValueError(f"Unknown granularity: {granularity}")

    peer_df = _resolve_peers_with_scores(
        peers_scaled, edges, institution_id_scaled, info_df, scaled_to_real
    )

    return {
        'rca':            rca.reset_index(drop=True) if hasattr(rca, 'reset_index') else rca,
        'peers':          peer_df,
        'entropy':        entropy.reset_index(drop=True) if hasattr(entropy, 'reset_index') else entropy,
        'impact':         impact.reset_index(drop=True) if hasattr(impact, 'reset_index') else impact,
        'stats':          stats.reset_index(drop=True) if hasattr(stats, 'reset_index') else stats,
        'stats_periods':  stats_periods.reset_index(drop=True) if hasattr(stats_periods, 'reset_index') else stats_periods,
        'peers_scaled':   peers_scaled,
        'edges':          edges,
    }


def get_peer_real_ids(peers_scaled_set, scaled_to_real):
    """Convert a set of scaled IDs to a list of real institution IDs."""
    return [scaled_to_real[s] for s in peers_scaled_set if s in scaled_to_real]
