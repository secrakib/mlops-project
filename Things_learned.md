# Things Learnt from Project

## MLOps Project

### GitHub Actions
- `workflow_dispatch` will create a manual button in the GUI.
- Should run code as a module using `python -m <module>` to avoid `src` not found / import issues.

### Streamlit
- Need `psycopg2` to connect python scripts to Postgres.
- Have to have a wakeup function to wake all services in parallel.

### .yml Configuration
- YAML is used as a dictionary to access variable values from a central point.

### Logging
- Check `if logger.handlers: return logger` so reloading Uvicorn/Streamlit doesn't create duplicate logs.
- Store `request_id` in a `ContextVar` and inject it via `logging.Filter` to trace requests without passing arguments everywhere.
- Always wrap custom DB handler `emit()` in a `try/except` so a database hiccup doesn't crash the user's API call (fail-open).
- Use `SimpleConnectionPool` from `psycopg2.pool` instead of opening a brand-new connection for every log record.
- Attach multiple handlers to one logger to send structured JSON to `stdout` (Render logs) and insert into Postgres at the same time.
- Use `python-json-logger` (`JsonFormatter`) so logs output as raw JSON fields instead of flat text strings.

### PostgreSQL
- Use `TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP` to auto-record UTC creation time on insert without manually passing timestamps from Python.

### Data Pipeline & Preprocessing
- **Out-of-Time (OOT) Split:** Sort chronologically by date (`issue_d`) before splitting train/val/test to simulate real-world production and avoid lookahead bias.
- **Pandera `strict='filter'`:** Automatically drops extra columns not defined in the schema while enforcing data types and nullability rules.
- **Config-Driven Schemas:** Build validation schemas dynamically from YAML configs to prevent hardcoding feature lists in validation logic.
- **Training vs. Inference Flag:** Pass `is_inference=True` to reusable preprocessing steps to bypass target/date column checks during live API calls.
- **ColumnTransformer + Pipeline:** Bundle imputation (`SimpleImputer`) and scaling (`StandardScaler`) together and set `remainder='drop'` to eliminate unselected columns cleanly.

### Model Monitoring & Drift Detection
- **Render Cold-Start Poller:** Ping health endpoints (`/-/healthy`) in a retry loop before pushing metrics so ephemeral jobs don't crash while free-tier services wake up.
- **Prometheus Pushgateway for Ephemeral Jobs:** Standard Prometheus pulls (scrapes) from long-running servers; short-lived batch scripts (like drift jobs) must push metrics out to Pushgateway using `push_to_gateway()`.
- **Decoupled Baseline via MLflow Aliases:** Use `client.get_model_version_by_alias()` and `client.download_artifacts()` to pull `baseline_probs.npy` directly from the active staging/production run instead of hardcoding validation sets.
- **Why `baseline_probs` is Needed:** Ground-truth labels arrive late (e.g., loan defaults take months to surface), making real-time accuracy tracking impossible. Storing the validation set's prediction distribution during training provides the "Expected" benchmark to detect drift immediately without true labels.
- **Time-Windowed SQL Pulls:** Use PostgreSQL `WHERE ts >= NOW() - INTERVAL '24 hours'` to slice a rolling inference window without loading entire log tables into memory.
- **Log-Epsilon Guard:** Replace 0% histogram bucket counts with a small epsilon (`0.0001`) before calculating PSI to prevent `division by zero` and `log(0) = -inf`.

### FastAPI & App Lifecycle
- **Pre-load Heavy Assets:** Use FastAPI's lifespan (`@asynccontextmanager`) to load database connections and ML models into memory *before* the server starts accepting traffic.
- **Global Caching via `app.state`:** Store loaded models and configs in `app.state` on startup. This allows request routes to access them instantly from RAM without reloading from disk or network.
- **State-Aware Health Checks:** Make your `/health` endpoint check if the model is actually loaded (returning a 503 if not). This stops load balancers from routing traffic to instances that are still waking up.
- **Automated API Metrics:** You can expose default Prometheus metrics (latency, request counts, HTTP codes) for all routes in one line using `prometheus-fastapi-instrumentator`.

### Middleware & Request Tracing
- **Safe Context Management:** When using `ContextVars` (like tracing IDs) in middleware, always reset them inside a `try...finally` block. Otherwise, data can leak across concurrent asynchronous requests.
- **Trace ID Pass-Back:** Always attach your internally generated `request_id` to the outgoing HTTP response headers. This lets frontend clients or API consumers report bugs using the exact ID you need to search your logs.

### Pydantic & Configuration
- **Dynamic API Schemas:** Instead of hardcoding hundreds of ML feature fields into a Pydantic model, read a YAML config and use Pydantic's `create_model` to generate the validation schema dynamically at runtime.
- **Computed Settings:** Use `@property` inside your Pydantic `BaseSettings` class to automatically assemble complex connection strings or URIs from basic environment variables.
- **Ignore Extra Env Vars:** Add `extra = "ignore"` to your settings config so your app doesn't crash if the deployment environment injects unrelated environment variables.

### ML Inference & Explainability
- **Business-Driven Thresholds:** Don't default to a `0.5` probability cutoff. Calculate the decision threshold dynamically using a cost matrix (the business cost of False Positives vs. False Negatives).
- **Unwrapping Model Pipelines:** Explainability tools (like SHAP) often crash on pipelines or calibrated models. You must programmatically dig into the pipeline steps and extract the core base estimator first.
- **Smart Explainer Routing:** Conditionally apply SHAP explainers based on the model type. Use the fast `TreeExplainer` for tree models, but dynamically fall back to `KernelExplainer` (using a pre-saved background dataset) for others.

### Model Training & Tuning
- **Pipeline Parameter Prefixing:** When tuning estimators wrapped in a `Pipeline`, prefix parameter names with the step name (e.g., `classifier__learning_rate`) so `RandomizedSearchCV` routes them to the correct component.
- **Random Search Cap Guard:** Clamp random search iterations using `min(n_iter, total_combinations)` so the search doesn't crash or trigger warnings if the combinations in your grid are fewer than `n_iter`.
- **Handling Class Imbalance:** Set XGBoost's `scale_pos_weight = (negative_count / positive_count)` or Logistic Regression's `class_weight='balanced'` to prevent models from ignoring the minority class.

### Evaluation & Calibration
- **Headless Plot Generation:** Always set `matplotlib.use('Agg')` before importing `pyplot` in automated pipelines or backend servers so figure rendering doesn't crash from missing display drivers.
- **Probability Calibration:** Raw model outputs are rarely true probabilities. Use `CalibratedClassifierCV(method='isotonic')` (wrapping with `FrozenEstimator` to avoid refitting) on a holdout validation set so output scores reflect actual likelihoods.
- **Separation Measurement (KS Test):** Use `scipy.stats.ks_2samp` to measure the maximum difference between positive and negative score distributions—a high KS statistic indicates strong class separation regardless of the threshold.
- **Cost-Optimized Threshold Search:** Instead of guessing a `0.5` decision cutoff, evaluate business costs across a grid of thresholds (`np.linspace(0.01, 0.99, 99)`) to find the exact probability threshold that minimizes dollar losses.

### MLflow & Pipeline Orchestration
- **Automated Model Gating:** Compare candidate model evaluation metrics (e.g., business cost) directly against the active production run via `MlflowClient()` before automatically assigning the `Staging` alias.
- **SHAP Background Sampling:** `KernelExplainer` is too slow on full training sets. Sample a representative subset (`shap.sample(X_train, 1000)`), save it with `joblib`, and log it as an MLflow artifact for serving.
- **Ephemeral File Cleanups:** Delete temporary local artifacts (`os.remove()`) immediately after logging them to MLflow to prevent disk bloat on orchestrator runners.

### Docker & Infrastructure
- **Targeted Multi-Stage Builds:** Install dependencies once in a shared `base` stage, then declare lightweight branch stages (`FROM base as api`, `FROM base as frontend`) to run distinct services from a single `Dockerfile`.
- **Config Variable Templating with `sed`:** If tools like Prometheus don't support environment variable interpolation in configs, provide a `.tmpl` file and substitute variables dynamically using `sed` in the Docker `ENTRYPOINT` before starting the process.
- **Docker Compose Networking:** Containers in the same compose network resolve each other by their service names (e.g., `http://api:8000`, `http://pushgateway:9091`), removing the need for hardcoded IP addresses.