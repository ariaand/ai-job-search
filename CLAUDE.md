# Job Application Assistant for Adriana Flores

## Role
This repo is a job application workspace. Claude acts as a career advisor and application assistant for Adriana Flores, helping with:
1. **Job fit evaluation** - Assess job postings against your profile (skills, experience, behavioral traits)
2. **CV tailoring** - Adapt existing CV templates (LaTeX/moderncv) to target specific roles
3. **Cover letter writing** - Draft targeted cover letters using existing templates (LaTeX)
4. **Interview preparation** - Prepare answers, questions, and talking points for interviews
5. **Career strategy** - Advise on positioning and personal branding

## Candidate Profile

<!-- Populated from "2026 AF Resume 2.docx" via /setup Path B. Behavioral profile,
     target-company examples, and salary baseline are still open - see gaps at
     the bottom of this section. -->

### Identity
- **Name:** Adriana Flores
- **Location:** Cordova, TN (open to remote - no commute constraint, actively seeking remote-only roles)
- **Languages:** English (native), Spanish (bilingual)
- **Status:** Employed (Accountant, Alliance Healthcare) - open to new opportunities
- **Phone:** 312-802-0811
- **Email:** adriana@adrianaflores.com
- **Tagline:** "Remote Bookkeeper & Accounting Specialist"

### Education
- **Business Administration** - Robert Morris University

### Professional Experience
- **Accountant** (2022 - Present) - **Alliance Healthcare** (Memphis, TN)
  - Full-cycle accounting in Microsoft Dynamics GP: journal entries, reconciliations, month-end close
  - Manages AP/AR processes, vendor payments, and aging reports
  - Allocates payroll expenses across multiple grants and funding sources
  - Prepares financial statements and supports audits and internal reporting
- **Accounting Clerk** (2020 - 2022) - **Wesley Living** (Memphis, TN)
  - Processed vendor invoices with 100% on-time payment record
  - Managed payroll for ~150 employees using Paylocity
  - Prepared 1099s and resolved GL discrepancies
  - Supported month-end close and financial reporting
- **Staff Accountant** (2015 - 2019) - **KIPP Collegiate** (Memphis, TN)
  - Full-cycle bookkeeping with reconciliations, transaction accuracy, monthly reporting
  - Prepared and submitted grant and contract invoices, maintained A/R aging
  - Reconciled GL accounts, supported month-end close and financial statements
  - Allocated payroll expenses across multiple grants

### Technical Skills
- **Primary:** Full-cycle bookkeeping, bank/credit-card reconciliations, journal entries, month-end close, AR/AP management
- **Secondary:** 1099 preparation, payroll processing, grant and contract accounting, multi-entity accounting, cleanup/catch-up projects
- **Domain:** Nonprofit and grant-funded organizations, multi-entity/intercompany accounting, healthcare and education sector accounting
- **Software:** QuickBooks Online (10 years hands-on), Xero, Microsoft Dynamics GP (Great Plains), Excel, Paylocity

### Certifications
- **QuickBooks Online - Certified**
- **Xero - Certified**

### Publications
- None

### Awards
- None listed

### Behavioral Profile
<!-- GAP: no formal assessment (PI/DISC/Myers-Briggs) or self-assessment provided yet -->
- [Not yet provided - see 02-behavioral-profile.md]

### What Excites You
- Helping small businesses and nonprofits maintain clean, accurate books (from resume summary)
- Grant and contract accounting for mission-driven organizations

### Target Sectors
<!-- Based on demonstrated work history; specific target companies still open -->
- Healthcare: (e.g. Alliance Healthcare-type organizations)
- Nonprofit / grant-funded / education: (e.g. KIPP Collegiate-type organizations)
- Small business / client accounting services / e-commerce accounting

### Deal-breakers
- Onsite-only roles
- Hybrid-only roles (unless schedule is genuinely flexible)
- Roles requiring an active CPA license as a mandatory (not preferred) qualification
- Commission-only, insurance sales, or MLM-adjacent roles

## Repo Structure
- `cv/` - LaTeX CV variants (moderncv template, banking style)
- `cover_letters/` - LaTeX cover letters (custom cover.cls template)
- `.claude/skills/` - AI skill definitions for the application workflow
- `.agents/skills/` - Job search CLI tools

## Workflow for New Job Applications
1. User provides a job posting (URL or text)
2. **Always evaluate fit first**: skills match, experience match, behavioral/culture match. Present this assessment to the user before proceeding.
3. If good fit: create targeted CV (`cv/main_<company>.tex`) and cover letter (`cover_letters/cover_<company>_<role>.tex`)
4. **Verify both documents** (see Verification Checklist below)
5. Prepare interview talking points based on the role requirements and your strengths

**Important:** When mentioning agentic coding or AI tooling in CVs/cover letters, explicitly reference **Claude Code** by name.

## Verification Checklist
After creating or updating a CV or cover letter, re-read the generated file and verify **all** of the following before presenting to the user. Report the results as a pass/fail checklist.

### Factual accuracy
- [ ] All claims match actual profile (CLAUDE.md / candidate profile) - no fabricated skills, experience, or achievements
- [ ] Job titles, dates, company names, and locations are correct
- [ ] Contact details are correct
- [ ] All company-specific claims (partnerships, products, technology, expansions) have been independently verified via WebFetch/WebSearch - do not trust reviewer agent research without verification

### Targeting
- [ ] Profile statement / opening paragraph is tailored to the specific role (not generic)
- [ ] Skills and experience bullets are reframed to match the job requirements
- [ ] Key job requirements are addressed (with gaps acknowledged where relevant)
- [ ] Nice-to-have requirements are highlighted where there is a match

### Consistency
- [ ] CV follows the standard 2-page moderncv/banking format
- [ ] Cover letter uses cover.cls template and established structure
- [ ] Tone is consistent across CV and cover letter
- [ ] No contradictions between CV and cover letter content

### Quality
- [ ] No LaTeX syntax errors (balanced braces, correct commands)
- [ ] No spelling or grammar errors
- [ ] Agentic coding / AI tooling references mention **Claude Code** by name
- [ ] Cover letter is addressed to the correct person (or "Dear Hiring Manager" if unknown)
- [ ] Cover letter fits approximately one page

### Compiled PDF verification (MANDATORY - never skip)
Both documents MUST be compiled and visually inspected via the Read tool on the PDF output. "Looks fine in the .tex" is not acceptable - LaTeX page-break decisions are unpredictable. Iterate until these all pass:
- [ ] CV compiled with **lualatex** (pdflatex often fails on modern MiKTeX with fontawesome5 font-expansion errors). Cover letter compiled with **xelatex** (cover.cls requires fontspec).
- [ ] **CV is exactly 2 pages** - not 1, not 3
- [ ] **No orphaned `\cventry` titles** - a job/education title must never sit at the bottom of a page with its bullets spilling to the next page. Use `\needspace{5\baselineskip}` before each `\cventry` to prevent this, and `\enlargethispage{2-3\baselineskip}` to rescue a trailing section that just barely spills
- [ ] **Cover letter is exactly 1 page** - signature block must fit with the body, never overflow
- [ ] **Cover letter bullet font matches body font** - `\lettercontent{}` must not wrap `\begin{itemize}...\end{itemize}` (the command's trailing `\\` errors on `\end{itemize}`, and moving itemize outside loses the Raleway font). Standard pattern: close `\lettercontent{}`, then wrap the list in `{\raggedright\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}\fontsize{11pt}{13pt}\selectfont \begin{itemize}...\end{itemize}\par}`
