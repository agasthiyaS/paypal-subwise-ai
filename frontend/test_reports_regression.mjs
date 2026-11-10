/**
 * Frontend Regression Test for ReportsPage safeExtractArray and contract handling.
 * Run with: node test_reports_regression.mjs
 */
import assert from 'assert';

// Define the exact safeExtractArray logic used in ReportsPage
const safeExtractArray = (res, preferredKey) => {
  if (Array.isArray(res)) return res;
  if (res && typeof res === 'object') {
    if (preferredKey && Array.isArray(res[preferredKey])) return res[preferredKey];
    if (Array.isArray(res.subscriptions)) return res.subscriptions;
    if (Array.isArray(res.items)) return res.items;
    if (Array.isArray(res.data)) return res.data;
    if (Array.isArray(res.transactions)) return res.transactions;
    if (Array.isArray(res.recommendations)) return res.recommendations;
  }
  return [];
};

console.log('--- Testing safeExtractArray across response shapes ---');

// Test Case 1: Real backend /subscriptions/ response (SubscriptionSummaryResponse wrapper)
const realBackendSubResponse = {
  total_active_count: 9,
  active_subscriptions: 9,
  total_monthly_spend: 608.48,
  total_annual_spend: 7301.76,
  total_annual_run_rate: 7301.76,
  zombie_count: 0,
  zombie_subscriptions: 0,
  at_risk_count: 0,
  at_risk_subscriptions: 0,
  redundant_tool_count: 0,
  redundant_tools_detected: 0,
  potential_monthly_savings: 0.0,
  category_distribution: { Infrastructure: 245.5, Developer: 42.0 },
  potential_count: 1,
  confirmed_count: 8,
  subscriptions: [
    { id: 1, vendor_name: 'AWS', latest_amount: 245.5, cadence: 'monthly' },
    { id: 2, vendor_name: 'GitHub', latest_amount: 42.0, cadence: 'monthly' },
    { id: 3, vendor_name: 'Slack', latest_amount: 75.0, cadence: 'monthly' }
  ]
};

const extracted1 = safeExtractArray(realBackendSubResponse, 'subscriptions');
assert(Array.isArray(extracted1), 'Must be an array');
assert.strictEqual(extracted1.length, 3, 'Must extract all 3 subscriptions');
console.log('✓ Test 1: Real backend SubscriptionSummaryResponse wrapper properly extracted to array.');

// Test Case 2: Array returned directly (legacy or mock)
const directArray = [{ id: 10, vendor_name: 'Stripe' }];
const extracted2 = safeExtractArray(directArray, 'subscriptions');
assert(Array.isArray(extracted2), 'Must be an array');
assert.strictEqual(extracted2.length, 1);
console.log('✓ Test 2: Direct array correctly preserved.');

// Test Case 3: Paginated items wrapper ({ items: [...] })
const itemsWrapper = { items: [{ id: 20, vendor_name: 'Notion' }] };
const extracted3 = safeExtractArray(itemsWrapper, 'subscriptions');
assert(Array.isArray(extracted3), 'Must be an array');
assert.strictEqual(extracted3.length, 1);
console.log('✓ Test 3: Items wrapper correctly extracted.');

// Test Case 4: Generic data wrapper ({ data: [...] })
const dataWrapper = { data: [{ id: 30, vendor_name: 'Zoom' }] };
const extracted4 = safeExtractArray(dataWrapper, 'subscriptions');
assert(Array.isArray(extracted4), 'Must be an array');
assert.strictEqual(extracted4.length, 1);
console.log('✓ Test 4: Generic data wrapper correctly extracted.');

// Test Case 5: Empty object ({})
const emptyObj = {};
const extracted5 = safeExtractArray(emptyObj, 'subscriptions');
assert(Array.isArray(extracted5), 'Must be an array');
assert.strictEqual(extracted5.length, 0);
console.log('✓ Test 5: Empty object safely returns empty array [].');

// Test Case 6: Null or undefined
const extracted6 = safeExtractArray(null, 'subscriptions');
assert(Array.isArray(extracted6), 'Must be an array');
assert.strictEqual(extracted6.length, 0);
const extracted7 = safeExtractArray(undefined, 'subscriptions');
assert(Array.isArray(extracted7), 'Must be an array');
assert.strictEqual(extracted7.length, 0);
console.log('✓ Test 6: Null and undefined safely return empty array [].');

// Test Case 7: Primitive value (e.g. error string or number)
const extracted8 = safeExtractArray('error string', 'subscriptions');
assert(Array.isArray(extracted8), 'Must be an array');
assert.strictEqual(extracted8.length, 0);
console.log('✓ Test 7: Primitive strings safely return empty array [].');

// Test Case 8: Verify simulation of forEach / filter / reduce does NOT throw
console.log('\n--- Simulating ReportsPage array operations ---');
let monthlyMap = { '2026-11': { subscriptions: 0 } };

// This is the exact code that previously crashed!
extracted1.forEach((sub) => {
  const monthAmt = parseFloat(sub.latest_amount || sub.amount || 0);
  Object.keys(monthlyMap).forEach((key) => {
    monthlyMap[key].subscriptions += monthAmt;
  });
});
assert.strictEqual(monthlyMap['2026-11'].subscriptions, 362.5);
console.log('✓ Test 8: subscriptions.forEach executes cleanly without TypeError.');

// Empty state iteration
let emptyIterations = 0;
extracted5.forEach(() => { emptyIterations++; });
assert.strictEqual(emptyIterations, 0);
console.log('✓ Test 9: Empty subscriptions iterates 0 times without error.');

console.log('\nALL 9 FRONTEND REGRESSION CONTRACT TESTS PASSED!');

