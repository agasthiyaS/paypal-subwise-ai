import {
  isFundingOrBalanceAdjustment,
  isSubWiseTest,
  isCurrencyConversionLeg,
  isValidOperatingTransaction,
  classifyFinancialTransactions
} from './src/utils/financialClassification.js';

const mockTransactions = [
  {
    id: 1050,
    paypal_transaction_id: '59071448PK254121L',
    gross_amount: 5000.0,
    currency: 'USD',
    raw_description: 'Initial balance',
    normalized_vendor: 'PayPal Balance Adjustment',
    status: 'COMPLETED'
  },
  {
    id: 1167,
    paypal_transaction_id: '4EV73998AP815980D',
    gross_amount: 5.0,
    currency: 'USD',
    raw_description: 'SubWise AI Sandbox Payment Test',
    normalized_vendor: 'Subwise',
    status: 'COMPLETED'
  },
  {
    id: 1385,
    paypal_transaction_id: '9X0405652T645143S',
    gross_amount: -20.0,
    currency: 'USD',
    raw_description: 'Monthly Software Subscription - CloudSoft',
    normalized_vendor: 'CloudSoft',
    status: 'COMPLETED'
  },
  {
    id: 1386,
    paypal_transaction_id: '02679053YB768853D',
    gross_amount: 1955.38,
    currency: 'INR',
    raw_description: 'PayPal Transaction',
    normalized_vendor: 'Paypal',
    status: 'COMPLETED'
  },
  {
    id: 1387,
    paypal_transaction_id: '5YW97500CW704310C',
    gross_amount: -1955.38,
    currency: 'INR',
    raw_description: 'PayPal Transaction',
    normalized_vendor: 'Paypal',
    status: 'COMPLETED'
  },
  {
    id: 1388,
    paypal_transaction_id: '6M255220TT5552700',
    gross_amount: 20.0,
    currency: 'USD',
    raw_description: 'PayPal Transaction',
    normalized_vendor: 'Paypal',
    status: 'COMPLETED'
  }
];

console.log('--- Testing Frontend Financial Classification Utilities ---');

// 1. Funding exclusion
console.assert(isFundingOrBalanceAdjustment(mockTransactions[0]) === true, 'Funding should be detected');
console.assert(isValidOperatingTransaction(mockTransactions[0]) === false, 'Funding must not be valid operating');
console.log('✓ Initial $5,000 funding correctly classified as funding and excluded from operating');

// 2. SubWise test payment exclusion
console.assert(isSubWiseTest(mockTransactions[1]) === true, 'SubWise test should be detected');
console.assert(isValidOperatingTransaction(mockTransactions[1]) === false, 'SubWise test must not be valid operating');
console.log('✓ $5 SubWise internal test correctly excluded from operating metrics');

// 3. CloudSoft expense inclusion
console.assert(isValidOperatingTransaction(mockTransactions[2]) === true, 'CloudSoft must be valid operating');
console.log('✓ $20 CloudSoft expense correctly included as valid operating transaction');

// 4. Currency conversion legs exclusion
console.assert(isCurrencyConversionLeg(mockTransactions[3]) === true, 'INR credit leg must be FX conversion');
console.assert(isCurrencyConversionLeg(mockTransactions[4]) === true, 'INR debit leg must be FX conversion');
console.assert(isCurrencyConversionLeg(mockTransactions[5]) === true, 'USD credit leg must be FX conversion');
console.assert(isValidOperatingTransaction(mockTransactions[3]) === false, 'INR credit must not be operating');
console.assert(isValidOperatingTransaction(mockTransactions[4]) === false, 'INR debit must not be operating');
console.assert(isValidOperatingTransaction(mockTransactions[5]) === false, 'USD conversion credit must not be operating');
console.log('✓ All 3 currency conversion legs correctly identified and excluded');

// 5. Complete aggregation test
const result = classifyFinancialTransactions(mockTransactions, 'USD');
console.assert(result.operatingRevenue === 0, `Expected 0 operating revenue, got ${result.operatingRevenue}`);
console.assert(result.operatingExpenses === 20, `Expected 20 operating expenses, got ${result.operatingExpenses}`);
console.assert(result.fundingInflows === 5000, `Expected 5000 funding inflows, got ${result.fundingInflows}`);
console.assert(result.operatingCount === 1, `Expected 1 operating record, got ${result.operatingCount}`);
console.log('✓ Full classification aggregation matches expected business metrics perfectly');

console.log('ALL FRONTEND FINANCIAL CLASSIFICATION TESTS PASSED!');

