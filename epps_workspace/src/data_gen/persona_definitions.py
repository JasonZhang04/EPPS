from typing import Dict, Any

PERSONAS = {
    "Minimalist": {
        "description": "You hate visual clutter. Every item must be hidden inside closed receptacles (e.g., inside closets, drawers, or cabinets, fridge). Nothing should be left resting 'ON' a surface if it can be placed 'INSIDE' something.",
        "ground_truth_logic": "Items go INSIDE closed containers."
    },
    "Functionalist": {
        "description": "You prioritize immediate access. You leave items resting 'ON' the surface where they are most frequently used. Electronics go ON the desk, study materials go ON the bookshelf or desk, food goes INSIDE the fridge, but everyday items like keys stay ON the kitchen table.",
        "ground_truth_logic": "Items stay ON context-relevant surfaces."
    },
    "Child_Safe": {
        "description": "You are organizing a room to be safe for a toddler. Dangerous or fragile items (electronics, glass, chemicals, small objects) MUST be placed out of reach (e.g., INSIDE high cabinets or ON high bookshelves). Soft or safe items (clothing) can be placed in lower areas like the closet or sofa.",
        "ground_truth_logic": "Hazardous items are elevated or secured INSIDE high receptacles."
    }
}

GROUND_TRUTH_EVAL = {
    "Minimalist": {
        "power_bank": "desk", 
        "novel": "bookshelf", 
        "sweater": "closet",
        "bag_of_chips": "fridge" 
    },
    "Functionalist": {
        "power_bank": "desk",     
        "novel": "sofa",          
        "sweater": "closet",
        "bag_of_chips": "kitchen_table" 
    },
    "Child_Safe": {
        "power_bank": "bookshelf", 
        "novel": "sofa",           
        "sweater": "closet",       
        "bag_of_chips": "fridge"   
    }
}
