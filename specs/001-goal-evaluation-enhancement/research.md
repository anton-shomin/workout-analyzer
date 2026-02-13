# Research: Goal Evaluation Enhancement

## Decision: Add goal field to workout metadata and enhance AI analysis

### Rationale:
The feature requires extracting a 'goal' field from workout file metadata and incorporating it into the AI analysis. This follows the existing pattern used by other metadata fields like 'date', 'type', 'weight', and 'duration'. The implementation involves two main changes:
1. Updating the workout parser to extract the goal field
2. Modifying the AI prompt to include goal evaluation

### Implementation Approach:
1. **Data Layer**: Add 'goal' field to YAML frontmatter of workout files
2. **Parsing Layer**: Update `parse_workout_file()` to extract the goal field
3. **Logic Layer**: Modify `build_workout_prompt()` to include goal in AI analysis
4. **Execution Layer**: No changes needed as workout_data flows through existing pipeline

### Alternatives Considered:

#### Alternative 1: Store goals in separate configuration file
- **Pros**: Centralized goal management, easier to update goals
- **Cons**: More complex implementation, requires cross-referencing files, breaks existing single-file workflow

#### Alternative 2: Infer goals from workout content automatically
- **Pros**: No manual input required from user
- **Cons**: Less accurate, harder to implement reliably, removes user control over goal specification

#### Alternative 3: Add goal as command-line parameter
- **Pros**: Simple implementation, no file modifications needed
- **Cons**: Doesn't persist goal with workout data, requires user to remember and specify goal each time

## Decision: Use "Not specified" as default value when goal is absent

### Rationale:
When a workout file doesn't contain a goal in its metadata, the system should gracefully handle this case by using a default value. This maintains backward compatibility with existing workout files while providing clear indication to the AI that no specific goal was set.

## Decision: Enhance AI prompt to explicitly evaluate goal alignment

### Rationale:
The AI prompt needs to be modified to specifically ask the AI model to evaluate how well the workout aligns with the stated goal. This ensures the analysis focuses on goal achievement rather than just providing generic feedback. The enhanced prompt will include the goal in the context section and explicitly request goal alignment assessment.