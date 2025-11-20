import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from database import create_document, get_documents
from schemas import Lead, Dream, QuizAnswer, Report, User, Subscription

app = FastAPI(title="Revelia.life API", description="Dream interpretation API with tiers and multilingual support")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"name": "Revelia.life", "status": "ok"}

# -------------------- Lead Magnets & SEO helpers --------------------
class LeadIn(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    language: Optional[str] = "es"
    source: Optional[str] = "landing"

@app.post("/api/lead")
def capture_lead(lead: LeadIn):
    lead_doc = Lead(email=lead.email, name=lead.name, language=lead.language, source=lead.source)
    lead_id = create_document("lead", lead_doc)
    return {"ok": True, "id": lead_id}

# -------------------- Dream submission & analysis --------------------
class DreamIn(BaseModel):
    text: str
    language: Optional[str] = "es"
    user_email: Optional[EmailStr] = None

@app.post("/api/dream/analyze")
def analyze_dream(dream: DreamIn):
    # Simple rule-based pseudo-analysis to keep demo self-contained
    text_lower = dream.text.lower()
    tags = []
    if any(k in text_lower for k in ["agua", "water", "água"]):
        tags.append("agua")
    if any(k in text_lower for k in ["caer", "fall", "cair"]):
        tags.append("caida")
    if any(k in text_lower for k in ["volar", "fly", "voar"]):
        tags.append("volar")

    insights = {
        "summary": {
            "es": "Un análisis inicial basado en patrones comunes de sueños.",
            "en": "An initial analysis based on common dream patterns.",
            "pt": "Uma análise inicial baseada em padrões comuns de sonhos."
        },
        "themes": tags,
        "recommendations": {
            "es": ["Lleva un diario de sueños", "Practica higiene del sueño"],
            "en": ["Keep a dream journal", "Practice sleep hygiene"],
            "pt": ["Mantenha um diário de sonhos", "Pratique higiene do sono"]
        }
    }

    dream_doc = Dream(user_email=dream.user_email, text=dream.text, language=dream.language, analysis=insights, tags=tags)
    dream_id = create_document("dream", dream_doc)
    return {"ok": True, "id": dream_id, "analysis": insights}

# -------------------- Pro: Quiz & history --------------------
@app.post("/api/quiz/submit")
def submit_quiz(payload: QuizAnswer):
    quiz_id = create_document("quizanswer", payload)
    return {"ok": True, "id": quiz_id}

@app.get("/api/dream/history")
def dream_history(email: EmailStr):
    docs = get_documents("dream", {"user_email": email})
    # Convert ObjectId to string-safe values
    for d in docs:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return {"ok": True, "items": docs}

# -------------------- Premium: audio intake --------------------
@app.post("/api/dream/audio")
async def analyze_dream_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form("es"),
    user_email: Optional[EmailStr] = Form(None)
):
    # For demo: we do not actually transcribe; we store the filename and create a placeholder analysis
    filename = file.filename
    insights = {
        "summary": {
            "es": "Análisis a partir de audio (placeholder)",
            "en": "Analysis from audio (placeholder)",
            "pt": "Análise a partir de áudio (placeholder)"
        },
        "themes": ["audio"],
    }
    dream_doc = Dream(user_email=user_email, text="[audio input]", language=language, analysis=insights, audio_filename=filename, tags=["audio"])
    dream_id = create_document("dream", dream_doc)
    return {"ok": True, "id": dream_id, "analysis": insights}

# -------------------- Reports via email (stub) --------------------
class ReportIn(BaseModel):
    user_email: EmailStr
    dream_id: Optional[str] = None
    language: Optional[str] = "es"

@app.post("/api/report/send")
def send_report(payload: ReportIn):
    # In a full app, integrate an email provider. Here we persist the report content for traceability.
    localized_subject = {
        "es": "Informe detallado de tu sueño",
        "en": "Detailed dream report",
        "pt": "Relatório detalhado do seu sonho"
    }.get(payload.language or "es", "Informe")

    content = {
        "es": "Gracias por confiar en Revelia.life. Adjuntamos un análisis más profundo de tu sueño.",
        "en": "Thanks for trusting Revelia.life. We attach a deeper analysis of your dream.",
        "pt": "Obrigado por confiar na Revelia.life. Anexamos uma análise mais profunda do seu sonho."
    }.get(payload.language or "es")

    report_doc = Report(user_email=payload.user_email, dream_id=payload.dream_id, subject=localized_subject, content=content, language=payload.language or "es", delivered=False)
    report_id = create_document("report", report_doc)
    return {"ok": True, "id": report_id, "queued": True}

# -------------------- Utility: SEO-friendly sitemap and robots --------------------
@app.get("/robots.txt")
def robots():
    txt = """User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"""
    return JSONResponse(content=txt, media_type="text/plain")

@app.get("/sitemap.xml")
def sitemap():
    base = os.getenv("FRONTEND_URL", "https://example.com")
    xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
  <url><loc>{base}/</loc></url>
  <url><loc>{base}/pricing</loc></url>
  <url><loc>{base}/analyze</loc></url>
  <url><loc>{base}/about</loc></url>
</urlset>"""
    return JSONResponse(content=xml, media_type="application/xml")

# Keep existing test endpoint for DB diagnostics
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
