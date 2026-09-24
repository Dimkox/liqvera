[CmdletBinding()]
param(
    [string]$WorkflowPath = (Join-Path $PSScriptRoot '..\deploy\n8n\stage-a-orchestrator.workflow.json')
)

$ErrorActionPreference = 'Stop'
$requiredURLs = @(
    'http://stage-a-falsifier:8080/healthz',
    'http://stage-a-falsifier:8080/readyz',
    'http://stage-a-falsifier:8080/v1/experiment/status',
    'http://stage-a-falsifier:8080/v1/ops/data-quality',
    'http://stage-a-falsifier:8080/v1/business/operator-revenue'
)

function Fail([string]$Message) {
    throw "Stage A n8n validation failed: $Message"
}

if (-not (Test-Path -LiteralPath $WorkflowPath -PathType Leaf)) {
    Fail "workflow is missing: $WorkflowPath"
}

$raw = Get-Content -LiteralPath $WorkflowPath -Raw
try {
    $workflow = $raw | ConvertFrom-Json -Depth 100
} catch {
    Fail "workflow is not valid JSON: $($_.Exception.Message)"
}

if ($workflow.id -ne 'stageAOrchestrator01') { Fail 'workflow id must be stageAOrchestrator01' }
if ($workflow.name -ne 'Stage A HL+Lighter - ORCHESTRATOR (NO EXECUTION)') { Fail 'workflow name is not the approved no-execution name' }
if ($workflow.active -ne $false) { Fail 'workflow must be inactive' }
if ($null -eq $workflow.nodes -or $workflow.nodes.Count -eq 0) { Fail 'workflow must contain nodes' }

if ($raw -match '(?i)credential|executecommand|websocket|telegram|\b(?:trade|rfq|account)\b|private[_-]?key|api[_-]?key|wallet|sendtx|placeorder|cancel(?:order)?|withdraw|transfer') {
    Fail 'workflow contains a credential, forbidden node type, external URL, or execution-related string'
}
foreach ($match in [regex]::Matches($raw, 'https?://[^"\s]+')) {
    if ($requiredURLs -notcontains $match.Value -and $match.Value -ne 'http://stage-a-falsifier:8080') {
        Fail "workflow contains an external URL: $($match.Value)"
    }
}

$requiredNodes = @(
    'Manual start',
    'Every 5 minutes',
    'Stage A config',
    'GET health',
    'GET ready',
    'GET experiment status',
    'GET data quality',
    'GET operator revenue',
    'Fail-closed gate'
)
$nodesByName = @{}
foreach ($node in $workflow.nodes) {
    if ([string]::IsNullOrWhiteSpace($node.name)) { Fail 'every node must have a name' }
    if ($nodesByName.ContainsKey($node.name)) { Fail "duplicate node name: $($node.name)" }
    $nodesByName[$node.name] = $node
}
foreach ($name in $requiredNodes) {
    if (-not $nodesByName.ContainsKey($name)) { Fail "required node is missing: $name" }
}

$expectedNodeTypes = @{
    'n8n-nodes-base.manualTrigger' = 1
    'n8n-nodes-base.scheduleTrigger' = 1
    'n8n-nodes-base.set' = 1
    'n8n-nodes-base.httpRequest' = 5
    'n8n-nodes-base.code' = 1
}
if ($workflow.nodes.Count -ne 9) { Fail 'workflow must contain exactly nine allowlisted nodes' }
foreach ($node in $workflow.nodes) {
    if (-not $expectedNodeTypes.ContainsKey($node.type)) { Fail "node type is not allowlisted: $($node.type)" }
}
foreach ($nodeType in $expectedNodeTypes.Keys) {
    $actualCount = @($workflow.nodes | Where-Object { $_.type -eq $nodeType }).Count
    if ($actualCount -ne $expectedNodeTypes[$nodeType]) {
        Fail "node type $nodeType has count $actualCount; expected $($expectedNodeTypes[$nodeType])"
    }
}

if ($nodesByName['Manual start'].type -ne 'n8n-nodes-base.manualTrigger') { Fail 'Manual start must be a manual trigger' }
if ($nodesByName['Every 5 minutes'].type -ne 'n8n-nodes-base.scheduleTrigger') { Fail 'Every 5 minutes must be a schedule trigger' }
if ($nodesByName['Stage A config'].type -ne 'n8n-nodes-base.set') { Fail 'Stage A config must be a Set node' }
if ($nodesByName['Fail-closed gate'].type -ne 'n8n-nodes-base.code') { Fail 'Fail-closed gate must be a Code node' }
if ($nodesByName['Every 5 minutes'].parameters.rule.interval.Count -ne 1 -or
    $nodesByName['Every 5 minutes'].parameters.rule.interval[0].field -ne 'minutes' -or
    $nodesByName['Every 5 minutes'].parameters.rule.interval[0].minutesInterval -ne 5) {
    Fail 'schedule must run exactly every five minutes'
}

foreach ($edge in @(
    @{ From = 'Manual start'; To = 'Stage A config' },
    @{ From = 'Every 5 minutes'; To = 'Stage A config' },
    @{ From = 'Stage A config'; To = 'GET health' },
    @{ From = 'GET health'; To = 'GET ready' },
    @{ From = 'GET ready'; To = 'GET experiment status' },
    @{ From = 'GET experiment status'; To = 'GET data quality' },
    @{ From = 'GET data quality'; To = 'GET operator revenue' },
    @{ From = 'GET operator revenue'; To = 'Fail-closed gate' }
)) {
    $connection = $workflow.connections.PSObject.Properties[$edge.From].Value
    if ($null -eq $connection -or $null -eq $connection.main -or $null -eq $connection.main[0] -or
        $null -eq ($connection.main[0] | Where-Object { $_.node -eq $edge.To })) {
        Fail "required flow is missing: $($edge.From) -> $($edge.To)"
    }
}
$seenURLs = @{}
foreach ($node in $workflow.nodes) {
    if ($node.type -ne 'n8n-nodes-base.httpRequest') { continue }
    if ($node.parameters.method -ne 'GET') { Fail "HTTP node $($node.name) must use GET" }
    $url = [string]$node.parameters.url
    if ($requiredURLs -notcontains $url) { Fail "HTTP node $($node.name) has a non-contract URL: $url" }
    $seenURLs[$url] = $true
}
foreach ($url in $requiredURLs) {
    if (-not $seenURLs.ContainsKey($url)) { Fail "required GET endpoint is missing: $url" }
}

$expectedGateCode = @'
const response = (nodeName) => {
  const items = $items(nodeName);
  if (!items || items.length !== 1) {
    throw new Error(`missing or ambiguous response from ${nodeName}`);
  }
  return items[0].json;
};

const experiment = response('GET experiment status');
const revenueResponse = response('GET operator revenue');
if (experiment.execution_available !== false || revenueResponse.execution_available !== false) {
  throw new Error('execution_available must be false');
}

const operatorRevenue = revenueResponse.data?.operator_revenue;
if (operatorRevenue?.contract_complete !== true) {
  throw new Error('operator revenue contract is incomplete');
}
for (const field of ['source', 'rate', 'turnover_basis', 'payout_terms', 'collection_mechanism', 'infrastructure_cost']) {
  if (operatorRevenue[field] === undefined || operatorRevenue[field] === null || operatorRevenue[field] === '') {
    throw new Error(`operator revenue contract lacks ${field}`);
  }
}

return [{
  json: {
    mode: experiment.mode,
    execution_available: false,
    operator_revenue_contract_complete: true
  }
}];
'@
$gateCode = ([string]$nodesByName['Fail-closed gate'].parameters.jsCode).Replace("`r`n", "`n").TrimEnd("`n")
$expectedGateCode = $expectedGateCode.Replace("`r`n", "`n").TrimEnd("`n")
if ($gateCode -cne $expectedGateCode) {
    Fail 'fail-closed gate must match the canonical structural contract'
}

Write-Host "Stage A n8n workflow is valid: $WorkflowPath"
