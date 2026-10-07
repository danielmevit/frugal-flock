# Dark theme and live work map

Owner request recorded on 2026-10-08. Dark mode is a requested UI addition;
the connected work map below is the proposed design for the requested live
overview. Both remain planned. The existing browser ships in v0.5.3;
recoverable continuation remains the next delivery priority.

## Dark theme

Provide Light, Dark and System choices in the workspace header or settings.
Follow the operating system initially and remember an explicit choice in the
browser. Apply it across the workspace, forms, output, files and work map.

Use dark neutral surfaces, readable text and restrained state colors. Keep
focus outlines clear, and distinguish states with words and icons as well
as color. Preserve the existing layout and behavior when changing themes.
Theme selection is local presentation and needs no AI call.

## A map of the work

Offer a Work map beside the existing list view. Show who owns each task and
what stage the work has reached. Files and branches belong in a selected
node's detail panel rather than in the initial graph.

An illustrative future view, not an observation of a running team:

```mermaid
flowchart LR
    L[Lead] --> W1[Worker: Grok]
    L --> W2[Worker: Gemini]
    W1 --> T1[Task: execution logic]
    W2 --> T2[Task: interface]
    T1 --> C1[Checks]
    T2 --> C2[Checks]
```

Connections must say what they mean: task ownership, delegation, dependency
or review. Draw a connection only when recorded evidence supports that
relationship. The current activity endpoint supplies worker/task ownership
and process, validation and review observations. It does not supply a lead
identity or a complete dependency graph. Start with a Project hub when lead
data is unavailable; add lead and dependency connections when supported.

## Keep large projects readable

- Start with active work and tasks needing attention. Group completed work
  under expandable history; show how many records a group contains.
- Group tasks by worker. Keep each worker's current attempt separate from
  its earlier attempts and historical results.
- Offer search and filters for worker and task state. Expanding a group or
  focusing a task should reveal its immediate connections first.
- Keep a bounded number of expanded nodes, with a visible count and an
  explicit way to reveal more. Choose the initial bound during UI work.
- Preserve node positions and the selected task while observations update.
  Avoid moving the whole graph on every refresh. Offer Fit view and Reset.
- Keep the list view available, including on small screens and for keyboard
  navigation. Nodes need readable labels, not just provider logos.

Selecting a node opens its task, latest recorded update and evidence. Link
to protected Source output and tracked files when those capabilities and
worker grants are enabled. Display missing capabilities plainly. Selecting
a node observes work; starting, stopping or accepting work remains an
explicit action in the existing workflow.

## Live means observed

Reuse the current activity polling first: the shipped page refreshes every
two seconds. Show the observation time and update the affected nodes rather
than reconstructing the layout. On failure, mark the view unavailable and
remove current-state claims; an old graph must not look live.

Use the actual process, validation and review states independently. A held
worker lock or old running record does not prove an AI is currently making
progress. Preserve Unknown and interrupted completion. Do not infer overall
acceptance from a successful process exit or a recorded reviewer approval.

Use a small state transition to make genuine updates visible, respecting
reduced motion. Do not animate fabricated work, invent percentages, estimate
quota from node activity or call an AI to summarize every refresh. Existing
protected output excerpts can provide short updates where enabled.

## Delivery

Implement the theme as a small UI slice, then a read-only work map using
existing observed ownership and states. Add richer delegation/dependency
data separately when the engine records it. Assign a release number when
the UI scope is frozen; these additions are not included in published v0.5.3.

Check theme persistence and contrast, accurate states, failed observations,
stable selection and layout, grouped history, keyboard access and a real
browser journey. A larger fixture should exercise the collapsed view.
Follow the selected work mode and use the full required gate at release.
