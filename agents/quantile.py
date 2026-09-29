from agents.recommendation import assign_recommendations, classify_candidate_recommendation

def assign_quantiles(candidates, thresholds=None):
    return assign_recommendations(candidates, thresholds)
