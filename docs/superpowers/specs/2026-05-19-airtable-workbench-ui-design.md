# Airtable Workbench UI Optimization Design

- Date: 2026-05-19
- Reference: `docs/design-references/airtable-DESIGN.md`
- Approved approach: Workbench Reskin
- Scope order: A first, then B

## Goal

Optimize the existing frontend presentation toward the Airtable reference style without changing backend APIs, routing, authentication, or task creation behavior.

The work should make the app feel like a sober workflow software workbench: white canvas, dark ink, restrained borders, compact tables, near-black primary actions, and limited signature accents from the Airtable palette. It should not become a marketing page, a card-heavy dashboard, or a blue SaaS admin template.

## Approved Scope

### A. Global Visual System And Layout Shell

Apply the Airtable-style vocabulary across the existing app shell:

- Replace the current blue-led palette with Airtable-inspired tokens.
- Tune Ant Design theme tokens for buttons, tables, tags, menus, drawers, tabs, progress, inputs, and layout backgrounds.
- Keep the current sidebar-based information architecture.
- Restyle `AppLayout`, `Sidebar`, `PageShell`, and `Toolbar` to create a unified workbench shell.
- Preserve existing routes and page-level data fetching.
- Keep responsive collapse behavior for the sidebar and prevent text overflow on narrow screens.

### B. Task Center Homepage

After the global shell is in place, refine the task center homepage:

- Convert status filters into Airtable-style view tabs with counts.
- Keep the task table dense and scannable while improving row rhythm, borders, status tags, progress display, and action affordances.
- Add a lightweight task summary area for running, completed, failed, and queued states when task data is available.
- Restyle empty state to feel like a calm workbench prompt rather than a generic icon state.
- Keep the existing task creation drawer entry point and existing pagination behavior.

## Design System

### Color Palette

Use the Airtable reference as the source of truth:

- Primary / ink: `#181d26`
- Primary active: `#0d1218`
- Body text: `#333840`
- Muted text: `#41454d` or a softened derivative for tertiary labels
- Hairline border: `#dddddd`
- Strong border: `#9297a0`
- Canvas: `#ffffff`
- Soft surface: `#f8fafc`
- Dark sidebar surface: `#181d26`
- Dark elevated surface: `#1d1f25`
- Signature coral: `#aa2d00`
- Signature forest: `#0a2e0e`
- Signature cream: `#f5e9d4`
- Signature peach: `#fcab79`
- Signature mint / yellow may be reserved for status support, not dominant layout color.

Current blue primary colors should be removed from the main UI treatment. Blue may remain only where required by browser defaults or external AntD internals that are not practical to override in this pass.

### Typography

The reference names Haas Grotesk, but the implementation should not add a new font dependency in this pass. Use the existing system font stack and make the style closer to the reference through weight, size, and line-height:

- Page titles: 20-24px, weight 400 or 500, line-height around 1.25.
- Section labels and table text: 12-14px, compact but readable.
- Buttons: 14-16px, weight 500.
- Avoid negative letter spacing.
- Avoid bold headings unless needed for hierarchy.

### Spacing

Continue the existing 8px-based spacing system:

- Page header: 16-24px vertical rhythm.
- Content area: 24-28px desktop padding, reduced on small screens.
- Toolbar/view tabs: 6-8px gaps.
- Table rows: compact 38-48px row heights.

### Radius And Elevation

- Keep corners small: 4px, 6px, 8px, and occasional 10px for framed work surfaces.
- Use pill radius only for true pills or circular icon controls.
- Avoid stacked cards and page sections styled as decorative floating cards.
- Prefer borders and surface contrast over shadows.
- Use shadows sparingly or not at all.

### Motion

- Use subtle 150-200ms hover/focus transitions for controls.
- Preserve existing running-status pulse only if it remains restrained.
- Do not add decorative animation.

## Architecture

This is a frontend-only visual optimization. The implementation should keep the current React + Ant Design structure:

- `frontend/src/theme/tokens.ts` becomes the shared Airtable-inspired token source.
- `frontend/src/theme/antdTheme.ts` maps those decisions into AntD component tokens.
- `frontend/src/components/layout/AppLayout.tsx` remains the high-level shell.
- `frontend/src/components/layout/Sidebar.tsx` keeps the navigation model but updates dark workbench styling.
- `frontend/src/components/layout/PageShell.tsx` provides the white page header and soft content canvas.
- `frontend/src/components/layout/Toolbar.tsx` becomes the reusable view-tab/search/action row.
- `frontend/src/components/task/TaskList.tsx` receives task-center-specific table treatment.
- `frontend/src/components/common/StatusTag.tsx`, `EmptyState.tsx`, and related common components may be tuned to match the new system.
- `frontend/src/index.css` can hold global AntD overrides and keyframes that cannot be expressed cleanly through component tokens.

No new routing layer, global state system, or UI framework should be introduced.

## Component Design

### App Shell

The app remains a left-sidebar workbench.

The sidebar uses the Airtable dark ink surface, a small peach/coral brand mark, restrained nav hover states, and compact user/logout controls. Collapsed mode stays supported. The sidebar should not add marketing copy, large logos, or decorative gradients.

### Page Shell

`PageShell` becomes a consistent white header plus soft content canvas:

- Header has title, optional subtitle, breadcrumb, and right-aligned actions.
- Title weight is lighter than the current implementation.
- Subtitle stays muted and compact.
- Content background remains soft, with child components responsible for their own framed work surfaces.

### Toolbar / View Tabs

`Toolbar` should support Airtable-style view tabs:

- Active tab uses cream fill and subtle border.
- Inactive tabs are quiet text buttons.
- Counts remain visible but secondary.
- Search input and action controls align to the right when present.
- Layout wraps cleanly on mobile.

### Buttons

Primary actions use near-black background with white text. Hover/active states deepen the ink color. Secondary buttons are white with a hairline border. Danger actions remain semantically red/coral but should not dominate normal screens.

### Tables

Tables are central to the workbench feel:

- Compact rows.
- Clear header background.
- Hairline borders.
- Low-radius framed table container.
- No heavy card shadow.
- Hover state should be subtle and not blue.

### Status Tags

Status tags should retain meaning while matching the palette:

- `running`: cream or light coral support with dark/coral text.
- `succeeded`: light forest/mint support with forest text.
- `failed`: light coral support with coral text.
- `pending`: soft neutral support with muted ink.
- `aborted`: warm support from mustard/yellow derivatives.

Running status may keep a subtle dot pulse.

### Task Center Summary

The homepage may include a compact summary row above the table. It should be functional and derived from current task data:

- Running count.
- Succeeded count for current loaded page.
- Failed count.
- Pending/queued count.

This summary must not invent cross-page totals if the current API response only contains the loaded page. Labels should avoid implying all-time/global totals unless the API actually provides them.

### Empty State

Empty states should use concise text, a direct action when available, and a small signature-color panel or restrained icon treatment. Avoid oversized generic AntD empty artwork.

## Data Flow

The task center continues to use the existing `useQuery` call to `listTasks` with status and page parameters. The status view tabs update the same `statusFilter` state and reset `page` to 1.

Derived UI values, such as filter counts and summary cards, should be calculated from the currently loaded `tasks` array. This means counts are page-local unless the backend later exposes aggregate counts.

Row click behavior continues to navigate to task detail. The explicit view action should remain available and should avoid double-triggering row navigation if clicked.

## Error Handling

This design does not change API error behavior. Existing React Query and page-level error handling should remain in place.

Visual states should stay clear for:

- Loading: table skeleton/loading state should use the new neutral palette.
- Empty: use the new workbench empty state.
- Failed task status: use the new coral status treatment.
- Disabled pagination: keep disabled controls visibly muted.

## Accessibility And Responsive Behavior

- Preserve button semantics for interactive controls.
- Keep focus indicators visible and compatible with the ink/cream palette.
- Maintain sufficient contrast for text, active tabs, and status tags.
- Ensure sidebar collapsed mode remains usable.
- On narrow screens, headers and toolbars stack; task table may hide lower-priority columns as the existing design already favors compact operational use.
- Button labels and tab labels must not overflow their containers.

## Testing And Verification

Implementation should be verified with:

- `npm run build` in `frontend`.
- TypeScript compilation through the existing build.
- Browser inspection of the task center at desktop width.
- Browser inspection at a narrow/mobile width for sidebar collapse, header wrapping, toolbar wrapping, and table legibility.
- Manual check that task row click and explicit detail action still navigate correctly.

If a local backend is not available, visual verification may use the frontend's existing empty/loading states where possible, and the limitation should be reported.

## Non-Goals

- Do not redesign the task creation drawer beyond token/theme consistency unless a small style issue blocks the approved look.
- Do not change backend APIs or add aggregate count endpoints.
- Do not redesign task detail or settings pages beyond global shell/theme consistency in this pass.
- Do not introduce a new design library.
- Do not add decorative gradients, large hero sections, or marketing-style content.
