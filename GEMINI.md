# Project Overview

This project is a G-code editor and visualizer written in Python. It provides a graphical user interface (GUI) for editing G-code files, with features like syntax highlighting, auto-completion, and a 2D/3D preview of the toolpath.

**Main Technologies:**

*   **Python:** The core language of the application.
*   **Tkinter:** Used for creating the graphical user interface.
*   **Matplotlib:** Used for generating the 3D preview of the G-code toolpath.

**Architecture:**

The application is structured into several modules:

*   `main.py`: The entry point of the application. It creates the main window and handles file operations.
*   `gui.py`: Creates the main menu bar and buttons.
*   `editor.py`: Implements the custom G-code editor with features like syntax highlighting, auto-completion, and tooltips.
*   `gcode_parser.py`: Parses the G-code and extracts the toolpaths.
*   `preview.py`: Generates the 2D and 3D preview of the G-code toolpath.
*   `data/gcode_definitions.json`: Contains the definitions of G-code commands used for auto-completion and tooltips.

# Building and Running

To run the application, execute the following command in your terminal:

```bash
python app/main.py
```

**Dependencies:**

The application requires the following Python libraries:

*   **matplotlib**

You can install the dependencies using pip:

```bash
pip install matplotlib
```

# Development Conventions

*   **Code Style:** The code follows the PEP 8 style guide for Python.
*   **Testing:** There are no explicit tests in the project.
*   **Contributions:** The project does not have a contribution guide.
