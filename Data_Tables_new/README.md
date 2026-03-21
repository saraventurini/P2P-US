# Data Tables

Plain CSV files used by the P2P dashboard. Source: OpenAlex. Coverage: United States.

## Root files

| File | Description |
|---|---|
| `institutions_info.csv.gz` | 309 institutions with name, coordinates, country, research level, banchmark (boolean) |
| `institutions_relationships.csv.gz` | Parent-child relationships between institutions |
| `topics.csv.gz` | 4,516 research topics with field, domain, and scaled IDs |
| `institution_id_name.csv.gz` | Full OpenAlex 4117 institution (education type) IDs to names |

## All/

Aggregate data across all fields.

| File | Rows | Description |
|---|---|---|
| `RCA.csv.gz` | Portfolio composition (RCA) per institution, period, and field |
| `stats.csv.gz` | Yearly publication and author counts per institution |
| `entropy.csv.gz` | Disorder index per institution and period |
| `impact.csv.gz` | Average, standard deviation and median FWCI per institution and year (to calculate Relative impact and impact |uniformity)
| `grants.csv.gz` | Funding amount won from NSF and NIH per institution and year |
| `edges.csv.gz` | Similarity scores between institution pairs (geom2 edge type) |
| `peers.csv.gz` | Peer assignments: which institutions are peers of which |

## Domain/

Same structure as `All/`, split by domain (4 domains: Life Sciences, Social Sciences, Physical Sciences, Health Sciences). Each file has a `domain_id_scaled` column (0-3) identifying the domain. Peers are not calculated, as are fixed using all fields. 

## Field/

Same structure as `All/`, split by field (~26 fields). Each file has a `field_id_scaled` column identifying the field.

## Topic/

| File | Rows | Description |
|---|---|---|
| `impact_topic.csv.gz` | Topic-level specialization counts per institution |
| `topics_embedding.csv.gz` | 2D embedding coordinates for topic landscape visualization |

## Column glossary

| Column | Meaning |
|---|---|
| `institution_id` | OpenAlex institution ID |
| `institution_id_scaled2` | 0-based index (row position in `institutions_info.csv`) |
| `period_id` | 0 = 1990-1999, 1 = 2000-2009, 2 = 2010-2019, 3 = 2020-2024 |
| `domain_id` | 1-based domain ID (1-4) |
| `domain_id_scaled` | 0-based domain ID (0-3) |
| `field_id_scaled` | 0-based field ID |
| `portfolio_composition` | Share of publications in a given field (RCA-based) |
| `disorder_index` | Entropy-based measure of research diversity |
| `similarity_score` | Cosine similarity between institution research profiles |
