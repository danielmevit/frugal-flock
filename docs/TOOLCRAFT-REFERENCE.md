# Toolcraft reference — original Frugal Flock UI

## Scope

The owner named `npx @pixel-point/toolcraft create` as inspiration, with an
explicit instruction not to copy its code. **Do not run its scaffolder in
this repository or import its source, templates, assets, runtime, or skills.**
This boundary applies regardless of upstream licensing.

The official [Mesh FX demo](https://toolcraft.sh/demos/mesh-fx) was viewed
on 2026-10-03. It uses a dominant working area, a compact right-side
inspector with grouped controls, restrained app chrome, and a small
contextual toolbar. See also the [official project](https://toolcraft.sh/).
No Toolcraft dependency or implementation was added to Frugal Flock.

## Adapt the composition, not the creative-canvas product

- Main area: current task conversation, plan, activity, or result.
- Right inspector: named workers/providers, task scope, checks, and evidence.
- Group advanced settings into expandable sections; show a simple next
  action without forcing a beginner to learn orchestration terminology.
- Keep task-specific actions nearby. Label Start, Stop, Request changes,
  and Apply literally; never let a decorative control imply approval.
- Use original typography, spacing, colors, icons, and components following
  the Frugal Flock identity. No 3D runtime or image-processing canvas needed.
- On narrow screens, collapse the inspector without hiding the next
  decision. Support keyboard focus, readable labels, and reduced motion.

This refines [UX-DIRECTION.md](UX-DIRECTION.md); it does not start UI work.
After M1 is verified and accepted, M2 is a clearly labeled mock-data
prototype. Real provider control and project writes are separate work.
