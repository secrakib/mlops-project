# Index

| Date | Session Time | Goals | Status | Jump |
|------|---------------|-------|--------|------|
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

**Context:** The user was blocked from running the training pipeline locally (`python src/training/flow.py`) because Prefect kept crashing during initialization with an Alembic migration error (`Can't locate revision identified by 'f416ea180ae1'`). Later, after a pipeline run, another error popped up (`UNIQUE constraint failed`).

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
