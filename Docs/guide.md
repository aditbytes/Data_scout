# DataScout — User Guide

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Audience:** End users, analysts, and business stakeholders  

---

## 1. What is DataScout?

DataScout is an **autonomous enterprise data analyst** that lets you upload any dataset and ask questions about it in plain English. Powered by **Claude 3.5 Sonnet on Amazon Bedrock**, it writes and executes Python code behind the scenes to deliver accurate, data-driven answers — no coding required.

### What You Can Do
- 📁 **Upload** CSV, Excel, or JSON datasets (up to 100 MB)
- 💬 **Ask** natural language questions about your data
- 📊 **Get** tables, statistics, and charts as answers
- 💻 **View** the generated Python code for transparency
- 📥 **Download** results and visualizations

### What Makes It Different
| Feature | DataScout | ChatGPT / Generic LLM |
|---------|-----------|----------------------|
| Numerical Accuracy | ✅ Computes via code execution | ❌ Often hallucinates numbers |
| Data Privacy | ✅ Your data stays in your AWS account | ⚠️ Data sent to third-party servers |
| Code Transparency | ✅ Shows every line of code | ❌ Hidden "reasoning" |
| Enterprise Ready | ✅ AES-256 encryption, IAM, audit logs | ❌ Consumer-grade |

---

## 2. Getting Started

### Step 1: Open DataScout

Navigate to the DataScout URL provided by your administrator (e.g., `https://datascout.yourcompany.com`), or run locally:

```bash
streamlit run streamlit_app/app.py
# Opens at http://localhost:8501
```

### Step 2: Upload Your Dataset

1. Click the **"Upload Your Dataset"** section
2. Drag and drop your file, or click **Browse files**
3. Supported formats: **CSV, XLSX, XLS, JSON**
4. Maximum file size: **100 MB**

Once uploaded, you'll see:
- ✅ File name, row count, column count, and file size
- 🔎 An expandable **preview** of the first 5 rows
- ⚠️ Data quality warnings if any columns have missing values

### Step 3: Ask a Question

Type a question in the **"Ask a Question"** field and click **🔍 Ask**. Examples:

```
What are the top 5 products by total revenue?
Show me monthly revenue trends
What is the average revenue by region?
What is the correlation between quantity and revenue?
Show me the profit distribution across categories
```

> 💡 **Tip:** DataScout generates **contextual suggestions** based on your dataset's columns and data types.

### Step 4: Review Results

Results appear in **4 tabs**:

| Tab | What You See |
|-----|--------------|
| 📝 **Explanation** | Plain-language description of the analysis approach |
| 📊 **Results** | Data tables, statistics, and computed values |
| 💻 **Code** | The Python code that was generated and executed |
| 📈 **Charts** | Visualizations (bar charts, line charts, distributions) |

### Step 5: Ask Follow-Up Questions

DataScout remembers context within your session. You can ask follow-up questions like:

```
First:  "What is the total revenue by region?"
Then:   "Now break it down by product"
Then:   "Show me the trend over time for the top region"
```

All past queries appear in the **Query History** section at the bottom.

---

## 3. Query Writing Tips

### ✅ Good Queries

| Query | Why It Works |
|-------|-------------|
| "What is the average revenue by region?" | Clear metric + clear grouping |
| "Show me the top 10 products by profit" | Specific number + clear sorting |
| "What is the correlation between price and quantity?" | Clear analytical task |
| "Create a bar chart of sales by category" | Explicit visualization request |
| "Are there any outliers in the revenue column?" | Statistical analysis |

### ❌ Queries to Avoid

| Query | Why It's Problematic | Better Version |
|-------|---------------------|----------------|
| "Tell me about my data" | Too vague | "Show me summary statistics for all numeric columns" |
| "Predict next month's sales" | Needs time-series model, not one query | "Show me the monthly sales trend for 2025" |
| "Fix my data" | Ambiguous | "How many null values are in each column?" |

### 🎯 Advanced Queries

```
Statistical:   "Run a chi-square test on category vs. region"
Comparative:   "Which region has the highest revenue growth rate?"
Conditional:   "What is the average order value for customers with > 10 orders?"
Multi-step:    "Compare revenue and profit margins across all product categories"
```

---

## 4. Understanding Results

### Data Tables
- All numbers are **computed from your data** — never guessed or hallucinated
- Tables include column headers and formatted values
- Click **📥 Download Results** to save as text

### Charts & Visualizations
- Charts are generated using **matplotlib** and **seaborn**
- Click **📥 Download Chart** to save as PNG
- Charts are auto-sized to fit your screen

### Code Transparency
- Every analysis shows the exact Python code used
- Click **📋 Copy Code** to reuse in Jupyter, Colab, etc.
- Code always uses **pandas**, **numpy**, **matplotlib**, and **seaborn**

---

## 5. Session Management

| Feature | Behavior |
|---------|----------|
| **Session Duration** | 30 minutes of inactivity |
| **Data Retention** | Datasets auto-deleted after 7 days |
| **Conversation History** | Preserved within session |
| **Multiple Datasets** | One dataset per session |

> 💡 **Tip:** Refresh the page to start a new session with a different dataset.

---

## 6. Supported File Formats

| Format | Extension | Max Size | Notes |
|--------|-----------|----------|-------|
| CSV | `.csv` | 100 MB | UTF-8 recommended |
| Excel | `.xlsx`, `.xls` | 100 MB | First sheet only |
| JSON | `.json` | 100 MB | Array of objects format |

### Data Preparation Tips

1. **Clean headers** — Use short, descriptive column names without special characters
2. **Consistent formats** — Dates should be in ISO format (`YYYY-MM-DD`)
3. **No merged cells** — Excel files should have flat, tabular structure
4. **Remove empty rows** — Trailing blank rows can affect analysis
5. **UTF-8 encoding** — Save CSV files with UTF-8 encoding

---

## 7. Security & Privacy

### Data Protection
- 🔒 All uploads encrypted with **AES-256** at rest
- 🔒 Data transmitted over **HTTPS/TLS**
- 🔒 Data stored in **your private AWS account** — never shared
- 🗑️ Session data **auto-deleted after 7 days**

### What Is Logged (and What Is NOT)

| Logged | NOT Logged |
|--------|-----------|
| Query length (chars) | Query text content |
| Execution time | Data values |
| Success/failure status | Column contents |
| File size (MB) | Row-level data |
| Hashed filename | Original filename |

> 🛡️ DataScout is designed with **privacy-by-default** — no actual data values are ever stored in logs.

---

## 8. FAQ

**Q: My upload is rejected. Why?**  
A: Check that your file is CSV, XLSX, XLS, or JSON and under 100 MB. Other formats (PDF, TXT, Parquet) are not supported.

**Q: Why does the analysis take 30+ seconds?**  
A: Complex queries involving large datasets, multiple groupings, or chart generation take longer. Try simplifying the query or reducing dataset size.

**Q: Can I upload multiple datasets?**  
A: Currently one dataset per session. Upload a new dataset by refreshing the page.

**Q: Are my results saved?**  
A: Within a session, all results are preserved in Query History. After the session ends (30 min inactivity), results are cleared.

**Q: The numbers don't look right. What should I do?**  
A: Check the **Code tab** to see exactly what was computed. If the code logic looks wrong, rephrase your question more specifically.

**Q: Can I use DataScout on my phone?**  
A: Yes — the interface is responsive and works on tablets and phones, though a desktop browser provides the best experience.

---

## 9. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Submit query |
| `Ctrl + L` | Clear text input |
| `Tab` | Navigate between sections |

---

## 10. Contact & Support

- **Documentation:** `Docs/` folder in the project repository
- **Bug Reports:** Submit via GitHub Issues or the PR template
- **Support Email:** support@datascout.ai
- **Demo Script:** See `demo/demo_script.md` for a guided walkthrough
