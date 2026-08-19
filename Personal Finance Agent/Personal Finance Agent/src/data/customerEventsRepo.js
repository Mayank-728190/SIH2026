import { readCSVFile } from './csvReader.js';

let eventsCache = null;
let customerEventsMap = null;

function loadEvents() {
  if (!eventsCache) {
    console.log('[CustomerEventsRepo] Loading customer_events.csv...');
    eventsCache = readCSVFile('customer_events.csv');
    customerEventsMap = new Map();

    for (const e of eventsCache) {
      if (!customerEventsMap.has(e.Customer_ID)) {
        customerEventsMap.set(e.Customer_ID, []);
      }
      customerEventsMap.get(e.Customer_ID).push({
        ...e,
        Offer_Clicked: e.Offer_Clicked === 'True' || e.Offer_Clicked === 'true',
        Offer_Redeemed: e.Offer_Redeemed === 'True' || e.Offer_Redeemed === 'true',
      });
    }
    console.log(`[CustomerEventsRepo] Loaded ${eventsCache.length} events across ${customerEventsMap.size} customers.`);
  }
}

export function getCustomerEvents(customerId) {
  loadEvents();
  return customerEventsMap.get(customerId) || [];
}

export function getRecentCustomerEvents(customerId, count = 10) {
  const events = getCustomerEvents(customerId);
  const sorted = [...events].sort((a, b) => (b.Date || '').localeCompare(a.Date || ''));
  return sorted.slice(0, count);
}
