from utils import calculate_verified_score
import json

def test_scoring():
    print("--- Enterprise Scoring Tests ---")

    # Case 1: THE PURPLE SQUIRREL (Perfect Match)
    # Should be capped at 95.
    case1 = {
        "basic_qualification_match": [{"match_status": "Full"}],
        "preferred_qualification_match": [{"match_status": "Full"}],
        "role_alignment": {"match_status": "Aligned"},
        "seniority_status": "Match"
    }
    res1 = calculate_verified_score(case1)
    print(f"Case 1 (Perfect): Score={res1['overall_relevance_score']} (Expected 95), Eligible={res1['meets_minimum_requirements']}")

    # Case 2: OVERQUALIFIED (Lead applying for Senior)
    # -10 Penalty for Overqualified. Base 95 -> 85.
    case2 = {
        "basic_qualification_match": [{"match_status": "Full"}],
        "preferred_qualification_match": [{"match_status": "Full"}],
        "role_alignment": {"match_status": "Aligned"},
        "seniority_status": "Overqualified"
    }
    res2 = calculate_verified_score(case2)
    print(f"Case 2 (Overqualified): Score={res2['overall_relevance_score']} (Expected 85), Eligible={res2['meets_minimum_requirements']}")

    # Case 3: ELIGIBILITY FAILURE (Missing Basic Qual)
    # -20 Penalty. Eligible = False.
    case3 = {
        "basic_qualification_match": [{"match_status": "Missing"}], # The killer
        "preferred_qualification_match": [{"match_status": "Full"}],
        "role_alignment": {"match_status": "Aligned"},
        "seniority_status": "Match"
    }
    res3 = calculate_verified_score(case3)
    print(f"Case 3 (Ineligible): Score={res3['overall_relevance_score']} (Expected <= 75), Eligible={res3['meets_minimum_requirements']} (Expected False)")

    # Case 4: REALISTIC CANDIDATE
    # Partial Basic (-10), Missing Preferred (-5), Match Seniority.
    # 95 - 10 - 5 = 80.
    case4 = {
        "basic_qualification_match": [{"match_status": "Partial"}],
        "preferred_qualification_match": [{"match_status": "Missing"}],
        "role_alignment": {"match_status": "Aligned"},
        "seniority_status": "Match"
    }
    res4 = calculate_verified_score(case4)
    print(f"Case 4 (Realistic): Score={res4['overall_relevance_score']} (Expected 80), Eligible={res4['meets_minimum_requirements']} (Expected True)")

if __name__ == "__main__":
    test_scoring()
