// The backend's educational validation flag on a roadmap or draft
// (educational_summary in career_chat.py): educational is true only when
// every learning stage centers on a verified course, program, or
// certificate. The backend also refuses to approve anything else; this only
// keeps the page honest about it.
//
//   "verified"    educational === true
//   "unverified"  educational === false (e.g. a generic checklist stored
//                 before verification existed)
//   "unknown"     no flag (an older response); never treated as verified

export function educationalStatus(roadmap) {
  if (roadmap?.educational === true) return "verified";
  if (roadmap?.educational === false) return "unverified";
  return "unknown";
}

const NEW_ROADMAP_HINT =
  'You can reject it and ask the assistant for a new personalized educational roadmap (for example, "Generate a new roadmap").';

export const PROPOSAL_NOTICES = {
  unverified:
    "This draft doesn't contain verified courses, programs, or certificates, so it can't be approved. " +
    NEW_ROADMAP_HINT,
  unknown:
    "This draft couldn't be checked for verified courses, programs, or certificates, so it can't be approved here. " +
    NEW_ROADMAP_HINT,
};

// Shown on an approved roadmap without verified offerings. It stays the
// student's roadmap, progress included; nothing needs re-approval.
export const APPROVED_UNVERIFIED_NOTICE =
  "This roadmap doesn't include verified courses, programs, or certificates. It stays your roadmap " +
  "and your progress is kept. Ask the assistant for a new personalized educational roadmap whenever you'd like one.";

// What the proposal card shows: {canApprove, notice}. Only a pending,
// verified draft can be approved; reject is always available while pending.
export function proposalReview(proposal, status = "pending") {
  if (status !== "pending") return { canApprove: false, notice: null };
  const educational = educationalStatus(proposal);
  return educational === "verified"
    ? { canApprove: true, notice: null }
    : { canApprove: false, notice: PROPOSAL_NOTICES[educational] };
}

// The notice for an approved roadmap (null when none is needed). A missing
// flag claims nothing either way.
export function approvedRoadmapNotice(roadmap) {
  return educationalStatus(roadmap) === "unverified" ? APPROVED_UNVERIFIED_NOTICE : null;
}
