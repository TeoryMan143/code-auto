## Fill codes

Put one student code per row in a CSV under the `code` header. By default, the
command reads `resources/codes.csv`; use `--csv` to choose another CSV inside
the `resources` folder.
The form values can be selected when starting the fill command. Any option you
do not provide keeps the current default. The date defaults to today.

```powershell
uv run fill --csv morning-codes.csv --start 09:00 --end 10:00 
	--course "Professional communication..." 
	--teacher "TEACHER"
```

The command runs in dry mode by default and saves screenshots. Add `--submit`
only after checking the dry run:

```powershell
uv run fill --start 09:00 --end 10:00 --submit
```

Run `uv run fill --help` to see all selectable fields, including `--monitor`,
`--activity`, `--modality`, `--comment`, and the course/teacher options.
