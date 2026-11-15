# Film brief: the Progress Agentic RAG sales enablement portal, end to end

Prepared 26 October 2026 for a video producer. Everything below is read off the live build (commit 4b6965d, deployed 25 October 2026 16:11Z) and its page registry. Treat it as the spec; confirm each frame against the live host on the day of capture.

## 1. The one-line brief

A walkthrough film of the whole portal, for Progress sellers and SEs who have never opened it: how to prepare for a meeting in minutes, then how to present every one of the nineteen live use cases on a working system, with the words to say over each one. The viewer should finish knowing what to type, what to click, what will appear, and what to say when it does.

- Host: https://your-app.fly.dev
- Audience: Progress sellers, SEs and sales leaders. Internal. Forwardable inside Progress.
- Film type: demo film (real product footage, produced around it). Not a concept film.
- Runtime: 12 to 15 minutes as one film with chapter markers, plus a 90-second cut of chapters 1, 2 and 3 for a team channel.
- Delivery: 1920x1080 at 30, AAC stereo 48k, about -14 LUFS, music-free, no captions, Progress-themed stage and cards, one narrator throughout.

## 2. What the portal is, in the words the film should use

Two layers, and the film keeps the seam visible:

- **Prepare, on the Progress side.** A seller types a few sentences about the room they are walking into. The portal searches reference write-ups of kinds of business, generates one structured answer, runs its own checks, and returns three use cases to show, in order, each with the reason quoted from the seller's own words, an opening line, an objection with its response, discovery questions, and a Word copy. Where nothing fits, it declines and says so. The wait narrates what the platform is doing.
- **Present, on Home-two's side.** Home-two Supply is an invented American industrial distributor in Canton, Ohio, with branches at Youngstown, Akron, Canton, Erie, Mansfield, Wheeling and Toledo. Every Present page runs on its records: stock, orders, customers, suppliers, jobs, documents, product pictures, fourteen synthetic calls. Behind the agent pages sit two tool servers the agent calls over MCP: a simulated ERP standing in for an OpenEdge application behind the Progress OpenEdge MCP Server, and a simulated warehouse system. The ERP's data and service are invented; the MCP calls are real.

The sentence to say about the ERP, exactly: "a simulated ERP standing in for an OpenEdge application behind the Progress OpenEdge MCP Server, which exposes an OpenEdge application's business logic and data to AI workflows over MCP; the ERP's data and service here are invented, the MCP calls are real."

What the film must say plainly, once, early: Home-two does not exist, the records are generated from a fixed seed, no real customer is named anywhere, and the mechanism is the product. The portal says this on every Present page in its own banner ("Home-two stands in for your customer...") and the film can let that banner carry it.

## 3. Navigation the producer needs

- Top rail on the Prepare side: Playbook (`/#prepare`), Present Home-two (`/#ask`), How this works.
- Prepare modes: Guided (five steps) and Manual (pick pages yourself). Start over clears the browser-held brief. The brief is sent once and is not logged or stored on the server, and the page says so.
- Present side rail, in the order the page shows it, with the use case behind each label and its direct route:
  - Ask (`/#ask`): the Home-two home. Persona switch, three question chips (documents, records, warehouse), live counters read from the ERP.
  - Ask pages: Watch the lookups it chooses (`/#uc/agentic-retrieval`), One question across every system (`/#uc/ask-records`), Brief me on this customer (`/#uc/account-briefing`), Ask as two roles at once (`/#uc/entitlement-scoped`), A question the records cannot answer (`/#uc/refusal`), See how an answer is measured (`/#uc/answer-quality`).
  - Operations: Supplier scorecard (`/#uc/scorecards`), Relationships (`/#uc/knowledge-graph`).
  - Inbound: Invoice intake (`/#uc/document-intelligence`), Document queue (`/#uc/triage`), Contract vs receival (`/#uc/contradictions`).
  - Trade portal: Order by conversation (`/#uc/conversational-commerce`), Help in your language (`/#uc/multilingual`), Site answers for machines (`/#uc/answer-engine`).
  - Contact center: Call records (`/#uc/media-intelligence`).
  - Content: Claim checks (`/#uc/claim-substantiation`), Content gaps (`/#uc/content-gaps`), Taxonomy (`/#uc/taxonomy`), Content from records (`/#uc/content-from-records`).
- Language switch (English | Español) in the Present rail: generated answers come back in the viewer's language; documents, citations and call audio stay English, and the page says so in Spanish.
- Sign-ins (Switch user, top right of Present): Visitor (not signed in), Tavernell Construction (trade account C-1000), Dana Whitaker (Counter, Youngstown; the default), Priya Raman (Finance). Each page names the sign-in it expects; the film uses the one the page names.
- "How this works" (top right of every Present page): the reveal. The one place the Progress Agentic RAG name and mechanism appear on the Present side. It lists what actually happens, in order, naming the agent, the tool servers and the caller's token.

## 4. Film structure, chapter by chapter, with talk track

Narration is written to be spoken, not read off the screen. Keep on-screen cards under eight words. The narrator never reads a UI label aloud when the picture already shows it. Where a line below is in quotation marks it is the suggested narration; everything else is direction.

### Chapter 0: cold open (0:00 to 0:25)

Picture: the Prepare page with four sentences being typed, hard cut to the shortlist landing with "3 use cases to show, out of 19 in total", hard cut to the agentic retrieval board filling with calls.

"Thursday, ten minutes before the call. You type four sentences about who you are seeing. The portal picks what to show them, and tells you why in your own words. Then you show it, live, on a working system."

Title card: Progress Agentic RAG Sales Enablement. Prepare, then present.

### Chapter 1: what it is (0:25 to 1:15)

Picture: the two rails side by side as framed plates: Playbook on the left, Present Home-two on the right.

"Two halves. On our side, you prepare. On their side, you present. The preparation uses Progress Agentic RAG to decide what to show about Progress Agentic RAG, so the first thing a prospect sees the product do is reason about them. The presenting side is Home-two Supply, an invented distributor with real records behind every page. Nothing here is a mock-up: every answer you will see in this film was produced live during one recording pass, and we will say where it ran."

Card: build 4b6965d, captured <date>. The film names its own capture.

### Chapter 2: Prepare, the five steps (1:15 to 4:30)

Route `/#prepare`, Guided. Clear the browser first (Start over).

Step 1, Who are you seeing. Type the electrical wholesaler brief verbatim (it is invented; keep it word for word so the picks are reproducible in spirit): "We are an electrical wholesaler with eight trade branches across two states, serving contractors and maintenance teams. Trade customers ring the branches all day for stock, prices and lead times, and the counter staff check three systems to answer them. We hold supplier price files, product data sheets and a terms and returns policy in shared folders. I am meeting the general manager of trade sales and the head of branch operations on Thursday."

"Four things make it work: who they are and what they sell, who you are meeting, what they have said, what they use today. Write it the way you would say it. If you are short on time, tap an example."

Step 2, Watch it choose. Hold on the narrated wait for its whole length (eight to twelve seconds live). Punch in on each line as it arrives.

"This wait is the lesson. First, one search over the reference write-ups, keyword and semantic together, and it generates nothing. Then one structured generation on the same knowledge box, pinned to a named model, with the shape of the answer fixed before it writes. Then the checks, which run in this application and not on the platform: every generated field is tested, and a field that fails is held back with a reason, never rewritten. A seller who has read no documentation finishes this step knowing what retrieval, grounding and a withheld claim look like."

Step 3, Your shortlist. Show the heading "3 use cases to show, out of 19 in total, in this order" and "Why this order". Punch in on pick 1, "Why it fits", and the quoted clause.

"Three pages, in order. Each one opens with a clause copied from what you typed, word for word. The portal does not paraphrase you, and where it cannot tie a reason to your words it says so instead of inventing one. Read what each pick says it will not show. That sentence is there so you never oversell the demo."

Step 4, The playbook. Open the collapsed block "For this kind of room, from the reference material": opening question, objections to expect, discovery questions. Then press Download the playbook as Word and show the first page rendered.

"The opening line is spoken to the buyer, not about them. The objections and discovery questions are written for this kind of business and labelled as reference material, not about this deal, so you know what is authored and what is generated. The Word copy follows whatever you edit in Manual mode, and it carries the list of what was held back and why."

Step 5, Present. Show the step with its pick, the "What to say" text, and the Open the page link.

"From here each pick opens its Present page in a new window, signed in as the persona the page names."

The refusal. Start over, type a two-sentence invented boutique winery, press Build. Show the decline.

"When nothing fits, it says so. No kind of business matched, so it will not put a playbook behind it, and it tells you what to add. Every page stays open to show by hand. A seller should see this once so the decline reads as integrity in the room, not as a failure."

### Chapter 3: Present, the agent pages (4:30 to 8:00)

Sign in as Dana Whitaker (Counter, Youngstown) unless stated.

**Agentic retrieval** (`/#uc/agentic-retrieval`). Chip: "What is on order SO-41153 and has any of it shipped?" Expect about 25 seconds. Let the board fill in real time: Agent chooses the calls, MCP tool surface, OpenEdge ERP (simulated), Warehouse (simulated), Documents. Then the per-call lanes with times, then the answer with each code underlined and "4 codes named in the answer, 4 traced to the call that returned them".

"Watch the agent decide. It chose two ERP calls, seven warehouse calls and one document search; nobody scripted that. Every code in the answer is underlined because it was checked against the rows a call returned. If a code had come from nowhere, the answer would say so. That is the spine of this whole demo: an agent working a business system over MCP, under the sign-in's own permissions, showing its working."

**One question across every system** (`/#uc/ask-records`). Chip: "Which trade customers are over their credit limit, and do any of them have open orders?" Show the lookups posting as they happen, then the ledger lines, each tabbed with its record set.

"One plain question, several record sets, one answer laid out as ledger lines. Each line is tabbed with where it came from. A line that names no returned record is counted as the agent's own wording, in the open."

**Brief me on this customer** (`/#uc/account-briefing`). Pick Ashtabula Port Services (C-1098), press Brief me. Five panels fill as calls return, then the briefing with citation chips and the counts: Lines written, Shown, Withheld, Agent's own wording.

"Before a meeting, one customer read from the ERP, the warehouse and the documents at once. Every line in the briefing points at the row or passage behind it, and a line carrying a figure no source states is withheld and counted rather than shown. That withheld count is the number to point at in the room."

**Ask as two roles at once** (`/#uc/entitlement-scoped`). Chip: "What are the payment terms and volume rebate for the supplier of CV-CD125-SS?" Show the grid "Who can read what" first, then both runs (counter and finance) side by side, then "The roles were separated" with the two figures traced to the finance sign-in's own lookups and the padlocks on the counter side.

"Same question, two sign-ins, at the same time. The grid is drawn before anything is asked, so the room knows what each role may read. Finance gets the rebate figures; the counter sign-in gets a padlock where the tool server removed the field. The difference is traced to the lookup, not asserted."

**A question the records cannot answer** (`/#uc/refusal`). Chip: "How many packs of CV-CD125-SS are at Canton, and what is the margin on them?" Show the survey sheet (what these records do not hold), the agent's read rows, and the answer giving the packs and withholding the margin.

"It answers what the records support and stops at the edge. Fifty-seven packs at Canton, and the margin cannot be determined because cost is barred for this sign-in. The records it read are stamped as read, not as an answer."

**See how an answer is measured** (`/#uc/answer-quality`). Chip: "Which disc grade for stainless steel". Show the passages as slips lighting as the score returns, the qualitative badge, and the movable line. Six live asks per session; use one.

"Every answer can be scored for how well the retrieved evidence supports its wording. It is not a check that the answer is right, and the page says so. Move the line and the room sees which passages count as supporting, and whether this answer would be held for a person."

### Chapter 4: Inbound, documents and checking (8:00 to 10:00)

**Invoice intake** (`/#uc/document-intelligence`). Press Read the certificate. The scanned batch certificate is on the left, six of fifteen entries handwritten; fields light green only when the live read finds the value word for word; the shelf life that disagrees with the supplier bulletin (36 versus 24 months) is shown beside it; a person signs off.

"A supplier's certificate, the kind someone retypes by hand. The document is on screen and the read lights each field as it is confirmed, word for word in the document itself. Where a figure disagrees with another document, both are shown. A person signs off; nothing is corrected silently."

**Document queue** (`/#uc/triage`). Show the rack of waiting enquiries, press read on "Disc failed mid-cut", show the lookups, the recommended owner and urgency, and assign.

"Incoming work read against the records on request. It recommends an owner and an urgency; a person clicks to assign, and the trail is kept."

**Contract vs receival** (`/#uc/contradictions`). Chip: "How many days does a customer have to return unused fasteners?" Three documents set out side by side, each with its quote marked, three different figures, and the control pair that agrees.

"Three documents, three answers: thirty, twenty-eight and fourteen days. A knowledge base would hand you whichever ranked first. This reads each document on its own and shows all three, with an agreeing pair as the control so the room can see the comparison is real."

### Chapter 5: Trade portal, other readers (10:00 to 11:45)

**Order by conversation** (`/#uc/conversational-commerce`). Chip: "Which disc should I use on stainless, and how many packs can I get at Youngstown today?" Chat on the left, basket slip on the right; a line appears only when a lookup returned the product; confirm; the order is read back from Orders.

"A buying conversation that ends in an order line. Nothing appears in the basket until a lookup returned it, availability is printed above the button, and after an explicit confirmation the order is written and read back. It is real only inside Home-two: no payment, nothing dispatched."

**Help in your language** (`/#uc/multilingual`). The page opens on a recorded run dated 25 October 2026 and labelled Recorded. Show the Spanish question, the answer in Spanish, and the English source passage with the sentence the answer rests on marked. Optionally run one live chip; do not run the controls (they are the out-of-corpus questions and should decline).

"One set of English documents, answered in the language of the person asking, cited back to the English source. The page tells you retrieval across languages scores lower than in English, and it never prints a retrieval score beside a refusal. Say that before the room asks."

**Site answers for machines** (`/#uc/answer-engine`). Chip: "Which disc grade must be used on stainless steel?" Left: what a person reads, drawn in a browser frame that is not a published page. Right: the same fact as a record with named properties tied to passages; a property with no passage withheld and counted.

"One generated call, two readers. A person reads the answer; a machine reads the record beside it, each property tied to a passage. The tools that now read sites instead of people get the same grounding the person does."

### Chapter 6: Contact center and content desk (11:45 to 13:45)

**Call records** (`/#uc/media-intelligence`). Fourteen invented calls, twelve voiced. Switch the dashboard By call and By passage, open a bar to list the calls it counts, open "Changing a delivery window for chilled stock" (0:48), show the waveform and speaker turns with their labels, then ask one question about that call and show the citation move the player.

"Calls turned into a dashboard, counted from labels at two levels, the whole call and one passage. Open a bar and the calls behind the number are listed. Ask about one call and the answer is cited to a passage, and the player moves to it."

**Claim checks** (`/#uc/claim-substantiation`). Press Check on "All structural bolts are hot-dip galvanized." and on "Every disc in the Corvane range carries a three-year shelf life." Show the verdict land on the sentence and the page it was decided from open beside it. Leave one sentence Not checked on screen.

"Marketing copy checked a sentence at a time against the documents that are supposed to support it. The page the quote was found in opens beside the verdict. An unchecked sentence reads Not checked, never passed."

**Content gaps** (`/#uc/content-gaps`). Show the shelf of documents sized by words, the declined questions, and the sentence saying whose questions these are.

"The questions asked that the content could not answer, beside the documents the searches reached. Read the line at the top: it says whose questions these are. On this demo they are the team's, and the page will not pretend otherwise."

**Taxonomy** (`/#uc/taxonomy`). Press Propose a taxonomy over the pile (44 documents, 13,054 words). Show the concept cards with their passages, rename one, merge two, and show the SKOS file rebuild.

"A working taxonomy proposed from a sample of the content itself. Each concept carries the passages its terms were found in; a term with no passage is withheld and counted. Rename, merge and drop call no model. It is a proposal for a person to review, not a governed taxonomy, and the page says that."

**Content from records** (`/#uc/content-from-records`). Trade bulletin, English, Build draft. Expect about 45 seconds including the sentence checks; show the sources landing on the left, then the draft placed block by block with citations and product pictures and the Draft stamp. Then switch Language to Spanish and build again (about 10 seconds; the Spanish draft is placed after its figures and codes are found in a cited source).

"A trade bulletin assembled from ERP rows, document passages and the product pictures the system holds. Every sentence names where it came from; a figure no source states is withheld and counted; there is no send button. The same piece in Spanish, from the same English sources."

### Chapter 7: Operations desks, quickly (13:45 to 14:30)

**Supplier scorecard** (`/#uc/scorecards`). Sign in as Priya Raman (Finance). Heat matrix of ten suppliers, 92 figures, 8 cells with nothing to count shown hatched; tap a figure to open the rows behind it; point at the blind spot named.

"Ten figures per supplier, every one a query over the records, no model anywhere on this page. An empty population is a hatched cell, never a zero, and the page names what it cannot measure."

**Relationships** (`/#uc/knowledge-graph`). Start at batch K88213, walk one hop to the product and the certificate, walk again, open a document node, and show a padlocked stub for a link this sign-in may not read.

"Walking the links between things one hop at a time. Each hop is one relationship search with its time in the ledger, and every link is a code that appears in a document's own text. A link you may not read is a padlocked stub with a count and no content."

### Chapter 8: How this works, and what is real (14:30 to 15:00)

Open How this works on the agentic retrieval page. Punch in on the numbered steps.

"Every Present page can explain itself. This is the one place the product name and mechanism appear on Home-two's side: your browser asks this application signed in as the role you chose; the application opens a session with the Progress Agentic RAG agent, passing your session token; the agent decides the lookups; each lookup lands on one of this application's tool servers carrying your token, so your role's limits apply as if you had clicked through by hand."

Then a plain card, three lines: Invented: Home-two and everything in it. Real: the agent, its tool calls, the answers, the checks and the counts. Recorded: the Help in your language page opens on a dated run and says so.

Close: "Run it before your next conversation, then tell us where it got the room wrong." URL on screen: your-app.fly.dev. Progress end card on the Progress stage.

## 5. Capture plan and metered budget

- One scripted capture pass, driven by Playwright, against the live host, after an identity gate: GET /healthz must report the build the film names, dirty false. Record the healthz JSON with the capture.
- Record video at 1x (Playwright cannot record at 2x); take punch material from device-scale-2 screenshots captured at the same moments.
- Viewport 1440x900 for plates; 390x844 for nothing (this is a desktop film).
- Budget, hard cap: 2 playbook runs (the wholesaler and the winery) and 30 asks. Expected spend from the chapter list above: agentic 1, ask-records 1, briefing 2, entitlement 2, refusal 1, quality 2, triage 1, document intelligence 1, contradictions 3, commerce 2, multilingual 0 or 1, answer-engine 1, calls 1, claims 2 to 4, taxonomy 1, content English 1 plus up to 6 sentence checks, content Spanish 1, graph 0 (hops are relationship searches, not generations). Count a fan-out as its fan-out. Abort before the cap, record the count, and never re-run a chapter to get a prettier take: re-shoot only a failed step.
- Every answer shown in the film is a real run from this pass. No stored answer is presented as live; the multilingual page's recorded run is labelled on screen by the product itself.
- No team key exists on this app; the product labels all traffic as the team's. Do not drive the content gaps page with throwaway questions to populate it.
- Do not leave a local server running after capture (rule 15d). Capture against the live host only.

## 6. Production standard (binding)

- Produced, not captured: footage sits in a framed device plate on one consistent Progress stage (navy, Progress palette, the lockup from brand/logos, Progress Sans Display for headlines and Text for body). Title card and end card on the Progress stage; the stage check must read Progress ink navy at both ends.
- The image performs the line: when the narrator cites a figure, a code or a withheld count, that element fills the frame at readable size with the spoken phrase emphasised, cropped to the phrase plus bounded padding, every punch magnifying at least 3x. Highlights are drawn over the real capture, never a retyped card.
- Legibility floor applies to text inside the plates, not only authored type: every evidence line, disclosure, badge and count the narration relies on is legible at phone width. Audit by class (claims, qualifications, evidence) and fix the evidence class first.
- Engagement floor: camera moves or cuts counted; frozen frames under about a quarter of runtime; longest silent static stretch under 2.5 seconds; narration gaps under 1.5 seconds except deliberate holds. Live footage does not supply motion; push gently on the plate through the shared motion helper.
- Narration: one ElevenLabs voice throughout, cast by fit for an internal explainer register (default `hope`, US neutral, matching the Present side's US English); never a placeholder voice, never macOS say. Explainer pace, roughly 140 to 160 words a minute. Write pauses into the copy; never an ellipsis on v3 (unbounded pause).
- No music, ever. No captions unless the GM asks. Voice the actual query and answer where they carry the beat (the refusal, the disagreement, the withheld margin).
- A chapter marker at each chapter start, and the 90-second cut composed from chapters 1, 2 and 3 as its own cut, never a crop.

## 7. Fences, checked by script over narration, cards and every frame

- Vocabulary seam: "knowledge box", "Retrieval Agent" and "REMi" may be said over Prepare and inside the How this works reveal, and must not appear over any other Present footage or on any card shown over it. "Progress Agentic RAG" is always spelled out; bare "ARAG" and "Nuclia" never appear in voice, card or frame.
- No deployment-mode claim of any kind, in any form. That position is held. Do not say where the product runs.
- No real company, customer or account name anywhere: narration, cards, frames, filenames. Home-two's customers and suppliers are invented and are the only names that may appear.
- The seller's brief is invented and appears only on the Prepare side. No money figure or meeting detail of the seller's appears in any card.
- Australian English in cards and narration copy (the Present side's own text is US English and is left as captured). No em dashes. No delve, leverage, unlock, seamless, game-changing.
- Every card asserts only what the frame beside it shows. A number on a card is read off the frame, never typed from memory.
- Scan every captured frame for hosting-region strings (aws-, rag.progress.cloud), the vendor name and ARAG_ environment names; the sign-in pill and the product's own banners stay in frame because they are true of the capture.
- Package audit on the delivered file: container metadata carries no author names, no template titles; md5 and duration named in the acceptance; build twice and compare hashes before accepting.

## 8. Known weaknesses to state, not hide

- The value line in a playbook is withheld wherever the seller's notes name no material, which on short briefs is most picks. Say it in Chapter 2.
- One invented distributor sits behind every pick, so a wrong-industry demo can sit behind the right pick (an insurer's room will still see fasteners). Say it in Chapter 8.
- A rebuild of the same brief can return different picks, and answers can differ run to run. The film names its build and capture time for that reason.
- Retrieval across languages scores lower than in English; the multilingual page says so and the film repeats it.
- The content gaps page lists the team's own questions and says so; the film must not imply visitor demand.

## 9. Acceptance

First draft goes to the review queue after ONE internal pass (GM standing instruction, 17 October 2026), with known weaknesses stated in the note. Safety still runs before submission: the leak sweep with planted controls, the no-fake check (every shown answer traced to a line in the capture log), the claim check over narration and cards, the vocabulary seam scan, the stage check, container metadata, and the audio spec. A fresh-eyes viewer with no build context watches the draft and answers two questions separately: did you understand it, and would you keep watching. Submit via the DAM work queue with the md5, duration, build id and capture time in the note, and the chapter list in the description.
