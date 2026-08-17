targetScope = 'resourceGroup'

param location string = resourceGroup().location
param owner string
param expiry string
param imageTag string = '0.8.1'

var suffix = toLower(uniqueString(subscription().id, resourceGroup().id))
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

resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: 'oai-frontier-rm-${suffix}'
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: 'appi-frontier-rm-${suffix}'
}

resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-frontier-rm-api-${suffix}'
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
        targetPort: 8080
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
          name: 'frontier-rm-api'
          image: '${containerRegistry.properties.loginServer}/frontier-rm-api:${imageTag}'
          env: [
            { name: 'HOST', value: '0.0.0.0' }
            { name: 'PORT', value: '8080' }
            { name: 'FRONTIER_AI_MODE', value: 'azure' }
            { name: 'AZURE_CLIENT_ID', value: workloadIdentity.properties.clientId }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAI.properties.endpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: 'frontier-gpt-4-1-mini' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/health'
                port: 8080
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

output apiName string = apiApp.name
output apiFqdn string = apiApp.properties.configuration.ingress.fqdn
output apiUrl string = 'https://${apiApp.properties.configuration.ingress.fqdn}'