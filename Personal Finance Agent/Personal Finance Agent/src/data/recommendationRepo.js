import { readCSVFile } from './csvReader.js';

let recCache = null;
let recMap = null;

function loadRecommendations() {
  if (!recCache) {
    console.log('[RecommendationRepo] Loading recommendations.csv...');
    const raw = readCSVFile('recommendations.csv');
    recCache = raw.map(r => ({
      ...r,
      Product_Affinity_Score: Number(r.Product_Affinity_Score || 0),
      Offer_Acceptance_Probability: Number(r.Offer_Acceptance_Probability || 0),
      Recommendation_Accepted: r.Recommendation_Accepted === 'True' || r.Recommendation_Accepted === 'true',
      Expected_Revenue_Uplift: Number(r.Expected_Revenue_Uplift || 0),
    }));
    recMap = new Map();
    for (const r of recCache) {
      recMap.set(r.Customer_ID, r);
    }
    console.log(`[RecommendationRepo] Loaded ${recCache.length} baseline recommendations.`);
  }
}

export function getBaselineRecommendation(customerId) {
  loadRecommendations();
  return recMap.get(customerId) || null;
}
