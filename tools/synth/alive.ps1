@(Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'tools/synth/run_all\.sh' -and $_.Name -eq 'bash.exe' }).Count
