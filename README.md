# Automated Logistics Performance Reporting System

An automated Python-based reporting system designed to streamline **Key Account Manager (KAM) operations** by eliminating repetitive manual work involved in generating company-wise logistics performance reports.

The system collects a **Company ID through Google Forms**, automatically processes the corresponding shipment data, calculates logistics performance metrics, updates a live Google Sheet, and emails the completed reports to the requester.

---

## 🚀 Project Overview

In a typical manual workflow, KAMs need to:

* Submit a company/reporting request
* Find the relevant shipment records
* Filter data for the required company and time period
* Calculate performance metrics
* Prepare an Excel report
* Share raw data
* Email the reports to the requester
* Track completed requests

This project automates the complete workflow using **Python, Google Forms, Google Sheets, and email automation**.

Once Windows Task Scheduler is configured, the system can execute automatically on an **hourly basis with zero manual intervention**.

---

## 🔄 Workflow

```text
KAM
 │
 ▼
Google Form
 │
 │ Company ID
 ▼
Request Google Sheet
 │
 │ Pending Request
 ▼
Python Controller
 │
 ├── Check for new requests
 │
 ├── Identify Company ID
 │
 ├── Filter last 3 months of shipment data
 │
 ├── Calculate performance metrics
 │
 ├── Update Google Performance Sheet
 │
 ├── Generate XLSX report
 │
 ├── Create ZIP of raw shipment data
 │
 ├── Email reports to requester
 │
 └── Mark request as "Done"
 │
 ▼
Completed Report
```

---

## ⚙️ Key Features

### 1. Automated Request Collection

KAMs submit a **Company ID** through a Google Form.

The submitted request is stored in a connected Google Sheet with a status such as:

```text
Pending
```

### 2. Automatic Request Detection

The Python controller checks the request sheet whenever it runs and identifies new pending requests.

This prevents the need for manually running the reporting process for every company.

### 3. Company-wise Data Filtering

For each pending request, the system:

* Reads the requested Company ID
* Filters the raw shipment dataset
* Extracts the relevant records
* Processes approximately **3 months of shipment data**

### 4. Logistics Performance Analysis

The system calculates important logistics performance metrics such as:

* Turnaround Time (TAT)
* SLA Compliance
* Delivery Performance
* Delivery Categories
* Shipment-level performance
* Company-wise performance summaries

### 5. Automated Google Sheet Reporting

The calculated results are pushed into a Google Sheet that acts as the **live performance report**.

This allows KAMs to access the latest processed performance information without manually preparing reports.

### 6. Automated Report Delivery

After processing, the system automatically emails the requester:

* 📦 ZIP file containing the relevant raw shipment data
* 📊 XLSX file containing the performance report

### 7. Duplicate Processing Prevention

After successful processing, the request status is changed from:

```text
Pending → Done
```

This ensures that the same request is **not processed multiple times**.

### 8. Scheduled Automation

With Windows Task Scheduler configured, the entire pipeline can run automatically:

```text
Every Hour
     ↓
Check Requests
     ↓
Process Pending Requests
     ↓
Generate Reports
     ↓
Send Email
     ↓
Mark Request Done
```

---

## 🛠️ Tech Stack

| Technology                 | Purpose                               |
| -------------------------- | ------------------------------------- |
| **Python**                 | Core automation and data processing   |
| **Pandas**                 | Data cleaning, filtering and analysis |
| **Google Forms**           | Collecting Company ID requests        |
| **Google Sheets**          | Request management and live reporting |
| **Excel / XLSX**           | Performance report generation         |
| **ZIP**                    | Packaging raw shipment data           |
| **Email Automation**       | Automated report delivery             |
| **Windows Task Scheduler** | Scheduled execution                   |

---

## 📊 Data Processing Pipeline

The system follows an automated ETL-style workflow:

### Extract

Data is collected from:

* Google Sheets
* Raw shipment datasets
* Request submissions

### Transform

Python processes the data by:

* Filtering records by Company ID
* Selecting the required time period
* Cleaning shipment information
* Calculating TAT
* Evaluating SLA compliance
* Categorizing deliveries
* Generating company-level performance metrics

### Load

Processed results are:

* Written to Google Sheets
* Exported as XLSX
* Packaged with relevant raw data
* Delivered to the requester through email

---

## 📁 Repository Structure

```text
Automated-Logistics-Performance-Reporting-System/
│
├── request_controller (1).py
│   └── Main automation controller
│
├── Seller_Performance_Python Script(Himanshu_Yadav).txt
│   └── Seller/company performance calculation logic
│
├── Shipway internship report formatting.pdf
│   └── Project/internship documentation
│
└── README.md
    └── Project documentation
```

---

## 🧠 Core Logic

The controller follows a simple request-processing mechanism:

```python
while True:

    check_request_sheet()

    for request in pending_requests:

        company_id = request["Company ID"]

        shipment_data = filter_shipment_data(
            company_id,
            last_3_months
        )

        performance = calculate_metrics(
            shipment_data
        )

        update_google_sheet(performance)

        generate_xlsx(performance)

        create_raw_data_zip(shipment_data)

        send_email(
            xlsx_report,
            raw_data_zip
        )

        mark_request_as_done(request)
```

The actual implementation contains the project-specific processing and integration logic.

---

## 🔐 Request State Management

The system uses request status tracking to make the workflow reliable.

### Pending Request

```text
Company ID → Pending
```

The controller detects and processes it.

### Completed Request

```text
Company ID → Done
```

The controller skips it during future runs.

This provides a simple mechanism for **idempotent request processing** and helps prevent duplicate reports.

---

## 🎯 Business Impact

The primary goal of this project is to reduce repetitive manual reporting work for KAM operations.

### Before Automation

```text
Manual Request
      ↓
Find Data
      ↓
Filter Data
      ↓
Calculate Metrics
      ↓
Prepare Excel
      ↓
Compress Raw Data
      ↓
Send Email
      ↓
Track Request
```

### After Automation

```text
Submit Company ID
       ↓
   Everything
   Automated
       ↓
Receive Reports
```

The automation improves:

* ⏱️ Reporting turnaround time
* 📊 Reporting consistency
* 🔄 Process reliability
* 📧 Report delivery
* 📁 Data organization
* 👨‍💼 KAM productivity

Most importantly, it removes repetitive manual steps from the reporting workflow.

---

## 💡 Why This Project?

This project was built to solve a practical business problem rather than simply demonstrate a technical concept.

The focus was on combining:

**Data Processing + Business Logic + Automation + Reporting**

into a single end-to-end workflow.

It demonstrates how Python can be used not only for data analysis but also to automate repetitive operational processes.

---

## 🔮 Future Improvements

Potential improvements include:

* Add centralized logging and error tracking
* Add retry mechanisms for failed requests
* Add email notifications for processing failures
* Add automated data validation
* Add dashboard integration with Power BI
* Add request priority handling
* Add execution history and audit logs
* Containerize the application for easier deployment
* Move scheduled execution to a cloud-based service

---

## 👨‍💻 Skills Demonstrated

* Python Automation
* Pandas
* Data Cleaning
* Data Processing
* Exploratory Data Analysis
* Business Logic Implementation
* Google Sheets Integration
* Excel Report Automation
* Email Automation
* Workflow Automation
* Task Scheduling
* ETL Concepts
* Operational Reporting

---

## 📌 Project Highlights

> **Input:** Company ID submitted through Google Form

> **Processing:** 3 months of shipment data

> **Output:** Performance report + raw data ZIP

> **Delivery:** Automated email

> **Tracking:** Pending → Done

> **Execution:** Hourly automation through Task Scheduler

---

## 📄 Documentation

Additional project documentation is available in the repository, including the internship/project report.

---

## 👤 Author

**Himanshu Yadav**

B.Tech | Data Analytics & Data Science

### Areas of Interest

* Data Analytics
* Data Science
* Python Automation
* Business Intelligence
* Machine Learning

---

⭐ If you found this project useful, consider giving the repository a star!
