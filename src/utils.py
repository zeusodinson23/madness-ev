
"""
Utility function for MadnessEV

This module contains the mathematical foundation: 
- COnverting odds to probabilities
- Removing the vig
- Calculating the expected value
""" 

def american_to_implied_prob(odds: int) -> float: 
    """
    Converts American odds to implied probability.
    
    Examples: 
    -150 -> 0.60 (60% chance (150/250))
    +200 -> 0.33 (33% chance (100/300))
    """
    if odds < 0:
        # Favourite: probability = |odds|/(|odds| + 100)
        return abs(odds) / (abs(odds) + 100)
    else: 
        # Underdog: probability = (100)/( 100 + odds )
        return (100)/(odds + 100)
    

def american_to_decimal(odds: int) -> float:
        """
        Convert American odds to decimal odds
        Decimal odds show total return per $1 bet.
        - Decimal 3.0 means: bet $1, get $3 back (including the $1)

        Examples:
         -150 -> 1.67 (250/150)
         +200 -> 3.00 (100+200=300/100=3.0)
         Basically (winnings/staked)

        """
        if odds < 0:
            return (abs(odds) + 100) / (abs(odds))
        else:
            return (odds + 100) / (100)
        
        print(american_to_decimal(-150)) # 1.67
        print(american_to_decimal(200)) # 3.0



def calculate_vig(prob_a: float, prob_b: float) -> float:
     """
     Calculate the bookmaker's vig (profit margin) from the implied probabilities of two outcomes.

     Example: 
     Both sides vig at -110: 0.524 + 0.524 = 1.048
     Vig + 1.048 - 1 = 0.048 (4.8%)       
     """

     vig = (prob_a + prob_b) - 1
     return vig

def remove_vig(prob_a: float, prob_b: float) -> tuple: 
     """
     Remove the bookmaker's vig from the implied probabilities to get the true probabilities that sum to 100%

     Method: Divide each probability by the total. 

     Eg: 
        Both sides vig at -110: 0.524 + 0.524 = 1.048
        Remove vig: 0.524/1.048 = 0.5 (50% chance)
                    0.524/1.048 = 0.5 (50% chance)

     """
     total = prob_a + prob_b 
     return (prob_a / total, prob_b / total)

def calculate_ev(model_prob:float, deicmal_odds: float, stake:float = 100) -> float: 
    """
    Calculate the expected value (EV) of a bet given the model's probability and the decimal odds.

    EV = (probability of winning * profit if win) - (probability of losing * stake)


    Positive EV = profitable bet in the long run
    Negative EV = losing bet in the long run

    Example: 

    Model says 60% chance, odds are 1.67, stake is $100
    EV = (0.6 * (1.67 * 100)) - ((1 - 0.6) * 100)
       = (0.6 * 167) - (0.4 * 100)
       = 100.2 - 40
       = $60.20 (positive EV, good bet)
    """
    profit_if_win = (deicmal_odds * stake) - stake
    Loss_if_lose = stake
    ev = (model_prob * profit_if_win) - ((1 - model_prob) * Loss_if_lose)
    return ev

def kelly_fraction(model_prob: float, decimal_odds: float) -> float:
    """
    Calculate the Kelly fraction for optimal bet sizing.

    Kelly Fraction = (bp - q) / b
    where:
    b = decimal odds - 1 (net odds)
    p = model's probability of winning
    q = 1 - p (probability of losing)

    Example:
    Model says 60% chance, odds are 1.67
    b = 1.67 - 1 = 0.67
    p = 0.6
    q = 0.4

    Kelly Fraction = (0.67 * 0.6 - 0.4) / 0.67
                   = (0.402 - 0.4) / 0.67
                   = 0.002 / 0.67
                   ≈ 0.003 (Kelly suggests betting about 0.3% of bankroll)
    """
    b = decimal_odds - 1
    p = model_prob
    q = 1 - p

    kelly_fraction = ((b * p) - q) / b
    return max(kelly_fraction,0) # Don't bet a negative fraction (which would mean betting against the outcome)


def kelly_stake(bankroll: float, model_prob: float, decimal_odds: float, 
                fraction: float = 0.25) -> float:
    """
    Calculate actual dollar amount to bet using fractional Kelly.
    
    Args:
        bankroll: Your total betting bankroll
        model_prob: Your probability estimate
        decimal_odds: The decimal odds offered
        fraction: Kelly fraction to use (default 0.25 = quarter Kelly)
    
    Example:
        $1000 bankroll, 40% chance at 3.0 odds, quarter Kelly
        Full Kelly = 10%, Quarter Kelly = 2.5%
        Bet = $1000 × 0.025 = $25
    """
    full_kelly = kelly_fraction(model_prob, decimal_odds)
    return bankroll * full_kelly * fraction
