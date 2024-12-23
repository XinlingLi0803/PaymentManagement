from bson import ObjectId


class PaymentModel:
    def __init__(self, db):
        self.collection = db["payments"]

    def get_payment_by_id(self, payment_id: str):
        try:
            return self.collection.find_one({"_id": ObjectId(payment_id)})
        except Exception as e:
            print(f"Error finding payment by ID: {e}")
            return None

    def get_payments(self, filters, skip, limit):
        payments = list(self.collection.find(filters).skip(skip).limit(limit))
        # Convert ObjectId to string for JSON serialization
        for payment in payments:
            payment["_id"] = str(payment["_id"])
        return payments

    def update_payment(self, payment_id, update_data):
        return self.collection.update_one({"_id": ObjectId(payment_id)}, {"$set": update_data})

    def delete_payment(self, payment_id):
        return self.collection.delete_one({"_id": ObjectId(payment_id)})
