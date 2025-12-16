import streamlit as st
import random
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import time

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'setup'
    st.session_state.player_score = 0
    st.session_state.computer_score = 0
    st.session_state.turn_score = 0
    st.session_state.dice = [1, 2, 3, 4, 5, 6]
    st.session_state.kept_dice = []
    st.session_state.remaining_dice = 6
    st.session_state.current_player = 'player'
    st.session_state.turn_history = []
    st.session_state.game_history = []
    st.session_state.show_rules = False
    st.session_state.dice_images = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅"
    }
    st.session_state.selected_dice_set = 'standard'
    st.session_state.computer_dice = []
    st.session_state.computer_turn_in_progress = False
    st.session_state.computer_roll_history = []
    st.session_state.computer_current_roll_score = 0
    st.session_state.computer_total_turn_score = 0

# Dice sets
DICE_SETS = {
    'standard': [1, 2, 3, 4, 5, 6],
    'lucky': [1, 1, 5, 5, 3, 6],  # More 1s and 5s
    'odd': [3, 3, 4, 4, 1, 6],  # More 3s and 4s
    'heavenly': [1, 5, 6, 1, 5, 6],  # Only 1s, 5s, 6s
    'loaded': [6, 6, 5, 5, 1, 2],  # High numbers favored
}

# Scoring rules
SCORING_RULES = {
    'single_1': 100,
    'single_5': 50,
    'three_1s': 1000,
    'three_2s': 200,
    'three_3s': 300,
    'three_4s': 400,
    'three_5s': 500,
    'three_6s': 600,
    'straight': 1000,
    'three_pairs': 500,
    'four_of_a_kind': 1000,
    'five_of_a_kind': 2000,
    'six_of_a_kind': 3000,
}


def roll_dice(num_dice: int, dice_set: str) -> List[int]:
    """Roll specified number of dice from the selected dice set"""
    if num_dice <= 0:
        return []

    dice_faces = DICE_SETS[dice_set]
    return [random.choice(dice_faces) for _ in range(num_dice)]


def calculate_score(dice: List[int]) -> Tuple[int, List[Dict]]:
    """
    Calculate score for given dice and return possible scoring combinations.
    Returns: (score, scoring_dice_info)
    """
    if not dice:
        return 0, []

    dice_counts = {i: dice.count(i) for i in range(1, 7)}
    score = 0
    scoring_info = []

    # Check for straight (1-6)
    if all(count == 1 for count in dice_counts.values()) and len(dice) == 6:
        score += SCORING_RULES['straight']
        scoring_info.append({
            'dice': dice.copy(),
            'rule': 'straight',
            'points': SCORING_RULES['straight']
        })
        return score, scoring_info

    # Check for three pairs
    pairs = [count for count in dice_counts.values() if count == 2]
    if len(pairs) == 3 and len(dice) == 6:
        score += SCORING_RULES['three_pairs']
        scoring_info.append({
            'dice': dice.copy(),
            'rule': 'three_pairs',
            'points': SCORING_RULES['three_pairs']
        })
        return score, scoring_info

    # Check for six of a kind
    for value, count in dice_counts.items():
        if count == 6:
            score += SCORING_RULES['six_of_a_kind']
            scoring_info.append({
                'dice': [value] * 6,
                'rule': f'six_of_a_kind ({value}s)',
                'points': SCORING_RULES['six_of_a_kind']
            })
            return score, scoring_info

    # Check for five of a kind
    for value, count in dice_counts.items():
        if count == 5:
            score += SCORING_RULES['five_of_a_kind']
            scoring_info.append({
                'dice': [value] * 5,
                'rule': f'five_of_a_kind ({value}s)',
                'points': SCORING_RULES['five_of_a_kind']
            })
            # Check remaining single die
            remaining_dice = [v for v in dice if v != value]
            if remaining_dice:
                single_score, single_info = calculate_score(remaining_dice)
                score += single_score
                scoring_info.extend(single_info)
            return score, scoring_info

    # Check for four of a kind
    for value, count in dice_counts.items():
        if count == 4:
            score += SCORING_RULES['four_of_a_kind']
            scoring_info.append({
                'dice': [value] * 4,
                'rule': f'four_of_a_kind ({value}s)',
                'points': SCORING_RULES['four_of_a_kind']
            })
            # Check remaining two dice
            remaining_dice = [v for v in dice if v != value]
            if remaining_dice:
                single_score, single_info = calculate_score(remaining_dice)
                score += single_score
                scoring_info.extend(single_info)
            return score, scoring_info

    # Check for three of a kind
    for value, count in dice_counts.items():
        if count == 3:
            if value == 1:
                score += SCORING_RULES['three_1s']
                scoring_info.append({
                    'dice': [1, 1, 1],
                    'rule': 'three_1s',
                    'points': SCORING_RULES['three_1s']
                })
            else:
                score += SCORING_RULES[f'three_{value}s']
                scoring_info.append({
                    'dice': [value, value, value],
                    'rule': f'three_{value}s',
                    'points': SCORING_RULES[f'three_{value}s']
                })

            # Check remaining dice
            remaining_dice = [v for v in dice if v != value]
            if remaining_dice:
                single_score, single_info = calculate_score(remaining_dice)
                score += single_score
                scoring_info.extend(single_info)
            return score, scoring_info

    # Check for single 1s and 5s
    temp_dice = dice.copy()
    scoring_dice = []

    for die in temp_dice:
        if die == 1:
            score += SCORING_RULES['single_1']
            scoring_dice.append(die)
            scoring_info.append({
                'dice': [1],
                'rule': 'single_1',
                'points': SCORING_RULES['single_1']
            })
        elif die == 5:
            score += SCORING_RULES['single_5']
            scoring_dice.append(die)
            scoring_info.append({
                'dice': [5],
                'rule': 'single_5',
                'points': SCORING_RULES['single_5']
            })

    # Remove scored dice from consideration for combinations
    for die in scoring_dice:
        if die in temp_dice:
            temp_dice.remove(die)

    return score, scoring_info


def can_score(dice: List[int]) -> bool:
    """Check if any scoring combination exists in the dice"""
    score, _ = calculate_score(dice)
    return score > 0


def computer_turn_step():
    """Execute one step of the computer's turn (one roll)"""
    if st.session_state.computer_turn_in_progress:
        # Roll dice
        dice = roll_dice(st.session_state.remaining_dice, st.session_state.selected_dice_set)
        st.session_state.computer_dice = dice

        # Check if any scoring dice
        if not can_score(dice):
            st.session_state.turn_history.append(
                f"🤖 Computer Farkled! Lost {st.session_state.computer_total_turn_score} points."
            )
            st.session_state.computer_turn_in_progress = False
            return False

        # Calculate score for this roll
        roll_score, scoring_info = calculate_score(dice)
        st.session_state.computer_current_roll_score = roll_score
        st.session_state.computer_total_turn_score += roll_score

        # Record roll
        dice_str = " ".join([st.session_state.dice_images[d] for d in dice])
        roll_record = {
            'dice': dice,
            'score': roll_score,
            'scoring_info': scoring_info,
            'remaining_dice': st.session_state.remaining_dice
        }
        st.session_state.computer_roll_history.append(roll_record)

        # Count scoring dice for hot dice
        scoring_dice_count = 0
        for combo in scoring_info:
            scoring_dice_count += len(combo['dice'])

        # Update remaining dice
        st.session_state.remaining_dice -= scoring_dice_count
        if st.session_state.remaining_dice == 0:  # Hot dice
            st.session_state.remaining_dice = 6

        # Computer decision making
        behind_by = st.session_state.player_score - st.session_state.computer_score

        # Determine if computer should continue
        should_continue = True

        if st.session_state.computer_total_turn_score >= 1000:
            should_continue = False
        elif st.session_state.remaining_dice <= 2 and st.session_state.computer_total_turn_score >= 750:
            should_continue = False
        elif behind_by > 1000 and st.session_state.computer_total_turn_score < 1500:
            should_continue = True  # Take more risks when far behind
        elif behind_by > 500 and st.session_state.remaining_dice >= 3:
            should_continue = True
        else:
            # Random element to make computer more human-like
            should_continue = random.random() < 0.5  # 50% chance to keep rolling

        if not should_continue:
            # Computer decides to bank
            st.session_state.computer_score += st.session_state.computer_total_turn_score
            st.session_state.turn_history.append(
                f"🤖 Computer banked {st.session_state.computer_total_turn_score} points."
            )
            st.session_state.computer_turn_in_progress = False

            # Check win condition
            if st.session_state.computer_score >= 10000:
                st.session_state.game_state = 'game_over'
                st.session_state.turn_history.append("💀 COMPUTER WINS THE GAME!")
            return False

        return True  # Continue rolling


def reset_computer_turn():
    """Reset computer turn state"""
    st.session_state.computer_dice = []
    st.session_state.computer_roll_history = []
    st.session_state.computer_current_roll_score = 0
    st.session_state.computer_total_turn_score = 0
    st.session_state.computer_turn_in_progress = True


def reset_turn():
    """Reset for a new turn"""
    st.session_state.turn_score = 0
    st.session_state.dice = []
    st.session_state.kept_dice = []
    st.session_state.remaining_dice = 6
    st.session_state.computer_dice = []
    st.session_state.computer_roll_history = []
    st.session_state.computer_current_roll_score = 0
    st.session_state.computer_total_turn_score = 0
    st.session_state.computer_turn_in_progress = False


def start_new_game():
    """Initialize a new game"""
    st.session_state.player_score = 0
    st.session_state.computer_score = 0
    st.session_state.game_state = 'playing'
    st.session_state.current_player = 'player'
    st.session_state.turn_history = []
    st.session_state.turn_score = 0
    st.session_state.dice = []
    st.session_state.kept_dice = []
    st.session_state.remaining_dice = 6
    st.session_state.computer_dice = []
    st.session_state.computer_roll_history = []
    st.session_state.computer_current_roll_score = 0
    st.session_state.computer_total_turn_score = 0
    st.session_state.computer_turn_in_progress = False
    st.session_state.game_history.append({
        'start_time': datetime.now().strftime("%H:%M:%S"),
        'player_score': 0,
        'computer_score': 0
    })


# Streamlit UI
st.set_page_config(
    page_title="Farkle - Dice Game",
    page_icon="🎲",
    layout="wide"
)

# Custom CSS with HIGH CONTRAST COLORS - UPDATED DICE DISPLAY STYLES
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #5D2906;  /* Darker brown for better contrast */
        font-size: 3em;
        font-weight: bold;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        background: linear-gradient(45deg, #FFD700, #FFA500); /* Gold gradient */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .score-card {
        background: linear-gradient(135deg, #FFF8DC, #F5DEB3); /* Brighter parchment */
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        border: 4px solid #8B0000; /* Dark red border */
    }

    /* UPDATED DICE DISPLAY STYLES WITH HIGH CONTRAST */
    .dice-display {
        font-size: 4em; /* Larger dice */
        text-align: center;
        margin: 20px auto;
        min-height: 120px;
        padding: 25px;
        background: linear-gradient(135deg, #000000, #222222) !important;
        border-radius: 15px;
        border: 5px solid #FFFFFF !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.6), inset 0 0 20px rgba(255,255,255,0.2);
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
    }

    .player-dice-display {
        background: linear-gradient(135deg, #00008B, #0000CD) !important;
        border: 5px solid #00FFFF !important;
        box-shadow: 0 10px 25px rgba(0,100,255,0.7), 0 0 30px rgba(0,255,255,0.4);
    }

    .computer-dice-display {
        background: linear-gradient(135deg, #8B0000, #B22222) !important;
        border: 5px solid #FFD700 !important;
        box-shadow: 0 10px 25px rgba(255,0,0,0.7), 0 0 30px rgba(255,215,0,0.4);
    }

    .dice-character {
        display: inline-block;
        width: 80px;
        height: 80px;
        line-height: 80px;
        text-align: center;
        background: #FFFFFF !important;
        border-radius: 15px;
        border: 4px solid #FF0000 !important;
        margin: 0 5px;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        box-shadow: 0 5px 15px rgba(0,0,0,0.5), inset 0 0 10px rgba(0,0,0,0.1);
    }

    .dice-roll-label {
        font-size: 1.8em;
        font-weight: bold;
        text-align: center;
        margin: 15px 0;
        padding: 12px;
        border-radius: 10px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .player-roll-label {
        color: #00FFFF !important;
        background: linear-gradient(90deg, #00008B, #0000FF);
        border: 3px solid #00FFFF;
    }

    .computer-roll-label {
        color: #FFD700 !important;
        background: linear-gradient(90deg, #8B0000, #B22222);
        border: 3px solid #FFD700;
    }

    .roll-score-display {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin: 20px auto;
        padding: 20px;
        border-radius: 15px;
        border: 4px solid;
        background: #FFFFFF;
        max-width: 80%;
    }

    .player-score-display {
        color: #0000FF !important;
        border-color: #0000FF !important;
        background: linear-gradient(135deg, #E6F3FF, #C2E0FF) !important;
        box-shadow: 0 8px 20px rgba(0,0,255,0.3);
    }

    .computer-score-display {
        color: #FF0000 !important;
        border-color: #FF0000 !important;
        background: linear-gradient(135deg, #FFE6E6, #FFC2C2) !important;
        box-shadow: 0 8px 20px rgba(255,0,0,0.3);
    }

    .scoring-breakdown {
        background: #FFFFFF !important;
        border: 4px solid #000000 !important;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }

    .scoring-item {
        background: linear-gradient(135deg, #F8F8FF, #F0F0FF);
        border-left: 8px solid;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-right: 3px solid #000000;
    }

    .scoring-dice {
        font-size: 2.5em;
        margin: 10px 0;
        text-align: center;
    }

    /* Dice colors for maximum contrast */
    .dice-1 { color: #FF0000 !important; text-shadow: 2px 2px 4px rgba(255,0,0,0.5); }
    .dice-2 { color: #0000FF !important; text-shadow: 2px 2px 4px rgba(0,0,255,0.5); }
    .dice-3 { color: #008000 !important; text-shadow: 2px 2px 4px rgba(0,128,0,0.5); }
    .dice-4 { color: #FF8C00 !important; text-shadow: 2px 2px 4px rgba(255,140,0,0.5); }
    .dice-5 { color: #800080 !important; text-shadow: 2px 2px 4px rgba(128,0,128,0.5); }
    .dice-6 { color: #000000 !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }

    .player-turn {
        background: linear-gradient(135deg, #E0FFFF, #87CEEB) !important; /* Bright cyan */
        border: 4px solid #0000FF !important; /* Bright blue */
        box-shadow: 0 0 15px rgba(0, 100, 255, 0.5);
    }
    .computer-turn {
        background: linear-gradient(135deg, #FFE4E1, #FFB6C1) !important; /* Bright pink */
        border: 4px solid #FF0000 !important; /* Bright red */
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #8B0000, #B22222); /* Dark to medium red */
        color: #FFFFFF !important; /* White text */
        font-weight: bold;
        border: none;
        padding: 14px 28px;
        border-radius: 12px;
        transition: all 0.3s;
        font-size: 1.1em;
        border: 2px solid #000000; /* Black border */
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #B22222, #8B0000);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(178, 34, 34, 0.4);
    }
    .history-box {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        max-height: 350px;
        overflow-y: auto;
        border: 3px solid #000000; /* Black border */
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
    }
    .roll-history-item {
        padding: 10px;
        margin: 8px 0;
        border-radius: 8px;
        background: #F8F8FF;
        border-left: 6px solid #8B0000;
        font-weight: 500;
    }
    .computer-thinking {
        animation: pulse 1.5s infinite;
        padding: 15px;
        border-radius: 12px;
        background: linear-gradient(90deg, #FF0000, #FF4500); /* Red to orange */
        color: #FFFFFF !important; /* White text */
        text-align: center;
        font-weight: bold;
        font-size: 1.2em;
        border: 3px solid #000000; /* Black border */
    }
    @keyframes pulse {
        0% { 
            opacity: 0.8;
            box-shadow: 0 0 10px rgba(255, 69, 0, 0.5);
        }
        50% { 
            opacity: 1;
            box-shadow: 0 0 20px rgba(255, 69, 0, 0.8);
        }
        100% { 
            opacity: 0.8;
            box-shadow: 0 0 10px rgba(255, 69, 0, 0.5);
        }
    }
    .stSuccess {
        background-color: #90EE90 !important; /* Light green */
        color: #006400 !important; /* Dark green text */
        border: 3px solid #006400 !important;
    }
    .stError {
        background-color: #FFCCCB !important; /* Light red */
        color: #8B0000 !important; /* Dark red text */
        border: 3px solid #8B0000 !important;
    }
    .stInfo {
        background-color: #ADD8E6 !important; /* Light blue */
        color: #00008B !important; /* Dark blue text */
        border: 3px solid #00008B !important;
    }
    .metric-card {
        background: linear-gradient(135deg, #E6E6FA, #D8BFD8); /* Lavender */
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 3px solid #4B0082; /* Indigo */
    }
    .section-header {
        color: #8B0000; /* Dark red */
        font-weight: bold;
        border-bottom: 3px solid #8B0000;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background: linear-gradient(180deg, #2F4F4F, #1C1C1C) !important; /* Dark gradient */
    }
    /* Better scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #F5F5F5;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb {
        background: #8B0000;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #B22222;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">🎲 FARKLE 🎲</div>', unsafe_allow_html=True)

# Sidebar for controls and info
with st.sidebar:
    st.markdown('<h2 style="color: #FFD700;">🎮 Game Controls</h2>', unsafe_allow_html=True)

    if st.button("🎮 NEW GAME", use_container_width=True, type="primary"):
        start_new_game()

    if st.button("📜 SHOW/HIDE RULES", use_container_width=True):
        st.session_state.show_rules = not st.session_state.show_rules

    st.divider()

    st.markdown('<h2 style="color: #FFD700;">🎲 Dice Selection</h2>', unsafe_allow_html=True)
    dice_set_option = st.selectbox(
        "Choose your dice set:",
        options=list(DICE_SETS.keys()),
        format_func=lambda x: x.title(),
        key="dice_select"
    )
    st.session_state.selected_dice_set = dice_set_option

    # Dice set descriptions with better contrast
    dice_descriptions = {
        'standard': "🎲 Balanced dice (1-6)",
        'lucky': "🍀 More 1s and 5s (easier scoring)",
        'odd': "🎭 More 3s and 4s (better for triples)",
        'heavenly': "👑 Only 1, 5, 6 (no 2, 3, 4)",
        'loaded': "🎯 High numbers favored (more 5s, 6s)"
    }

    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        border: 3px solid #8B0000;
        margin: 10px 0;
    ">
    <h4 style="color: #8B0000; margin: 0;">🎯 {dice_set_option.title()} Dice</h4>
    <p style="color: #000000; margin: 5px 0 0 0;">{dice_descriptions[dice_set_option]}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(
        '<h2 style="color: #FFD700; background: #000000; padding: 10px; border-radius: 8px; border: 3px solid #FFD700;">📊 SCORING RULES</h2>',
        unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #FFFFFF, #F0F0F0);
        padding: 20px;
        border-radius: 12px;
        border: 4px solid #000000;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    ">
    <ul style="
        list-style-type: none;
        padding-left: 0;
        margin: 0;
    ">
    <li style="
        background: #FFEBEE;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #D32F2F;
        border-right: 2px solid #D32F2F;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Single 1:</strong> 
    <span style="color: #D32F2F; font-weight: bold; font-size: 1.2em;">100 points</span>
    </li>

    <li style="
        background: #E3F2FD;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #1976D2;
        border-right: 2px solid #1976D2;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Single 5:</strong> 
    <span style="color: #1976D2; font-weight: bold; font-size: 1.2em;">50 points</span>
    </li>

    <li style="
        background: #FFF3E0;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #F57C00;
        border-right: 2px solid #F57C00;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Three 1s:</strong> 
    <span style="color: #D32F2F; font-weight: bold; font-size: 1.2em;">1,000 points</span>
    </li>

    <li style="
        background: #E8F5E9;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #388E3C;
        border-right: 2px solid #388E3C;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Three 2s-6s:</strong> 
    <span style="color: #388E3C; font-weight: bold; font-size: 1.2em;">200-600 points</span>
    <div style="color: #666666; font-size: 0.9em; margin-top: 5px;">
    (2s: 200, 3s: 300, 4s: 400, 5s: 500, 6s: 600)
    </div>
    </li>

    <li style="
        background: #F3E5F5;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #7B1FA2;
        border-right: 2px solid #7B1FA2;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Straight (1-6):</strong> 
    <span style="color: #7B1FA2; font-weight: bold; font-size: 1.2em;">1,000 points</span>
    </li>

    <li style="
        background: #FFF8E1;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #FF8F00;
        border-right: 2px solid #FF8F00;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Three Pairs:</strong> 
    <span style="color: #FF8F00; font-weight: bold; font-size: 1.2em;">500 points</span>
    </li>

    <li style="
        background: #E0F7FA;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #0097A7;
        border-right: 2px solid #0097A7;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Four of a Kind:</strong> 
    <span style="color: #0097A7; font-weight: bold; font-size: 1.2em;">1,000 points</span>
    </li>

    <li style="
        background: #E8F5E9;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #43A047;
        border-right: 2px solid #43A047;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Five of a Kind:</strong> 
    <span style="color: #43A047; font-weight: bold; font-size: 1.2em;">2,000 points</span>
    </li>

    <li style="
        background: #FFEBEE;
        margin: 10px 0;
        padding: 15px;
        border-radius: 8px;
        border-left: 8px solid #C62828;
        border-right: 2px solid #C62828;
    ">
    <strong style="color: #000000; font-size: 1.1em;">Six of a Kind:</strong> 
    <span style="color: #C62828; font-weight: bold; font-size: 1.2em;">3,000 points</span>
    </li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<h3 style="color: #FFD700; text-align: center;">🎯 FIRST TO 10 000 POINTS WINS! 🏆</h3>',
                unsafe_allow_html=True)

# Main game area
col1, col2 = st.columns([2, 1])

with col1:
    # Game state
    if st.session_state.game_state == 'setup':
        st.markdown("### 🎮 Welcome to Farkle!")
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #FFF8DC, #F5DEB3);
            padding: 25px;
            border-radius: 15px;
            border: 4px solid #8B0000;
        ">

        <h4 style="color: #00008B;">🎯 How to Play:</h4>
        <ol style="color: #000000;">
        <li><strong>Click "NEW GAME" to start</strong></li>
        <li><strong>Roll dice and select scoring combinations</strong></li>
        <li><strong>Bank your points before you Farkle!</strong></li>
        <li><strong>First to 10,000 points wins</strong></li>
        </ol>

        <h4 style="color: #00008B;">⚡ Key Rules:</h4>
        <ul style="color: #000000;">
        <li>You <strong>MUST</strong> score at least one die each roll</li>
        <li>If no scoring dice, you <strong>FARKLE</strong> and lose all points for that turn</li>
        <li><strong>HOT DICE</strong>: Score all 6 dice → roll all 6 again!</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 START PLAYING NOW!", use_container_width=True, type="primary"):
            start_new_game()

    elif st.session_state.game_state == 'playing':
        # Score display
        score_col1, score_col2 = st.columns(2)

        with score_col1:
            turn_class = "player-turn" if st.session_state.current_player == 'player' else ""
            st.markdown(f'<div class="score-card {turn_class}">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #0000FF;">🧑 PLAYER SCORE</h3>', unsafe_allow_html=True)
            st.markdown(f'<h1 style="color: #0000FF; font-size: 3em;">{st.session_state.player_score}</h1>',
                        unsafe_allow_html=True)
            if st.session_state.current_player == 'player':
                st.markdown(
                    f'<h4 style="color: #00008B;">🎯 Current Turn: <span style="color: #FF0000;">{st.session_state.turn_score}</span> points</h4>',
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with score_col2:
            turn_class = "computer-turn" if st.session_state.current_player == 'computer' else ""
            st.markdown(f'<div class="score-card {turn_class}">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #FF0000;">🤖 COMPUTER SCORE</h3>', unsafe_allow_html=True)
            st.markdown(f'<h1 style="color: #FF0000; font-size: 3em;">{st.session_state.computer_score}</h1>',
                        unsafe_allow_html=True)
            if st.session_state.current_player == 'computer':
                st.markdown(
                    f'<h4 style="color: #8B0000;">🎯 Current Turn: <span style="color: #0000FF;">{st.session_state.computer_total_turn_score}</span> points</h4>',
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        if st.session_state.current_player == 'player':
            # Player's turn
            st.markdown('<h3 style="color: #0000FF; border-bottom: 3px solid #0000FF;">🧑 YOUR TURN</h3>',
                        unsafe_allow_html=True)

            if st.session_state.remaining_dice > 0 and not st.session_state.dice:
                # First roll of turn
                if st.button("🎲 ROLL DICE!", use_container_width=True, type="primary"):
                    st.session_state.dice = roll_dice(
                        st.session_state.remaining_dice,
                        st.session_state.selected_dice_set
                    )

                    # Check for Farkle
                    if not can_score(st.session_state.dice):
                        st.session_state.turn_history.append(
                            f"🎯 PLAYER FARKLED! Lost {st.session_state.turn_score} points."
                        )
                        st.session_state.turn_score = 0
                        st.session_state.current_player = 'computer'
                        reset_computer_turn()
                        st.rerun()

            elif st.session_state.dice:
                # Display current dice with high contrast
                st.markdown(f'<div class="dice-roll-label player-roll-label">🎲 YOUR DICE ROLL 🎲</div>',
                            unsafe_allow_html=True)

                # Create individual dice characters with high contrast
                dice_html = '<div class="dice-display player-dice-display">'
                for d in st.session_state.dice:
                    dice_class = f"dice-{d}"
                    dice_html += f'<span class="dice-character {dice_class}">{st.session_state.dice_images[d]}</span>'
                dice_html += '</div>'
                st.markdown(dice_html, unsafe_allow_html=True)

                # Calculate scoring options
                score, scoring_info = calculate_score(st.session_state.dice)

                if score > 0:
                    st.markdown(f'''
                    <div class="roll-score-display player-score-display">
                    🎯 AVAILABLE SCORE: <span style="color: #FF0000; font-size: 1.2em;">{score}</span> POINTS 🎯
                    </div>
                    ''', unsafe_allow_html=True)

                    # Show scoring breakdown with high contrast
                    st.markdown('<div class="scoring-breakdown">', unsafe_allow_html=True)
                    st.markdown(
                        '<h4 style="color: #000000; text-align: center; border-bottom: 3px solid #0000FF; padding-bottom: 10px;">📊 SCORING BREAKDOWN</h4>',
                        unsafe_allow_html=True)

                    for combo in scoring_info:
                        dice_str = " ".join([st.session_state.dice_images[d] for d in combo['dice']])
                        # Color-code based on points
                        if combo['points'] >= 1000:
                            border_color = "#FF0000"
                            bg_color = "#FFF0F0"
                        elif combo['points'] >= 500:
                            border_color = "#FF8C00"
                            bg_color = "#FFF8F0"
                        else:
                            border_color = "#0000FF"
                            bg_color = "#F0F8FF"

                        st.markdown(f'''
                        <div class="scoring-item" style="border-left-color: {border_color}; background: {bg_color};">
                        <div class="scoring-dice" style="color: {border_color};">{dice_str}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #000000; font-weight: bold; font-size: 1.1em;">{combo['rule'].upper()}</span>
                            <span style="color: {border_color}; font-weight: bold; font-size: 1.3em; background: #FFFFFF; padding: 5px 15px; border-radius: 5px; border: 2px solid {border_color};">{combo['points']} pts</span>
                        </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if st.button("✅ BANK POINTS", use_container_width=True, type="secondary"):
                            st.session_state.player_score += st.session_state.turn_score + score
                            st.session_state.turn_history.append(
                                f"🏦 PLAYER BANKED {st.session_state.turn_score + score} POINTS"
                            )

                            # Check win condition
                            if st.session_state.player_score >= 10000:
                                st.session_state.game_state = 'game_over'
                                st.session_state.turn_history.append("🎉 🎉 PLAYER WINS THE GAME! 🎉 🎉")
                            else:
                                st.session_state.current_player = 'computer'
                                reset_computer_turn()
                            reset_turn()
                            st.rerun()

                    with col_b:
                        if st.button("🎯 KEEP SCORING DICE", use_container_width=True):
                            st.session_state.kept_dice.extend(st.session_state.dice)
                            st.session_state.turn_score += score

                            # Count scoring dice for hot dice
                            scoring_dice_count = 0
                            for combo in scoring_info:
                                scoring_dice_count += len(combo['dice'])

                            st.session_state.remaining_dice -= scoring_dice_count

                            if st.session_state.remaining_dice == 0:  # Hot dice
                                st.session_state.remaining_dice = 6
                                st.session_state.turn_history.append("🔥 🔥 HOT DICE! Roll all 6 again! 🔥")

                            st.session_state.dice = []
                            st.rerun()

                    with col_c:
                        if st.button("🔄 RE-ROLL REMAINING", use_container_width=True):
                            st.session_state.dice = []
                            st.rerun()

                else:
                    st.error("❌ NO SCORING DICE AVAILABLE!")
                    if st.button("❌ END TURN (FARKLE)", use_container_width=True):
                        st.session_state.turn_history.append(
                            f"🎯 PLAYER FARKLED! Lost {st.session_state.turn_score} points."
                        )
                        st.session_state.turn_score = 0
                        st.session_state.current_player = 'computer'
                        reset_computer_turn()
                        reset_turn()
                        st.rerun()

        else:
            # Computer's turn
            st.markdown('<h3 style="color: #FF0000; border-bottom: 3px solid #FF0000;">🤖 COMPUTER\'S TURN</h3>',
                        unsafe_allow_html=True)

            # Show current computer dice if any
            if st.session_state.computer_dice:
                st.markdown(f'<div class="dice-roll-label computer-roll-label">🤖 COMPUTER\'S DICE ROLL 🤖</div>',
                            unsafe_allow_html=True)

                # Create individual dice characters with high contrast
                dice_html = '<div class="dice-display computer-dice-display">'
                for d in st.session_state.computer_dice:
                    dice_class = f"dice-{d}"
                    dice_html += f'<span class="dice-character {dice_class}">{st.session_state.dice_images[d]}</span>'
                dice_html += '</div>'
                st.markdown(dice_html, unsafe_allow_html=True)

                # Show score for current roll
                if st.session_state.computer_current_roll_score > 0:
                    score, scoring_info = calculate_score(st.session_state.computer_dice)
                    st.markdown(f'''
                    <div class="roll-score-display computer-score-display">
                    🤖 COMPUTER SCORED: <span style="color: #000000; font-size: 1.2em;">{score}</span> POINTS 🤖
                    </div>
                    ''', unsafe_allow_html=True)

                    # Show scoring combinations with high contrast
                    if scoring_info:
                        st.markdown('<div class="scoring-breakdown">', unsafe_allow_html=True)
                        st.markdown(
                            '<h4 style="color: #000000; text-align: center; border-bottom: 3px solid #FF0000; padding-bottom: 10px;">🤖 COMPUTER\'S SCORING</h4>',
                            unsafe_allow_html=True)

                        for combo in scoring_info:
                            dice_str = " ".join([st.session_state.dice_images[d] for d in combo['dice']])
                            # Color-code based on points
                            if combo['points'] >= 1000:
                                border_color = "#FF0000"
                                bg_color = "#FFF0F0"
                            elif combo['points'] >= 500:
                                border_color = "#FF8C00"
                                bg_color = "#FFF8F0"
                            else:
                                border_color = "#8B0000"
                                bg_color = "#F8F0F0"

                            st.markdown(f'''
                            <div class="scoring-item" style="border-left-color: {border_color}; background: {bg_color};">
                            <div class="scoring-dice" style="color: {border_color};">{dice_str}</div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: #000000; font-weight: bold; font-size: 1.1em;">{combo['rule'].upper()}</span>
                                <span style="color: {border_color}; font-weight: bold; font-size: 1.3em; background: #FFFFFF; padding: 5px 15px; border-radius: 5px; border: 2px solid {border_color};">{combo['points']} pts</span>
                            </div>
                            </div>
                            ''', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

            # Show thinking/status
            if st.session_state.computer_turn_in_progress:
                st.markdown('<div class="computer-thinking">🤖 COMPUTER IS THINKING... 🤖</div>', unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)
                with col_b:
                    if st.button("🎲 COMPUTER ROLLS", use_container_width=True, type="primary"):
                        continue_turn = computer_turn_step()
                        if not continue_turn:
                            # Computer's turn ended
                            st.session_state.current_player = 'player'
                            reset_turn()
                        st.rerun()
            else:
                # Start computer turn
                if st.button("🤖 START COMPUTER TURN", use_container_width=True, type="secondary"):
                    st.session_state.computer_turn_in_progress = True
                    st.rerun()

            # Show computer roll history
            if st.session_state.computer_roll_history:
                st.markdown(
                    '<h4 style="color: #000000; background: #FFD700; padding: 10px; border-radius: 8px; border: 3px solid #8B0000; text-align: center;">📊 COMPUTER\'S ROLL HISTORY</h4>',
                    unsafe_allow_html=True)

                for i, roll in enumerate(st.session_state.computer_roll_history, 1):
                    # Create a high contrast card for each roll
                    with st.expander(f"🎲 ROLL #{i}: {roll['score']} POINTS ({roll['remaining_dice']} dice remaining)",
                                     expanded=False):
                        # Display dice with high contrast
                        dice_html = '<div style="background: #000000; padding: 15px; border-radius: 10px; border: 3px solid #FFD700; margin: 10px 0; text-align: center;">'
                        for d in roll['dice']:
                            dice_class = f"dice-{d}"
                            dice_html += f'<span class="dice-character {dice_class}" style="margin: 5px;">{st.session_state.dice_images[d]}</span>'
                        dice_html += '</div>'
                        st.markdown(dice_html, unsafe_allow_html=True)

                        # Display score
                        st.markdown(f'''
                        <div style="
                            background: linear-gradient(135deg, #FFFFFF, #F8F8F8);
                            padding: 15px;
                            border-radius: 10px;
                            border: 3px solid #FF0000;
                            margin: 10px 0;
                            text-align: center;
                        ">
                        <span style="color: #000000; font-weight: bold; font-size: 1.2em;">SCORE:</span>
                        <span style="color: #FF0000; font-weight: bold; font-size: 1.5em; margin-left: 10px;">{roll['score']} POINTS</span>
                        </div>
                        ''', unsafe_allow_html=True)

                        # Display scoring combinations
                        if roll['scoring_info']:
                            st.markdown(
                                '<h5 style="color: #000000; border-bottom: 2px solid #0000FF; padding-bottom: 5px;">🎯 SCORING COMBINATIONS:</h5>',
                                unsafe_allow_html=True)
                            for combo in roll['scoring_info']:
                                dice_str = " ".join([st.session_state.dice_images[d] for d in combo['dice']])
                                st.markdown(f'''
                                <div style="
                                    background: #FFFFFF;
                                    padding: 10px;
                                    margin: 5px 0;
                                    border-radius: 8px;
                                    border-left: 6px solid #008000;
                                    border-right: 2px solid #000000;
                                ">
                                <div style="color: #000000; font-weight: bold;">🎲 {dice_str}</div>
                                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                                    <span style="color: #000000;">{combo['rule']}</span>
                                    <span style="color: #FF0000; font-weight: bold;">{combo['points']} pts</span>
                                </div>
                                </div>
                                ''', unsafe_allow_html=True)

    elif st.session_state.game_state == 'game_over':
        st.balloons()

        # FIX: Changed from 1000 to 10000 for win condition
        winner = "PLAYER" if st.session_state.player_score >= 10000 else "COMPUTER"
        winner_color = "#0000FF" if winner == "PLAYER" else "#FF0000"

        st.markdown(f'<h1 style="color: {winner_color}; text-align: center; font-size: 4em;">🏆 {winner} WINS! 🏆</h1>',
                    unsafe_allow_html=True)

        col1_final, col2_final = st.columns(2)
        with col1_final:
            st.markdown(f"""
            <div class="score-card player-turn">
            <h3 style="color: #0000FF;">🧑 FINAL PLAYER SCORE</h3>
            <h1 style="color: #0000FF; font-size: 4em;">{st.session_state.player_score}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col2_final:
            st.markdown(f"""
            <div class="score-card computer-turn">
            <h3 style="color: #FF0000;">🤖 FINAL COMPUTER SCORE</h3>
            <h1 style="color: #FF0000; font-size: 4em;">{st.session_state.computer_score}</h1>
            </div>
            """, unsafe_allow_html=True)

        # Show final computer roll history if any
        if st.session_state.computer_roll_history:
            st.markdown(
                '<h3 style="color: #FFFFFF; background: #000000; padding: 15px; border-radius: 10px; border: 4px solid #FF0000; text-align: center;">🤖 COMPUTER\'S FINAL TURN</h3>',
                unsafe_allow_html=True)

            for i, roll in enumerate(st.session_state.computer_roll_history, 1):
                # High contrast dice display
                dice_html = '<div style="background: #000000; padding: 20px; border-radius: 12px; border: 4px solid #FFD700; margin: 15px 0; text-align: center;">'
                for d in roll['dice']:
                    dice_class = f"dice-{d}"
                    dice_html += f'<span class="dice-character {dice_class}" style="margin: 8px;">{st.session_state.dice_images[d]}</span>'
                dice_html += '</div>'
                st.markdown(dice_html, unsafe_allow_html=True)

                st.markdown(f'''
                <div style="
                    background: linear-gradient(135deg, #FFFFFF, #F0F0F0);
                    padding: 20px;
                    border-radius: 12px;
                    border: 4px solid #000000;
                    margin: 15px 0;
                    text-align: center;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
                ">
                <div style="color: #000000; font-size: 1.3em; margin-bottom: 10px;">
                    <strong>🎲 ROLL #{i}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 20px;">
                    <div style="color: #000000; font-size: 1.1em;">Dice: {roll['remaining_dice']} remaining</div>
                    <div style="color: #FF0000; font-weight: bold; font-size: 1.8em; background: #FFFFFF; padding: 8px 20px; border-radius: 8px; border: 3px solid #FF0000;">
                        {roll['score']} POINTS
                    </div>
                </div>
                </div>
                ''', unsafe_allow_html=True)

        if st.button("🔄 PLAY AGAIN", use_container_width=True, type="primary"):
            start_new_game()

with col2:
    st.markdown('<h3 style="color: #8B0000;">📜 TURN HISTORY</h3>', unsafe_allow_html=True)

    if st.session_state.turn_history:
        history_box = '<div class="history-box">'
        for entry in reversed(st.session_state.turn_history[-12:]):  # Show last 12 entries
            if "FARKLE" in entry.upper():
                history_box += f'<div class="roll-history-item" style="border-left-color: #FF0000; background: #FFE4E1;">'
                history_box += f'<span style="color: #FF0000; font-weight: bold;">⚠️ {entry}</span>'
            elif "BANKED" in entry.upper():
                history_box += f'<div class="roll-history-item" style="border-left-color: #008000; background: #F0FFF0;">'
                history_box += f'<span style="color: #008000; font-weight: bold;">💰 {entry}</span>'
            elif "WINS" in entry.upper():
                history_box += f'<div class="roll-history-item" style="border-left-color: #FFD700; background: #FFFACD;">'
                history_box += f'<span style="color: #8B0000; font-weight: bold; font-size: 1.1em;">🎯 {entry}</span>'
            elif "HOT DICE" in entry.upper():
                history_box += f'<div class="roll-history-item" style="border-left-color: #FF4500; background: #FFE4B5;">'
                history_box += f'<span style="color: #FF4500; font-weight: bold;">🔥 {entry}</span>'
            elif "COMPUTER" in entry.upper():
                history_box += f'<div class="roll-history-item" style="border-left-color: #8B008B; background: #E6E6FA;">'
                history_box += f'<span style="color: #8B008B; font-weight: bold;">🤖 {entry}</span>'
            else:
                history_box += f'<div class="roll-history-item" style="border-left-color: #0000FF; background: #F0F8FF;">'
                history_box += f'<span style="color: #0000FF; font-weight: bold;">🎲 {entry}</span>'
            history_box += '</div>'
        history_box += '</div>'
        st.markdown(history_box, unsafe_allow_html=True)
    else:
        st.info("📝 No turns yet. Start playing!")

    st.divider()

    # Show current game stats
    st.markdown('<h3 style="color: #00008B;">🎯 GAME STATUS</h3>', unsafe_allow_html=True)

    if st.session_state.game_state == 'playing':
        if st.session_state.current_player == 'player':
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🎯 PLAYER'S TURN", "YOUR MOVE!", delta=None)
            st.metric("🏆 POINTS NEEDED", 10000 - st.session_state.player_score,
                      delta_color="normal")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🤖 COMPUTER'S TURN", "WATCHING...", delta=None)
            st.metric("🏆 COMPUTER NEEDS", 10000 - st.session_state.computer_score,
                      delta_color="inverse")
            st.markdown('</div>', unsafe_allow_html=True)

        # Dice remaining
        dice_color = "#0000FF" if st.session_state.current_player == 'player' else "#FF0000"
        st.markdown(f"""
        <div style="background: #F8F8FF; padding: 15px; border-radius: 10px; border: 3px solid {dice_color}; margin: 10px 0;">
        <h4 style="color: {dice_color}; margin: 0;">🎲 DICE REMAINING</h4>
        <h2 style="color: {dice_color}; text-align: center; margin: 10px 0;">{st.session_state.remaining_dice}</h2>
        </div>
        """, unsafe_allow_html=True)

        # Turn score
        turn_score = st.session_state.turn_score if st.session_state.current_player == 'player' else st.session_state.computer_total_turn_score
        player_text = "YOUR TURN SCORE" if st.session_state.current_player == 'player' else "COMPUTER'S TURN SCORE"
        st.markdown(f"""
        <div style="background: #FFF8DC; padding: 15px; border-radius: 10px; border: 3px solid #FFA500; margin: 10px 0;">
        <h4 style="color: #FF8C00; margin: 0;">🎯 {player_text}</h4>
        <h2 style="color: #FF8C00; text-align: center; margin: 10px 0;">{turn_score}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Show rules if toggled
    if st.session_state.show_rules:
        st.divider()
        st.markdown('<h3 style="color: #8B0000;">📖 GAME RULES</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background: #FFF8DC; padding: 20px; border-radius: 12px; border: 3px solid #8B0000;">
        <h4 style="color: #00008B;">🎯 OBJECTIVE:</h4>
        <p style="color: #000000;">Be the first to score <strong style="color: #FF0000;">10,000 points</strong>.</p>

        <h4 style="color: #00008B;">🔄 ON YOUR TURN:</h4>
        <ol style="color: #000000;">
        <li><strong>Roll all 6 dice</strong></li>
        <li><strong>Set aside scoring dice</strong> (you must score at least one)</li>
        <li><strong>Choose:</strong> <span style="color: #008000;">BANK</span> or <span style="color: #FF0000;">ROLL AGAIN</span></li>
        </ol>

        <h4 style="color: #00008B;">⚡ IF YOU FARKLE:</h4>
        <p style="color: #000000;">Roll with <strong>NO scoring dice</strong>? You <strong style="color: #FF0000;">FARKLE</strong> and lose <strong>ALL</strong> points for that turn.</p>

        <h4 style="color: #00008B;">🔥 HOT DICE:</h4>
        <p style="color: #000000;">Score <strong>all 6 dice</strong>? Roll <strong>all 6 again</strong>!</p>

        <h4 style="color: #00008B;">💡 STRATEGY TIPS:</h4>
        <ul style="color: #000000;">
        <li><strong>Bank early</strong> when ahead</li>
        <li><strong>Take risks</strong> when behind</li>
        <li><strong>Watch for hot dice</strong> opportunities</li>
        <li><strong>Choose your dice set</strong> wisely</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown(
    "<div style='"
    "text-align: center; "
    "color: #FFFFFF; "
    "background: linear-gradient(90deg, #8B0000, #00008B); "
    "padding: 15px; "
    "border-radius: 10px; "
    "font-weight: bold; "
    "font-size: 1.1em;"
    "'>"
    "🎲 FARKLE | Built with Streamlit 🏰"
    "</div>",
    unsafe_allow_html=True
)

# Auto-refresh during computer turn for animation effect
if st.session_state.computer_turn_in_progress:
    time.sleep(0.5)
    st.rerun()