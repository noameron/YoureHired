# Theme Toggle Capability

## Overview

Provides a persistent light/dark theme toggle accessible on every page, allowing users to switch between themes with their preference saved across sessions.

## ADDED Requirements

### Requirement: Theme toggle component MUST be visible on all pages

The application MUST display a theme toggle button in a fixed position on every page.

#### Scenario: User sees theme toggle on role selection page
- **Given** the user navigates to the role selection page
- **When** the page loads
- **Then** a theme toggle button is visible in the top-right corner
- **And** the button displays a sun icon if current theme is dark
- **And** the button displays a moon icon if current theme is light

#### Scenario: User sees theme toggle on practice page
- **Given** the user navigates to the practice page
- **When** the page loads
- **Then** a theme toggle button is visible in the top-right corner

### Requirement: Theme toggle MUST switch between dark and light modes

Clicking the theme toggle MUST switch the current theme immediately.

#### Scenario: User switches from dark to light mode
- **Given** the current theme is dark
- **When** the user clicks the theme toggle button
- **Then** the theme changes to light mode immediately
- **And** all UI elements update to use light mode colors
- **And** the toggle icon changes from sun to moon

#### Scenario: User switches from light to dark mode
- **Given** the current theme is light
- **When** the user clicks the theme toggle button
- **Then** the theme changes to dark mode immediately
- **And** all UI elements update to use dark mode colors
- **And** the toggle icon changes from moon to sun

### Requirement: Theme preference MUST persist across sessions

The user's theme preference MUST be saved and restored on subsequent visits.

#### Scenario: Theme persists after page refresh
- **Given** the user sets the theme to light mode
- **When** the user refreshes the page
- **Then** the theme remains light mode

#### Scenario: Theme persists after browser restart
- **Given** the user sets the theme to dark mode
- **And** closes and reopens the browser
- **When** the user returns to the application
- **Then** the theme is dark mode

### Requirement: Dark mode MUST be the default theme

New visitors without a saved preference MUST see dark mode by default.

#### Scenario: First-time visitor sees dark mode
- **Given** the user has never visited the application before
- **When** the user loads any page
- **Then** the theme is dark mode

### Requirement: Application MUST NOT flash wrong theme on page load

The correct theme MUST be applied before any content is rendered.

#### Scenario: Page loads without theme flash
- **Given** the user has set their theme to light mode
- **When** the user navigates to any page
- **Then** the page renders in light mode immediately
- **And** there is no visible flash of dark mode content
