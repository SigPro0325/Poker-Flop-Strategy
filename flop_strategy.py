from collections import Counter
import random

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
rank_to_value = {rank: i for i, rank in enumerate(ranks, start=2)}

hand_strength_values = {
    "Royal Flush": 1.0,
    "Straight Flush": 0.9,
    "Four of a Kind": 0.85,
    "Full House": 0.8,
    "Flush": 0.75,
    "Straight": 0.7,
    "Three of a Kind": 0.65,
    "Two Pair": 0.6,
    "One Pair": 0.5,
    "High Card": 0.4,  # You may adjust these values based on your assessment of hand strength
}

def convert_hand_type_to_strength(hand_type):
    return hand_strength_values.get(hand_type, 0)  # Default to 0 if hand_type not found

def evaluate_hand_strength(hole_cards, community_cards):
    total_cards = hole_cards + community_cards
    sorted_ranks = sorted([rank_to_value[card[0]] for card in total_cards], reverse=True)
    suits = [card[1] for card in total_cards]
    suit_counts = Counter(suits)
    rank_counts = Counter([card[0] for card in total_cards])

    # Check for Straight Flush or Royal Flush
    straight_flush_result, high_card = is_straight_flush(total_cards)  # Ensure this function is defined correctly
    if straight_flush_result:
        if high_card == 14:  # Ace high in a straight flush indicates a Royal Flush
            return "Royal Flush", high_card
        return "Straight Flush", high_card

    # Four of a Kind
    if any(count == 4 for count in rank_counts.values()):
        return "Four of a Kind", max(rank_counts, key=rank_counts.get)

    # Full House
    three_of_a_kind = [rank for rank, count in rank_counts.items() if count == 3]
    pairs = [rank for rank, count in rank_counts.items() if count == 2]
    if three_of_a_kind and pairs:
        return "Full House", max(three_of_a_kind, key=lambda x: rank_to_value[x])

    # Flush
    flush_suit = next((suit for suit, count in suit_counts.items() if count >= 5), None)
    if flush_suit:
        flush_cards = [card for card in total_cards if card[1] == flush_suit]
        flush_ranks = sorted([rank_to_value[card[0]] for card in flush_cards], reverse=True)
        return "Flush", flush_ranks[0]

    # Straight
    straight, highest_straight_card = is_straight(sorted_ranks)
    if straight:
        return "Straight", highest_straight_card

    # Three of a Kind
    if three_of_a_kind:
        return "Three of a Kind", max(three_of_a_kind, key=lambda x: rank_to_value[x])

    # Two Pair
    if len(pairs) >= 2:
        return "Two Pair", max(pairs, key=lambda x: rank_to_value[x])

    # One Pair
    if pairs:
        return "One Pair", pairs[0]

    # High Card
    high_card = max(sorted_ranks)
    return "High Card", high_card




def estimate_hand_potential(hole_cards, flop_cards):
    total_cards = hole_cards + flop_cards
    outs = set()

    
    suits_counts = Counter(card[1] for card in total_cards)
    rank_values = [rank_to_value[card[0]] for card in total_cards]
    rank_counts = Counter(rank_values)

    # Check for flush draw potential
    for suit, count in suits_counts.items():
        if count == 4:
            for rank in ranks:
                if (rank, suit) not in total_cards:
                    outs.add((rank, suit))

    # Check for straight draw potential
    for i in range(len(rank_values) - 2):
        sorted_unique_values = sorted(set(rank_values))
        for start in range(0, len(sorted_unique_values) - 2):
            window = sorted_unique_values[start:start + 5]
            if window[-1] - window[0] <= 4 or (14 in window and len(set([1, 2, 3, 4]).intersection(set(window))) == 4):
                missing_values = set(range(window[0], window[-1] + 1)).difference(sorted_unique_values)
                for value in missing_values:
                    for suit in suits:
                        outs.add((ranks[value-2], suit))

    # Check for improving pairs or three of a kind
    for rank, value in rank_to_value.items():
        if rank_counts.get(value, 0) == 2:
            outs.update({(rank, suit) for suit in suits if (rank, suit) not in total_cards})
        elif rank_counts.get(value, 0) == 3:
            outs.add((rank, next(suit for suit in suits if (rank, suit) not in total_cards)))

    # Convert outs to potential score
    num_outs = len(outs)
    potential_score = num_outs / 47  # Assuming 47 unknown cards after the flop

    hand_potential = min(potential_score, 1)
    return min(potential_score, 1)  # Cap the score at 1


def calculate_bet_amount(hand_strength, hand_potential, pot_size, stack_size):

  base_percentage = 0.5  # Start with a base bet of 50% of the pot

    # Adjust bet size based on hand strength and potential
  if hand_strength > 0.8 or hand_potential > 0.8:
      base_percentage += 0.2  # Increase bet for strong hands or high potential
  elif hand_strength < 0.4:
      base_percentage *= 0.5  # Decrease bet for weaker hands

    # Consider pot size and stack size for bet sizing
  bet_size = int(base_percentage * pot_size)
  bet_size = min(bet_size, stack_size)  # Ensure bet does not exceed stack size

    # Dynamic adjustments
    # Increase bet size in aggressive play or decrease in more conservative play
  if hand_strength > 0.7:
      bet_size = min(int(1.2 * bet_size), stack_size)  # Can't bet more than the stack size
  elif hand_strength < 0.5 and hand_potential < 0.5:
      bet_size = int(0.8 * bet_size)  # Smaller bets with low hand strength and potential

  return bet_size

def calculate_bet_size(pot_size, hand_strength, hand_potential, stack_size):
        base_bet = pot_size // 4
        if hand_strength > 0.8 or hand_potential > 0.8:
            bet_size = min(base_bet * 2, stack_size)  # More aggressive betting for strong hands or high potential
        elif hand_strength > 0.5 or hand_potential > 0.5:
            bet_size = min(base_bet, stack_size)  # Standard bet for decent hands
        else:
            bet_size = 0  # No bet for weaker hands
        return bet_size


def make_decision(position, action_sequence, hand_strength, hand_potential, pot_size, opponents_profiles, stack_size):
    # Initial bet size calculation
    bet_size = calculate_bet_size(pot_size, hand_strength, hand_potential, stack_size)
    
    # Adjust bet size based on position and observed action sequence
    if position == 'late' and all(action == 'check' for action in action_sequence):
        # More aggressive in late position if all previous actions were checks
        bet_size = min(bet_size * 1.5, stack_size)  # Increase bet size, capped at stack size
    elif position == 'early' and 'raise' in action_sequence:
        # More conservative in early position if there's been a raise
        if hand_strength < 0.5:
            return 'fold', 0  # Fold weaker hands
        else:
            bet_size = min(bet_size, stack_size)  # Maintain or decrease bet size
    
    # Decision logic based on adjusted bet size and hand strength
    if hand_strength > 0.8 or hand_potential > 0.8:
        action = 'raise' if bet_size > 0 else 'check'
    elif hand_strength > 0.5:
        action = 'call' if 'bet' in action_sequence or 'raise' in action_sequence else 'check'
    else:
        action = 'fold'
    
    return action, bet_size


def is_royal_flush(total_cards):
    is_flush_result, flush_suit = is_flush(total_cards)
    if not is_flush_result:
        return False, None
    values = [rank_to_value[card[0]] for card in total_cards if card[1] == flush_suit]
    return set(values) >= {10, 11, 12, 13, 14}, None


def is_straight_flush(total_cards):
    is_flush_flag, flush_suit = is_flush(total_cards)
    if not is_flush:
      return False, None
    if is_flush_flag:
        flush_cards = [card for card in total_cards if card[1] == flush_suit]
        is_straight_flag, straight_high_card = is_straight([rank_to_value[card[0]] for card in flush_cards])
        if is_straight_flag:
            # Check if the straight flush's high card is an Ace
            if straight_high_card == rank_to_value['A']:  
                return True, "Royal Flush"
            return True, "Straight Flush", straight_high_card
    return False, None

def is_four_of_a_kind(total_cards):
    rank_counts = Counter(card[0] for card in total_cards)
    return 4 in rank_counts.values(), None

def is_full_house(total_cards):
    rank_counts = Counter(card[0] for card in total_cards)
    has_three = any(count == 3 for count in rank_counts.values())
    has_two = any(count == 2 for count in rank_counts.values())
    return has_three and has_two, None


def is_flush(total_cards):
    suits = [card[1] for card in total_cards]
    suit_counts = Counter(suits)
    for suit, count in suit_counts.items():
        if count >= 5:
            flush_cards = [card for card in total_cards if card[1] == suit]
            highest_card = max(flush_cards, key=lambda card: rank_to_value[card[0]])
            return True, highest_card[1]  # Return suit of the flush
    return False, None

def is_straight(values):
    # Ensure Ace can act as low if present
    if 14 in values:
        values = values + [1]  # Add Ace as low value
    values = sorted(set(values))  # Sort and remove duplicates
    for i in range(len(values) - 4):
        consecutive = True
        for j in range(1, 5):
            if values[i + j] - values[i] != j:
                consecutive = False
                break
        if consecutive:
            return True, values[i + 4]
        # Special case for Ace-low straight
        if set(values[i:i+5]) == {2, 3, 4, 5, 14}:
            return True, 5
    return False, None

def is_three_of_a_kind(total_cards):
    rank_counts = Counter(card[0] for card in total_cards)
    return any(count == 3 for count in rank_counts.values()), None


def is_two_pair(total_cards):
    rank_counts = Counter(card[0] for card in total_cards)
    pairs = [rank for rank, count in rank_counts.items() if count == 2]
    return len(pairs) >= 2, pairs

def is_one_pair(total_cards):
    rank_counts = Counter(card[0] for card in total_cards)
    return any(count == 2 for count in rank_counts.values()), None

def is_high_card(total_cards):
    values = [rank_to_value[card[0]] for card in total_cards]
    high_card = max(values)
    return True, high_card

def early_position_strategy(action_sequence, hand_strength, hand_potential, bet_size):
        if not action_sequence and (hand_strength > 0.7 or hand_potential > 0.7):
            return 'bet', bet_size
        elif 'bet' in action_sequence or 'raise' in action_sequence:
            if hand_strength > 0.7 or hand_potential > 0.7:
                return 'call', bet_size
            else:
                return 'fold', 0
        return 'check', 0

def middle_position_strategy(action_sequence, hand_strength, hand_potential, bet_size, opponents_profiles):
        aggressive_opponents = sum(op['aggression_factor'] > 0.5 for op in opponents_profiles)
        if not action_sequence:
            if aggressive_opponents and (hand_strength > 0.6 or hand_potential > 0.6):
                return 'bet', bet_size  # More likely to take the initiative against aggressive players
        elif 'bet' in action_sequence or 'raise' in action_sequence:
            if hand_strength > 0.6:
                return 'call', bet_size  # Stay in the game with decent hands
            else:
                return 'fold', 0
        return 'check', 0

def late_position_strategy(action_sequence, hand_strength, hand_potential, bet_size, opponents_profiles):
        if not action_sequence:
            if hand_strength > 0.5 or hand_potential > 0.6:
                return 'bet', bet_size  # Utilize position to apply pressure
        elif 'bet' in action_sequence or 'raise' in action_sequence:
            if hand_strength > 0.5 or hand_potential > 0.6:
                return 'raise', bet_size * 1.5  # Assertiveness with the advantage of information
            else:
                return 'call', bet_size  # More inclined to see the turn with potential
        return 'check', 0

def determine_hand_type_and_key_cards(total_cards):
    # Assuming rank_to_value is defined globally
    sorted_cards = sorted(total_cards, key=lambda x: (-rank_to_value[x[0]], x[1]))

    # Initialize variables to store the results
    hand_type = None
    key_cards = []

    # Utilize global hand evaluation functions
    is_straight_flush, straight_flush_high = is_straight_flush(total_cards)
    if is_straight_flush:
        hand_type = "Straight Flush" if straight_flush_high != 'A' else "Royal Flush"
        key_cards = [card for card in sorted_cards if rank_to_value[card[0]] >= rank_to_value[straight_flush_high] - 4]  # Approximation
        return hand_type, [card[0] for card in key_cards[:5]]

    is_four, _ = is_four_of_a_kind(total_cards)
    if is_four:
        hand_type = "Four of a Kind"
        key_cards = [card for card in sorted_cards if card[0] == _]
        # Find kicker
        kickers = [card for card in sorted_cards if card[0] != _]
        key_cards += kickers[:1]
        return hand_type, [card[0] for card in key_cards]

    is_full, _ = is_full_house(total_cards)
    if is_full:
        hand_type = "Full House"
        # Find the three of a kind and pair
        key_cards = [card for card in sorted_cards if card[0] == _]
        return hand_type, [card[0] for card in key_cards[:5]]

    is_flush, flush_high = is_flush(total_cards)
    if is_flush:
        hand_type = "Flush"
        flush_cards = [card for card in sorted_cards if card[1] == flush_high[1]]
        key_cards = flush_cards[:5]
        return hand_type, [card[0] for card in key_cards]

    is_straight, straight_high = is_straight([rank_to_value[card[0]] for card in total_cards])
    if is_straight:
        hand_type = "Straight"
        # Approximation to find straight cards
        key_cards = [card for card in sorted_cards if rank_to_value[card[0]] >= straight_high - 4]
        return hand_type, [card[0] for card in key_cards[:5]]

    is_three, _ = is_three_of_a_kind(total_cards)
    if is_three:
        hand_type = "Three of a Kind"
        key_cards = [card for card in sorted_cards if card[0] == _]
        return hand_type, [card[0] for card in key_cards[:5]]

    is_two, pairs = is_two_pair(total_cards)
    if is_two:
        hand_type = "Two Pair"
        # Approximation to find two pairs
        key_cards = [card for card in sorted_cards if card[0] in pairs]
        return hand_type, [card[0] for card in key_cards[:5]]

    is_one, _ = is_one_pair(total_cards)
    if is_one:
        hand_type = "One Pair"
        key_cards = [card for card in sorted_cards if card[0] == _]
        return hand_type, [card[0] for card in key_cards[:5]]

    # High Card
    hand_type = "High Card"
    key_cards = sorted_cards[:5]
    return hand_type, [card[0] for card in key_cards]


def hand_score(hand_type, key_cards):
    base_scores = {
        "Royal Flush": 100000,
        "Straight Flush": 90000,
        "Four of a Kind": 80000,
        "Full House": 70000,
        "Flush": 60000,
        "Straight": 50000,
        "Three of a Kind": 40000,
        "Two Pair": 30000,
        "One Pair": 20000,
        "High Card": 10000
    }
    score = base_scores.get(hand_type, 0)

    # Assuming rank_to_value is globally defined
    for i, card in enumerate(key_cards):
        # Here, card is expected to be a rank like 'A', 'K', 'Q', etc.
        card_value = rank_to_value[card] if card in rank_to_value else 0
        score += card_value * (10 ** (4 - i))  # Decrease the weight for less significant cards

    return score


def calculate_backdoor_draws(total_cards):
    suits = [card[1] for card in total_cards]
    suit_counts = Counter(suits)

    # Utilize global rank_to_value mapping for conversion
    ranks = [rank_to_value[card[0]] if card[0] in rank_to_value else 0 for card in total_cards]
    rank_counts = Counter(ranks)

    backdoor_flush_potential = False
    backdoor_straight_potential = False

    # Check for backdoor flush draw potential
    for count in suit_counts.values():
        if count == 3:  # Three cards of the same suit indicate a backdoor flush draw
            backdoor_flush_potential = True
            break

    # Check for backdoor straight draw potential
    sorted_ranks = sorted(set(ranks))  # Use set to remove duplicates
    for i in range(len(sorted_ranks) - 2):
        # Look for any sequence of 3 cards within a 5-card span that could turn into a straight
        if 1 <= sorted_ranks[i + 2] - sorted_ranks[i] <= 4:
            backdoor_straight_potential = True
            break

    # Count the actual number of outs for backdoor draws
    backdoor_flush_outs = len([suit for suit, count in suit_counts.items() if count == 3]) * (13 - 3)  # Potential outs for each suit
    backdoor_straight_outs = 0
    if backdoor_straight_potential:
        # This is simplified; detailed calculation would require assessing gaps and available ranks
        backdoor_straight_outs = 8  # A rough estimation for backdoor straight draws

    return {
        'backdoor_flush_potential': backdoor_flush_potential,
        'backdoor_straight_potential': backdoor_straight_potential,
        'backdoor_flush_outs': backdoor_flush_outs,
        'backdoor_straight_outs': backdoor_straight_outs
    }

def assess_bluffing_potential(hole_cards, community_cards, position, opponents_profiles, action_sequence, stack_to_pot_ratio):
    total_cards = hole_cards + community_cards
    backdoor_draws = calculate_backdoor_draws(total_cards)

    # Initialize bluffing potential score
    bluffing_potential = 0

    # Increase potential based on backdoor draws
    if backdoor_draws['backdoor_flush_potential']:
        bluffing_potential += 0.2
    if backdoor_draws['backdoor_straight_potential']:
        bluffing_potential += 0.15

    # Adjust for position - more likely to bluff in later positions
    if position in ['dealer', 'late']:
        bluffing_potential += 0.1
    elif position in ['early', 'middle']:
        bluffing_potential -= 0.1

    # Consider opponents' tendencies
    aggressive_opponents = sum(op['aggression_factor'] > 0.5 for op in opponents_profiles)
    if aggressive_opponents > 0:
        # Less likely to bluff against aggressive players
        bluffing_potential -= 0.2
    else:
        # More likely to bluff against passive players
        bluffing_potential += 0.2

    # Action sequence adjustments
    if 'raise' in action_sequence or 'bet' in action_sequence:
        # Less likely to bluff after aggressive actions
        bluffing_potential -= 0.2
    elif len(action_sequence) == 0 or 'check' in action_sequence:
        # More likely to bluff in a passive pot
        bluffing_potential += 0.15

    # Stack to pot ratio considerations
    if stack_to_pot_ratio > 10:
        # More comfortable bluffing with a larger stack to pot ratio
        bluffing_potential += 0.1
    elif stack_to_pot_ratio < 5:
        # Less likely to bluff with a smaller stack to pot ratio
        bluffing_potential -= 0.1

    # Ensure bluffing potential is within reasonable bounds
    bluffing_potential = max(0, min(bluffing_potential, 1))

    return bluffing_potential



def calculate_outs(hole_cards, community_cards):
    total_cards = hole_cards + community_cards
    outs = set()

    suits = [card[1] for card in total_cards]
    suit_counts = Counter(suits)
    for suit, count in suit_counts.items():
        if count == 4:  # One card away from a flush
            missing_ranks = [rank for rank in ranks if (rank, suit) not in total_cards]
            for rank in missing_ranks:
                outs.add((rank, suit))

    values = sorted({rank_to_value[card[0]] for card in total_cards})
    for i in range(1, 11):  # Ace can be high or low
        straight_possibility = {i, i+1, i+2, i+3, i+4}
        current_values = set(values)
        if not straight_possibility.issubset(current_values):
            missing_values = straight_possibility.difference(current_values)
            for val in missing_values:
                rank = ranks[val-2] if val != 14 else 'A'
                outs.update([(rank, suit) for suit in ['h', 'd', 'c', 's']])

    rank_counts = Counter([card[0] for card in total_cards])
    for rank, count in rank_counts.items():
        if count == 2 or count == 3:  # Potential for improvement
            missing_suits = [suit for suit in ['h', 'd', 'c', 's'] if (rank, suit) not in total_cards]
            outs.update([(rank, suit) for suit in missing_suits])

    highest_community_card_value = max([rank_to_value[card[0]] for card in community_cards], default=0)
    for rank in ranks:
        rank_value = rank_to_value[rank]
        if rank_value > highest_community_card_value:
            outs.update([(rank, suit) for suit in ['h', 'd', 'c', 's'] if (rank, suit) not in total_cards])

    # Including backdoor draws requires defining 'calculate_backdoor_draws' appropriately
    # This might involve adjusting the existing function or incorporating its logic here directly

    unseen_cards = 52 - len(total_cards)
    return min(len(outs), unseen_cards)

def categorize_hand(total_cards):
    rank_values = [rank_to_value[card[0]] for card in total_cards]
    suit_counts = Counter(card[1] for card in total_cards)
    rank_counts = Counter(rank_values)

    is_flush = any(count >= 5 for count in suit_counts.values())
    is_straight, straight_high_card = is_straight(rank_values)

    if is_flush and is_straight:
        return "Straight Flush", straight_high_card
    if 4 in rank_counts.values():
        return "Four of a Kind", max(rank_counts, key=rank_counts.get)
    if 3 in rank_counts.values() and 2 in rank_counts.values():
        return "Full House", max(rank_counts, key=lambda x: (rank_counts[x], x))
    if is_flush:
        return "Flush", max(suit_counts, key=suit_counts.get)
    if is_straight:
        return "Straight", straight_high_card
    if 3 in rank_counts.values():
        return "Three of a Kind", max(rank_counts, key=rank_counts.get)
    if list(rank_counts.values()).count(2) >= 2:
        return "Two Pair", sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)[:2]
    if 2 in rank_counts.values():
        return "One Pair", max(rank_counts, key=rank_counts.get)
    return "High Card", max(rank_values)

def assess_hand_strength(hole_cards, community_cards):
    # Directly call the evaluate_hand_strength function.
    hand_type, hand_score = evaluate_hand_strength(hole_cards, community_cards)
    return hand_type, hand_score


def assess_hand_potential(hole_cards, community_cards):
    # Combine hole and community cards for a total view of the hand
    total_cards = hole_cards + community_cards
    suits = [card[1] for card in total_cards]
    ranks = [card[0] for card in total_cards]
    rank_values = {rank: index+2 for index, rank in enumerate("23456789TJQKA")}
    numeric_ranks = [rank_values[rank] for rank in ranks]

    # Calculate suit and rank distributions
    suit_distribution = Counter(suits)
    rank_distribution = Counter(numeric_ranks)

    # Determine flush draw potential
    flush_draw = max(suit_distribution.values()) == 4
    backdoor_flush_draw = max(suit_distribution.values()) == 3

    # Determine straight draw potential
    straight_draw = has_straight_draw(numeric_ranks)
    backdoor_straight_draw = has_backdoor_straight_draw(numeric_ranks)

    # Calculate the number of outs for a flush or a straight
    flush_outs = 9 if flush_draw else (2 if backdoor_flush_draw else 0)
    straight_outs = calculate_straight_outs(numeric_ranks)

    # Assess overall hand potential
    total_outs = flush_outs + straight_outs
    potential_score = min(total_outs / 47, 1)

    return potential_score, flush_draw, straight_draw, (backdoor_flush_draw or backdoor_straight_draw)


def has_straight_draw(ranks):
    """Check for an open-ended or gutshot straight draw."""
    unique_ranks = sorted(set(ranks))
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i+4] - unique_ranks[i] in [4, 5]:  # Open-ended or one-gap
            return True
    # Special case for A-2-3-4-5 straight
    if set([14, 2, 3, 4, 5]).issubset(set(ranks + [1])):
        return True

def has_backdoor_straight_draw(ranks):
    """Check for a potential backdoor straight draw."""
    unique_ranks = sorted(set(ranks))
    for i in range(len(unique_ranks) - 3):
        if unique_ranks[i+3] - unique_ranks[i] <= 5:  # Two gaps or less
            return True
    return False


def calculate_straight_outs(ranks):
    """Estimate the number of outs for a straight draw, simplified version."""
    if has_straight_draw(ranks):
        return 4  # Assuming an open-ended straight draw
    if has_backdoor_straight_draw(ranks):
        return 1  # Simplified estimate for backdoor straight draws
    return 0

def evaluate_flop_texture(community_cards):

    suits = [card[1] for card in community_cards]
    ranks = [card[0] for card in community_cards]
    rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                  '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    values = [rank_values[rank] for rank in ranks]

    # Suitedness
    suit_counts = {suit: suits.count(suit) for suit in set(suits)}
    max_suit_count = max(suit_counts.values())
    suitedness = max_suit_count >= 2

    # Connectivity
    sorted_values = sorted(values)
    gaps = [sorted_values[i + 1] - sorted_values[i] for i in range(len(sorted_values) - 1)]
    connected = all(gap <= 4 for gap in gaps) and len(set(gaps)) <= 2

    # High cards
    high_cards = any(value >= 11 for value in values)  # J or higher

    # Specific texture types
    texture_type = "dry"
    if suitedness and connected:
        texture_type = "wet connected"
    elif suitedness and not connected:
        texture_type = "wet unconnected"
    elif not suitedness and connected:
        texture_type = "monotone connected"
    elif high_cards:
        texture_type = "high card"

    return {
        "suitedness": suitedness,
        "connectivity": connected,
        "high_cards": high_cards,
        "texture": texture_type
    }

def consider_opponent_tendencies(opponent_actions, recent_actions):
    # Initial score based on overall opponent profile
    tendency_score = 0.5  # Neutral baseline

    # Adjust for observed aggression
    aggression_factor = opponent_actions.get('aggression_factor', 1)
    if aggression_factor > 1:
        tendency_score += (aggression_factor - 1) * 0.1  # Increase score for more aggressive opponents

    # Adjust for recent betting patterns
    recent_aggression = sum(action in ['bet', 'raise', 're-raise'] for action in recent_actions)
    recent_passivity = sum(action in ['check', 'call'] for action in recent_actions)

    # More weight to recent actions
    if recent_aggression > recent_passivity:
        tendency_score += 0.1
    else:
        tendency_score -= 0.1

    # Adjust for fold rate if significant
    if 'fold_rate' in opponent_actions and opponent_actions['fold_rate'] > 0.5:
        # Opponent folds more than 50% of the time, adjust strategy to bluff more
        tendency_score -= 0.1

    # Consider adaptability based on variance in recent actions compared to historical patterns
    if 'adaptability_score' in opponent_actions:
        # Higher adaptability means opponent is more unpredictable, requiring cautious play
        tendency_score -= opponent_actions['adaptability_score'] * 0.05

    return tendency_score

def calculate_bluff_frequency(hand_strength, hand_potential, flop_texture, opponent_profile):
    # Base bluffing frequency on hand strength and potential
    if hand_strength < 0.5 and hand_potential > 0.8:
        base_frequency = 0.3  # Higher potential justifies more frequent bluffs
    elif hand_strength < 0.5:
        base_frequency = 0.2  # Low hand strength, low potential - conservative bluffing
    else:
        base_frequency = 0  # Good hand strength negates the need for bluffing

    # Adjust based on flop texture
    if flop_texture['suitedness'] > 1 or flop_texture['connectedness'] > 1:
        base_frequency += 0.1  # More bluffing on dynamic textures

    # Adjust based on opponent's profile
    if opponent_profile['aggression_factor'] > 0.5:
        base_frequency -= 0.1  # Less bluffing against aggressive opponents
    elif opponent_profile['aggression_factor'] < 0.3:
        base_frequency += 0.1  # More bluffing against passive opponents

    # Ensure bluffing frequency is within bounds
    return min(max(base_frequency, 0), 1)

def should_bluff(bluff_frequency, position_adjustment, opponent_tendencies_adjustment, hand_strength, hand_potential, stack_to_pot_ratio, game_stage, num_opponents, opponent_range_adjustment):

    # Initial decision score based on provided parameters
    decision_score = bluff_frequency + position_adjustment + opponent_tendencies_adjustment + opponent_range_adjustment

    # Hand-based adjustments
    if hand_strength < 0.3 and hand_potential > 0.7:
        decision_score += 0.3  # Encourage bluffing with weak hands that have high potential
    elif hand_strength > 0.7:
        decision_score -= 0.3  # Reduce bluffing with strong hands

    # Stack to pot ratio adjustments
    if stack_to_pot_ratio < 1:
        decision_score -= 0.15
    elif stack_to_pot_ratio > 5:
        decision_score += 0.15

    # Game stage adjustments
    if game_stage in ['turn', 'river']:
        decision_score += 0.1  # More likely to bluff in later stages

    # Number of opponents adjustments
    if num_opponents > 2:
        decision_score -= 0.2  # Less likely to bluff against multiple opponents

    # Normalize the decision score to ensure it remains within logical bounds
    decision_score = min(max(decision_score, 0), 1)

    # Decision threshold adjustment based on game dynamics and risk management
    decision_threshold = 0.5  # Base threshold for making a bluff decision
    if game_stage == 'river':
        decision_threshold += 0.1  # Higher threshold on the river due to increased risk

    # Final decision
    return decision_score > decision_threshold

def determine_bet_size(hand_strength, hand_potential, position, opponent_profile, stack_size_ratio, num_opponents):
  base_size = 0.5  # Start with a base bet size of 50% of the pot

  # Hand strength and potential adjustments
  if hand_strength > 0.8 or (hand_potential > 0.8 and hand_strength > 0.5):
      base_size += 0.25  # Increase for strong hands or high potential hands
  elif hand_strength < 0.4 and hand_potential < 0.4:
      base_size *= 0.4  # Decrease for weak hands

  # Positional adjustments
  if position in ['dealer', 'late']:
      base_size += 0.15  # Increase in late positions
  elif position in ['early', 'middle']:
      base_size -= 0.1  # Decrease in early or middle positions

  # Opponent profile adjustments
  if opponent_profile['aggression_factor'] > 0.7:
      base_size -= 0.15  # Decrease against highly aggressive opponents
  elif opponent_profile['aggression_factor'] < 0.3:
      base_size += 0.15  # Increase against passive opponents

  # Stack size ratio adjustments
  if stack_size_ratio < 10:
      base_size *= 0.9  # Tighter play with shorter stacks
  elif stack_size_ratio > 50:
      base_size *= 1.1  # More leverage with deeper stacks

  # Number of opponents adjustments
  if num_opponents > 1:
      base_size *= max(0.8, 1 - 0.05 * (num_opponents - 1))  # Adjust bet size in multi-way pots

  # Ensure the bet size is within a reasonable range
  base_size = min(max(base_size, 0.2), 1.0)  # Clamp between 20% and 100% of the pot

  return base_size

def bluff_strategy(hole_cards, community_cards, position, opponents_profiles, pot_size, stack_size, action_sequence):
    # Evaluate the current hand's strength and potential for improvement
    hand_strength = assess_hand_strength(hole_cards, community_cards)
    hand_potential = assess_hand_potential(hole_cards, community_cards)

    # Analyze the texture of the flop to understand how it interacts with potential hands
    flop_texture = evaluate_flop_texture(community_cards)

    # Adjust based on the tendencies of the opponent and the current position
    opponent_tendencies_adjustment = consider_opponent_tendencies(opponents_profiles)
    position_adjustment = adjust_for_position(position, action_sequence, hand_strength, hand_potential, pot_size, stack_size)

    # Determine the frequency of bluffing and the optimal size of the bet
    bluff_frequency = calculate_bluff_frequency(hand_strength, hand_potential, flop_texture, opponent_tendencies_adjustment)
    bet_size = determine_bet_size(hand_strength, hand_potential, flop_texture, opponent_tendencies_adjustment, pot_size, stack_size)

    # Make a decision to bluff or not based on the calculated bluff frequency and the context of the game
    if should_bluff(bluff_frequency, position_adjustment, opponent_tendencies_adjustment, hand_strength, hand_potential):
        action = 'bluff'
    else:
        # Default action if not bluffing; could be 'check' or 'fold' based on the context
        action = 'check' if bet_size == 0 else 'fold'

    return action, bet_size

def generate_sample_hand():
    """Generates a sample hand with hole cards and community cards."""
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    deck = [(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)

    hole_cards = deck[:2]
    community_cards = deck[2:5]  # Simulate the flop
    return hole_cards, community_cards

def flop_strategy(position, action_sequence, hand_strength, hand_potential, pot_size, opponents_profiles):

    stack_size = 100000  # Fixed stack size for the AI player
    bet_size = calculate_bet_size(pot_size, hand_strength, hand_potential, stack_size)

    # Early Position Strategy
    if position == 'early':
        return early_position_strategy(action_sequence, hand_strength, hand_potential, bet_size)

    # Middle Position Strategy
    elif position == 'middle':
        return middle_position_strategy(action_sequence, hand_strength, hand_potential, bet_size, opponents_profiles)

    # Late Position Strategy (Not Dealer)
    elif position == 'late':
        return late_position_strategy(action_sequence, hand_strength, hand_potential, bet_size, opponents_profiles)

    return 'check', 0  # Default action

    decision = make_decision(position, action_sequence, hand_strength, hand_potential, pot_size, opponents_profiles)

    # Inside test_flop_strategy:
    hand_strength_numerical, _ = evaluate_hand_strength(hole_cards, community_cards)
    hand_potential_numerical = estimate_hand_potential(hole_cards, community_cards)  # Adjust if necessary to ensure a numerical return value
    action, bet_amount = make_decision(position, action_sequence, hand_strength_numerical, hand_potential_numerical, pot_size, opponents_profiles)



    return decision


def get_card_action(best_hand, highest_hand, min_amount, max_amount):
    """
    Determines the appropriate poker action (call, raise, or fold) based on the player's hand strength
    and current betting context.
    """
    # Convert numerical hand categories to a simple strength metric
    hand_strength = best_hand / 9  # Normalizing
    highest_table_strength = highest_hand / 9  # Assuming 1-9 scale where 9 is strongest

    if hand_strength > 0.8 or hand_strength > highest_table_strength:
        action = "raise"
        amount = min(max_amount, min_amount * 2)  # Example aggressive raise, adjust as needed
    elif hand_strength > 0.5:
        action = "call"
        amount = min_amount
    else:
        action = "fold"
        amount = 0

    return action, amount

def get_pre_flop_action(hole_card, min_amount, max_amount):
    """
    Determines the appropriate pre-flop action (call, raise, or fold) based on the hole cards
    and the betting amounts.
    """
    # Simplified strategy based on hole card strength
    hole_strength = sum(rank_to_value[card[0]] for card in hole_card) / 28  # Normalized strength

    if hole_strength > 0.7:  # Strong hands, consider raising
        action = "raise"
        amount = min(max_amount, min_amount * 2)  # Example raise amount, adjust as needed
    elif hole_strength > 0.4:  # Medium strength, call
        action = "call"
        amount = min_amount
    else:  # Weak hands, fold
        action = "fold"
        amount = 0

    return action, amount



def test_flop_strategy():


    stack_size = 10000
    hole_cards, community_cards = generate_sample_hand()
    pot_size = random.randint(1000, 5000)  # Simulate a pot size
    position = random.choice(['early', 'middle', 'late'])  # Randomize position for the test
    action_sequence = random.choice([[], ['bet'], ['check', 'check']])  # Simulate possible action sequences before AI's turn

    # Placeholder for opponents' profiles (simplified for testing)
    opponents_profiles = [{'aggression_factor': random.uniform(0.1, 0.9)} for _ in range(3)]  # Simulating 3 opponents

    # Evaluate hand strength and potential
    hand_type, _ = evaluate_hand_strength(hole_cards, community_cards)  # This returns the hand type, e.g., "Straight"
    hand_strength_numerical = convert_hand_type_to_strength(hand_type)  # Convert hand type to numerical strength
    hand_potential_numerical = estimate_hand_potential(hole_cards, community_cards)  # Ensure this returns a numerical potential score

    # Make a decision based on the current game state
    action, bet_amount = make_decision(position, action_sequence, hand_strength_numerical, hand_potential_numerical, pot_size, opponents_profiles, stack_size)

    print(f"Hole Cards: {hole_cards}")
    print(f"Community Cards: {community_cards}")
    print(f"Position: {position}")
    print(f"Action Sequence: {action_sequence}")
    print(f"Pot Size: {pot_size}")
    print(f"Hand Strength: {hand_strength_numerical:.2f}, Hand Potential: {hand_potential_numerical:.2f}")
    print(f"Decision: {action}, Bet Amount: {bet_amount}")  # Display the decision and bet amount

test_flop_strategy()







