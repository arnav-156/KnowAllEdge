# GraphPage Feature Quick Reference

## 🎯 Quick Feature Guide

### 🔍 Search Bar
**Location:** Top-center
**Usage:** Type to search all node content
**Shortcut:** `Ctrl+F`
**Features:**
- Real-time highlighting (golden glow)
- Match counter badge
- Clear button (✕)
- Dims non-matching nodes

### 🗺️ MiniMap
**Location:** Bottom-right (above shortcuts)
**Usage:** Click to navigate large graphs
**Colors:**
- 🟣 Purple = Topic
- 🔵 Blue = Subtopics
- ⚪ Gray = Explanations

### 🎮 Zoom Controls
**Location:** Bottom-left
**Buttons:**
- **+** Zoom in
- **−** Zoom out
- **⊡** Fit view (center all)
- **🔒** Lock/unlock
**Alternative:** Mouse wheel to zoom

### 🎯 Node Filters
**Location:** Bottom-left panel
**Toggles:**
- [ ] 📌 Topic
- [ ] 📋 Subtopics
- [ ] 💬 Explanations
**Feature:** State persists across sessions

### 📥 Export
**Location:** Top-right
**Buttons:**
- **📥 PNG** - Raster image (high quality)
- **📄 PDF** - Vector document (landscape)
**Shortcut:** `Ctrl+E`
**Filename:** `{topic}_concept_map.png/pdf`

### 🔄 Layout
**Location:** Top-right
**Options:**
- **↓ Vertical** - Top to bottom
- **→ Horizontal** - Left to right
**Tip:** Try both for different perspectives

### 💬 Tooltips
**Usage:** Hover over any node
**Shows:**
- Full node content
- Subtopic context (for explanations)
**Type:** Native browser tooltips

### 💾 Auto-Save
**Feature:** Automatic state persistence
**Saves:**
- Filter settings
- Search query
**Storage:** Browser localStorage

---

## ⌨️ Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| **Ctrl+F** | Focus Search | Jump to search bar |
| **Ctrl+E** | Export | Export to PNG |
| **Esc** | Close | Close open modal |
| **Mouse Wheel** | Zoom | Zoom in/out |
| **Click+Drag** | Pan | Move around graph |

---

## 🎨 Node Colors

| Type | Color | Description |
|------|-------|-------------|
| Topic | 🟣 Purple Gradient | Main concept |
| Subtopic | 🔵 Light Blue | Key areas |
| Explanation | ⚪ Light Gray | Detailed info |
| Error | 🔴 Light Red | Failed generation |

---

## 💡 Pro Tips

### Navigation
1. **Use MiniMap** for quick jumps in large graphs
2. **Double-click** background to fit view
3. **Ctrl+F** then type to find specific content
4. **Toggle filters** to focus on specific levels

### Search
1. Search is **case-insensitive**
2. Matches **partial words**
3. Searches **all node content** (not just visible text)
4. **Clear search** to reset highlighting

### Export
1. **Hide filters** before export for clean image
2. **Fit view** before export for best framing
3. **Use vertical layout** for printable documents
4. **PNG for web**, **PDF for presentations**

### Performance
1. **Hide explanations** for faster navigation with many nodes
2. **Use search** instead of scrolling
3. **Fit view** after filtering to recenter
4. **Clear search** when done to restore full opacity

---

## 📱 Mobile Usage

### Touch Gestures
- **Pinch** to zoom in/out
- **Drag** with one finger to pan
- **Tap** node to open modal
- **Double-tap** to fit view

### Mobile Tips
1. MiniMap still works on mobile
2. Use landscape orientation for better view
3. Export works on mobile browsers
4. Tooltips work on long-press (varies by browser)

---

## 🐛 Troubleshooting

### Search not working?
- Check if search bar is visible (top-center)
- Clear browser cache
- Reload page

### Export creating blank images?
- Wait for graph to fully load
- Try fit view first
- Check browser console for errors

### Filters not persisting?
- Enable browser localStorage
- Not in private/incognito mode?
- Clear localStorage and try again

### Keyboard shortcuts not working?
- Make sure modal is closed
- Check if input field is focused
- Try clicking graph background first

---

## 🎓 Best Practices

### For Students
1. **Search** to find specific concepts quickly
2. **Export PDF** for studying offline
3. **Filter subtopics only** for overview
4. **Use tooltips** for quick reference

### For Teachers
1. **Export PNG** for presentations
2. **Filter explanations** to show structure
3. **Use vertical layout** for linear teaching
4. **Share exported files** with students

### For Researchers
1. **Search across all nodes** for connections
2. **Export both layouts** for comparison
3. **Use MiniMap** for navigation
4. **Filter by type** to analyze structure

---

## 📊 Feature Coverage

### Implemented Features (12/12) ✅

#### Must Fix (4/4)
- ✅ Edge connections
- ✅ Text truncation
- ✅ Click modal
- ✅ Proper node IDs

#### Should Fix (8/8)
- ✅ Search bar
- ✅ MiniMap
- ✅ Zoom controls
- ✅ Node filtering
- ✅ Export PNG/PDF
- ✅ LocalStorage
- ✅ Keyboard navigation
- ✅ Hover tooltips

---

## 🚀 Coming Soon (Optional)

### Planned Enhancements
- [ ] SVG export
- [ ] Custom themes
- [ ] Search history
- [ ] Undo/Redo
- [ ] Share links
- [ ] Node editing
- [ ] Collaboration

---

## 📞 Support

### Common Questions

**Q: How do I export?**
A: Click 📥 PNG or 📄 PDF in top-right, or press Ctrl+E

**Q: Search not finding my node?**
A: Make sure the node isn't filtered out. Enable all filters.

**Q: How do I reset everything?**
A: Clear search, enable all filters, click fit view

**Q: Can I edit nodes?**
A: Not yet - click to view full content in modal

**Q: Where are my exports saved?**
A: Downloads folder (browser default location)

---

## 🎉 Quick Start Guide

### First Time Users
1. **View the graph** - Auto-generated on page load
2. **Try search** - Press Ctrl+F and type any word
3. **Click a node** - Opens detailed modal
4. **Export** - Click 📥 PNG to download
5. **Explore filters** - Toggle different node types

### Power Users
1. **Ctrl+F** → Search
2. **Ctrl+E** → Export
3. **Esc** → Close
4. **Mouse wheel** → Zoom
5. **MiniMap** → Navigate

---

**Last Updated:** November 12, 2025
**Version:** 2.0 (Complete Implementation)
**Status:** Production Ready ✅
