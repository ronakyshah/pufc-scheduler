# pufc-scheduler


Automated Referee Assignment Engine: Optimized via Multi-Constraint Greedy Selection Algorithm

This code attempts to assign referees to games for the week based on their age.  Additional constraints like avaialbility need to be incorporated.

Input Data Schemas

exampleSchedule.csv and referee_input.csv provide the starting points for generating assignments

TODO:  

(1) Test Google spreadsheet lookup that integrates with Google workspace documentation for club's referee listing.  This is where we plan to centralize and secure referee information for week-to-week planning

(2) Build and test API connectivity to AdminSports

(3) Implement the following logic as a separate look-up to ensure modularity

  Rule 1 (High-Stakes Centers): Grades 6 & 8 (Divisions 1 & 2) require a Center Referee who is >18 years old OR has >=2 years of experience
  
  Rule 2 (High-Stakes ARs): Assistant Referees (ARs) for Grade 8 (Divisions 1 & 2) must have >6 months (0.5 years) of experience.
  
  Rule 3 (Junior Development): Grades 3 & 4 Center Referees can be any age, but the algorithm preferentially selects candidates >=18  years old.
  
  Rule 4 (Mid-Grade Centers): Grade 5 Center Referees must have >6 months of experience.
  
  Rule 5 (Open Slots): ARs for Grade 5 (all divisions) and Grades 6 & 8 (Divisions 3+) have no age or experience restrictions.
  
  Rule 6: Referee availability as outlined in referee_input.csv columns for Start and End Times
