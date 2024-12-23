from datetime import date
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from models import PaymentModel
from database import db
from schemas import Payment, PaymentUpdate
from datetime import datetime
from utils import normalize_csv
from bson import ObjectId
import os
import pandas as pd

router = APIRouter()

# Instantiate Model
payment_model = PaymentModel(db)


@router.get("/")
def get_payments(status: str = None, name: str = None, city: str = None, skip: int = 0, limit: int = 10):
    filters = {}
    if status:
        filters["payee_payment_status"] = status
    if name:
        filters["$or"] = [
            {"payee_first_name": {"$regex": name, "$options": "i"}},
            {"payee_last_name": {"$regex": name, "$options": "i"}}
        ]
    if city:
        filters["payee_city"] = {"$regex": city, "$options": "i"}

    payments = payment_model.get_payments(filters, skip, limit)
    return payments


@router.post("/")
def create_payment(payment: Payment):
    payment_dict = payment.dict()
    payment_dict["total_due"] = calculate_total_due(payment)
    payment_dict = update_status(payment_dict)
    payment_id = payment_model.create_payment(payment_dict)
    return {"payment_id": str(payment_id)}


def calculate_total_due(payment: Payment):
    discount = payment.due_amount * (payment.discount_percent or 0) / 100
    tax = payment.due_amount * (payment.tax_percent or 0) / 100
    return round(payment.due_amount - discount + tax, 2)


def update_status(payment):
    if payment["payee_due_date"] == date.today().isoformat():
        payment["payee_payment_status"] = "due_now"
    elif payment["payee_due_date"] < date.today().isoformat():
        payment["payee_payment_status"] = "overdue"
    return payment


@router.put("/{payment_id}")
def update_payment(payment_id: str, due_date: str = None, due_amount: float = None, status: str = None):
    """
    更新支付信息，仅允许修改 due_date, due_amount, 和 payee_payment_status
    """
    # 查询支付记录
    payment = payment_model.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    update_data = {}

    if due_date:
        try:
            # 验证时间格式
            valid_date = datetime.strptime(due_date, "%Y-%m-%d")
            update_data["payee_due_date"] = valid_date.strftime("%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if due_amount is not None:
        if due_amount < 0:
            raise HTTPException(
                status_code=400, detail="Due amount cannot be negative.")
        update_data["due_amount"] = due_amount

    if status:
        if status not in ["pending", "due_now", "overdue", "completed"]:
            raise HTTPException(status_code=400, detail="Invalid status.")
        update_data["payee_payment_status"] = status

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No valid fields to update.")

    # 更新支付记录
    update_result = payment_model.update_payment(payment_id, update_data)
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {"message": "Payment updated successfully", "updated_fields": update_data}


@router.delete("/{payment_id}")
def delete_payment(payment_id: str):
    delete_result = payment_model.delete_payment(payment_id)
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment deleted successfully"}


@router.get("/load-csv")
def load_csv():
    """
    加载和清洗 CSV 数据，并插入 MongoDB
    """
    csv_path = os.path.join(os.path.dirname(__file__),
                            "../data/payment_information.csv")
    df = normalize_csv(csv_path)

    for _, row in df.iterrows():
        payment_data = row.to_dict()
        try:
            # 验证并插入数据
            payment = Payment(**payment_data)
            payment_model.create_payment(payment.dict())
        except Exception as e:
            print(f"Error processing row {payment_data}: {e}")
    return {"message": "CSV data loaded successfully"}
