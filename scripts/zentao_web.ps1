# Get API token
$body = @{account="200625"; password="Qin200625"} | ConvertTo-Json
$resp = Invoke-WebRequest -Uri "http://zd.iniess.cn/api.php/v1/tokens" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
$tok = ($resp.Content | ConvertFrom-Json).token
Write-Host "Token: $tok"

# Use token as session cookie for web
$sess = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$cookie = New-Object System.Net.Cookie("zentaosid", $tok, "/", "zd.iniess.cn")
$sess.Cookies.Add($cookie)

# Try creating execution with web session
$body = "name=Phase2-UI&begin=2026-07-10&end=2026-08-15&days=30&type=sprint&products%5B%5D=3"
$r = Invoke-WebRequest -Uri "http://zd.iniess.cn/execution-create-3.html" -Method POST -Body $body -WebSession $sess -UseBasicParsing -ContentType "application/x-www-form-urlencoded" -MaximumRedirection 0 -ErrorAction SilentlyContinue
Write-Host "Exec: $($r.StatusCode) $($r.Headers.Location)"
