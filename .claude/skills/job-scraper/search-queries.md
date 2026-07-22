# Accounting Job Search Queries

## Search Sites

### Primary accounting job boards
- **accountingfly.com** — remote and flexible accounting, bookkeeping, tax, audit, controller, and finance roles
- **accountingjobs.com** — accounting and finance job listings
- **careers.aicpa-cima.com** — accounting, audit, tax, finance, and CPA-track roles
- **efinancialcareers.com** — finance, accounting, FP&A, analyst, and controller roles
- **roberthalf.com/us/en/jobs** — accounting, bookkeeping, payroll, AR/AP, and finance contract or permanent roles

### General job boards
- **linkedin.com/jobs**
- **indeed.com**
- **ziprecruiter.com**
- **glassdoor.com**
- **wellfound.com/jobs** — startup bookkeeping, finance operations, and accounting roles
- **remote.co/remote-jobs/accounting**
- **flexjobs.com/remote-jobs/accounting**
- **weworkremotely.com**
- **builtin.com/jobs/remote/finance**

### Employer and staffing career pages
Search company career pages for bookkeeping firms, fractional CFO firms, e-commerce companies, SaaS companies, property-management companies, real-estate businesses, nonprofits, and professional-services firms.

## Default Search Preferences

- Location: United States
- Work arrangement: remote first; include work-from-anywhere and flexible-schedule roles
- Employment types: full-time, part-time, contract, temporary, and fractional
- Date range: posted within the last 14 days
- Exclude: commission-only, unpaid, onsite-only, insurance sales, financial advisor sales, tax-preparer-only seasonal roles unless requested

## Priority 1: Bookkeeping and Staff Accounting

```text
site:linkedin.com/jobs ("remote bookkeeper" OR "senior bookkeeper" OR "full charge bookkeeper") (QuickBooks OR Xero) -onsite
site:indeed.com ("remote bookkeeper" OR "full charge bookkeeper") (QuickBooks Online OR Xero)
site:accountingfly.com (bookkeeper OR "staff accountant" OR "client accounting services") remote
site:accountingjobs.com (bookkeeper OR "staff accountant" OR "general ledger accountant") remote
site:remote.co/remote-jobs/accounting (bookkeeper OR accountant)
```

## Priority 2: Accounting Operations

```text
site:linkedin.com/jobs ("accounts payable specialist" OR "accounts receivable specialist" OR "accounting specialist") remote
site:indeed.com ("accounting coordinator" OR "accounting operations" OR "billing specialist") remote
site:roberthalf.com/us/en/jobs (bookkeeper OR "accounts payable" OR "accounts receivable" OR payroll) remote
site:ziprecruiter.com ("accounting clerk" OR "accounting assistant" OR "billing specialist") remote
```

## Priority 3: Senior Accounting and Controller Track

```text
site:linkedin.com/jobs ("senior accountant" OR "accounting manager" OR "assistant controller") remote
site:accountingfly.com ("senior accountant" OR controller OR "fractional controller") remote
site:careers.aicpa-cima.com ("senior accountant" OR "accounting manager" OR controller) remote
site:efinancialcareers.com ("financial reporting" OR "general ledger" OR "assistant controller") remote
```

## Priority 4: QuickBooks, Xero, and Client Accounting Services

```text
site:linkedin.com/jobs ("QuickBooks Online" OR QBO OR Xero) (bookkeeper OR accountant) remote
site:indeed.com ("client accounting services" OR CAS OR "outsourced accounting") remote
site:accountingfly.com (QuickBooks OR Xero OR "client advisory services") remote
site:wellfound.com/jobs (bookkeeper OR accountant OR "finance operations") remote
```

## Priority 5: Industry-Focused Accounting

```text
site:linkedin.com/jobs ("real estate accountant" OR "property accountant" OR "construction accountant") remote
site:indeed.com ("ecommerce accountant" OR "e-commerce bookkeeper" OR "SaaS accountant") remote
site:linkedin.com/jobs ("nonprofit accountant" OR "grant accountant" OR "fund accountant") remote
site:indeed.com ("law firm bookkeeper" OR "legal bookkeeper" OR "trust accounting") remote
```

## Priority 6: Flexible and Part-Time Roles

```text
site:flexjobs.com/remote-jobs/accounting (bookkeeper OR accountant OR payroll)
site:remote.co/remote-jobs/accounting (part-time OR contract OR flexible)
site:linkedin.com/jobs ("part-time bookkeeper" OR "contract accountant" OR "fractional accountant") remote
site:indeed.com ("part time remote bookkeeper" OR "contract remote accountant")
```

## Role Keywords

Use these titles to expand searches:

- Bookkeeper
- Full-Charge Bookkeeper
- Senior Bookkeeper
- Staff Accountant
- Senior Accountant
- General Ledger Accountant
- Accounting Specialist
- Accounting Coordinator
- Accounting Assistant
- Accounts Payable Specialist
- Accounts Receivable Specialist
- Billing Specialist
- Payroll Specialist
- Reconciliation Specialist
- Property Accountant
- Real Estate Accountant
- E-commerce Accountant
- Client Accounting Services Accountant
- Outsourced Accountant
- Accounting Manager
- Assistant Controller
- Fractional Controller
- Finance Operations Specialist
- Virtual Accounting Assistant

## Skill Keywords

Prioritize roles mentioning:

- QuickBooks Online or QBO
- Xero
- Microsoft Dynamics GP or Great Plains
- Excel
- Bank and credit-card reconciliations
- General ledger
- Journal entries
- Month-end close
- Financial statements
- Accounts payable and accounts receivable
- Payroll
- Cash flow
- Budgeting and forecasting
- Revenue recognition
- Intercompany accounting
- Property accounting
- E-commerce accounting
- Client accounting services

## Exclusion Keywords

Use negative terms where supported:

```text
-sales -commission -insurance -advisor -onsite -door-to-door -unpaid
```

Do not automatically exclude CPA-required roles. Instead, flag them when a CPA license is mandatory rather than preferred.

## Result Ranking

Score jobs in this order:

1. Remote and flexible schedule
2. Strong match to bookkeeping or accounting experience
3. QuickBooks Online, Xero, Microsoft Dynamics GP, or Excel relevance
4. Full-time W-2 roles, then part-time W-2, then contract roles
5. Clear salary range and direct employer application link
6. Posted within the last seven days

Flag these separately:

- Requires CPA license
- Requires public-accounting audit experience
- Requires advanced tax-preparation credentials
- Hybrid or location-restricted remote role
- Contract role without benefits
- Salary omitted

## Adapting Queries

- `/scrape bookkeeping` — run Priority 1, Priority 4, and Priority 6
- `/scrape staff accountant` — run Priority 1, Priority 3, and Priority 4
- `/scrape accounts payable` — run Priority 2 and Priority 6
- `/scrape controller` — run Priority 3 and Priority 4
- `/scrape real estate` — run Priority 5 plus bookkeeping searches
- `/scrape broad` — run all categories
