import logging
import uuid

from notchandemo import GrpcDemoSession, apply_magic_to_make_faster

import time

logging.basicConfig(level=logging.DEBUG)

# try:
#     session_id = str(uuid.uuid4())
#     session_id = '02ae0c33-08e4-4a89-ae9e-e5f9c7fb65ff'
#     print(f'Opening session {session_id}')
#     session = GrpcDemoSession('lrp-rg-eastus.eastus.cloudapp.azure.com', session_id=session_id)
#     msg = ''
#     while msg != 'quit':
#         msg = input('Type "quit" to, well, quit!: ')
# finally:
#     session.close()


if __name__ == '__main__':
    import os

    try:
        subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    except KeyError:
        print('Missing required environment variable "AZURE_SUBSCRIPTION_ID"')
        exit()

    session = GrpcDemoSession('lrp-rg-eastus.eastus.cloudapp.azure.com', session_id='02ae0c33-08e4-4a89-ae9e-e5f9c7fb65ff')
    
    apply_magic_to_make_faster()

    import azure.mgmt.storage
    from azure.mgmt.storage.models import StorageAccountCreateParameters
    import azure.identity
    client = azure.mgmt.storage.StorageManagementClient(
        azure.identity.AzureCliCredential(),
        subscription_id,
        session=session)
    parameters = StorageAccountCreateParameters(
        sku={'name': 'Premium_LRS'}, kind='Storage', location='westus')
    lros = []
    for i in range(1):
        lros.append(client.storage_accounts.begin_create('johanste-testresourcegroup', f'johanstexnzticxy{i+2711}', parameters=parameters))
    for lro in lros:
        print(lro.result())
