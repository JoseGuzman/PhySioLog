# PhysioLog – AI Context

This is like the project contract for our collaboration. It defines the architecture, rules, and constraints for building PhysioLog (Flask + Plotly dashboard) while preparing for AWS + Docker deployment.

Architecture:

- Flask app factory
- API: physiolog/routes_api.py
- Web routes: physiolog/routes_web.py
- Business logic: physiolog/services.py
- Frontend: static/js/dashboard.js (Plotly)

Rules:

- Keep routes thin; logic in services.py
- Do not change API contracts unless asked
- Keep JS modular; avoid global side effects

Constraints:

- Must run in Docker with environment variables
- No local file system dependencies
- Must be production-ready (logging, error handling)