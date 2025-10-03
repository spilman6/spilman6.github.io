# Copilot Instructions for spilman6.github.io

This document provides essential context for AI coding agents working in this repository.

## Project Overview

This is a personal portfolio and course content website built with:
- GitHub Pages for hosting
- Jekyll as the static site generator
- Bootstrap for responsive layout and styling
- Custom CSS for theming and overrides

## Repository Structure

```
/
├── assets/          # Static assets (images, etc)
├── Bookmarks/       # Bookmarklets section
├── courses/         # Course content pages
├── css/            # Stylesheet files
│   ├── styles.css    # Main Bootstrap styles
│   ├── override.css  # Custom theme overrides
│   └── test.css      # Testing styles
└── js/             # JavaScript files
```

## Key Architecture Patterns

1. **Page Layout**
   - Uses Bootstrap's responsive grid system
   - Fixed-top navigation with collapsible sidebar (`#sideNav`)
   - Sections are organized with `resume-section` class
   - Mobile-first design approach

2. **Styling Architecture**
   - Base styles from Bootstrap in `styles.css`
   - Theme customizations in `override.css` 
   - Custom variables defined in `:root` (e.g. `--prime-color: #BD5D38`)

3. **Course Content Structure**
   - Each course has its own directory under `/courses`
   - Course pages follow a consistent card-based layout
   - Uses markdown for content with YAML frontmatter

## Common Development Tasks

1. **Adding a New Course Page**
   - Create new directory under `/courses`
   - Include index.html with standard course template
   - Add course card to main courses page
   - Link required assets and stylesheets

2. **Styling Updates**
   - Add custom styles to `override.css`, not `styles.css`
   - Use Bootstrap utility classes where possible
   - Follow mobile-first responsive patterns

## Project Conventions

1. **HTML Structure**
   - Use semantic HTML5 elements
   - Include standard meta tags and stylesheets
   - Follow Bootstrap component patterns
   - Use Font Awesome for icons

2. **CSS Guidelines**
   - CSS custom properties for theming
   - Bootstrap classes for layout/spacing
   - Override styles use descriptive classes
   - Mobile-first media queries

3. **Asset Management**
   - Images go in `/assets/img/`
   - External scripts loaded from CDN
   - Local scripts in `/js`
   - Favicons in assets root

## Integration Points

1. **External Dependencies**
   - Bootstrap CSS/JS (v5.2.3)
   - Font Awesome (v6.6.0)
   - Google Fonts (Saira Extra Condensed, Muli)
   - Jekyll for static site generation

2. **Social Links**
   - LinkedIn, GitHub, Twitter, Facebook
   - Update in both index.html and Bookmarks/index.html

## Best Practices

1. Use consistent section structure with `resume-section` class
2. Follow Bootstrap's responsive breakpoints
3. Keep Jekyll front matter organized
4. Maintain mobile-first responsive design
5. Use semantic HTML elements
6. Follow established file/folder naming conventions