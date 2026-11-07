# MakeitDoc

> An open, account-free document and creative utility studio built for everyday productivity.

---

## Problem Statement

Nothing really — as an engineer, why pay for subscriptions, endure intrusive ads, or rely on third-party SaaS platforms with artificial file limits and paywalls (no hate to existing tools) when I can build my own clean, private, and capable platform? 

MakeitDoc was built from scratch to be the single place where I can convert, edit, organize, and sketch without accounts, watermarks, or hidden paywalls.

---

## About The Project

**MakeitDoc** is a web-based productivity and document utility studio designed with an *Editorial Utility Studio* aesthetic. It combines robust document-processing engines with creative canvas tools into a unified, minimal interface.

Everything runs on clean, ephemeral processing — files are handled in-memory and temporary sandboxes, converted or edited, and served straight back to the user without storing personal data.

---

## Features

### 📄 PDF Suite
* **Merge PDF** — Combine multiple PDF files into a single, cohesive document (supports up to 100 MB and 300 pages).
* **Split PDF** — Extract specific page ranges (e.g., `1-5`) or split every page into an organized `.zip` archive.
* **Rotate PDF** — Reorient misaligned document pages by 90°, 180°, or 270° with deflation for compact file sizes.
* **Compress PDF** — Optimize heavy PDFs with customizable image compression profiles (Low, Medium, High).
* **Protect PDF** — Secure sensitive documents with industry-standard AES-256 bit encryption and custom passwords.

---

### 🔄 Document Conversions
* **Word to PDF** — Convert `.docx` Microsoft Word documents into clean, universally readable PDF files with a dual-engine architecture (LibreOffice with native AbiWord fallback).
* **PDF to Word** — Extract and transform structured PDF documents back into fully editable `.docx` files.
* **Image to PDF** — Convert and compile multiple JPG/PNG images into a standardized PDF with custom margins, orientation, and A4 or original sizing.

---

### 🎨 Creative Studio & Workspace
* **Image Editor** — Browser-based photo manipulation tool with cropping, brightness/contrast adjustments, resizing, text annotations, and instant export.
* **Collage Maker** — Arrange multiple images into responsive grid and mosaic collages with custom canvas ratios, border radius, and spacing controls.
* **Quick Notes** — A visual whiteboard canvas inspired by modern creative studios. Draw, sketch, drop shapes and sticky notes, format typography, and export directly to PNG, SVG, or JSON.

---

### ⚡ Design & Architecture Highlights
* **Zero Friction**: No sign-ups, logins, or cookies required — open any tool and start working immediately.
* **Editorial Utility System**: Purpose-built typography hierarchy (Instrument Sans, DM Sans, and IBM Plex Mono) paired with a nature-inspired forest green design palette.
* **Dark & Light Mode**: Complete, contrast-conscious theming that respects system preferences and persists across sessions.
* **Privacy by Design**: Files are processed in isolated temporary workspaces and immediately cleared from the server after download.
* **Full Mobile & Desktop Responsiveness**: Fluid sidebar drawer, live keyboard shortcuts (`⌘K` / `Ctrl+K` search), and adaptable controls across all screen sizes.
