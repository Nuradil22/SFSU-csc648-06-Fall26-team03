import test from 'node:test';
import assert from 'node:assert/strict';
import {
  APPROVED_UNVERIFIED_NOTICE,
  PROPOSAL_NOTICES,
  approvedRoadmapNotice,
  educationalStatus,
  proposalReview,
} from './educational.js';

const verified = { title: 'R', goals: [], educational: true, offerings: 2 };
const generic = { title: 'Old checklist', goals: [], educational: false, offerings: 0 };
const noFlag = { title: 'Older response', goals: [] };

test('status comes only from an explicit flag', () => {
  assert.equal(educationalStatus(verified), 'verified');
  assert.equal(educationalStatus(generic), 'unverified');
  assert.equal(educationalStatus(noFlag), 'unknown');
  assert.equal(educationalStatus(null), 'unknown');
  // Truthy values that aren't true never count as verified.
  assert.equal(educationalStatus({ educational: 'true' }), 'unknown');
  assert.equal(educationalStatus({ educational: 1 }), 'unknown');
});

test('a verified pending draft can be approved with no notice', () => {
  assert.deepEqual(proposalReview(verified), { canApprove: true, notice: null });
});

test('a generic pending draft cannot be approved and says why', () => {
  const review = proposalReview(generic);
  assert.equal(review.canApprove, false);
  assert.equal(review.notice, PROPOSAL_NOTICES.unverified);
  assert.match(review.notice, /verified courses, programs, or certificates/);
  assert.match(review.notice, /reject it and ask the assistant for a new personalized educational roadmap/);
});

test('a draft without the flag is not assumed verified', () => {
  const review = proposalReview(noFlag);
  assert.equal(review.canApprove, false);
  assert.equal(review.notice, PROPOSAL_NOTICES.unknown);
});

test('decided drafts show no approval notice', () => {
  for (const status of ['approved', 'rejected', 'superseded']) {
    assert.deepEqual(proposalReview(generic, status), { canApprove: false, notice: null });
  }
});

test('an approved generic roadmap gets an informational notice, never a re-approval', () => {
  assert.equal(approvedRoadmapNotice(generic), APPROVED_UNVERIFIED_NOTICE);
  assert.match(APPROVED_UNVERIFIED_NOTICE, /stays your roadmap and your progress is kept/);
  assert.doesNotMatch(APPROVED_UNVERIFIED_NOTICE, /approv/i);
  assert.equal(approvedRoadmapNotice(verified), null);
  assert.equal(approvedRoadmapNotice(noFlag), null); // claims nothing either way
});
