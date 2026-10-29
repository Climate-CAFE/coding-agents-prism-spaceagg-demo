---
name: weighted-spatial-aggregation
description: Use when aggregating gridded environmental data to geographic regions using area-weighted and population-weighted methods, including coverage, missing-data handling, and temporal summaries.
---

# Weighted Spatial Aggregation

Aggregate gridded environmental data into geographic summaries using explicit weighting methods. Follow `AGENTS.md` and the approved feature specification for scientific decisions.

Use `areal-overlay` to prepare cell-to-polygon intersection areas.

## Weighting Methods

### Area-Weighted Mean

For a geographic zone with raster cell values `v_i` and intersection areas `a_i`:

`mean = sum(a_i * v_i) / sum(a_i)`

- Include only cells with valid values and positive overlap areas.
- Exclude NoData from both numerator and denominator; preserve valid zeros.
- Return missing (NaN) when no valid cells contribute.
- Calculate coverage as valid overlap area divided by the full zone area.
- Distinguish geographic coverage from valid-data coverage.

### Population-Weighted Mean

For a larger region with zone estimates `m_j` and populations `p_j`:

`mean = sum(p_j * m_j) / sum(p_j)`

- Include only zones with valid estimates and positive population.
- Calculate population coverage against the full region population.
- Report missing zones and excluded population.
- Return missing when no valid population contributes.
- Apply minimum coverage thresholds only when explicitly specified.

Both means are normalized over valid observations. Coverage must be reported separately to describe how much of the original geography or population contributed.

## Workflow

1. Obtain validated cell-to-zone overlap areas from `areal-overlay`.
2. Calculate area-weighted estimates and coverage for each zone and date.
3. Join zone estimates to population data using approved geographic identifiers and vintages.
4. Calculate population-weighted estimates and coverage for each region and date.
5. Validate results and write outputs with unique geographic/date keys.
6. Reuse validated daily estimates for temporal aggregation when required.

## Temporal Aggregation

- Derive annual summaries from validated daily estimates.
- Distinguish mean daily values from annual totals and preserve units.
- Track valid, missing, and expected days.
- Never interpret missing dates as zero.
- Do not report incomplete annual totals as complete-year estimates.

## Scientific Validation

- Test both weighting formulas against small, independently calculated examples.
- Include valid zeros, missing observations, partial coverage, and zero denominators.
- Check nonnegative weights, coverage bounds, and geographic key uniqueness.
- Verify that population and boundary vintages are compatible.
- Preserve geographic identifiers, units, dates, and relevant metadata.
- Report missingness and coverage alongside estimates.

## Implementation Guidance

- Implement production calculations in `src/` and focused pytest tests in `tests/`.
- Keep weighting functions separate from data loading, geographic joins, and output writing.
- Use configured paths, geographic scope, and scientific parameters.
- Do not hardcode coverage thresholds or silently change weighting methods.
- Ask for approval when the specification does not define a scientific decision.
