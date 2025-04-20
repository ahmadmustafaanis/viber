#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI tool to analyze a repository, generate a directory tree,
extract Python definitions, and prepare for docstring generation.
"""

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

import openai


# --- Placeholder for LLM Interaction ---
# Replace this function with actual calls to your chosen LLM API
# (e.g., OpenAI, Anthropic, local Llama)
def generate_docstring_llm(function_signature: str, code_context: str = "") -> str:
    """
    Placeholder function to simulate LLM docstring generation.

    Args:
        function_signature: The function definition line (e.g., "def my_func(a, b):").
        code_context: Optional surrounding code or class context.

    Returns:
        A placeholder docstring.
    """
    print(f"      [INFO] Simulating LLM call for: {function_signature.strip()}")
    # --- LLM API Call Start ---
    # Example using OpenAI (requires `pip install openai` and API key setup)
    # try:
    #     import openai
    #     # Ensure your OPENAI_API_KEY environment variable is set
    #     # openai.api_key = "YOUR_API_KEY"
    #
    prompt = (
        f"Generate a concise Python docstring (triple quotes) for the following function signature, "
        f"considering the potential context:\n\n"
        f"Context:\n{code_context}\n\n"
        f"Function Signature:\n{function_signature}\n\n"
        f"Docstring:"
    )
    #
    response = openai.chat.completions.create(
        model="gpt-4.1",  # Or another suitable model
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant generating Python docstrings.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.5,
    )
    docstring = response.choices[0].message.content.strip()
    #     # Basic validation/cleanup
    if not docstring.startswith('"""') or not docstring.endswith('"""'):
        docstring = f'"""\n    {docstring}\n    """'
    return docstring
    # except ImportError:
    #     print("      [WARN] OpenAI library not installed. Skipping actual LLM call.")
    #     return '"""\n    [LLM Placeholder] Docstring generation requires an LLM API call.\n    Replace the `generate_docstring_llm` function.\n    """'
    # except Exception as e:
    #     print(f"      [ERROR] LLM API call failed: {e}")
    #     return f'"""\n    [LLM Error] Failed to generate docstring: {e}\n    """'
    # --- LLM API Call End ---


def get_tree_structure(repo_path: Path) -> str:
    """
    Generates the directory tree structure using the 'tree' command.

    Args:
        repo_path: Path object for the repository root.

    Returns:
        The tree structure string or an error message.
    """
    try:
        # Use '-a' to include hidden files, '-L' to limit depth (optional),
        # '--noreport' to suppress the final count line.
        # Adjust depth (-L) as needed, or remove for full tree.
        result = subprocess.run(
            ["tree", "-a", "--noreport"],  # Add '-L 3' for depth limit e.g.
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout
    except FileNotFoundError:
        return "[Error] 'tree' command not found. Please install it (e.g., 'sudo apt install tree' or 'brew install tree')."
    except subprocess.CalledProcessError as e:
        return f"[Error] 'tree' command failed: {e.stderr}"
    except Exception as e:
        return f"[Error] Failed to get tree structure: {e}"


def extract_definitions(py_file_path: Path) -> list[tuple[str, str, str]]:
    """
    Parses a Python file and extracts class and function definitions using AST.

    Args:
        py_file_path: Path object for the Python file.

    Returns:
        A list of tuples: (type, definition_line, class_context).
        Type is 'class' or 'function'.
        Class_context is the name of the containing class for methods, else None.
    """
    definitions = []
    try:
        with open(py_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(py_file_path))
            lines = content.splitlines()

            for node in ast.walk(tree):
                class_context = None
                # Find containing class for methods
                parent = getattr(node, "parent", None)
                while parent:
                    if isinstance(parent, ast.ClassDef):
                        class_context = parent.name
                        break
                    parent = getattr(parent, "parent", None)

                if isinstance(node, ast.FunctionDef):
                    # Get the full definition line from the source
                    start_lineno = node.lineno
                    end_lineno = node.body[0].lineno if node.body else start_lineno
                    # Heuristic to capture the signature line(s), might need refinement for complex multiline signatures
                    signature_lines = lines[start_lineno - 1 : end_lineno - 1]
                    signature = " ".join(
                        line.strip()
                        for line in signature_lines
                        if line.strip().startswith("def") or line.strip().endswith(":")
                    ).strip()
                    if not signature.startswith(
                        "def "
                    ):  # Ensure it looks like a function def
                        signature = lines[
                            start_lineno - 1
                        ].strip()  # Fallback to single line

                    definitions.append(("function", signature, class_context))

                elif isinstance(node, ast.ClassDef):
                    # Get the class definition line
                    start_lineno = node.lineno
                    # Heuristic for class definition line
                    signature = lines[start_lineno - 1].strip()
                    definitions.append(
                        ("class", signature, None)
                    )  # No class context for a class itself

            # Assign parent nodes for context lookup (simple approach)
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    child.parent = node

    except FileNotFoundError:
        print(
            f"  [WARN] File not found during parsing: {py_file_path}", file=sys.stderr
        )
    except SyntaxError as e:
        print(f"  [WARN] Syntax error parsing {py_file_path}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"  [ERROR] Failed to parse {py_file_path}: {e}", file=sys.stderr)
    return definitions


def main():
    """Main function to orchestrate the repository analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze a repository, create viber.txt with tree structure, "
        "Python definitions, and LLM docstring placeholders."
    )
    parser.add_argument(
        "--repo_path",
        type=str,
        help="Path to the target repository directory.",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    # viber_file_path = repo_path / "viber.txt"
    viber_file_path = Path("viber.txt").resolve()

    if not repo_path.is_dir():
        print(f"Error: Path '{repo_path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    if viber_file_path.exists():
        print(
            f"Info: '{viber_file_path.name}' already exists in '{repo_path}'. Skipping creation."
        )
        # Optional: Add logic here to overwrite or update if needed
        # e.g., ask the user or add a --force flag
        sys.exit(0)

    print(f"Analyzing repository: {repo_path}")
    print(f"Creating '{viber_file_path.name}'...")

    try:
        with open(viber_file_path, "w", encoding="utf-8") as vf:
            # 1. Add Tree Structure
            print("Generating directory tree...")
            tree_output = get_tree_structure(repo_path)
            vf.write("=" * 80 + "\n")
            vf.write("DIRECTORY TREE STRUCTURE\n")
            vf.write("=" * 80 + "\n\n")
            vf.write(tree_output)
            vf.write("\n\n")

            # 2. Find and Process Python Files
            print("Finding and processing Python files...")
            vf.write("=" * 80 + "\n")
            vf.write("PYTHON FILE DEFINITIONS & DOCSTRINGS\n")
            vf.write("=" * 80 + "\n\n")

            python_files_found = False
            for root, _, files in os.walk(repo_path):
                # Skip common virtual environment folders and __pycache__
                root_path = Path(root)
                if any(
                    part
                    in [
                        ".git",
                        ".vscode",
                        ".idea",
                        "venv",
                        "env",
                        ".env",
                        "__pycache__",
                        "node_modules",
                        "build",
                        "dist",
                    ]
                    for part in root_path.relative_to(repo_path).parts
                ):
                    continue

                for file in files:
                    if file.endswith(".py"):
                        python_files_found = True
                        py_file_path = Path(root) / file
                        relative_path = py_file_path.relative_to(repo_path)
                        print(f"  Processing: {relative_path}")

                        vf.write("-" * 60 + "\n")
                        vf.write(f"File: {relative_path}\n")
                        vf.write("-" * 60 + "\n\n")

                        definitions = extract_definitions(py_file_path)

                        if not definitions:
                            vf.write("  (No classes or functions found)\n\n")
                            continue

                        # Read file content once for context if needed by LLM
                        try:
                            with open(py_file_path, "r", encoding="utf-8") as f_content:
                                file_content_for_context = f_content.read()
                        except Exception:
                            file_content_for_context = ""  # Handle read errors

                        for def_type, signature, class_context in definitions:
                            context_info = (
                                f" (in class {class_context})" if class_context else ""
                            )
                            vf.write(f"{def_type.capitalize()}{context_info}:\n")
                            vf.write(f"  {signature}\n")

                            if def_type == "function":
                                # 3. Generate and add docstring (using placeholder)
                                # Pass signature and potentially some context
                                docstring = generate_docstring_llm(
                                    signature, code_context=file_content_for_context
                                )
                                # Indent the docstring
                                indented_docstring = "\n".join(
                                    ["    " + line for line in docstring.splitlines()]
                                )
                                vf.write(f"{indented_docstring}\n\n")
                            else:
                                vf.write("\n")  # Add space after class definition

            if not python_files_found:
                vf.write("(No Python files found in the repository)\n")

        print(f"\nAnalysis complete. Output written to '{viber_file_path}'")
        print("\nNOTE: Docstrings were generated using a placeholder.")
        print("      You need to edit the script's `generate_docstring_llm` function")
        print("      to integrate with a real LLM API (e.g., OpenAI, Llama).")

    except IOError as e:
        print(
            f"Error: Could not write to file '{viber_file_path}': {e}", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Add parent node tracking to AST nodes for context lookup
    # This needs to be done before ast.walk if used within extract_definitions
    # However, the current implementation does context lookup differently.
    # Keeping this note for alternative AST strategies.
    # def setup_parents(tree):
    #     for node in ast.walk(tree):
    #         for child in ast.iter_child_nodes(node):
    #             child.parent = node
    # # Call setup_parents(tree) after ast.parse if using parent pointers extensively

    main()
