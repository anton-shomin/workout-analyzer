# Tasks: Goal Evaluation Enhancement

**Input**: Design documents from `/specs/001-goal-evaluation-enhancement/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Review existing workout analyzer architecture and codebase
- [x] T002 [P] Examine current workout parsing implementation in parsers/workout_parser.py
- [x] T003 [P] Examine current AI prompt generation in ai/prompts.py
- [x] T004 [P] Review existing workout file format and YAML frontmatter structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Update workout parser to extract goal field from YAML frontmatter in parsers/workout_parser.py
- [x] T006 [P] Modify workout_data dictionary to include goal field in parsers/workout_parser.py
- [x] T007 Update build_workout_prompt function to accept and include goal in ai/prompts.py
- [x] T008 [P] Modify prompt template to include goal evaluation section in ai/prompts.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Workout Analysis with Goal Context (Priority: P1) 🎯 MVP

**Goal**: Enable AI to analyze workouts in the context of user-specified goals, providing targeted feedback on whether exercise selection and execution align with objectives.

**Independent Test**: The system can be tested by providing a workout with a specific goal (e.g., "Strength gain", "Fat loss", "Endurance improvement") and verifying that the AI analysis explicitly addresses alignment with that goal.

### Implementation for User Story 1

- [x] T009 [US1] Create test workout file with goal field in YAML frontmatter for testing
- [x] T010 [US1] Verify parser correctly extracts goal field from workout file
- [x] T011 [US1] Update AI prompt to emphasize goal alignment as most important evaluation point
- [x] T012 [US1] Test that AI analysis includes explicit evaluation of workout-goal alignment
- [x] T013 [US1] Validate that mismatched exercises and goals generate specific feedback about misalignment

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Goal-Based Exercise Selection Feedback (Priority: P2)

**Goal**: Enable AI to evaluate whether exercise selection was appropriate for the stated goal, providing actionable insights for future workout planning.

**Independent Test**: The system can be tested by comparing AI feedback on workouts with different exercise selections for the same goal, verifying that feedback varies appropriately based on exercise appropriateness.

### Implementation for User Story 2

- [x] T014 [US2] Create test workout files with exercises that don't support the stated goal
- [x] T015 [US2] Update AI prompt to specifically ask for exercise-goal alignment assessment
- [x] T016 [US2] Verify AI identifies specific exercises that don't align with the goal
- [x] T017 [US2] Ensure AI suggests alternative exercises that better align with the goal
- [x] T018 [US2] Test that feedback varies appropriately based on exercise appropriateness

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Goal-Oriented Recovery Recommendations (Priority: P3)

**Goal**: Enable AI to provide recovery recommendations based on both workout intensity and the stated goal, optimizing rest periods for goal achievement.

**Independent Test**: The system can be tested by verifying that recovery recommendations vary based on both workout intensity and stated goal (e.g., different recovery for strength vs endurance goals).

### Implementation for User Story 3

- [x] T019 [US3] Create test workout files with high-intensity exercises and specific goals
- [x] T020 [US3] Update AI prompt to include goal-specific recovery recommendations
- [x] T021 [US3] Verify AI provides different recovery advice based on workout goal
- [x] T022 [US3] Test that recovery recommendations consider both intensity and goal type
- [x] T023 [US3] Validate CNS load considerations in recovery advice for strength-focused sessions

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T024 [P] Handle edge case where workout file has no goal specified in parsers/workout_parser.py
- [x] T025 [P] Ensure backward compatibility with existing workout files that lack goal field
- [x] T026 [P] Add proper error handling for malformed goal values
- [x] T027 [P] Update README.md with documentation about goal field usage
- [x] T028 [P] Create example workout files demonstrating goal usage in EXAMPLES.md
- [x] T029 Run quickstart validation to ensure all functionality works as expected

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together:
Task: "Create test workout file with goal field in YAML frontmatter for testing"
Task: "Verify parser correctly extracts goal field from workout file"
Task: "Update AI prompt to emphasize goal alignment as most important evaluation point"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence