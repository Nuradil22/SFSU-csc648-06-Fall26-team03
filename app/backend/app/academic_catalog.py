"""Curated SFSU Computer Science course records for recommendation validation.

A hand-checked subset of the official SFSU Academic Bulletin 2026-2027
(https://bulletin.sfsu.edu/courses/csc/), used to:

1. Give both comparison models the same verified academic reference data.
2. Flag recommendations whose course code, title, or prerequisite claims do
   not match the record.

This is a subset, not the whole catalog. A recommendation whose course is not
listed here is reported as "unverified", never silently treated as real.
"""

import re

# code -> {"title", "units", "prerequisites" (short official summary),
#          "prereq_codes" (course codes appearing in the prerequisite rule)}
CATALOG: dict[str, dict] = {
    "CSC 101": {"title": "Introduction to Computing", "units": 3,
                "prerequisites": "None", "prereq_codes": []},
    "CSC 110": {"title": "Computational Thinking and Quantitative Reasoning", "units": 3,
                "prerequisites": "None", "prereq_codes": []},
    "CSC 215": {"title": "Intermediate Computer Programming", "units": 4,
                "prerequisites": "CSC 101 with a grade of C or better",
                "prereq_codes": ["CSC 101"]},
    "CSC 220": {"title": "Data Structures", "units": 3,
                "prerequisites": "CSC 210 or CSC 215 with a grade of C or better",
                "prereq_codes": ["CSC 210", "CSC 215"]},
    "CSC 221": {"title": "Data Structure Lab", "units": 1,
                "prerequisites": "CSC 210 or CSC 215; concurrent enrollment in CSC 220",
                "prereq_codes": ["CSC 210", "CSC 215", "CSC 220"]},
    "CSC 230": {"title": "Discrete Mathematical Structures for Computer Science", "units": 3,
                "prerequisites": "CSC 210 or CSC 215 or ENGR 213, and MATH 227 (may be taken concurrently)",
                "prereq_codes": ["CSC 210", "CSC 215", "ENGR 213", "MATH 227"]},
    "CSC 256": {"title": "Machine Structures", "units": 3,
                "prerequisites": "CSC 230 with a grade of C or better",
                "prereq_codes": ["CSC 230"]},
    "CSC 300GW": {"title": "Ethics, Communication, and Tools for Software Development - GWAR",
                  "units": 3,
                  "prerequisites": "Upper-division CSC majors/minors; GE Area 1A/A2; CSC 210 or CSC 215",
                  "prereq_codes": ["CSC 210", "CSC 215"]},
    "CSC 306": {"title": "An Interdisciplinary Approach to Computer Programming", "units": 3,
                "prerequisites": "None listed", "prereq_codes": []},
    "CSC 307": {"title": "An Interdisciplinary Approach to Web Programming", "units": 3,
                "prerequisites": "None listed", "prereq_codes": []},
    "CSC 309": {"title": "Computer Programming", "units": 3,
                "prerequisites": "None listed", "prereq_codes": []},
    "CSC 311": {"title": "Data Structures for Data Science Application Development", "units": 3,
                "prerequisites": "CSC 306 or equivalent",
                "prereq_codes": ["CSC 306"]},
    "CSC 317": {"title": "Introduction to Web Software Development", "units": 3,
                "prerequisites": "CSC 220 or permission of the instructor",
                "prereq_codes": ["CSC 220"]},
    "CSC 340": {"title": "Programming Methodology", "units": 3,
                "prerequisites": "CSC 220 and CSC 230 with grades of C or better",
                "prereq_codes": ["CSC 220", "CSC 230"]},
    "CSC 408": {"title": "Machine Learning and Data Science for Personalized Medicine", "units": 3,
                "prerequisites": "CSC 220 or CSC 311 or equivalent; a college-level biology course",
                "prereq_codes": ["CSC 220", "CSC 311"]},
    "CSC 411": {"title": "Intermediate Machine Learning for Interdisciplinary Data Scientists",
                "units": 3,
                "prerequisites": "CSC 220 or CSC 311 or equivalent; a college-level biology course",
                "prereq_codes": ["CSC 220", "CSC 311"]},
    "CSC 412": {"title": "Advanced Software Lab", "units": 1,
                "prerequisites": "CSC 220; concurrent enrollment in CSC 340 recommended",
                "prereq_codes": ["CSC 220", "CSC 340"]},
    "CSC 413": {"title": "Software Development", "units": 3,
                "prerequisites": "CSC 220 and CSC 317 with grades of C or better",
                "prereq_codes": ["CSC 220", "CSC 317"]},
    "CSC 415": {"title": "Operating System Principles", "units": 3,
                "prerequisites": "CSC 256, CSC 340, MATH 324, and PHYS 230 with grades of C or better",
                "prereq_codes": ["CSC 256", "CSC 340", "MATH 324", "PHYS 230"]},
    "CSC 510": {"title": "Analysis of Algorithms I", "units": 3,
                "prerequisites": "CSC 340 and MATH 324 with grades of C or better",
                "prereq_codes": ["CSC 340", "MATH 324"]},
    "CSC 520": {"title": "Theory of Computing", "units": 3,
                "prerequisites": "CSC 220 and CSC 230; MATH 225 or MATH 325 with grades of C or better",
                "prereq_codes": ["CSC 220", "CSC 230", "MATH 225", "MATH 325"]},
    "CSC 600": {"title": "Programming Paradigms and Languages", "units": 3,
                "prerequisites": "CSC 413 and CSC 510 with grades of C or better, or graduate standing",
                "prereq_codes": ["CSC 413", "CSC 510"]},
    "CSC 615": {"title": "Embedded Linux Systems and Physical Computing", "units": 3,
                "prerequisites": "CSC 415 with a grade of C or better or permission of the instructor",
                "prereq_codes": ["CSC 415"]},
    "CSC 620": {"title": "Natural Language Technologies", "units": 3,
                "prerequisites": "Upper-division standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 630": {"title": "Computer Graphics Systems Design", "units": 3,
                "prerequisites": "CSC 413 and either MATH 225 or MATH 325 with grades of C or better",
                "prereq_codes": ["CSC 413", "MATH 225", "MATH 325"]},
    "CSC 642": {"title": "Human-Computer Interaction", "units": 3,
                "prerequisites": "CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 645": {"title": "Computer Networks", "units": 3,
                "prerequisites": "Upper-division standing; CSC 415 with a grade of C or better",
                "prereq_codes": ["CSC 415"]},
    "CSC 648": {"title": "Software Engineering", "units": 3,
                "prerequisites": "Upper-division standing; CSC 317 and CSC 413",
                "prereq_codes": ["CSC 317", "CSC 413"]},
    "CSC 651": {"title": "System Administration", "units": 3,
                "prerequisites": "CSC 413 and CSC 415 with grades of C or better",
                "prereq_codes": ["CSC 413", "CSC 415"]},
    "CSC 652": {"title": "Introduction to Security and Data Privacy", "units": 3,
                "prerequisites": "CSC 415 with a grade of C or better or permission of the instructor",
                "prereq_codes": ["CSC 415"]},
    "CSC 656": {"title": "Computer Organization", "units": 3,
                "prerequisites": "CSC 415 (may be taken concurrently) or permission of the instructor",
                "prereq_codes": ["CSC 415"]},
    "CSC 659": {"title": "AI Explainability and Ethics", "units": 3,
                "prerequisites": "Upper-division standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 664": {"title": "Multimedia Systems", "units": 3,
                "prerequisites": "Upper-division standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 665": {"title": "Artificial Intelligence", "units": 3,
                "prerequisites": "Upper-division standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 667": {"title": "Internet Application Design and Development", "units": 3,
                "prerequisites": "Upper-division standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 668": {"title": "Advanced Object Oriented Software Design and Development", "units": 3,
                "prerequisites": "Senior standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
    "CSC 671": {"title": "Deep Learning", "units": 3,
                "prerequisites": "Upper-division standing; CSC 510; MATH 225 or MATH 325",
                "prereq_codes": ["CSC 510", "MATH 225", "MATH 325"]},
    "CSC 675": {"title": "Introduction to Database Systems", "units": 3,
                "prerequisites": "Upper-division standing; CSC 413 with a grade of C or better",
                "prereq_codes": ["CSC 413"]},
}

# Codes the model may write without the bulletin suffix (e.g. "CSC 300" for
# "CSC 300GW").
ALIASES = {"CSC 300": "CSC 300GW"}

_CODE_RE = re.compile(r"[A-Za-z]{2,5}\s*\d{3}[A-Za-z]*")


def normalize_code(code) -> str | None:
    """'csc648' / 'CSC-648' -> 'CSC 648'; 'CSC 300' -> 'CSC 300GW'."""
    if not isinstance(code, str):
        return None
    match = _CODE_RE.search(code.upper().replace("-", " "))
    if not match:
        return None
    normalized = re.sub(r"^([A-Z]{2,5})\s*(\d{3}[A-Z]*)$", r"\1 \2", match.group(0))
    return ALIASES.get(normalized, normalized)


def _norm_title(title) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(title or "").lower())


def catalog_for_prompt() -> list[dict]:
    """Compact records both models receive as shared reference data."""
    return [
        {"code": code, "title": c["title"], "units": c["units"],
         "prerequisites": c["prerequisites"]}
        for code, c in sorted(CATALOG.items())
    ]


def validate_course(code, title=None, prerequisites_claimed=None) -> dict:
    """Check one recommendation against the curated record.

    status:
      verified       - code and title match the record
      unverified     - course code is not in the curated records
      title_mismatch - code exists but the stated title differs
    Prerequisite claims are checked only against recorded prerequisite codes;
    a claim the record cannot confirm is listed as unverified, never confirmed.
    """
    normalized = normalize_code(code)
    record = CATALOG.get(normalized) if normalized else None

    if record is None:
        return {
            "status": "unverified",
            "course_code": normalized or code,
            "issue": "Course code is not in the curated SFSU records; cannot confirm it exists.",
        }

    issues = []
    status = "verified"

    if title and _norm_title(title) != _norm_title(record["title"]):
        status = "title_mismatch"
        issues.append(
            f'Stated title "{title}" differs from the bulletin title '
            f'"{record["title"]}".'
        )

    claimed_codes = []
    for claim in prerequisites_claimed or []:
        claimed_codes.extend(normalize_code(m) for m in _CODE_RE.findall(str(claim)))
    claimed_codes = [c for c in claimed_codes if c and c != normalized]

    unknown_prereqs = [c for c in claimed_codes if c not in record["prereq_codes"]]
    if unknown_prereqs:
        issues.append(
            "Prerequisite claim not confirmed by the record: "
            + ", ".join(sorted(set(unknown_prereqs)))
            + f' (recorded: {record["prerequisites"]}).'
        )

    return {
        "status": status,
        "course_code": normalized,
        "catalog_title": record["title"],
        "catalog_prerequisites": record["prerequisites"],
        "issue": " ".join(issues) or None,
    }


def compare_recommendations(recs_a: list[dict], recs_b: list[dict]) -> dict:
    """Which recommendations the two models agree on, by course code or title.

    Agreement is only about overlap between the two outputs; it is not evidence
    that either recommendation is accurate.
    """
    def key(rec):
        code = normalize_code(rec.get("course_code"))
        return code or ("title:" + _norm_title(rec.get("title")))

    keys_a = {key(r) for r in recs_a}
    keys_b = {key(r) for r in recs_b}

    return {
        "shared": sorted(k for k in keys_a & keys_b if not k.startswith("title:")),
        "shared_titles": sorted(k[6:] for k in keys_a & keys_b if k.startswith("title:")),
        "only_a": sorted(k for k in keys_a - keys_b if not k.startswith("title:")),
        "only_b": sorted(k for k in keys_b - keys_a if not k.startswith("title:")),
    }
