# AI Full-Build Recipe — from reference app to working project

How to take an idea ("build me an app like X") end-to-end with an AI agent: structure,
git model, quality gates, and the evaluation loop. Written after the **Vecto** build
(`D:\Vibe Coding\_desktop apps\Vecto` — a Vector Magic-style vectorizer); point any
model at this file plus `ai-project-setup-playbook.md` (same folder) and say:
*"Build <thing> following `_refs/ai-full-build-recipe.md`."*

---

## 1. Plan from the reference, not from imagination

- Inspect the reference app's install folder before writing any plan. DLL names, release
  notes, sample files, and its *own output files* reveal architecture and behavior
  (Vecto's core insight — shared boundary geometry — came from reading Vector Magic's
  sample SVG, not its marketing).
- Deliver a plan first; build only after an explicit "go build it".
- Pick the stack the human already works in (here: C# / .NET 8 / WPF, 0 warnings policy).

## 2. Bootstrap (once, per `ai-project-setup-playbook.md`)

Solution skeleton + `AGENTS.md` router + `docs/ai/` (START_HERE, DECISIONS, GOTCHAS,
and for algorithm-shaped projects **ALGORITHM_INDEX.md** — stage → algorithm → params →
code anchor). `.codegraph/` gitignored; `codegraph init` after the first code lands.
Never hand-maintain file maps; CodeGraph owns structure, markdown owns intent.

## 3. The git branch model (main + dev)

Branches are just named pointers into one commit history — the repo holds both; checking
out switches the working folder between them. The model used in all these projects:

- **`main`** = releases only. It sits at the last released state.
- **`dev`** = the working branch; every session's commits land here.
- On an explicit release request: merge dev → main (and tag `vX.Y.Z`).

Setup commands (what a model should run on day one):

```bash
git init -b main          # first commit = bootstrap scaffold, on main
git checkout -b dev       # all work happens here from now on
# ... commits on dev ...
git push -u origin main dev
```

Instruction line that makes any model follow it (put it in AGENTS.md, as Vecto does):
> Work on `dev`; merge to `main` only on an explicit release request. Commit after each
> verified milestone with a real message. Push `dev` after committing.

GitHub shows the **default branch** when you open the repo — for active private projects
set it to `dev` (`gh repo edit <owner>/<repo> --default-branch dev`) so current work and
docs are what you see; keep it `main` for public repos where visitors should see releases.

## 4. Work in verified milestones, not big bangs

Per phase: implement → `build` (0 warnings / 0 errors, TreatWarningsAsErrors on) →
tests green → run the real thing (CLI smoke, app `--smoke` flag) → CHANGELOG entry →
commit on dev → push. A WPF app should have a headless `--smoke` mode (trace something,
write output, exit 0/11) so the full stack is verifiable without eyes.

## 5. Evaluation-first development (the biggest lesson from Vecto)

For any output-quality project (vectorizer, audio, image processing), build the
**ground-truth round-trip harness** as early as possible:

1. Take real ground-truth files (for Vecto: the reference app's own sample SVGs).
2. Degrade them into the input a user would have (render vector → raster).
3. Run your engine on that input.
4. Re-render your output and **diff against the ground truth** — objective per-pixel
   metrics (perceptual ΔE, % wrong pixels) + a visual diff heatmap + payload stats
   (node counts vs the original).

This turns "it looks wobbly" into numbers and pictures the agent can iterate against:
change a constant → re-bench → compare. Every quality fix in Vecto v0.2–v0.4 came from
this loop. The agent must also *look at the rendered images*, not just the numbers —
several bugs were visible before they were measurable.

Two facts to remember for tracing-type projects:
- Error is roughly constant in absolute pixels → **higher-resolution input halves
  relative error per doubling**. Feed the tool good rasters.
- Metrics reward tracing noise; geometry priors (line/arc/primitive hypotheses) are what
  make output *clean* — validate them with shape-specific tests (a band's edges must be
  exactly 2 straight lines; a circle ≤8 segments within 0.8 px radial error).

## 6. Tests assert invariants, not snapshots

Geometric/structural truths that survive tuning: areas must tile the canvas exactly
(planarity), corners of rectangles stay exact, same input + seed → byte-identical
output, culture-invariance (run one test under de-DE — comma decimals corrupt output
formats silently).

## 7. Documentation upkeep (what future models need)

- CHANGELOG per milestone (the session log), ROADMAP with done/next/backlog.
- DECISIONS.md: every durable "why X over Y" the moment it's decided.
- GOTCHAS.md: environment traps as they're discovered (WSL `/mnt` quirks, license-locked
  package versions, `dotnet.exe` vs `dotnet`).
- ALGORITHM_INDEX.md: keep the stage table in sync with the pipeline — it's the fastest
  onboarding surface for the next model.
- `.codegraph/` never gets committed: a fresh clone runs `codegraph init` (seconds) and
  has the full structural index; the markdown carries everything a rebuild can't infer.

## 8. Handoff prompt (fill in)

> You're taking over **<project>** at `<path>`. Read `AGENTS.md`, then
> `docs/ai/START_HERE.md` and follow its links; recent work is in `CHANGELOG.md`.
> Fresh clone: `codegraph init`. Work on `dev` in verified milestones (build 0/0 →
> tests → run → CHANGELOG → commit → push). Quality work goes through the bench
> harness — numbers *and* rendered images — before and after every change.
