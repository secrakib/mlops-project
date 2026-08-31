# Index

| Date | Session Time | Goals | Status | Jump |
|------|---------------|-------|--------|------|
| 2026-08-31 | 20:48 | Implement Online Serving Layer (Part 4); Fix Artifact Loading | ✅✅✅✅ | [#2026-08-31-2048](#2026-08-31-2048-session-summary) |
| 2026-08-31 | 20:37 | Verify Final Pipeline Execution; Clarify Architecture Choices | ✅✅ | [#2026-08-31-2037](#2026-08-31-2037-session-summary) |
| 2026-08-31 | 20:14 | Refactor Offline ML Pipeline; Fix Prefect & Sklearn issues | ✅ | [#2026-08-31-2014](#2026-08-31-2014-session-summary) |
| 2026-08-27 | 21:50 | Resolve Local Prefect DB Corruptions; Eliminate Target Leakage; Refactor Temporal Split to Ratios | ✅✅✅ | [#2026-08-27-2150](#2026-08-27-2150-session-summary) |
| 2026-08-27 | 15:07 | Verify Status and Update Spec Remote | ✅ | [#2026-08-27-1507](#2026-08-27-1507-session-summary) |
| 2026-08-27 | 15:05 | Create Base Dataset; Configure Git Ignore and Push | ✅✅ | [#2026-08-27-1505](#2026-08-27-1505-session-summary) |

# Entries

### <a name="2026-08-27-1505-session-summary"></a>[2026-08-27 15:05] Session Summary

**Duration:** ~35 minutes
**Overview:** This session focused on initializing the base dataset for the credit risk scoring system. We processed the raw LendingClub dataset based on project requirements, aligned DVC tracking, and secured the repository by preventing raw data tracking before pushing everything to GitHub.

**Goals:** 2 total — 2 done, 0 partial, 0 blocked

---

### Goal 1: Create Base Dataset

**Status:** ✅ Done

**Context:** The user wanted to create a new `dataset.csv` file using the accepted and rejected datasets based on the requirements in `spec.md`, and save the code in `notebook/dataset.ipynb`.

**Approach / Plan:** 
Initially, the user suggested using both the accepted and rejected datasets. After reviewing `spec.md` (which requires the `loan_status` target and `issue_d` for temporal splits), I proposed only using the accepted dataset, as the rejected dataset lacks these critical fields and reject inference would overcomplicate the scope. The user agreed. 
The plan was to load the accepted dataset, filter for 2016-2018 issuance, map `loan_status` to binary (Fully Paid vs Charged Off), and drop identified leakage columns. We also needed to rename the existing DVC pointer (`raw_applicants.csv.dvc`) to `dataset.csv.dvc` and update references in `spec.md`.

**Work Done:** 
- Created a Python script (`scratch/process_data.py`) to generate `notebook/dataset.ipynb` and process the data.
- Ran the script in the background to load the ~1.7GB `accepted_2007_to_2018Q4.csv` file.
- Generated `dataset.csv` with exactly 518,706 rows, perfectly aligning with the ~500K rows goal.
- Renamed `data/raw_applicants.csv.dvc` to `dataset.csv.dvc`.
- Updated `spec.md` to reference the new DVC pointer name.

**Errors & Issues:** 
- Initially encountered a schema validation error when calling `run_command` due to passing a string for `WaitMsBeforeAsync` instead of an integer. Fixed by correctly passing an integer.

**Files Touched:**
- `notebook/dataset.ipynb` — Created to store the data processing logic.
- `data/dataset.csv` — The generated clean dataset.
- `data/dataset.csv.dvc` — Renamed the DVC tracking file.
- `spec.md` — Updated documentation to reference `dataset.csv.dvc`.

**Outcome:** The dataset is fully processed, correctly sized, and documented.

### Goal 2: Configure Git Ignore and Push

**Status:** ✅ Done

**Context:** Before pushing the changes to the DagsHub DVC remote and GitHub, the user wanted to ensure `.csv` files were ignored by git.

**Approach / Plan:** Append a rule for `*.csv` files in the existing `.gitignore` and execute the standard git staging, commit, and push flow.

**Work Done:**
- Edited `.gitignore` to add a specific `# Data / DVC tracked files` section ignoring `*.csv`.
- Staged `.gitignore`, `spec.md`, `data/`, and `notebook/`.
- Committed with message "Add dataset processing notebook, update DVC pointer, and ignore csv files".
- Pushed changes to `origin/main` on GitHub.

**Errors & Issues:**
- None encountered.

**Files Touched:**
- `.gitignore` — Added `*.csv` exclusion rule.

**Outcome:** All work is safely committed and pushed to the remote repository, and large CSV files are prevented from accidentally entering git history.

---

### Open Threads / Next Steps
None at this time. The data pipeline foundation is set and tracked.

---

### <a name="2026-08-27-1507-session-summary"></a>[2026-08-27 15:07] Session Summary

**Duration:** ~5 minutes
**Overview:** This short session was focused on verifying the Git and DVC sync status, followed by committing and pushing a documentation update regarding the DVC remote configuration. Everything was found to be in sync and the updates were successfully pushed to GitHub.

**Goals:** 1 total — 1 done, 0 partial, 0 blocked

---

### Goal 1: Verify Status and Update Spec Remote

**Status:** ✅ Done

**Context:** The user checked if Git and DVC status were okay to ensure the workspace was clean. After making a clarification in `spec.md` about the DVC remote being a DagsHub S3 bucket, they requested to push the changes to GitHub.

**Approach / Plan:** Checked the Git working tree status to ensure everything was clean and in sync with the remote. After the user manually modified `spec.md`, the plan was to stage, commit, and push the changes. Initially, a broad `git add .` was attempted, but it was restricted to `spec.md` as per user instruction.

**Work Done:**
- Reviewed terminal outputs confirming DVC data and pipelines were up to date and in sync with `origin`.
- Ran `git status` which confirmed the `main` branch was clean and up to date.
- Staged `spec.md` explicitly.
- Committed with the message "docs: update spec data tracking to specify dagshub s3 bucket remote".
- Pushed the commit to `origin/main`.

**Errors & Issues:**
- `git add . ; git commit ...` command was denied execution by the user, who provided an alternative instruction to only push the changed file. This was resolved by specifically running `git add spec.md`.

**Files Touched:**
- `spec.md` — Updated the Data Tracking section to explicitly state the use of a DagsHub S3 bucket remote.

**Outcome:** Repository sync status was confirmed, and documentation was updated and pushed successfully.

---

### Open Threads / Next Steps
None at this time. The documentation is up to date and synced.

---

### <a name="2026-08-27-2150-session-summary"></a>[2026-08-27 21:50] Session Summary

**Duration:** ~45 minutes
**Overview:** This session focused on fixing local Prefect orchestration errors and deeply analyzing the dataset to remove severe target leakage that was artificially inflating model performance to 0.9999 AUC-PR. We also improved the data splitting logic to be dynamic and pushed the refined pipeline to GitHub.

**Goals:** 3 total — 3 done, 0 partial, 0 blocked

---

### Goal 1: Resolve Local Prefect DB Corruptions

**Status:** ✅ Done

**Context:** The user was blocked from running the training pipeline locally because Prefect kept crashing during initialization with an Alembic migration error (`Can't locate revision identified by 'f416ea180ae1'`). Later, after a pipeline run, another error popped up (`UNIQUE constraint failed`).

> **Pipeline Execution Notes (Windows / PowerShell):**
> 
> **Option 1: Running directly as a script**
> ```powershell
> $env:PYTHONPATH="."
> $env:PYTHONIOENCODING="utf-8"
> python src/training/flow.py
> ```
> - `$env:PYTHONPATH="."`: Adds the repository root to `sys.path` so imports like `from src.features.feature_pipeline import ...` resolve without `ModuleNotFoundError`.
> - `$env:PYTHONIOENCODING="utf-8"`: Prevents Windows PowerShell `UnicodeEncodeError` crashes when Prefect and MLflow log Unicode emojis/characters (e.g., 🏃, 🧪).
> 
> **Option 2: Running as a module (Recommended)**
> ```powershell
> $env:PYTHONIOENCODING="utf-8"
> python -m src.training.flow
> ```
> - Running with `python -m src.training.flow` automatically adds the current working directory to `sys.path`, eliminating the need to set `$env:PYTHONPATH="."` manually.

**Approach / Plan:** Both errors were caused by the local SQLite tracking database for Prefect (`~/.prefect/prefect.db`) being corrupted or out-of-sync due to version downgrading (Prefect 3 back to Prefect 2) and Windows concurrency quirks. Since this DB is purely for local metadata and not the remote MLflow tracking, the simple fix is to physically delete it.

**Work Done:**
- Attempted `prefect server database reset -y` but it failed.
- Instructed the user to run `Remove-Item -Force ~/.prefect/prefect.db`.
- The user successfully deleted the database, allowing the pipeline to execute smoothly.

**Errors & Issues:**
- `alembic.util.exc.CommandError: Can't locate revision identified by 'f416ea180ae1'`: Prefect 2 trying to read a Prefect 3 schema. Fixed by deleting DB.
- `sqlite3.IntegrityError: UNIQUE constraint failed`: Known Prefect `aiosqlite` concurrency bug on Windows. Fixed by deleting DB.

**Files Touched:**
- None.

**Outcome:** The orchestration layer was successfully stabilized for local development.

### Goal 2: Eliminate Target Leakage

**Status:** ✅ Done

**Context:** The user noticed both Logistic Regression and XGBoost were achieving impossibly high `0.9999` AUC-PR scores, with Logistic Regression barely winning out. The user asked for a deep dive to analyze the dataset and fix this.

**Approach / Plan:** Suspecting target leakage (future columns predicting the outcome), I wrote a scratch Python script to compute the Pearson correlation between all numeric columns and the `loan_status` target. I identified several post-origination columns with huge correlations. We needed to add these to the `leakage_cols` list in the config to drop them during feature engineering.

**Work Done:**
- Created and executed `scratch/find_leakage.py` to identify highly correlated features.
- Found `last_fico_range_high` (0.76), `last_fico_range_low` (0.63), `total_rec_prncp` (0.47), and several other payment tracking columns acting as target leaks.
- Updated `training_config.yaml` to explicitly drop these columns.
- Reran the pipeline and confirmed that AUC-PR dropped to a realistic `~0.43`, with XGBoost properly outperforming Logistic Regression.

**Errors & Issues:**
- Models initially tied near 1.0 AUC-PR due to leakage. Fixed by explicitly removing future data.

**Files Touched:**
- `config/training_config.yaml` — Expanded the `leakage_cols` list.

**Outcome:** The models are now learning genuine credit risk patterns rather than cheating by reading future payment values.

### Goal 3: Refactor Temporal Split to Ratios

**Status:** ✅ Done

**Context:** The dataset was previously split into train/val/test using hardcoded dates (`val_start: 2017-05-01`, etc.). The user correctly suggested that it would be more robust to sort the data chronologically and split it using percentage ratios.

**Approach / Plan:** We refactored `feature_pipeline.py` to sort the dataframe by `issue_d` in ascending order, calculate index boundaries based on user-defined ratios, and slice the dataframe accordingly.

**Work Done:**
- Modified `temporal_split` in `feature_pipeline.py` to use `val_ratio` and `test_ratio`.
- Replaced `split_dates` with `split_ratios` (0.7, 0.15, 0.15) in `training_config.yaml`.
- Updated `flow.py` to pass the ratio configuration to the splitting function.
- Successfully pushed all changes to GitHub using `git add`, `commit`, and `push`.

**Errors & Issues:**
- None.

**Files Touched:**
- `config/training_config.yaml` — Migrated to `split_ratios`.
- `src/features/feature_pipeline.py` — Implemented ratio-based slicing logic after chronological sorting.
- `src/training/flow.py` — Updated the function call arguments.

**Outcome:** The data splitting mechanism is now dynamic, preserving Out-Of-Time validation while being adaptable to new datasets. All code is tracked on GitHub.

---

### Open Threads / Next Steps
None at this time. The model is realistically evaluated, XGBoost is winning, and the pipeline is solid.

---

### <a name="2026-08-31-2014-session-summary"></a>[2026-08-31 20:14] Session Summary

**Duration:** ~2 hours
**Overview:** This session focused on refactoring the Offline ML Pipeline (Part 3) to make it production-ready. We migrated feature configuration to a central YAML file, introduced strict data validation with Pandera, bundled preprocessing steps using scikit-learn Pipelines, added offline SHAP dataset generation, and resolved several environment/execution bugs.

**Goals:** 1 total — 1 done, 0 partial, 0 blocked

---

### Goal 1: Refactor Offline ML Pipeline

**Status:** ✅ Done

**Context:** The user wanted to eliminate target leakage and ensure zero training-serving skew before building the online FastAPI layer. The codebase needed a robust configuration and strict schema validations.

**Approach / Plan:** We decided to extract feature names into `training_config.yaml`, use `pandera` to validate data immediately upon loading, and bundle `SimpleImputer` and `StandardScaler` with our estimators (`LogisticRegression` and `XGBClassifier`) into `sklearn.pipeline.Pipeline` objects. We also planned to pre-compute a SHAP background dataset to speed up online serving.

**Work Done:**
- Added `pandera` to dependencies and implemented `get_pandera_schema` with `strict='filter'`.
- Updated `train.py` to use `Pipeline`, properly prefixing `GridSearchCV` parameters with `classifier__`.
- Modified `flow.py` to include `validate_data_task` and generate/log a `shap_background.pkl` artifact.
- Successfully executed the training flow on a minimal grid search, then reverted to the full parameter grid for the final training run.
- Appended instructions on how to properly execute the training flow.

**Errors & Issues:**
- `sklearn.utils._param_validation.InvalidParameterError`: Older syntax `cv='prefit'` in `CalibratedClassifierCV` was deprecated and failed. Fixed by switching to `FrozenEstimator(model)`.
- `UnicodeEncodeError` regarding a runner emoji `\U0001f3c3` in MLflow when executing the training script on Windows. Fixed by explicitly setting the console encoding before running. **Note: To run the training flow safely, you must use:**
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  python -m src.training.flow
  ```
- `RuntimeError: main thread is not in main loop`: Matplotlib crashed at the end of the Prefect background task due to trying to launch a GUI. Fixed by adding `matplotlib.use('Agg')` in `evaluate.py`.

**Files Touched:**
- `config/training_config.yaml` — Migrated feature lists.
- `src/features/feature_pipeline.py` — Added Pandera validation.
- `src/training/train.py` — Wrapped models in `Pipeline`.
- `src/training/flow.py` — Orchestrated new tasks and SHAP generation.
- `src/training/evaluate.py` — Fixed `FrozenEstimator` and Matplotlib backend.
- `requirements.txt` — Added `pandera`.
- `spec.md` — Updated architectural plans.

**Outcome:** The offline pipeline is fully refactored, robust, and correctly tracked in MLflow. The winning XGBoost model is properly aliased as Staging.

---

### Open Threads / Next Steps
Begin implementation of the Online Serving Layer (FastAPI).

---

### <a name="2026-08-31-2037-session-summary"></a>[2026-08-31 20:37] Session Summary

**Duration:** ~25 minutes
**Overview:** This short follow-up session focused on verifying the success of the full-grid offline ML pipeline execution, and addressing user questions regarding model performance metrics (AUC-PR drop) and the necessity of certain YAML config blocks alongside Pandera validation.

**Goals:** 2 total — 2 done, 0 partial, 0 blocked

---

### Goal 1: Verify Final Pipeline Execution

**Status:** ✅ Done

**Context:** The final pipeline with the full XGBoost hyperparameter grid needed to be run to completion and registered to MLflow.

**Approach / Plan:** The user manually ran the flow via terminal (`$env:PYTHONIOENCODING="utf-8"; python -m src.training.flow`) and provided the log output. I reviewed the logs for any concerning anomalies or failures.

**Work Done:**
- Reviewed the pipeline trace which showed a clean execution.
- Verified XGBoost was selected as the winning model (learning_rate: 0.1, max_depth: 5, n_estimators: 200).
- Confirmed MLflow effectively registered `version 8` as `Staging`.
- Addressed minor warnings (Pydantic model namespace, Pandera import deprecation, and MLflow artifact path deprecation), clarifying that they are non-critical third-party notices.
- Drafted the `implementation_plan.md` for Part 4 (Online Serving API) to tee up the next session.

**Errors & Issues:**
- Non-critical deprecation warnings from `pydantic`, `pandera`, and `mlflow`. No pipeline breaks.

**Files Touched:**
- `implementation_plan.md` — Drafted plans for FastAPI serving layer.

**Outcome:** The offline training pipeline run is officially verified and completed.

### Goal 2: Clarify Architecture Choices

**Status:** ✅ Done

**Context:** The user had two specific questions regarding the current state of the pipeline:
1. Why the AUC-PR degraded to ~0.43 compared to a previous run from 18 hours ago (~0.71).
2. Why we kept `leakage_cols` in `training_config.yaml` when `pandera` already drops all unselected columns using `strict='filter'`.

**Approach / Plan:** Provide clear, context-aware explanations in chat without requiring code changes unless preferred by the user.

**Work Done:**
- Explained that the AUC-PR drop was due to successfully removing **Target Leakage**. The 0.71 run had illegal access to future payment information, whereas 0.43 represents an honest, robust baseline for origination-time credit risk prediction.
- Confirmed the user's observation that `leakage_cols` is functionally dead code because Pandera's `strict='filter'` acts as a strict allowlist. We agreed to keep the block in the YAML purely as explicit documentation/warning to future developers about which columns are known leaks.

**Errors & Issues:**
- None.

**Files Touched:**
- None.

**Outcome:** Clarified machine learning and architecture design decisions. User opted to retain the legacy config block for documentation purposes.

---

### Open Threads / Next Steps
Begin implementation of the Online Serving Layer (FastAPI) as documented in the new implementation plan.

---

### <a name="2026-08-31-2048-session-summary"></a>[2026-08-31 20:48] Session Summary

**Duration:** ~2.5 hours
**Overview:** This major session was dedicated to implementing the complete "Online Serving API" (Part 4 of the spec). We transitioned from offline modeling to a live scoring endpoint. Work included designing the API architecture, verifying external database connectivity (Supabase), building out the FastAPI application with custom correlation middleware, and robustly integrating the MLflow model and SHAP explainer into the FastAPI lifespan. We encountered and resolved significant artifact loading issues (pickle vs joblib, and NumPy vs DataFrame formats) to achieve a stable, production-ready server.

**Goals:** 4 total — 4 done, 0 partial, 0 blocked

---

### Goal 1: Plan Online Serving & Verify Database

**Status:** ✅ Done

**Context:** The user requested an implementation plan for Part 4 (Online Serving API) based on `spec.md`, explicitly asking to identify required `.env` variables, gap-analyze the spec, and ensure we learn from previous errors. Additionally, the user wanted to verify the Supabase PostgreSQL connection before proceeding.

**Approach / Plan:** 
I reviewed `spec.md` and created an `implementation_plan.md` that detailed the configuration, middleware, schemas, and main FastAPI app. I identified that `DAGSHUB_USER_TOKEN`, `MLFLOW_TRACKING_URI`, and `DATABASE_URL` were needed. The user provided a Supabase URL, and we wrote a scratch script to hit the database to confirm it was healthy.

**Work Done:**
- Created the comprehensive `implementation_plan.md` for Part 4.
- Wrote and executed `scratch/test_db.py` to test the Supabase connection string.
- Addressed user feedback to ensure the API receives allowed origins and model aliases dynamically from the environment.

**Problems Faced & Solutions:** No significant problems were encountered during planning.

**Files Touched:**
- `implementation_plan.md` — Documented the full Part 4 architecture.
- `scratch/test_db.py` — Verified Supabase connectivity.

**Outcome:** We achieved alignment on the API architecture and confirmed that our external logging database was reachable.

---

### Goal 2: Implement FastAPI App & Middleware

**Status:** ✅ Done

**Context:** With the plan approved, we needed to write the actual code for the serving layer, ensuring strong typing, observability, and adherence to the trained model's feature schema.

**Approach / Plan:** 
We built the app layer-by-layer: first configuration, then dynamic schemas (reading exactly what the model expects from `training_config.yaml`), then request ID middleware (for tracing), and finally the `main.py` router containing the `/score`, `/health`, and `/metrics` endpoints.

**Work Done:**
- Created `config/serving_config.yaml` and `src/serving/config.py` for environment parsing.
- Created `src/serving/schemas.py` using Pydantic's `create_model` to enforce the 77-feature numeric schema dynamically.
- Created `src/serving/middleware.py` utilizing `contextvars` to generate and inject a unique `X-Request-ID`.
- Authored `src/serving/main.py` implementing the FastAPI application, Prometheus metrics, and the model prediction logic.

**Problems Faced & Solutions:** No significant problems were encountered.

**Files Touched:**
- `config/serving_config.yaml`, `src/serving/config.py`, `src/serving/schemas.py`, `src/serving/middleware.py`, `src/serving/main.py` — Created the core serving application.
- `requirements.txt` — Added `fastapi`, `uvicorn`, `prometheus-fastapi-instrumentator`, and `httpx`.

**Outcome:** The FastAPI application was fully constructed and ready for startup testing.

---

### Goal 3: Fix Artifact Loading Issues

**Status:** ✅ Done

**Context:** When attempting to boot the FastAPI server locally using `uvicorn`, the application crashed during the `lifespan` startup phase while attempting to download and load the MLflow model and SHAP artifacts.

**Approach / Plan:** 
We had to debug two sequential startup crashes related to how the training pipeline saved artifacts versus how the serving pipeline loaded them.

**Work Done:**
- Replaced `pickle.load()` with `joblib.load()` in `main.py`.
- Updated `src/training/flow.py` to use `shap.sample(X_train, 100)` instead of `shap.kmeans` on preprocessed data.
- Ran `$env:PYTHONIOENCODING="utf-8"; python -m src.training.flow` to register the new model version (v9) to `Staging`.

**Problems Faced & Solutions:**

**Problem 1 — UnpicklingError**
- **Problem:** Uvicorn crashed with `_pickle.UnpicklingError` when loading `shap_background.pkl`.
- **Diagnosis:** The artifact was saved in `flow.py` using `joblib.dump()`, but `main.py` was attempting to load it using the standard `pickle.load()` module.
- **Solution:** Modified `src/serving/main.py` to import and use `joblib.load()`.
- **Result:** The server successfully loaded the file, moving us to the next error.
- **Root Cause / Lesson:** Symmetric serialization libraries must be used across the training and serving boundaries.

**Problem 2 — SHAP Explainer Initialization Crash**
- **Problem:** Uvicorn crashed with `Failed to load SHAP artifact: Specifying the columns using strings is only supported for dataframes.`
- **Diagnosis:** The MLflow model (a scikit-learn Pipeline) expects a raw Pandas DataFrame with string columns, but the background dataset was saved as a NumPy array.
- **Solution:** Modified `flow.py` to save a random sample of the raw Pandas DataFrame (`shap.sample(X_train, 100)`).
- **Result:** FastAPI `KernelExplainer` successfully loaded the artifact and calculated SHAP values mapped precisely to raw inputs.
- **Root Cause / Lesson:** When using SHAP `KernelExplainer` with a full sklearn Pipeline that relies on Pandas DataFrames, the background dataset must also be a Pandas DataFrame to preserve column names.

**Problem 3 — Missing Unicode Encodings in Plan**
- **Problem:** The implementation plan to fix the SHAP issue omitted `$env:PYTHONIOENCODING="utf-8"`, which would have caused Windows PowerShell to crash when MLflow printed emojis.
- **Diagnosis:** The user reviewed the plan and referred to `SESSION_LOG.md` to flag the missing encoding setting.
- **Solution:** Rewrote the implementation plan to prepend `$env:PYTHONIOENCODING="utf-8"` before all execution commands.
- **Result:** All scripts executed cleanly without `UnicodeEncodeError`.
- **Root Cause / Lesson:** Always apply the Unicode encoding fix on Windows when running MLflow scripts.

**Files Touched:**
- `src/serving/main.py` — Switched to `joblib`.
- `src/training/flow.py` — Updated SHAP background to raw DataFrame.

**Outcome:** The FastAPI server successfully completes its lifespan startup routine and connects to MLflow.

---

### Goal 4: Verify API Contract

**Status:** ✅ Done

**Context:** With the server theoretically stable, we needed mathematical proof that the endpoints satisfy the contract established in `spec.md`.

**Approach / Plan:** 
Write a suite of `pytest` automated tests that utilize FastAPI's `TestClient` to hit the `/health` and `/score` endpoints, verifying response structures and HTTP codes.

**Work Done:**
- Authored `tests/test_api_contract.py`.
- Executed `$env:PYTHONIOENCODING="utf-8"; pytest tests/test_api_contract.py`.

**Problems Faced & Solutions:** No significant problems were encountered. The tests passed (`4 passed`) on the first run after the SHAP fix was applied.

**Files Touched:**
- `tests/test_api_contract.py` — Created test suite.

**Outcome:** We confirmed the `/score` endpoint correctly returns a probability, decision, request ID, and properly mapped `shap_values`. The Online Serving Layer is fully operational locally.

---

### Open Threads / Next Steps
The Online Serving API is complete. The next logical step according to `spec.md` is to implement the monitoring and prediction logging pipelines (Part 5) to write live traffic to the Supabase database.

---
