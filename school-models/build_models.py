"""Build Bell Schedule Modeler models for peer schools.

Each school is written as its published times. The script turns those times into the
app's model format (default lengths, passing gaps, lunch-wave lanes), then rebuilds the
times from the model and checks they match what was entered.

Run:  python build_models.py
Writes one .json per school plus all-schools.json (import that one to get every school).
"""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DAYS = {"Sun": 0, "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}
CLASS_HUES = [212, 158, 32, 340, 268, 95, 12, 240, 186, 130, 300]
CAT_HUES = {"lunch": 52, "advisory": 300, "break": 130, "other": 186}


def t(s):
    """'8:30' -> minutes after midnight. School-day hours below 7 are afternoon."""
    h, m = map(int, s.split(":"))
    if h < 7:
        h += 12
    return h * 60 + m


def lanes(*ls):
    return ("lanes", list(ls))


def parse(entry):
    m = re.match(r"^(\d{1,2}:\d{2})-(\d{1,2}:\d{2}) (.+)$", entry)
    if not m:
        raise ValueError(f"Bad entry: {entry!r}")
    name, _, cat = m.group(3).partition("|")
    return t(m.group(1)), t(m.group(2)), name.strip(), cat.strip() or None


def guess_cat(name):
    n = name.lower()
    if "lunch" in n or "jummah" in n:
        return "lunch"
    if "advis" in n:
        return "advisory"
    if "break" in n or "free" in n:
        return "break"
    if re.match(r"^(period \d+|block \d+|[a-z]\+?\*?|[a-z] block\*?|\d)$", n):
        return "class"
    return "other"


def build(school):
    blocks, order = {}, []

    def block_for(name, cat):
        if name not in blocks:
            blocks[name] = {"name": name, "cat": cat or guess_cat(name), "durs": []}
            order.append(name)
        elif cat and blocks[name]["cat"] != cat:
            raise ValueError(f"{school['name']}: {name} has two types")
        return blocks[name]

    days = [{"start": 480, "items": [], "_entries": []} for _ in range(14)]
    for key, entries in school["days"].items():
        weeks = [0, 1] if key[0] == "*" else [int(key[0]) - 1]
        dow = DAYS[key[-3:]]
        for w in weeks:
            days[w * 7 + dow]["_entries"] = entries

    gaps_seen = Counter()
    for day in days:
        prev_end = None
        for e in day["_entries"]:
            if isinstance(e, tuple):
                ls = [[parse(x) for x in lane] for lane in e[1]]
                s0 = min(lane[0][0] for lane in ls)
                item = {"t": "s", "gap": 0 if prev_end is None else s0 - prev_end, "lanes": []}
                for lane in ls:
                    out, p = [], s0
                    for (s, en, name, cat) in lane:
                        b = block_for(name, cat)
                        b["durs"].append(en - s)
                        out.append({"t": "b", "name": name, "dur": en - s, "gap": s - p})
                        p = en
                    item["lanes"].append(out)
                end = max(lane[-1][1] for lane in ls)
                start = s0
            else:
                s, end, name, cat = parse(e)
                b = block_for(name, cat)
                b["durs"].append(end - s)
                item = {"t": "b", "name": name, "dur": end - s, "gap": 0 if prev_end is None else s - prev_end}
                start = s
            if prev_end is None:
                day["start"] = start
            else:
                if item["gap"] < 0:
                    raise ValueError(f"{school['name']}: overlap before {e}")
                if item["gap"] > 0:  # back-to-back items don't say what passing time is
                    gaps_seen[item["gap"]] += 1
            day["items"].append(item)
            prev_end = end

    passing = gaps_seen.most_common(1)[0][0] if gaps_seen else 5
    hue_i = 0
    out_blocks, ids = [], {}
    for i, name in enumerate(order):
        b = blocks[name]
        if b["cat"] == "class":
            hue = CLASS_HUES[hue_i % len(CLASS_HUES)]
            hue_i += 1
        else:
            hue = CAT_HUES[b["cat"]]
        ids[name] = f"b{i + 1}"
        out_blocks.append({"id": ids[name], "name": name, "cat": b["cat"],
                           "len": Counter(b["durs"]).most_common(1)[0][0], "hue": hue, "target": None})
    lens = {b["name"]: b["len"] for b in out_blocks}

    n = 0

    def item_json(it, first_in_lane=False, top_first=False):
        nonlocal n
        n += 1
        default_gap = 0 if (first_in_lane or top_first) else passing
        gap = None if it["gap"] == default_gap else it["gap"]
        if top_first:
            gap = None
        if it["t"] == "s":
            return {"id": f"i{n}", "t": "s", "gap": gap,
                    "lanes": [[item_json(x, first_in_lane=(j == 0)) for j, x in enumerate(l)] for l in it["lanes"]]}
        return {"id": f"i{n}", "t": "b", "blockId": ids[it["name"]],
                "dur": None if it["dur"] == lens[it["name"]] else it["dur"], "gap": gap}

    class_lens = [b["len"] for b in out_blocks if b["cat"] == "class"]
    model = {
        "name": school["name"], "passing": passing,
        "defaultStart": Counter(d["start"] for d in days if d["items"]).most_common(1)[0][0],
        "blockLen": Counter(class_lens).most_common(1)[0][0] if class_lens else 50,
        "classTarget": None, "blocks": out_blocks,
        "days": [{"start": d["start"], "items": [item_json(x, top_first=(k == 0)) for k, x in enumerate(d["items"])]} for d in days],
    }
    check(model, days, school["name"])
    return model


def check(model, days, name):
    """Lay the model out the way the app does and compare with the entered times."""
    blocks = {b["id"]: b for b in model["blocks"]}

    def dur(it):
        if it["t"] == "s":
            return max(seq_len(l, False) for l in it["lanes"])
        return it["dur"] if it["dur"] is not None else blocks[it["blockId"]]["len"]

    def gap(it, i, top):
        if i == 0:
            return 0 if top else (it["gap"] or 0)
        return it["gap"] if it["gap"] is not None else model["passing"]

    def layout(items, t0, top):
        out, tt = [], t0
        for i, it in enumerate(items):
            s = tt + gap(it, i, top)
            e = s + dur(it)
            out.append((it, s, e))
            tt = e
        return out

    def seq_len(items, top):
        L = layout(items, 0, top)
        return L[-1][2] if L else 0

    def flat(items, t0, top):
        res = []
        for it, s, e in layout(items, t0, top):
            if it["t"] == "s":
                res.append(("split", [flat(l, s, False) for l in it["lanes"]]))
            else:
                res.append((s, e, blocks[it["blockId"]]["name"]))
        return res

    for d, (md, src) in enumerate(zip(model["days"], days)):
        want = []
        for e in src["_entries"]:
            if isinstance(e, tuple):
                want.append(("split", [[parse(x)[:3] for x in lane] for lane in e[1]]))
            else:
                want.append(parse(e)[:3])
        got = flat(md["items"], md["start"], True)
        if got != want:
            raise AssertionError(f"{name}, day {d}: model does not reproduce the source times\n{got}\n{want}")


# ---------------------------------------------------------------------------
# Schools. Keys: "*Mon" = both weeks, "1Mon" = Week 1 only, "2Mon" = Week 2 only.
# ---------------------------------------------------------------------------
SCHOOLS = []

SCHOOLS.append({"name": "Phillips Academy Andover", "file": "phillips-andover", "days": {
    "*Mon": ["8:30-9:10 Period 1", "9:20-10:00 Period 2", "10:05-10:45 Conference", "10:50-11:30 Period 3",
             "11:40-12:20 Period 4", "12:30-1:10 Period 5", "1:20-2:00 Period 6", "2:10-2:50 Period 7"],
    "*Tue": ["8:30-9:45 Period 3", "9:55-10:35 Advising", "10:45-12:00 Period 4", "12:10-1:25 Period 5", "1:35-2:50 Period 6"],
    "*Wed": ["8:30-9:45 Period 1", "9:50-10:15 Conference", "10:20-11:35 Period 2", "11:45-1:00 Period 7"],
    "*Thu": ["8:30-9:45 Period 3", "9:50-10:40 Department Meeting", "10:45-12:00 Period 4", "12:10-1:25 Period 5", "1:35-2:50 Period 6"],
    "*Fri": ["8:30-9:45 Period 1", "9:55-11:10 Period 2", "11:20-12:20 Community Meeting Time",
             "12:25-1:25 Protected Time/Team Meetings", "1:35-2:50 Period 7"],
}})

EXETER_WED = {
    "1Wed": ["8:00-8:50 A", "9:00-9:50 C", "10:00-10:30 Meditation", "10:40-11:10 Advising", "11:20-12:10 E", "12:20-1:10 G"],
}
SCHOOLS.append({"name": "Phillips Exeter (Spring 2026)", "file": "phillips-exeter-spring-2026", "days": {
    "*Mon": ["8:00-8:50 T", "9:00-9:50 B", "10:00-10:40 Assembly", "10:50-11:40 C", "11:50-12:40 D",
             "12:40-1:40 Lunch", "1:40-2:30 E", "2:30-3:00 Universal Free", "3:00-3:50 Y", "3:50-4:20 Universal Free", "4:20-5:10 G"],
    "*Tue": ["8:00-8:50 U", "9:00-9:50 A", "10:00-10:40 Faculty Meeting", "10:50-11:40 D", "11:50-12:40 C",
             "12:40-1:40 Lunch", "1:40-2:30 E", "2:30-3:00 Universal Free", "3:00-3:50 F", "3:50-4:20 Universal Free", "4:20-5:10 G"],
    **EXETER_WED,
    "2Wed": ["8:00-8:50 D", "9:00-9:50 B", "10:00-10:30 Meditation", "10:40-11:10 Advising", "11:20-12:10 F", "12:20-1:10 Office Hours"],
    "*Thu": ["8:00-8:50 V", "9:00-9:50 D", "10:00-10:40 Department Meeting", "10:50-11:40 A", "11:50-12:40 B",
             "12:40-1:40 Lunch", "1:40-2:30 X", "2:30-3:00 Office Hours", "3:00-3:50 F", "4:00-4:50 G"],
    "*Fri": ["8:00-8:50 W", "9:00-9:50 C", "10:00-10:40 Assembly", "10:50-11:40 B", "11:50-12:40 A",
             "12:40-1:40 Lunch and Jummah|lunch", "1:40-2:30 E", "2:40-3:30 F", "3:30-4:20 Office Hours", "4:20-5:10 Z"],
}})

SCHOOLS.append({"name": "Phillips Exeter (Winter 2025-26)", "file": "phillips-exeter-winter-2025-26", "days": {
    "*Mon": ["8:00-8:50 T", "9:00-9:50 B", "10:00-10:40 Core Values Project", "10:50-11:40 C", "11:50-12:40 D",
             "12:40-1:40 Lunch", "1:40-2:30 E", "2:40-3:30 F", "3:30-4:00 Sports/PE break|break", "4:00-4:50 G", "5:00-5:50 Q"],
    "*Tue": ["8:00-8:50 U", "9:00-9:50 A", "10:00-10:40 Faculty Meeting", "10:50-11:40 D", "11:50-12:40 C",
             "12:40-1:40 Lunch", "1:40-2:30 E", "2:40-3:30 F", "3:30-4:00 Sports/PE break|break", "4:00-4:50 Z", "5:00-5:50 H"],
    **EXETER_WED,
    "2Wed": ["8:00-8:50 D", "9:00-9:50 B", "10:00-10:30 Meditation", "10:40-11:10 Advising", "11:20-12:10 F", "12:20-1:10 H"],
    "*Thu": ["8:00-8:50 V", "9:00-9:50 D", "10:00-10:40 Department Meeting", "10:50-11:40 A", "11:50-12:40 B",
             "12:40-1:40 Lunch", "1:40-2:30 X", "2:40-3:30 F", "3:30-4:00 Sports/PE break|break", "4:00-4:50 G", "5:00-5:50 H"],
    "*Fri": ["8:00-8:50 W", "9:00-9:50 C", "10:00-10:40 Assembly", "10:50-11:40 B", "11:50-12:40 A",
             "12:40-1:40 Lunch and Jummah|lunch", "1:40-2:30 E", "2:40-3:30 Y", "3:30-4:00 Sports/PE break|break", "4:00-4:50 G", "5:00-5:50 H"],
}})

SCHOOLS.append({"name": "The Hill School", "file": "hill-school", "days": {
    "*Mon": ["8:25-9:13 A", "9:20-10:08 B", "10:08-10:22 Break", "10:22-11:10 C", "11:17-12:05 D",
             "12:15-12:45 Adviser Lunch|lunch", "12:52-1:40 E", "1:47-2:35 F", "2:42-3:30 G"],
    "*Tue": ["8:25-9:40 D", "9:47-10:12 Chapel", "10:19-11:34 A", "11:44-12:14 Lunch", "12:21-1:36 B",
             "1:43-2:08 Office Hours", "2:15-3:30 C"],
    "*Wed": ["8:25-9:40 E", "9:47-11:02 F", "11:02-11:17 Break", "11:17-12:32 G", "12:42-1:12 Lunch", "1:19-2:19 Club Meeting"],
    "*Thu": ["8:25-9:40 B", "9:47-10:12 Advisory", "10:19-11:34 C", "11:44-12:14 Lunch", "12:21-1:36 D",
             "1:43-2:08 Office Hours", "2:15-3:30 A"],
    "*Fri": ["8:25-9:40 G", "9:47-10:12 Chapel", "10:19-11:34 E", "11:44-12:14 Lunch", "12:21-1:36 F",
             "1:43-2:30 Student Meeting"],
}})

SCHOOLS.append({"name": "Peddie (Blue/Gold weeks)", "file": "peddie", "days": {
    "1Mon": ["8:30-9:20 A", "9:30-10:20 B", "10:25-10:45 Chapel", "10:45-11:15 Conference", "11:20-12:35 C",
             "12:35-1:20 Lunch", "1:20-2:10 D", "2:20-3:10 E"],
    "1Tue": ["8:00-9:15 F", "9:30-10:20 G", "10:25-11:15 DM/X", "11:20-12:35 A", "12:35-1:45 Conference/Lunch|lunch", "1:45-2:35 B"],
    "1Wed": ["8:30-9:20 D", "9:30-10:20 C", "10:25-11:15 Community Meeting/Advisory|advisory", "11:20-12:35 E",
             "12:35-1:20 Lunch", "1:20-2:10 G", "2:20-3:10 F"],
    "1Thu": ["8:00-9:15 B", "9:30-10:20 A", "10:25-11:15 DM/X", "11:20-12:35 D", "12:35-1:45 Conference/Lunch|lunch", "1:45-2:35 C"],
    "1Fri": ["8:30-9:20 E", "9:30-10:20 B", "10:25-10:45 Chapel", "10:45-11:15 Conference", "11:20-12:35 G",
             "12:35-1:20 Lunch", "1:20-2:10 F", "2:20-3:10 A"],
    "1Sat": ["8:30-9:20 C", "9:30-10:20 D", "10:30-11:20 E"],
    "2Mon": ["8:30-9:20 F", "9:30-10:20 G", "10:25-10:45 Chapel", "10:45-11:15 Conference", "11:20-12:35 A",
             "12:35-1:20 Lunch", "1:20-2:10 B", "2:20-3:10 C"],
    "2Tue": ["8:00-9:15 D", "9:30-10:20 E", "10:25-11:15 DM/X", "11:20-12:35 F", "12:35-1:45 Conference/Lunch|lunch", "1:45-2:35 G"],
    "2Wed": ["8:30-9:20 B", "9:30-10:20 A", "10:25-11:15 Community Meeting/Advisory|advisory", "11:20-12:35 C",
             "12:35-1:20 Lunch", "1:20-2:10 E", "2:20-3:10 D"],
    "2Thu": ["8:00-9:15 G", "9:30-10:20 F", "10:25-11:15 DM/X", "11:20-12:35 B", "12:35-1:45 Conference/Lunch|lunch", "1:45-2:35 A"],
    "2Fri": ["8:30-9:20 C", "9:30-10:20 G", "10:25-10:45 Chapel", "10:45-11:15 Conference", "11:20-12:35 E",
             "12:35-1:20 Lunch", "1:20-2:10 D", "2:20-3:10 F"],
}})


def choate_split(x):
    return lanes(["11:05-11:45 Lunch", f"11:45-12:50 {x}"], [f"11:05-12:10 {x}", "12:10-12:50 Lunch"])


SCHOOLS.append({"name": "Choate Rosemary Hall (2023-24)", "file": "choate", "days": {
    "*Mon": ["8:15-9:20 A", "9:30-10:35 B", "10:35-11:05 Conference", choate_split("C"), "1:00-2:05 D", "2:15-3:20 E"],
    "*Tue": ["8:15-9:20 F", "9:35-10:25 School Meeting", "10:25-11:05 Conference", choate_split("G"), "1:00-2:05 A", "2:15-3:20 B"],
    "*Wed": ["8:15-9:20 E", "9:30-10:35 C", "10:45-11:50 D", "12:00-12:50 Student Programming/Faculty Collaboration"],
    "*Thu": ["8:00-8:50 Faculty/Department Meetings", "9:00-10:05 G", "10:15-11:20 F",
             lanes(["11:30-12:10 Lunch", "12:10-1:15 A"], ["11:30-12:35 A", "12:35-1:15 Lunch"]),
             "1:25-2:30 B", "2:40-3:30 Advising"],
    "*Fri": ["8:15-9:20 C", "9:30-10:35 D", "10:35-11:05 Conference", choate_split("E"), "1:00-2:05 F", "2:15-3:20 G"],
}})

DEERFIELD = lambda a, mtg, b, lunch, c: [f"8:30-10:00 Block {a}", f"10:05-10:50 {mtg}", f"10:55-12:25 Block {b}",
                                          f"12:40-1:15 {lunch}", f"1:20-2:50 Block {c}", "2:55-3:40 Flex Time"]
DEERFIELD_WED = lambda a, b, c: [f"8:30-9:30 Block {a}", "9:40-10:20 School Meeting", f"10:25-11:25 Block {b}",
                                 f"11:30-12:30 Block {c}", "12:35-1:30 Walk-Through Lunch"]
SCHOOLS.append({"name": "Deerfield", "file": "deerfield", "days": {
    "1Mon": DEERFIELD(1, "Faculty Meeting", 2, "Sit-Down Lunch", 3),
    "1Tue": DEERFIELD(4, "Extra Help", 5, "Advisory Sit-Down Lunch|lunch", 6),
    "1Wed": DEERFIELD_WED(1, 2, 3),
    "1Thu": DEERFIELD(4, "Department Meetings", 5, "Sit-Down Lunch", 6),
    "1Fri": DEERFIELD(1, "Advisory Meetings", 2, "Sit-Down Lunch", 3),
    "2Mon": DEERFIELD(4, "Faculty Meeting", 5, "Sit-Down Lunch", 6),
    "2Tue": DEERFIELD(1, "Extra Help", 2, "Advisory Sit-Down Lunch|lunch", 3),
    "2Wed": DEERFIELD_WED(4, 5, 6),
    "2Thu": DEERFIELD(1, "Department Meetings", 2, "Sit-Down Lunch", 3),
    "2Fri": DEERFIELD(4, "Advisory Meetings", 5, "Sit-Down Lunch", 6),
}})


def sps_split(x, start="11:15", mid="12:00", end="12:45"):
    return lanes([f"{start}-{mid} {x}", f"{mid}-{end} Lunch"], [f"{start}-{mid} Lunch", f"{mid}-{end} {x}"])


SPS_DAY = lambda a, b, split, c, last: ["8:00-8:25 Office Hours", "8:30-8:55 Chapel", f"9:05-9:50 {a}", "9:55-10:20 Flex/Office Hours",
                                         f"10:25-11:10 {b}", sps_split(split), f"12:50-2:10 {c}", f"2:15-3:00 {last}"]
UNL = "B-week class|class"
SCHOOLS.append({"name": "St. Paul's School (A/B weeks)", "file": "st-pauls", "days": {
    "1Mon": SPS_DAY("A", "B", "C", "D", "E"),
    "1Tue": SPS_DAY("F", "D", "A", "C", "Dept/College Meetings"),
    "1Wed": ["8:00-8:45 Meetings", "8:50-10:10 B", "10:15-11:00 E", "11:05-11:30 Flex/Office Hours", "11:35-12:20 C"],
    "1Thu": ["8:00-8:45 Faculty Meetings", "8:50-9:15 Chapel", "9:25-10:10 B", "10:15-10:40 Flex/Office Hours", "10:45-11:30 A",
             sps_split("F", "11:35", "12:20", "1:05"), "1:10-2:30 E", "2:35-3:15 House Meetings"],
    "1Fri": SPS_DAY("C", "E", "B", "F", "D"),
    "1Sat": ["8:30-9:50 A", "9:55-10:40 D", "10:45-11:10 Flex/Office Hours", "11:15-12:00 F"],
    "2Mon": SPS_DAY(UNL, UNL, "C", UNL, UNL),
    "2Tue": SPS_DAY(UNL, UNL, "A", UNL, "Dept/College Meetings"),
    "2Wed": ["8:00-8:45 Advising Team Meetings|other", f"8:50-10:10 {UNL}", f"10:15-11:00 {UNL}", "11:05-11:30 Flex/Office Hours", f"11:35-12:20 {UNL}"],
    "2Thu": ["8:00-8:25 Office Hours", "8:30-8:55 Chapel", f"9:05-9:50 {UNL}", "9:55-10:20 Flex/Office Hours", f"10:25-11:10 {UNL}",
             sps_split("F"), f"12:50-2:10 {UNL}", "2:15-3:15 Advising Meetings"],
    "2Fri": SPS_DAY(UNL, UNL, "B", UNL, UNL),
    "2Sat": [f"8:30-9:50 {UNL}", f"9:55-10:40 {UNL}", "10:45-11:10 Flex/Office Hours", f"11:15-12:00 {UNL}"],
}})

NMH_CSPLIT = lanes(["12:10-1:20 C", "1:20-1:50 Lunch"], ["12:00-12:40 Lunch", "12:40-1:50 C"])
NMH_DAY = lambda first, mid, advising: [f"8:00-8:40 {first}", "8:50-10:00 A", f"10:10-10:40 {mid}", "10:50-12:00 B", NMH_CSPLIT,
                                         f"2:00-2:20 {advising}", "2:25-3:35 D", "4:05-5:45 E (arts, athletics, cocurriculars)|other"]
SCHOOLS.append({"name": "Northfield Mount Hermon (CMAP)", "file": "northfield-mount-hermon", "days": {
    "*Mon": NMH_DAY("Extra Help", "All School Meeting", "Individual Advising"),
    "*Tue": NMH_DAY("Extra Help", "Flexible (activities vary)", "Individual Advising"),
    "1Wed": ["8:00-8:40 Flexible (activities vary)", "8:50-9:50 A", "10:00-11:00 B+",
             lanes(["11:10-12:10 BD*", "12:10-1:30 Lunch"], ["11:00-1:30 Lunch"])],
    "2Wed": ["8:00-8:40 Flexible (activities vary)", "8:50-9:50 C", "10:00-11:00 D+",
             lanes(["11:10-12:10 All-School Meeting", "12:10-1:30 Lunch"], ["11:00-1:30 Lunch"])],
    "*Thu": NMH_DAY("Extra Help", "Campus/Dorm Meeting", "Group Advising"),
    "*Fri": NMH_DAY("Extra Help", "Student Leader Meeting", "Individual Advising"),
}})


def bk_split(x):
    return lanes([f"11:15-12:00 {x}", "12:00-12:40 Lunch"], ["11:15-11:55 Lunch", f"11:55-12:40 {x}"])


SCHOOLS.append({"name": "Berkshire (2026-27)", "file": "berkshire", "days": {
    "1Mon": ["8:00-8:25 Office Hours", "8:30-9:15 E", "9:20-10:10 School Meeting", "10:20-11:05 G", bk_split("C"), "12:50-2:05 A", "2:15-3:00 D"],
    "1Tue": ["8:00-8:25 Office Hours", "8:30-9:15 F", "9:20-9:45 Form/House Meeting", "9:50-11:05 B", bk_split("D"), "12:50-2:05 C", "2:15-3:00 G"],
    "1Wed": ["8:15-8:55 Faculty Meeting", "9:00-9:45 A", "9:55-10:40 E", "10:50-11:35 F", "11:35-12:30 Advisory Lunch|lunch"],
    "1Thu": ["8:00-8:25 Office Hours", "8:30-9:15 B", "9:20-9:45 School Assembly", "9:50-11:05 E", bk_split("G"), "12:50-2:05 F", "2:15-3:00 A"],
    "1Fri": ["8:00-8:25 Office Hours", "8:30-9:15 C", "9:20-9:45 Advisory", "9:50-11:05 D", bk_split("B"), "12:50-2:05 G", "2:15-3:00 E"],
    "1Sat": ["9:00-9:45 D", "9:55-10:40 B", "10:50-11:35 C"],
    "2Mon": ["8:00-8:25 Office Hours", "8:30-9:15 F", "9:20-10:10 School Meeting", "10:20-11:05 A", bk_split("E"), "12:50-2:05 B", "2:15-3:00 D"],
    "2Tue": ["8:00-8:25 Office Hours", "8:30-9:15 G", "9:20-9:45 Dept/Club Meeting", "9:50-11:05 C", bk_split("F"), "12:50-2:05 A", "2:15-3:00 B"],
    "2Wed": ["8:15-8:55 Faculty Meeting", "9:00-9:45 E", "9:55-10:40 C", "10:50-11:35 G", "11:35-12:30 Advisory Lunch|lunch"],
    "2Thu": ["8:00-8:25 Office Hours", "8:30-9:15 D", "9:20-9:45 School Assembly", "9:50-11:05 F", bk_split("A"), "12:50-2:05 E", "2:15-3:00 C"],
    "2Fri": ["8:00-8:25 Office Hours", "8:30-9:15 A", "9:20-9:45 Advisory", "9:50-11:05 G", bk_split("B"), "12:50-2:05 D", "2:15-3:00 F"],
    "2Sat": ["9:00-11:35 Programming"],
}})

WM_FRI = lambda a, b, c, d: [f"8:20-9:30 Block {a}", "9:35-10:05 Chapel", f"10:10-11:20 Block {b}",
                             "11:25-12:30 Buffet Lunch/Meetings|lunch", f"12:35-1:45 Block {c}", f"1:50-3:00 Block {d}"]
WM_SAT = lambda a, b: [f"8:20-9:30 Block {a}", f"9:35-10:45 Block {b}", "10:50-11:30 Meetings", "11:30-1:00 Buffet Lunch"]
SCHOOLS.append({"name": "Westminster (2026-27)", "file": "westminster", "days": {
    "*Mon": ["8:20-9:30 Block 1", "9:35-10:30 Faculty Meeting", "10:35-11:45 Block 2", "11:50-12:30 Family-Style Lunch",
             "12:35-1:45 Block 3", "1:50-3:00 Block 4"],
    "*Tue": ["8:20-9:30 Block 5", "9:35-10:30 Chapel and Advisory|advisory", "10:35-11:45 Block 6", "11:50-12:30 Family-Style Lunch",
             "12:35-1:45 Block 7", "1:50-3:00 Block 1"],
    "*Wed": ["8:20-9:30 Block 2", "9:35-10:45 Block 3", "10:50-12:00 Block 4", "12:00-1:00 Buffet Lunch"],
    "*Thu": ["8:20-9:30 Block 5", "9:35-10:30 Speaker Block|other", "10:35-11:45 Block 6", "11:50-12:30 Advisory Lunch|lunch",
             "12:35-1:45 Block 7", "1:50-3:00 Block 1"],
    "1Fri": WM_FRI(2, 3, 4, 5), "1Sat": WM_SAT(6, 7),
    "2Fri": WM_FRI(6, 7, 2, 3), "2Sat": WM_SAT(4, 5),
}})


def blair_split(x, a1, a2, b1, b2):
    """Blair lists two waves of a block (x1 and x2); lunch fills the other part of each wave."""
    return lanes([f"{a1}-{a2} {x} Block", f"{a2}-{b2} Lunch"], [f"{a1}-{b1} Lunch", f"{b1}-{b2} {x} Block"])


SCHOOLS.append({"name": "Blair Academy", "file": "blair", "days": {
    "1Mon": ["8:30-9:30 A Block", "9:40-10:40 B Block", "10:45-11:25 School Meeting", blair_split("C", "11:30", "12:30", "12:30", "1:30"),
             "1:35-2:10 Conference Block", "2:15-3:15 D Block"],
    "1Tue": ["8:30-9:30 E Block", "9:40-10:40 F Block", "10:45-11:10 Conference Block", blair_split("G", "11:15", "12:15", "11:55", "12:55"),
             "1:05-2:05 H Block", "2:15-3:15 C Block"],
    "1Wed": ["8:30-9:30 H Block", "9:40-10:40 D Block", "10:50-11:50 E Block", blair_split("A", "12:00", "1:00", "12:30", "1:30"),
             "1:35-2:00 Chapel"],
    "1Thu": ["8:30-9:30 Faculty Meeting & PD", "9:40-10:40 G Block", "10:45-11:10 Student Clubs",
             blair_split("F", "11:15", "12:15", "11:55", "12:55"), "1:05-2:05 B Block", "2:15-3:15 A Block"],
    "1Fri": ["8:30-9:30 D Block", "9:40-10:40 C Block", "10:45-11:20 Conference Block", blair_split("H", "11:25", "12:25", "12:30", "1:30"),
             "1:40-2:40 E Block", "2:45-3:15 School Meeting"],
    "1Sat": ["8:30-9:30 B Block", "9:40-10:40 F Block", "10:50-11:50 G Block"],
    "2Mon": ["8:30-9:30 A Block", "9:40-10:40 B Block", "10:45-11:10 School Meeting", blair_split("C", "11:15", "12:15", "11:55", "12:55"),
             "1:05-2:05 D Block", "2:15-3:15 H Block"],
    "2Tue": ["8:30-9:30 E Block", "9:40-10:40 F Block", "10:45-11:10 Conference Block", blair_split("G", "11:15", "12:15", "11:55", "12:55"),
             "1:05-2:05 B Block", "2:15-3:15 C Block"],
    "2Wed": ["8:30-9:30 H Block", "9:40-10:40 D Block", "10:50-11:50 E Block", blair_split("A", "12:00", "1:00", "12:30", "1:30"),
             "1:40-2:40 G Block", "2:45-3:15 Chapel"],
    "2Thu": ["8:30-9:30 C Block", "9:40-10:40 G Block", "10:45-11:10 Student Clubs",
             blair_split("F", "11:15", "12:15", "11:55", "12:55"), "1:05-2:05 B Block", "2:15-3:15 A Block"],
    "2Fri": ["8:30-9:30 D Block", "9:40-10:40 F Block", "10:45-11:20 Conference Block", blair_split("H", "11:25", "12:25", "12:30", "1:30"),
             "1:40-2:40 E Block", "2:45-3:15 School Meeting"],
}})

SCHOOLS.append({"name": "St. Andrew's School (2026-27)", "file": "st-andrews", "days": {
    "*Mon": ["8:30-9:30 A", "9:40-10:40 B", "10:50-11:50 C", "11:50-12:35 Lunch", "12:40-1:40 D", "1:50-2:50 E", "2:55-3:25 Extra Help"],
    "*Tue": ["8:30-9:30 F", "9:40-10:40 G", "10:50-11:50 A", "11:50-12:35 Lunch", "12:40-1:40 B", "1:50-2:50 H Block/Meetings|class", "2:55-3:25 Extra Help"],
    "*Wed": ["8:30-9:30 C", "9:40-10:40 D", "10:50-12:35 Long Lunch", "12:40-1:40 E", "1:50-2:50 F", "2:55-3:25 Extra Help"],
    "*Thu": ["8:30-9:30 G", "9:40-10:40 A", "10:50-11:50 B", "11:50-12:35 Advisory Lunch|lunch", "12:40-1:40 C", "1:50-2:50 School Meeting", "2:55-3:25 Extra Help"],
    "*Fri": ["8:30-9:30 D", "9:40-10:40 E", "10:50-11:50 Orchestra/Faculty", "11:50-12:35 Lunch", "12:40-1:40 F", "1:50-2:50 G", "2:55-3:25 SPARK"],
}})


def taft():
    """Taft: 15 'ABCDE in Rotation' slots a week, so A-E meet three times each.
    The published grid doesn't give the order, so letters cycle A->E through the slots in time order.
    Week 1 uses the regular Wednesday and Saturday; Week 2 uses Alt. Wednesday and Alt. Saturday
    (each pairing gives exactly 15 slots)."""
    R = "ROT"
    fg = lambda x, y: lanes([f"11:20-12:30 {x}", "12:35-1:45 Lunch"], ["11:20-12:30 Lunch", f"12:35-1:45 {y}"])
    week = {
        "Mon": [f"8:15-9:25 {R}", "9:30-10:00 Advisory", f"10:05-11:15 {R}", fg("F", "G"), f"1:50-3:00 {R}"],
        "Tue": [f"8:15-9:25 {R}", "9:30-10:00 School Meeting", f"10:05-11:15 {R}", fg("G", "F"), f"1:50-3:00 {R}"],
        "Thu": ["8:00-8:50 Faculty PLC", f"9:05-10:15 {R}", f"10:25-11:35 {R}", "11:40-12:10 Community Lunch",
                "12:15-12:55 Community Flex", "1:05-1:45 Faculty Flex", f"1:50-3:00 {R}"],
        "Fri": [f"8:15-9:25 {R}", "9:30-10:00 Grade Meetings", f"10:05-11:15 {R}", fg("F", "G"), f"1:50-3:00 {R}"],
    }
    variants = {
        1: {"Wed": [f"8:15-9:25 {R}", "9:30-12:00 Taft Time"],
            "Sat": [f"9:00-10:10 {R}", "10:15-10:35 Assembly", f"10:40-11:50 {R}"]},
        2: {"Wed": [f"8:15-9:25 {R}", "9:30-9:50 Assembly", f"9:55-11:05 {R}", f"11:15-12:25 {R}"],
            "Sat": ["9:00-11:30 Taft Time"]},
    }
    days = {}
    for w in (1, 2):
        i = 0
        for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat"):
            out = []
            for e in week.get(d) or variants[w][d]:
                if isinstance(e, str) and e.endswith(R):
                    e = e[:-len(R)] + "ABCDE"[i % 5]
                    i += 1
                out.append(e)
            days[f"{w}{d}"] = out
        assert i == 15, f"Taft week {w} has {i} rotation slots"
    return {"name": "Taft (2026-27)", "file": "taft", "days": days}


SCHOOLS.append(taft())


def main():
    models = []
    for s in SCHOOLS:
        m = build(s)
        models.append(m)
        with open(os.path.join(HERE, f"{s['file']}.json"), "w", encoding="utf-8") as f:
            json.dump({"app": "bell-schedule-modeler", "version": 1, "models": [m]}, f, indent=1)
    with open(os.path.join(HERE, "all-schools.json"), "w", encoding="utf-8") as f:
        json.dump({"app": "bell-schedule-modeler", "version": 1, "models": models}, f, indent=1)
    for m in models:
        print(f"{m['name']}: {len(m['blocks'])} blocks, passing {m['passing']}, default length {m['blockLen']}")


if __name__ == "__main__":
    main()
