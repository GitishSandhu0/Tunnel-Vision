// =============================================================================
// TUNNEL VISION – Idempotent Ingestion Pattern (Annotated Example)
// =============================================================================
// This file demonstrates the correct Cypher pattern for all write operations
// in Tunnel Vision.  Every mutation uses MERGE instead of CREATE to ensure
// the operation is safe to run multiple times (idempotent).
//
// Why MERGE instead of CREATE?
// ─────────────────────────────
// CREATE always produces a new node/relationship, even if an identical one
// already exists.  In a multi-user system with background jobs re-processing
// exports, CREATE would cause:
//   • Duplicate Entity nodes for "Python" across different users
//   • Duplicate INTERESTED_IN edges if a user re-uploads their data
//   • Bloated graph that breaks pathfinding (two "Python" nodes never connect)
//
// MERGE performs a lookup first:
//   "If a node/edge matching this pattern exists → return it.
//    If it does NOT exist → create it exactly once."
//
// Combined with ON CREATE SET / ON MATCH SET, MERGE lets us:
//   • Set initialisation properties only on first creation
//   • Update "last seen" timestamps on every subsequent match
//   • Safely accumulate per-user weights without overwriting global nodes
// =============================================================================


// ---------------------------------------------------------------------------
// STEP 1 – Upsert the User node
// ---------------------------------------------------------------------------
// The User node is keyed by the Supabase auth UUID.
// ON MATCH SET updates the timestamp every time we see this user again.
// The uniqueness constraint on User.id (see constraints.cypher) guarantees
// this MERGE is O(log n) regardless of total user count.

MERGE (u:User {id: "example-user-uuid-1234"})
  ON CREATE SET u.created    = datetime(),   // only set on first-ever insert
                u.last_updated = datetime()
  ON MATCH  SET u.last_updated = datetime(); // update every subsequent run


// ---------------------------------------------------------------------------
// STEP 2 – Upsert a global Entity node
// ---------------------------------------------------------------------------
// Entity nodes are SHARED across all users.  The node key is (name, type).
// Two users who both engage with "Python" → one shared :Entity node with
// two incoming INTERESTED_IN edges (one per user).
//
// This is the cornerstone of the Shared Master Node architecture: shared
// nodes enable cross-user RELATED_TO paths, which power the Recommendations
// feature.

MERGE (e:Entity {name: "Python", type: "TECH"})
  ON CREATE SET e.created   = datetime(),
                e.last_seen = datetime()
  ON MATCH  SET e.last_seen = datetime();


// ---------------------------------------------------------------------------
// STEP 3 – Upsert the personal INTERESTED_IN relationship
// ---------------------------------------------------------------------------
// MERGE on a relationship also looks up the *combination* of:
//   (start node pattern) + [relationship type + properties] + (end node pattern)
//
// Because each user has their own weight/mentions, the relationship is
// personalised while the Entity node remains global.
//
// Re-processing the same user's export simply updates weight and mentions
// in place; it never creates a second INTERESTED_IN edge.

MATCH (u:User   {id:   "example-user-uuid-1234"})
MATCH (e:Entity {name: "Python", type: "TECH"})
MERGE (u)-[r:INTERESTED_IN]->(e)
  ON CREATE SET r.weight   = 0.95,          // initial weight from AI extraction
                r.mentions = 42,            // raw mention count
                r.created  = datetime(),
                r.updated  = datetime()
  ON MATCH  SET r.weight   = 0.95,          // overwrite with latest extraction
                r.mentions = 42,
                r.updated  = datetime();


// ---------------------------------------------------------------------------
// STEP 4 – Upsert a global Category node
// ---------------------------------------------------------------------------
// Category nodes are also shared.  "Technology" is one node no matter how
// many users explore it.  The uniqueness constraint on Category.name ensures
// MERGE is fast.

MERGE (c:Category {name: "Technology"})
  ON CREATE SET c.created = datetime();


// ---------------------------------------------------------------------------
// STEP 5 – Upsert the personal EXPLORES relationship (User → Category)
// ---------------------------------------------------------------------------

MATCH (u:User     {id:   "example-user-uuid-1234"})
MATCH (c:Category {name: "Technology"})
MERGE (u)-[r:EXPLORES]->(c)
  ON CREATE SET r.weight  = 0.9,
                r.created = datetime(),
                r.updated = datetime()
  ON MATCH  SET r.weight  = 0.9,
                r.updated = datetime();


// ---------------------------------------------------------------------------
// STEP 6 – Upsert the Entity → Category classification edge
// ---------------------------------------------------------------------------
// This edge is also global (not per-user).  It tells the graph that the
// "Python" entity belongs to the "Technology" category.
// Running this for every user who knows Python creates only one BELONGS_TO
// edge because MERGE de-duplicates it.

MATCH (e:Entity   {name: "Python",     type: "TECH"})
MATCH (c:Category {name: "Technology"})
MERGE (e)-[:BELONGS_TO]->(c);


// ---------------------------------------------------------------------------
// STEP 7 – Upsert cross-entity RELATED_TO edges (master knowledge graph)
// ---------------------------------------------------------------------------
// RELATED_TO edges link entities in the global master graph.  They are
// seeded by the seed_master_nodes.cypher script but can also be added
// dynamically when the AI extraction finds co-occurring entities in a batch.
//
// strength is a 0–1 float representing the conceptual proximity of the two topics.

MATCH (a:Topic {name: "Machine Learning"})
MATCH (b:Topic {name: "Statistics"})
MERGE (a)-[r:RELATED_TO]->(b)
  ON CREATE SET r.strength = 0.9,
                r.created  = datetime()
  ON MATCH  SET r.strength = 0.9,       // idempotently refresh strength
                r.updated  = datetime();


// ---------------------------------------------------------------------------
// VERIFICATION QUERY (read-only – run after ingestion to inspect results)
// ---------------------------------------------------------------------------
// Un-comment and run this in the Neo4j Browser to verify the above writes:
//
// MATCH (u:User {id: "example-user-uuid-1234"})
// OPTIONAL MATCH (u)-[ri:INTERESTED_IN]->(e:Entity)
// OPTIONAL MATCH (u)-[re:EXPLORES]->(c:Category)
// OPTIONAL MATCH (e)-[:BELONGS_TO]->(c2:Category)
// RETURN u, ri, e, re, c, c2
// LIMIT 50
