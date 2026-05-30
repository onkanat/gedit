# Project Overview

This project is a G-code editor and visualizer written in Python. It provides a graphical user interface (GUI) for editing G-code files, with features like syntax highlighting, auto-completion, and a 2D/3D preview of the toolpath.

**Main Technologies:**

* **Python:** The core language of the application.
* **Tkinter:** Used for creating the graphical user interface.
* **Matplotlib:** Used for generating the 3D preview of the G-code toolpath.
* **NumPy:** Used for numeric operations (e.g., arc interpolation) in previews.

**Architecture:**

The application is structured into several modules:

*   `main.py`: The entry point of the application. It creates the main window and handles file operations.
*   `gui.py`: Creates the main menu bar and buttons.
*   `editor.py`: Implements the custom G-code editor with features like syntax highlighting, auto-completion, and tooltips.
* `gcode_parser.py`: Parses the G-code and extracts the toolpaths. Tracks modal state (plane, units,
	motion, coord system, spindle) and returns `{paths, layers}` with `line_no`/`raw` fields. Supports
	plane-aware arcs (G17/G18/G19) using I/J/K or R with safety checks.
* `preview.py`: Generates the 2D and 3D preview of the G-code toolpath. Includes a 2D plane selector
	(Auto/G17/G18/G19), grid/axes, scaling and centering with guards; 3D view uses equalized axes.
* `data/gcode_definitions.json`: Contains the definitions of G-code commands used for auto-completion and tooltips.

## Building and Running

To run the application, execute the following command in your terminal:

```bash
python app/main.py
```

**Dependencies:**

The application requires the following Python libraries:

* **matplotlib**
* **numpy**

You can install the dependencies using pip:

```bash
pip install matplotlib numpy
```

Quick start (macOS + zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

## Development Conventions

* **Code Style:** The code follows the PEP 8 style guide for Python.
* **Testing:** There are no explicit tests in the project. Consider adding small smoke tests for parser and preview.
* **Contributions:** The project does not have a contribution guide.
