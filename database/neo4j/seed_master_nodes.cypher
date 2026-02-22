// =============================================================================
// TUNNEL VISION – Master Knowledge Graph Seed Data
// =============================================================================
// Populates the "vast universe" of human knowledge that user interest bubbles
// float within.  These nodes exist independently of any user; they are the
// backbone that enables cross-user pathfinding and serendipitous discovery.
//
// Structure
// ─────────
//   (:Topic {name, description, domain})
//   (:Topic)-[:RELATED_TO {strength}]->(:Topic)
//   (:Category {name})-[:CONTAINS]->(:Topic)
//
// Run once after applying constraints.cypher.
// All statements use MERGE so re-running is safe.
// =============================================================================

// ---------------------------------------------------------------------------
// SCIENCE & NATURE
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Science"});
MERGE (:Topic {name: "Physics",        domain: "Science", description: "Study of matter, energy, and the fundamental forces of nature"});
MERGE (:Topic {name: "Chemistry",      domain: "Science", description: "Study of substances, their properties, and reactions"});
MERGE (:Topic {name: "Biology",        domain: "Science", description: "Study of living organisms and life processes"});
MERGE (:Topic {name: "Astronomy",      domain: "Science", description: "Study of celestial objects and the universe"});
MERGE (:Topic {name: "Geology",        domain: "Science", description: "Study of Earth's physical structure and history"});
MERGE (:Topic {name: "Neuroscience",   domain: "Science", description: "Scientific study of the nervous system"});
MERGE (:Topic {name: "Ecology",        domain: "Science", description: "Study of organisms and their environment"});
MERGE (:Topic {name: "Genetics",       domain: "Science", description: "Study of genes, heredity, and variation"});
MERGE (:Topic {name: "Climate Science",domain: "Science", description: "Study of long-term patterns in weather and climate"});

// Science relationships
MATCH (a:Topic {name: "Physics"}), (b:Topic {name: "Chemistry"})        MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Chemistry"}), (b:Topic {name: "Biology"})         MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Biology"}), (b:Topic {name: "Genetics"})          MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Biology"}), (b:Topic {name: "Ecology"})           MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Biology"}), (b:Topic {name: "Neuroscience"})      MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Astronomy"}), (b:Topic {name: "Physics"})         MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Ecology"}), (b:Topic {name: "Climate Science"})   MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Geology"}), (b:Topic {name: "Climate Science"})   MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);

// Category links
MATCH (cat:Category {name: "Science"}), (t:Topic {domain: "Science"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// TECHNOLOGY & COMPUTING
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Technology"});
MERGE (:Topic {name: "Machine Learning",      domain: "Technology", description: "Algorithms that improve through experience"});
MERGE (:Topic {name: "Artificial Intelligence",domain: "Technology", description: "Simulation of human intelligence in machines"});
MERGE (:Topic {name: "Web Development",       domain: "Technology", description: "Building applications for the web"});
MERGE (:Topic {name: "Cybersecurity",         domain: "Technology", description: "Protection of computer systems and networks"});
MERGE (:Topic {name: "Cloud Computing",       domain: "Technology", description: "Delivery of computing services over the internet"});
MERGE (:Topic {name: "Blockchain",            domain: "Technology", description: "Distributed ledger technology"});
MERGE (:Topic {name: "Robotics",              domain: "Technology", description: "Design and operation of robots"});
MERGE (:Topic {name: "Data Science",          domain: "Technology", description: "Extraction of insights from data"});
MERGE (:Topic {name: "Open Source Software",  domain: "Technology", description: "Software with publicly available source code"});
MERGE (:Topic {name: "Quantum Computing",     domain: "Technology", description: "Computing using quantum mechanical phenomena"});

MATCH (a:Topic {name: "Artificial Intelligence"}), (b:Topic {name: "Machine Learning"})       MERGE (a)-[:RELATED_TO {strength: 0.95}]->(b);
MATCH (a:Topic {name: "Machine Learning"}),        (b:Topic {name: "Data Science"})           MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Data Science"}),            (b:Topic {name: "Statistics"})<-[:CONTAINS]-(:Category {name: "Mathematics"}) MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Cloud Computing"}),         (b:Topic {name: "Web Development"})        MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Cybersecurity"}),           (b:Topic {name: "Blockchain"})             MERGE (a)-[:RELATED_TO {strength: 0.6}]->(b);
MATCH (a:Topic {name: "Quantum Computing"}),       (b:Topic {name: "Physics"})                MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Robotics"}),                (b:Topic {name: "Artificial Intelligence"}) MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Machine Learning"}),        (b:Topic {name: "Neuroscience"})           MERGE (a)-[:RELATED_TO {strength: 0.6}]->(b);
MATCH (a:Topic {name: "Open Source Software"}),    (b:Topic {name: "Web Development"})        MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);

MATCH (cat:Category {name: "Technology"}), (t:Topic {domain: "Technology"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// MATHEMATICS
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Mathematics"});
MERGE (:Topic {name: "Statistics",      domain: "Mathematics", description: "Collection, analysis, and interpretation of data"});
MERGE (:Topic {name: "Calculus",        domain: "Mathematics", description: "Mathematics of continuous change"});
MERGE (:Topic {name: "Linear Algebra",  domain: "Mathematics", description: "Study of vectors, matrices, and linear maps"});
MERGE (:Topic {name: "Graph Theory",    domain: "Mathematics", description: "Study of graphs as mathematical structures"});
MERGE (:Topic {name: "Cryptography",    domain: "Mathematics", description: "Techniques for secure communication"});

MATCH (a:Topic {name: "Statistics"}),    (b:Topic {name: "Machine Learning"})  MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Linear Algebra"}),(b:Topic {name: "Machine Learning"})  MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Calculus"}),      (b:Topic {name: "Physics"})           MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Graph Theory"}),  (b:Topic {name: "Data Science"})      MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Cryptography"}),  (b:Topic {name: "Cybersecurity"})     MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Cryptography"}),  (b:Topic {name: "Blockchain"})        MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);

MATCH (cat:Category {name: "Mathematics"}), (t:Topic {domain: "Mathematics"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// ARTS & CULTURE
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Arts & Culture"});
MERGE (:Topic {name: "Visual Art",      domain: "Arts & Culture", description: "Creative works perceived visually"});
MERGE (:Topic {name: "Music",           domain: "Arts & Culture", description: "Art form using sound organized over time"});
MERGE (:Topic {name: "Film & Cinema",   domain: "Arts & Culture", description: "Art and industry of motion pictures"});
MERGE (:Topic {name: "Literature",      domain: "Arts & Culture", description: "Written works considered to have artistic value"});
MERGE (:Topic {name: "Architecture",    domain: "Arts & Culture", description: "Art and science of designing buildings"});
MERGE (:Topic {name: "Photography",     domain: "Arts & Culture", description: "Art of capturing images using light"});
MERGE (:Topic {name: "Theatre & Drama", domain: "Arts & Culture", description: "Performing art using live performance"});
MERGE (:Topic {name: "Dance",           domain: "Arts & Culture", description: "Art form using movement of the body"});
MERGE (:Topic {name: "Design",          domain: "Arts & Culture", description: "Creative process of planning and making"});

MATCH (a:Topic {name: "Music"}),        (b:Topic {name: "Theatre & Drama"})  MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Film & Cinema"}),(b:Topic {name: "Music"})            MERGE (a)-[:RELATED_TO {strength: 0.75}]->(b);
MATCH (a:Topic {name: "Film & Cinema"}),(b:Topic {name: "Literature"})       MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Photography"}),  (b:Topic {name: "Visual Art"})       MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Architecture"}), (b:Topic {name: "Design"})           MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Design"}),       (b:Topic {name: "Visual Art"})       MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Dance"}),        (b:Topic {name: "Music"})            MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);

MATCH (cat:Category {name: "Arts & Culture"}), (t:Topic {domain: "Arts & Culture"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// HISTORY & SOCIETY
// ---------------------------------------------------------------------------
MERGE (:Category {name: "History & Society"});
MERGE (:Topic {name: "Ancient History",       domain: "History & Society", description: "Study of civilisations before the Middle Ages"});
MERGE (:Topic {name: "Modern History",        domain: "History & Society", description: "History from the 15th century to the present"});
MERGE (:Topic {name: "Political Science",     domain: "History & Society", description: "Study of political systems and behaviour"});
MERGE (:Topic {name: "Sociology",             domain: "History & Society", description: "Study of human social behaviour and society"});
MERGE (:Topic {name: "Anthropology",          domain: "History & Society", description: "Study of human societies and cultures"});
MERGE (:Topic {name: "Geography",             domain: "History & Society", description: "Study of places and relationships between people and environments"});

MATCH (a:Topic {name: "Ancient History"}),   (b:Topic {name: "Anthropology"})    MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Modern History"}),    (b:Topic {name: "Political Science"}) MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Sociology"}),         (b:Topic {name: "Anthropology"})     MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Political Science"}), (b:Topic {name: "Sociology"})        MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Geography"}),         (b:Topic {name: "Ecology"})          MERGE (a)-[:RELATED_TO {strength: 0.65}]->(b);
MATCH (a:Topic {name: "Geography"}),         (b:Topic {name: "Anthropology"})     MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);

MATCH (cat:Category {name: "History & Society"}), (t:Topic {domain: "History & Society"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// BUSINESS & ECONOMICS
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Business & Economics"});
MERGE (:Topic {name: "Economics",           domain: "Business & Economics", description: "Study of production, consumption, and transfer of wealth"});
MERGE (:Topic {name: "Entrepreneurship",    domain: "Business & Economics", description: "Process of creating and running a new business"});
MERGE (:Topic {name: "Finance",             domain: "Business & Economics", description: "Management of money and investments"});
MERGE (:Topic {name: "Marketing",           domain: "Business & Economics", description: "Activities for promoting and selling products"});
MERGE (:Topic {name: "Investing",           domain: "Business & Economics", description: "Allocating money with the expectation of profit"});
MERGE (:Topic {name: "Cryptocurrency",      domain: "Business & Economics", description: "Digital or virtual currencies using cryptography"});

MATCH (a:Topic {name: "Economics"}),       (b:Topic {name: "Finance"})          MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Finance"}),         (b:Topic {name: "Investing"})        MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Cryptocurrency"}),  (b:Topic {name: "Blockchain"})       MERGE (a)-[:RELATED_TO {strength: 0.95}]->(b);
MATCH (a:Topic {name: "Cryptocurrency"}),  (b:Topic {name: "Investing"})        MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Entrepreneurship"}),(b:Topic {name: "Marketing"})        MERGE (a)-[:RELATED_TO {strength: 0.75}]->(b);
MATCH (a:Topic {name: "Marketing"}),       (b:Topic {name: "Data Science"})     MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);

MATCH (cat:Category {name: "Business & Economics"}), (t:Topic {domain: "Business & Economics"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// HEALTH & WELLNESS
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Health & Wellness"});
MERGE (:Topic {name: "Nutrition",        domain: "Health & Wellness", description: "Study of food and its effect on health"});
MERGE (:Topic {name: "Mental Health",    domain: "Health & Wellness", description: "Emotional, psychological, and social well-being"});
MERGE (:Topic {name: "Fitness",          domain: "Health & Wellness", description: "Physical activity and exercise for health"});
MERGE (:Topic {name: "Medicine",         domain: "Health & Wellness", description: "Science and practice of diagnosing and treating disease"});
MERGE (:Topic {name: "Psychology",       domain: "Health & Wellness", description: "Scientific study of the human mind and behaviour"});

MATCH (a:Topic {name: "Nutrition"}),    (b:Topic {name: "Biology"})      MERGE (a)-[:RELATED_TO {strength: 0.75}]->(b);
MATCH (a:Topic {name: "Fitness"}),      (b:Topic {name: "Nutrition"})    MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);
MATCH (a:Topic {name: "Mental Health"}),(b:Topic {name: "Psychology"})   MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Psychology"}),   (b:Topic {name: "Neuroscience"}) MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Medicine"}),     (b:Topic {name: "Biology"})      MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Medicine"}),     (b:Topic {name: "Chemistry"})    MERGE (a)-[:RELATED_TO {strength: 0.8}]->(b);

MATCH (cat:Category {name: "Health & Wellness"}), (t:Topic {domain: "Health & Wellness"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// PHILOSOPHY & ETHICS
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Philosophy & Ethics"});
MERGE (:Topic {name: "Philosophy",    domain: "Philosophy & Ethics", description: "Study of fundamental questions about existence, knowledge, and ethics"});
MERGE (:Topic {name: "Ethics",        domain: "Philosophy & Ethics", description: "Branch of philosophy dealing with moral principles"});
MERGE (:Topic {name: "Logic",         domain: "Philosophy & Ethics", description: "Study of correct reasoning"});
MERGE (:Topic {name: "Religion",      domain: "Philosophy & Ethics", description: "Belief systems and spiritual practices"});

MATCH (a:Topic {name: "Ethics"}),     (b:Topic {name: "Philosophy"})        MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Logic"}),      (b:Topic {name: "Philosophy"})        MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Logic"}),      (b:Topic {name: "Mathematics"})       MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Ethics"}),     (b:Topic {name: "Artificial Intelligence"}) MERGE (a)-[:RELATED_TO {strength: 0.75}]->(b);
MATCH (a:Topic {name: "Religion"}),   (b:Topic {name: "Anthropology"})      MERGE (a)-[:RELATED_TO {strength: 0.75}]->(b);
MATCH (a:Topic {name: "Philosophy"}), (b:Topic {name: "Psychology"})        MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);

MATCH (cat:Category {name: "Philosophy & Ethics"}), (t:Topic {domain: "Philosophy & Ethics"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// SPORTS & GAMES
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Sports & Games"});
MERGE (:Topic {name: "Football",      domain: "Sports & Games", description: "Team sport played with a ball on a field"});
MERGE (:Topic {name: "Basketball",    domain: "Sports & Games", description: "Team sport played in a court with a hoop"});
MERGE (:Topic {name: "Esports",       domain: "Sports & Games", description: "Competitive video gaming"});
MERGE (:Topic {name: "Chess",         domain: "Sports & Games", description: "Two-player strategy board game"});
MERGE (:Topic {name: "Video Games",   domain: "Sports & Games", description: "Electronic games for entertainment"});

MATCH (a:Topic {name: "Esports"}),    (b:Topic {name: "Video Games"})         MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Chess"}),      (b:Topic {name: "Artificial Intelligence"}) MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Video Games"}),(b:Topic {name: "Film & Cinema"})        MERGE (a)-[:RELATED_TO {strength: 0.65}]->(b);
MATCH (a:Topic {name: "Football"}),   (b:Topic {name: "Data Science"})         MERGE (a)-[:RELATED_TO {strength: 0.6}]->(b);
MATCH (a:Topic {name: "Basketball"}), (b:Topic {name: "Data Science"})         MERGE (a)-[:RELATED_TO {strength: 0.6}]->(b);

MATCH (cat:Category {name: "Sports & Games"}), (t:Topic {domain: "Sports & Games"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// ENVIRONMENT & SUSTAINABILITY
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Environment & Sustainability"});
MERGE (:Topic {name: "Renewable Energy",   domain: "Environment & Sustainability", description: "Energy from naturally replenished sources"});
MERGE (:Topic {name: "Conservation",       domain: "Environment & Sustainability", description: "Protection of natural resources and environments"});
MERGE (:Topic {name: "Sustainability",     domain: "Environment & Sustainability", description: "Meeting present needs without compromising future generations"});

MATCH (a:Topic {name: "Renewable Energy"}),(b:Topic {name: "Climate Science"})  MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Conservation"}),    (b:Topic {name: "Ecology"})           MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Sustainability"}),  (b:Topic {name: "Economics"})         MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Sustainability"}),  (b:Topic {name: "Climate Science"})   MERGE (a)-[:RELATED_TO {strength: 0.85}]->(b);
MATCH (a:Topic {name: "Renewable Energy"}),(b:Topic {name: "Physics"})            MERGE (a)-[:RELATED_TO {strength: 0.75}]->(b);

MATCH (cat:Category {name: "Environment & Sustainability"}), (t:Topic {domain: "Environment & Sustainability"}) MERGE (cat)-[:CONTAINS]->(t);


// ---------------------------------------------------------------------------
// LANGUAGE & COMMUNICATION
// ---------------------------------------------------------------------------
MERGE (:Category {name: "Language & Communication"});
MERGE (:Topic {name: "Linguistics",        domain: "Language & Communication", description: "Scientific study of language and its structure"});
MERGE (:Topic {name: "Journalism",         domain: "Language & Communication", description: "Gathering and reporting of news"});
MERGE (:Topic {name: "Creative Writing",   domain: "Language & Communication", description: "Writing that expresses imagination or invention"});
MERGE (:Topic {name: "Public Speaking",    domain: "Language & Communication", description: "Art of effective verbal communication to an audience"});

MATCH (a:Topic {name: "Linguistics"}),    (b:Topic {name: "Anthropology"})    MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Linguistics"}),    (b:Topic {name: "Artificial Intelligence"}) MERGE (a)-[:RELATED_TO {strength: 0.65}]->(b);
MATCH (a:Topic {name: "Creative Writing"}),(b:Topic {name: "Literature"})     MERGE (a)-[:RELATED_TO {strength: 0.9}]->(b);
MATCH (a:Topic {name: "Journalism"}),     (b:Topic {name: "Political Science"}) MERGE (a)-[:RELATED_TO {strength: 0.7}]->(b);
MATCH (a:Topic {name: "Public Speaking"}),(b:Topic {name: "Psychology"})      MERGE (a)-[:RELATED_TO {strength: 0.65}]->(b);

MATCH (cat:Category {name: "Language & Communication"}), (t:Topic {domain: "Language & Communication"}) MERGE (cat)-[:CONTAINS]->(t);
