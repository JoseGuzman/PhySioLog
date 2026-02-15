# PhysioLog – AI Context

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
