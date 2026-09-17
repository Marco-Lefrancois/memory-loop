param(
    [Parameter(Position=0)]
    [string]$Target,
    [switch]$Test
)

$argsList = @()
if ($Target) { $argsList += $Target }
if ($Test) { $argsList += "--test" }

python "$PSScriptRoot\switch_key.py" @argsList
