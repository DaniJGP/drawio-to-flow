# drawio-to-flow

Small utility for converting a [draw.io](https://www.draw.io/) diagram into [React Flow](https://reactflow.dev/) JSON format.

## Files

- [app.py](app.py) — Python script that generates JSON output.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/DaniJGP/drawio-to-flow.git
   cd drawio-to-flow
   ```

2. (Recommended) Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create a Draw.io diagram, then export it as XML. Save the XML in the same directory as `app.py`
2. Run the script:

  ```bash
  python app.py <path/to/diagrams.xml> [path/to/diagrams.json]
  ```

## Notes

- The input XML file path is required, while the output JSON file path is optional (defaults to `out/diagrams.json`).
- Input and output files are ignored by [.gitignore](.gitignore).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).