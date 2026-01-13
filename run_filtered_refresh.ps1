# PowerShell script to run a filtered refresh cycle for specific venues
# Usage: .\run_filtered_refresh.ps1 puttery_nyc kick_axe_brooklyn

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Venues
)

Write-Host "Starting filtered refresh cycle for $($Venues.Count) venues:" -ForegroundColor Cyan
foreach ($venue in $Venues) {
    Write-Host "  - $venue" -ForegroundColor Yellow
}

# Convert to Python list format
$venuesList = $Venues -join "','"
$pythonCode = @"
from app import refresh_all_venues_task

venues = ['$venuesList']
result = refresh_all_venues_task.delay(venues_filter=venues)
print(f'Task ID: {result.id}')
print(f'Status: {result.status}')
"@

Write-Host "`nSubmitting task..." -ForegroundColor Cyan
python -c $pythonCode

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Task submitted successfully!" -ForegroundColor Green
    Write-Host "Monitor progress in Celery worker logs" -ForegroundColor Gray
} else {
    Write-Host "`n✗ Error submitting task" -ForegroundColor Red
    exit 1
}
