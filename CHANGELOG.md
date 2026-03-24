# Changelog

## v0.2.6 — 2026-03-24
**Search**
- Search now matches stat names in addition to crystal names (e.g. type "crit" to find all Critical Rate crystals)

**Quick filter chip row**
- Horizontal scrollable chip row below tabs: ATK%, MATK%, CR, CD%, INT%, DEX%, NMPR, MP
- Single-select — tap once to filter, tap again to clear
- `···` at the end opens the full stat picker; shows a count badge when filters are active
- First-visit: `···` pulses with a tooltip to surface the feature (dismissed on first tap, never shown again)
- Removed the standalone ⊞ header button (chip row replaces it)

## v0.2.5 — 2026-03-23
**Data fixes**
- Diark ← Armasite (was incorrectly linked from Devil Dango)
- Raging Dragon Bovinari ← Clawed Iron Witch (was Melancia)
- Jiva ← Altoblepas (was marked standalone, now correctly linked)
- Pillorocas ← Ox King (was marked standalone, now correctly linked)
- Stormun: reclassified as Weapon Crysta (Coryn Club misclassified as Enhancer)
- Shadow Devil Cavalier: reclassified as Additional Crysta (not Enhancer)

## v0.2.4 — 2026-03-21
- Mobile is now the default page (`index.html`); desktop removed
- Hover tooltip on mouse (name, stats, drop source)
- Search match: matched nodes pulse border to distinguish from chain members
- Type anywhere → auto-focus search box
- Stat rows: value column hugs name (grid layout, not spread apart)
- Panel drawer height reduced so nodes stay visible behind it
- Pan boundary margin tightened
- Zoom buttons: rapid clicks no longer queue/clutter (cancel previous animation)
- **Fix:** wheel scroll pans vertically, does not zoom; pinch zoom works independently
- **Fix:** DOM event listeners were accumulating on each tab/search/filter change, causing broken pan clamp, tap, and momentum

## v0.2.3 — 2026-03-19
- Fix: search now shows full bloodline (ancestors + descendants) of matched crystal

## v0.2.2
- Mobile view with bottom drawer panel, stat picker, touch momentum, edge hiding during pan
- Separate mobile.html with auto-redirect for touch devices ≤900px
- Desktop: Mobile button in header

## v0.2.1
- Reset View restores exact initial viewport (pan + zoom) per tab
- Scroll = vertical pan with momentum; zoom via +/− buttons and slider
- Longest upgrade chain always appears topmost
- Minimap viewport box scales with zoom level
- Removed enhancer toggle — enhancers always shown

## v0.2.0
- Pan boundary clamped to node extents (left/right based on graph width)
- Smooth scroll momentum with friction
- Zoom slider (logarithmic scale)
- Favicon added

## v0.1.0
- Initial release: Cytoscape.js graph, dagre layout, slot tabs, stat filter chips, side panel, minimap
