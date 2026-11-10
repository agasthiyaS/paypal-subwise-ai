/**
 * PayPal SubWise AI — Verified Demonstration Dataset
 * 
 * NOTICE:
 * This data is clearly labeled demonstration data designed for simulated evaluation.
 * It is NOT live transaction data from PayPal.
 */

export const DEMO_METADATA = {
  isDemonstrationData: true,
  environment: 'Demonstration Sandbox (Pre-Configured)',
  disclaimer: 'This is curated sample data to demonstrate cash-flow simulation and subscription analytics. It does not reflect live PayPal production accounts.',
  currency: 'USD',
  companyName: 'Acme Cloud Dynamics LLC',
  ownerName: 'Sarah Jenkins',
  industry: 'Software & Technology Services',
};

export const DEMO_FINANCIAL_METRICS = {
  totalIncome: 18450.00,
  incomeChangePct: 8.2,
  totalExpenses: 11280.00,
  expenseChangePct: -3.5,
  subscriptionExpenses: 1985.99,
  subscriptionChangePct: 14.1, // Price creep alert
  availableCashBalance: 52400.00,
  projectedRunwayMonths: 9.4,
  targetRunwayMonths: 6,
  financialHealthScore: 84, // 0 - 100
  financialHealthStatus: 'Healthy Buffer',
  potentialMonthlySavings: 548.00,
  potentialAnnualSavings: 6576.00,
};

export const DEMO_SUBSCRIPTIONS = [
  {
    id: 1,
    name: 'AWS Cloud Infrastructure',
    merchant: 'Amazon Web Services Inc',
    category: 'Cloud Infrastructure',
    amount: 540.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-18',
    isEssential: true,
    tier: 'Tier 1 (Core Ops)',
    status: 'Active',
    priceCreepPct: 4.2,
    confidenceScore: 0.98,
    usageScore: 94,
    notes: 'Primary hosting, EC2 clusters & S3 data pipeline.'
  },
  {
    id: 2,
    name: 'Google Workspace Enterprise',
    merchant: 'Google LLC',
    category: 'Productivity & Email',
    amount: 72.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-20',
    isEssential: true,
    tier: 'Tier 1 (Core Ops)',
    status: 'Active',
    priceCreepPct: 0.0,
    confidenceScore: 0.99,
    usageScore: 98,
    notes: 'Email, Docs, and Google Meet video conferencing.'
  },
  {
    id: 3,
    name: 'Slack Business Plus',
    merchant: 'Slack Technologies Inc',
    category: 'Team Collaboration',
    amount: 225.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-25',
    isEssential: true,
    tier: 'Tier 2 (Important)',
    status: 'At Risk',
    priceCreepPct: 25.0, // Significant creep
    confidenceScore: 0.96,
    usageScore: 82,
    notes: 'Increased by $45/mo due to 5 inactive provisioned seats.'
  },
  {
    id: 4,
    name: 'GitHub Enterprise Org',
    merchant: 'GitHub Inc',
    category: 'Developer Tools',
    amount: 49.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-28',
    isEssential: true,
    tier: 'Tier 1 (Core Ops)',
    status: 'Active',
    priceCreepPct: 0.0,
    confidenceScore: 0.97,
    usageScore: 95,
    notes: 'Source code repositories and CI/CD actions.'
  },
  {
    id: 5,
    name: 'HubSpot Marketing Hub',
    merchant: 'HubSpot Inc',
    category: 'CRM & Marketing',
    amount: 320.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-12-02',
    isEssential: true,
    tier: 'Tier 2 (Important)',
    status: 'Active',
    priceCreepPct: 0.0,
    confidenceScore: 0.95,
    usageScore: 78,
    notes: 'Inbound lead tracking and customer email workflows.'
  },
  {
    id: 6,
    name: 'OpenAI API Billing',
    merchant: 'OpenAI LLC',
    category: 'AI & Data Services',
    amount: 185.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-12-05',
    isEssential: true,
    tier: 'Tier 2 (Important)',
    status: 'At Risk',
    priceCreepPct: 32.1,
    confidenceScore: 0.94,
    usageScore: 88,
    notes: 'LLM inference endpoints for customer AI feature.'
  },
  {
    id: 7,
    name: 'Zoom Workplace Pro',
    merchant: 'Zoom Video Communications',
    category: 'Video Conferencing',
    amount: 65.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-14',
    isEssential: false,
    tier: 'Tier 3 (Discretionary)',
    status: 'Redundant',
    priceCreepPct: 0.0,
    confidenceScore: 0.96,
    usageScore: 35,
    notes: 'Redundant with Google Meet already included in Google Workspace.'
  },
  {
    id: 8,
    name: 'Asana Premium Workspaces',
    merchant: 'Asana Inc',
    category: 'Project Management',
    amount: 149.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-16',
    isEssential: false,
    tier: 'Tier 3 (Discretionary)',
    status: 'Redundant',
    priceCreepPct: 0.0,
    confidenceScore: 0.95,
    usageScore: 28,
    notes: 'Redundant with Notion workspace utilized by engineering and marketing.'
  },
  {
    id: 9,
    name: 'Notion Team Plan',
    merchant: 'Notion Labs Inc',
    category: 'Knowledge & Docs',
    amount: 48.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-22',
    isEssential: true,
    tier: 'Tier 2 (Important)',
    status: 'Active',
    priceCreepPct: 0.0,
    confidenceScore: 0.97,
    usageScore: 92,
    notes: 'Internal company wiki, product roadmaps, and sprint documentation.'
  },
  {
    id: 10,
    name: 'Dropbox Business Standard',
    merchant: 'Dropbox Inc',
    category: 'Cloud Storage',
    amount: 90.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-11-27',
    isEssential: false,
    tier: 'Tier 3 (Discretionary)',
    status: 'Zombie',
    priceCreepPct: 0.0,
    confidenceScore: 0.98,
    usageScore: 12,
    notes: 'Low activity detected. Files can be archived to Google Drive (included).'
  },
  {
    id: 11,
    name: 'Mailchimp Standard Plan',
    merchant: 'Intuit Mailchimp',
    category: 'Email Marketing',
    amount: 115.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-12-04',
    isEssential: false,
    tier: 'Tier 3 (Discretionary)',
    status: 'Redundant',
    priceCreepPct: 0.0,
    confidenceScore: 0.96,
    usageScore: 22,
    notes: 'Duplicate email system; marketing emails can be routed through HubSpot.'
  },
  {
    id: 12,
    name: 'Datadog Pro Infrastructure',
    merchant: 'Datadog Inc',
    category: 'DevOps & Monitoring',
    amount: 210.00,
    frequency: 'Monthly',
    nextPaymentDate: '2026-12-08',
    isEssential: true,
    tier: 'Tier 2 (Important)',
    status: 'Active',
    priceCreepPct: 7.5,
    confidenceScore: 0.93,
    usageScore: 84,
    notes: 'Application APM and server uptime telemetry.'
  },
];

export const DEMO_CASHFLOW_HISTORY_AND_FORECAST = [
  // Historical 6 Months
  { month: 'Jun 2026', income: 16800, expenses: 10800, subscriptions: 1820, balance: 42100, isForecast: false },
  { month: 'Jul 2026', income: 17400, expenses: 11100, subscriptions: 1850, balance: 45200, isForecast: false },
  { month: 'Aug 2026', income: 18100, expenses: 11400, subscriptions: 1890, balance: 48900, isForecast: false },
  { month: 'Sep 2026', income: 15900, expenses: 10900, subscriptions: 1940, balance: 49400, isForecast: false }, // Slight dip
  { month: 'Oct 2026', income: 17800, expenses: 11150, subscriptions: 1960, balance: 51250, isForecast: false },
  { month: 'Nov 2026', income: 18450, expenses: 11280, subscriptions: 1986, balance: 52400, isForecast: false }, // Current month
  // Forecast 6 Months Forward
  { month: 'Dec 2026', income: 18800, expenses: 11350, subscriptions: 1986, balance: 54350, isForecast: true },
  { month: 'Jan 2027', income: 17900, expenses: 11400, subscriptions: 1986, balance: 55350, isForecast: true },
  { month: 'Feb 2027', income: 18600, expenses: 11450, subscriptions: 1986, balance: 57000, isForecast: true },
  { month: 'Mar 2027', income: 19200, expenses: 11500, subscriptions: 1986, balance: 59200, isForecast: true },
  { month: 'Apr 2027', income: 19500, expenses: 11550, subscriptions: 1986, balance: 61650, isForecast: true },
  { month: 'May 2027', income: 20100, expenses: 11600, subscriptions: 1986, balance: 64650, isForecast: true },
];

export const DEMO_CATEGORY_BREAKDOWN = [
  { name: 'Cloud Infrastructure', value: 540.00, color: '#0070ba' },
  { name: 'CRM & Marketing', value: 435.00, color: '#003087' },
  { name: 'Team Collaboration', value: 225.00, color: '#10b981' },
  { name: 'DevOps & Monitoring', value: 210.00, color: '#f59e0b' },
  { name: 'AI & Data Services', value: 185.00, color: '#6366f1' },
  { name: 'Project Management', value: 149.00, color: '#ec4899' },
  { name: 'Cloud Storage', value: 90.00, color: '#8b5cf6' },
  { name: 'Productivity & Docs', value: 120.00, color: '#00cfde' },
];

export const DEMO_RECOMMENDATIONS = [
  {
    id: 1,
    type: 'CONSOLIDATE',
    title: 'Consolidate Zoom ($65/mo) into Google Meet',
    vendor: 'Zoom Video Communications',
    category: 'Video Conferencing',
    potentialMonthlySaving: 65.00,
    potentialAnnualSaving: 780.00,
    runwayImpactDays: 8,
    severity: 'High',
    insight: 'Your business already subscribes to Google Workspace Enterprise, which provides HD video conferencing via Google Meet. Eliminating duplicate Zoom licenses immediately preserves liquidity.',
    actionPlan: 'Transition team cal links to Google Meet, export recorded webinars, and cancel Zoom renewal before Nov 14.',
    scriptTemplate: 'Hello Zoom Billing Support,\n\nOur company (Acme Cloud Dynamics) is consolidating enterprise communications into our Google Workspace environment. Please ensure our monthly subscription (#ZM-49201) does not renew at the end of the current billing period on Nov 14.\n\nThank you,\nFinance Department'
  },
  {
    id: 2,
    type: 'CONSOLIDATE',
    title: 'Migrate Asana ($149/mo) Workflows into Notion',
    vendor: 'Asana Inc',
    category: 'Project Management',
    potentialMonthlySaving: 149.00,
    potentialAnnualSaving: 1788.00,
    runwayImpactDays: 18,
    severity: 'High',
    insight: 'Engineering and Product teams are actively using Notion ($48/mo) for sprint docs and roadmaps, while Asana utilization dropped to 28%. Centralizing tasks in Notion saves $1,788 annually.',
    actionPlan: 'Export Asana board CSVs, import into existing Notion Database templates, and revoke Asana team access.',
    scriptTemplate: 'Hi Asana Team,\n\nWe are restructuring internal workflows and consolidating task management into Notion. We will be discontinuing our Asana subscription effective Nov 16. Please confirm cancellation.\n\nBest regards,\nOperations Team'
  },
  {
    id: 3,
    type: 'DOWNGRADE',
    title: 'Audit Inactive Seats on Slack Business Plus',
    vendor: 'Slack Technologies Inc',
    category: 'Team Collaboration',
    potentialMonthlySaving: 45.00,
    potentialAnnualSaving: 540.00,
    runwayImpactDays: 6,
    severity: 'Medium',
    insight: 'Slack charges increased by +25% over the past quarter. Telemetry reveals 5 provisioned user seats have had zero login activity for over 60 days.',
    actionPlan: 'Open Slack Member Directory, deactivate the 5 dormant user accounts, and request a prorated billing credit from Slack customer support.',
    scriptTemplate: 'Hello Slack Support,\n\nWe completed an internal access review for Acme Cloud Dynamics and identified 5 provisioned members who have departed or become inactive. We have deactivated these accounts and request our billing count be adjusted down to active users immediately.\n\nSincerely,\nIT & Finance'
  },
  {
    id: 4,
    type: 'CANCEL',
    title: 'Retire Zombie Subscription: Dropbox Business ($90/mo)',
    vendor: 'Dropbox Inc',
    category: 'Cloud Storage',
    potentialMonthlySaving: 90.00,
    potentialAnnualSaving: 1080.00,
    runwayImpactDays: 11,
    severity: 'Medium',
    insight: 'Dropbox has registered under 12% usage over the past 90 days. Company files are already synchronized in Google Drive. This subscription represents unmonitored SaaS waste.',
    actionPlan: 'Run a one-time cloud sync to verify all assets are mirrored in Google Drive, then cancel auto-renewal in PayPal.',
    scriptTemplate: 'To Dropbox Customer Care,\n\nPlease terminate auto-renewal for our Dropbox Business team plan (Account #DB-98412) effective immediately. Please confirm final invoice generation.\n\nThank you,\nAdministration'
  },
  {
    id: 5,
    type: 'SWITCH_ANNUAL',
    title: 'Switch AWS EC2 Reserved Instances to Annual Commit',
    vendor: 'Amazon Web Services',
    category: 'Cloud Infrastructure',
    potentialMonthlySaving: 108.00,
    potentialAnnualSaving: 1296.00,
    runwayImpactDays: 14,
    severity: 'Low',
    insight: 'AWS is a mission-critical Tier 1 workload that will not be cancelled. Converting on-demand instances to 1-year Savings Plans yields standard 20% infrastructure cost savings.',
    actionPlan: 'Open AWS Cost Explorer, apply 1-Year Compute Savings Plan recommendation with no upfront payment.',
    scriptTemplate: null
  },
  {
    id: 6,
    type: 'CONSOLIDATE',
    title: 'Retire Mailchimp ($115/mo) in favor of HubSpot CRM',
    vendor: 'Intuit Mailchimp',
    category: 'Email Marketing',
    potentialMonthlySaving: 115.00,
    potentialAnnualSaving: 1380.00,
    runwayImpactDays: 14,
    severity: 'High',
    insight: 'HubSpot Marketing Hub ($320/mo) already includes enterprise email marketing and segmentation. Maintaining a separate Mailchimp account causes duplicate list sync fees.',
    actionPlan: 'Export Mailchimp subscriber tags to HubSpot contacts and terminate Mailchimp billing before Dec 4.',
    scriptTemplate: 'Dear Mailchimp Support,\n\nWe have migrated our marketing broadcasts to HubSpot CRM. Please cancel our monthly subscription for account #MC-8812 prior to next billing date.\n\nRegards,\nMarketing Operations'
  }
];

export const DEMO_UPCOMING_PAYMENTS = [
  { id: 7, name: 'Zoom Workplace Pro', date: '2026-11-14', amount: 65.00, category: 'Video Conferencing', isEssential: false },
  { id: 8, name: 'Asana Premium', date: '2026-11-16', amount: 149.00, category: 'Project Management', isEssential: false },
  { id: 1, name: 'AWS Cloud Hosting', date: '2026-11-18', amount: 540.00, category: 'Cloud Infrastructure', isEssential: true },
  { id: 2, name: 'Google Workspace', date: '2026-11-20', amount: 72.00, category: 'Productivity & Email', isEssential: true },
  { id: 9, name: 'Notion Team', date: '2026-11-22', amount: 48.00, category: 'Knowledge & Docs', isEssential: true },
  { id: 3, name: 'Slack Business Plus', date: '2026-11-25', amount: 225.00, category: 'Team Collaboration', isEssential: true },
];

