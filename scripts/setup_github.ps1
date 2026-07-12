# GitHub API Token
# 添加 GITHUB_TOKEN 到环境
$env:GITHUB_TOKEN = $env:GITHUB_TOKEN  # 从环境变量读取
if ($env:GITHUB_TOKEN) {
    Write-Host "GITHUB_TOKEN configured: $($env:GITHUB_TOKEN.Substring(0,8))..."
} else {
    Write-Host "GITHUB_TOKEN not set. Set via: `$env:GITHUB_TOKEN = 'your_token'"
}
