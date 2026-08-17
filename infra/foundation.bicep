targetScope = 'resourceGroup'

param location string = resourceGroup().location
param owner string
param expiry string

var suffix = toLower(uniqueString(subscription().id, resourceGroup().id))
var commonTags = {
  workload: 'frontier-rm-cockpit'
  environment: 'dev'
  owner: owner
  expiry: expiry
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-frontier-rm-${suffix}'
  location: location
  tags: commonTags
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-frontier-rm-${suffix}'
  location: location
  kind: 'web'
  tags: commonTags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acrfrontierrm${suffix}'
  location: location
  tags: commonTags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource workloadIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-frontier-rm-${suffix}'
  location: location
  tags: commonTags
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-frontier-rm-${suffix}'
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'oai-frontier-rm-${suffix}'
  location: location
  tags: commonTags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'oai-frontier-rm-${suffix}'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
  }
}

resource chatModel 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: azureOpenAI
  name: 'frontier-gpt-4-1-mini'
  sku: {
    name: 'GlobalStandard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

resource acrPullRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
}

resource openAIUserRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
}

resource registryPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(containerRegistry.id, workloadIdentity.id, acrPullRole.id)
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPullRole.id
  }
}

resource openAIUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, workloadIdentity.id, openAIUserRole.id)
  properties: {
    principalId: workloadIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: openAIUserRole.id
  }
}

output registryName string = containerRegistry.name
output registryServer string = containerRegistry.properties.loginServer
output environmentId string = containerEnvironment.id
output environmentName string = containerEnvironment.name
output identityId string = workloadIdentity.id
output identityClientId string = workloadIdentity.properties.clientId
output identityPrincipalId string = workloadIdentity.properties.principalId
output azureOpenAIId string = azureOpenAI.id
output azureOpenAIName string = azureOpenAI.name
output azureOpenAIEndpoint string = azureOpenAI.properties.endpoint
output azureOpenAIDeployment string = chatModel.name
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString