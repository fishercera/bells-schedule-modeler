# Bell Schedule Modeler

A single-page, self-contained HTML tool for modeling and comparing school bell schedules. Open `index.html` in a browser; there is nothing to build or install.

## Contents

| Path | What it is |
|---|---|
| `index.html` | The app. |
| `school-models/` | Schedule models for 14 peer schools, as JSON the app can import. Rebuilt from `build_models.py`. See [`school-models/README.md`](school-models/README.md) for the rules and per-school choices. |
| `Hotchkiss_Proposals/` | Proposed Hotchkiss schedule models (block waterfall, and block waterfall with a morning flex), also importable JSON. |

## Using the models

Open `index.html`, click **Import**, and choose either `school-models/all-schools.json` (every school at once) or a single school's file, or one of the Hotchkiss proposals.

The school models are export version 1. The app now exports version 2, which adds each model's own types (with default lengths and a "counts as class time" flag) and notes on types, blocks and single placements. Version 1 files still import with the same totals: each model gets Class, Lunch and Other, plus Advisory and Break only if one of its blocks uses them, and each type takes the most common length among its blocks.

## Types

Every model has three fixed types, **Class**, **Lunch** and **Other**, which can't be renamed or deleted. A new model starts with only those three. Every other type, including Advisory and Break in older models, belongs to that model and can be renamed or deleted; deleting one moves its blocks to a type you pick (Other by default).

## Not in the repo

`ScheduleDocs/` (the source PDFs and screenshots the peer-school models were built from) is kept locally and listed in `.gitignore`.
