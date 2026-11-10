/**
 * Shared Financial Classification & Ledger Filtering Utilities
 * Ensures consistent exclusion of non-operating funding, internal sandbox test payments,
 * and currency conversion legs across Dashboard, Reports, and Analytics.
 */

export const NON_OPERATING_KEYWORDS = [
  'initial balance', 'account funding', 'balance adjustment', 'general funding',
  'deposit', 'bank transfer', 'wallet funding', 'reserve deposit', 'top up',
  'reversal', 'adjustment', 'paypal balance'
];

export const SUBWISE_TEST_KEYWORDS = [
  'subwise', 'subwise ai'
];

export const CURRENCY_CONVERSION_KEYWORDS = [
  'currency conversion', 'exchange rate', 'conversion leg', 'fx conversion', 'paypal transaction', 'paypal transfer'
];

/**
 * Checks if a transaction is non-operating capital funding or balance adjustment.
 */
export function isFundingOrBalanceAdjustment(tx) {
  if (!tx) return false;
  const desc = (tx.raw_description || '').toLowerCase();
  const cat = (tx.category || '').toLowerCase();
  const vendor = (tx.normalized_vendor || '').toLowerCase();
  return NON_OPERATING_KEYWORDS.some(kw => desc.includes(kw) || cat.includes(kw) || vendor.includes(kw));
}

/**
 * Checks if a transaction is an internal SubWise sandbox test payment.
 */
export function isSubWiseTest(tx) {
  if (!tx) return false;
  const desc = (tx.raw_description || '').toLowerCase();
  const cat = (tx.category || '').toLowerCase();
  const vendor = (tx.normalized_vendor || '').toLowerCase();
  return SUBWISE_TEST_KEYWORDS.some(kw => desc.includes(kw) || cat.includes(kw) || vendor.includes(kw));
}

/**
 * Checks if a transaction is an internal currency conversion leg or intermediate settlement entry.
 */
export function isCurrencyConversionLeg(tx, allTransactions = []) {
  if (!tx) return false;
  const desc = (tx.raw_description || '').toLowerCase().trim();
  const cat = (tx.category || '').toLowerCase().trim();
  const vendor = (tx.normalized_vendor || '').toLowerCase().trim();

  if (CURRENCY_CONVERSION_KEYWORDS.some(kw => desc.includes(kw) || cat.includes(kw) || vendor.includes(kw))) {
    return true;
  }

  // Cross-currency or generic internal transfers
  if (desc === 'paypal transaction' || vendor === 'paypal' || vendor === 'paypal transfer') {
    return true;
  }

  return false;
}

/**
 * Determines whether a transaction is a valid operating revenue or expense.
 * Must be completed, not funding, not a SubWise test, and not a currency conversion leg.
 */
export function isValidOperatingTransaction(tx, allTransactions = []) {
  if (!tx || (tx.status && tx.status.toUpperCase() !== 'COMPLETED')) {
    return false;
  }
  if (isFundingOrBalanceAdjustment(tx)) {
    return false;
  }
  if (isSubWiseTest(tx)) {
    return false;
  }
  if (isCurrencyConversionLeg(tx, allTransactions)) {
    return false;
  }
  return true;
}

/**
 * Segregates transactions into operating revenue, operating expenses, funding,
 * and currency conversion legs, respecting currency isolation.
 */
export function classifyFinancialTransactions(transactions = [], baseCurrency = 'USD') {
  let operatingRevenue = 0;
  let operatingExpenses = 0;
  let fundingInflows = 0;
  let conversionInflows = 0;
  let conversionOutflows = 0;
  let operatingCount = 0;

  const operatingTransactions = [];
  const conversionLegs = [];

  transactions.forEach((tx) => {
    if (!tx) return;
    const gross = Number(tx.gross_amount) || Number(tx.amount) || 0;
    const curr = (tx.currency || baseCurrency).toUpperCase();

    if (isFundingOrBalanceAdjustment(tx)) {
      if (gross > 0) fundingInflows += gross;
    } else if (isSubWiseTest(tx)) {
      // Excluded from operating metrics
    } else if (isCurrencyConversionLeg(tx, transactions)) {
      conversionLegs.push(tx);
      if (gross > 0) conversionInflows += gross;
      else conversionOutflows += Math.abs(gross);
    } else if (isValidOperatingTransaction(tx, transactions)) {
      operatingTransactions.push(tx);
      operatingCount++;
      // Only aggregate into base currency if matching currency
      if (curr === baseCurrency.toUpperCase()) {
        if (gross > 0) operatingRevenue += gross;
        else operatingExpenses += Math.abs(gross);
      }
    }
  });

  return {
    operatingRevenue: Math.round(operatingRevenue * 100) / 100,
    operatingExpenses: Math.round(operatingExpenses * 100) / 100,
    fundingInflows: Math.round(fundingInflows * 100) / 100,
    conversionInflows: Math.round(conversionInflows * 100) / 100,
    conversionOutflows: Math.round(conversionOutflows * 100) / 100,
    operatingCount,
    operatingTransactions,
    conversionLegs,
  };
}

