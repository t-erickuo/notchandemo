echo on

curl -k https://lrp-rg-eastus.eastus.cloudapp.azure.com/api/v1/session/02ae0c33-08e4-4a89-ae9e-e5f9c7fb65ff -d "{
  \"specVersion\": \"V1\",
  \"source\": \"asdasd\",
  \"id\": \"$1\",
  \"type\": \"type\",
  \"datacontenttype\": \"application/json\"
  }" -H "x-ms-client-principal-name: test" -H "x-ms-client-principal-claims: FabricOwner,PlatformAdministrator,TenantAdministrator" -H "x-ms-client-type: Operators" -H 'content-type: application/json'