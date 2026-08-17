targetScope = 'subscription'

@description('Must be explicitly set after the subscription name and ID are confirmed by the user.')
@allowed([true])
param subscriptionConfirmed bool

@description('Azure region selected after subscription confirmation.')
param location string

@description('Owner tag used for internal lifecycle management.')
param owner string

@description('ISO date after which the demo resources should be reviewed or removed.')
param expiry string

param resourceGroupName string = 'rg-frontier-rm-ebc-dev'

resource demoResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    workload: 'frontier-rm-cockpit'
    environment: 'dev'
    owner: owner
    expiry: expiry
  }
}

output resourceGroupId string = demoResourceGroup.id
output confirmed bool = subscriptionConfirmed
