import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import crypto from 'node:crypto';
import path from 'node:path';
import zlib from 'node:zlib';
const here=path.dirname(new URL(import.meta.url).pathname);
const dwp=process.env.OKF_DWP_ROOT || '/Users/crpage/repos/okf-dwp';
const demo=process.env.AI_DEMO_ROOT || '/Users/crpage/tmp/ai-demo-learning-design';
const explorer=process.env.OKF_EXPLORER_ROOT || '/Users/crpage/repos/okf-explorer';
for(const [repo,expected] of [[demo,'977193212c23923824b54d4e0766ffcad9d17bf0'],[dwp,'d45774648f00008ffff744a9c8d37bd154070d1c'],[explorer,'fff8781907aa46aed40c70a984b502c12dd5e201']]){
  const actual=execFileSync('git',['-C',repo,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
  if(actual!==expected)throw new Error('Review source revision change before regenerating: '+repo);
}
const registry=JSON.parse(fs.readFileSync(dwp+'/evaluation/staff-questions/cases.json'));
const corpusManifest=JSON.parse(fs.readFileSync(dwp+'/combined/data/manifest.json'));
const catalogue=corpusManifest.chunks.datasets.flatMap(p=>JSON.parse(p.endsWith('.gz')?zlib.gunzipSync(fs.readFileSync(dwp+'/combined/'+p)):fs.readFileSync(dwp+'/combined/'+p)));
for(const record of catalogue) record.route ||= record.open || 'dataset/'+record.name;
const routes=new Set(catalogue.map(x=>x.route));
const candidate=new Map(registry.source_candidates.map(x=>[x.id,x]));
const cases=new Map(registry.cases.map(x=>[x.id,x]));
const sid=n=>'staff-'+String(n).padStart(3,'0');
// Each tuple is title | observable outcome | submitted practice artefact.
const caseLessons={
1:['Scope a journey abroad','Distinguish the benefit, destination, duration, purpose and relevant period before selecting evidence.','Create a clarification tree; compare temporary absence, treatment and permanent departure without claiming one universal rule.'],
2:['Separate age from first entitlement','Distinguish pensionable age, qualifying conditions, claim and payment dates.','For the supplied birth-date example, mark which date questions the captured table can support and which need further evidence; do not produce an entitlement decision.'],
3:['State Pension and PIP','Distinguish separate qualification from an assumed payment offset.','Draw a directed interaction with explicit component, period and unresolved evidence.'],
4:['Separate pension regimes and components','Identify new State Pension, legacy retirement pension and transitional evidence as different scopes.','Produce a regime-and-component map with source-backed prerequisites and an unresolved NI-record boundary.'],
5:['Other benefits alongside State Pension','Separate possible additional support from established entitlement.','Make a candidate-benefit matrix with a qualifying-condition column; reject automatic passporting.'],
6:['Challenge the savings-maximum premise','Distinguish capital, valuation, disregards and income treatment from a single assumed cut-off.','Create a dependency map; label missing conditions rather than returning a universal savings maximum.'],
7:['Build a dated Pension Credit series','Bind each rate observation to an effective period, component and source version.','Populate a five-period evidence table; explicitly leave unavailable observations blank.'],
8:['Resolve SDA before retrieving rates','Keep Severe Disablement Allowance distinct from the Pension Credit severe-disability addition.','Ask for clarification and build two separately labelled evidence routes; do not choose a meaning silently.'],
9:['Additional amounts over time','Distinguish separate additional amounts and their qualifying conditions in a dated comparison.','Create a component-by-period matrix; record both missing rates and missing qualifications.'],
10:['Map assessment elements','Separate an input, an eligibility condition and a calculation parameter.','Classify every proposed threshold and identify the source, period and unresolved dependency.'],
11:['Housing Benefit and Pension Credit','Distinguish income treatment, housing costs and passporting direction.','Draw separate candidate relationships and identify what evidence is needed for each.'],
12:['Self-funded permanent care','Retain partner and household qualifications while examining a self-funded scenario.','Write a qualified evidence note with headings, continuations and household assumptions visible.'],
13:['Publicly funded permanent care','Show why changing funding does not remove the need to check household and component rules.','Compare with the self-funded scenario; annotate every changed fact and unresolved dependency.'],
14:['Identify relevant partner facts','Distinguish partner, couple, household membership and a person merely sharing accommodation.','Build a fact-to-definition table and flag any missing facts before proposing an interpretation.'],
15:['Specify calculation inputs','Trace proposed inputs to their purpose, evidence and applicability.','Produce an input dictionary that separates unknown, zero, not applicable and not supplied.'],
16:['Describe calculation dependencies','Represent the structure of a calculation without treating an incomplete source package as an executable formula.','Draw a dependency graph with units, effective periods and unresolved branches; do not calculate an award.'],
17:['Test the partner comparison','Explain how a partner scenario changes the evidence needed rather than just changing a numeric amount.','Compare synthetic single and couple fact patterns while keeping all other facts constant.'],
18:['Challenge all care-home scenarios','Define a bounded scenario space and identify what an all-scenarios claim would require.','Submit a matrix of permanence, funding, partner/household and component distinctions, with uncovered cells.'],
19:['Explain Pension Credit clearly','Give a plain-English structural explanation while separating source statements from interpretation.','Write a short explanation and an evidence ledger; retain limitations instead of hiding them in a footnote.'],
20:['Trace qualification conditions','Separate demonstrated conditions from assumptions about facts, dates and regime.','Create a conditions-and-evidence checklist with an explicit cannot-determine outcome.'],
21:['Separate eligibility from rate','Keep the qualifying test, component and dated rate as distinct evidence needs.','Prepare a review brief that cannot collapse these three decisions into one lookup.'],
22:['State Pension within Pension Credit research','Distinguish receipt of one benefit from qualification for another and the treatment of income.','Prepare a directed interaction note with an explicit counterexample to automatic entitlement.'],
24:['Additional support with IIDB','Separate IIDB qualification, supplements and other benefit conditions.','Build a candidate-support map; mark every unproven dependency.'],
25:['IIDB around pension age','Distinguish IIDB from Reduced Earnings Allowance and related age-dependent questions.','Create a transition table with independent evidence requirements for each named benefit.'],
26:['Child DLA to PIP: first occurrence','Distinguish age-related transition, an existing award, a new claim and relevant dates.','Capture the exact governed input tuple and an unresolved transition checklist for later replay.'],
27:['IIDB and JSA variants','Separate income-based, contributory and New Style JSA before discussing interactions.','Compare three variant-specific evidence plans; reject a single unqualified yes/no answer.'],
28:['IIDB and ESA variants','Separate income-related, contributory and New Style ESA before discussing interactions.','Build a variant matrix that identifies missing overlap and income-treatment evidence.'],
29:['IIDB and disability benefit families','Distinguish benefit-level associations from component-specific payment rules.','Make a directed component map for IIDB, PIP, Attendance Allowance and DLA with provenance.'],
30:['IIDB and PIP in detail','Explain why a related-benefit link does not prove the rule for concurrent payment.','Audit one candidate relationship against its cited source and list unresolved qualifications.'],
31:['Additional support associated with PIP','Separate a possible qualifying benefit from automatic entitlement to a supplement.','Prepare a conditions-first discovery matrix with daily-living and mobility components distinguished.'],
32:['PIP around pension age','Distinguish the treatment of an existing award from a new claim at a different date.','Submit a change-of-facts counterexample and the evidence it requires.'],
33:['Child DLA to PIP: replay occurrence','Recognise the duplicate wording and reproduce governed evidence under identical inputs.','Replay staff-026 with the same version and budget; compare evidence identity, not merely answer wording.'],
34:['PIP and JSA variants','Separate the PIP component from the JSA regime and proposed interaction.','Submit a variant-specific directed map and a negative control changing the JSA regime.'],
35:['PIP and ESA variants','Separate the PIP component from the ESA regime and proposed interaction.','Show which evidence is shared and which must be re-established after an ESA-variant change.'],
36:['PIP, Attendance Allowance and DLA','Distinguish age, component, transition and overlap questions.','Produce a comparison with no assumed symmetric equivalence between these benefits.'],
37:['War pensions and constant attendance','Keep War Pensions Constant Attendance Allowance separate from the industrial injuries allowance.','Resolve the terminology, scope the requested variations and record missing rates or overlap rules instead of adding payments.'],
38:['Caring qualification','Identify source-backed caring conditions separately from evidence that they are met.','Build a conditions-to-evidence checklist using only synthetic facts.'],
39:['Caring interactions','Distinguish Carer’s Allowance from a Pension Credit carer addition and impacts on another person.','Draw directed claimant/carer/other-person effects and test an unsupported symmetry claim.'],
40:['Caring for several people','Avoid inferring multiple payments from multiple caring responsibilities.','Compare one-person and two-person synthetic scenarios and justify every proposed change or non-conclusion.'],
23:['Pension Credit and a move abroad','Re-scope the general absence question for the named benefit and temporary/permanent distinction.','Create a benefit-specific evidence plan and explain why the general absence result cannot simply be copied.']
};
const lesson=(title,outcome,practice,evidence=[],questionIds=[],minutes=3)=>({title,outcome,practice,evidence_routes:evidence,question_ids:questionIds,minutes});
const cLesson=n=>{const id=sid(n),c=cases.get(id),v=caseLessons[n];return lesson(...v,c.candidate_ids.map(id=>candidate.get(id).route),[id],4);};
const personas={adviser:'persona/welfare-rights-adviser',pensions:'persona/pensions-specialist',policy:'persona/policy-law-reviewer',assurance:'persona/evidence-assurance-reviewer',engineer:'persona/knowledge-engineer',assisted:'persona/assisted-support',applicant:'persona/applicant-change-reporter',rules:'persona/rules-architect'};
const paths=[];
function add(id,title,demoIds,roles,prerequisites,objective,assessment,steps){paths.push({id,title,demo_ids:demoIds,persona_routes:roles.map(x=>personas[x]),prerequisites,objective,assessment,steps:steps.map((s,i)=>({...s,id:`${id}-s${String(i+1).padStart(2,'0')}`,route:`learning/${id}/s${String(i+1).padStart(2,'0')}`,route_status:'proposed-lesson-record-not-published'}))});}
add('p01','Read evidence before trusting an answer',[1,2,3],['adviser','pensions','policy','assurance','engineer','assisted'],[],
'Build a reproducible claim-to-evidence ledger and stop when the supplied material is insufficient.',
'Classify an unseen evidence package, verify one claim and reject one unsupported claim. All mandatory boundaries must pass.',[
lesson('Baseline and role','State what success looks like for your role.','Answer three baseline prompts without help; retain them for later comparison.',['persona/evidence-assurance-reviewer']),
lesson('Distinguish the layers','Separate original guidance, extracted text and project-authored interpretation.','Classify three items and explain the authority each does and does not have.',['chapter/77','term/dmg-evidence-assessment']),
lesson('Read the source in context','Check a paragraph with its heading and continuation.','Capture the locator and a qualification that would be lost in an isolated quotation.',['page/77/0020','page/77/0021']),
lesson('Use concepts without overclaiming','Distinguish a mention tag, semantic assertion and legal applicability.','Explain why each visible link is or is not enough to support a claim.',['staff-domain/partner']),
lesson('Separate search, context and answer','Identify which operation finds records, assembles evidence or generates an answer.','Draw the three stages and name the artefact returned by each.',['persona/knowledge-engineer']),
lesson('Read insufficiency honestly','Distinguish retained candidates, required evidence and unresolved obligations.','Write three separately defined denominators and identify an omitted requirement.',['staff-domain/calculation']),
lesson('Make the result accessible','Explain a result without relying on colour, jargon or pointer-only actions.','Use keyboard navigation and give a plain-English explanation with one source and one gap.',['persona/assisted-support']),
lesson('Foundation assessment','Apply the evidence rubric independently.','Submit a claim ledger, a refused unsupported conclusion and a reproducible source identity.',['term/dmg-evidence-assessment'],[],6)
]);
add('p02','Absence abroad and residence',[1],['adviser','policy'],['p01'],'Scope absence questions and expose benefit-specific exceptions without making a universal claim.','Pass a changed-duration or changed-purpose case; explicitly re-evaluate applicability.',[
lesson('Set the scope','Name the missing benefit, jurisdiction, dates and purpose.','Write the minimum clarification questions.',['staff-domain/abroad']),cLesson(1),
lesson('Inspect territorial assumptions','Locate the territorial and temporal scope of a candidate passage.','Annotate what cannot be carried into another jurisdiction.',['page/dmg-vol2-ch7-part1/0116']),cLesson(23),
lesson('Read continuations','Avoid treating the first matching paragraph as the whole rule.','Follow the chapter context and record a remaining source dependency.',['document/dmg-vol2-ch7-part6']),
lesson('Change a material fact','Explain why a permanent move cannot inherit a temporary-absence conclusion.','Submit a before/after evidence-requirement table.',['staff-domain/abroad']),
lesson('Absence assessment','Give a qualified evidence plan for an unseen absence scenario.','Submit scope, sources, exceptions and an escalation decision.',['persona/policy-law-reviewer'],[],6)
]);
add('p03','Pension regimes, age and transitions',[1],['pensions','policy'],['p01'],'Separate age, regime, conditions, claim and payment across State Pension and disability transitions.','Classify an unseen transition without equating age with entitlement or first payment.',[
lesson('Create a regime map','Separate new State Pension from the legacy regime.','Draw two source branches and list the date needed to choose between them.',['staff-domain/new-state-pension','staff-domain/retirement-pension']),
cLesson(2),cLesson(4),cLesson(25),cLesson(32),
lesson('Audit the age table','Preserve the table heading, band and continuation.','Explain what the table establishes and what it does not establish.',['page/dmg-vol12-ch74/0068']),
lesson('Remove the date','Recognise when an answer becomes unsupported after a date or regime is removed.','Reject or qualify a deliberately under-specified synthetic case.',['staff-domain/pension-age']),
lesson('Transition assessment','Present a regime-aware evidence brief.','Submit a timeline separating qualification, claim, award and payment.',['staff-domain/payment'],[],6)
]);
add('p04','Pension Credit inputs and calculation structure',[1,2,3],['pensions','rules','assurance'],['p01'],'Explain Pension Credit assessment dependencies without turning incomplete guidance into an award calculator.','Submit an input dictionary and dependency graph with typed unknowns, dated parameters and unresolved obligations.',[
lesson('Distinguish the decisions','Separate eligibility, inputs, components and payable amount.','Sketch four boxes and the evidence each requires.',['staff-domain/calculation']),
...[19,20,6,10,15,16,21].map(cLesson),
lesson('Test a misleading threshold','Detect a capital example being presented as a universal maximum.','Repair the claim and show the missing valuation or disregard dependency.',['term/capital-valuation','term/capital-disregards']),
lesson('Calculation-structure assessment','Explain a complete design with explicit unresolved branches.','Submit the dependency graph and input dictionary; no personal award or production formula.',['persona/rules-architect'],[],6)
]);
add('p05','Historical rates, additions and ambiguous terms',[1,3],['pensions','policy','assurance'],['p01'],'Construct a date-bound evidence series and resolve SDA without inventing missing values.','Deliver a five-period table with a source for every populated cell, explicit gaps and separate SDA meanings.',[
lesson('Define the five-period window','Turn a relative request into an explicit reproducible period.','Record the as-of date and agree five benefit years; for the demo use 2022/23–2026/27 as a proposed window, subject to available evidence.',['staff-domain/rates']),
cLesson(8),cLesson(7),cLesson(9),
lesson('Separate effective and capture dates','Identify which date governs a rate observation.','Label a source date, effective period and acquisition date separately.',['page/77/0064']),
lesson('Keep missing observations missing','Avoid filling an absent year from memory or interpolation.','Add a gap row and a source acquisition requirement.',['page/dmg-memo-02-26-f7835f1e40/0002']),
lesson('Test a mislabelled amount','Detect an amount assigned to the wrong component or period.','Correct a deliberately relabelled table cell and explain the evidence.',['staff-domain/severe-disability-addition','staff-domain/sda']),
lesson('Rates assessment','Produce an auditable historical comparison.','Submit the table, terminology decision, gaps and provenance; never substitute a present rate.',['staff-domain/rates'],[],6)
]);
add('p06','Partners, household and care-home changes',[1,2,3],['adviser','pensions','assurance'],['p01'],'Preserve household qualifications and distinguish permanence, funding and components when reviewing care-home questions.','Pass a new household/funding variant and identify omitted qualifications in a plausible answer.',[
lesson('Model the facts','Distinguish partner status, household membership, permanence and funding.','Create a synthetic fact matrix without claimant identifiers.',['staff-domain/partner','staff-domain/care-home']),
...[14,17,12,13,18].map(cLesson),
lesson('Read the qualifying heading','Detect a source heading that limits a quoted proposition.','Annotate the heading and continuation before accepting a claim.',['page/78/0025','page/77/0020']),
lesson('Check ignored-person dependencies','Recognise why sharing accommodation alone may not settle a disability-addition question.','Record normal-residence, ignored-person and partner dependencies still needing review.',['staff-domain/severe-disability-ignored-persons','staff-domain/severe-disability-normal-residence']),
lesson('Review a plausible AI answer','Find a material omission despite an exact quotation.','Mark the unsupported inference and rewrite it with the missing condition visible.',['staff-domain/household-separation']),
lesson('Household assessment','Explain changed evidence needs after a material fact changes.','Submit the scenario matrix and an independent critique of a new answer.',['persona/pensions-specialist'],[],6)
]);
add('p07','Directed benefit interactions and disability transitions',[1],['adviser','assurance','policy'],['p01'],'Distinguish qualification, income treatment, overlap, passporting and transition for named benefit variants.','Pass a changed-variant and reversed-edge case; reproduce the duplicate question package exactly.',[
lesson('Classify an interaction','Name the relation before evaluating whether it is supported.','Define five relation types in plain English and give a non-example of each.',['staff-domain/overlap']),
lesson('Draw directed edges','Keep source, target, component and regime explicit.','Demonstrate why an A-to-B relation cannot simply be reversed.',['term/dmg-overlapping-benefits']),
...[3,5,11,22,24,26,27,28,29,30,31,33,34,35,36,37].map(cLesson),
lesson('Counterexample round','Detect a variant swap and an invalid symmetric inference.','Correct both errors and identify the evidence to reacquire.',['staff-domain/esa-new-style','staff-domain/jsa-income-based']),
lesson('Interaction assessment','Produce a bounded directed interaction map.','Submit two variant-specific maps, duplicate-replay identities and unresolved conditions.',['persona/evidence-assurance-reviewer'],[],6)
]);
add('p08','Caring conditions and effects on others',[1],['adviser','assurance'],['p01'],'Separate caring conditions, qualifying payments and interactions without assuming multiple awards.','Reject a doubled-payment inference and distinguish effects on the carer from effects on another person.',[
lesson('Distinguish the people and payments','Separate carer, cared-for person, Carer’s Allowance and a carer additional amount.','Draw a labelled people-and-payments diagram.',['staff-domain/carers-allowance','staff-domain/carer-addition']),
...[38,39,40].map(cLesson),
lesson('Evidence of caring','Distinguish a condition from evidence that a synthetic case meets it.','Create an evidence checklist and identify unknown facts.',['term/ca-care-statement-evidence']),
lesson('Change the qualifying payment','Re-evaluate dependencies when one relevant fact changes.','Record which conclusions must be withdrawn or rechecked.',['term/ca-qualifying-disability-payment']),
lesson('Caring assessment','Give a supported scope statement and a safe next step.','Submit the directed map, source locators and unresolved evidence.',['persona/welfare-rights-adviser'],[],6)
]);
add('p09','Test whether OKF improves the AI demonstration',[1],['engineer','assurance','policy'],['p01','p06'],'Measure token use and evidence quality fairly without presuming the desired result.','Publish a paired experiment with complete accounting, blinded claim assessment and failed runs retained.',[
lesson('State a falsifiable hypothesis','Separate token economy from answer quality.','Pre-register success thresholds and explicitly allow no improvement or worse results.',['persona/knowledge-engineer']),
lesson('Freeze the experiment','Keep model, settings, question, source version and output budget comparable.','Create the input manifest and record unavoidable differences between conditions.',['persona/knowledge-engineer']),
lesson('Choose representative cases','Cover ambiguity, dates, interactions and household qualification.','Select staff-002, 006, 008, 012, 026 and 033 plus an unknown-term control.',['staff-domain/partner'],[2,6,8,12,26,33].map(sid)),
lesson('Define the controls','Distinguish raw-source versus OKF evidence from a no-evidence control.','Prepare equal-source A/B packages; retain no-evidence as a separate diagnostic, not the fair baseline.',['term/dmg-evidence-assessment']),
lesson('Measure all the costs','Count prompts, tool returns, retries, output and amortised preparation separately.','Submit totals, latency and failure rates for repeated runs, with unavailable provider fields labelled.',['persona/knowledge-engineer']),
lesson('Review claims independently','Separate citation match from correctness, qualifications and completeness.','Blind the treatment labels and score claims against the same frozen evidence.',['persona/policy-law-reviewer']),
lesson('Replay and disclose','Retain exact identities and explain failures or ties.','Replay the duplicate and unknown control; retain raw results and exclusions.',['persona/evidence-assurance-reviewer']),
lesson('Comparison assessment','Make only conclusions supported by the experiment.','Submit a paired results table, variability, limitations and a reproducibility manifest.',['persona/evidence-assurance-reviewer'],[],6)
]);
add('p10','Design an accessible Pension Credit application journey',[2],['applicant','assisted','engineer','pensions'],['p01','p04','p06'],'Map an official form and its notes to a synthetic, accessible application flow without equating data collection with entitlement.','Submit a versioned field map and a keyboard-complete synthetic journey, with missing form evidence explicitly blocked.',[
lesson('Set the application boundary','Separate a demonstration submission from an official claim.','Write the opening and confirmation copy; use fictional data and a local demo receipt.',['persona/applicant-change-reporter']),
lesson('Acquire the form family','Pin PC1, PC1 notes and PC1H as separate source artefacts.','Record publication version, original URLs, hashes, page locators and extraction checks.',['staff-domain/calculation']),
lesson('Trace each field','Link collected data to an exact form question and purpose.','Build the form-question to field to validation to conditional-routing matrix.',['staff-domain/calculation']),
lesson('Represent uncertainty','Keep unknown, empty, zero and not applicable distinct.','Create synthetic missing-data cases and explain what the user should do next.',['staff-domain/eligibility']),
lesson('Model household branches','Use validated form conditions to design household and care branches.','Trace two fictional journeys without deriving branches solely from benefit mention tags.',['staff-domain/partner','staff-domain/care-home']),
lesson('Prototype with CASA','Choose and pin a tested CASA package and accessible components.','Retain package identity, route tests, labels, error summary and keyboard results.',['persona/knowledge-engineer']),
lesson('Check answers and corrections','Let a person inspect and change every answer before submission.','Demonstrate correction, cancellation and recovery with consistent state.',['persona/assisted-support']),
lesson('Application-design assessment','Prove field provenance and accessible completion.','Submit the field map, recordings and fictional receipt; block release if required source fields remain unverified.',['persona/applicant-change-reporter'],[],6)
]);
add('p11','Demonstrate a trustworthy agent-assisted application',[2],['engineer','assisted','assurance'],['p10'],'Demonstrate callable browser tools that share validation and user control with the human application flow.','Complete the same synthetic case through both routes, prove result parity, consent and failure recovery.',[
lesson('Verify the host capability','Distinguish tool registration from callable WebMCP in the actual host.','Record browser, host, API and one successful observed discovery/invocation; otherwise label the path blocked.',['persona/knowledge-engineer']),
lesson('Specify a small tool surface','Define inspect, update, validate, review and submit operations with clear boundaries.','Write input/output contracts and state which operations mutate draft or submitted state.',['persona/rules-architect']),
lesson('Share the validation','Apply the same rules and state to human and tool-driven entry.','Submit the same invalid and valid values through both routes and compare outcomes.',['persona/knowledge-engineer']),
lesson('Keep the person in control','Bind confirmation to the exact reviewed application state.','Show a changed answer invalidating earlier confirmation; do not treat conversation text as blanket submission authority.',['persona/assisted-support']),
lesson('Test cancellation and retry','Prevent duplicate submission and support recoverable tool failure.','Demonstrate a cancelled request, retry and one fictional receipt with a stable submission identity.',['persona/evidence-assurance-reviewer']),
lesson('Treat content as data','Ignore instructions embedded in retrieved guidance or field content.','Run an inert injection fixture and show that it cannot alter permissions or submission policy.',['persona/knowledge-engineer']),
lesson('Measure parity and cost','Compare the same completed application through human and agent routes.','Report correctness, recovery, calls, tokens and elapsed time without assuming the agent route wins.',['persona/evidence-assurance-reviewer']),
lesson('Agent-assistance assessment','Prove callable capability, parity and informed confirmation.','Submit invocation evidence, a human-route comparison and failed-case logs; provide an honest non-WebMCP fallback if unavailable.',['persona/assisted-support'],[],6)
]);
add('p12','From evidence to a reviewable rules prototype',[3],['rules','policy','assurance'],['p04','p05','p06','p07','p09'],'Separate evidence, propositions, reviewed rules and executable tests; block incomplete or unreviewed rules from award decisions.','Deliver a non-operational rule specification, traceability and counterexample tests with explicit promotion blockers.',[
lesson('Challenge definitive-bundle assumptions','Explain why a captured guide is not a complete executable legal specification.','Inventory temporal, statutory, exception and source gaps before defining a rule.',['persona/rules-architect']),
lesson('Choose one bounded rule family','State a small scope and exclude unsupported regimes.','Propose a Pension Credit input-validation or evidence-routing rule, not a full award calculator.',['staff-domain/calculation']),
lesson('Extract a proposition','Retain conditions, negation, exceptions and source context.','Write one candidate proposition and link it to exact source passages.',['term/dmg-evidence-assessment']),
lesson('Record the interpretation','Distinguish a source proposition from a model-proposed rule.','Produce a reviewer decision record with disagreements and unresolved points.',['persona/policy-law-reviewer']),
lesson('Type inputs and outputs','Represent dates, units and unknowns explicitly.','Create a typed decision table with indeterminate and out-of-scope outputs.',['staff-domain/calculation']),
lesson('Model dates and dependencies','Bind rule variants to effective periods and complete support dependencies.','Show that removing an exception or applicable date blocks evaluation.',['staff-domain/rates']),
lesson('Create synthetic boundary cases','Test neighbouring values and changed material facts.','Submit positive, negative, missing-data, out-of-period and contradictory-evidence cases.',['staff-domain/partner']),
lesson('Compare with independent review','Avoid using the generating model as its own correctness oracle.','Have a designated reviewer check traceability and expected outcomes; keep specialist approval pending where unavailable.',['persona/evidence-assurance-reviewer']),
lesson('Design the promotion gate','Prevent unreviewed rules becoming a public entitlement service.','Specify owner approval, legal validation, provenance, tests, rollback and monitoring before any operational use.',['persona/policy-law-reviewer']),
lesson('Rules-capstone assessment','Demonstrate a transparent non-operational prototype.','Submit the rule pack and a blocked case; no award, real claimant decision or claim of complete legal coverage.',['persona/rules-architect'],[],6)
]);
const design={schema:'okf-dwp-learning-design.v1',status:'proposed-not-user-or-specialist-validated',created:'2026-09-22',locale:'en-GB',title:'DWP demonstration learning programme',source_revisions:{ai_demo:'977193212c23923824b54d4e0766ffcad9d17bf0',okf_dwp:'d45774648f00008ffff744a9c8d37bd154070d1c',explorer:'fff8781907aa46aed40c70a984b502c12dd5e201'},limits:{paths:12,steps_per_path:24},persona_basis:'All eight persona routes exist in the inspected combined corpus. They are projected, not user-validated; ai-demo itself names no personas. Service-builder participation is mapped to knowledge-engineer and rules-architect.',runtime_boundary:'Every learning/* route is proposed. Existing evidence routes are verified, but lesson records and assessment enforcement are not published.',paths};
const ownership={p02:[1,23],p03:[2,4,25,32],p04:[6,10,15,16,19,20,21],p05:[7,8,9],p06:[12,13,14,17,18],p07:[3,5,11,22,24,26,27,28,29,30,31,33,34,35,36,37],p08:[38,39,40]};
const coverage=registry.cases.map(c=>({case_id:c.id,question_sha256:crypto.createHash('sha256').update(c.question).digest('hex'),primary_path:Object.keys(ownership).find(p=>ownership[p].includes(Number(c.id.slice(-3)))),lesson_ids:paths.flatMap(p=>p.steps.filter(s=>s.question_ids.includes(c.id)).map(s=>s.id)),duplicate_of:c.duplicate_of,candidate_routes:c.candidate_ids.map(id=>candidate.get(id).route)}));
const questions=fs.readFileSync(demo+'/demo-1-overview.md','utf8').split('## Sample Questions')[1].split('\n').filter(x=>x.startsWith('- ')).map(x=>x.slice(2).trim());
const missing=[...new Set(paths.flatMap(p=>[...p.persona_routes,...p.steps.flatMap(s=>s.evidence_routes)]))].filter(r=>!routes.has(r));
if(missing.length) throw new Error('Missing evidence routes: '+missing.join(', '));
if(questions.length!==40 || questions.some((q,i)=>q!==registry.cases[i].question))throw new Error('Demo question mismatch');
if(paths.length>12||paths.some(p=>p.steps.length>24)||coverage.some(c=>!c.primary_path||!c.lesson_ids.length))throw new Error('Coverage or limit failure');
const allIds=new Set(paths.map(p=>p.id));for(const p of paths){if(new Set(p.steps.map(s=>s.route)).size!==p.steps.length)throw new Error('Duplicate step route');for(const req of p.prerequisites)if(!allIds.has(req))throw new Error('Unknown prerequisite');}
const visit=(id,seen=[])=>{if(seen.includes(id))throw new Error('Prerequisite cycle');paths.find(p=>p.id===id).prerequisites.forEach(x=>visit(x,[...seen,id]));};paths.forEach(p=>visit(p.id));
const projection={schema:'okf-large-learning-presentation.v1',title:design.title,introduction:'Choose a role and learning objective. Completion ticks record activity, not assessed competence. This is a draft curriculum awaiting lesson publication.',paths:paths.map(p=>({id:p.id,title:p.title,description:p.objective,steps:p.steps.map(({route,title,outcome,practice,minutes})=>({route,title,outcome,practice,minutes}))}))};
for(const [name,data] of Object.entries({'learning-design.json':design,'question-coverage.json':coverage,'reader-presentation.DRAFT.json':projection}))fs.writeFileSync(path.join(here,name),JSON.stringify(data,null,2)+'\n');
const manifests=['evaluation/staff-questions/cases.json','domain-profile/staff-needs/journeys.json','combined/okf-explorer.json','combined/data/manifest.json'].map(p=>({repository:'okf-dwp',path:p,sha256:crypto.createHash('sha256').update(fs.readFileSync(dwp+'/'+p)).digest('hex')}));for(const p of ['README.md','demo-1-overview.md','demo-2-overview.md'])manifests.push({repository:'ai-demo',path:p,sha256:crypto.createHash('sha256').update(fs.readFileSync(demo+'/'+p)).digest('hex')});fs.writeFileSync(path.join(here,'source-manifest.json'),JSON.stringify({revisions:design.source_revisions,files:manifests},null,2)+'\n');
const lines=['# DWP learning paths: detailed lesson plan','','Design only. Lesson routes are proposed; evidence routes are verified against the local combined corpus. Durations are planning estimates, not observed timings. Each outcome is assessed using the rubric in DESIGN.md.'];
for(const p of paths){lines.push('',`## ${p.id.toUpperCase()} — ${p.title}`,'',`**Objective:** ${p.objective}`,'',`**Personas:** ${p.persona_routes.map(x=>x.split('/')[1]).join(', ')}. **Prerequisites:** ${p.prerequisites.join(', ')||'None'}. **Estimated time:** ${p.steps.reduce((a,s)=>a+s.minutes,0)} minutes. **Steps:** ${p.steps.length}.`,'',`**Assessment:** ${p.assessment}`,'');for(const [i,s] of p.steps.entries())lines.push(`### ${i+1}. ${s.title} (${s.minutes} minutes)`,'',`- Outcome: ${s.outcome}`,`- Practice and submitted evidence: ${s.practice}`,`- Case references: ${s.question_ids.join(', ')||'Cross-cutting demonstration activity'}.`,`- Existing source anchors: ${s.evidence_routes.map(r=>'`'+r+'`').join(', ')}.`,`- Proposed lesson record: \`${s.route}\`.`, '');}
fs.writeFileSync(path.join(here,'LESSONS.md'),lines.join('\n')+'\n');
const validation={schema:'okf-dwp-learning-design-check.v1',status:'passed-design-integrity-only',paths:paths.length,steps:paths.reduce((a,p)=>a+p.steps.length,0),max_steps:Math.max(...paths.map(p=>p.steps.length)),step_counts:Object.fromEntries(paths.map(p=>[p.id,p.steps.length])),question_occurrences:40,unique_questions:39,exact_demo_registry_matches:40,covered_question_occurrences:coverage.filter(c=>c.primary_path&&c.lesson_ids.length).length,existing_source_candidate_routes:registry.source_candidates.length,all_source_candidate_routes_present:registry.source_candidates.every(c=>routes.has(c.route)),existing_evidence_and_persona_routes:[...new Set(paths.flatMap(p=>[...p.persona_routes,...p.steps.flatMap(s=>s.evidence_routes)]))].length,missing_evidence_routes:missing,acyclic_prerequisites:true,proposed_lesson_routes:paths.reduce((a,p)=>a+p.steps.length,0),runtime_published:false,assessment_enforcement_implemented:false};fs.writeFileSync(path.join(here,'design-validation.json'),JSON.stringify(validation,null,2)+'\n');console.log(JSON.stringify(validation));

// Validate against the actual pinned Reader parser, not a duplicate schema.
const ts=(await import(path.join(explorer,'apps/okf-explorer/node_modules/typescript/lib/typescript.js'))).default;
const parserSource=fs.readFileSync(path.join(explorer,'apps/okf-explorer/src/lib/viewer/largeLearning.ts'),'utf8');
const parserJs=ts.transpileModule(parserSource,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {largeLearningPresentation}=await import('data:text/javascript;base64,'+Buffer.from(parserJs).toString('base64'));
const parsed=largeLearningPresentation(projection);
if(JSON.stringify(parsed)!==JSON.stringify({title:projection.title,introduction:projection.introduction,paths:projection.paths}))throw new Error('Reader rejects or truncates the projection');
validation.exact_reader_parser='passed-no-truncation';
fs.writeFileSync(path.join(here,'design-validation.json'),JSON.stringify(validation,null,2)+'\n');
