---
title: "From Tables to Cards: Modernizing the TableCloth Catalog UI"
date: 2025-12-08T00:00:00+09:00
draft: false
slug: "tablecloth-catalog-ui-refactoring"
tags:
  - TableCloth
  - Open Source
  - C#
  - Web Development
  - XSL
  - Generic Host
categories:
  - Development
translationKey: "tablecloth-catalog-ui-refactoring"
description: "The TableCloth catalog page has been redesigned with a modern card UI and category filtering. Generic Host pattern and quality management tools have also been introduced."
tldr: "The TableCloth catalog page has been redesigned with a modern card UI and category filtering. Generic Host pattern and quality management tools have also been introduced."
cover:
  image: "images/posts/tablecloth-catalog-ui-refactoring.jpg"
  alt: "TableCloth Catalog UI Update"
---

## Introduction

If you've ever used internet banking in Korea, you'll be familiar with the numerous security program installation requirements. While ActiveX has disappeared, countless security plugins that replaced it—AhnLab Safe Transaction, TouchEn nxKey, Veraport, and more—still demand installation on our PCs.

The [TableCloth](https://yourtablecloth.app) project is an open-source tool that allows you to run these security programs in an isolated Windows Sandbox environment. The [TableCloth Catalog](https://github.com/yourtablecloth/TableClothCatalog) serves as a database that organizes which security programs are required for each financial website.

## Update Overview

Five commits have been applied to the TableCloth Catalog project. This update is a comprehensive improvement across three areas: **Frontend**, **Backend**, and **DevOps**.

| Area | Changes | Key Technologies |
| ------ | --------- | ------------------ |
| **Frontend** | Complete catalog page redesign | Card UI, Category Filters, Responsive Layout |
| **Backend** | Build tool architecture refactoring | Generic Host, Dependency Injection, Structured Logging |
| **DevOps** | Quality management automation tools | Image Validation, Unused Resource Cleanup, Favicon Collection |

Let's examine what changed in each area and why these decisions were made.

---

## Frontend: From Tables to Cards

### Why Change the UI?

The existing catalog page was a typical HTML table format. Categories, service names, and required package lists were arranged in rows and columns. While functionally adequate, it had several limitations.

First, users had to scroll through over 100 services to find what they needed. On mobile devices, horizontal scrolling degraded usability, and the lack of visual hierarchy made information difficult to parse. Most importantly, category-based filtering was impossible, making it hard to quickly locate desired services.

To address these issues, we decided to completely redesign with a card-based UI.

### Responsive Card UI with XSL Transform

An interesting aspect of the TableCloth Catalog is that data is stored in XML format, and the web page is rendered through **XSLT (XSL Transformations)**. The browser directly transforms XML to HTML without any server-side logic.

#### Design Token System

The key to modern CSS design is **design tokens**. By defining colors, spacing, and shadows as CSS variables, you can maintain consistent design while making maintenance easier.

```css
:root {
    /* Color Palette */
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    
    /* Shadows */
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    
    /* Layout */
    --radius: 12px;
}
```

This color scheme draws inspiration from Tailwind CSS's default palette. Combining slate-based text colors with blue accent colors creates a clean yet professional impression.

### Responsive Layout with CSS Grid

The key to the card layout is the combination of CSS Grid's `auto-fill` and `minmax()`:

```css
.services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1.25rem;
}
```

This single line of CSS achieves the following: column count automatically adjusts based on screen width, each card maintains a minimum of 340px while distributing evenly across available space, and spacing between cards remains consistent at 20px.

The 340px minimum width was calculated to display cleanly as a single column even on mobile devices (approximately 375px).

### Adding Life with Micro-interactions

Cards that respond to user interaction are more engaging than static ones:

```css
.service-card {
    transition: transform 0.2s, box-shadow 0.2s;
}

.service-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}
```

When hovering, the card slightly rises. The 0.2-second transition feels smooth yet responsive. The 4px elevation is subtle but definitely noticeable.

## JavaScript Category Filter Implementation

Filtering is essential when searching through over 100 services. We implemented it with vanilla JavaScript:

```javascript
function filterCards(category) {
    const cards = document.querySelectorAll('.service-card');
    const buttons = document.querySelectorAll('.filter-btn');
    
    // Update button state
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Filter cards
    cards.forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}
```

The key is assigning a `data-category` attribute to each card. In XSL, it's generated like this:

```xml
<div class="service-card" data-category="{@Category}">
```

This approach has several advantages. Since filtering happens client-side, no server requests are needed. As a simple toggle feature, complex URL state management isn't required. Additionally, all cards display normally even when JavaScript is disabled, following the Progressive Enhancement principle.

### Visual Category Distinction

Each category was assigned a unique color badge:

```css
.category-Banking { background: #dbeafe; color: #1e40af; }
.category-CreditCard { background: #fce7f3; color: #9d174d; }
.category-Government { background: #d1fae5; color: #065f46; }
.category-Financing { background: #fef3c7; color: #92400e; }
.category-Insurance { background: #e0e7ff; color: #3730a3; }
.category-Education { background: #f3e8ff; color: #6b21a8; }
.category-Security { background: #fee2e2; color: #991b1b; }
.category-Other { background: #f1f5f9; color: #475569; }
```

The color choices carry meaning. Banking uses blue to symbolize trust and stability, while CreditCard uses pink/magenta associated with payments. Government uses green to represent public service, and Financing uses amber reminiscent of money. Insurance uses indigo to signify protection, and Security uses red to indicate caution and warnings.

---

## Backend: Refactoring Build Tools with Generic Host Pattern

Along with UI improvements, the backend tool `catalogutil.cs` was significantly refactored. The core change was applying .NET's **Generic Host** pattern.

### What is Generic Host?

Generic Host is a framework in .NET that manages application lifecycle, dependency injection, configuration, and logging. Originally used in ASP.NET Core web applications, it became available for console apps and background services starting with .NET Core 3.0.

```csharp
// Generic Host setup
var builder = Host.CreateApplicationBuilder(args);

// Read timeout value from configuration
const double DefaultTimeoutSeconds = 15d;
const double MinTimeoutSeconds = 5d;
var configuredTimeout = builder.Configuration.GetValue("TimeoutSeconds", DefaultTimeoutSeconds);
var timeoutSeconds = Math.Max(configuredTimeout, MinTimeoutSeconds);

// Service registration (Dependency Injection)
builder.Services.AddSingleton<CatalogLoader>();
builder.Services.AddSingleton<ImageConverter>();
```

### Why Generic Host for a Console App?

You might ask, "Is this complex pattern necessary for a simple build script?" However, the benefits of Generic Host are clear:

#### **Dependency Injection (DI)**

```csharp
// Explicit dependencies through constructor injection
public class CatalogLoader
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<CatalogLoader> _logger;
    
    public CatalogLoader(HttpClient httpClient, ILogger<CatalogLoader> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }
}
```

Using DI reduces coupling between classes, makes testing easier, and makes dependencies explicit.

#### **Configuration Management**

```csharp
// Read settings from appsettings.json or environment variables
var timeout = builder.Configuration.GetValue("TimeoutSeconds", 15d);
```

Using external configuration instead of hardcoded values allows different settings per environment.

#### **Structured Logging**

```csharp
_logger.LogInformation("Processing service: {ServiceName}", service.Name);
```

Structured logging transforms logs from simple strings into searchable data.

---

## DevOps: Quality Management Automation and Favicon Collection Improvements

### Favicon Collection Improvements

To display icons for each service in the catalog, we need to collect favicons from the respective websites. This update significantly improved the favicon collection logic.

### Web App Manifest Support

Modern websites define app icons through `manifest.json` (or `manifest.webmanifest`):

```json
{
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192" },
    { "src": "/icons/icon-512.png", "sizes": "512x512" }
  ]
}
```

The new version parses the HTML's `<link rel="manifest">` tag to find the manifest file and extract icon information from it.

### Fallback Strategy

If one method fails to find a favicon, the next method is attempted:

1. **Web App Manifest**: icons array from `manifest.json`
2. **Link Tags**: `<link rel="icon">` or `<link rel="shortcut icon">`
3. **Default Location**: `/favicon.ico`
4. **External Services**: Google Favicon service as fallback

This multi-layered fallback strategy allows successful icon retrieval from most websites.

### Automated Image Quality Management

Data quality management is always a challenge in open-source projects. The newly added quality management tool automatically performs several verification tasks.

First, there's image integrity verification. It checks whether icon files for all services registered in the catalog actually exist and detects corrupted or unloadable images. PNG format validity is also verified.

Next, there's unused resource cleanup functionality.

```text
⚠️  Orphan image found: images/Banking/OldBank.png
    → This image is not referenced by any service in the catalog
```

It automatically detects cases where a service was deleted but its image remains.

---

## Conclusion

This update is more than just a "pretty UI" change. We improved UX so users can quickly find desired services, enhanced code quality to make the project easier for developers to maintain, and built a system that automatically validates data integrity.

The value of open-source projects comes from the careful thought put into every line of code. If you're interested in the TableCloth project, visit the catalog page directly or explore the code on GitHub.

## References

- [TableCloth Catalog GitHub](https://github.com/yourtablecloth/TableClothCatalog)
- [TableCloth Project Homepage](https://yourtablecloth.app)
- [TableCloth Catalog Web Page](https://yourtablecloth.app/TableClothCatalog/)
- [.NET Generic Host Official Documentation](https://learn.microsoft.com/dotnet/core/extensions/generic-host)
