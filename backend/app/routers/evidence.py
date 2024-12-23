from fastapi import APIRouter, HTTPException, UploadFile, File
from models import PaymentModel
from database import db
from bson import ObjectId
from datetime import datetime
import os
import shutil
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter()

payment_model = PaymentModel(db)
# 文件存储路径
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "../evidence_files")
os.makedirs(EVIDENCE_DIR, exist_ok=True)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@router.post("/{payment_id}/upload")
def upload_evidence_file(payment_id: str, file: UploadFile = File(...)):
    """
    上传证据文件
    """
    # 验证 payment_id 是否存在
    payment = payment_model.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # 验证支付状态是否为 completed
    if payment.get("payee_payment_status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot upload evidence for payment not marked as completed"
        )

    # 存储文件逻辑
    file_path = f"evidence_files/{payment_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 更新数据库记录
    db["evidence"].insert_one({
        "payment_id": payment_id,
        "file_path": file_path,
        "file_name": file.filename,
        "uploaded_at": datetime.utcnow()
    })

    return {"message": "Evidence uploaded successfully", "file_path": file_path}


@router.get("/{payment_id}/download-link")
def generate_download_link(payment_id: str):
    """
    生成文件的下载链接
    """
    evidence = db["evidence"].find_one({"payment_id": payment_id})
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    file_path = evidence.get("file_path")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    download_url = f"{BASE_URL}/evidence/{payment_id}/file"

    return JSONResponse(
        content={
            "download_url": download_url,
        }
    )


@router.get("/{payment_id}/file")
def serve_file(payment_id: str):
    """
    提供文件下载
    """
    evidence = db["evidence"].find_one({"payment_id": payment_id})
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    file_path = evidence.get("file_path")
    file_name = evidence.get("file_name")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 自动检测 MIME 类型
    mime_type = "application/pdf" if file_path.endswith(".pdf") else \
                "image/jpeg" if file_path.endswith(".jpg") else \
                "image/png" if file_path.endswith(".png") else \
                "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=file_name
    )
