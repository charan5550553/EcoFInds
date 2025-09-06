# Ecofinds Backend

This is the **backend** of the Ecofinds project.  
It is built using **Flask (Python)** and provides APIs + server logic.

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ecofinds-backend.git
cd ecofinds-backend
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate    # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
python app.py
```
By default, the server runs at: `http://127.0.0.1:5000`

### 5. Project Structure
```
app.py            → Flask application entry point
requirements.txt  → Python dependencies
README.md         → Documentation
```

## 📌 Notes
- Ensure the frontend (`ecofinds-frontend`) is properly configured to point to this backend.
