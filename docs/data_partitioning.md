# Data Partitioning

## Regional Schemas

In local dev, regions are simulated as PostgreSQL schemas:
- `region_ireland` — Irish road segments and reservations
- `region_uk` — UK road segments and reservations
- `region_france` — French road segments and reservations

Each schema has identical table structures (`road_segments`, `reservations`), mimicking what would be separate databases in separate AWS regions.

## Partitioning Strategy

Road segments are assigned to regions by geographic bounding box:
- Ireland: lat 51-55.5, lng -10.5 to -6.0
- UK: lat 49.9-58.7, lng -5.7 to 1.8
- France: lat 42-51, lng -5 to 8.5

Cross-border segments (e.g. Dublin→Holyhead ferry, Calais→Dover) trigger the saga pattern.
