# Anchor Frontend

React + TypeScript + Tailwind CSS frontend for grounded requirements review.

## Sprint 4: Four-Lane Review UI

### Features

**Four-Lane Layout:**
1. **Confirmed** (green) - Grounded requirements ready for review
2. **Needs Review** (yellow) - Quarantined + ungrounded candidates
3. **Conflicts** (red) - Detected contradictions
4. **Possible Gaps** (gray) - Unconsumed substantive segments

**Per-Item Actions:**
- Accept
- Reject (with reason)
- Edit (with before/after tracking)

**Jump-to-Quote:**
- Click evidence → scroll to source segment
- Highlighted context view

**Audit Trail:**
- Complete history of all actions
- Actor, timestamp, before/after

### Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:3000

### API Connection

Backend must be running on http://localhost:8000

Vite proxy automatically forwards `/api/*` requests to backend.

### Key Components

- `ReviewBoard.tsx` - Four-lane layout
- `RequirementCard.tsx` - Requirement summary with quick actions
- `RequirementDetail.tsx` - Full requirement view with jump-to-quote
- `api.ts` - API client functions

### Visual Distinction

- **Grounded**: Green badge, green accent
- **Quarantined**: Red badge, red accent (fabricated citations)
- **Ungrounded**: Gray badge (no supporting text found)

### Non-Negotiable: Jump-to-Quote

Clicking any evidence citation must:
1. Scroll to the exact source segment
2. Highlight the segment temporarily
3. Show full context around the quote

This is the grounding guarantee - humans can verify every citation.
