from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# PERSONAS
# ---------------------------------------------------------------------------

PERSONAS = {
    "Minimalist": {
        "description": (
            "You hate visual clutter. Every item must be hidden inside closed receptacles "
            "(closet, fridge, bathroom_cabinet). Nothing should be left resting ON a surface. "
            "Clothing goes INSIDE the closet. Electronics go INSIDE the closet. "
            "Food goes INSIDE the fridge. Hygiene items go INSIDE the bathroom_cabinet."
        ),
        "ground_truth_logic": "Everything INSIDE closed containers: closet for non-food/non-hygiene, fridge for food, bathroom_cabinet for hygiene."
    },
    "Functionalist": {
        "description": (
            "You prioritize immediate access. Items rest ON the surface where they are most "
            "frequently used. Electronics and study materials go ON the desk. "
            "Books and reference materials go ON the bookshelf. Food goes INSIDE the fridge. "
            "Everyday carry items (keys, wallet, mail) stay ON the kitchen_table near the exit. "
            "Leisure reading goes ON the sofa. Hygiene items go INSIDE the bathroom_cabinet."
        ),
        "ground_truth_logic": "Items stay ON context-relevant surfaces based on their use location."
    },
    "Child_Safe": {
        "description": (
            "You organize for toddler safety. Any item that is small, electronic, fragile, sharp, "
            "or potentially harmful MUST be placed out of reach ON the bookshelf (high surface) "
            "or INSIDE the bathroom_cabinet (secured). Soft and safe items like clothing and "
            "magazines go INSIDE the closet or ON the sofa. Food goes INSIDE the fridge. "
            "Paper items like mail and sticky_notes go ON the desk."
        ),
        "ground_truth_logic": "Hazardous/small items elevated to bookshelf or bathroom_cabinet; safe items in closet/sofa."
    },
    "Social_Host": {
        "description": (
            "You organize with guests in mind. All personal clutter must be hidden: clothing, "
            "loose leisure items, and magazines go INSIDE the closet. Food goes INSIDE the fridge. "
            "The desk may stay organized and visible (work/electronics acceptable there). "
            "Hygiene items go INSIDE the bathroom_cabinet. Keys and wallet stay ON the "
            "kitchen_table since guests don't enter the bedroom."
        ),
        "ground_truth_logic": "Guest-visible areas clear; personal items in closet; workspace items on desk acceptable."
    },
    "Creative_Worker": {
        "description": (
            "Your desk is your universe. Every item you might actively use — electronics, "
            "notebooks, pens, chargers, reading material, even your mug and hand cream — stays "
            "ON the desk for maximum accessibility. Food goes INSIDE the fridge. "
            "Clothing goes INSIDE the closet. Hygiene items go INSIDE the bathroom_cabinet. "
            "When in doubt, put it ON the desk."
        ),
        "ground_truth_logic": "Desk-centric: all work and utility items ON desk; food in fridge; clothing in closet."
    },
}

# ---------------------------------------------------------------------------
# NOVEL ITEM GROUND TRUTHS
# 12-item pool of items not in the VirtualHome environment (purely symbolic).
# Ground truths reflect each persona's organizing philosophy.
# ---------------------------------------------------------------------------

NOVEL_ITEM_GROUND_TRUTHS: Dict[str, Dict[str, str]] = {
    "Minimalist": {
        "power_bank":   "closet",
        "magazine":     "closet",
        "sweater":      "closet",
        "bag_of_chips": "fridge",
        "wallet":       "closet",
        "umbrella":     "closet",
        "mug":          "closet",
        "sticky_notes": "closet",
        "hand_cream":   "bathroom_cabinet",
        "book_novel":   "closet",
        "flashlight":   "closet",
        "backpack":     "closet",
    },
    "Functionalist": {
        "power_bank":   "desk",
        "magazine":     "sofa",
        "sweater":      "closet",
        "bag_of_chips": "kitchen_table",
        "wallet":       "kitchen_table",
        "umbrella":     "kitchen_table",
        "mug":          "kitchen_table",
        "sticky_notes": "desk",
        "hand_cream":   "bathroom_cabinet",
        "book_novel":   "sofa",
        "flashlight":   "desk",
        "backpack":     "kitchen_table",
    },
    "Child_Safe": {
        "power_bank":   "bookshelf",
        "magazine":     "sofa",
        "sweater":      "closet",
        "bag_of_chips": "fridge",
        "wallet":       "bookshelf",
        "umbrella":     "closet",
        "mug":          "bathroom_cabinet",
        "sticky_notes": "desk",
        "hand_cream":   "bathroom_cabinet",
        "book_novel":   "sofa",
        "flashlight":   "bookshelf",
        "backpack":     "closet",
    },
    "Social_Host": {
        "power_bank":   "desk",
        "magazine":     "closet",
        "sweater":      "closet",
        "bag_of_chips": "fridge",
        "wallet":       "kitchen_table",
        "umbrella":     "closet",
        "mug":          "bathroom_cabinet",
        "sticky_notes": "desk",
        "hand_cream":   "bathroom_cabinet",
        "book_novel":   "closet",
        "flashlight":   "closet",
        "backpack":     "closet",
    },
    "Creative_Worker": {
        "power_bank":   "desk",
        "magazine":     "desk",
        "sweater":      "closet",
        "bag_of_chips": "fridge",
        "wallet":       "desk",
        "umbrella":     "closet",
        "mug":          "desk",
        "sticky_notes": "desk",
        "hand_cream":   "desk",
        "book_novel":   "desk",
        "flashlight":   "desk",
        "backpack":     "desk",
    },
}

# ---------------------------------------------------------------------------
# CHORE-TYPE-SPECIFIC CORRECTIONS
#
# Each correction represents the human user overriding the agent's default
# (societal-norm) placement with their persona-driven preference.
# Keyed by chore_type so corrections are contextually relevant to the
# items the agent just observed in that session.
# ---------------------------------------------------------------------------

CHORE_CORRECTIONS: Dict[str, Dict[str, List[str]]] = {
    "Minimalist": {
        # Agent left jacket on sofa; Minimalist hides it in closet
        "Morning Routine":  ["[MOVED] jacket : (ON sofa) -> (INSIDE closet)"],
        # Agent left apple on kitchen_table; Minimalist puts it in fridge
        "Grocery Put-Away": ["[MOVED] apple : (ON kitchen_table) -> (INSIDE fridge)"],
        # Agent left laptop on desk; Minimalist hides it in closet
        "Office Setup":     ["[MOVED] laptop : (ON desk) -> (INSIDE closet)"],
        # Agent left headphones on desk; Minimalist hides them in closet
        "Electronics Tidy": ["[MOVED] headphones : (ON desk) -> (INSIDE closet)"],
        # Agent left shoes on sofa; Minimalist puts them in closet
        "Clothing Pickup":  ["[MOVED] shoes : (ON sofa) -> (INSIDE closet)"],
        # Agent left water_glass on kitchen_table; Minimalist puts it in closet
        "Kitchen Cleanup":  ["[MOVED] water_glass : (ON kitchen_table) -> (INSIDE closet)"],
        # Agent left notebook on desk; Minimalist hides it in closet
        "Desk Cleanup":     ["[MOVED] notebook : (ON desk) -> (INSIDE closet)"],
        # Agent left tv_remote on sofa; Minimalist hides it in closet
        "Living Room Tidy": ["[MOVED] tv_remote : (ON sofa) -> (INSIDE closet)"],
    },
    "Functionalist": {
        # Agent put keys in closet; Functionalist moves them to kitchen_table (near exit)
        "Morning Routine":  ["[MOVED] keys : (INSIDE closet) -> (ON kitchen_table)"],
        # Agent left milk on counter; Functionalist puts it in fridge (food context)
        "Grocery Put-Away": ["[MOVED] milk : (ON kitchen_table) -> (INSIDE fridge)"],
        # Agent put textbook in closet; Functionalist moves it to bookshelf (study context)
        "Office Setup":     ["[MOVED] textbook : (INSIDE closet) -> (ON bookshelf)"],
        # Agent put tablet in closet; Functionalist moves it to desk (electronics context)
        "Electronics Tidy": ["[MOVED] tablet : (INSIDE closet) -> (ON desk)"],
        # Agent left jacket on desk; Functionalist puts it in closet (clothing context)
        "Clothing Pickup":  ["[MOVED] jacket : (ON desk) -> (INSIDE closet)"],
        # Agent left apple on desk; Functionalist moves it to fridge (food context)
        "Kitchen Cleanup":  ["[MOVED] apple : (ON desk) -> (INSIDE fridge)"],
        # Agent put laptop in closet; Functionalist moves it to desk (work context)
        "Desk Cleanup":     ["[MOVED] laptop : (INSIDE closet) -> (ON desk)"],
        # Agent left tv_remote on desk; Functionalist moves it to sofa (leisure context)
        "Living Room Tidy": ["[MOVED] tv_remote : (ON desk) -> (ON sofa)"],
    },
    "Child_Safe": {
        # Agent left keys on sofa (reachable); Child_Safe elevates them to bookshelf
        "Morning Routine":  ["[MOVED] keys : (ON sofa) -> (ON bookshelf)"],
        # Agent left apple on sofa; Child_Safe puts it in fridge (food secured)
        "Grocery Put-Away": ["[MOVED] apple : (ON sofa) -> (INSIDE fridge)"],
        # Agent left laptop on kitchen_table (reachable); Child_Safe elevates it
        "Office Setup":     ["[MOVED] laptop : (ON kitchen_table) -> (ON bookshelf)"],
        # Agent left headphones on kitchen_table; Child_Safe elevates them
        "Electronics Tidy": ["[MOVED] headphones : (ON kitchen_table) -> (ON bookshelf)"],
        # Agent left shoes on sofa; Child_Safe puts them in closet (put away safely)
        "Clothing Pickup":  ["[MOVED] shoes : (ON sofa) -> (INSIDE closet)"],
        # Agent left water_glass on sofa (glass = fragile); Child_Safe secures it
        "Kitchen Cleanup":  ["[MOVED] water_glass : (ON sofa) -> (INSIDE bathroom_cabinet)"],
        # Agent left charger on desk (cord = hazard); Child_Safe elevates it
        "Desk Cleanup":     ["[MOVED] charger : (ON desk) -> (ON bookshelf)"],
        # Agent left tv_remote on sofa; Child_Safe elevates it (small, choke hazard)
        "Living Room Tidy": ["[MOVED] tv_remote : (ON sofa) -> (ON bookshelf)"],
    },
    "Social_Host": {
        # Agent left jacket on sofa (visible to guests); Social_Host hides it
        "Morning Routine":  ["[MOVED] jacket : (ON sofa) -> (INSIDE closet)"],
        # Agent left apple on kitchen_table; Social_Host puts it in fridge (kitchen spotless)
        "Grocery Put-Away": ["[MOVED] apple : (ON kitchen_table) -> (INSIDE fridge)"],
        # Agent left notebook on sofa (visible); Social_Host hides it
        "Office Setup":     ["[MOVED] notebook : (ON sofa) -> (INSIDE closet)"],
        # Agent left headphones on sofa (personal clutter); Social_Host hides them
        "Electronics Tidy": ["[MOVED] headphones : (ON sofa) -> (INSIDE closet)"],
        # Agent left shoes on sofa (visible); Social_Host hides them
        "Clothing Pickup":  ["[MOVED] shoes : (ON sofa) -> (INSIDE closet)"],
        # Agent left mail on kitchen_table (personal clutter); Social_Host hides it
        "Kitchen Cleanup":  ["[MOVED] mail : (ON kitchen_table) -> (INSIDE closet)"],
        # Agent left notebook on sofa; Social_Host hides it
        "Desk Cleanup":     ["[MOVED] notebook : (ON sofa) -> (INSIDE closet)"],
        # Agent left tv_remote on sofa; Social_Host hides it (living room must be pristine)
        "Living Room Tidy": ["[MOVED] tv_remote : (ON sofa) -> (INSIDE closet)"],
    },
    "Creative_Worker": {
        # Agent put keys on kitchen_table; Creative_Worker moves them to desk
        "Morning Routine":  ["[MOVED] keys : (ON kitchen_table) -> (ON desk)"],
        # Agent left cheese on sofa; Creative_Worker puts it in fridge (food leaves desk area)
        "Grocery Put-Away": ["[MOVED] cheese : (ON sofa) -> (INSIDE fridge)"],
        # Agent put notebook in closet; Creative_Worker moves it to desk (always accessible)
        "Office Setup":     ["[MOVED] notebook : (INSIDE closet) -> (ON desk)"],
        # Agent put charger in closet; Creative_Worker moves it to desk
        "Electronics Tidy": ["[MOVED] charger : (INSIDE closet) -> (ON desk)"],
        # Agent left jacket on desk (clothing clutters workspace); Creative_Worker puts it away
        "Clothing Pickup":  ["[MOVED] jacket : (ON desk) -> (INSIDE closet)"],
        # Agent left water_glass on kitchen_table; Creative_Worker brings it to desk
        "Kitchen Cleanup":  ["[MOVED] water_glass : (ON kitchen_table) -> (ON desk)"],
        # Agent put pen in closet; Creative_Worker moves it back to desk
        "Desk Cleanup":     ["[MOVED] pen : (INSIDE closet) -> (ON desk)"],
        # Agent left headphones on sofa; Creative_Worker moves them to desk
        "Living Room Tidy": ["[MOVED] headphones : (ON sofa) -> (ON desk)"],
    },
}

# ---------------------------------------------------------------------------
# CHORE SCHEDULE (20 turns)
#
# Each entry defines one turn for every persona. The chore_type, context,
# training_items (for VH simulation), and novel_items (for evaluation) are
# intentionally correlated so the CGM receives thematically consistent signals.
#
# Chore types: 8 types, each appearing 2-3 times over 20 turns.
# Novel items: drawn from NOVEL_ITEM_GROUND_TRUTHS pool, 3 per turn,
#   chosen to match the semantic category of that session's training items.
# ---------------------------------------------------------------------------

CHORE_SCHEDULE: List[Dict] = [
    # --- Cycle 1 (Turns 1-8): one of each chore type ---
    {
        "chore_type": "Morning Routine",
        "context": "Morning routine before heading out",
        "training_items": [("water_glass", 34), ("keys", 35), ("jacket", 31), ("toothpaste", 33)],
        "novel_items": ["wallet", "umbrella", "hand_cream"],
    },
    {
        "chore_type": "Grocery Put-Away",
        "context": "Putting away groceries after shopping",
        "training_items": [("apple", 20), ("milk", 21), ("salmon", 22), ("cheese", 23)],
        "novel_items": ["bag_of_chips", "mug", "sweater"],
    },
    {
        "chore_type": "Office Setup",
        "context": "Setting up workspace for the day",
        "training_items": [("laptop", 24), ("textbook", 28), ("notebook", 29), ("pen", 30)],
        "novel_items": ["sticky_notes", "power_bank", "book_novel"],
    },
    {
        "chore_type": "Electronics Tidy",
        "context": "Collecting scattered tech devices",
        "training_items": [("tablet", 25), ("charger", 26), ("headphones", 27), ("tv_remote", 36)],
        "novel_items": ["power_bank", "flashlight", "backpack"],
    },
    {
        "chore_type": "Clothing Pickup",
        "context": "Picking up clothes from around the house",
        "training_items": [("jacket", 31), ("shoes", 32), ("sunglasses", 38)],
        "novel_items": ["sweater", "umbrella", "backpack"],
    },
    {
        "chore_type": "Kitchen Cleanup",
        "context": "Kitchen cleanup after dinner",
        "training_items": [("apple", 20), ("water_glass", 34), ("mail", 37), ("keys", 35)],
        "novel_items": ["bag_of_chips", "mug", "wallet"],
    },
    {
        "chore_type": "Desk Cleanup",
        "context": "End-of-workday desk cleanup",
        "training_items": [("laptop", 24), ("notebook", 29), ("pen", 30), ("charger", 26)],
        "novel_items": ["sticky_notes", "magazine", "book_novel"],
    },
    {
        "chore_type": "Living Room Tidy",
        "context": "Tidying the living room before relaxing",
        "training_items": [("tv_remote", 36), ("headphones", 27), ("textbook", 28), ("notebook", 29)],
        "novel_items": ["magazine", "book_novel", "flashlight"],
    },
    # --- Cycle 2 (Turns 9-16): second pass, varied novel items ---
    {
        "chore_type": "Morning Routine",
        "context": "Quick morning tidy before work",
        "training_items": [("water_glass", 34), ("keys", 35), ("jacket", 31), ("toothpaste", 33)],
        "novel_items": ["wallet", "hand_cream", "umbrella"],
    },
    {
        "chore_type": "Grocery Put-Away",
        "context": "Weekend grocery run put-away",
        "training_items": [("apple", 20), ("milk", 21), ("salmon", 22), ("cheese", 23)],
        "novel_items": ["bag_of_chips", "hand_cream", "mug"],
    },
    {
        "chore_type": "Office Setup",
        "context": "Pre-meeting workspace organization",
        "training_items": [("laptop", 24), ("textbook", 28), ("notebook", 29), ("pen", 30)],
        "novel_items": ["sticky_notes", "book_novel", "power_bank"],
    },
    {
        "chore_type": "Electronics Tidy",
        "context": "Untangling and storing electronics",
        "training_items": [("tablet", 25), ("charger", 26), ("headphones", 27), ("tv_remote", 36)],
        "novel_items": ["power_bank", "backpack", "flashlight"],
    },
    {
        "chore_type": "Clothing Pickup",
        "context": "Laundry day organization",
        "training_items": [("jacket", 31), ("shoes", 32), ("sunglasses", 38)],
        "novel_items": ["sweater", "backpack", "umbrella"],
    },
    {
        "chore_type": "Kitchen Cleanup",
        "context": "Cleanup after meal prep",
        "training_items": [("apple", 20), ("water_glass", 34), ("mail", 37), ("keys", 35)],
        "novel_items": ["mug", "bag_of_chips", "wallet"],
    },
    {
        "chore_type": "Desk Cleanup",
        "context": "Post-project workspace reset",
        "training_items": [("laptop", 24), ("notebook", 29), ("pen", 30), ("charger", 26)],
        "novel_items": ["magazine", "sticky_notes", "book_novel"],
    },
    {
        "chore_type": "Living Room Tidy",
        "context": "Pre-company living room cleanup",
        "training_items": [("tv_remote", 36), ("headphones", 27), ("textbook", 28), ("notebook", 29)],
        "novel_items": ["magazine", "flashlight", "sweater"],
    },
    # --- Cycle 3 (Turns 17-20): third pass on most-informative chores ---
    {
        "chore_type": "Morning Routine",
        "context": "Weekend morning routine cleanup",
        "training_items": [("water_glass", 34), ("keys", 35), ("jacket", 31), ("toothpaste", 33)],
        "novel_items": ["umbrella", "hand_cream", "wallet"],
    },
    {
        "chore_type": "Grocery Put-Away",
        "context": "Bulk shopping storage",
        "training_items": [("apple", 20), ("milk", 21), ("salmon", 22), ("cheese", 23)],
        "novel_items": ["mug", "bag_of_chips", "hand_cream"],
    },
    {
        "chore_type": "Office Setup",
        "context": "Study session preparation",
        "training_items": [("laptop", 24), ("textbook", 28), ("notebook", 29), ("pen", 30)],
        "novel_items": ["book_novel", "sticky_notes", "flashlight"],
    },
    {
        "chore_type": "Clothing Pickup",
        "context": "End-of-week wardrobe reset",
        "training_items": [("jacket", 31), ("shoes", 32), ("sunglasses", 38)],
        "novel_items": ["sweater", "backpack", "magazine"],
    },
]

# ---------------------------------------------------------------------------
# BACKWARD COMPAT — kept so report_scores.py and old notebooks don't break
# ---------------------------------------------------------------------------

GROUND_TRUTH_EVAL = {
    persona: {
        "power_bank": items["power_bank"],
        "novel":      items.get("book_novel", items.get("magazine", "closet")),
        "sweater":    items["sweater"],
        "bag_of_chips": items["bag_of_chips"],
    }
    for persona, items in NOVEL_ITEM_GROUND_TRUTHS.items()
}

# Old flat CORRECTION_SCENARIOS alias (5-way rotation) kept for any scripts that
# import it directly. Points to the same underlying corrections in chore order.
CORRECTION_SCENARIOS = {
    persona: [
        corrections["Morning Routine"],
        corrections["Grocery Put-Away"],
        corrections["Office Setup"],
        corrections["Electronics Tidy"],
        corrections["Clothing Pickup"],
    ]
    for persona, corrections in CHORE_CORRECTIONS.items()
}
