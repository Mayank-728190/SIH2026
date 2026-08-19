import { readCSVFile } from './csvReader.js';

let offerCache = null;
let merchantCache = null;
let merchantMap = null;

function loadMerchants() {
  if (!merchantCache) {
    console.log('[OfferRepo] Loading merchants.csv...');
    const raw = readCSVFile('merchants.csv');
    merchantCache = raw.map(m => ({
      ...m,
      Merchant_Risk_Score: Number(m.Merchant_Risk_Score || 0),
      Partner_Offer_Eligible: m.Partner_Offer_Eligible === 'True' || m.Partner_Offer_Eligible === 'true',
    }));
    merchantMap = new Map();
    for (const m of merchantCache) {
      merchantMap.set(m.Merchant_ID, m);
    }
  }
}

function loadOffers() {
  loadMerchants();
  if (!offerCache) {
    console.log('[OfferRepo] Loading offers.csv...');
    const raw = readCSVFile('offers.csv');
    offerCache = raw.map(o => {
      const merchant = merchantMap.get(o.Merchant_ID) || null;
      return {
        ...o,
        Cashback_Percentage: Number(o.Cashback_Percentage || 0),
        Reward_Points: Number(o.Reward_Points || 0),
        Merchant_Name: merchant ? merchant.Merchant_Name : 'Partner Merchant',
        Merchant_Risk_Score: merchant ? merchant.Merchant_Risk_Score : 0,
      };
    });
    console.log(`[OfferRepo] Loaded ${offerCache.length} offers.`);
  }
}

export function getAllOffers() {
  loadOffers();
  return offerCache;
}

export function getAllMerchants() {
  loadMerchants();
  return merchantCache;
}

export function getOfferById(offerId) {
  loadOffers();
  return offerCache.find(o => o.Offer_ID === offerId) || null;
}
