"""
Export all Data/ files (pkl + csv.gz) into Data_Tables/ as readable CSVs.
Only keeps columns actually used by the dashboard.

Usage:
    python export_tables.py
"""

import os
import pickle
import pandas as pd

DATA_ROOT = os.path.join(os.path.dirname(__file__), 'Data')
OUT_ROOT  = os.path.join(os.path.dirname(__file__), 'Data_Tables')
EDGE_TYPE = 'geom2'

# ---------------------------------------------------------------------------
# Columns actually used by the app (traced from app.py, charts.py, resolver.py)
# ---------------------------------------------------------------------------
INFO_COLS = [
    'institution_id', 'institution_name', 'country_name',
    'latitude', 'longitude', 'research_level',
]
TOPICS_COLS = [
    'topic_id', 'topic_name', 'field_name', 'field_id_scaled',
    'domain_id', 'domain_name', 'domain_id_scaled',
]
STATS_COLS = ['year', 'institution_id', 'n_works', 'n_authors']
ENTROPY_COLS = ['institution_id', 'period_id', 'disorder_index']
IMPACT_COLS = ['institution_id', 'year', 'relative_impact', 'impact_uniformity']
EDGES_COLS = ['similarity_score', 'institution_id_scaled2', 'institution_id_scaled2_neighbor']
RCA_COLS = [
    'period_id', 'institution_id', 'field_id_scaled',
    'domain_id', 'portfolio_composition', 'field_name', 'domain_name',
]
RCA_TOPIC_COLS = [
    'count_specialized_topic', 'institution_id', 'topic_id',
    'domain_id_scaled', 'field_id_scaled',
]
EMBED_COLS = ['topic_id', 'feature_0', 'feature_1']


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f'  -> {path}  ({len(df)} rows, {len(df.columns)} cols)')


def keep(df, cols):
    """Keep only listed columns that exist in df."""
    return df[[c for c in cols if c in df.columns]]


def export_root_files(out_dir):
    """Root-level CSV/pkl files."""
    ensure_dir(out_dir)

    # institutions_info
    info = pd.read_csv(os.path.join(DATA_ROOT, 'institutions_info_df_selected.csv.gz'), compression='gzip')
    save_csv(keep(info, INFO_COLS), os.path.join(out_dir, 'institutions_info.csv'))

    # relationships  (add child_name from id_name dict)
    rels = pd.read_csv(os.path.join(DATA_ROOT, 'institutions_relationships_df_selected.csv.gz'), compression='gzip')
    id_name = pickle.load(open(os.path.join(DATA_ROOT, 'dict_institution_id_name.pkl'), 'rb'))
    rels['child_name'] = rels['child'].map(id_name)
    save_csv(rels[['institution_id', 'child', 'child_name']], os.path.join(out_dir, 'institutions_relationships.csv'))

    # topics
    topics = pd.read_csv(os.path.join(DATA_ROOT, 'df_topics.csv.gz'), compression='gzip')
    save_csv(keep(topics, TOPICS_COLS), os.path.join(out_dir, 'topics.csv'))

    # id→name lookup
    df = pd.DataFrame(list(id_name.items()), columns=['institution_id', 'institution_name'])
    save_csv(df, os.path.join(out_dir, 'institution_id_name.csv'))


def export_all(out_dir):
    """Data/All/ — single DataFrames + one-level dicts."""
    ensure_dir(out_dir)

    # RCA
    df = pd.read_csv(os.path.join(DATA_ROOT, 'All', 'RCA_df_selected.csv.gz'), compression='gzip')
    save_csv(keep(df, RCA_COLS), os.path.join(out_dir, 'RCA.csv'))

    # Stats
    df = pd.read_csv(os.path.join(DATA_ROOT, 'All', 'institutions_stats_selected.csv.gz'), compression='gzip')
    save_csv(keep(df, STATS_COLS), os.path.join(out_dir, 'stats.csv'))

    # Entropy
    df = pd.read_csv(os.path.join(DATA_ROOT, 'All', 'entropy_df_selected.csv.gz'), compression='gzip')
    save_csv(keep(df, ENTROPY_COLS), os.path.join(out_dir, 'entropy.csv'))

    # Impact
    df = pd.read_csv(os.path.join(DATA_ROOT, 'All', 'institutions_impact_rev_selected.csv.gz'), compression='gzip')
    save_csv(keep(df, IMPACT_COLS), os.path.join(out_dir, 'impact.csv'))

    # Edges (only columns used by resolver)
    edges_dict = pickle.load(open(os.path.join(DATA_ROOT, 'All', 'edges_df_selected_dict.pkl'), 'rb'))
    save_csv(keep(edges_dict[EDGE_TYPE], EDGES_COLS), os.path.join(out_dir, 'edges.csv'))

    # Peers
    peers_dict = pickle.load(open(os.path.join(DATA_ROOT, 'All', 'institution_peers_selected_dict.pkl'), 'rb'))
    peers = peers_dict[EDGE_TYPE]
    rows = [{'institution_id_scaled2': k, 'peer_id_scaled2': p}
            for k, pset in peers.items() for p in sorted(pset)]
    save_csv(pd.DataFrame(rows), os.path.join(out_dir, 'peers.csv'))


def export_by_key(level, subdir, out_dir):
    """Data/Domain/ or Data/Field/ — dicts keyed by domain/field id."""
    ensure_dir(out_dir)

    key_label = 'domain_id_scaled' if level == 'Domain' else 'field_id_scaled'

    file_col_map = {
        'RCA':     (f'RCA_df_selected_by{level.lower()}_dict.pkl',                    RCA_COLS),
        'stats':   (f'institutions_stats_selected_by{level.lower()}_dict.pkl',         STATS_COLS),
        'entropy': (f'entropy_df_selected_by{level.lower()}_dict.pkl',                 ENTROPY_COLS),
        'impact':  (f'institutions_impact_rev_selected_by{level.lower()}_dict.pkl',    IMPACT_COLS),
    }
    for label, (fname, cols) in file_col_map.items():
        d = pickle.load(open(os.path.join(DATA_ROOT, subdir, fname), 'rb'))
        frames = []
        for key, df in d.items():
            df = keep(df, cols).copy()
            df[key_label] = key
            frames.append(df)
        save_csv(pd.concat(frames, ignore_index=True), os.path.join(out_dir, f'{label}.csv'))

    # Edges
    edges_all = pickle.load(open(os.path.join(DATA_ROOT, subdir,
                                              f'edges_df_selected_by{level.lower()}_dict.pkl'), 'rb'))
    edges = edges_all[EDGE_TYPE]
    frames = []
    for key, df in edges.items():
        df = keep(df, EDGES_COLS).copy()
        df[key_label] = key
        frames.append(df)
    save_csv(pd.concat(frames, ignore_index=True), os.path.join(out_dir, 'edges.csv'))

    # Peers
    peers_all = pickle.load(open(os.path.join(DATA_ROOT, subdir,
                                              f'institution_peers_selected_by{level.lower()}_dict.pkl'), 'rb'))
    peers = peers_all[EDGE_TYPE]
    rows = []
    for key, inst_dict in peers.items():
        for inst_id, pset in inst_dict.items():
            for p in sorted(pset):
                rows.append({key_label: key, 'institution_id_scaled2': inst_id, 'peer_id_scaled2': p})
    save_csv(pd.DataFrame(rows), os.path.join(out_dir, 'peers.csv'))


def export_topic(out_dir):
    """Data/Topic/ — CSV files."""
    ensure_dir(out_dir)

    df = pd.read_csv(os.path.join(DATA_ROOT, 'Topic', 'RCA_topic_df_selected.csv.gz'), compression='gzip')
    save_csv(keep(df, RCA_TOPIC_COLS), os.path.join(out_dir, 'RCA_topic.csv'))

    df = pd.read_csv(os.path.join(DATA_ROOT, 'Topic', 'topics_embedding_reduced_weighted_df.csv.zip'))
    save_csv(keep(df, EMBED_COLS), os.path.join(out_dir, 'topics_embedding.csv'))


def main():
    print('Exporting root files...')
    export_root_files(OUT_ROOT)

    print('\nExporting All...')
    export_all(os.path.join(OUT_ROOT, 'All'))

    print('\nExporting Domain...')
    export_by_key('Domain', 'Domain', os.path.join(OUT_ROOT, 'Domain'))

    print('\nExporting Field...')
    export_by_key('Field', 'Field', os.path.join(OUT_ROOT, 'Field'))

    print('\nExporting Topic...')
    export_topic(os.path.join(OUT_ROOT, 'Topic'))

    print('\nDone! All tables saved to Data_Tables/')


if __name__ == '__main__':
    main()
