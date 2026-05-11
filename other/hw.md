Hi Philip!

I hope this message finds you well. Below, you'll find my advice on which areas to focus on, as well as the promised homework. I'm omitting specifics on AI/LLM since this field is rapidly evolving; the more you know, the better.

	1	LeetCode - The World's Leading Online Programming Learning Platform (https://leetcode.com/) - The free section of the platform is an excellent resource for exploring the various challenges you may encounter during a coding interview.
	2	Key concepts to grasp before interviews (you can use any chat-based LLM to explain these and suggest reading materials for a deep dive). It's normal to find some of these topics complex at first; true understanding comes with hands-on experience.
	a	APIs (REST/GraphQL fundamentals)Contracts, request/response, HTTP semantics, versioning, backward compatibility.
	b	Databases & Data Modeling (SQL vs NoSQL)
	c	Modeling tradeoffs, normalization vs denormalization, indexing, transactions, constraints.
	d	System Design & Scalability Basics
	e	Components (client/service/DB), bottlenecks, horizontal vs vertical scaling, load balancing.
	f	CI/CD (Continuous Integration & Deployment/Delivery)
	g	Pipelines, automated tests, artifacts, environments, safe releases/rollback strategy.
	h	Version Control & Collaboration (Git workflows)
	i	Branching, PRs, code reviews, merge conflicts, release branching vs trunk-based.
	j	Authentication vs Authorization
	k	Identity vs permissions, sessions vs JWT, RBAC, least privilege, common auth pitfalls.
	l	Cloud & Deployment Fundamentals
	m	VMs vs containers, managed services, regions/zones, configuration, infra as code (conceptually).
	n	Observability (Logs/Metrics/Tracing)
	o	What each is for, debugging production, alerting signals, SLO-ish thinking.
	p	Reliability & Failure Handling
	q	Timeouts, retries, idempotency, rate limiting, graceful degradation, circuit breakers.
	r	Security Fundamentals (practical)
	s	Secrets management, input validation, common vulns (injection/XSS), secure defaults.
	3	Amazon's principles (https://www.amazon.jobs/content/en/our-workplace/leadership-principles) emphasize attitude and culture more than technology, making them essential to understand. Various resources detail Amazon's interviewing techniques, which are increasingly adopted industry wide. While tools like ChatGPT, Gemini, and Perplexity can provide valuable guidance, I recommend reviewing the Amazon Behavioral Interview Questions and Answers (2026 Guide) on Exponent  (https://www.tryexponent.com/blog/how-to-nail-amazons-behavioral-interview-questions)for a comprehensive overview.


-------------------------------------------------------------

Homework:

Objective
Build a tiny web app with one form that captures a shop’s “Request Eggs” submission and saves the data.

You're free to choose any technology and decide whether to deploy it in the cloud or locally. Mainstream cloud providers offer trial credits, so you won't incur any costs. You may seek assistance as needed (AI in any form including coding agents is good too), but ensure you can explain how everything works and justify your decisions.

Your choices may include but not limited to
	•	Tech stack: any (Node, Python, .NET, Go, Rust, C++, etc.).
	•	Persistence: JSONL file, SQLite, or SQL database (Postgres/MySQL/SQL Server).
	•	Deployment: local is perfectly fine; cloud is optional (keep costs near zero).
Form fields
Farm name, contact, phone/email (optional), location (ZIP/city);
Type (Conventional/CageFree/FreeRange/Organic), Size (Medium/Large/XLarge/Jumbo), Grade (AA/A/B), Pack (12ct_carton/18ct_carton/24ct_tray/30dozen_case);
Quantity (value + unit), price per dozen, available start/end (optional), notes.
Endpoints (minimum)
	•	GET / → renders the form
	•	POST /submit → saves one record; respond { id: "<uuid>" } on success
	•	GET /entries → returns all records as JSON
	•	GET /exportcsv → returns CSV of all records *
	•	GET /healthz → returns 200 OK
Validation
Required: farm name, contact, location, type, size, grade, pack, quantity value & unit.
Numeric fields must be numbers (quantity, price per dozen). Show friendly errors.
Deliverables
	•	Repo preferably (or zipped folder) with source and one‑command run (e.g., npm start, python app.py, make run).
	•	README.md with setup, run steps, endpoints, and a small diagram of request → handler → storage.
	•	Export proof (the actual export.csv or a screenshot of /export.csv).
	•	At least one test (simple request or unit test).
Definition of done
Starts locally with one command or deployed to the cloud and available online; form submits and persists data; /entries returns JSON; /export.csv downloads CSV; /healthz returns 200; README + one test present and passing; console logs include method/path/status.
Timeline
Propose a target completion date in your reply. Daily check‑ins aren’t required use the README to document decisions and trade‑offs.
Questions are welcome. Please reply with your chosen stack and target date.

Grading system:

10 points maximum.
	•	The code walkthrough has been conducted. 1 point.
	•	The app runs or can be started in the suggested environment without any code modifications. 1 point. 
	•	The UI is accessible and renders without visible errors. 1 point (bonus point for no errors in the browser console). 
	•	The UI accepts data and validates required fields (bonus point for human-readable errors). 1 point. 
	•	The data provided in the UI is successfully sent to the backend and can be listed from the backend side. 1 point. 
	•	More than one data entry can be created. 1 point. 
	•	The data is listed in the UI as a simple grid. 1 point. 
	•	The data persists even after restarting the application. 1 point.