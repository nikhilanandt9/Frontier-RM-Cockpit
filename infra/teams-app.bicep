targetScope = 'resourceGroup'

param location string = resourceGroup().location
param owner string
param expiry string
param apiUrl string
param imageTag string = '0.2.0'

var suffix = toLower(uniqueString(subscription().id, resourceGroup().id))
var shortSuffix = take(suffix, 8)
var commonTags = {
  workload: 'frontier-rm-cockpit'
  environment: 'dev'
  owner: owner
  expiry: expiry
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: 'cae-frontier-rm-${suffix}'
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: 'acrfrontierrm${suffix}'
}

resource workloadIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: 'id-frontier-rm-${suffix}'
}

resource teamsApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-frm-teams-${shortSuffix}'
  location: location
  tags: commonTags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${workloadIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 3978
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: workloadIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontier-rm-teams'
          image: '${containerRegistry.properties.loginServer}/frontier-rm-teams:${imageTag}'
          env: [
            { name: 'HOST', value: '0.0.0.0' }
            { name: 'PORT', value: '3978' }
            { name: 'FRONTIER_API_URL', value: apiUrl }
            { name: 'FRONTIER_BOT_AUTH_MODE', value: 'botframework' }
            { name: 'BOT_ID', value: workloadIdentity.properties.clientId }
            { name: 'BOT_TENANT_ID', value: tenant().tenantId }
            { name: 'AZURE_CLIENT_ID', value: workloadIdentity.properties.clientId }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 3978
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 20
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

resource azureBot 'Microsoft.BotService/botServices@2022-09-15' = {
  name: 'bot-frontier-rm-${suffix}'
  location: 'global'
  kind: 'azurebot'
  tags: commonTags
  sku: {
    name: 'F0'
  }
  properties: {
    displayName: 'Frontier RM'
    description: 'Internal fictional Premier RM demonstration'
    endpoint: 'https://${teamsApp.properties.configuration.ingress.fqdn}/api/messages'
    msaAppId: workloadIdentity.properties.clientId
    msaAppTenantId: tenant().tenantId
    msaAppType: 'UserAssignedMSI'
    msaAppMSIResourceId: workloadIdentity.id
    schemaTransformationVersion: '1.3'
  }
}

resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: azureBot
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
    properties: {
      isEnabled: true
    }
  }
}

output teamsName string = teamsApp.name
output teamsFqdn string = teamsApp.properties.configuration.ingress.fqdn
output botName string = azureBot.name
output botId string = workloadIdentity.properties.clientId
output messagingEndpoint string = azureBot.properties.endpoint