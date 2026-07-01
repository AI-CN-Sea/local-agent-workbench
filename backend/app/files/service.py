from hashlib import sha256
from pathlib import Path
import re
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.database.service import create_session, create_uploaded_file_record, ensure_project
from app.schemas.security import FileUploadResponse
from app.security.payload_scanner import scan_payload

ALLOWED_EXTENSIONS = {
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".docx",
    ".pdf",
    ".pptx",
    ".xlsx",
    ".csv",
    ".tex",
    ".bib",
    ".py",
    ".cpp",
    ".java",
    ".m",
    ".md",
    ".txt",
}

CHUNK_SIZE = 1024 * 1024


async def quarantine_upload(file: UploadFile, project_id: str | None = None) -> FileUploadResponse:
    original_filename = _safe_original_filename(file.filename)
    safe_project_id = _safe_project_id(project_id)
    findings = scan_payload(original_filename)
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File extension is not allowed.")

    content, digest = await _read_limited_file(file)
    stored_filename = f"{uuid4().hex}{extension}"

    session = create_session()
    try:
        project = ensure_project(session, safe_project_id)
        effective_project_id = project.id
        relative_dir = Path(settings.upload_storage_root) / effective_project_id / "uploads" / "quarantine"
        relative_dir.mkdir(parents=True, exist_ok=True)
        relative_path = relative_dir / stored_filename
        relative_path.write_bytes(content)

        record = create_uploaded_file_record(
            session,
            project_id=effective_project_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            size_bytes=len(content),
            extension=extension,
            relative_path=relative_path.as_posix(),
            sha256=digest,
            scanner_findings=[finding.type for finding in findings],
        )
    finally:
        session.close()

    return FileUploadResponse(
        file_id=record.id,
        original_filename=record.original_filename,
        size_bytes=record.size_bytes,
        extension=record.extension,
        relative_path=record.relative_path,
        sha256=record.sha256,
        status=record.status,
    )


def _safe_original_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    name = filename.replace("\\", "/").split("/")[-1].strip()
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Filename is invalid.")
    return name[:260]


def _safe_project_id(project_id: str | None) -> str | None:
    if project_id is None or project_id == "":
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", project_id):
        raise HTTPException(status_code=400, detail="Project id is invalid.")
    return project_id


async def _read_limited_file(file: UploadFile) -> tuple[bytes, str]:
    buffer = bytearray()
    hasher = sha256()

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="File exceeds 20MB limit.")
        hasher.update(chunk)

    return bytes(buffer), hasher.hexdigest()
