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
import json # Added import

import openai


# --- Placeholder for LLM Interaction ---
# Replace this function with actual calls to your chosen LLM API
# (e.g., OpenAI, Anthropic, local Llama)

# --- Helper function for building LLM messages ---
def _build_llm_messages(
    system_prompt_content: str, 
    user_prompt_initial_sections: list[str], 
    chat_history: list[dict], 
    user_question_section: str, 
    user_prompt_final_sections: list[str] = None
) -> list[dict]:
    """
    Constructs the 'messages' list for LLM API calls.
    """
    user_prompt_parts = list(user_prompt_initial_sections)

    # Append Chat History
    user_prompt_parts.append("\n--- Conversation History ---")
    if chat_history:
        for message in chat_history:
            user_prompt_parts.append(f"{message['role']}: {message['content']}")
    else:
        user_prompt_parts.append("(No previous conversation history)")
    user_prompt_parts.append("--- End of Conversation History ---")

    # Append User Question Section
    user_prompt_parts.append(user_question_section)

    # Append Final Sections
    if user_prompt_final_sections:
        user_prompt_parts.extend(user_prompt_final_sections)
    
    final_user_prompt = "\n".join(user_prompt_parts)
    
    return [
        {"role": "system", "content": system_prompt_content},
        {"role": "user", "content": final_user_prompt}
    ]

# --- Placeholder Q&A functions ---
def handle_qa_session(user_question: str, viber_txt_content: str, repo_path: Path, chat_history: list[dict]) -> str:
    """
    Orchestrates the Q&A process by:
    1. Getting relevant code references from viber.txt content.
    2. Reading the content of those references.
    3. Generating an answer based on all available information.
    """
    print("  [Agent] Okay, I need to figure out which files might be relevant...")
    code_references = get_relevant_code_references_llm(viber_txt_content, user_question, chat_history)
    # print(f"    [DEBUG] References found: {code_references}") # Optional debug

    retrieved_code = ""
    if code_references:
        print(f"  [Agent] I've identified {len(code_references)} potential file(s)/reference(s). Reading them now...")
        retrieved_code_content = read_code_from_references(repo_path, code_references)
        
        # Check if read_code_from_references returned actual code or a message
        # Common messages from read_code_from_references indicating no actual code:
        no_code_messages = [
            "No code references provided to read.", # Should not happen if code_references is true
            "No code content could be retrieved based on the references. Files might be missing, outside the repository, or unreadable."
        ]

        if retrieved_code_content in no_code_messages or not retrieved_code_content.strip():
            print("  [Agent] I found references, but couldn't retrieve any actual code content from them. Proceeding without specific code snippets.")
            retrieved_code = "" # Ensure it's an empty string
        else:
            retrieved_code = retrieved_code_content
            # Simple way to count snippets based on current formatting
            snippet_count = len(retrieved_code.split("--- Content from:")) - 1 
            print(f"  [Agent] Successfully read {snippet_count} code snippet(s).")
            # print(f"    [DEBUG] Retrieved code:\n{retrieved_code[:500]}...") # Optional debug
    else:
        print("  [Agent] I couldn't identify specific code files for your question from viber.txt. I'll try to answer based on the general information and chat history.")
        retrieved_code = "" # Ensure it's an empty string

    print("  [Agent] Now, I'm formulating an answer...")
    answer = get_answer_llm(user_question, viber_txt_content, retrieved_code, chat_history)
    
    return answer

def get_relevant_code_references_llm(viber_txt_content: str, user_question: str, chat_history: list[dict]) -> list[dict]:
    """
    Identifies relevant files and entities (functions/classes) from viber.txt
    content based on a user question and chat history using an LLM.

    Args:
        viber_txt_content: The string content of viber.txt.
        user_question: The user's current question.
        chat_history: A list of previous conversation turns.

    Returns:
        A list of dictionaries, where each dictionary represents a relevant file
        and its entities. Returns an empty list if no relevant files are found
        or in case of an error.
    """
    system_prompt = """
You are an expert code analysis assistant. Your task is to identify the specific files and, if applicable, function or class names within a software repository that are most relevant to answering a user's question. You will be given the content of 'viber.txt', which includes a directory tree and summaries of Python definitions. You will also receive the user's current question and the conversation history.

Your goal is to output a JSON object with two keys:
1.  "rationale": A brief explanation (1-2 sentences) of why you are selecting these files/entities.
2.  "files": A list of objects, where each object has:
    *   "path": The relative file path from the repository root (e.g., "src/main.py").
    *   "entities": A list of strings, where each string is a function name (e.g., "my_function") or a class name (e.g., "MyClass") from that file. If the whole file is relevant, or if you are unsure about specific entities, provide an empty list [].

Only list files that exist according to the 'viber.txt' directory tree.
Do not hallucinate file paths or entities.
If no specific files or entities seem relevant, or if the question is not about the code, you can return an empty list for "files".
"""

    initial_sections = [
        "Here is the content of 'viber.txt', which describes the repository structure and available Python definitions:",
        "--- viber.txt content ---",
        viber_txt_content,
        "--- end of viber.txt content ---",
        "\nGiven the viber.txt content, the current conversation history, and the user's question, please identify the most relevant code references."
        # Note: The chat history block will be added by the helper.
    ]
    
    question_section = f"\nUser Question: \"{user_question}\""
    
    final_sections = [
        "\nPlease return your response as a JSON object with 'rationale' and 'files' keys as described in the system prompt."
    ]

    messages = _build_llm_messages(
        system_prompt_content=system_prompt, # system_prompt is the existing variable name
        user_prompt_initial_sections=initial_sections,
        chat_history=chat_history,
        user_question_section=question_section,
        user_prompt_final_sections=final_sections
    )

    try:
        print("      [INFO] Calling LLM to get relevant code references...")
        # print(f"      [DEBUG] System Prompt: {system_prompt}") # For debugging
        # print(f"      [DEBUG] User Prompt built by helper: {messages[1]['content']}") # For debugging
        
        response = openai.chat.completions.create(
            model="gpt-4o", # Using gpt-4o as recommended
            messages=messages, # Use messages from helper
            response_format={"type": "json_object"},
            max_tokens=1000, # Increased max_tokens
            temperature=0.2,
        )
        
        response_content = response.choices[0].message.content
        # print(f"      [DEBUG] LLM raw response: {response_content}") # For debugging

        try:
            data = json.loads(response_content)
            if isinstance(data, dict) and "files" in data and isinstance(data["files"], list):
                # Basic validation for items within "files" list
                validated_files = []
                for item in data["files"]:
                    if isinstance(item, dict) and "path" in item and "entities" in item:
                        if isinstance(item["path"], str) and isinstance(item["entities"], list):
                            validated_files.append(item)
                        else:
                            print(f"      [WARN] Invalid item structure in 'files' list: {item}", file=sys.stderr)
                    else:
                        print(f"      [WARN] Invalid item in 'files' list (missing 'path' or 'entities'): {item}", file=sys.stderr)
                
                if "rationale" in data:
                    print(f"      [INFO] LLM Rationale: {data['rationale']}")
                else:
                    print("      [WARN] 'rationale' key missing from LLM response.", file=sys.stderr)

                return validated_files
            else:
                print(f"      [ERROR] LLM response JSON structure is invalid. Expected dict with 'files' list, got: {type(data)}", file=sys.stderr)
                print(f"      [DEBUG] Invalid JSON data: {data}", file=sys.stderr)
                return []
        except json.JSONDecodeError as e:
            print(f"      [ERROR] Failed to decode LLM response as JSON: {e}", file=sys.stderr)
            print(f"      [DEBUG] Raw response content that failed parsing: {response_content}", file=sys.stderr)
            return []

    except openai.APIError as e:
        print(f"      [ERROR] OpenAI API error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"      [ERROR] An unexpected error occurred in get_relevant_code_references_llm: {e}", file=sys.stderr)
        return []

def read_code_from_references(repo_path: Path, code_references: list[dict]) -> str:
    """
    Reads the content of files specified in code_references from the repository.

    Args:
        repo_path: The absolute Path object for the root of the repository.
        code_references: A list of dictionaries, where each dictionary
                         should have a "path" key (relative file path) and
                         an optional "entities" key (list of strings).

    Returns:
        A string containing the concatenated content of the referenced files,
        each preceded by a header. Returns a message if no content is retrieved.
    """
    retrieved_code_parts = []
    resolved_repo_path = repo_path.resolve() # Resolve once for reliable comparison

    if not code_references:
        return "No code references provided to read."

    for reference in code_references:
        file_path_str = reference.get("path")
        if not file_path_str:
            print("      [WARN] Skipping reference due to missing 'path'.", file=sys.stderr)
            continue

        absolute_file_path = resolved_repo_path.joinpath(file_path_str).resolve()

        # Security Check: Ensure the file is within the repository
        if not str(absolute_file_path).startswith(str(resolved_repo_path)):
            print(
                f"      [WARN] Skipping '{file_path_str}' as it's outside the repository path: '{absolute_file_path}'",
                file=sys.stderr
            )
            continue
        
        if not absolute_file_path.is_file():
            print(f"      [WARN] File not found or is not a file: {absolute_file_path}", file=sys.stderr)
            continue

        try:
            content = absolute_file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"      [WARN] Could not read file {absolute_file_path}: {e}", file=sys.stderr)
            continue

        entities = reference.get("entities", [])
        if entities:
            header = f"--- Content from: {file_path_str} (Entities requested: {', '.join(entities)}) ---\n"
        else:
            header = f"--- Content from: {file_path_str} ---\n"
        
        retrieved_code_parts.append(header)
        retrieved_code_parts.append(content)
        retrieved_code_parts.append("\n\n") # Two newlines for separation

    if not retrieved_code_parts:
        return "No code content could be retrieved based on the references. Files might be missing, outside the repository, or unreadable."
    
    return "".join(retrieved_code_parts)

def get_answer_llm(user_question: str, viber_txt_content: str, retrieved_code: str, chat_history: list[dict]) -> str:
    """
    Generates an answer to a user's question using an LLM, based on
    viber.txt content, retrieved code snippets, and chat history.

    Args:
        user_question: The user's current question.
        viber_txt_content: The string content of viber.txt.
        retrieved_code: String containing specific code snippets relevant to the question.
        chat_history: A list of previous conversation turns.

    Returns:
        A string containing the LLM's answer, or an error message.
    """
    system_prompt = """
You are a knowledgeable and helpful AI assistant. Your task is to answer questions about a software repository.
You will be provided with:
1.  An overview of the repository structure and Python definitions (from 'viber.txt').
2.  Specific code snippets that have been deemed relevant to the user's question.
3.  The history of the current conversation.
4.  The user's current question.

Please synthesize all this information to provide a clear, concise, and accurate answer.
When referring to specific code, try to mention the file path or function/class names if they are available in the provided snippets.
If the provided code snippets are insufficient or don't seem relevant to the question, acknowledge that in your answer.
Do not make up information if it's not present in the provided context.
"""

    initial_sections = [
        "Here is an overview of the repository from 'viber.txt':",
        "--- viber.txt content ---",
        viber_txt_content,
        "--- end of viber.txt content ---",
        "\nHere are specific code snippets retrieved that might be relevant:",
        "--- Retrieved Code Snippets ---",
        retrieved_code if retrieved_code.strip() else "(No specific code snippets were retrieved or provided for this question)",
        "--- End of Retrieved Code Snippets ---"
        # Note: The chat history block will be added by the helper.
    ]
    
    # This includes the specific framing text for the question
    question_section = f"\nPlease answer the following question based on all the provided information:\nUser Question: \"{user_question}\""

    messages = _build_llm_messages(
        system_prompt_content=system_prompt, # system_prompt is the existing variable name
        user_prompt_initial_sections=initial_sections,
        chat_history=chat_history,
        user_question_section=question_section,
        user_prompt_final_sections=None # No final sections for this LLM call
    )

    try:
        print("      [INFO] Calling LLM to get answer...")
        # print(f"      [DEBUG] System Prompt for get_answer_llm: {system_prompt}") # For debugging
        # print(f"      [DEBUG] User Prompt for get_answer_llm built by helper: {messages[1]['content']}") # For debugging

        response = openai.chat.completions.create(
            model="gpt-4o", 
            messages=messages, # Use messages from helper
            max_tokens=1500, 
            temperature=0.5, # Using 0.5 as a balance
        )
        
        answer = response.choices[0].message.content
        return answer.strip()

    except openai.APIError as e:
        print(f"      [ERROR] OpenAI API error in get_answer_llm: {e}", file=sys.stderr)
        return "Error: Could not get an answer from the LLM due to an API issue."
    except Exception as e:
        print(f"      [ERROR] An unexpected error occurred in get_answer_llm: {e}", file=sys.stderr)
        return "Error: An unexpected issue occurred while trying to get an answer."
# --- End Placeholder Q&A functions ---
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
        "Python definitions, and LLM docstring placeholders, or run Q&A mode."
    )
    parser.add_argument(
        "--repo_path",
        type=str,
        help="Path to the target repository directory. Required for generation and Q&A mode.",
    )
    parser.add_argument(
        "--qa", action="store_true", help="Enable interactive Q&A mode."
    )
    args = parser.parse_args()

    if args.qa:
        # QA Mode
        viber_file_path_qa = Path("viber.txt").resolve()

        if not args.repo_path:
            print("Error: --repo_path is required for Q&A mode.", file=sys.stderr)
            sys.exit(1)

        repo_path = Path(args.repo_path).resolve()
        if not repo_path.is_dir():
            print(
                f"Error: Path '{repo_path}' for --repo_path is not a valid directory.",
                file=sys.stderr,
            )
            sys.exit(1)

        if not viber_file_path_qa.exists():
            print(
                "Error: viber.txt not found in the current directory. "
                "Please generate it first or ensure it's present.",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"QA mode enabled. viber.txt found. Repository context: {repo_path}")
        print("Type 'exit' or 'quit' to end the session.")

        try:
            viber_content = viber_file_path_qa.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error: Could not read viber.txt: {e}", file=sys.stderr)
            sys.exit(1)

        chat_history = []
        while True:
            user_question = input("Ask a question (or type 'exit' to quit): ")
            if user_question.lower() in ["exit", "quit"]:
                print("Exiting Q&A mode.")
                break

            # Actual call to handle_qa_session
            agent_answer = handle_qa_session(user_question, viber_content, repo_path, chat_history)
            
            print(f"Agent: {agent_answer}") # This will print the answer or any error message from the LLM stages
            
            chat_history.append({"role": "user", "content": user_question})
            # Only add assistant response to history if it's not a critical error message from handle_qa_session
            # For simplicity now, we add everything. Refinement could be to check if agent_answer starts with "Error:"
            chat_history.append({"role": "assistant", "content": agent_answer})
            print() # for readability

        sys.exit(0) # Exit after Q&A loop

    # Original viber.txt generation logic starts here
    # This part should only run if args.qa is False.

    if not args.repo_path:
        print(
            "Error: --repo_path is required for viber.txt generation mode.",
            file=sys.stderr,
        )
        sys.exit(1)

    repo_path = Path(args.repo_path).resolve()
    viber_file_path = Path("viber.txt").resolve()

    if not repo_path.is_dir():
        print(f"Error: Path '{repo_path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Check for existing viber.txt only in generation mode
    if viber_file_path.exists():
        print(
            f"Info: '{viber_file_path.name}' already exists. Skipping creation."
        )
        # To prevent accidental overwrites, we exit.
        # Consider adding a --force flag if overwriting is desired.
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
