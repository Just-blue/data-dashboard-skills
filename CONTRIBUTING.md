# Add a dashboard

Create `skills/<dashboard-name>/` using a descriptive lowercase hyphenated name. Keep everything needed to run or install that dashboard inside its folder:

- `SKILL.md`: name/description and agent workflow; state required inputs and limitations.
- `README.md` (and translations when available): standalone setup and runnable examples.
- `scripts/`, `assets/`, `references/`: implementation and resources actually used.
- A dependency file, `tests/`, `LICENSE` and third-party notices as applicable.

Do not import another dashboard's private modules or depend on a developer's filesystem. Bundle redistributable assets with their license. Use synthetic examples, label them, and exclude generated output and credentials. Publish only implemented dashboards in the root catalog.

Update both root README catalogs and the third-party notices index. Add the dashboard to `.github/workflows/tests.yml` with its own dependencies and test command; different runtimes may need separate jobs. Run its tests and the collection installer tests. Verify installation in a temporary directory so it cannot overwrite a personal skill.

The root installer discovers `skills/*/SKILL.md` and copies one folder. Runtime dependencies are managed by each dashboard. A new shared framework is unnecessary unless actual common requirements justify it.

Code/documentation use the repository MIT license. Include a copy within each skill so a standalone install preserves attribution. Third-party assets retain their own licenses.
