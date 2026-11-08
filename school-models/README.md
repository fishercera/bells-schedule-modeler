# Peer school models

Import `all-schools.json` with the app's **Import** button to add every school at once, or import a single school's file. Models are rebuilt from `build_models.py`, which holds each schedule as published and checks that every model reproduces those times exactly.

Class minutes per week (from the app's own totals):

| School | Week 1 | Week 2 | Source |
|---|---|---|---|
| Phillips Academy Andover | 1,330 | 1,330 | PDF p. 1 |
| Phillips Exeter, Spring 2026 | 1,600 | 1,550 | PDF p. 2 |
| Phillips Exeter, Winter 2025–26 | 1,800 | 1,800 | PDF p. 3 |
| The Hill School | 1,386 | 1,386 | PDF p. 4 |
| Peddie (Blue / Gold weeks) | 1,475 | 1,325 | PDF p. 5 |
| Choate Rosemary Hall, 2023–24 | 1,365 | 1,365 | PDF p. 6 |
| Deerfield | 1,260 | 1,260 | PDF p. 7 |
| St. Paul's School (A / B weeks) | 1,290 | 1,290 | PDF pp. 8–9 |
| Northfield Mount Hermon (CMAP) | 1,240 | 1,240 | PDF p. 12 |
| Berkshire, 2026–27 | 1,380 | 1,245 | PDF p. 13 |
| Westminster, 2026–27 | 1,470 | 1,470 | PDF p. 14 |
| Blair Academy | 1,440 | 1,440 | blair.edu calendar, Nov 9–21, 2026 |
| St. Andrew's School, 2026–27 | 1,320 | 1,320 | standrews-de.org/academics |
| Taft, 2026–27 | 1,260 | 1,260 | Taft website screenshot |

Loomis Chaffee (PDF pp. 10–11) was left out on request.

Transitions and the longest run of class blocks (from the app's own totals):

- A **transition** is each move from one block to the next in a student's day, including 0-minute passing. Arriving and leaving don't count. A range means it depends on the student's lane.
- The **longest run** is the most class blocks in a row that any student has over the two weeks. A run ends at a block that isn't class time, or at a gap of 30 minutes or more. Its length in minutes runs from the start of the first block to the end of the last.
- **Some lanes only** means only students in some lanes of a split have a run that long.

| School | Transitions, Week 1 | Transitions, Week 2 | Longest run (blocks) | Run length | |
|---|---|---|---|---|---|
| Phillips Academy Andover | 22 | 22 | 5 | 4h | |
| Phillips Exeter (Spring 2026) | 43 | 43 | 2 | 1h 50m | |
| Phillips Exeter (Winter 2025-26) | 45 | 45 | 2 | 1h 50m | |
| The Hill School | 30 | 30 | 3 | 2h 38m | |
| Peddie (Blue/Gold weeks) | 32 | 30 | 3 | 2h 50m | |
| Choate Rosemary Hall (2023-24) | 27 | 27 | 3 | 3h 35m | |
| Deerfield | 24 | 24 | 2 | 2h 5m | |
| St. Paul's School (A/B weeks) | 39 | 39 | 3 | 3h | Some lanes only |
| Northfield Mount Hermon (CMAP) | 35–36 | 35–36 | 2 | 2h 30m | |
| Berkshire (2026-27) | 34 | 32 | 3 | 3h 5m | |
| Westminster (2026-27) | 26 | 26 | 3 | 3h 40m | |
| Blair Academy | 31 | 30 | 4 | 4h 30m | Some lanes only |
| St. Andrew's School (2026-27) | 29 | 29 | 3 | 3h 20m | |
| Taft (2026-27) | 24 | 24 | 2 | 2h 30m | |

Two rows were checked by hand against the published times:

- **Taft:** Week 1 is Mon 5, Tue 5, Wed 1, Thu 6, Fri 5 and Sat 2, for 24 transitions. Week 2 is 5, 5, 3, 6, 5 and 0 (Saturday is Taft Time only), also 24. Its longest run is 2 blocks. Thursday's C (9:05) and D (to 11:35) run 2h 30m, and so do Week 2 Wednesday's C and D. On Monday, Lunch splits each lane's run into two of 2 blocks or fewer.
- **Deerfield:** each Monday, Tuesday, Thursday and Friday has 6 items, so 5 transitions, and each Wednesday has 4, for 24 a week. Its longest run is Wednesday's Block 2 and Block 3, 10:25–12:30, which is 2 blocks and 2h 5m. On every other day a meeting, lunch or flex time separates the blocks.

## Rules used for every school

- Only the academic day is modeled: from the first scheduled item to the last class, meeting or extra-help slot. Afternoon athletics, dinner, evening clubs and study hall are left out.
- Letter, number and "Period" blocks are **Class**. Lunch and Jummah are **Lunch**. Advising and advisory are **Advisory**. Labelled free time is **Break**. Assemblies, chapel, meetings, office hours, flex and conference time are **Other**.
- A labelled gap between two timed items (for example "Break" or "Universal Free") is filled with a block of that name. An unlabelled gap counts as passing time.
- A schedule with only one week is copied into both Week 1 and Week 2.
- Handwritten numbers on the PDF pages are notes, not schedule data, and were ignored.

## School-specific choices

- **Andover:** Periods marked (L) contain lunch, but no lunch time is printed, so there is no Lunch block. Lunch shows as 0.
- **Exeter (both terms):** PE1–PE5 and Sports/Rehearsals overlap the letter blocks and are left out. Wednesday Week 1 and Week 2 differ as printed. Spring Wednesday Week 2 "Office Hours" is placed in the 12:20–1:10 slot. Wednesday lunch has no end time, so it is left out. Winter's 3:30–4:00 gap (PE4/FG sports) is a Break.
- **Hill:** Friday "Student Meeting" is read as 1:43–2:30; the start time is faint on the scan.
- **Peddie:** Blue week is Week 1 and Gold week is Week 2. "Conf./Lunch" counts as Lunch. "DM/X" is Other.
- **Choate:** The 2023–24 schedule. The early and late lunch waves are lanes. "Conference" fills the unlabelled 10:35–11:05 slot.
- **St. Paul's:** A week is Week 1, using the handwritten letters. The B-week page prints only the lunch-wave letters (C, A, F, B), so its other class slots are named "B-week class". Class totals are right, but per-letter totals for B week are not.
- **Northfield Mount Hermon:** Wednesday 1 and Wednesday 2 are Weeks 1 and 2. The C1/C2 waves are lanes, with lunch in the free half. The E block (4:05–5:45, arts, athletics and cocurriculars) is Other, not Class. On Wednesdays the 11:00–1:30 lunch window runs alongside BD* or the All-School Meeting, so lunch and passing show ranges.
- **Berkshire:** First and second lunch are lanes. Week 2 Saturday is "Programming" (Other). The schedule alternates by the effective weeks listed on the page.
- **Westminster:** Friday and Saturday rotate over three weeks. The model uses that rotation's Weeks 1 and 2, so Friday/Saturday Week 3 (Blocks 4–7 and 2–3) is not represented, and some blocks get slightly more time than in a full three-week cycle.
- **Blair:** The calendar repeats every two weeks. Week 1 is Nov 9–14, 2026 (Saturday classes), and Week 2 is Nov 16–21 (no Saturday classes). Each split block (C1/C2 and so on) is lunch-wave lanes, with lunch filling the rest of each wave, because lunch times aren't listed. Asterisked blocks (for example "H Block*") are treated as the plain block.
- **St. Andrew's:** "H Block / Meetings" counts as Class.
- **Taft:** The 15 "ABCDE in Rotation" slots each week are filled A→E in time order, so each of A–E meets three times for 70 minutes. The real order isn't published, but every block's total is the same either way. Week 1 uses the regular Wednesday and Saturday, and Week 2 uses Alt. Wednesday and Alt. Saturday (each pairing has exactly 15 slots). "F or Lunch" / "G or Lunch" are lanes, so a student has one of F or G and lunch in the other slot.
