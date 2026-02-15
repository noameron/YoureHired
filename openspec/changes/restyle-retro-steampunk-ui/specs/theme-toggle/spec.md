## REMOVED Requirements

### Requirement: Theme toggle component MUST be visible on all pages
**Reason**: The application now uses a single unified retro steampunk theme. Dark/light mode switching is no longer supported.
**Migration**: Remove ThemeToggle component, useTheme composable, and theme initialization script from index.html.

### Requirement: Theme toggle MUST switch between dark and light modes
**Reason**: Only one theme exists. Toggle functionality is no longer needed.
**Migration**: Remove all theme switching logic.

### Requirement: Theme preference MUST persist across sessions
**Reason**: With a single theme, there is no preference to persist.
**Migration**: Remove localStorage theme key and related code.

### Requirement: Dark mode MUST be the default theme
**Reason**: Replaced by the single retro steampunk theme which is always active.
**Migration**: No default selection needed.

### Requirement: Application MUST NOT flash wrong theme on page load
**Reason**: With a single theme, there is no wrong theme to flash.
**Migration**: Remove inline theme initialization script from index.html.
