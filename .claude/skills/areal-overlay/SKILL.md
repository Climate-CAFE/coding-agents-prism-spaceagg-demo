---
name: areal-overlay
description: Use when intersecting polygons (such as Census blocks) with raster grid cells or other polygons to calculate overlap areas, normalized weights, and geographic coverage. Covers densification, equal-area measurement, sliver handling, and numerical validation.
---

# Areal Overlay

Areal overlay calculates polygon intersection areas and weights used by downstream spatial aggregation.

This Skill provides reusable implementation and validation guidance. Project-specific scientific decisions belong in the feature specification.

## Workflow

1. **Validate inputs.** Check for null, empty, and invalid geometries. Report issues and repair geometries only when approved by the specification.

2. **Identify candidate intersections.** Use spatial indexing or bounding-box filtering to identify overlapping polygon pairs. Ensure the grid covers the study area and report any uncovered zones.

3. **Calculate intersections.** Intersect polygons in the common CRS specified by the project. Preserve unique zone and grid-cell identifiers.

4. **Densify when necessary.** Densify polygon edges before reprojection when needed to preserve area accuracy. Use the segment length and method defined in the specification.

5. **Measure areas.** Transform intersections and zones to the configured equal-area CRS and calculate areas consistently.

6. **Handle slivers.** Remove intersections below the specified minimum area threshold. Record the number and total area removed.

7. **Calculate weights.** For each zone with retained intersections:

   `weight = overlap_area / sum(retained_overlap_areas)`

   If the specification requires a different denominator, follow that definition and document it.

8. **Calculate geographic coverage.**

   `coverage = sum(retained_overlap_areas) / zone_area`

   Keep coverage separate from normalized weights.

9. **Write outputs.** Preserve zone IDs, grid-cell IDs, overlap areas, weights, and coverage. Ensure each zone–cell pair is unique.

## Validation

- All retained overlap areas are positive.
- Normalized weights sum to 1 within the specified tolerance for zones with retained intersections.
- Weights are greater than 0 and at most 1.
- Geographic coverage is between 0 and 1, allowing numerical tolerance.
- Report zones with no intersections or insufficient coverage.
- Check for duplicate zone–cell pairs.
- Report the number and area of removed slivers.
- Compare a sample of equal-area measurements against geodesic reference calculations when required by the specification.
- When allocating extensive attributes such as population, verify conservation under the specified weighting and coverage rules. Report any unallocated population.

## Scientific Decisions

The feature specification must define:

- Equal-area CRS appropriate for the study region.
- Whether densification is required and the segment length.
- Minimum overlap area threshold.
- Weight normalization method and tolerance.
- Minimum geographic coverage and failure behavior.
- Whether geometry repair is permitted.

Do not assume Washington-specific parameters apply to other states.

## Guardrails

- Never silently modify geometries or change scientific methods.
- Never treat normalized weights as evidence of complete geographic coverage.
- Do not silently discard uncovered zones or excluded intersections.
- Keep the implementation in `src/`; use this Skill for guidance.