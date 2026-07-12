$body = @{account="200625"; password="Qin200625"} | ConvertTo-Json
$resp = Invoke-WebRequest -Uri "http://zd.iniess.cn/api.php/v1/tokens" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
$tok = ($resp.Content | ConvertFrom-Json).token
Write-Host "Token: $tok"
