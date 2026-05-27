from flask import Flask, request, render_template, jsonify
import os
import json
from datetime import datetime, timezone

app = Flask(__name__)

# -------------------------------------------------------
# loopED starter app
# Jotform -> Render webhook -> rule engine -> HTML output
# -------------------------------------------------------

def parse_jotform_submission(req):
    """
    Jotform webhooks can arrive in slightly different shapes depending on settings.
    This function tries to safely extract the submitted answers.

    For early testing, we keep the parser flexible and inspect the payload.
    """
    if req.is_json:
        payload = req.get_json(silent=True) or {}
    else:
        payload = req.form.to_dict(flat=False)

        # Flatten single-item lists from form encoded data
        payload = {
            key: value[0] if isinstance(value, list) and len(value) == 1 else value
            for key, value in payload.items()
        }

    return payload


def normalize_answers(payload):
    """
    Convert raw Jotform webhook payload into the variables used by the loopED engine.

    IMPORTANT:
    You will need to update these field names after inspecting your first real
    Jotform webhook payload. Jotform field keys often look like:
        q3_patientAge
        q12_restingHeartRate
        rawRequest
    """
    raw_text = json.dumps(payload).lower()

    # Very simple starter extraction.
    # Replace these with actual Jotform field mappings once you inspect payloads.
    answers = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "raw_payload_preview": json.dumps(payload, indent=2)[:3000],

        # Starter defaults
        "active_suicidality": any(term in raw_text for term in [
            "active suicidal", "suicidal intent", "plan to end", "kill myself"
        ]),
        "self_harm_medical_attention": any(term in raw_text for term in [
            "medical attention", "emergency department", "stitches"
        ]),
        "pregnant": "pregnant" in raw_text and "not pregnant" not in raw_text,
        "insulin_use": "insulin" in raw_text,
        "recent_dka": "dka" in raw_text or "diabetic ketoacidosis" in raw_text,
        "purging": any(term in raw_text for term in [
            "vomit", "purging", "laxative", "diuretic"
        ]),
        "severe_restriction": any(term in raw_text for term in [
            "severe restriction", "not eating", "very little"
        ]),
    }

    return answers


def evaluate_looped_engine(answers):
    """
    Minimal placeholder logic for the first working prototype.

    This is intentionally conservative and simple:
    - urgent safety/medical flags force urgent recommendation
    - active ED behaviours suggest clinical follow-up/monitoring
    - otherwise baseline support/psychoeducation

    You can later replace this with your Variables -> Thresholds -> Criteria ->
    Patterns -> Gap Map -> Modifiers -> Risk Lane Override Rules structure.
    """

    urgent_reasons = []
    high_reasons = []
    monitoring_reasons = []
    support_reasons = []

    if answers.get("active_suicidality"):
        urgent_reasons.append("Active suicidality signal was detected.")

    if answers.get("self_harm_medical_attention"):
        urgent_reasons.append("Self-harm requiring medical attention was detected.")

    if answers.get("insulin_use") and answers.get("recent_dka"):
        urgent_reasons.append("Insulin use with recent DKA signal was detected.")

    if answers.get("pregnant") and (
        answers.get("purging") or answers.get("severe_restriction")
    ):
        urgent_reasons.append("Pregnancy with active eating-disorder behaviour was detected.")

    if answers.get("purging"):
        high_reasons.append("Purging or compensatory behaviour signal was detected.")

    if answers.get("severe_restriction"):
        high_reasons.append("Severe restriction signal was detected.")

    if not urgent_reasons and not high_reasons:
        support_reasons.append("No urgent/high-risk signal was detected in this starter logic.")

    if urgent_reasons:
        risk_lane = "URGENT"
        recommendation = (
            "This response includes urgent safety or medical risk signals. "
            "The provider should consider immediate clinical assessment and escalation pathways."
        )
    elif high_reasons:
        risk_lane = "HIGH"
        recommendation = (
            "This response includes elevated clinical risk signals. "
            "The provider should consider timely follow-up, medical monitoring, and escalation if symptoms worsen."
        )
    else:
        risk_lane = "BASELINE / MONITOR"
        recommendation = (
            "This response does not trigger urgent/high-risk starter flags. "
            "Consider psychoeducation, monitoring, and routine follow-up based on clinical judgment."
        )

    return {
        "risk_lane": risk_lane,
        "recommendation": recommendation,
        "urgent_reasons": urgent_reasons,
        "high_reasons": high_reasons,
        "monitoring_reasons": monitoring_reasons,
        "support_reasons": support_reasons,
    }


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "loopED"})


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Jotform should POST submissions here:
        https://YOUR-RENDER-SERVICE.onrender.com/webhook

    GET is allowed only so you can visit the URL in a browser and confirm it exists.
    """
    if request.method == "GET":
        return jsonify({
            "message": "loopED webhook endpoint is live. Jotform should POST submissions here.",
            "endpoint": "/webhook"
        })

    payload = parse_jotform_submission(request)
    answers = normalize_answers(payload)
    result = evaluate_looped_engine(answers)

    # In this starter version, we do NOT save submissions to a database.
    # The result is rendered immediately as an HTML page.
    return render_template(
        "result.html",
        answers=answers,
        result=result
    )


@app.route("/test", methods=["GET"])
def test_result():
    """
    Manual test page without Jotform.
    Visit:
        https://YOUR-RENDER-SERVICE.onrender.com/test
    """
    fake_answers = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "raw_payload_preview": "Manual test payload",
        "active_suicidality": False,
        "self_harm_medical_attention": False,
        "pregnant": False,
        "insulin_use": False,
        "recent_dka": False,
        "purging": True,
        "severe_restriction": False,
    }
    result = evaluate_looped_engine(fake_answers)
    return render_template("result.html", answers=fake_answers, result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
