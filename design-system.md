# Design system

Calm, warm and clean — closer to a wellbeing app than a hospital. Tokens live in `frontend/src/styles/app.css`.

## Colour
| Role | Light | Dark |
| --- | --- | --- |
| Background | `#F7F9F8` | `#0F1513` |
| Surface | `#FFFFFF` | `#18201D` |
| Text / secondary | `#1C2622` / `#5B6B65` | `#E8EEEB` / `#9AABA4` |
| Primary (teal) | `#2A7F78` | `#5CC2B6` |
| Mental | `#7B6FB0` | `#A99EE0` |
| Fitness | `#C9733A` | `#F2A877` |
| Sports medicine | `#B8604A` | `#E8957F` |
| Nutrition | `#4F8E4B` | `#86C482` |
| Education | `#3D7BC4` | `#78A9E6` |
| Good / follow-up / error | `#3E8E5E` / `#B5791F` / `#C2544A` | `#6CC38F` / `#E6B060` / `#E58378` |

Service colours mark *what* something is; trend colours mark *direction*, never judgement. Red is kept for technical errors and the emergency call button.

## Type
IBM Plex Sans Arabic (Arabic) + IBM Plex Sans (English). Scale 28 / 22 / 18 / 16 / 14; body never below 16. Line height 1.6 Arabic, 1.5 English. Tabular figures for values.

## Layout & interaction
- Mobile first, max content width 560–640 px, 16 px gutters, 8 px spacing grid.
- Bottom navigation with five tabs; *Book* is the raised centre action.
- Touch targets ≥ 48 px. Radii: 10 (controls), 16 (panels), 24 (card / sheets).
- One primary action per screen; secondary actions live in lists or sheets.
- RTL/LTR via logical properties only (`inline-start/end`); directional icons flip, others don't.
- Motion 200–300 ms, only in response to actions; `prefers-reduced-motion` respected.
- Theme: light / dark / automatic, applied before first paint and saved to the account.

## The signature element
The personal card header: the user's identity on a solid primary panel, critical alerts as tags, and a thin four-colour band (mental · fitness · nutrition · education) as the card's mark. Everything else stays quiet so the card reads first.
