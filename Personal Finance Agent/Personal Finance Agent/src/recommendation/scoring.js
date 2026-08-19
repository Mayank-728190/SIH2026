/**
 * Scoring Module: Calculates recommendation score (0 to 100) for products and offers.
 */

export function scoreProduct(fullProfile, product, eligibilityResult) {
  if (eligibilityResult.status !== 'ELIGIBLE') {
    return 0;
  }

  const { customer, behavior } = fullProfile;
  let score = 50; // base score for eligible product

  // 1. CIBIL score headroom bonus (up to +15 pts)
  const minCibil = Number(product.Eligibility_Min_CIBIL || 300);
  const cibil = Number(customer.CIBIL_Score || 600);
  const cibilHeadroom = cibil - minCibil;
  if (cibilHeadroom > 0) {
    score += Math.min(15, Math.floor(cibilHeadroom / 20));
  }

  // 2. Financial Health & Income Fit (+10 pts)
  const finHealth = Number(customer.Financial_Health_Score || 50);
  score += Math.round((finHealth - 50) / 5);

  // 3. Category & Behavior Alignment (+15 pts)
  const productType = product.Product_Type || '';
  const topCategory = behavior.topCategory || '';

  if (productType.includes('Fixed Deposit') || productType.includes('Recurring Deposit')) {
    if (customer.Savings_Ratio > 0.5) score += 10;
    if (customer.Fixed_Deposit_Holder) score += 5; // proven affinity
  } else if (productType.includes('Loan')) {
    if (customer.Loan_Eligibility_Score > 80) score += 10;
    if (customer.Debt_to_Income_Ratio < 0.3) score += 5;
  } else if (productType.includes('Investment')) {
    if (customer.Investment_Readiness_Score > 60) score += 10;
    if (customer.Savings_Ratio > 0.4) score += 5;
  } else if (productType.includes('Savings') || productType.includes('Current')) {
    if (customer.Avg_Monthly_Balance > 100000) score += 10;
  }

  // 4. Spending volume impact
  if (behavior.dynamicTotalSpend > 30000) {
    score += 5;
  }

  // Normalize score between 1 and 99
  return Math.min(99, Math.max(1, Math.round(score)));
}

export function scoreOffer(fullProfile, offer, eligibilityResult) {
  if (eligibilityResult.status !== 'ELIGIBLE') {
    return 0;
  }

  const { customer, behavior } = fullProfile;
  let score = 40; // base score for eligible offer

  // 1. Merchant Category Match (+30 pts max)
  const categoryExpenses = behavior.categoryExpenses || {};
  const offerCategory = offer.Category || '';
  const categorySpend = Number(categoryExpenses[offerCategory] || 0);

  if (categorySpend > 0) {
    const totalSpend = behavior.dynamicTotalSpend || 1;
    const spendRatio = categorySpend / totalSpend;
    score += Math.min(25, Math.round(spendRatio * 50));
    if (offerCategory === behavior.topCategory) {
      score += 10; // extra boost for top spending category
    }
  }

  // 2. Offer reward strength (+15 pts)
  if (offer.Cashback_Percentage > 0) {
    score += Math.min(15, offer.Cashback_Percentage * 1.5);
  }
  if (offer.Reward_Points > 0) {
    score += Math.min(15, Math.round(offer.Reward_Points / 100));
  }

  // 3. Customer Responsiveness & Loyalty Tier (+10 pts)
  const responsiveness = Number(customer.Offer_Responsiveness_Score || 50);
  score += Math.round((responsiveness - 50) / 10);

  if (customer.Loyalty_Tier === 'Platinum') score += 5;
  else if (customer.Loyalty_Tier === 'Gold') score += 3;

  return Math.min(99, Math.max(1, Math.round(score)));
}
