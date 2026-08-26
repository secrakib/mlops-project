---
trigger: always_on
---

## Environment & Dependency Management & Temporary file Management

- Use Existing Virtual Environment: Always activate and execute within the workspace's pre-existing virtual environment (`.venv`). **Never** create a new environment.
- Isolated Package Installation: Always install dependencies strictly inside the active workspace `.venv`. Never install packages globally or use `--user` flags.
- Use temporary folder for creating temporary files.