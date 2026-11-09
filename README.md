# Bell Schedule Modeler

A single-page, self-contained HTML tool for modeling and comparing school bell schedules. Open `index.html` in a browser; there is nothing to build or install.

## Contents

| Path | What it is |
|---|---|
| `index.html` | The app. |
| `school-models/` | Schedule models for 14 peer schools, as JSON the app can import. Rebuilt from `build_models.py`. See [`school-models/README.md`](school-models/README.md) for the rules and per-school choices. |
| `Hotchkiss_Proposals/` | Hotchkiss schedule models, also importable JSON: the current schedule (status quo) and three proposals (block waterfall; block waterfall with a morning flex; block waterfall minimizing back-to-back class). Each has a 2-hour Co-curricular block (its own type, not class time) starting 5 minutes after the last block on Monday, Tuesday, Thursday and Friday of both weeks. |

## Using the models

Open `index.html`, click **Import**, and choose either `school-models/all-schools.json` (every school at once) or a single school's file, or one of the Hotchkiss proposals.

The school models are export version 1. The app now exports version 4. Version 2 added each model's own types (with default lengths and a "counts as class time" flag) and notes on types, blocks and single placements; version 3 added student groups; version 4 adds blocks each student attends only some meetings of. Older files still import with the same totals:
- each model gets Class, Lunch and Other, plus Advisory and Break only if one of its blocks uses them, and each type takes the most common length among its blocks;
- each model gets the four default student groups, with every block for all students;
- every block counts every meeting.

## Splits

Click a split's ≡ tab to open **Split options**. Its lane list shows each lane's blocks, left to right. **◀** and **▶** move a lane left or right, for example to make Lane 3 into Lane 2. Lane order only changes how the split is drawn (on screen and in the PDF): lanes are alternatives, so no total changes. Each row also has **Keep only** and, with more than two lanes, **Remove**.

**Matching blocks are drawn once.** When neighboring lanes hold the same block at the same start and end times (and the same note for that day, or none), the calendar and the PDF draw it as one wide block across those lanes. This is display only: each lane still has its own placement, so totals are counted exactly as before. Clicking (or dragging) a merged block picks the copy in the lane under the pointer and shows the copies separately again while it's selected. Changing one copy's time or length makes them stop matching, so they're drawn separately.

## Types

Every model has three fixed types, **Class**, **Lunch** and **Other**, which can't be renamed or deleted. A new model starts with only those three. Every other type, including Advisory and Break in older models, belongs to that model and can be renamed or deleted; deleting one moves its blocks to a type you pick (Other by default).

## Student groups

Some blocks are only for some students, such as a Senior class meeting or Prep Human Development. Each model has its own student groups, listed in the **Student groups** panel:

- **Defaults:** a model starts with **Prep, LM, UM and Senior**, each ticked as a grade. You can rename or delete them.
- **Your own groups:** add plain groups, such as Athlete or Musician. Leave **Is a grade** unticked for groups that cut across grades.
- **Combined groups:** add groups such as Underclassmen = Prep + LM.

A block is for **All students** unless you tick groups under **Who attends** in its settings. Tagging a block with a combined group makes it for every member. A block for only some groups shows a short group label and a corner tab on the calendar, and its hover card says who it's for.

### How a group's totals are worked out

- **Each plain group:** its day is the blocks for all students plus the blocks tagged for it.
- **Skipped blocks:** a block it skips counts as **Free time**, not passing time. Passing periods stay passing.
- **Splits:** a group is in the lanes holding a block tagged for it. Failing that, it's in the lanes with a block it attends, or with no tagged block at all. If every lane holds only blocks tagged for other groups, it isn't in the split, and the split's full length is Free time for it.
- **Transitions and the longest run:** these count only the blocks the group attends. A free stretch of 30 minutes or more ends a run.
- **Combined groups:** the total is the lowest to highest of the members. **All students** is the lowest to highest of the groups ticked as grades. With no grades, All students counts every block as if it were for everyone.
- **Blocks only some students have:** a block that only some groups (or some lanes) have counts only the students who have it, and is marked ◐.

With nothing tagged, every group's totals equal the totals before groups existed.

### Where to see them

- **Ledger and week headers:** these show All students.
- **Groups tab:** a column for every group, over two weeks or one week, with **Export CSV…**.
- **Compare:** **Student groups** checkboxes add a row per group under each measure. Groups are matched across models by name.

## Blocks students attend only some of

Some blocks repeat through the week, but each student is assigned to only some of the meetings. HD in the Morning Flex proposal has 16 placements, 8 of them on each student's schedule, but a student attends one a week. In a block's settings, set **Each student attends** to **Only some**, then a number **per week** or **per two weeks**. The block then shows a label such as "1/wk" or "1/2wk".

- **What counts:** totals count that many meetings for each student, or all of them where a student has fewer. The counted minutes go to the block, its type and class time. The other meetings go on the **Free time** line.
- **Per week:** each week counts up to the number.
- **Per two weeks:** the two weeks together count up to the number, so each week shows a range (the meetings could fall in either week).
- **Day headers:** they show a range. The low end assumes the student skips that day's meeting and the high end that they attend it. When the number covers every meeting a student has, every meeting counts.
- **Transitions and the longest run:** these still count every meeting, since any of them could be the one a student attends.
- **Meeting length:** if the meetings have different lengths, each counts as the block's average length.
- **With student groups:** the limit applies within each group's own day.

## Exports, downloads and the PDF

- **Export** gives one model or all models as JSON (to share or re-import with **Import**), the bell schedule and totals as CSV, and totals by student group as CSV. **Copy** works everywhere.
- **Download:** on your own computer the browser saves the file at once. In the published version (a claude.ai page) Claude first asks the person to confirm the file name and size; saying no saves nothing.
- **PDF** (top bar) saves the current model's Week 1 and Week 2 as a two-page US Letter landscape PDF, laid out like the Schedule tab and showing the whole schedule. It shows each week's class time, passing and Free time, each day's class time and hours, and every block with its times, colors, split lanes and group or "1/wk" labels. The PDF maker (jsPDF) loads from cdnjs the first time, so it needs an internet connection. Characters outside its font, such as emoji, print as "?".
- **Print** appears only on your own computer: a published claude.ai page can't open the print dialog. Use **PDF** there instead.

## Published version

The modeler is published as a claude.ai page: <https://claude.ai/artifact/VbB7uEsZZxXeVuoUnfYb13>. It's private until it is shared from the page's Share menu.

- **Saving:** each person's schedules are saved in their own browser, as with `index.html`. Nobody sees anyone else's, and a private window or cleared site data starts over, so keep downloaded JSON files as backups. To share a model, download its JSON from Export and send it; the other person uses Import.
- **Starting models:** someone opening it for the first time starts with the four Hotchkiss models, Deerfield, and the two built-in samples. People who have used it before keep their own saved models, even after an update. To pick up updated starting models they can Import the new files, or use **Start over**, which replaces every model saved in their browser with the current starting models (after offering to download them all first).
- **Downloads:** the page is published with the `downloads` capability, so Download and PDF work there through Claude's save prompt for people signed in to Claude. People who aren't signed in (or are in a private window) don't get the save prompt, so those buttons are hidden for them; Copy in Export still works. Print is not available there.

### Updating it

1. Make the change in `index.html` (and the model files, if the starting models should change).
2. Run `python build_artifact.py`. It writes `dist/bell-schedule-modeler.html` (the page to publish, without the outer page tags claude.ai adds itself) and `dist/preview.html` (the same page with those tags, to try on this computer). `dist/` is not kept in git.
3. Republish `dist/bell-schedule-modeler.html` to the same link, keeping the `downloads` capability. Asking Claude Code to "republish the bell schedule modeler to its artifact" does this.

## Not in the repo

`ScheduleDocs/` (the source PDFs and screenshots the peer-school models were built from) is kept locally and listed in `.gitignore`.
