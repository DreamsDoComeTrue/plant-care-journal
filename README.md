# Verdant Plant Care Journal

An MVP for the CS4800 Software Engineering with AI checkpoint. It uses a Flask backend, responsive HTML/CSS frontend, and Cloud Firestore for persistent cloud data. Photo uploads are intentionally omitted because they are not required for the checkpoint.

## Features

- Add plant profiles with nickname, species, and light needs.
- View all plants on a dashboard with task status.
- Add recurring care tasks such as watering, misting, fertilizing, or pruning.
- Check off tasks; they automatically become due again after their interval.
- Add date-stamped plant journal notes.
- Persist plant, task, and note data in Cloud Firestore.
- Run automated tests with GitHub Actions.
- Deploy the Flask app on Render.

## Firebase setup

1. Create a Firebase project at https://console.firebase.google.com.
2. Open **Build → Firestore Database** and create a database.
3. Open **Project settings → Service accounts**.
4. Click **Generate new private key** and download the JSON file. Never commit this file to GitHub.
5. Use the JSON contents as the `FIREBASE_SERVICE_ACCOUNT` environment variable locally and on Render.

For local development on Windows PowerShell:

```powershell
$env:FIREBASE_SERVICE_ACCOUNT = Get-Content .\service-account.json -Raw
python app.py
```

Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS` to the path of the JSON file.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Render deployment

1. Push this project to GitHub.
2. In Render, choose **New → Blueprint** and select the repository.
3. Render reads `render.yaml`.
4. When prompted for `FIREBASE_SERVICE_ACCOUNT`, paste the complete service-account JSON contents.
5. Deploy the Blueprint.

The service starts with `gunicorn app:app`. No Render disk is needed because Firestore stores the data remotely.
