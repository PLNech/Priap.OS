# Charte Graphique - Priap.OS

## Brand Concept: "The Digital Oracle"

**Priap.OS** = Priapos (Greek god of gardens, fertility, vegetation) + OS (Operating System)

We're building an **AI Oracle** that tends the digital garden of LeekWars, maximizing our leek's potential through systematic experimentation (STELLAR methodology).

### Aesthetic Fusion

| Source | Contribution |
|--------|-------------|
| **Priapos/Greek Classics** | Wisdom, ritual, prophecy, marble textures |
| **LeekWars** | Vegetables, combat, growth, green life force |
| **Cyberpunk** | Neon glows, circuits, dark backgrounds, tech edge |
| **Singularity/AGI** | Oracle eye, all-seeing AI, purple divinity |

**Result**: **Greco-Futurism** - Ancient wisdom encoded in neural networks

---

## Color Palette

### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Void Black** | `#1A1A2E` | Background, dark sections |
| **Marble Cream** | `#E8E4D9` | Text on dark, highlights |
| **Oracle Cyan** | `#00F5D4` | Primary accent, links, glow effects |
| **Divine Purple** | `#7B2CBF` | AGI/divinity vibes, secondary accent |
| **Leek Green** | `#90BE6D` | Life force, success states, growth |

### Accent Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Bronze Highlight** | `#B8860B` | Text underlines, subtle accents |
| **Radiation Glow** | `#39FF14` | Intense green for emphasis |
| **Warning Coral** | `#FF6B6B` | Errors, losses, alerts |

### CSS Variables

```css
:root {
  /* Primary */
  --color-void: #1A1A2E;
  --color-marble: #E8E4D9;
  --color-cyan: #00F5D4;
  --color-purple: #7B2CBF;
  --color-leek: #90BE6D;

  /* Accents */
  --color-bronze: #B8860B;
  --color-radiation: #39FF14;
  --color-coral: #FF6B6B;

  /* Semantic */
  --color-bg: var(--color-void);
  --color-text: var(--color-marble);
  --color-link: var(--color-cyan);
  --color-success: var(--color-leek);
  --color-error: var(--color-coral);
}
```

---

## Typography

### Font Stack

| Role | Font | Fallback | Weight |
|------|------|----------|--------|
| **Headlines** | Cinzel | Georgia, serif | 700 |
| **Body** | Inter | system-ui, sans-serif | 400, 500 |
| **Code** | JetBrains Mono | Consolas, monospace | 400 |

### CSS

```css
:root {
  --font-display: 'Cinzel', Georgia, serif;
  --font-body: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, 'Courier New', monospace;
}

h1, h2, h3 {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

body {
  font-family: var(--font-body);
  font-weight: 400;
  line-height: 1.6;
}

code, pre {
  font-family: var(--font-mono);
}
```

---

## Logo Concept

### The Oracle Eye

A pyramid/eye motif (like Eye of Providence) with a **leek as the pupil**.

```
      ▲
     /🥬\      <- Leek as the all-seeing pupil
    /────\
   /______\
  ═════════
   PRIAP.OS
```

**Elements**:
- Triangle/pyramid: Ancient wisdom, stability
- Eye/leek pupil: The Oracle sees through combat data
- Circuit traces: Optional, radiating from the eye
- Glow effect: Cyan/purple neon aura

### Logo Variations

1. **Full logo**: Pyramid + eye + wordmark
2. **Icon only**: Just the pyramid/eye (for favicons, small spaces)
3. **Wordmark only**: "PRIAP.OS" in Cinzel with bronze underline

---

## Visual Motifs

### Decorative Elements

| Element | Description | Usage |
|---------|-------------|-------|
| **Circuit Laurels** | Laurel wreath made of PCB traces | Victory, headers |
| **Greek Key + Circuits** | Meander pattern with tech twist | Section dividers |
| **Marble Texture** | Subtle noise/grain overlay | Backgrounds |
| **Neon Glow** | Box-shadow with cyan/purple | Hover states, focus |
| **Glitch Effect** | RGB split on images | Hero section, drama |

### Section Dividers

```
════════════════════╣ SECTION TITLE ╠════════════════════
```

Or with circuit motif:
```
──●──────────────────────────────────────────────●──
```

---

## UI Components

### Buttons

```css
.btn-primary {
  background: linear-gradient(135deg, var(--color-purple), var(--color-cyan));
  color: var(--color-void);
  border: none;
  padding: 0.75rem 1.5rem;
  font-family: var(--font-display);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.btn-primary:hover {
  box-shadow: 0 0 20px var(--color-cyan);
}
```

### Code Blocks

```css
pre {
  background: #0d1117;
  border-left: 3px solid var(--color-cyan);
  padding: 1rem;
  overflow-x: auto;
}

code {
  color: var(--color-leek);
}
```

### Chips/Tags (GitHub-style)

```css
.chip {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: rgba(0, 245, 212, 0.1);
  border: 1px solid var(--color-cyan);
  border-radius: 2rem;
  font-size: 0.875rem;
  color: var(--color-cyan);
}
```

### Links

```css
a {
  color: var(--color-cyan);
  text-decoration: none;
  border-bottom: 1px solid var(--color-bronze);
  transition: all 0.2s;
}

a:hover {
  color: var(--color-marble);
  border-color: var(--color-cyan);
}
```

---

## Writing Tone

### Voice

**Playful Mythological + Tech Blog Casual**

- Use Oracle/prophecy metaphors but keep it grounded
- Meta-reflection on the dev process ("here's what we learned...")
- Real code samples with explanations
- GitHub-style UX affordances (chips, issue links, commit refs)

### Examples

**Good**:
> "The Oracle spoke: kiting at low damage levels is a path to timeout and defeat. We tested 1000 fights and the data was clear..."

**Too esoteric**:
> "From the depths of the digital Delphi, the spirits whispered of movement patterns beyond mortal comprehension..."

**Good meta-reflection**:
> "Plot twist: our 'improvement' was actually statistical noise. Here's how we caught it with proper sample sizes..."

### Content Patterns

1. **Hypothesis → Test → Result → Learning**
2. **Show the code, explain the why**
3. **Link to commits, issues, experiments.md**
4. **Use chips for status**: `✅ VALIDATED` `❌ REJECTED` `🔄 TESTING`

---

## File Structure

```
docs/
├── src/
│   ├── components/
│   │   ├── Header.astro
│   │   ├── Footer.astro
│   │   ├── Chip.astro
│   │   └── CodeBlock.astro
│   ├── layouts/
│   │   ├── Base.astro
│   │   └── BlogPost.astro
│   ├── pages/
│   │   ├── index.astro          # Landing
│   │   ├── methodology.astro    # STELLAR framework
│   │   └── blog/
│   │       └── [...slug].astro
│   └── styles/
│       └── charte.css
├── public/
│   ├── fonts/
│   ├── images/
│   │   └── logo/
│   └── favicon.svg
└── content/
    └── blog/
        ├── 001-the-oracle-awakens.md
        └── 002-counter-kiter-discovery.md
```

---

## Technical Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Generator** | Astro | Fast, modern, partial hydration for interactive bits |
| **Styling** | Vanilla CSS + CSS Variables | Simple, no build complexity |
| **Fonts** | Google Fonts (self-hosted) | Cinzel, Inter, JetBrains Mono |
| **Hosting** | GitHub Pages | Free, integrated with repo |
| **Content** | Markdown + Astro Content Collections | Easy blog management |

---

## References

- [Cinzel Font](https://fonts.google.com/specimen/Cinzel)
- [Inter Font](https://fonts.google.com/specimen/Inter)
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/)
- [Astro Documentation](https://docs.astro.build)
