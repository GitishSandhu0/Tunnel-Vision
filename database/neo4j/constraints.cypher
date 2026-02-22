// =============================================================================
// TUNNEL VISION – Neo4j AuraDB Uniqueness Constraints & Indexes
// =============================================================================
// Run these statements ONCE after provisioning your AuraDB instance.
// All use IF NOT EXISTS so re-running is safe.
//
// Why this matters
// ────────────────
// The Shared Master Node architecture relies on every MERGE looking up nodes
// by their unique key.  Without a uniqueness constraint, Neo4j performs a full
// label scan on MERGE, which is O(n) and causes duplicate nodes under
// concurrent writes.  With a constraint, MERGE is O(log n) via the backing
// B-tree index.
// =============================================================================


// ---------------------------------------------------------------------------
// USER nodes  –  keyed by the Supabase auth UUID
// ---------------------------------------------------------------------------
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;


// ---------------------------------------------------------------------------
// ENTITY nodes  –  global, shared across all users
// (name, type) together form the natural key:
//   ("Python", "TECH")  ≠  ("Python", "PERSON")
// ---------------------------------------------------------------------------
CREATE CONSTRAINT entity_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE (e.name, e.type) IS NODE KEY;


// ---------------------------------------------------------------------------
// CATEGORY nodes  –  broad knowledge domains (unique by name)
// ---------------------------------------------------------------------------
CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;


// ---------------------------------------------------------------------------
// TOPIC nodes  –  master knowledge-graph seed topics (unique by name)
// ---------------------------------------------------------------------------
CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
FOR (t:Topic) REQUIRE t.name IS UNIQUE;


// ---------------------------------------------------------------------------
// GDELT ARTICLE nodes  –  realtime news articles from the GDELT Project
// keyed by canonical URL
// ---------------------------------------------------------------------------
CREATE CONSTRAINT gdelt_article_url_unique IF NOT EXISTS
FOR (a:GDELTArticle) REQUIRE a.url IS UNIQUE;


// ---------------------------------------------------------------------------
// Supporting indexes for fast lookup and traversal
// ---------------------------------------------------------------------------

// Entity lookup by name alone (used in RELATED_TO pathfinding)
CREATE INDEX entity_name_index IF NOT EXISTS
FOR (e:Entity) ON (e.name);

// Entity lookup by type (used for dashboard filters: "show me all ORGs")
CREATE INDEX entity_type_index IF NOT EXISTS
FOR (e:Entity) ON (e.type);

// Category lookup by name
CREATE INDEX category_name_index IF NOT EXISTS
FOR (c:Category) ON (c.name);

// Topic lookup by name
CREATE INDEX topic_name_index IF NOT EXISTS
FOR (t:Topic) ON (t.name);

// GDELTArticle lookup by domain (useful for filtering by news source)
CREATE INDEX gdelt_article_domain_index IF NOT EXISTS
FOR (a:GDELTArticle) ON (a.domain);

// GDELTArticle lookup by seen_date (useful for time-range queries)
CREATE INDEX gdelt_article_seen_date_index IF NOT EXISTS
FOR (a:GDELTArticle) ON (a.seen_date);
