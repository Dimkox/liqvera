[CmdletBinding()]
param(
    [string]$WorkflowPath = (Join-Path $PSScriptRoot '..\deploy\n8n\stage-a-orchestrator.workflow.json'),
    [string]$ValidatorPath = (Join-Path $PSScriptRoot 'validate-stage-a-n8n.ps1')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $WorkflowPath -PathType Leaf)) {
    throw "Workflow is missing: $WorkflowPath"
}
if (-not (Test-Path -LiteralPath $ValidatorPath -PathType Leaf)) {
    throw "Validator is missing: $ValidatorPath"
}

$positiveAccepted = $false
try {
    & $ValidatorPath -WorkflowPath $WorkflowPath
    $positiveAccepted = $true
} catch {
    throw "Validator rejected the unmodified workflow: $($_.Exception.Message)"
}
if (-not $positiveAccepted) {
    throw 'Validator did not accept the unmodified workflow'
}

$source = Get-Content -LiteralPath $WorkflowPath -Raw | ConvertFrom-Json -Depth 100
$mutations = @(
    @{
        Name = 'side-effect-email-node'
        Apply = {
            param($workflow)
            $workflow.nodes += [pscustomobject]@{
                parameters = [pscustomobject]@{}
                id = 'side-effect-email'
                name = 'Side effect email'
                type = 'n8n-nodes-base.emailSend'
                typeVersion = 2
                position = @(1920, 320)
            }
        }
    },
    @{
        Name = 'comment-only-gate'
        Apply = {
            param($workflow)
            $gate = $workflow.nodes | Where-Object { $_.name -eq 'Fail-closed gate' }
            $gate.parameters.jsCode = "// execution_available operator_revenue contract_complete source rate turnover_basis payout_terms collection_mechanism infrastructure_cost`nreturn [{ json: { execution_available: false } }];"
        }
    },
    @{
        Name = 'seven-minute-schedule'
        Apply = {
            param($workflow)
            $schedule = $workflow.nodes | Where-Object { $_.name -eq 'Every 5 minutes' }
            $schedule.parameters.rule.interval[0].minutesInterval = 7
        }
    }
)

$accepted = @()
foreach ($mutation in $mutations) {
    $temporary = New-TemporaryFile
    try {
        $workflow = $source | ConvertTo-Json -Depth 100 | ConvertFrom-Json -Depth 100
        & $mutation.Apply $workflow
        $workflow | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $temporary.FullName -Encoding utf8NoBOM

        $wasAccepted = $false
        try {
            & $ValidatorPath -WorkflowPath $temporary.FullName
            $wasAccepted = $true
        } catch {
            Write-Host "Mutation rejected as required: $($mutation.Name)"
        }
        if ($wasAccepted) {
            Write-Host "Mutation incorrectly accepted: $($mutation.Name)"
            $accepted += $mutation.Name
        }
    } finally {
        Remove-Item -LiteralPath $temporary.FullName -Force -ErrorAction SilentlyContinue
    }
}

if ($accepted.Count -gt 0) {
    throw "Validator accepted forbidden mutations: $($accepted -join ', ')"
}

Write-Host 'All Stage A n8n mutations were rejected.'
