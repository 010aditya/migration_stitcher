
# 🛠️ Migration Assist Post-Processor Tool

This tool enhances the output of class-by-class LLM migrations (e.g., EJB, Struts, JSP → Spring Boot) to generate a fully buildable and production-grade Spring Boot application.

## 🚀 Features

| Category | Capability |
|---------|------------|
| 🔧 Build Setup | Auto-generates or fixes `build.gradle` using:<br>• legacy `pom.xml`<br>• imported annotations<br>• reference Spring Boot apps |
| 🧠 Context Stitching | Combines legacy code, migrated code, enterprise framework, and semantically matched reference code |
| 🛠 Fix Agent | Fixes broken class and method references, regenerates code via GPT with full stitched context |
| ✨ Completion Agent | Adds missing methods, logic, boilerplate using LLM + legacy/ref pair |
| 🔍 GPT Retry Cycle | Automatically retries failed files with LLM + fix history tracking |
| 🧪 Build Validation | Compiles the project using Gradle and extracts build errors |
| 🔁 Gradle Fixing | Patches `build.gradle` based on build logs (missing dependencies, plugins, etc.) |
| 🧽 Markdown Cleanup | Strips ```java and ``` from generated files to ensure compilation |
| 🔗 Class + Method Linking | Rewires incorrect service/repository/controller names and method calls |
| 🤝 Reference Matching | Uses `reference_dir` to surface real-world example mappings via embeddings |
| 📊 Logging & Reports | Stores fix history, retry logs, method/class resolution notes, and full output trace |

## 📂 Directory Structure

```
project-root/
├── cli.py
├── agents/
│   ├── fix_and_compile.py
│   ├── completion_agent.py
│   ├── gradle_setup_agent.py
│   ├── retry_agent.py
│   ├── context_stitcher.py
│   ├── reference_promoter.py
│   └── fix_history_logger.py
├── data/
│   ├── mapping.json               # Required input
│   └── reference_embeddings.json  # Auto-generated
├── logs/
│   ├── fix_history/               # JSON log per file
│   └── build_output.log           # Last Gradle output
├── migration_report.json          # Summary of entire migration process
```

## ✅ Inputs Required

| Flag | Description |
|------|-------------|
| `--legacy` | Path to legacy codebase |
| `--migrated` | Output from Migration Assist |
| `--map` | `mapping.json` containing file mappings |
| `--reference` | Folder of reference legacy/migrated apps |
| `--enterprise` | Optional shared enterprise framework (common services, utils, etc.) |

## 🧪 Outputs Generated

| File/Folder | Description |
|-------------|-------------|
| `build.gradle` | Fully working gradle config (in `--migrated` dir) |
| `settings.gradle` | Auto-generated if missing |
| `gradlew`, `gradlew.bat`, `gradle-wrapper.properties` | Added if needed |
| `logs/fix_history/*.json` | Per-file log of fixes and completions |
| `migration_report.json` | Summary status of all files, fix types, retry count |
| `data/reference_embeddings.json` | Semantic embedding cache (auto-created) |
| Cleaned `.java` files | All ```java markdown blocks removed post-generation |

## 🧠 How It Works (Simplified Flow)

```
mapping.json ─┐
              ├─> ContextStitcherAgent ─┬─> FixAndCompileAgent ─┐
legacy code ──┘                         │                       │
                                        │                       ├─> RetryAgent
reference_dir ──> ReferencePromoterAgent┘                       │
                                                                │
migrated code ─────────────────────────────────────────────────┘
```

## 🔄 Example CLI Command

```bash
python cli.py \
  --legacy legacy_codebase/ \
  --migrated migration_output/ \
  --map data/mapping.json \
  --reference reference_dir/ \
  --enterprise shared_framework/
```

## 🔐 Environment

Create a `.env` file:

```env
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o
```

## ✅ Setup (for Local Use)

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 📌 Fix Types Logged

Each file’s fix history may include:

- `broken_class_ref`: Wrong or missing service/repo injected
- `method_name_mismatch`: Method call didn't match actual method
- `missing_method_stub`: Method inferred but not implemented
- `gpt_completion`: File logic completed by LLM
- `build_gradle_patch`: Missing dependency/plugin fixed
