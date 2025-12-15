$envFileContent = @()

foreach ($arg in $args) {
    if ($arg -like "*=*") {
        $envFileContent += $arg
    }
}

if ($envFileContent.Count -gt 0) {
    Set-Content -Path "debug.env" -Value ($envFileContent -join "`n") -Encoding UTF8
}

