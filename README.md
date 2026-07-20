# MirrorPace

A personal AI running coach that builds a persistent digital twin of a single athlete over time.

Not a chatbot over Strava data — a model that understands the athlete, follows their evolution, and helps make better training decisions.

---

## Current phase

**Phase 1 — Data Engine**

Transforming raw FIT and GPX files into reliable normalized activity objects.

---

## Architecture

```
Data Engine → Runner Intelligence → Activity Intelligence → Runner Model → Knowledge Engine → Coach Agent
```

See `docs/` for detailed documentation on vision, architecture, and decisions.

---

## Setup

```bash
uv sync
uv run pytest
```

---

## Data

Raw activity files (FIT, GPX) are **not versioned**. Place your Strava archive in `data/raw/strava/`:

```
data/
  raw/
    strava/
      fit/    ← .fit files
      gpx/    ← .gpx files
```

The `data/` directory is gitignored to keep personal GPS and fitness data off GitHub.
