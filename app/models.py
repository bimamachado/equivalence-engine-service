from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
from sqlalchemy import UniqueConstraint


class TaxonomyVersion(Base):
    __tablename__ = "taxonomy_versions"
    id = Column(String, primary_key=True)  # uuid string
    tenant_id = Column(String, index=True, nullable=False)
    version = Column(String, index=True, nullable=False)
    status = Column(String, default="active")  # draft|active|deprecated
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TaxonomyNode(Base):
    __tablename__ = "taxonomy_nodes"
    id = Column(Integer, primary_key=True)  # node_id
    taxonomy_version_id = Column(String, ForeignKey("taxonomy_versions.id"), index=True, nullable=False)
    area = Column(String, nullable=False)
    subarea = Column(String, nullable=False)
    conceito = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    palavras_chave = Column(JSON, nullable=False)  # lista
    nivel = Column(String, nullable=False)  # basico|intermediario|avancado
    critico = Column(Boolean, default=False)

class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    id = Column(String, primary_key=True)  # uuid string
    tenant_id = Column(String, index=True, nullable=False)
    version = Column(String, index=True, nullable=False)
    config = Column(JSON, nullable=False)  # thresholds/pesos/flags
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CourseBinding(Base):
    __tablename__ = "course_policy_binding"
    id = Column(String, primary_key=True)  # uuid
    tenant_id = Column(String, index=True, nullable=False)
    course_id = Column(String, index=True, nullable=False)
    taxonomy_version_id = Column(String, ForeignKey("taxonomy_versions.id"), nullable=False)
    policy_version_id = Column(String, ForeignKey("policy_versions.id"), nullable=False)
    active_from = Column(DateTime(timezone=True), server_default=func.now())

class EquivalenceResult(Base):
    __tablename__ = "equivalence_results"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_id", name="uq_equiv_tenant_request"),
    )
    id = Column(String, primary_key=True)  # uuid
    request_id = Column(String, index=True, nullable=False)
    tenant_id = Column(String, index=True, nullable=False)
    course_id = Column(String, index=True, nullable=True)

    origem_nome = Column(String, nullable=False)
    origem_carga = Column(Integer, nullable=False)
    origem_hash = Column(String, nullable=False)

    destino_nome = Column(String, nullable=False)
    destino_carga = Column(Integer, nullable=False)
    destino_hash = Column(String, nullable=False)

    decision = Column(String, index=True, nullable=False)
    score = Column(Integer, nullable=False)
    breakdown = Column(JSON, nullable=False)
    missing = Column(JSON, nullable=False)
    missing_critical = Column(JSON, nullable=False)

    justificativa_curta = Column(Text, nullable=False)
    justificativa_detalhada = Column(Text, nullable=False)

    degraded_mode = Column(Boolean, default=False)
    model_version = Column(String, nullable=False)
    policy_version = Column(String, nullable=False)
    taxonomy_version = Column(String, nullable=False)

    timings_ms = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)  # uuid
    tenant_id = Column(String, index=True, nullable=False)
    status = Column(String, index=True, default="queued")  # queued|running|done|failed
    total = Column(Integer, default=0)
    done = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

class JobItem(Base):
    __tablename__ = "job_items"
    id = Column(String, primary_key=True)  # uuid
    job_id = Column(String, ForeignKey("jobs.id"), index=True, nullable=False)
    status = Column(String, index=True, default="queued")  # queued|running|done|failed
    payload = Column(JSON, nullable=False)
    result_id = Column(String, ForeignKey("equivalence_results.id"), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TaxonomyEmbedding(Base):
    __tablename__ = "taxonomy_embeddings"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    taxonomy_version_id = Column(String, index=True, nullable=False)
    node_id = Column(Integer, index=True, nullable=False)
    vector = Column(JSON, nullable=False)  # lista float (MVP). Produção: pgvector.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TextEmbedding(Base):
    __tablename__ = "text_embeddings"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(String, index=True, nullable=False)
    taxonomy_version_id = Column(String, index=True, nullable=False)
    text_hash = Column(String, index=True, nullable=False)
    vector = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Label(Base):
    __tablename__ = "equivalence_labels"
    id = Column(String, primary_key=True)  # uuid
    result_id = Column(String, ForeignKey("equivalence_results.id"), index=True, nullable=False)
    labeled_by = Column(String, nullable=False)
    label = Column(String, nullable=False)  # DEFERIDO|INDEFERIDO|ANALISE_HUMANA
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True)          # ex: "arbe"
    name = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=False)  # hash do segredo
    status = Column(String, default="active")      # active|disabled
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint('key_hash', name='uq_api_keys_key_hash'),
    )
    id = Column(String, primary_key=True)  # uuid
    tenant_id = Column(String, ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String, nullable=False)  # ex: "prod-api", "dashboard-admin"
    key_hash = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # admin|auditor|api-client
    status = Column(String, default="active")  # active|revoked|disabled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)