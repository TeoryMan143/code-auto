## Fill codes

Put one student code per row in `resources/codes.csv` under the `code` header.
The form values can be selected when starting the fill command. Any option you
do not provide keeps the current default.

```powershell
uv run fill --date 2026-10-02 --start 09:00 --end 10:00 `
	--course "Professional communication..." `
	--teacher "TEACHER"
```

The command runs in dry mode by default and saves screenshots. Add `--submit`
only after checking the dry run:

```powershell
uv run fill --date 2026-10-02 --start 09:00 --end 10:00 --submit
```

Run `uv run fill --help` to see all selectable fields, including `--monitor`,
`--activity`, `--modality`, `--comment`, and the course/teacher options.
