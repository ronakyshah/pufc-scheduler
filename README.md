# pufc-scheduler


Slide 1: Title & Presentation OverviewSlide Title: Automated Referee Assignment EngineSubtitle: Optimized via Multi-Constraint Greedy Selection AlgorithmVisual Layout: Dark slate background, minimal white typography, and an icon representing football/soccer or logic flow.Core Content:Brief description of the automated scheduling problem.Overview of the matching objective: maximize coverage while strictly enforcing experience and age brackets across specific match grades.

Slide 2: Input Data SchemasTo run the greedy assignment algorithm, your presentation needs to define the structure of the data sources.Game Schedule SchemaDate (YYYY-MM-DD)Time (HH:MM AM/PM)Grade (Integer value: 3, 4, 5, 6, 8)Division (Integer value: 1, 2, 3+)Referee Roster SchemaName / Email / Cell NumberYears Refereeing (Float value, e.g., 0.5 for 6 months)Age (Integer value)

TODO:  Implement the following logic as a separate look-up to ensure modularity
Slide 3: Algorithmic Logic & ConstraintsThis slide serves as the operational flowchart for the presentation, breaking down the mandatory constraints into logical rules
  Rule 1 (High-Stakes Centers): Grades 6 & 8 (Divisions 1 & 2) require a Center Referee who is \(\ge 18\) years old OR has \(>2\) years of experience
  Rule 2 (High-Stakes ARs): Assistant Referees (ARs) for Grade 8 (Divisions 1 & 2) must have \(\ge 6\) months (0.5 years) of experience.
  Rule 3 (Junior Development): Grades 3 & 4 Center Referees can be any age, but the algorithm preferentially selects candidates \(\le 18\) years old.
  Rule 4 (Mid-Grade Centers): Grade 5 Center Referees must have \(\ge 6\) months of experience.
  Rule 5 (Open Slots): ARs for Grade 5 (all divisions) and Grades 6 & 8 (Divisions 3+) have no age or experience restrictions.
