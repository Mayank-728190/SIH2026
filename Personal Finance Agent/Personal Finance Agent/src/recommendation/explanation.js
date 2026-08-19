/**
 * Explanation Generator: Creates factual, data-backed rationale for recommendations.
 */

export function generateProductExplanation(fullProfile, product, eligibilityResult, score) {
  const { customer, behavior } = fullProfile;
  const reasons = [];

  // Eligibility points
  if (eligibilityResult.status === 'ELIGIBLE') {
    reasons.push(`Customer meets all eligibility criteria (CIBIL Score: ${customer.CIBIL_Score}, Monthly Income: ₹${customer.Monthly_Income.toLocaleString()}).`);
  } else {
    reasons.push(`Eligibility Status: ${eligibilityResult.status} - ${eligibilityResult.reasons.join(' ')}`);
  }

  // Financial alignment
  if (customer.CIBIL_Score >= product.Eligibility_Min_CIBIL + 50) {
    reasons.push(`Customer's CIBIL score of ${customer.CIBIL_Score} comfortably exceeds the minimum requirement of ${product.Eligibility_Min_CIBIL}.`);
  }

  if (customer.Savings_Ratio > 0.4 && (product.Product_Type.includes('Fixed Deposit') || product.Product_Type.includes('Investment'))) {
    reasons.push(`Customer maintains a healthy savings ratio of ${(customer.Savings_Ratio * 100).toFixed(1)}%, indicating high investment capacity.`);
  }

  if (customer.Outstanding_Loan_Amount > 0 && product.Product_Type.includes('Loan')) {
    reasons.push(`Active loan history observed (Outstanding: ₹${customer.Outstanding_Loan_Amount.toLocaleString()}), with EMI of ₹${customer.EMI_Amount.toLocaleString()}.`);
  }

  const signals = {
    cibilScore: customer.CIBIL_Score,
    monthlyIncome: customer.Monthly_Income,
    savingsRatio: customer.Savings_Ratio,
    financialHealthScore: customer.Financial_Health_Score,
    topSpendingCategory: behavior.topCategory,
  };

  return {
    name: product.Product_Name,
    type: product.Product_Type,
    score,
    eligibility: eligibilityResult.status,
    reasons,
    signals,
  };
}

export function generateOfferExplanation(fullProfile, offer, eligibilityResult, score) {
  const { customer, behavior } = fullProfile;
  const reasons = [];

  const offerCategory = offer.Category || 'General';
  const catSpend = Number(behavior.categoryExpenses[offerCategory] || 0);

  if (catSpend > 0) {
    reasons.push(`Customer spends ₹${catSpend.toLocaleString()} in ${offerCategory} category across ${behavior.transactionCount} transactions.`);
  }

  if (offerCategory === behavior.topCategory) {
    reasons.push(`${offerCategory} is customer's #1 top spending category.`);
  }

  if (offer.Cashback_Percentage > 0) {
    reasons.push(`Offer provides ${offer.Cashback_Percentage}% cashback on ${offer.Merchant_Name || offerCategory} transactions.`);
  }
  if (offer.Reward_Points > 0) {
    reasons.push(`Offer provides ${offer.Reward_Points} bonus reward points on eligible purchases.`);
  }

  if (customer.Loyalty_Tier) {
    reasons.push(`Customer holds ${customer.Loyalty_Tier} tier status with offer responsiveness score of ${customer.Offer_Responsiveness_Score}.`);
  }

  const signals = {
    category: offerCategory,
    categorySpending: catSpend,
    isTopCategory: offerCategory === behavior.topCategory,
    totalMonthlySpend: behavior.dynamicTotalSpend,
    loyaltyTier: customer.Loyalty_Tier,
  };

  return {
    name: offer.Offer_Name,
    merchant: offer.Merchant_Name,
    category: offer.Category,
    score,
    eligibility: eligibilityResult.status,
    reasons,
    signals,
  };
}
