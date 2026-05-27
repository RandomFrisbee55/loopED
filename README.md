# loopED

Minimal starter project for the loopED clinical-support prototype.

## Flow

Jotform submission → Render webhook → Flask app → loopED starter logic → HTML Loop Card

## Render settings

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Webhook endpoint: `https://YOUR-RENDER-SERVICE.onrender.com/webhook`

## Local run

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://localhost:5000
http://localhost:5000/test
http://localhost:5000/health
```

## Important privacy note

This starter app does not store submissions in a database. It renders the result immediately.
For clinical/PHIPA-sensitive use, avoid sending identifiable PHI until the deployment, hosting,
security, privacy, and institutional approvals are reviewed.
