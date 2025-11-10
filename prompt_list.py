entity_2_description_tail_single = """Knowledge graph consist of triplets (subject entity, relation, object entity). There is an entity 'ENTITY'  that satisfies (sth. or sb., {{TAIL_RELATION}}, ENTITY) and (ENTITY, {{HEAD_RELATION}}, sth. or sb.). Please infer its type with a short description. Fill in the format below and don't give the explanation:
{"type": "the type of the entity", "description": "the short description of the entity"}"""

entity_2_description_head_single = """Knowledge graph consist of triplets (subject entity, relation, object entity). There is an entity 'ENTITY' that satisfies (sth. or sb., {{TAIL_RELATION}}, ENTITY) and (ENTITY, {{HEAD_RELATION}}, sth. or sb.). Please infer its type with a short description. Fill in the format below and don't give the explanation:
{"type": "the type of the entity", "description": "the short description of the entity"}"""

entity_2_description = """There is an entity named 'ENTITY', it satisfies several knowledge triplets, please provide its type with a short description.
Here is an example:
Several knowledge triplets: 
The 'ENTITY' works as the object: sth. or sb. ->  City/Town -> 'ENTITY'
The 'ENTITY' works as the subject: 'ENTITY' -> Newspapers -> sth., sb. or specific value; 'ENTITY' -> Time zone(s) -> sth., sb. or specific value; 'ENTITY' -> Area -> sth., sb. or specific value; 'ENTITY' -> Contained by -> sth., sb. or specific value; 'ENTITY' -> Population -> sth., sb. or specific value
The output is: {"type": "geographic location", "description": "a geographic location or administrative area that is associated with specific characteristics, such as a mailing address city, newspaper circulation areas, time zones, and population statistics."}

Several knowledge triplets: 
The 'ENTITY' works as the object: {{OBJECT_TRIPLETS}}
The 'ENTITY' works as the subject: {{SUBJECT_TRIPLETS}}
Now you need to directly output its type with a short description. Fill in the format below without other information or notes:
{"type": "the type of the entity", "description": "the short description of the entity"}
The output is: """

entity_2_description_light = """Please provide the type with a short description of the 'ENTITY' based on the context. 
Here is an example:
Context: sth. or sb. ->  City/Town -> 'ENTITY'
'ENTITY' -> Newspapers -> sth., sb. or specific value; 'ENTITY' -> Time zone(s) -> sth., sb. or specific value; 'ENTITY' -> Area -> sth., sb. or specific value; 'ENTITY' -> Contained by -> sth., sb. or specific value; 'ENTITY' -> Population -> sth., sb. or specific value
The output is: {"type": "geographic location", "description": "a geographic location or administrative area that is associated with specific characteristics, such as a newspaper circulation areas, time zones, and population statistics."}

Context: {{OBJECT_TRIPLETS}}
{{SUBJECT_TRIPLETS}}
Now you need to directly output its type with a short description. Fill in the format below without other information or notes:
{"type": "the type of the entity", "description": "the short description of the entity"}
The output is: """

entity_2_description_light_light = """Please provide the type with a short description of the 'ENTITY' based on the context. 
Here is an example:
Context: 
'ENTITY' is the object of verbs: City/Town
'ENTITY' is the subject of verbs: Newspapers; Time zone(s); Area; Contained by; Population
The output is: {"type": "geographic location", "description": "a geographic location or administrative area that is associated with specific characteristics, such as a newspaper circulation areas, time zones, and population statistics."}

Context: 
'ENTITY' is the object of verbs: {{OBJECT_TRIPLETS}}
'ENTITY' is the subject of verbs: {{SUBJECT_TRIPLETS}}
Now you need to directly output its type with a short description. Fill in the format below without other information or notes:
{"type": "the type of the entity", "description": "the short description of the entity"}
The output is: """

# prompt for relation prune, for stage 2, step 1
extract_relation_prompt = """Please retrieve %s relations (separated by semicolon) that contribute to the question and rate their contribution on a scale from 0 to 1 (the sum of the scores of %s relations is 1).
Q: Name the president of the country whose main spoken language was Brahui in 1980?
Topic Entity: Brahui Language
Relations: language.human_language.main_country; language.human_language.language_family; language.human_language.iso_639_3_code; base.rosetta.languoid.parent; language.human_language.writing_system; base.rosetta.languoid.languoid_class; language.human_language.countries_spoken_in; kg.object_profile.prominent_type; base.rosetta.languoid.document; base.ontologies.ontology_instance.equivalent_instances; base.rosetta.languoid.local_name; language.human_language.region
A: 1. {language.human_language.main_country (Score: 0.4)}: This relation is highly relevant as it directly relates to the country whose president is being asked for, and the main country where Brahui language is spoken in 1980.
2. {language.human_language.countries_spoken_in (Score: 0.3)}: This relation is also relevant as it provides information on the countries where Brahui language is spoken, which could help narrow down the search for the president.
3. {base.rosetta.languoid.parent (Score: 0.2)}: This relation is less relevant but still provides some context on the language family to which Brahui belongs, which could be useful in understanding the linguistic and cultural background of the country in question.

Q: """

extract_relation_prompt_light = """Please retrieve %s relations that contribute to the question from the following relations (separated by semicolons).
Q: Name the president of the country whose main spoken language was Brahui in 1980?
Topic Entity: Brahui Language
Relations: language.human_language.main_country; language.human_language.language_family; language.human_language.iso_639_3_code; base.rosetta.languoid.parent; language.human_language.writing_system; base.rosetta.languoid.languoid_class; language.human_language.countries_spoken_in; kg.object_profile.prominent_type; base.rosetta.languoid.document; base.ontologies.ontology_instance.equivalent_instances; base.rosetta.languoid.local_name; language.human_language.region
The output is: 
['language.human_language.main_country','language.human_language.countries_spoken_in','base.rosetta.languoid.parent']

Q: """

# prompt for judge
# Notice that the triplets do not need to explicitly provide the answer, as users can replace the entity IDs within them with their corresponding formal names. For example, "Peter, father, m.0000 (person)" could support to answer the question "What is the name of peter's father".
judge_prompt = """Given a question and the associated retrieved knowledge graph triplets (subject entity, relation, object entity), you are asked to answer whether it’s sufficient for you to answer the question with these triplets (Yes or No). If you believe the information is sufficient to make an educated guess or infer the answer, please answer 'Yes'. If the information is completely unrelated or does not provide any clue, then answer 'No'. Please note that while other entities are represented as IDs and its type (e.g., 'Taylor Swift' could be represented by 'm.0011 (person)'), you should assume you are familiar with their formal names.
Q: Find the person who said "Taste cannot be controlled by law", what did this person die from?
Knowledge Triplets: Taste cannot be controlled by law., media_common.quotation.author, m.0wfjf99 (person)
A: {No}. The retrieved knowledge graph triplet provides a quotation and identifies the author as a person (m.0wfjf99), but it does not provide any information about the cause of death of that person. To answer the question about what the person died from, additional information regarding the individual's death is required, which is not present in the provided triplet. Therefore, the triplet is insufficient to answer the question.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: The Long Winter, book.written_work.author, m.0bvl_7 (person)
m.0bvl_7 (person), people.person.places_lived|people.place_lived.location, m.0wfjc51 (place)
A: {Yes}. The retrieved knowledge graph triplets include information about the author of "The Long Winter" (m.0bvl_7) and the location associated with her, which allows us to answer the question about where the artist lived. Therefore, the triplets are sufficient to answer the question.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: Steve Bisciotti, sports.professional_sports_team.owner_s, m.0wfhxx3 (sports team)
Steve Bisciotti, sports.sports_team_owner.teams_owned, m.0wfhxx3 (sports team)
Steve Bisciotti, organization.organization_founder.organizations_founded, m.0ct38sr (company)
A: {No}. The retrieved knowledge graph triplets identify the team owned by Steve Bisciotti but do not provide any information about the coach of that team. To answer the question about who the coach is, additional information regarding the coaching staff of the team is required, which is not present in the provided triplets. Therefore, the triplets are insufficient to answer the question.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: Rift Valley Province, location.administrative_division.country, m.0ct38sr (country)
m.0ct38sr (country), location.country.currency_used, m.0wfhxs4 (currency)
A: {Yes}. The retrieved knowledge graph triplets provide information about Rift Valley Province's association with a country (m.0ct38sr) and further detail that this country uses a specific currency (m.0wfhxs4). This allows us to answer the question about the form of currency used in the nation where Rift Valley Province is located. Therefore, the triplets are sufficient to answer the question.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: National Anthem of Bolivia, government.national_anthem_of_a_country.anthem|government.national_anthem_of_a_country.country, m.0whmwxl (country)
National Anthem of Bolivia, music.composition.composer, m.0wfjmw6 (person)
National Anthem of Bolivia, music.composition.lyricist, m.0j7l4rw (person)
m.0whmwxl (country), location.country.national_anthem, UnName_Entity
A: {No}. The retrieved knowledge graph triplets identify the country associated with the National Anthem of Bolivia but do not provide any information about the nations that border that country. Therefore, additional information regarding the borders of the identified country is required, which is not present in the provided triplets. Thus, the triplets are insufficient to answer the question.

Q: """

judge_prompt_light = """Given a question and the associated retrieved knowledge graph triplets (subject entity, relation, object entity), you are asked to answer whether it’s sufficient for you to answer the question with these triplets (Yes or No). Note that while several entities are represented as MIDs and corresponding type (e.g., 'Taylor Swift' could be represented by 'm.0011 (person)'), you should assume the formal names are known.
Q: Find the person who said "Taste cannot be controlled by law", what did this person die from?
Knowledge Triplets: Taste cannot be controlled by law., media_common.quotation.author, m.0wfjf99 (person)
A: {No}. The retrieved knowledge graph triplet provides a quotation and identifies the author as a person (m.0wfjf99), but it does not provide any information about the cause of death of that person. To answer the question about what the person died from, additional information regarding the individual's death is required, which is not present in the provided triplet. Therefore, the triplet is insufficient to answer the question.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: The Long Winter, book.written_work.author, m.0bvl_7 (person)
m.0bvl_7 (person), people.person.places_lived|people.place_lived.location, m.0wfjc51 (place)
A: {Yes}. The retrieved knowledge graph triplets include information about the author of "The Long Winter" (m.0bvl_7) and the location associated with her, which allows us to answer the question about where the artist lived. Therefore, the triplets are sufficient to answer the question.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: Steve Bisciotti, sports.professional_sports_team.owner_s, m.0wfhxx3 (sports team)
Steve Bisciotti, sports.sports_team_owner.teams_owned, m.0wfhxx3 (sports team)
Steve Bisciotti, organization.organization_founder.organizations_founded, m.0ct38sr (company)
A: {No}. The retrieved knowledge graph triplets identify the team owned by Steve Bisciotti but do not provide any information about the coach of that team. To answer the question about who the coach is, additional information regarding the coaching staff of the team is required, which is not present in the provided triplets. Therefore, the triplets are insufficient to answer the question.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: Rift Valley Province, location.administrative_division.country, m.0ct38sr (country)
m.0ct38sr (country), location.country.currency_used, m.0wfhxs4 (currency)
A: {Yes}. The retrieved knowledge graph triplets provide information about Rift Valley Province's association with a country (m.0ct38sr) and further detail that this country uses a specific currency (m.0wfhxs4). This allows us to answer the question about the form of currency used in the nation where Rift Valley Province is located. Therefore, the triplets are sufficient to answer the question.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: National Anthem of Bolivia, government.national_anthem_of_a_country.anthem|government.national_anthem_of_a_country.country, m.0whmwxl (country)
National Anthem of Bolivia, music.composition.composer, m.0wfjmw6 (person)
National Anthem of Bolivia, music.composition.lyricist, m.0j7l4rw (person)
m.0whmwxl (country), location.country.national_anthem, UnName_Entity
A: {No}. The retrieved knowledge graph triplets identify the country associated with the National Anthem of Bolivia but do not provide any information about the nations that border that country. Therefore, additional information regarding the borders of the identified country is required, which is not present in the provided triplets. Thus, the triplets are insufficient to answer the question.

Q: """

# prompt for rag generator
generator_prompt = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets. Please note that while other entities are represented as IDs (e.g., 'm.0011'), you should assume you are familiar with their formal names.
Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: The Long Winter, book.written_work.author, m.0bvl_7 (person)
m.0bvl_7 (person), people.person.places_lived|people.place_lived.location, m.0wfjc51 (place)
A: {m.0wfjc51 (place)}. The artist nominated for The Long Winter, m.0bvl_7 (person), lived in a location that is represented by the entity m.0wfjc51.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: Rift Valley Province, location.administrative_division.country, m.0ct38sr (country)
m.0ct38sr (country), location.country.currency_used, m.0wfhxs4 (currency)
A: {m.0wfhxs4 (currency)}. Rift Valley Province is located in a country represented by the entity m.0ct38sr, which uses the currency represented by the entity m.0wfhxs4.

Q: """

# prompt for CoT Generator
generate_directly = """Q: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
A: First, the education institution has a sports team named George Washington Colonials men's basketball in is George Washington University , Second, George Washington University is in Washington D.C. The answer is {Washington, D.C.}.

Q: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
A: First, Bharoto Bhagyo Bidhata wrote Jana Gana Mana. Second, Bharoto Bhagyo Bidhata lists Pramatha Chaudhuri as an influence. The answer is {Bharoto Bhagyo Bidhata}.

Q: Who was the artist nominated for an award for You Drive Me Crazy?
A: First, the artist nominated for an award for You Drive Me Crazy is Britney Spears. The answer is {Jason Allen Alexander}.

Q: What person born in Siegen influenced the work of Vincent Van Gogh?
A: First, Peter Paul Rubens, Claude Monet and etc. influenced the work of Vincent Van Gogh. Second, Peter Paul Rubens born in Siegen. The answer is {Peter Paul Rubens}.

Q: What is the country close to Russia where Mikheil Saakashvii holds a government position?
A: First, China, Norway, Finland, Estonia and Georgia is close to Russia. Second, Mikheil Saakashvii holds a government position at Georgia. The answer is {Georgia}.

Q: What drug did the actor who portrayed the character Urethane Wheels Guy overdosed on?
A: First, Mitchell Lee Hedberg portrayed character Urethane Wheels Guy. Second, Mitchell Lee Hedberg overdose Heroin. The answer is {Heroin}."""


question_abstractly = """Please answer the questions step by step, the format of the reasoning process should be kept consistent with examples.
Question: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
Thought: First, the education institution has a sports team named George Washington Colonials men's basketball in is George Washington University. Second, George Washington University is in Washington D.C.. The answer is Washington, D.C..
Reasoning Path: {George Washington University (education institution) -> represented in sports by -> George Washington Colonials men's basketball (sport team)}; {George Washington University (education institution) -> located in -> Washington D.C. (state)}
Answer: Washington D.C. (state)

Question: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
Thought: First, the song Jana Gana Mana was written by Bharoto Bhagyo Bidhata. Second, Bharoto Bhagyo Bidhata listed Pramatha Chaudhuri as an influence. The answer is Pramatha Chaudhuri.
Reasoning Path: {Bharoto Bhagyo Bidhata (person) -> wrote -> Jana Gana Mana (song)}; {Bharoto Bhagyo Bidhata (person) -> listed as influence -> Pramatha Chaudhuri (person)}
Answer: Bharoto Bhagyo Bidhata (person)

Question: from francestown, what is the closest ski area?
Thought: First, I need to identify the nearest ski area to Francestown. The closest ski area to Francestown is Crotched Mountain Ski & Ride. The answer is Crotched Mountain Ski & Ride.
Reasoning Path: {Francestown (location) -> closest ski area -> Crotched Mountain Ski & Ride (ski area)}
Answer: Crotched Mountain Ski & Ride (ski area)"""