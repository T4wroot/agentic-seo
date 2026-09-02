# Contributing to Agentic SEO

Thank you for your interest in contributing to **Agentic SEO**! 🎉

We welcome contributions of all kinds: new sub-skills, performance optimizations, bug fixes, documentation improvements, translation into other languages, and feature suggestions.

---

## 🛠️ Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/agentic-seo.git
   cd agentic-seo
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify repository inventory:**
   ```bash
   python3 scripts/validate_skill_inventory.py
   python3 scripts/reference_freshness.py resources/references --max-age-days 90
   ```

---

## 📂 Project Structure

- `SKILL.md`: Main entrypoint skill definition for AI agents.
- `skills/`: Sub-skill modules and native IDE format definitions.
- `scripts/`: Python audit, crawling, analysis, and validation scripts.
- `resources/`: Agents, templates, and reference documentation.
- `docs/`: Guides, visual assets, and screenshots.

---

## 📝 Contribution Guidelines

1. **Branch Naming**: Use descriptive branch names like `feature/new-subskill`, `fix/schema-validator`, or `docs/fa-guide`.
2. **Deterministic Evidence**: All automated audit checks should produce structured JSON outputs alongside user-facing markdown.
3. **Keep Inventory Synced**: When adding scripts or skills, update `SKILL.md`, `README.md`, and run `scripts/validate_skill_inventory.py`.
4. **Pull Requests**: Provide a clear description of what changed and why in the PR template.

---

## 💬 Questions & Community

Feel free to open an issue or start a discussion for any questions!
