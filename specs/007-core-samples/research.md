# Research: Core Sample Model Enhancement

**Feature**: 007-core-samples | **Date**: 2026-01-16 | **Phase**: 0 - Outline & Research

## Research Questions

Based on Technical Context "NEEDS CLARIFICATION" items and User Story 5 complexity note, the following research is required:

### Q1: Sample Relationship Patterns & Complexity

**Context**: User Story 5 addresses typed sample relationships for provenance tracking. Clarification session noted "sample relationships can be very complex in some cases and will require research into proper implementation patterns."

**Research Tasks**:

1. Survey existing sample management systems (IGSN, SESAR, DataONE, GeoDIVA) for relationship patterns
2. Identify common relationship types across multiple research domains
3. Evaluate circular relationship prevention strategies
4. Assess performance implications of deep hierarchy queries
5. Determine if django-treebeard or django-mptt integration needed for complex hierarchies

**Decision**: Simple typed relationships with bidirectional queries

**Rationale**:

- **Relationship Types** (controlled vocabulary):
  - `parent-child`: General hierarchical relationship
  - `derived-from`: Sample derived/processed from another
  - `split-from`: Sub-sample created by splitting
  - `aliquot-of`: Representative portion taken from larger sample
  - `section-of`: Physical section cut from sample

- **Implementation**: Simple many-to-many through model (`SampleRelation`) with:
  - `source`: ForeignKey to Sample (the origin/parent sample)
  - `target`: ForeignKey to Sample (the destination/child sample)
  - `relationship_type`: CharField with controlled vocabulary
  - Bidirectional access via related names (`related`, `related_to`)

- **Circular Prevention**: Model clean() validation prevents:
  - Self-references (sample cannot relate to itself)
  - Direct circular relationships (A → B and B → A with same type)
  - Deep circular chains (graph traversal check, configurable depth limit)

- **Query Performance**:
  - For simple parent→children: Single query with prefetch_related
  - For deep hierarchies (5+ levels): Recursive CTE query or iterative fetching
  - No need for MPTT/treebeard unless >10 levels or high-frequency tree queries

**Alternatives Considered**:

- **django-treebeard**: Rejected - Adds complexity for uncommon use case, most portals have shallow hierarchies (<5 levels)
- **django-mptt**: Rejected - Similar reasoning, plus maintenance concerns (less actively maintained)
- **Separate hierarchy tables per relationship type**: Rejected - Complicates queries, vocabulary provides sufficient typing

**Performance Implications**:

- Shallow hierarchies (<5 levels): Standard Django ORM performs well
- Deep hierarchies (5-10 levels): May need recursive queries or caching
- Very deep (>10 levels): Rare in practice, can optimize if needed
- Recommendation: Start simple, optimize based on actual usage patterns

### Q2: Polymorphic Query Optimization

**Context**: Performance goal of <200ms for polymorphic queries with 1000+ samples.

**Research Tasks**:

1. Understand django-polymorphic query overhead
2. Identify optimization strategies for mixed-type querysets
3. Evaluate prefetch_related vs select_related effectiveness
4. Determine if custom QuerySet methods needed

**Decision**: Custom QuerySet with selective prefetching

**Rationale**:

- django-polymorphic adds one additional JOIN per query to fetch polymorphic type
- Overhead minimal (<50ms) for typical queries
- Main optimization: Avoid N+1 queries via prefetch_related
- Custom methods:
  - `with_related()`: Prefetch dataset, location, contributors
  - `with_metadata()`: Prefetch descriptions, dates, identifiers
  - `select_subclasses()`: Force specific subclass loading when needed

**Performance Benchmarks** (estimated):

- Base polymorphic query: +10-20ms overhead vs non-polymorphic
- With prefetch_related: Reduces N+1 from O(n) to O(1) queries
- 1000 samples: ~150ms with optimizations (within <200ms goal)

**Alternatives Considered**:

- **Non-polymorphic approach**: Rejected - Loses type information, requires manual type tracking
- **Separate tables per type**: Rejected - Violates Django polymorphic patterns, complicates queries

### Q3: IGSN Metadata Alignment

**Context**: Sample model should align with IGSN v1.0 schema, but redesign project ongoing.

**Research Tasks**:

1. Review IGSN v1.0 metadata schema
2. Identify core fields vs optional fields
3. Check redesign project status
4. Plan for schema evolution

**Decision**: Core fields aligned, monitor redesign

**Rationale**:

- **Core IGSN fields implemented**:
  - name (title)
  - sample_type (controlled vocabulary)
  - location (spatial data)
  - material (optional)
  - collection_date (via SampleDate)
  - identifiers (via SampleIdentifier with IGSN type)

- **Monitoring strategy**:
  - Track IGSN redesign via GitHub/mailing lists
  - Plan migration in future feature if schema changes significantly
  - Keep model flexible (concrete FK for metadata, controlled vocabularies, extensible polymorphic base)

**Alternatives Considered**:

- **Full IGSN v1.0 compliance**: Rejected - Many fields optional/portal-specific
- **Wait for redesign completion**: Rejected - Timeline uncertain, need functional model now

### Q4: Mixin Design Patterns

**Context**: SampleFormMixin and SampleFilterMixin must work with registry auto-generation.

**Research Tasks**:

1. Determine mixin vs base class approach
2. Define mixin responsibilities vs registry responsibilities
3. Ensure compatibility with Feature 004 registry

**Decision**: Mixins provide reusable field configuration, not registration logic

**Rationale**:

- **SampleFormMixin provides**:
  - Pre-configured widgets (dataset autocomplete, status select)
  - Field ordering for common sample fields
  - Request parameter handling for queryset filtering
  - Does NOT handle registration or auto-generation (registry responsibility)

- **SampleFilterMixin provides**:
  - Common filters (status, dataset, polymorphic type)
  - Generic search configuration
  - Does NOT handle filterset generation (registry responsibility)

- **Usage pattern**:

  ```python
  # Developer defines custom form
  class RockSampleForm(SampleFormMixin, forms.ModelForm):
      class Meta:
          model = RockSample
          fields = ['name', 'dataset', 'status', 'mineral_type', 'hardness']
      # Mixin provides widget/field setup for name/dataset/status
      # Developer only defines mineral_type/hardness specific behavior
  ```

**Alternatives Considered**:

- **Base classes instead of mixins**: Rejected - Less flexible for multiple inheritance
- **Mixins handle registration**: Rejected - Violates separation of concerns, duplicates Feature 004

## Summary of Decisions

| Question | Decision | Impact on Implementation |
|----------|----------|--------------------------|
| Sample Relationships | Simple typed relationships via SampleRelation model | Implement clean() validation for circular prevention, provide recursive query utility for deep hierarchies |
| Polymorphic Queries | Custom QuerySet with prefetch methods | Create SampleQuerySet with with_related(), with_metadata(), select_subclasses() |
| IGSN Alignment | Core fields aligned, monitor redesign | Implement core IGSN fields, document alignment, plan future migration if needed |
| Mixin Design | Mixins provide reusable configuration, not registration | Keep mixins focused on field/widget setup, registry handles auto-generation |

## Open Questions for Phase 1

- Should SampleRelation allow multiple relationships of same type between two samples?
- What permission model for viewing relationships (inherit from samples or separate)?
- Should relationships be soft-deletable or hard-deleted?
- How should admin interface display relationship graph (inline vs separate view)?

These will be resolved during data-model.md design phase.
