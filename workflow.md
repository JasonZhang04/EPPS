# Environments
# - vh310        : VirtualHome simulation (Python 3.10)
# - tinker_env   : Tinker API + EPPS pipeline (Python 3.11)
# - epps311      : for final evaluation, use this one!!!

# 1. Activate environment
# For VirtualHome / physics simulation:
conda activate vh310
# For Tinker API / LLM inference:
# conda activate tinker_env

# 2. Navigate to project
cd ~/Desktop/JHU/"JHU 2025-2026"/"JHU 2026 Spring"/MSI/EPPS

# 3. Open Unity (if you need rendering)
open virtualhome/simulation/unity_simulator/macos_exec.2.2.4.app

# 4. Work on your scripts, then push changes
git add .
git commit -m "your message"
git push origin main

----------------------------------------------------------------------------------

# note: Set your Tinker API key as an environment variable (do not commit keys to git)
# export TINKER_API_KEY="tml-..."
----------------------------------------------------------------------------------

# Updated Data Generation

----------------------------------------------------------------------------------

# Most up to data running pipeline

Prerequisites

Activate the correct environment: conda activate epps311
Be inside epps_workspace/
Have TINKER_API_KEY set
Step 1 — Generate the dataset (already done, skip if data/eval_dataset.json exists)


python -m src.data_gen.dataset_compiler
Step 2 — Run evaluation


# Single persona
TINKER_API_KEY=your_key python -m src.eval.evaluator --persona Minimalist

# Multiple specific personas (run separately — they accumulate automatically)
TINKER_API_KEY=your_key python -m src.eval.evaluator --persona Functionalist

# All 5 personas in one shot (omit --persona entirely)
TINKER_API_KEY=your_key python -m src.eval.evaluator
Step 3 — View results


python -m src.eval.report_scores --turns

----------------------------------------------------------------------------------


# Overall EPPS Architecture

The central idea: instead of giving an LLM a raw log of "what the user did" and hoping it figures out their preferences, EPPS compiles those preferences offline into a structured rulebook (the CGM), then uses that rulebook as hard constraints at planning time.

Here's how all the pieces connect:


                    ┌─────────────────────────────────────────┐
                    │          DATA GENERATION                │
                    │  persona_definitions.py                 │
                    │         ↓                               │
                    │  vh_script_writer.py  →  Tinker LLM     │
                    │         ↓                               │
                    │  physics_validator.py → VH Simulator    │
                    │         ↓                               │
                    │  dataset_compiler.py  → eval_dataset.json│
                    └─────────────────────────────────────────┘
                                      ↓
                    ┌─────────────────────────────────────────┐
                    │          EVALUATION LOOP                │
                    │  evaluator.py reads each task entry:    │
                    │    history_log, correction_log,         │
                    │    novel_items, ground_truth            │
                    └──────┬──────────────────┬──────────────┘
                           │                  │
              ┌────────────▼──┐        ┌──────▼─────────────┐
              │   3 Baselines │        │     EPPSAgent       │
              │  ZeroShot     │        │  (epps_agent.py)    │
              │  RagHistory   │        │                     │
              │  NaiveSummary │        │  1. observe_background()
              └───────────────┘        │     → layer1_extractor.py
                     ↓                 │     → LLM extracts CGM
              predict(instruction,     │                     │
                novel_items,           │  2. receive_feedback()
                history_log)           │     → layer2_corrector.py
                                       │     → LLM updates CGM
                                       │     + Bayesian decay  │
                                       │                     │
                                       │  3. plan_execution()│
                                       │     → execution_planner.py
                                       │     → LLM uses CGM  │
                                       │       as hard rules  │
                                       └─────────────────────┘
                                                ↓
                                    ┌───────────────────────┐
                                    │   metrics.py (PFS)    │
                                    │   pred vs ground truth│
                                    └───────────────────────┘
Component by Component
schemas.py — the data contract
Defines the CGM as a Pydantic model. The hierarchy is: ItemOverride > CategoryRule > pre-trained LLM bias. A category rule says "all electronics → desk". An item override says "but specifically the tablet → closet". global_noise_items are things like keys or water glasses — transient, shouldn't form rules.

thinking_machine.py — the LLM client
A thin async wrapper around the Tinker API. Every LLM call in the system goes through ThinkingMachineClient.query(). Temperature 0.0 everywhere except data generation (0.7) to keep CGM extraction deterministic.

Layer 1 (layer1_extractor.py) — offline rule compilation
Takes the history_log (the [MOVED] diffs from VirtualHome), sends them to the LLM with the Layer 1 prompt, and gets back a CGM JSON. This runs once per user before any task.

Layer 2 (layer2_corrector.py) — implicit feedback
Takes the existing CGM + a correction log (human moving something the agent misplaced), asks the LLM to add an item_override without destroying the broader category rule. The Bayesian momentum decay in epps_agent.py then smooths the confidence: C_new = 0.8 * C_old + 0.2 * new_confidence, so one correction doesn't obliterate a rule with 10 observations behind it.

Layer 3 (execution_planner.py) — planning
Receives the CGM + novel items + instruction, tells the LLM to treat the CGM as "laws of physics" overriding its pre-trained common sense. Returns a {item: destination} JSON dict.

The 3 baselines all share the same predict(instruction, novel_items, history_log) signature but don't build a CGM:

ZeroShot: ignores history entirely, pure societal norms
RagHistory: dumps the raw log into the prompt (episodic memory, susceptible to noise)
NaiveSummary: 2-step — first summarizes the log to plain English, then plans from that (weaker than CGM because natural language doesn't enforce constraints)
evaluator.py loops over all 30 dataset tasks, runs all 4 agents, scores each with PFS (% of novel items placed correctly), saves to eval_results.json.