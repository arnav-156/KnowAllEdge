# PowerShell script to rename IntuiScape to KnowAllEdge throughout the project

Write-Host "Renaming project from IntuiScape to KnowAllEdge..." -ForegroundColor Cyan

# File extensions to process
$extensions = "*.md", "*.py", "*.js", "*.jsx", "*.json", "*.html", "*.css", "*.yml", "*.yaml", "*.txt", "*.sh", "*.cfg", "*.ini"

# Directories to exclude
$excludeDirs = "node_modules", ".venv", "venv", "__pycache__", ".git", ".pytest_cache", ".hypothesis"

$filesChanged = 0

# Get all files
$allFiles = Get-ChildItem -Path "." -Include $extensions -Recurse -File | Where-Object {
    $path = $_.FullName
    $exclude = $false
    foreach ($dir in $excludeDirs) {
        if ($path -like "*\$dir\*") {
            $exclude = $true
            break
        }
    }
    -not $exclude
}

Write-Host "Found $($allFiles.Count) files to process"

# Process each file
foreach ($file in $allFiles) {
    try {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $originalContent = $content
        
        # Apply replacements in order (most specific first)
        $content = $content -replace 'IntuiScape', 'KnowAllEdge'
        $content = $content -replace 'INTUITSCAPE', 'KNOWALLEDGE'
        $content = $content -replace 'Intuitscape', 'Knowalledge'
        $content = $content -replace 'intuitscape', 'knowalledge'
        
        # Write back if changed
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -NoNewline -Encoding UTF8
            $filesChanged++
            Write-Host "Updated: $($file.Name)" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Error processing $($file.Name): $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Complete! Files modified: $filesChanged" -ForegroundColor Green
