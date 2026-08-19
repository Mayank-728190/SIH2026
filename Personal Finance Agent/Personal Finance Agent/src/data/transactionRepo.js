import { readCSVFile, appendCSVRow } from './csvReader.js';

let transactionCache = null;
let customerTransactionsMap = null;
let maxTxnNumber = 1000000;

function loadTransactions() {
  if (!transactionCache) {
    console.log('[TransactionRepo] Loading transactions.csv...');
    transactionCache = readCSVFile('transactions.csv');
    customerTransactionsMap = new Map();
    
    for (const t of transactionCache) {
      if (!customerTransactionsMap.has(t.Customer_ID)) {
        customerTransactionsMap.set(t.Customer_ID, []);
      }
      customerTransactionsMap.get(t.Customer_ID).push(t);

      // Track max Txn ID for auto-incrementing
      if (t.Transaction_ID && t.Transaction_ID.startsWith('TXN_')) {
        const num = parseInt(t.Transaction_ID.replace('TXN_', ''), 10);
        if (!isNaN(num) && num > maxTxnNumber) {
          maxTxnNumber = num;
        }
      }
    }
    console.log(`[TransactionRepo] Loaded ${transactionCache.length} transactions across ${customerTransactionsMap.size} customers.`);
  }
}

export function getTransactionsByCustomer(customerId) {
  loadTransactions();
  const txns = customerTransactionsMap.get(customerId) || [];
  return txns.map(t => ({
    ...t,
    Transaction_Amount: Number(t.Transaction_Amount || 0),
    Transaction_Risk_Score: Number(t.Transaction_Risk_Score || 0),
    Fraud_Label: Number(t.Fraud_Label || 0),
  }));
}

export function getRecentTransactions(customerId, count = 10) {
  const txns = getTransactionsByCustomer(customerId);
  // Sort descending by date & time
  const sorted = [...txns].sort((a, b) => {
    const dateTimeA = `${a.Transaction_Date} ${a.Transaction_Time || '00:00:00'}`;
    const dateTimeB = `${b.Transaction_Date} ${b.Transaction_Time || '00:00:00'}`;
    return dateTimeB.localeCompare(dateTimeA);
  });
  return sorted.slice(0, count);
}

export function getTotalExpense(customerId, fromDate = null, toDate = null) {
  const txns = getTransactionsByCustomer(customerId);
  return txns.reduce((acc, t) => {
    if (t.Transaction_Type === 'Credit') return acc; // Only debit transactions count as expense
    if (t.Transaction_Status === 'Failed') return acc; // Ignore failed

    const tDate = t.Transaction_Date;
    if (fromDate && tDate < fromDate) return acc;
    if (toDate && tDate > toDate) return acc;

    return acc + t.Transaction_Amount;
  }, 0);
}

export function getCategoryWiseExpenses(customerId) {
  const txns = getTransactionsByCustomer(customerId);
  const categoryTotals = {};

  for (const t of txns) {
    if (t.Transaction_Type === 'Credit' || t.Transaction_Status === 'Failed') continue;
    const cat = t.Merchant_Category || 'Other';
    categoryTotals[cat] = (categoryTotals[cat] || 0) + Number(t.Transaction_Amount || 0);
  }

  return categoryTotals;
}

export function addTransaction(transactionInput) {
  loadTransactions();

  if (!transactionInput.Customer_ID) {
    throw new Error('Customer_ID is required to record a transaction.');
  }

  const amount = Number(transactionInput.Transaction_Amount);
  if (isNaN(amount) || amount <= 0) {
    throw new Error('Transaction Amount must be a positive number.');
  }

  maxTxnNumber++;
  const nextTxnId = 'TXN_' + String(maxTxnNumber).padStart(10, '0');
  const now = new Date();
  const dateStr = transactionInput.Transaction_Date || now.toISOString().split('T')[0];
  const timeStr = transactionInput.Transaction_Time || now.toTimeString().split(' ')[0];

  const newTxn = {
    Transaction_ID: nextTxnId,
    Customer_ID: transactionInput.Customer_ID,
    Transaction_Date: dateStr,
    Transaction_Time: timeStr,
    Transaction_Amount: String(amount),
    Transaction_Type: transactionInput.Transaction_Type || 'Debit',
    Merchant_Name: transactionInput.Merchant_Name || 'General Merchant',
    Merchant_Category: transactionInput.Merchant_Category || 'Other',
    Transaction_Channel: transactionInput.Transaction_Channel || 'UPI',
    Device_Type: transactionInput.Device_Type || 'Mobile',
    Transaction_Location: transactionInput.Transaction_Location || 'Local',
    Beneficiary_Type: transactionInput.Beneficiary_Type || 'Merchant',
    New_Beneficiary_Flag: String(transactionInput.New_Beneficiary_Flag ?? 0),
    International_Transaction_Flag: String(transactionInput.International_Transaction_Flag ?? 0),
    Transaction_Status: transactionInput.Transaction_Status || 'Success',
    Transaction_Risk_Score: String(transactionInput.Transaction_Risk_Score ?? 15),
    Fraud_Label: String(transactionInput.Fraud_Label ?? 0),
  };

  // Append to physical CSV file
  appendCSVRow('transactions.csv', newTxn);

  // Update in-memory cache dynamically
  transactionCache.push(newTxn);
  if (!customerTransactionsMap.has(newTxn.Customer_ID)) {
    customerTransactionsMap.set(newTxn.Customer_ID, []);
  }
  customerTransactionsMap.get(newTxn.Customer_ID).push(newTxn);

  console.log(`[TransactionRepo] Successfully appended transaction ${nextTxnId} for ${newTxn.Customer_ID}`);
  return {
    ...newTxn,
    Transaction_Amount: amount,
  };
}
