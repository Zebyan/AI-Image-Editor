# 🧠 Image AI Desktop App — Implementation Task Board

A structured, dependency-aware task board for building the app using **Python + PySide6** and packaging it as a **Windows executable**.

---

# 📌 EPIC 0 — Project Setup

## Tasks
- [ ] Initialize Git repository
- [ ] Create folder structure (app/, ui/, processors/, etc.)
- [ ] Create virtual environment
- [ ] Add `requirements.txt`
- [ ] Install core dependencies (PySide6, numpy, pillow, opencv)
- [ ] Create `main.py` entry point
- [ ] Add basic logging system

## Deliverable
Project runs with an empty window.

## Dependencies
None

---

# 📌 EPIC 1 — Core UI Shell

## Tasks
- [ ] Create `QMainWindow`
- [ ] Add menu bar (File, Edit, View, Help)
- [ ] Add left sidebar (module selector)
- [ ] Add central widget (image viewer placeholder)
- [ ] Add right panel (controls placeholder)
- [ ] Add status bar (image info, zoom, logs)
- [ ] Implement basic layout with `QDockWidget` or layouts

## Deliverable
Full UI skeleton visible and responsive.

## Dependencies
EPIC 0

---

# 📌 EPIC 2 — Image Loading & Viewer

## Tasks
- [ ] Implement image open dialog
- [ ] Add drag & drop support
- [ ] Load image via Pillow/OpenCV
- [ ] Convert image → QImage/QPixmap
- [ ] Display image in viewer
- [ ] Implement zoom (in/out)
- [ ] Implement pan (mouse drag)
- [ ] Implement fit-to-window
- [ ] Implement reset zoom
- [ ] Add checkerboard background (optional)

## Deliverable
User can load and interact with an image.

## Dependencies
EPIC 1

---

# 📌 EPIC 3 — App State & History

## Tasks
- [ ] Create `AppState` class
- [ ] Store:
  - [ ] original image
  - [ ] current image
  - [ ] preview image
  - [ ] image path
- [ ] Implement undo stack
- [ ] Implement redo stack
- [ ] Add reset image functionality
- [ ] Connect UI to state via signals

## Deliverable
State is centralized and undo/redo works.

## Dependencies
EPIC 2

---

# 📌 EPIC 4 — Export & File Operations

## Tasks
- [ ] Implement "Save As"
- [ ] Implement export dialog (format, quality)
- [ ] Support PNG, JPG, BMP
- [ ] Add overwrite protection
- [ ] Add recent files list

## Deliverable
User can save/export images reliably.

## Dependencies
EPIC 3

---

# 📌 EPIC 5 — Edit Module (MVP Core)

## Tasks

### Geometry
- [ ] Crop tool (selection overlay)
- [ ] Resize tool (width/height + aspect lock)
- [ ] Rotate tool (slider + 90° buttons)
- [ ] Flip tool (horizontal/vertical)

### Color
- [ ] Brightness slider
- [ ] Contrast slider
- [ ] Saturation slider

### Filters
- [ ] Blur (Gaussian)
- [ ] Sharpen
- [ ] Grayscale
- [ ] Sepia
- [ ] Negative

### System
- [ ] Non-destructive preview pipeline
- [ ] Apply / Cancel workflow
- [ ] Reset controls button

## Deliverable
User can edit images with preview + undo.

## Dependencies
EPIC 3

---

# 📌 EPIC 6 — Analysis Module

## Tasks

### Visual Stats
- [ ] RGB histogram (matplotlib widget)
- [ ] Channel toggle (R/G/B)

### Color Analysis
- [ ] Color palette (K-Means)
- [ ] Display swatches + percentages

### Metadata
- [ ] EXIF reader
- [ ] Table view display

### Quality
- [ ] Sharpness score (Laplacian variance)
- [ ] Noise estimation

### Structure
- [ ] Edge detection (Canny)

### System
- [ ] Run analysis in worker threads
- [ ] Cache results per image state

## Deliverable
User can inspect image properties.

## Dependencies
EPIC 5

---

# 📌 EPIC 7 — Worker System (Concurrency)

## Tasks
- [ ] Create base worker class (`QThread` or QRunnable)
- [ ] Implement signals:
  - [ ] started
  - [ ] progress
  - [ ] finished
  - [ ] error
- [ ] Integrate workers into:
  - [ ] analysis
  - [ ] heavy edits
- [ ] Add loading indicator / spinner

## Deliverable
UI does not freeze during heavy operations.

## Dependencies
EPIC 5

---

# 📌 EPIC 8 — Classification Module

## Tasks

### Models
- [ ] Implement model manager
- [ ] Load ResNet50
- [ ] Load EfficientNet-B0
- [ ] Load MobileNetV3

### Inference
- [ ] Preprocess image
- [ ] Run inference
- [ ] Softmax probabilities

### UI
- [ ] Model selector dropdown
- [ ] Run button
- [ ] Display Top-5 predictions
- [ ] Confidence bars

### Batch
- [ ] Folder input
- [ ] Loop inference
- [ ] Export CSV

## Deliverable
User can classify images and export results.

## Dependencies
EPIC 7

---

# 📌 EPIC 9 — Detection & Segmentation

## Tasks

### Face Detection
- [ ] Implement MTCNN or Haar cascade
- [ ] Draw bounding boxes

### Object Detection
- [ ] Integrate YOLOv8
- [ ] Draw boxes + labels
- [ ] Add confidence slider

### Segmentation
- [ ] Integrate SAM
- [ ] Click-to-segment
- [ ] Display mask overlay

### Viewer
- [ ] Add overlay layer system
- [ ] Toggle overlays on/off

## Deliverable
User can detect and visualize objects.

## Dependencies
EPIC 8

---

# 📌 EPIC 10 — Style Transfer

## Tasks

### Fast Styles
- [ ] Implement preset styles

### Advanced
- [ ] AdaIN style transfer
- [ ] Custom style image upload

### Controls
- [ ] Style strength slider
- [ ] Content preservation slider

### Output
- [ ] Resolution selector
- [ ] Preview vs full render

## Deliverable
User can stylize images.

## Dependencies
EPIC 9

---

# 📌 EPIC 11 — Generative AI

## Tasks

### Core
- [ ] Text-to-image
- [ ] Image-to-image

### Editing
- [ ] Inpainting (mask tool)
- [ ] Outpainting

### Enhancement
- [ ] Upscaling (Real-ESRGAN)

### Control
- [ ] ControlNet integration

### Architecture
- [ ] Abstract service layer (local vs remote)

## Deliverable
User can generate and modify images using AI.

## Dependencies
EPIC 10

---

# 📌 EPIC 12 — 3D Mesh (Optional)

## Tasks
- [ ] Integrate image → 3D model (TripoSR)
- [ ] Render preview (basic viewer)
- [ ] Export (.obj, .glb, .ply)

## Deliverable
Experimental 3D generation module.

## Dependencies
EPIC 11

---

# 📌 EPIC 13 — Settings & Persistence

## Tasks
- [ ] Implement `QSettings`
- [ ] Save:
  - [ ] theme
  - [ ] last opened files
  - [ ] window layout
  - [ ] preferred device
- [ ] Load settings on startup

## Deliverable
Persistent user preferences.

## Dependencies
EPIC 4

---

# 📌 EPIC 14 — Performance Optimization

## Tasks
- [ ] Generate preview thumbnails
- [ ] Separate preview vs full-res pipeline
- [ ] Optimize image conversions
- [ ] Lazy-load models
- [ ] Cache models

## Deliverable
Responsive app even on large images.

## Dependencies
EPIC 6+

---

# 📌 EPIC 15 — Error Handling

## Tasks
- [ ] Handle invalid images
- [ ] Handle large images
- [ ] Handle missing models
- [ ] Handle GPU errors
- [ ] Add user-friendly dialogs
- [ ] Log detailed errors

## Deliverable
App does not crash under edge cases.

## Dependencies
All previous

---

# 📌 EPIC 16 — Testing

## Tasks
- [ ] Unit tests for processors
- [ ] Unit tests for utils
- [ ] Integration tests (load → edit → save)
- [ ] Manual test scenarios

## Deliverable
Stable, tested application.

## Dependencies
EPIC 5+

---

# 📌 EPIC 17 — Packaging (Windows)

## Tasks
- [ ] Configure PyInstaller
- [ ] Add assets and icons
- [ ] Bundle dependencies
- [ ] Test `.exe` on clean system
- [ ] Fix missing DLLs/plugins

## Deliverable
Standalone Windows executable.

## Dependencies
Stable core app (EPIC 5+)

---

# 🚀 MVP Definition

## Must-have for first release
- [ ] Image loading
- [ ] Image viewer (zoom/pan)
- [ ] Crop / Resize / Rotate
- [ ] Brightness / Contrast
- [ ] Blur / Sharpen
- [ ] Histogram
- [ ] EXIF metadata
- [ ] Export
- [ ] Undo/Redo

---

# 🧭 Suggested Execution Order

1. EPIC 0 → 3 (foundation)
2. EPIC 4 (file handling)
3. EPIC 5 (editing)
4. EPIC 6 (analysis)
5. EPIC 7 (workers)
6. EPIC 8+ (AI features)
7. EPIC 17 (packaging)

---

# 🧠 Key Rule

> Do NOT implement AI-heavy features before the core image workflow is stable.

---

# 📅 Suggested 4-Week Plan

## Week 1
- EPIC 0–2

## Week 2
- EPIC 3–5

## Week 3
- EPIC 6–7

## Week 4
- Polish + MVP completion

---

# ✅ Success Criteria

- App runs as `.exe`
- UI is responsive
- Image editing is smooth
- No crashes under normal usage
- Clear structure for future AI expansion