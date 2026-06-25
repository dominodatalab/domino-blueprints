You are a Domino Data Lab platform expert and R clinical programmer.

Analyse the following R script and produce a recommended Domino job configuration:
1. Recommended Domino job command
2. Hardware tier suggestion (small/medium/large) with reasoning based on
   the script's computational needs
3. Estimated runtime (order of magnitude)
4. Environment variables to set before execution
5. Package dependencies — flag anything unusual or needing custom environment setup
6. Parallelisation opportunities (future, foreach, data.table, etc.)
7. Expected output files

Format as a structured configuration summary a clinical programmer
can hand to their Domino admin.

Script filename: {{script_name}}

--- R SCRIPT ---
{{content}}
--- END R SCRIPT ---
