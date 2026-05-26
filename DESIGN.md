---
name: IPS3608 Remote Control
description: Desktop instrument UI for the FNIRSI IPS3608 programmable bench power supply.
colors:
  instrument-ink: "#0F1B2A"
  instrument-panel: "#F4F6F8"
  instrument-white: "#FFFFFF"
  panel-seam: "#D7DEE6"
  console-slate: "#4A5A6A"
  hover-surface: "#EBF2FB"
  voltage-blue: "#0B84F3"
  ampere-green: "#00A86B"
  critical-red: "#EF4444"
  watt-gold: "#F59E0B"
  active-green: "#22C55E"
  active-green-deep: "#16A34A"
  stop-red: "#DC2626"
  transitional-yellow: "#EAB308"
  fault-orange: "#F97316"
typography:
  reading:
    fontFamily: "DSEG7 Classic, monospace"
    fontSize: "42px"
    fontWeight: 400
    lineHeight: 1
  unit:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1
  headline:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "10pt"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "1px"
rounded:
  card: "12px"
  panel: "8px"
  button: "6px"
  input: "5px"
spacing:
  xs: "2px"
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "16px"
components:
  button-base:
    backgroundColor: "{colors.instrument-white}"
    textColor: "{colors.instrument-ink}"
    rounded: "{rounded.button}"
    padding: "6px 10px"
  button-base-hover:
    backgroundColor: "{colors.hover-surface}"
    textColor: "{colors.instrument-ink}"
    rounded: "{rounded.button}"
    padding: "6px 10px"
  button-output-start:
    backgroundColor: "{colors.active-green-deep}"
    textColor: "{colors.instrument-white}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
    height: "56px"
  button-output-stop:
    backgroundColor: "{colors.stop-red}"
    textColor: "{colors.instrument-white}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
    height: "56px"
  metric-card:
    backgroundColor: "{colors.instrument-white}"
    rounded: "{rounded.card}"
    padding: "10px 8px"
---

# Design System: IPS3608 Remote Control

## 1. Overview

**Creative North Star: "The Measurement Console"**

This is instrument software, not application software. The model is the front panel of a professional bench rack unit rendered on screen: every element occupies its exact position, no element is decorative, and the reading is always the most prominent thing visible. The engineer using this app has one question at any given moment: *what is the device doing right now?* The interface answers that question without asking the user to look for it.

The palette is deliberately cool and low-saturation except where it carries semantic meaning. The background (`#F4F6F8`) is not white — it is the color of a brushed-aluminum bezel. The text (`#0F1B2A`) is not black — it has enough blue-shift to read as precision rather than ink. Color is reserved for data channels and operational state. When something is blue, green, red, or amber, there is a reason. The system rejects the idea that more color means more engagement.

This system explicitly refuses three failure modes: the SaaS dashboard with gradient metric cards and icon navigation, the consumer app ported from mobile with oversized touch targets, and the 2000s instrument software with embossed 3D borders and a toolbar crammed with 24px icons. The reference is the best of modern precision instrument UIs: Tektronix 5 Series, newer Keysight PathWave. Dense but organized. Authoritative but quiet.

**Key Characteristics:**
- Flat surfaces, 1px panel borders, no elevation shadows
- Channel colors (Voltage Blue, Ampere Green, Watt Gold, Critical Red) are the only saturated color on screen — and each maps exclusively to one physical quantity
- DSEG7 Classic 7-segment font for all live readings, giving the visual weight of physical display hardware
- Four operational states (Disconnected, Connecting, Connected, Error) each have a distinct color signature that is never ambiguous
- Information density is high; layout rhythm creates scannable order, not reduction

## 2. Colors: The Channel Palette

Four measurement channels, each with a permanent color identity. State colors are semantic and binary. Neutrals carry the surface.

### Primary

- **Instrument Ink** (`#0F1B2A`): The dominant text color. Near-black with a deliberate blue-navy undertone — reads as precision, not editorial ink. Used for all body text, panel titles, control labels, and numeric setpoints.

- **Voltage Blue** (`#0B84F3`): Exclusive to the Voltage channel. Used in the Voltage MetricCard value, unit label, sparkline, and the graph's V curve. Never used for state, navigation, or decoration.

- **Ampere Green** (`#00A86B`): Exclusive to the Current channel. Same logic as Voltage Blue: all Current channel representations use this color and only this color.

### Secondary

- **Critical Red** (`#EF4444`): Dual role. (1) The Temperature channel color in the MetricCard. (2) The error and disconnected state indicator color. These two uses do not conflict because temperature readings are visible only when connected; error states appear only when not connected or when a fault occurs.

- **Watt Gold** (`#F59E0B`): Exclusive to the Power channel. Calculated from V×I; displayed in the fourth MetricCard only.

### Tertiary

- **Active Green** (`#22C55E` / deep `#16A34A`): Operational state: connected, output ON, datalogger running. The deep variant (`#16A34A`) is used as the solid background of active action buttons (START OUTPUT, START LOG). The lighter `#22C55E` is used for status dot indicators. These are not channel colors — they communicate that the system is actively doing something the user requested.

- **Transitional Yellow** (`#EAB308`): The "Connecting..." state exclusively. Appears as status dot and button background tint. Temporary by definition; never lingers.

- **Fault Orange** (`#F97316`): Communication error state — distinct from Critical Red to avoid conflation with the Temperature channel. Tells the user the link to the device has failed, not that the device is overheating.

### Neutral

- **Instrument Panel** (`#F4F6F8`): The main window background. Cool gray with a fractional blue tint. Not white — the slight tint prevents the surface from competing with `#FFFFFF` widget backgrounds and gives the whole app the cool, matte quality of aluminum panel material.

- **Instrument White** (`#FFFFFF`): Widget surfaces: GroupBoxes, MetricCards, buttons (base state), spinboxes, tables. The contrast against Instrument Panel creates panel depth without shadow.

- **Panel Seam** (`#D7DEE6`): Borders on all containment elements — GroupBoxes, cards, inputs, table grid lines. Fine enough to read as a seam or separator, not a frame.

- **Console Slate** (`#4A5A6A`): Secondary text: MetricCard channel titles, setpoint annotations, delta labels, status log body text. Muted but readable. Never used for primary labels.

- **Hover Surface** (`#EBF2FB`): Button hover background. Slightly blue-tinted to signal affordance without changing the button's shape or border.

### Named Rules

**The Channel Monopoly Rule.** Each measurement channel color belongs to exactly one physical quantity. Voltage Blue appears in the Voltage card, the voltage graph curve, and nowhere else. Never use Voltage Blue for a "primary accent," a hyperlink, or a highlight that isn't directly about voltage. The same rule applies to Ampere Green, Watt Gold, and the temperature role of Critical Red. Collision with state colors is architecturally prevented: state colors (Active Green, Stop Red, Fault Orange) are spectrally distinct from channel colors.

**The Stop-Red Boundary Rule.** `#DC2626` (Stop Red) and `#EF4444` (Critical Red) are different colors with different roles. Stop Red is for actions that halt something (STOP OUTPUT button, error state indicator). Critical Red is for the Temperature channel. Do not substitute one for the other.

## 3. Typography

**Reading Font:** DSEG7 Classic (monospace fallback)
**Body/UI Font:** Segoe UI (system-ui, sans-serif fallback)

**Character:** DSEG7 Classic carries the visual authority of physical 7-segment instrument displays. Every live measurement is rendered in it — the engineer reads V, I, P, and T the same way they'd read a standalone DMM. Segoe UI handles everything else: it is the instrument's label printer, not its display. The pairing is not decorative; it is functional differentiation between data and annotation.

### Hierarchy

- **Reading** (DSEG7 Classic, 400, 42px, lh 1): Live measurement values in MetricCards. The largest text on the screen. Rendered in the channel color. No other text uses DSEG7.

- **Unit** (Segoe UI, 600, 16px, lh 1): Channel unit labels (V, A, W, °C) aligned to the bottom of the Reading. Rendered in channel color, smaller than the value, larger than all annotation text.

- **Headline** (Segoe UI, 700, 13px, lh 1.3): Output status label ("Output ON" / "Output OFF"). Panel-level prominence. Used sparingly — only where the operational state of a control group needs labeling.

- **Body** (Segoe UI, 400, 10pt, lh 1.4): All control labels, spinbox labels, ComboBox entries, menu items, status bar text, log panel entries. The default for everything not explicitly elevated.

- **Label** (Segoe UI, 600, 11px, ls 1px): MetricCard channel titles (VOLTAGE, CURRENT, TEMPERATURE, POWER), setpoint annotations, delta values, GroupBox titles. Uppercase letter-spacing signals annotation, not primary content.

### Named Rules

**The DSEG7 Exclusivity Rule.** DSEG7 Classic is used for live measurement values and nothing else. Not for setpoint inputs. Not for routine step parameters. Not for log timestamps. The 7-segment aesthetic earns its authority by being rare. Overusing it dilutes the signal.

## 4. Elevation

This system is flat. No drop shadows, no blur layers, no tonal ramp surfaces. Depth is created entirely through the contrast between Instrument Panel (`#F4F6F8`) background and Instrument White (`#FFFFFF`) widget surfaces, divided by Panel Seam (`#D7DEE6`) borders.

The MetricCard, the GroupBox, the LogTableDock — none of them cast shadows. They read as panels mounted flush to the instrument face, separated by seams, not stacked in space. This matches the physical metaphor: a rack instrument's front panel does not have a z-axis.

### Named Rules

**The Seam-Not-Shadow Rule.** When a containment element needs visual separation from its neighbors, add a `1px solid {panel-seam}` border. Never add `box-shadow`. The rare exception: if a floating dialog or dock widget needs to communicate that it sits above the main surface, a subtle ambient shadow (`0 4px 16px rgba(15, 27, 42, 0.10)`) is permitted. Modal overlays use a dark scrim, not blur.

## 5. Components

### MetricCard

The signature component. Four instances — one per measurement channel — occupy the lower-left quadrant of the application. Each card is self-contained: it owns the channel's color, the live reading, the setpoint reference, the delta, and a 60-sample sparkline history.

- **Shape:** Gently curved corners (12px radius), `1px solid {panel-seam}` border, no shadow
- **Background:** Instrument White (`#FFFFFF`)
- **Internal padding:** 10px horizontal, 8px vertical
- **Channel Title:** Label style, uppercase, Console Slate (`#4A5A6A`), 1px letter-spacing
- **Reading:** DSEG7 Classic 42px in channel color
- **Unit:** 16px, 600 weight, channel color, bottom-aligned to Reading
- **Setpoint annotation:** 11px, Console Slate, `"Set {value} {unit}"` format
- **Delta:** 11px, Active Green Deep (`#16A34A`) when within 5% tolerance, Stop Red (`#DC2626`) when outside
- **Sparkline:** 28px height, channel color, 1.5px line, 60-sample window, no axes
- **Fan indicator (Temperature card only):** `◌ FAN` / `⊙ FAN` in top-right of title row; inactive state is Console Slate, active state is Voltage Blue (`#0B84F3`) at 700 weight

### Buttons

Two behavioral families: base controls and output action buttons.

**Base controls** (Refresh, Export CSV, View Table, Manage, etc.):
- Shape: Slightly curved (6px radius)
- Default: Instrument White bg, Instrument Ink text, 1px Panel Seam border, 600 weight, `6px 10px` padding
- Hover: Hover Surface (`#EBF2FB`) bg, border and text unchanged
- No icon-only buttons. Label always present.

**Output action button** (START OUTPUT / STOP OUTPUT):
- Shape: 8px radius, no border
- Minimum height: 56px; font 13px Bold
- START state: Active Green Deep (`#16A34A`) bg, white text, `▶ START OUTPUT` label
- STOP state: Stop Red (`#DC2626`) bg, white text, `■ STOP OUTPUT` label
- The button is the full-width call-to-action for the Output Control panel. Its color changes entirely between states — not just tinted, replaced.

**Connection button** (contextual, 4 states):
- Connected: Instrument White bg tinted `#dcfce7`, Dark Green (`#166534`) text, `#86efac` border — "Disconnect"
- Disconnected: `#fee2e2` bg, Dark Red (`#991b1b`) text, `#fca5a5` border — "Connect"
- Connecting: `#fef9c3` bg, Dark Amber (`#a16207`) text, `#fde047` border — "Connect" (disabled)
- Communication Error: `#fed7aa` bg, Dark Amber-Orange (`#b45309`) text, `#fb923c` border — "Connect"

### Inputs and SpinBoxes

- Style: Instrument White bg, `1px solid {panel-seam}` border, 5px radius, `4px` padding
- Text: Instrument Ink, Body style
- No custom focus ring defined in current implementation — inherits system default. Future: `1px solid {voltage-blue}` focus ring without glow (instrument precision, not web affordance).
- Suffix labels (` V`, ` A`, ` °C`) are rendered inline by QDoubleSpinBox — treat as part of the input, not a trailing label.

### GroupBox Panels

The primary layout containers. Each panel groups a functional domain (Connection, Output Control, Datalogger, Realtime Readings, Realtime Graphs, Status).

- Shape: 8px radius border, `1px solid {panel-seam}`
- Background: Instrument White
- Title: Segoe UI, 700 weight, Instrument Ink, rendered above the top border edge via Qt's `subcontrol-origin: margin` mechanism
- Spacing from main window background creates visual panel separation without shadow

### Status Log Panel

- One-line summary bar: reads current state across all dimensions (connection, output, datalogger, samples, last data, last command, last error)
- Log text area: read-only, max 110px height, Body style, timestamps in `[HH:MM:SS]` format
- The summary line is the instrument's status register. It never shows a spinner, a toast, or an animated state; it shows a string.

### Datalogger Running Banner

When logging is active, a full-width banner appears:
- Background: `#dcfce7` (light green)
- Text: `#14532d` (dark green), `"DATALOGGING IN CORSO"`
- Border: `1px solid #86efac`
- Border-radius: 6px
- This is the only green used in the Datalogger panel — it communicates "this is running and recording." When stopped, the banner disappears entirely.

### Log Table Dock

- Docked right, closable, floatable
- Table: alternating row colors, no edit, single-row selection
- Column widths fixed: Timestamp 160px, V/I/P 90px each, Temperature 120px
- Numeric columns right-aligned
- No row header

## 6. Do's and Don'ts

### Do:

- **Do** use channel colors exclusively for their assigned physical quantity. Voltage Blue for voltage only. Ampere Green for current only. Watt Gold for power only. Critical Red for temperature (and error states that are architecturally separated from temperature display).
- **Do** render all live measurement values in DSEG7 Classic at 42px in the channel color. The 7-segment weight is the visual authority of the reading.
- **Do** use `1px solid #D7DEE6` as the only border treatment. No colored left-side accent stripes, no thick borders as decoration, no dashed dividers.
- **Do** use the four state colors (Active Green, Stop Red, Transitional Yellow, Fault Orange) consistently for their states. An engineer reading the connection button should know immediately whether the device is live, stopped, negotiating, or broken — color is load-bearing here.
- **Do** keep MetricCards at 12px radius, GroupBoxes at 8px, buttons at 6px, inputs at 5px. The tighter radius on interactive controls versus display containers is intentional — containers hold data, controls require precision clicks.
- **Do** keep the Instrument Panel background (`#F4F6F8`) distinct from Instrument White (`#FFFFFF`). The slight cool tint on the background creates panel depth without shadow. Never replace `#F4F6F8` with `#FFFFFF`.
- **Do** set the delta label green (`#16A34A`) when within ±5% of setpoint, red (`#DC2626`) when outside. This is the only per-reading state color in the card.
- **Do** ensure every state communicated by color is also communicated by text or icon. Status dot color plus a text label. Delta sign (+/−) plus delta color. Fan symbol (◌/⊙) plus color.

### Don't:

- **Don't** build a SaaS dashboard. No gradient metric cards. No icon-only sidebar navigation. No hero metric with a big number and a decorative gradient arc. This is instrument software, not a Notion clone.
- **Don't** use old-school instrument styling: no 3D embossed borders, no raised/sunken bevel effects, no toolbar rows packed with 16px icon buttons. The reference is current-generation precision instruments, not 2003 LabVIEW.
- **Don't** bring consumer or mobile patterns onto this desktop surface: no floating action buttons, no bottom navigation bar, no oversized tap targets, no Material Design Android affordances.
- **Don't** add drop shadows. The elevation model is flat-by-default. If a floating element genuinely needs to read as elevated (modal dialog, floating dock), use a single ambient shadow (`0 4px 16px rgba(15,27,42,0.10)`) — nothing larger, darker, or colorful.
- **Don't** use DSEG7 Classic for anything other than live measurement values. Not for setpoint inputs, not for timestamps, not for decorative numeric displays.
- **Don't** introduce a new saturated color without assigning it a permanent semantic role. The system currently uses exactly four channel colors and four state colors. A ninth color added without a clear assignment dilutes the encoding.
- **Don't** use `border-left` or `border-right` greater than 1px as a colored accent stripe on cards, list items, or callout boxes. Rewrite with a full border, a background tint, or nothing.
- **Don't** use gradient text (`background-clip: text` with a gradient). Measurement values are always a single solid channel color.
- **Don't** use the word "dashboard" to describe this interface internally or externally. It is a control panel.
