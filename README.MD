## Viber: Repository Analysis CLI Tool

![Viber Logo](viber.jpeg)
**Viber** is a command-line interface (CLI) tool designed to analyze a local code repository, generate a directory tree, extract Python class and function definitions, and scaffold placeholder docstrings using a language model API. Currently, Viber outputs a `viber.txt` report file, and future enhancements will include an agentic Q\&A workflow and automated code updates.

---

### Features

* **Directory Tree Generation**: Uses the `tree` command to produce a visual listing of all files and directories in the target repository.
* **Python Definition Extraction**: Parses `.py` files to identify `class` and `def` statements via the AST (Abstract Syntax Tree).
* **Docstring Scaffolding**: Integrates with an LLM API (placeholder implementation) to generate initial docstring templates for every function.
* **Configurable Exclusions**: Skips common folders like `.git`, virtual environments, cache directories, and build artifacts.

---

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/viber.git
   cd viber
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure prerequisites**

   * Python 3.8 or higher
   * `tree` command available (`sudo apt install tree` or `brew install tree`)
   * (Optional) OpenAI Python client if you plan to integrate real LLM calls

---

### Usage

```bash
python viber.py --repo_path /path/to/your/repo
```

* **`--repo_path`**: Path to the repository root to analyze.
* The tool will create a `viber.txt` in the current working directory with the analysis report.

#### Sample Output Structure (`viber.txt`)

```
================================================================================
DIRECTORY TREE STRUCTURE
================================================================================

<tree output here>

================================================================================
PYTHON FILE DEFINITIONS & DOCSTRINGS
================================================================================

------------------------------------------------------------
File: src/module/example.py
------------------------------------------------------------
Class:
  class Example:

Function:
  def foo(a, b):
    """
    Generated docstring placeholder
    """
```

---

### Configuration & Customization

* Edit `generate_docstring_llm` in `viber.py` to connect to your preferred LLM API:

  * Install the OpenAI client
  * Set the `OPENAI_API_KEY` environment variable
  * Adjust the `model` and `temperature` parameters as desired

---

### Roadmap

* [ ] **Agentic Q\&A Workflow**: Integrate an interactive agent that can answer repository-specific questions and guide users through code insights.
* [ ] **Automatic Code Updates**: Implement in-place insertion of generated docstrings and optional code refactoring based on LLM suggestions.
* [ ] Configuration file support for custom ignore patterns and depth limits.
* [ ] Multi-language support (beyond Python).

---

### Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

Please adhere to the existing style and add tests for new functionality.

---

### License

MIT License. See [LICENSE](LICENSE) for details.
