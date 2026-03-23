# drawio-to-flow

Small utility for converting a Draw.io diagram into JSON data that can be used as flow/chart input.

## Files

- [app.py](app.py) — Python script that generates JSON output.

## Run

Install Python 3, then run:

```bash
python app.py
```

## Notes

- [`main`](app.py) currently reads `diagrams.xml` and writes `diagrams.json`.
- Input and output files are ignored by [.gitignore](.gitignore).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).