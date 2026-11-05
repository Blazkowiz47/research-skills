# Shared visual style

Use these defaults across diagram types; retain each type's structural notation.

## Appearance

- Use translucent pastel fills, light outlines, generous spacing, and dark labels.
  Cuboid front/top/side opacities around 34% / 20% / 30% reproduce the accepted
  network style. Flat blocks may use about 23% opacity. Adapt for print contrast.
- Starting palette: blue `#8fc4ed`, teal `#74c8b1`, purple `#b5a4e7`, amber
  `#e8bd73`, muted red `#e8a0a0`; ink `#20334a`, secondary text `#60738a`,
  background `#f5f7fb` or white. These are defaults, not fixed category assignments.
- Use one consistent sans-serif family. Keep titles, labels, and annotations
  visibly distinct. Avoid long prose inside shapes and unnecessary enclosing cards.
- Use shape and text as well as color to distinguish roles and states. Check that
  selected paths, errors, and categories remain understandable without color.
- Cuboids and stacked sheets convey volume, tensor structure, or components.
  Use flat blocks, lifelines, or diamonds where those express the meaning better.
  Decorative depth must not suggest an unsupported dimension or hierarchy.

## Connections and layout

Choose direction by type: usually left-to-right for structure/data and top-to-bottom
for sequence time. Route around labels, minimize crossings, and make endpoints
unambiguous. A connection to an enclosing group differs from one to a child node.

Define arrow meaning within each diagram. Solid may mean data flow, an interaction,
or a synchronous call, depending on the view. Dashed returns in a sequence are
different from dashed routing weights in a network; do not impose one meaning
across all types. Label or separate conventions when combining views. Distinguish
requests from returned data, and control signals from payloads.

Use stable colors and identifiers across related views. Show repetition through
a representative unit and a count, rather than drawing every repeated object.
Keep omitted details explicit when they affect interpretation.

## Consistency across figures

Keep the same operation, object, and state visually consistent across related
figures and before/after panels: symbols, colors, labels, and connection styles
should agree. Preserve each diagram type's conventions when comparing different
types; a dashed sequence return does not become a routing signal.

An inactive section must be neutral grey throughout: weights, activations,
operator glyphs, labels, outlines, and internal arrows. Do not leave a dark or
colored operator inside a greyed block. Keep labels legible and identify the
state in text or a legend. Grey only the inactive branch, not a shared upstream
path that still feeds active branches. Distinguish inactive in this example from
removed, unavailable, or unimplemented.

When generating a figure family programmatically, reuse drawing primitives and
style definitions for operators, arrows, and active/inactive states. Pass state
through to child elements so individual renderers do not drift. Reuse existing
helpers where practical; a single figure does not require a rendering framework.

Inspect related exports together. Check every occurrence of an operator and
every child of an inactive group, including arrowheads and annotations. Compare
legends with the actual symbols and paths. Keep bundled examples aligned with
the written conventions when those conventions change.

## Rendering and delivery

Prefer editable SVG for custom diagrams, with a PNG preview; PDF is useful for a
paper when the available renderer supports it. Retain the editable source when
delivering other formats. Use available tools and the existing environment;
do not add project dependencies merely to draw a diagram.

Direct SVG or an existing diagram library can reproduce the style. If Mermaid
or another textual format is requested, honor it and apply the palette and
layout as far as it supports them. Do not switch to an external design service
unless requested. A prose outline or an unrendered code block alone is not a
finished visual when local rendering is available.

Render and inspect the actual export, not just the source. Check label fit,
edge crossings, arrowheads, transparencies, font fallback, and readability at
the intended paper/slide/chat size. Do not claim an export was inspected if it
was not. Preserve existing figures unless replacement was requested.

## Example assets

Each type reference links its own preview and editable SVG. The examples were
accepted as style references on 2026-11-05. Their content is illustrative or
proposed, not a claim about an implemented system. Adapt the visual vocabulary;
do not copy their fixed coordinates, model choices, or component counts as rules.
