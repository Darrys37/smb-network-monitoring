param(
    [ValidateSet('nginx_stopped','agent_stopped','interface_down','remote_http_filtered','dns_egress_blocked','cpu_stress')]
    [string]$Fault = 'nginx_stopped'
)

$ErrorActionPreference = 'Stop'
$mlProject = 'C:\Users\Darrys\do-an'
$mlRelease = Join-Path $mlProject 'evidence\ml-v2\ML_RELEASE.json'
if (-not (Test-Path -LiteralPath $mlRelease)) {
    throw 'ML acceptance review is not complete. Read the current status before running the fault demo.'
}

$mlLocks = [System.Collections.Generic.List[object]]::new()
$mlPreviousPythonPath = $env:PYTHONPATH
$mlPreviousEncoding = $env:PYTHONIOENCODING
$mlWakeRequested = $false
try {
    # Share the same byte locks as the Python coordinators; never inject in parallel.
    foreach ($mlLockName in @('ml-supervisor.lock','ml-acceptance.lock')) {
        $mlLockPath = Join-Path $PSScriptRoot ('verification\' + $mlLockName)
        $mlStream = [System.IO.File]::Open($mlLockPath, [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::ReadWrite)
        $mlEntry = @{ Stream = $mlStream; Locked = $false }
        $mlLocks.Add($mlEntry)
        if ($mlStream.Length -eq 0) { $mlStream.SetLength(1) }
        $mlStream.Lock(0, 1)
        $mlEntry.Locked = $true
    }
    if (-not ('MlLabDemoWake' -as [type])) {
        Add-Type @'
using System.Runtime.InteropServices;
public static class MlLabDemoWake {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
    }
    if ([MlLabDemoWake]::SetThreadExecutionState([uint32]2147483651) -eq 0) {
        throw 'Cannot establish the temporary display/system wake request.'
    }
    $mlWakeRequested = $true
    $env:PYTHONPATH = Join-Path $PSScriptRoot '.ssh-deps'
    if ($mlPreviousPythonPath) { $env:PYTHONPATH += [System.IO.Path]::PathSeparator + $mlPreviousPythonPath }
    $env:PYTHONIOENCODING = 'utf-8'
    & python (Join-Path $mlProject 'ml-research\run_demo_v2.py') --release $mlRelease --fault $Fault
    if ($LASTEXITCODE -ne 0) { throw "Demo exited with code $LASTEXITCODE; retain its evidence for review." }
}
finally {
    if ($mlWakeRequested) { [void][MlLabDemoWake]::SetThreadExecutionState([uint32]2147483648) }
    for ($mlIndex = $mlLocks.Count - 1; $mlIndex -ge 0; $mlIndex--) {
        $mlEntry = $mlLocks[$mlIndex]
        try { if ($mlEntry.Locked) { $mlEntry.Stream.Unlock(0, 1) } }
        finally { $mlEntry.Stream.Dispose() }
    }
    $env:PYTHONPATH = $mlPreviousPythonPath
    $env:PYTHONIOENCODING = $mlPreviousEncoding
}
