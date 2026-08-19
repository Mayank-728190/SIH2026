import { getCustomerById } from '../data/customerRepo.js';
import { getTransactionsByCustomer, getCategoryWiseExpenses } from '../data/transactionRepo.js';
import { getRiskProfile } from '../data/riskProfileRepo.js';
import { getCustomerEvents } from '../data/customerEventsRepo.js';
import { getBaselineRecommendation } from '../data/recommendationRepo.js';

export function getFullCustomerProfile(customerId) {
  const customer = getCustomerById(customerId);
  if (!customer) return null;

  const transactions = getTransactionsByCustomer(customerId);
  const categoryExpenses = getCategoryWiseExpenses(customerId);
  const riskProfile = getRiskProfile(customerId);
  const events = getCustomerEvents(customerId);
  const baselineRec = getBaselineRecommendation(customerId);

  // Calculate dynamic transaction signals
  const debitTxns = transactions.filter(t => t.Transaction_Type === 'Debit' && t.Transaction_Status !== 'Failed');
  const transactionCount = debitTxns.length;
  
  let dynamicTotalSpend = 0;
  for (const cat in categoryExpenses) {
    dynamicTotalSpend += categoryExpenses[cat];
  }

  const avgTransactionAmount = transactionCount > 0 ? (dynamicTotalSpend / transactionCount) : 0;

  // Find top spending categories dynamically
  const sortedCategories = Object.entries(categoryExpenses)
    .sort((a, b) => b[1] - a[1])
    .map(([cat, amount]) => ({
      category: cat,
      amount,
      percentage: dynamicTotalSpend > 0 ? ((amount / dynamicTotalSpend) * 100).toFixed(1) : '0',
    }));

  const topCategory = sortedCategories.length > 0 ? sortedCategories[0].category : 'General';

  // Event interaction metrics
  const offerClicks = events.filter(e => e.Offer_Clicked).length;
  const offerRedemptions = events.filter(e => e.Offer_Redeemed).length;
  const productViews = events.filter(e => e.Product_Viewed).length;

  return {
    customer,
    riskProfile,
    baselineRecommendation: baselineRec,
    behavior: {
      transactionCount,
      dynamicTotalSpend,
      avgTransactionAmount: Math.round(avgTransactionAmount),
      categoryExpenses,
      sortedCategories,
      topCategory,
      eventCount: events.length,
      offerClicks,
      offerRedemptions,
      productViews,
    },
  };
}
