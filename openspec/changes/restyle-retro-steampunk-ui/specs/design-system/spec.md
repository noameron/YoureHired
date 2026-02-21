## MODIFIED Requirements

### Requirement: Application MUST use centralized design tokens via CSS custom properties

All design values MUST be defined as CSS custom properties for consistency. Since the application uses a single retro steampunk theme, tokens no longer vary by theme class.

#### Scenario: Design tokens are available globally
- **Given** the application is running
- **When** any component renders
- **Then** CSS custom properties are available for colors, spacing, typography, shadows, and decorative effects
- **And** properties reflect the retro steampunk aesthetic

### Requirement: Color palette MUST use warm vintage steampunk tones

Color tokens MUST use a warm sepia/brass palette evoking Victorian-era industrial materials.

#### Scenario: Steampunk colors are applied
- **Given** the application is running
- **When** viewing any page
- **Then** backgrounds use aged parchment dark tones (#1A1410, #2A2218, #3A3028)
- **And** text uses warm cream/ivory colors (#E8DCC8, #C4B69C, #9A8B74)
- **And** accent elements use brass/copper tones (#C4883C primary)
- **And** borders use oxidized brass tones (#5A4A32, #6A5A42)

#### Scenario: Semantic colors maintain meaning with warm tones
- **Given** a status indicator is displayed
- **When** the status is success
- **Then** it uses patina green (#5A8A5A)
- **When** the status is warning
- **Then** it uses warm amber (#C49A3C)
- **When** the status is error
- **Then** it uses rust red (#A04030)
- **When** the status is info
- **Then** it uses steel blue (#4A7A9A)

### Requirement: Typography MUST use Abril Fatface, Libre Baskerville, and Cutive Mono fonts

The application MUST use Abril Fatface for display headings, Libre Baskerville for body text, and Cutive Mono for code — evoking 1930s Art Deco and vintage print aesthetics.

#### Scenario: Headings use Art Deco display font
- **Given** the application is running
- **When** viewing any heading (h1–h3)
- **Then** the text renders in Abril Fatface font family
- **And** falls back to Georgia, serif if unavailable

#### Scenario: Body text uses vintage serif font
- **Given** the application is running
- **When** viewing any body or paragraph text
- **Then** the text renders in Libre Baskerville font family
- **And** falls back to Georgia, 'Times New Roman', serif if unavailable

#### Scenario: Code uses typewriter mono font
- **Given** the application is running
- **When** viewing code blocks or code input areas
- **Then** the text renders in Cutive Mono font family
- **And** falls back to 'Courier New', Courier, monospace if unavailable

### Requirement: Button styles MUST follow steampunk design specification

Buttons MUST use brass-toned styling with vintage industrial effects.

#### Scenario: Primary button styling
- **Given** a primary button is rendered
- **Then** it has a brass/copper gradient background
- **And** it has rounded border radius with a subtle embossed edge effect
- **And** it has a warm brass-tinted drop shadow
- **When** the user hovers over the button
- **Then** the button brightens slightly and shadow deepens
- **And** a warm brass glow effect appears

#### Scenario: Secondary button styling
- **Given** a secondary button is rendered
- **Then** it has a transparent background with an oxidized brass border
- **When** the user hovers over the button
- **Then** the border and text turn brass/copper accent color

### Requirement: Form inputs MUST follow steampunk design specification

Input fields MUST use vintage industrial styling.

#### Scenario: Input field styling
- **Given** an input field is rendered
- **Then** it has an aged dark background color
- **And** it has a subtle inset shadow creating a recessed/engraved effect
- **When** the user focuses the input
- **Then** a brass/copper border appears
- **And** a warm glow ring surrounds the input

### Requirement: Cards MUST follow steampunk design specification

Card components MUST use aged parchment styling with brass accents.

#### Scenario: Card styling
- **Given** a card component is rendered
- **Then** it has an aged dark parchment background color
- **And** it has an oxidized brass border
- **And** it has brass rivet decorations at corners via CSS pseudo-elements
- **And** it has appropriate shadow styling creating depth

### Requirement: Badges MUST follow steampunk design specification

Badge components MUST use vintage-appropriate shapes and warm colors.

#### Scenario: Difficulty badge colors
- **Given** a difficulty badge is rendered
- **When** the difficulty is "easy"
- **Then** it has a patina green background and cream text
- **When** the difficulty is "medium"
- **Then** it has a warm amber background and dark text
- **When** the difficulty is "hard"
- **Then** it has a rust red background and cream text

### Requirement: Pages MUST display vintage vignette and texture background

Pages MUST have an aged parchment texture with darkened edges instead of the emerald gradient.

#### Scenario: Vintage background visible
- **Given** any page is loaded
- **When** viewing the page background
- **Then** a subtle vignette effect darkens the edges of the viewport
- **And** a faint paper grain texture is visible across the background
- **And** the background does not interfere with content readability

### Requirement: Design system MUST meet accessibility standards

The design system MUST meet WCAG AA accessibility standards with the steampunk palette.

#### Scenario: Focus states are visible
- **Given** an interactive element exists
- **When** the user focuses it via keyboard
- **Then** a visible brass-colored focus ring appears around the element

#### Scenario: Reduced motion is respected
- **Given** the user has reduced motion preference enabled
- **When** viewing any page
- **Then** animations and decorative effects are disabled or significantly reduced

#### Scenario: Color contrast meets WCAG AA
- **Given** any text is displayed
- **Then** the contrast ratio between text and background is at least 4.5:1
- **And** cream text (#E8DCC8) on dark parchment (#1A1410) achieves sufficient contrast

## ADDED Requirements

### Requirement: Application MUST display CSS-only film grain overlay

A subtle film grain effect MUST be visible across the application to evoke vintage film projection.

#### Scenario: Film grain is visible
- **Given** any page is loaded
- **When** viewing the page
- **Then** a subtle animated noise pattern overlays the entire viewport
- **And** the grain effect has very low opacity (does not impair readability)
- **And** the grain animates subtly to simulate film projection flicker

#### Scenario: Film grain respects reduced motion
- **Given** the user has reduced motion preference enabled
- **When** viewing any page
- **Then** the film grain animation is paused (static grain is acceptable)

### Requirement: Application MUST include decorative Art Deco ornaments and gear motifs

CSS-only decorative elements MUST be used at key UI boundaries to reinforce the steampunk aesthetic.

#### Scenario: Section dividers use Art Deco pattern
- **Given** a section divider or horizontal rule is rendered
- **Then** it displays as a decorative Art Deco geometric line pattern via CSS
- **And** it uses brass/copper accent colors

#### Scenario: Gear/cog motifs appear at decorative positions
- **Given** the page layout renders
- **Then** CSS-drawn gear/cog shapes appear as background decoration
- **And** decorative elements do not interfere with interactive content or readability
