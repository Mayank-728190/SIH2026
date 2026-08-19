import { getFullCustomerProfile } from './customerProfile.js';
import { getAllProducts } from '../data/productRepo.js';
import { getAllOffers } from '../data/offerRepo.js';
import { evaluateProductEligibility, evaluateOfferEligibility } from './eligibilityEngine.js';
import { scoreProduct, scoreOffer } from './scoring.js';
import { generateProductExplanation, generateOfferExplanation } from './explanation.js';

export function generateCustomerRecommendations(customerId) {
  const fullProfile = getFullCustomerProfile(customerId);
  if (!fullProfile) {
    return {
      error: 'Customer not found',
      products: [],
      offers: [],
    };
  }

  const products = getAllProducts();
  const offers = getAllOffers();

  // Process Products
  const processedProducts = products.map(product => {
    const eligibility = evaluateProductEligibility(fullProfile.customer, product, fullProfile.riskProfile);
    const score = scoreProduct(fullProfile, product, eligibility);
    const explanation = generateProductExplanation(fullProfile, product, eligibility, score);

    return {
      id: product.Product_ID,
      name: product.Product_Name,
      type: product.Product_Type,
      rewardRate: product.Reward_Rate,
      annualFee: product.Annual_Fee,
      interestRate: product.Interest_Rate,
      minCibil: product.Eligibility_Min_CIBIL,
      minIncome: product.Eligibility_Min_Income,
      score,
      eligibilityStatus: eligibility.status,
      eligibilityReasons: eligibility.reasons,
      explanation,
    };
  });

  // Filter eligible and sort by score
  const eligibleProducts = processedProducts
    .filter(p => p.eligibilityStatus === 'ELIGIBLE')
    .sort((a, b) => b.score - a.score);

  // Process Offers
  const processedOffers = offers.map(offer => {
    const eligibility = evaluateOfferEligibility(fullProfile.customer, offer, fullProfile.riskProfile);
    const score = scoreOffer(fullProfile, offer, eligibility);
    const explanation = generateOfferExplanation(fullProfile, offer, eligibility, score);

    return {
      id: offer.Offer_ID,
      name: offer.Offer_Name,
      category: offer.Category,
      merchantId: offer.Merchant_ID,
      merchantName: offer.Merchant_Name,
      cashbackPercentage: offer.Cashback_Percentage,
      rewardPoints: offer.Reward_Points,
      startDate: offer.Offer_Start_Date,
      endDate: offer.Offer_End_Date,
      score,
      eligibilityStatus: eligibility.status,
      eligibilityReasons: eligibility.reasons,
      explanation,
    };
  });

  const eligibleOffers = processedOffers
    .filter(o => o.eligibilityStatus === 'ELIGIBLE')
    .sort((a, b) => b.score - a.score);

  // Baseline CSV recommendation reference
  const baseline = fullProfile.baselineRecommendation || {};

  return {
    customerId,
    customerName: fullProfile.customer.Full_Name,
    summary: {
      totalDebitSpend: fullProfile.behavior.dynamicTotalSpend,
      topCategory: fullProfile.behavior.topCategory,
      cibilScore: fullProfile.customer.CIBIL_Score,
      monthlyIncome: fullProfile.customer.Monthly_Income,
    },
    baseline: {
      recommendedProduct: baseline.Recommended_Product,
      recommendedCreditCard: baseline.Recommended_Credit_Card,
      recommendedLoan: baseline.Recommended_Loan,
      recommendedInsurance: baseline.Recommended_Insurance,
      recommendedRewardOffer: baseline.Recommended_Reward_Offer,
      recommendedCashbackOffer: baseline.Recommended_Cashback_Offer,
      nextBestAction: baseline.Next_Best_Action,
    },
    topProducts: eligibleProducts.slice(0, 6),
    topOffers: eligibleOffers.slice(0, 6),
    allEligibleProductsCount: eligibleProducts.length,
    allEligibleOffersCount: eligibleOffers.length,
  };
}
