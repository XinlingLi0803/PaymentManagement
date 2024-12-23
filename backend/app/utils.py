def normalize_csv(file_path):
    import pandas as pd
    import numpy as np

    df = pd.read_csv(file_path)

    # 填充缺失字段
    df["discount_percent"] = df["discount_percent"].fillna(0).astype(float)
    df["tax_percent"] = df["tax_percent"].fillna(0).astype(float)
    df["due_amount"] = df["due_amount"].fillna(0).astype(float)

    # 确保字符串类型字段正确
    df["payee_postal_code"] = df["payee_postal_code"].astype(str)
    df["payee_phone_number"] = df["payee_phone_number"].astype(str)

    # 转换日期字段
    df["payee_added_date_utc"] = pd.to_datetime(
        df["payee_added_date_utc"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    df["payee_due_date"] = pd.to_datetime(
        df["payee_due_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    # 清洗 payee_country 字段
    df["payee_country"] = df["payee_country"].replace(
        {np.nan: "Unknown"}).astype(str)

    # 删除日期无效的行
    df = df.dropna(subset=["payee_added_date_utc", "payee_due_date"])

    # 计算 total_due
    df["total_due"] = df.apply(
        lambda row: round(
            row["due_amount"] - row["due_amount"] *
            row["discount_percent"] / 100
            + row["due_amount"] * row["tax_percent"] / 100,
            2,
        ),
        axis=1,
    )

    return df
