$stdout = "C:\Users\alivi\Documents\FusionCallingFoundation\acceptance\spoke-inspect.stdout.txt"
$stderr = "C:\Users\alivi\Documents\FusionCallingFoundation\acceptance\spoke-inspect.stderr.txt"
$exitCode = "C:\Users\alivi\Documents\FusionCallingFoundation\acceptance\spoke-inspect.exitcode.txt"

& "C:\Users\alivi\Documents\FusionCallingFoundation\.venv\Scripts\fusion-calling.exe" spoke-inspect 1> $stdout 2> $stderr
$LASTEXITCODE | Set-Content -NoNewline -Path $exitCode
