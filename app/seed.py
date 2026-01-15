import uuid
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models
from app.security import hash_api_key
import os
api_key = os.getenv("TENANT_API_KEY", "dev-arbe-key-123")
from app.security import hash_api_key
import os

admin_key = os.getenv("ADMIN_API_KEY", "dev-admin-123")
auditor_key = os.getenv("AUDITOR_API_KEY", "dev-auditor-123")
client_key = os.getenv("CLIENT_API_KEY", "dev-client-123")

# Tenant
t = models.Tenant(
    id="arbe",
    name="ARBE",
    api_key_hash="legacy",  # opcional manter, não usado no RBAC
    status="active"
)
db.merge(t)

def upsert_key(name: str, key_plain: str, role: str):
    kid = str(uuid.uuid4())
    db.add(models.ApiKey(
        id=kid,
        tenant_id="arbe",
        name=name,
        key_hash=hash_api_key(key_plain),
        role=role,
        status="active"
    ))

upsert_key("dashboard-admin", admin_key, "admin")
upsert_key("dashboard-auditor", auditor_key, "auditor")
upsert_key("prod-api-client", client_key, "api-client")

def run_seed():
    db: Session = SessionLocal()
    try:
        tenant_id = "arbe"
        course_id = "ADM-001"

        # TAXONOMY VERSION
        tv_id = str(uuid.uuid4())
        tv = models.TaxonomyVersion(id=tv_id, tenant_id=tenant_id, version="2026.01", status="active")
        db.add(tv)

        # TAXONOMY NODES
        nodes = [
            models.TaxonomyNode(
                id=1101, taxonomy_version_id=tv_id, area="Administração", subarea="Fundamentos",
                conceito="Teorias Administrativas",
                descricao="Principais escolas e teorias da administração (clássica, científica, burocrática, relações humanas).",
                palavras_chave=["taylor", "fayol", "weber", "administração científica", "burocracia", "relações humanas"],
                nivel="basico", critico=False
            ),
            models.TaxonomyNode(
                id=1102, taxonomy_version_id=tv_id, area="Administração", subarea="Gestão",
                conceito="Planejamento Estratégico",
                descricao="Planejamento, missão, visão, objetivos, análise estratégica e ferramentas como SWOT.",
                palavras_chave=["planejamento estratégico", "missão", "visão", "objetivos", "swot", "análise estratégica"],
                nivel="intermediario", critico=True
            ),
            models.TaxonomyNode(
                id=1103, taxonomy_version_id=tv_id, area="Administração", subarea="Gestão",
                conceito="Indicadores e Desempenho",
                descricao="KPIs, métricas, metas, acompanhamento e melhoria contínua.",
                palavras_chave=["kpi", "indicadores", "métricas", "metas", "desempenho", "dashboard"],
                nivel="intermediario", critico=False
            ),
            models.TaxonomyNode(
                id=1201, taxonomy_version_id=tv_id, area="Finanças", subarea="Fundamentos",
                conceito="Matemática Financeira",
                descricao="Juros simples/compostos, valor presente, valor futuro, descontos e séries.",
                palavras_chave=["juros", "compostos", "valor presente", "valor futuro", "taxa", "desconto"],
                nivel="basico", critico=True
            ),
            models.TaxonomyNode(
                id=1202, taxonomy_version_id=tv_id, area="Finanças", subarea="Gestão",
                conceito="Análise de Investimentos",
                descricao="VPL, TIR, payback, análise de viabilidade, risco e retorno.",
                palavras_chave=["vpl", "tir", "payback", "viabilidade", "risco", "retorno"],
                nivel="intermediario", critico=True
            ),
            models.TaxonomyNode(
                id=1301, taxonomy_version_id=tv_id, area="Marketing", subarea="Fundamentos",
                conceito="Composto de Marketing",
                descricao="4Ps/7Ps, segmentação, posicionamento e mix de marketing.",
                palavras_chave=["4ps", "7ps", "segmentação", "posicionamento", "mix de marketing"],
                nivel="basico", critico=False
            ),
            models.TaxonomyNode(
                id=1302, taxonomy_version_id=tv_id, area="Marketing", subarea="Estratégia",
                conceito="Jornada do Cliente e Funil",
                descricao="Atração, consideração, conversão, retenção, funil e jornada.",
                palavras_chave=["funil", "jornada do cliente", "conversão", "retenção", "consideração"],
                nivel="intermediario", critico=False
            ),
        ]
        for n in nodes:
            db.add(n)

        # POLICY VERSION
        pv_id = str(uuid.uuid4())
        policy = {
            "min_score_deferir": 80,
            "min_score_complemento": 65,
            "tolerancia_carga": 1.0,
            "exigir_criticos": True,
            "confidence_cutoff": 0.45,
            "weights": {"cobertura": 0.6, "critica": 0.4, "nivel": 0.1}
        }
        pv = models.PolicyVersion(id=pv_id, tenant_id=tenant_id, version="v3", config=policy)
        db.add(pv)

        # COURSE BINDING
        cb_id = str(uuid.uuid4())
        cb = models.CourseBinding(
            id=cb_id, tenant_id=tenant_id, course_id=course_id,
            taxonomy_version_id=tv_id, policy_version_id=pv_id
        )
        db.add(cb)

        db.commit()
        print("Seed OK:", {"tenant": tenant_id, "course_id": course_id, "taxonomy_version": "2026.01", "policy_version": "v3"})
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
