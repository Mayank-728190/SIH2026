import { readCSVFile } from './csvReader.js';

let productCache = null;
let productMap = null;

function loadProducts() {
  if (!productCache) {
    console.log('[ProductRepo] Loading products.csv...');
    const raw = readCSVFile('products.csv');
    productCache = raw.map(p => ({
      ...p,
      Eligibility_Min_CIBIL: Number(p.Eligibility_Min_CIBIL || 0),
      Eligibility_Min_Income: Number(p.Eligibility_Min_Income || 0),
      Reward_Rate: Number(p.Reward_Rate || 0),
      Annual_Fee: Number(p.Annual_Fee || 0),
      Interest_Rate: Number(p.Interest_Rate || 0),
    }));
    productMap = new Map();
    for (const p of productCache) {
      productMap.set(p.Product_ID, p);
    }
    console.log(`[ProductRepo] Loaded ${productCache.length} products.`);
  }
}

export function getAllProducts() {
  loadProducts();
  return productCache;
}

export function getProductById(productId) {
  loadProducts();
  return productMap.get(productId) || null;
}
