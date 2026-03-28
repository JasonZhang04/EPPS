# Story 
- Human communication is fundamentally pragmatically compressed — "tidy up" encodes complex spatial preferences, object hierarchies, and personal habits that vary per user
- Current VLMs treat every interaction as a fresh start, failing to accumulate user-specific semantic knowledge across time
- Even with full interaction history in context, VLMs cannot reliably extract and generalize stable semantic constraints to new scenes — this is a faithfulness problem, not just a memory problem
- The insight: Effective human-AI collaboration requires a shared, structured representation of the user's semantic world — a Common Ground Model (CGM) — built passively through observation, not explicit teaching

# Research Question
Can an agent, through passive observation of user behavior, build a structured Common Ground Model that improves the faithfulness and efficiency of pragmatic instruction following over time — without explicit correction, goal annotation, or model retraining?

# Failure Modes (Pragmatics) to Test
- Referential ambiguity — "put that away" when multiple candidates exist
- Vague predicates — "clean up" means different things to different people
- Goal underspecification — "make it look nice" requires knowing the user's aesthetic prototype
