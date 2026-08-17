targetScope = 'resourceGroup'

@description('Azure region that supports Microsoft Fabric F SKUs and has at least 4 available capacity units.')
param location string

@description('Microsoft Fabric capacity administrator user principal name.')
param capacityAdministrator string

param owner string
param expiry string
param capacityName string = 'fcfrontierrmebc${take(toLower(uniqueString(subscription().id, resourceGroup().id)), 8)}'

var commonTags = {
  workload: 'frontier-rm-cockpit'
  environment: 'dev'
  owner: owner
  expiry: expiry
}

resource fabricCapacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: capacityName
  location: location
  tags: commonTags
  sku: {
    name: 'F4'
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: [
        capacityAdministrator
      ]
    }
  }
}

output capacityId string = fabricCapacity.id
output capacityName string = fabricCapacity.name
output capacityLocation string = fabricCapacity.location
output capacitySku string = fabricCapacity.sku.name
