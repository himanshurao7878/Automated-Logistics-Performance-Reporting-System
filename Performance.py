import pandas as pd
import os
import pygsheets
from datetime import datetime
import sys

company_id = sys.argv[1] if len(sys.argv) > 1 else "90001"
# ------------------------------------------
# CONFIG
# ------------------------------------------
os.chdir(r'C:\Seller_performance')

raw_data_file = r'C:\Seller_performance\raw_csv\shipway_orders_last3months.csv'
# ------------------------------------------
# FAST CSV LOAD
# ------------------------------------------
Merge = pd.read_csv(raw_data_file, encoding='latin1', on_bad_lines='skip', low_memory=False)

# ------------------------------------------
# CLEAN COLUMN NAMES (FIX BOM ISSUE)
# ------------------------------------------
Merge.columns = (
    Merge.columns
    .str.replace('ï»¿', '', regex=False)
    .str.replace('"', '', regex=False)
    .str.strip()
)

print("Rows Loaded:", Merge.shape[0])
print("Columns:", Merge.columns.tolist())

# ------------------------------------------
# COMPANY ID FILTER
# ------------------------------------------
allowed_ids = [company_id]

Merge['Company ID'] = Merge['Company ID'].astype(str)
Merge = Merge[Merge['Company ID'].isin(allowed_ids)]

print("Rows After Company Filter:", Merge.shape[0])

if Merge.empty:
    raise ValueError("No rows found after Company ID filter")

# ------------------------------------------
# SMART DATE PARSER
# ------------------------------------------

# def smart_parse(col):

#     if pd.api.types.is_datetime64_any_dtype(col):
#         return col

#     sample = col.dropna().astype(str).head(5)

#     if not sample.empty and sample.str.match(r"\d{4}-\d{2}-\d{2}").all():
#         return pd.to_datetime(col, errors="coerce")

#     return pd.to_datetime(col, errors="coerce", dayfirst=True)

def smart_parse(col):
    if pd.api.types.is_datetime64_any_dtype(col):
        return col

    col = col.astype(str).str.replace("T", " ").str.strip()

    parsed = pd.to_datetime(col, format="%d-%m-%Y %H:%M:%S", errors="coerce")
    parsed = parsed.fillna(pd.to_datetime(col, format="%Y-%m-%d %H:%M:%S", errors="coerce"))
    parsed = parsed.fillna(pd.to_datetime(col, format="%d-%m-%Y %H:%M", errors="coerce"))
    parsed = parsed.fillna(pd.to_datetime(col, format="%Y-%m-%d %H:%M", errors="coerce"))

    numeric_mask = pd.to_numeric(col, errors='coerce').notna()
    if numeric_mask.any():
        parsed.loc[numeric_mask] = pd.to_datetime(
            pd.to_numeric(col[numeric_mask]),
            unit="D",
            origin="1899-12-30",
            errors="coerce"
        )

    return parsed


# ------------------------------------------
# DATE PARSING
# ------------------------------------------
date_cols = [
    "Order Assign Date",
    "Pickup Date",
    "First Attempt Date",
    "Delivery Date",
    "AWB Shipped Date",
    "EDD Date",
    "NDR Last Attempt Date",
    "NDR Second Attempt Date",
    "NDR Third Attempt Date",
    "RTO Initiated Date",
    "RTD Date"
]

for col in date_cols:
    if col in Merge.columns:
        Merge[col + "_ts"] = smart_parse(Merge[col])

# ------------------------------------------
# DATE ONLY
# ------------------------------------------
Merge["Assign_Date"] = Merge["Order Assign Date_ts"].dt.date
Merge["Attempt_Date"] = Merge["First Attempt Date_ts"].dt.date

# ------------------------------------------
# SPEED
# ------------------------------------------
Merge["speed"] = (
    Merge["Courier Slab"]
    .astype(str)
    .str.contains("express", case=False)
    .map({True: "Air", False: "Surface"})
)

# ------------------------------------------
# MONTH / WEEK
# ------------------------------------------
Merge["Assign_Timestamp"] = Merge["Order Assign Date_ts"]

Merge["Month"] = Merge["Assign_Timestamp"].dt.strftime('%b-%y')
Merge["Day"] = Merge["Assign_Timestamp"].dt.day

Merge["Week"] = pd.cut(
    Merge["Day"],
    bins=[0, 7, 14, 21, 31],
    labels=[1, 2, 3, 4],
    right=True
).astype("Int64")

Merge["Week_Month"] = "Week" + Merge["Week"].astype(str) + "-" + Merge["Month"]

# ------------------------------------------
# TRANSIT TIMES
# ------------------------------------------
Merge['O2P'] = (Merge['Pickup Date_ts'] - Merge['Order Assign Date_ts']).dt.days
Merge['O2D'] = (Merge['Delivery Date_ts'] - Merge['Order Assign Date_ts']).dt.days
Merge['P2A'] = (Merge['First Attempt Date_ts'] - Merge['Pickup Date_ts']).dt.days
Merge['P2D'] = (Merge['Delivery Date_ts'] - Merge['Pickup Date_ts']).dt.days

# ------------------------------------------
# ZONE NORMALIZATION
# ------------------------------------------
Merge["Zone_clean"] = (
    Merge["Zone"]
    .astype(str)
    .str.strip()
    .str.lower()
)

zone_map = {
    "metro to metro": "metro to metro",
    "same city": "same city",
    "same state": "same state",
    "north east , j&k": "north east , j&k",
    "rest of india": "rest of india"
}

Merge["Zone_clean"] = Merge["Zone_clean"].replace(zone_map)

# ------------------------------------------
# TAT LOGIC
# ------------------------------------------
tat_map = {
    "surface": {
        "rest of india": 7,
        "same city": 2,
        "same state": 3,
        "north east , j&k": 9,
        "metro to metro": 5,
    },
    "air": {
        "rest of india": 5,
        "same city": 2,
        "same state": 3,
        "north east , j&k": 7,
        "metro to metro": 3,
    }
}

Merge["TAT"] = Merge.apply(
    lambda x: tat_map.get(str(x["speed"]).lower(), {}).get(x["Zone_clean"], pd.NA),
    axis=1
)

Merge["TAT"] = pd.to_numeric(Merge["TAT"], errors="coerce")

# ------------------------------------------
# SLA STATUS
# ------------------------------------------
Merge["SLA_Status"] = Merge.apply(
    lambda x: (
        ""
        if pd.isna(x["P2A"]) or pd.isna(x["TAT"])
        else "Within_TAT" if x["P2A"] <= x["TAT"]
        else "TAT_Breached"
    ),
    axis=1
)

# ------------------------------------------
# ATTEMPT CATEGORY
# ------------------------------------------
def attempt_category(row):

    ac = pd.to_numeric(row["Total Attempt Counts"], errors="coerce")

    if pd.isna(row["First Attempt Date_ts"]) or pd.isna(ac) or ac == 0:
        return "Not_Attempt"
    elif ac == 1:
        return "FASR"
    else:
        return "NDR"

Merge["Attempt_Category"] = Merge.apply(attempt_category, axis=1)

# ------------------------------------------
# DELIVERED CATEGORY
# ------------------------------------------
Merge["Delivered_Category"] = Merge.apply(
    lambda x: (
        "FASR_Delivered"
        if x["Status"] == "DELIVERED"
        and pd.to_numeric(x["NDR Attempt Count"], errors="coerce") == 0
        else "NDR_Delivered"
        if x["Status"] == "DELIVERED"
        and pd.to_numeric(x["NDR Attempt Count"], errors="coerce") > 0
        else ""
    ),
    axis=1
)

# ------------------------------------------
# O2P COMPLIANCE
# ------------------------------------------
def o2p_cat(x):

    if pd.isna(x):
        return ""

    if x <= 1:
        return "Within 24 hours"

    if x <= 2:
        return "Within 48 hours"

    return "More than 48 hours"

Merge["O2P_Compliance"] = Merge["O2P"].apply(o2p_cat)

# ------------------------------------------
# STATUS GROUP
# ------------------------------------------
status_group_map = {
    "DELIVERED": "DELIVERED",
    "RTO DELIVERED": "RTO",
    "PICKUP EXCEPTION": "NOT PICKED",
    "LOST": "LOST & DAMAGED",
    "RTO IN TRANSIT": "RTO",
    "Shipment Booked": "NOT PICKED",
    "UNDELIVERED": "UNDELIVERED",
    "RTO NDR": "RTO",
    "RTO OFD": "RTO",
    "IN TRANSIT": "IN TRANSIT",
    "OUT FOR DELIVERY": "OUT FOR DELIVERY",
    "REACHED AT DESTINATION HUB": "IN TRANSIT",
    "AWB ASSIGNED": "NOT PICKED",
    "OUT FOR PICKUP": "NOT PICKED",
    "DELAYED": "UNDELIVERED",
    "PICKED UP": "IN TRANSIT",
    "DAMAGED": "LOST & DAMAGED",
    "RTO INITIATED" : "RTO",
    "SHIPPED" : "IN TRANSIT",
    "PICKUP GENERATED" : "NOT PICKED"
}

Merge["Order_Status_Group"] = Merge["Status"].map(status_group_map).fillna("Others")

# ------------------------------------------
# FINAL EXPORT
# ------------------------------------------
required_cols = [
'Company ID',
'Company Name',
'Courier ID',
'Parent Courier',
'Courier Slab',
'Tracking Number',
'Status',
'RAD Status Date',
'Total Order Amount',
'Payment Method',
'Shipping Pincode',
'Pickup Pincode',
'Zone',
'Pickup Date',
'Order Assign Date',
'AWB Shipped Date',
'EDD Date',
'First Attempt Date',
'NDR Last NDR Status',
'NDR Last Attempt Date',
'NDR/RTO Scan Reason',
'NDR Attempt Count',
'Product Name',
'Delivery Date',
'RTO Initiated Date',
'RTD Date',
'Follow-up Mode',
'Last Customer response',
'Assign_Date',
'Attempt_Date',
'speed',
'Month',
'Week_Month',
'O2P',
'O2D',
'P2A',
'P2D',
'Zone_clean',
'TAT',
'SLA_Status',
'O2P_Compliance',
'Attempt_Category',
'Delivered_Category',
'Order_Status_Group',
'Shipping State',
'Shipping city',
'NDR Second Attempt Date',
'NDR Third Attempt Date',
'Total Attempt Counts',
'Sub Status',
'Shipping City'
]

Final_Output = Merge[[c for c in required_cols if c in Merge.columns]]

Final_Output = Final_Output.fillna("")

today = datetime.today().strftime("%d-%m-%Y")

output_file = fr'C:\Seller_performance\seller_data\{company_id}_{today}.csv'

Final_Output.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d"
)

print("Final Output Saved:", output_file)

# ------------------------------------------
# GOOGLE SHEETS UPLOAD
# ------------------------------------------

gc = pygsheets.authorize(service_file="client_secret.json")

sh = gc.open_by_key("1RlzF5s5HjvA-64KjVUuNqdkxfq7NouRsByaJuLaFYNw")

wks = sh.worksheet_by_title("Raw")

wks.clear(start="A1")
wks.resize(rows=len(Final_Output) + 10, cols=len(Final_Output.columns) + 5)
wks.set_dataframe(Final_Output, "A1", copy_head=True)

print("Google Sheet upload completed")
