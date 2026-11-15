"""API response shapes. The single source of field names for server/ and web/.

Everything the product generates carries a Provenance. `kind` is the load-bearing field:
"extracted" means read deterministically from markup or structure that already exists on the
page (no model involved); "suggested" means a language model proposed it from page prose and
it is a suggestion until a human approves it. They are never the same kind of thing.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Kind = Literal["extracted", "suggested", "derived"]   # derived: built by the application from the page's structure (for example a breadcrumb trail), not read from markup and not proposed by a model
Band = Literal["high", "medium", "low"]


class Provenance(BaseModel):
    source_url: str
    resource_id: Optional[str] = None          # the platform resource this page was ingested as
    kind: Kind
    method: Literal["json-ld", "breadcrumb", "navigation", "model"]
    evidence: Optional[str] = None             # verbatim text from the page that supports the record
    evidence_verified: bool = False            # evidence found verbatim in the ingested page text


class Check(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class Confidence(BaseModel):
    """A review signal, never a guarantee. `band` is the headline; passed/total is the evidence
    beneath it. A high band means the cheap deterministic checks passed, not that the record is true."""
    band: Band
    passed: int
    total: int
    checks: list[Check] = Field(default_factory=list)


class Issue(BaseModel):
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    path: str = ""


class Validation(BaseModel):
    valid: bool                                  # no error-severity issues
    issues: list[Issue] = Field(default_factory=list)
    vocabulary: str = "Schema.org (official schemaorg-current-https.jsonld, bundled)"


class Cost(BaseModel):
    platform_calls: dict[str, int] = Field(default_factory=dict)   # by call kind
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    pages: int = 0
    tokens_per_page: Optional[float] = None
    model_calls_per_page: Optional[float] = None
    estimated_usd_per_page: Optional[float] = None   # only when the operator supplied a price assumption
    price_assumption: Optional[str] = None
    extrapolation_500_pages: Optional[dict[str, float]] = None
    notes: list[str] = Field(default_factory=list)


class CrawlGap(BaseModel):
    url: str
    reason: Literal["blocked_by_robots", "not_found", "http_error", "fetch_failed", "not_html",
                    "noindex", "excluded_by_pattern", "off_host", "over_page_cap", "link_only", "private_address", "redirected"]
    detail: str = ""
    in_sitemap: bool = False


class Counts(BaseModel):
    discovered: int = 0
    in_sitemap: int = 0
    fetched: int = 0
    ingested: int = 0
    failed: int = 0
    excluded: int = 0
    link_only: int = 0


class SiteStatus(BaseModel):
    id: str
    root_url: str
    state: Literal["queued", "discovering", "crawling", "ingesting", "extracting", "resolving",
                   "suggesting", "ready", "failed"]
    detail: str = ""
    error: Optional[str] = None
    started_at: float
    finished_at: Optional[float] = None
    counts: Counts = Field(default_factory=Counts)
    coverage_percent: Optional[float] = None       # ingested / every page address seen (unchanged meaning)
    permitted_coverage_percent: Optional[float] = None   # ingested / pages we were allowed to take (robots, noindex, patterns, redirects, non-pages and linked pages the user chose not to follow leave the denominator; 404s and unreachable pages stay)
    gaps: list[CrawlGap] = Field(default_factory=list)
    robots: dict[str, Any] = Field(default_factory=dict)
    scope: dict[str, Any] = Field(default_factory=dict)             # {mode, sitemap_urls, follows_links, estimate}: what this crawl will and will not read
    cost: Cost = Field(default_factory=Cost)
    structured_data: dict[str, int] = Field(default_factory=dict)   # complete / partial_or_invalid / none
    entity_counts: dict[str, int] = Field(default_factory=dict)     # by type
    relation_counts: dict[str, int] = Field(default_factory=dict)   # by support: markup / prose / navigation
    conflicts: int = 0
    ambiguities: int = 0
    platform_graph: dict[str, Any] = Field(default_factory=dict)    # read-back of deterministic relations
    changes: Optional[dict[str, Any]] = None                        # populated on a recrawl
    seconds_to_first_insight: Optional[float] = None
    dropped: Optional[dict[str, int]] = None            # model proposals discarded, by reason
    unsupported_dropped: int = 0


class ExistingMarkup(BaseModel):
    raw: str
    parsed: Optional[Any] = None
    validation: Validation


class Suggestion(BaseModel):
    id: str
    page_id: str
    jsonld: Any                                       # the proposed JSON-LD document
    property_provenance: dict[str, Kind] = Field(default_factory=dict)  # "Type.property" -> kind
    evidence: list[Provenance] = Field(default_factory=list)
    validation: Validation
    confidence: Confidence
    status: Literal["pending", "approved", "rejected"] = "pending"
    edited: bool = False
    decided_at: Optional[float] = None
    needs_review: list[str] = Field(default_factory=list)   # reasons a human must look (ambiguity, conflict)
    reviewer_changes: list[dict] = Field(default_factory=list)   # [{key, change}] what the reviewer added, changed or removed against the proposal


class PageSummary(BaseModel):
    id: str
    url: str
    title: Optional[str] = None
    status: Literal["ingested", "failed", "excluded"]
    reason: Optional[str] = None
    http_status: Optional[int] = None
    resource_id: Optional[str] = None
    in_sitemap: bool = False
    structured_data: Literal["complete", "partial_or_invalid", "none"] = "none"
    existing_types: list[str] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    entity_count: int = 0
    suggestion_status: Optional[str] = None
    suggestion_id: Optional[str] = None


class PageDetail(BaseModel):
    page: PageSummary
    source_text: str
    existing: list[ExistingMarkup]
    proposed: Optional[Suggestion] = None
    open_findings: list[dict] = Field(default_factory=list)   # unsettled conflicts and ambiguities that block approval of this page
    entities: list[dict] = Field(default_factory=list)
    relations: list[dict] = Field(default_factory=list)


class Node(BaseModel):
    id: str
    label: str
    type: str
    origin: Literal["extracted", "suggested", "both"]
    pages: list[dict] = Field(default_factory=list)       # [{page_id, url}]
    properties: dict[str, Any] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)
    type_note: str = ""                                       # set when the site's own type was not a Schema.org type and was normalised or could not be
    auto_merged: list[str] = Field(default_factory=list)       # short names merged into this entity by rule (a reviewer can undo with 'keep separate')
    provenance: list[Provenance] = Field(default_factory=list)
    confidence: Confidence
    ambiguous_with: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)


class Edge(BaseModel):
    id: str
    source: str
    target: str
    predicate: str                                   # a Schema.org property, or "relatedTo" when none fits
    label: str = ""                                  # human wording ("roasts", "worksFor"); the verb for relatedTo
    in_schema_org: bool = True                       # false: real relationship the vocabulary cannot express
    origin: Kind
    support: Literal["markup", "navigation", "prose"]
    provenance: Provenance
    corroboration: list[Provenance] = Field(default_factory=list)   # other places the same edge is stated
    confidence: Confidence
    wrapped_in: str = ""                            # "Offer": makesOffer is emitted as an Offer whose itemOffered is the target, which is how Schema.org expects it
    object_in_quote: bool = True                     # false: the sentence does not name the object; it comes from the page (see object_source)
    object_source: str = "quote"                     # where the object came from: quote | page title | page heading | a table on the page | 'our' ... | a short form ... | the preceding sentences


class Conflict(BaseModel):
    id: str
    entity_id: str
    entity_label: str
    property: str
    values: list[dict]                                  # [{value, page_id, url, kind, evidence}]
    note: str = ""
    acknowledged: bool = False           # a reviewer has seen this disagreement and recorded a decision
    reviewer_note: str = ""


class Ambiguity(BaseModel):
    id: str
    entity_ids: list[str]
    labels: list[str]
    reason: str
    status: Literal["needs_review", "kept_separate"] = "needs_review"
    keys: list[str] = Field(default_factory=list)          # normalised names the decision is stored against


class NavLink(BaseModel):
    id: str
    child: dict                  # {name, url}: the page lower in the site's own structure
    parent: dict                 # {name, url}
    method: str                  # breadcrumb | navigation
    found_on: str


class Graph(BaseModel):
    nodes: list[Node]                                  # entities only; pages are not entities
    edges: list[Edge]
    navigation: list[NavLink] = Field(default_factory=list)   # site structure from breadcrumbs and menus, page to page
    conflicts: list[Conflict]
    ambiguities: list[Ambiguity]
    unsupported_dropped: int = 0     # model proposals discarded because their evidence was not on the page
    dropped_edges: list[dict] = Field(default_factory=list)   # prose edges discarded because nothing on the page licenses their object (subject, predicate, object, quote, source)
    dropped_by_guard: dict = Field(default_factory=dict)   # how many drops each guard made: separation, sentence_object, competing_object, object_not_on_page
    edges_object_from_page: int = 0                  # kept in the explorer at the low band: the sentence does not name the object but the page does (never proposed or exported)
    note: str = ""


class AskRequest(BaseModel):
    site_id: str
    question: str


class Citation(BaseModel):
    n: int
    page_id: Optional[str] = None
    url: str
    title: Optional[str] = None
    resource_id: Optional[str] = None
    excerpt: str = ""
    claims: list[str] = Field(default_factory=list)   # the answer sentences this page was checked to support


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
    basis: Optional[str] = None                      # "pages", "site analysis" or both: what the answer stands on
    declined: bool = False
    unsupported_claims: int = 0                      # answer sentences no retrieved page was found to support (no marker placed)
    unsourced_sentences: list[str] = Field(default_factory=list)   # the exact sentences counted in unsupported_claims, so the interface marks those and no others
    non_assertions: int = 0                          # lead-ins and hedges that state no fact: neither supported nor unsupported, not counted in the band
    withheld_claims: int = 0                         # sentences removed because they asserted that two names are one thing without that pair being computed
    attempts: int = 1
    analysis_context: list[str] = Field(default_factory=list)  # application-assembled facts passed to the model, shown openly
    quality: Optional[dict] = None
    cost: dict = Field(default_factory=dict)
    error: Optional[str] = None


class CreateSite(BaseModel):
    url: str
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    max_pages: int = 100
    follow_links: bool = False        # False: read the sitemap's pages (and the typed address). True: also pages reached by links


class ApproveRequest(BaseModel):
    decision: Literal["approve", "reject"] = "approve"
    jsonld: Optional[Any] = None       # human-edited replacement; re-validated before it is accepted
    acknowledge_warnings: bool = False  # the reviewer has read the validation warnings on this record


class AmbiguityDecision(BaseModel):
    decision: Literal["merge", "separate"]


class ConflictAck(BaseModel):
    note: str = ""                    # why the reviewer is content to proceed (for example 'the index is stale; the product page is right')
