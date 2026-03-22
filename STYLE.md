
# Terminal Dark,Style Guide

## Philosophy

Terminal aesthetic inspired by CRT monitors and retro gaming UIs. Pure black
backgrounds, monospace typography, high-contrast text, minimal color usage.
Color is functional,it encodes data or indicates state, never decoration.

---

## Typography

**Font:** JetBrains Mono (Google Fonts CDN)

```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap" rel="stylesheet">
```

**Weights:** 400 (regular), 500 (medium), 700 (bold,headings only)
**Case:** all lowercase for UI text (headings, labels, nav, buttons)

### Scale

| Token        | Size | Weight | Color   | Usage                                  |
|--------------|------|--------|---------|----------------------------------------|
| heading-lg   | 20px | 500    | primary | page titles                            |
| heading-sm   | 14px | 500    | muted   | section headings                       |
| body         | 12px | 400    | primary | table content, paragraphs              |
| label        | 11px | 400    | muted   | form labels, column subheaders, captions |
| stat-value   | 20px | 500    | primary | metric card numbers                    |
| stat-label   | 11px | 400    | muted   | metric card descriptions               |

---

## Color System

### Grayscale (UI chrome)

| Token      | Hex       | Usage                                            |
|------------|-----------|--------------------------------------------------|
| black      | #000000   | page background, chart interiors                 |
| surface    | #1a1a1a   | nav, inputs, cards, buttons, elevated surfaces   |
| border     | #404040   | all borders and lines (white @ 25% on black)     |
| muted      | #808080   | labels, secondary text, inactive elements        |
| readable   | #b0b0b0   | body text in instructional/onboarding contexts   |
| primary    | #ffffff   | headings, body text, active content              |

Only two background tiers: black and surface. No other bg colors.

### Accent (UI interactive elements)

A single accent color used for all interactive chrome: active tab
underlines, links, button borders, focus rings, step numbers. Must not
collide with any data or semantic color. Choose one:

| Option | Hex       | Name       | Character                                  |
|--------|-----------|------------|--------------------------------------------|
| A      | #ffffff   | white      | purest terminal. links need underline       |
| B      | #e8d5b0   | warm white | amber phosphor CRT. retro warmth            |
| C      | #d4785a   | soft coral | warm, desaturated. near-orange without heat |
| D      | #5a9e8f   | muted teal | cool complement. risk: too subtle           |
| E      | #a78bfa   | lavender   | readable, modern-retro. discord-adjacent    |
| F      | #ff9800   | orange     | high energy. use only if excluded from data |

### Semantic (numeric indicators only)

These appear ONLY on numeric values indicating positive/negative change.
Never on sentences, labels, headings, officer names, or UI elements.

| Token    | Hex       | Usage                                       |
|----------|-----------|---------------------------------------------|
| positive | #2ecc71   | +N% diffs, positive changes, "complete" state |
| negative | #c0392b   | -N% diffs, negative changes, "incomplete" state |

### Data Visualization (categorical)

Assigned in order to data series. Never used in UI chrome. Reserved
semantic colors (#2ecc71, #c0392b) excluded from assignment.

| Slot | Hex       | Name    | Hue  | Origin          |
|------|-----------|---------|------|-----------------|
| 1    | #ff9800   | orange  | 30°  | warm primary    |
| 2    | #3498db   | blue    | 210° | cool primary    |
| 3    | #9c27b0   | purple  | 285° | warm secondary  |
| 4    | #00bcd4   | cyan    | 187° | terminal CRT    |
| 5    | #e6c730   | gold    | 50°  | amber monitor   |
| 6    | #e84393   | magenta | 330° | gap filler      |
| 7    | #808080   | gray    | n/a  | catch-all       |

Color wheel coverage: 30°, 50°, 187°, 210°, 285°, 330°,roughly
even distribution with no semantic collisions. If the accent color
occupies one of these slots, shift that slot's data color to gray or
drop it from the rotation.

---

## Borders & Lines

All borders are a single color: border (#404040).

| Element                   | Style                     |
|---------------------------|---------------------------|
| Nav bottom                | 1px solid border          |
| Input / dropdown          | 0.5px solid border        |
| Table header row          | 1px solid border          |
| Table body row separator  | 1px solid surface         |
| Section divider (heavy)   | 2px solid border          |
| Chart container           | 0.5px solid border        |
| Button                    | 0.5px solid border        |
| Card / info box           | 0.5px solid border        |
| Chart gridlines (Plotly)  | border                    |
| Chart axis lines (Plotly) | border                    |
| Zero-reference line       | 2px dashed border         |

---

## Components

### Nav bar (tab-style)
```
background:    surface
border-bottom: 1px solid border
layout:        flex, space-between
left:          tab links (inline, no ul/li)
right:         user info + action link
```

| State    | Text color | Underline             |
|----------|------------|-----------------------|
| inactive | muted      | none                  |
| hover    | primary    | none                  |
| active   | primary    | 2px solid accent      |

Action link (e.g. "switch account", "log out"): accent color.
User name: primary.

### Form inputs
```
background:    surface
border:        0.5px solid border
border-radius: 4-6px
padding:       8-10px 12-14px
color:         primary
focus ring:    accent (border-color or box-shadow)
```

Label above input: label token (11px, muted).

### Counter widget
```
[ - ]  3  [ + ]
```
| Part          | Default                          | Hover                     |
|---------------|----------------------------------|---------------------------|
| button bg     | surface                          | #2a2a2a                   |
| button border | 0.5px solid border               | 0.5px solid #606060       |
| button text   | muted                            | primary                   |
| value         | primary, weight 500, min-width 20px centered |                |

Buttons: 28x28px minimum (36px for mobile touch targets).

### Stat / metric cards
```
layout:        grid, 2-4 columns, gap 12px
background:    surface
border-radius: 6px
padding:       1rem
label:         stat-label token
value:         stat-value token (primary, or positive/negative if diff)
```

### Info box
```
background:    surface
border:        0.5px solid border
border-radius: 8px
padding:       1rem 1.25rem
text:          body token, primary color
```

Numeric values within may use semantic positive/negative coloring.
Surrounding prose stays primary (#ffffff).

### Progress bar
```
track:         surface, border-radius 4px, height 6px
fill:          positive (#2ecc71), or accent,project choice
text below:    label token
```

### Button (action)
```
background:    surface
border:        0.5px solid accent (or border for neutral)
border-radius: 4-6px
padding:       6-10px 14-24px
color:         accent (or muted for neutral)
font-size:     11-13px
hover:         lighten bg to #2a2a2a, brighten text
```

### Table
```
header bg:     surface (optional) or transparent
header text:   muted, weight 400
header border: 1px solid border
body text:     primary, weight 400
row separator: 1px solid surface
```

---

## Chart Theming (Plotly)

```python
CHART_LAYOUT = dict(
    plot_bgcolor="#000000",
    paper_bgcolor="#000000",
    font=dict(
        family="JetBrains Mono",
        color="#ffffff",
        size=12,
    ),
    xaxis=dict(
        gridcolor="#404040",
        linecolor="#404040",
        zerolinecolor="#404040",
    ),
    yaxis=dict(
        gridcolor="#404040",
        linecolor="#404040",
        zerolinecolor="#404040",
    ),
    legend=dict(
        font=dict(color="#ffffff"),
    ),
)

DATA_COLORS = [
    "#ff9800",  # orange
    "#3498db",  # blue
    "#9c27b0",  # purple
    "#00bcd4",  # cyan
    "#e6c730",  # gold
    "#e84393",  # magenta
    "#808080",  # gray
]
```

Single-series charts: use accent color for bars/lines.
Multi-series charts: use DATA_COLORS in order, opacity 0.7-0.8.
Trend lines: dashed #808080.
Reference lines (zero, threshold): 2px dashed #404040.

---

## Chart Theming (matplotlib)

```python
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.facecolor": "black",
    "axes.facecolor": "black",
    "axes.edgecolor": "white",
    "axes.labelcolor": "white",
    "text.color": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "#404040",
    "grid.alpha": 0.25,
    "legend.facecolor": "black",
    "legend.edgecolor": "white",
    "font.family": "monospace",
})

DATA_COLORS = [
    "#ff9800", "#3498db", "#9c27b0", "#00bcd4",
    "#e6c730", "#e84393", "#808080",
]
```

Spine visibility: hidden for heatmaps, white @ 25% alpha for line/bar plots.

---

## Layout Patterns

### Page structure
```
nav (surface bg, sticky top)
main content (black bg, max-width 900-1100px, padding 1.5-2rem)
```

### Results page header
```
left:  page heading (heading-lg)
right: "last updated: {timestamp}" (label) + refresh button (neutral btn)
```

### Login / onboarding page
```
heading (heading-lg, primary)
instruction card (surface bg, border, border-radius 8px)
  heading inside card (heading-sm or body, primary)
  body text (body size, readable color #b0b0b0)
  accent-colored step numbers
form below card
  label (readable color)
  input
  submit button (accent border + text)
```

---

## CSS Variables Template

```css
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

:root {
    --font:       'JetBrains Mono', monospace;
    --black:      #000000;
    --surface:    #1a1a1a;
    --border:     #404040;
    --muted:      #808080;
    --readable:   #b0b0b0;
    --primary:    #ffffff;
    --accent:     #e8d5b0;  /* swap per project */
    --positive:   #2ecc71;
    --negative:   #c0392b;

    --data-1:     #ff9800;
    --data-2:     #3498db;
    --data-3:     #9c27b0;
    --data-4:     #00bcd4;
    --data-5:     #e6c730;
    --data-6:     #e84393;
    --data-7:     #808080;

    color-scheme: dark;
}

* {
    font-family: var(--font);
    box-sizing: border-box;
}

body {
    background: var(--black);
    color: var(--primary);
    margin: 0;
}
```

---

## Rules

1. Color is functional. If it doesn't encode data or state, it's grayscale.
2. Two background tiers only: black and surface. No third level.
3. Semantic colors (positive/negative) appear only on numeric values, never on prose or labels.
4. Data visualization colors are never used in UI chrome.
5. The accent color is the only non-grayscale in the UI. Choose one per project.
6. All text is lowercase in UI elements.
7. All borders are the same color (#404040). No variation per element.
8. Charts match the UI: black bg, white text, #404040 grid, JetBrains Mono.
