$body = @{account="200625"; password="Qin200625"} | ConvertTo-Json
$resp = Invoke-WebRequest -Uri "http://zd.iniess.cn/api.php/v1/tokens" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
$tok = ($resp.Content | ConvertFrom-Json).token
Write-Host "Token: $tok"

# Start project
$h = @{Token=$tok; "Content-Type"="application/json"}
$r = Invoke-WebRequest -Uri "http://zd.iniess.cn/api.php/v1/projects/3" -Method PUT -Body '{"status":"doing","begin":"2026-07-10"}' -Headers $h -UseBasicParsing
Write-Host "Project status:" ($r.Content | ConvertFrom-Json).status

# Create execution
$execBody = '{"project":3,"name":"Phase2-UI","begin":"2026-07-10","end":"2026-08-15"}'
try {
    $r2 = Invoke-WebRequest -Uri "http://zd.iniess.cn/api.php/v1/executions" -Method POST -Body $execBody -Headers $h -ContentType "application/json" -UseBasicParsing
    Write-Host "Exec:" ($r2.Content | ConvertFrom-Json)
} catch {
    Write-Host "Exec fail:" $_.Exception.Message
    $err = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($err)
    Write-Host "  Body:" $reader.ReadToEnd()
}
