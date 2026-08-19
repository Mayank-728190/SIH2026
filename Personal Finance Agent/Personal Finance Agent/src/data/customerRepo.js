import { readCSVFile } from './csvReader.js';

let customerCache = null;
let customerMap = null;

function loadCustomers() {
  if (!customerCache) {
    console.log('[CustomerRepo] Loading customers.csv...');
    customerCache = readCSVFile('customers.csv');
    customerMap = new Map();
    for (const c of customerCache) {
      customerMap.set(c.Customer_ID, c);
    }
    console.log(`[CustomerRepo] Loaded ${customerCache.length} customers.`);
  }
}

export function getAllCustomers(limit = 100) {
  loadCustomers();
  return customerCache.slice(0, limit).map(c => ({
    Customer_ID: c.Customer_ID,
    Full_Name: c.Full_Name,
    City: c.City,
    State: c.State,
    Customer_Segment: c.Customer_Segment,
    Occupation: c.Occupation,
    CIBIL_Score: Number(c.CIBIL_Score || 0),
    Monthly_Income: Number(c.Monthly_Income || 0),
  }));
}

export function getCustomerById(customerId) {
  loadCustomers();
  const customer = customerMap.get(customerId);
  if (!customer) return null;
  
  // Format numeric values for easy downstream usage
  return {
    ...customer,
    Age: Number(customer.Age || 0),
    Monthly_Income: Number(customer.Monthly_Income || 0),
    Annual_Income: Number(customer.Annual_Income || 0),
    Account_Age_Months: Number(customer.Account_Age_Months || 0),
    Avg_Monthly_Balance: Number(customer.Avg_Monthly_Balance || 0),
    Savings_Ratio: Number(customer.Savings_Ratio || 0),
    Outstanding_Loan_Amount: Number(customer.Outstanding_Loan_Amount || 0),
    EMI_Amount: Number(customer.EMI_Amount || 0),
    CIBIL_Score: Number(customer.CIBIL_Score || 0),
    Debt_to_Income_Ratio: Number(customer.Debt_to_Income_Ratio || 0),
    Loan_Eligibility_Score: Number(customer.Loan_Eligibility_Score || 0),
    Investment_Capacity_Score: Number(customer.Investment_Capacity_Score || 0),
    Financial_Literacy_Score: Number(customer.Financial_Literacy_Score || 0),
    Wealth_Potential_Score: Number(customer.Wealth_Potential_Score || 0),
    Digital_Adoption_Score: Number(customer.Digital_Adoption_Score || 0),
    Customer_Satisfaction_Score: Number(customer.Customer_Satisfaction_Score || 0),
    Customer_Intent_Score: Number(customer.Customer_Intent_Score || 0),
    Churn_Risk_Score: Number(customer.Churn_Risk_Score || 0),
    Engagement_Score: Number(customer.Engagement_Score || 0),
    Monthly_Spend: Number(customer.Monthly_Spend || 0),
    Food_Spend: Number(customer.Food_Spend || 0),
    Grocery_Spend: Number(customer.Grocery_Spend || 0),
    Dining_Out_Spend: Number(customer.Dining_Out_Spend || 0),
    Travel_Spend: Number(customer.Travel_Spend || 0),
    Fuel_Spend: Number(customer.Fuel_Spend || 0),
    Shopping_Spend: Number(customer.Shopping_Spend || 0),
    Entertainment_Spend: Number(customer.Entertainment_Spend || 0),
    Healthcare_Spend: Number(customer.Healthcare_Spend || 0),
    Education_Spend: Number(customer.Education_Spend || 0),
    Utility_Bills_Spend: Number(customer.Utility_Bills_Spend || 0),
    Rent_or_Housing_Spend: Number(customer.Rent_or_Housing_Spend || 0),
    Insurance_Premium_Spend: Number(customer.Insurance_Premium_Spend || 0),
    Investment_Spend: Number(customer.Investment_Spend || 0),
    Subscription_Spend: Number(customer.Subscription_Spend || 0),
    Other_Spend: Number(customer.Other_Spend || 0),
    KYC_Verification_Score: Number(customer.KYC_Verification_Score || 0),
    Compliance_Score: Number(customer.Compliance_Score || 0),
    Behavior_Score: Number(customer.Behavior_Score || 0),
    Digital_Maturity_Score: Number(customer.Digital_Maturity_Score || 0),
    Financial_Health_Score: Number(customer.Financial_Health_Score || 0),
    Offer_Responsiveness_Score: Number(customer.Offer_Responsiveness_Score || 0),
    Investment_Readiness_Score: Number(customer.Investment_Readiness_Score || 0),
    Cross_Sell_Probability: Number(customer.Cross_Sell_Probability || 0),
    Upsell_Probability: Number(customer.Upsell_Probability || 0),
    Loan_Default_Risk: Number(customer.Loan_Default_Risk || 0),
    Churn_Probability: Number(customer.Churn_Probability || 0),
    Credit_Card_Holder: customer.Credit_Card_Holder === 'True' || customer.Credit_Card_Holder === 'true',
    Loan_Active: customer.Loan_Active === 'True' || customer.Loan_Active === 'true',
    Insurance_Holder: customer.Insurance_Holder === 'True' || customer.Insurance_Holder === 'true',
    Fixed_Deposit_Holder: customer.Fixed_Deposit_Holder === 'True' || customer.Fixed_Deposit_Holder === 'true',
  };
}

export function invalidateCustomerCache() {
  customerCache = null;
  customerMap = null;
}
