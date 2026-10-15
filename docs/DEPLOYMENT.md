# Deployment

The app is prepared for Streamlit Community Cloud. It has not been assigned a public application URL by this project.

Use repository **Priynka-Roy/actuarylab-ai-insurance-pricing-risk**, branch **main**, entry point **streamlit_app.py**, Python **3.12**. The owner may deploy after technical review. No secrets are required. The pinned `requirements.txt` is the deployment dependency file.

Startup reads integrity-verified, repository-controlled JSON summaries. It does not download source data, train estimators, or deserialize an untrusted pickle. Keep `artifacts/dashboard.json`, `reports/results.json`, the provenance record, frozen protocol and integrity manifest together when deploying. CI verifies the artifact bundle without requiring private source files.

Local setup:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/verify_artifacts.py
streamlit run streamlit_app.py --server.port 8504
```

Open [the local app](http://localhost:8504) on the same computer after starting it. A localhost link does not give another reader a public hosted app. The local port override belongs in the command; cloud configuration does not pin port 8504.

Simulation is educational, bounded and cached. It uses aggregate model-derived synthetic portfolio assumptions; users must not enter private real-person insurance records. Check the eight app sections, synthetic pricing calculation, stress comparison and mobile chart behavior after deployment. The routine startup health check confirms server readiness; behavioral tests and browser review provide separate evidence that pages render.
