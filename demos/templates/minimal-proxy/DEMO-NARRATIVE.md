# University demo: the run of play

Written for Jay, 9 October 2026. **The objective is a sale of Progress Agentic RAG, not a
tour of a build.** Everything below is ordered by what moves a buyer, and every claim in it
is one the live demo actually performs.

---

## Who is in the room, and what each one buys

A university never buys this with one signature. Four people care, for different reasons,
and the demo reaches all four - which is its real advantage over a point solution.

| Who | What keeps them awake | The moment that lands for them |
|---|---|---|
| **Marketing / digital experience** | The site is a maze. Enquiry volume they cannot deflect. No idea what visitors actually wanted. | The embeddable widget, and the insights surface |
| **Student experience / admissions** | International conversion. Enquiries that never become applications. | The multilingual ask, and the real apply link |
| **CIO / IT** | Risk, cost, another platform to run | The honest decline, the citations, and "how this works" |
| **A faculty head** | Their own knowledge is unfindable and the people who know it are retiring | The veterinary portal |

**You do not have to sell all four.** You have to find the one who is nodding and let the
others watch.

---

## The run, in order. About twelve minutes.

### 1. Open on their own homepage, not on our product

Load `your-app.fly.dev`. Say nothing about Progress Agentic RAG yet.

> "This is your homepage. The only thing we have changed is that you can ask it something."

**Why this order:** the moment you name a platform, they start evaluating a vendor. While
it looks like their site, they are evaluating their own website - and finding it wanting.

### 2. Ask something a prospective student actually asks

It is a conversation, not a search box - ask a follow-up and it remembers. Click a
suggested question or type one. **The pages it searched appear in about a second, with
their real photographs**, while the answer writes itself behind them. You will not be
looking at a spinner.

> "Those are the pages it searched, live, on your site. Now watch what it does with them."

When the answer lands, **point at the citation numbers**:

> "Every one of those is a link to your page. It is not telling them what it knows about
> universities. It is telling them what University says."

**This is the first close.** A university's deepest objection to AI is that it will say
something the university did not say. You have just answered it before they raised it.

Then look below the answer at **Where to next**. Those buttons are not decoration: they
are derived from what the answer itself named, in the order it named them, and every one
of them goes to University's own live page. If the answer names nothing, there are no
buttons - it never invents a next step.

> "It answered the question, and it also moved them one click closer to applying.
> Your analytics will see that."

**This is the conversion argument**, and it is what separates this from a search box.

### 3. THE MOMENT. Ask in Arabic.

Switch the language. Ask the same question.

Then stop talking for a second and let them read it.

> "Your website is in English. Your corpus is in English. Nobody translated anything. A
> student in Dubai asks in Arabic and gets your answer, citing your pages."

**This is the single most valuable fifteen seconds in the demo.** Nobody expects it, it is
visibly real, and University has campuses in **Dubai and Singapore** and students from **90
countries** - which came from their own corpus, not from a brochure.

If one person in the room leans forward, it will be here. Follow them.

### 4. Ask it something it cannot answer

Ask about something off-corpus. It will decline honestly and offer a contact route.

> "That matters more than the right answers. It did not invent a plausible one. If it
> cannot ground it in your content, it says so."

**This is the CIO's close.** Everything they have read about AI in the last two years is
about systems that make things up with confidence.

### 5. "How this works"

Open the reveal. **This is the only place the product gets named**, and that is deliberate.

> "This is the whole architecture. Your browser, our proxy, Progress Agentic RAG against
> your content, the answer with its sources. No model was trained on your data. Nothing
> was copied anywhere you would not expect."

### 6. The second business unit: the veterinary portal

Walk across to the faculty portal.

> "Same platform, different problem, different audience. The School of Veterinary Studies
> has decades of protocols, case material and teaching notes. Findable only by the people
> who already know it exists - and they are the ones retiring."

**You can type freely on this surface now.** Earlier it was safe only with the suggested
questions: the corpus was ten documents averaging 374 words, topically adjacent to the obvious
questions and never containing the answers, and the portal was declining before it generated
anything. It is now 34 documents and 27,918 words, and the floor that was tuned for a
thousand-document corpus has been set for this one. Thirty of thirty sampled questions now clear
it, and off-corpus questions still decline cleanly.

**Say the synthetic line before anyone asks**, pointing at the banner:

> "This content is invented, and it says so. Give us yours and this is a week's work, not
> a project."

**Why this beat earns its place:** it turns one department's budget into a platform
decision. The first surface is a marketing purchase. Together they are an institutional one.

### 7. The builder's kit

Open `/embed`. Two boxes, same engine, visibly different: different accent colour,
different languages offered, different placeholder - **and one of them is scoped to a
single section of the site, so the same question returns different sources in each.**

> "Two lines of HTML. Your brand, your languages, your scope. Your web team owns this,
> not us, and nothing about your knowledge box is exposed to the browser."

That last part is literally true and worth saying: there is no key, no token and no
endpoint name in anything the page downloads.

**This is the digital experience owner's close**, and it is the difference between a
project and a capability.

### 7b. If someone owns the website, show them the graph

Open `/wander`. Do not tour it - use it to answer one question: how does a visitor find
anything on a site this big without already knowing the words?

> "Your menu is a filing cabinet. From a typical page it reaches about five per cent of
> your site in two steps. These threads reach about seventy-four."

Those figures are computed live from the crawl, not typed into a slide. Then show the
honest half, because it is the better argument:

> "Fifty-eight of these pages share no thread at all - about one in five. That is because
> the vocabulary is ours, invented in an afternoon. Yours would close that gap."

**This is the content-investment close.** A university pays to write hundreds of pages
and its own navigation strands them - **21 pages here have one lateral neighbour or none,
and the threads reach all of them.** High school leavers sits four levels deep with a
single menu neighbour and a hundred and twenty-seven thread neighbours.

### 8. The insights surface

> "Your analytics tell you which pages were visited. This tells you what people were trying
> to find out, in their own words, in their own language - and where your content did not
> answer them. Every one of those is a page somebody should write."

**The declines are the product.** A content team has never had this list before.

**Say who asked them, before anyone works it out.** Most rows carry a `team` tag, and the
page says so and counts them separately:

> "We drove most of these ourselves, and the page labels every one of them, because we
> are not going to show you invented traffic. What you are looking at is the SHAPE. On
> your own site these are your visitors' questions, in their own words, and nobody has
> ever handed your content team that list."

The page also states plainly what it stores and what it does not - no address, no device,
no cookie, nothing that reaches a person. **That paragraph is for the CIO**, and most
analytics tools never say it.

**Your own questions appear here, and that is a feature.** Anything you ask on the site
during the demo lands as a `direct` row - the log cannot identify who asked, and the page
says so. Use it:

> "The question I asked you five minutes ago is in this list. That is the view filling
> from real asks, live, in front of you."

There is no honest way to tag a person typing in a browser - it would mean putting a key
in the page - so the log tells the truth about what it does and does not know.

---

## The close

Do not close on features. Close on their content.

> "Everything you have seen ran on your own public pages, crawled once, with nothing
> tuned for this meeting. Give us a corpus you actually care about - the international
> student journey, one faculty's research, the policy library - and we will stand it up on
> your content and you can judge it on your own material."

**That is the ARAG motion**: get into an evaluation on the buyer's own content and let
measured quality decide. It has won here before.

**The ask is a corpus, not a contract.**

---

## Lines you need if they come up

**"How do we know it is accurate?"**
> "You do not take our word for it, and we do not quote you an accuracy percentage -
> anyone who does is selling you a number from somebody else's data. Every answer cites
> your pages. Click one. The honest way to judge it is to run it on your own content,
> which is what I am proposing."

**"What about our data?"**
> "Three deployment modes: software as a service, private cloud, and hybrid where only
> inference and the index run in Progress's cloud. In hybrid the index rests there. What
> Progress has told us is what runs in their cloud - **not where your source documents are
> stored**, and I am not going to promise you something I have not been told. I will get
> that in writing for you. The modes were confirmed in October 2026 and are not published
> on any page yet, so get them in writing before you design against them."

**That answer sells better than a confident one.** A procurement team that catches a vendor
over-claiming on residency never trusts anything else they said.

**"Is this just ChatGPT on our website?"**
> "No. It only answers from your content, it cites every claim back to your page, and it
> refuses when your content does not cover it. Watch." Then ask it the off-corpus question
> again.

**"How long to get this live?"**
> "This took an afternoon on your public site. Your own corpus, your branding, your
> governance review - that is the real timeline, and it is weeks rather than a programme.
> Entry is a published subscription, not a seven-figure platform procurement."

**"Who else is doing this?"**
> Do not name other customers. Point at the two surfaces: "A student-facing front door and
> a faculty research portal are the two shapes that recur. You have both."

---

## What NOT to do

**Do not demo the knowledge graph as a FEATURE - use it to answer a question.** Its value
is discovery and navigation, not answer quality, and its own measurement says so: scoping
answers to the graph-walked pages rescued one question in five. But the content-investment
argument it carries is real and measured, so if anyone owns the website, open it and answer
"how would a visitor find anything here without already knowing the words". Read the reach
numbers off the screen rather than quoting them from memory.

**Do not apologise for the wait, and you should no longer need to manage it.** The platform
floor is about four seconds to retrieve and seven to generate, measured, and no model or parameter
change moves it - so the chat now paints the thumbnails, source cards and call-to-action buttons
from retrieval first, in about a second, while the answer text fills in behind them. There is
something real on screen almost immediately. If you ever do find yourself waiting, click early and
let the retrieved pages carry it; never apologise, which makes it the subject.

**Do not open the bare CorpusKit host or click outside the University portal.** Other demo
tenants live on that deployment.

**Arabic phone numbers: FIXED, no longer a caution.** The model used to write the digits
in the wrong order on roughly 7 of 10 Arabic asks. A guard now checks every number in an
answer against the cited sources, retries once, and withholds the whole response rather
than show one it cannot ground. Measured live after it shipped: 3 of 3 correct, none
withheld. Ask freely.

**Do not claim an accuracy figure, quote ARR or pipeline, or name another customer's
deal.** None of it helps and one of them ends the meeting.

**Do not promise that source documents stay with the customer in hybrid.** We have not been
told that. See the residency line above.

---

## What is real, so you never have to hedge

- **343 real pages** crawled from university.edu.au, of which 287 are distinct pages
  (the rest are short links and duplicates, excluded from every figure above)
- **Real photographs on the cards**, taken from University's own pages; where a page has no
  honest image of its own it gets a composed University-branded card, never a grey box
- **Four languages**, every one verified live against that English corpus
- **Every citation** resolves to a real University URL
- **34 veterinary documents, 27,918 words**, every one synthetic and disclosed as synthetic
  on the page that serves it
- **The veterinary corpus is synthetic** and the portal says so on every page
- **No accuracy claim anywhere**, because the knowledge box publishes none
