import { getCustomerById } from '../data/customerRepo.js';
import {
  getTransactionsByCustomer,
  getRecentTransactions as fetchRecentTxns,
  getTotalExpense as calcTotalExpense,
  getCategoryWiseExpenses as calcCategoryExpenses
} from '../data/transactionRepo.js';
import { getCustomerEvents as fetchEvents } from '../data/customerEventsRepo.js';
import { getRiskProfile as fetchRisk } from '../data/riskProfileRepo.js';
import { generateCustomerRecommendations } from '../recommendation/recommendationEngine.js';

export async function executeTool(name, args) {
  const { customerId } = args;
  if (!customerId) {
    return JSON.stringify({ error: 'customerId is required' });
  }

  try {
    switch (name) {
      case 'getCustomerProfile': {
        const customer = getCustomerById(customerId);
        if (!customer) return JSON.stringify({ error: `Customer ${customerId} not found` });
        return JSON.stringify(customer, null, 2);
      }

      case 'getTransactions': {
        const txns = getTransactionsByCustomer(customerId);
        const limit = args.limit || 50;
        return JSON.stringify(txns.slice(0, limit), null, 2);
      }

      case 'getRecentTransactions': {
        const count = args.count || 10;
        const txns = fetchRecentTxns(customerId, count);
        return JSON.stringify(txns, null, 2);
      }

      case 'getTotalExpense': {
        const expense = calcTotalExpense(customerId, args.from, args.to);
        return JSON.stringify({
          customerId,
          from: args.from || 'beginning',
          to: args.to || 'now',
          totalExpenseINR: expense,
          formatted: `₹${expense.toLocaleString()} INR`
        }, null, 2);
      }

      case 'getCategoryWiseExpenses': {
        const categories = calcCategoryExpenses(customerId);
        return JSON.stringify({
          customerId,
          categories
        }, null, 2);
      }

      case 'getCustomerEvents': {
        const events = fetchEvents(customerId);
        return JSON.stringify(events, null, 2);
      }

      case 'getRiskProfile': {
        const risk = fetchRisk(customerId);
        return JSON.stringify(risk || { message: 'No explicit risk profile found' }, null, 2);
      }

      case 'getEligibleProducts': {
        const recs = generateCustomerRecommendations(customerId);
        const eligible = recs.topProducts.map(p => ({
          id: p.id,
          name: p.name,
          type: p.type,
          score: p.score,
          status: p.eligibilityStatus,
          reasons: p.eligibilityReasons
        }));
        return JSON.stringify(eligible, null, 2);
      }

      case 'getRecommendations': {
        const recs = generateCustomerRecommendations(customerId);
        return JSON.stringify(recs, null, 2);
      }

      case 'getRecommendationReason': {
        const recs = generateCustomerRecommendations(customerId);
        const itemId = args.itemId;
        let match = recs.topProducts.find(p => p.id === itemId || p.name === itemId);
        if (!match) {
          match = recs.topOffers.find(o => o.id === itemId || o.name === itemId);
        }

        if (match) {
          return JSON.stringify({
            itemId: match.id,
            name: match.name,
            score: match.score,
            explanation: match.explanation
          }, null, 2);
        }

        return JSON.stringify({
          message: `Explanation for ${itemId || 'requested item'}: Top recommendation generated based on spending patterns, CIBIL score, and eligibility criteria.`,
          summary: recs.summary,
          baseline: recs.baseline
        }, null, 2);
      }

      default:
        return JSON.stringify({ error: `Unknown tool name: ${name}` });
    }
  } catch (err) {
    console.error(`[ToolExecutionError] ${name}:`, err);
    return JSON.stringify({ error: err.message });
  }
}
