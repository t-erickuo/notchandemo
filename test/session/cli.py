from datetime import date, datetime
import logging
import time
import uuid

from notchandemo import GrpcDemoSession, apply_magic_to_log_polling, apply_magic_to_make_faster, dateUtil

import random
import os
import azure.mgmt.storage
import azure.mgmt.compute
import azure.mgmt.network
from azure.mgmt.storage.models import StorageAccountCreateParameters
from azure.mgmt.compute.models import DiskCreateOption
import azure.identity

logging.basicConfig(level=logging.CRITICAL)

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

RESOURCE_GROUP_NAME='peshaotest'
LOCATION='southcentralusstg'
VM_NAME='peshao-17-15-42'
DATA_DISK_NAME=f'mydatadisk-{uuid.uuid1()}'

def create_storage_account():
    client = azure.mgmt.storage.StorageManagementClient(
        azure.identity.AzureCliCredential(),
        subscription_id,
        session=session)
    parameters = StorageAccountCreateParameters(
        sku={'name': 'Premium_LRS'}, kind='Storage', location=LOCATION)

    return client.storage_accounts.begin_create(RESOURCE_GROUP_NAME, f'erictest{random.randint(1,1000)}', parameters=parameters)

def create_virtual_machine():
    network_client = azure.mgmt.network.NetworkManagementClient(
        azure.identity.AzureCliCredential(),
        subscription_id)

    # provision virtual network
    VNET_NAME = "python-azure-vm-example-vnet"
    SUBNET_NAME = "python-azure-vm-example-subnet"
    IP_NAME = "python-azure-vm-example-ip"
    IP_CONFIG_NAME = "python-azure-vm-example-ip-config"
    NIC_NAME = "python-azure-vm-example-nic"

    # Create the virtual network 
    poller = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME,
        VNET_NAME,
        {
            "location": LOCATION,
            "address_space": {
                "address_prefixes": ["10.0.0.0/16"]
            }
        }
    )

    vnet_result = poller.result()
    print(f"Provisioned virtual network {vnet_result.name} with address prefixes {vnet_result.address_space.address_prefixes}")

    # Create the subnet
    poller = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, 
        VNET_NAME, SUBNET_NAME,
        { "address_prefix": "10.0.0.0/24" }
    )
    subnet_result = poller.result()
    print(f"Provisioned virtual subnet {subnet_result.name} with address prefix {subnet_result.address_prefix}")

    # Create the IP address
    poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
        IP_NAME,
        {
            "location": LOCATION,
            "sku": { "name": "Standard" },
            "public_ip_allocation_method": "Static",
            "public_ip_address_version" : "IPV4"
        }
    )

    ip_address_result = poller.result()
    print(f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}")

    # Create the network interface client
    poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
        NIC_NAME, 
        {
            "location": LOCATION,
            "ip_configurations": [ {
                "name": IP_CONFIG_NAME,
                "subnet": { "id": subnet_result.id },
                "public_ip_address": {"id": ip_address_result.id }
            }]
        }
    )

    nic_result = poller.result()
    print(f"Provisioned network interface client {nic_result.name}")

    # Create the virtual machine
    USERNAME = "pythonazureuser"
    PASSWORD = "ChangeM3N0w!"

    print(f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes.")
    dateUtility = dateUtil.DateUtil()
    dateUtility.record_start_time("provision VM")

    # Create the VM on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.
    poller = getComputeClientWithSessionOrNot().virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
        {
            "location": LOCATION,
            "storage_profile": {
                "image_reference": {
                    "publisher": 'AzureRT.PIRCore.TestWAStage',
                    "offer": "TestWindowsServer2012",
                    "sku": "R2",
                    "version": "latest"
                }
            },
            "hardware_profile": {
                "vm_size": "Standard_DS1_v2"
            },
            "os_profile": {
                "computer_name": VM_NAME,
                "admin_username": USERNAME,
                "admin_password": PASSWORD
            },
            "network_profile": {
                "network_interfaces": [{
                    "id": nic_result.id,
                }]
            }
        }
    )

    poller.result()
    dateUtility.record_end_time_and_total_time_elapsed("provisioning VM")

def attach_data_disk_to_vm():
    compute_client_with_no_session = azure.mgmt.compute.ComputeManagementClient(
        azure.identity.AzureCliCredential(),
        subscription_id)

    virtual_machine = compute_client_with_no_session.virtual_machines.get(
        RESOURCE_GROUP_NAME,
        VM_NAME
    )

    # Create managed data disk
    print('\nCreate (empty) managed Data Disk')
    async_disk_creation = compute_client_with_no_session.disks.begin_create_or_update(
        RESOURCE_GROUP_NAME,
        DATA_DISK_NAME,
        {
            'location': LOCATION,
            'disk_size_gb': 1,
            'creation_data': {
                'create_option': DiskCreateOption.empty
            }
        }
    )
    data_disk = async_disk_creation.result()

    # Attach data disk
    print('\nAttach Data Disk')
    virtual_machine.storage_profile.data_disks.append({
        'lun': random.randint(0,15),
        'name': DATA_DISK_NAME,
        'create_option': DiskCreateOption.attach,
        'managed_disk': {
            'id': data_disk.id
        }
    })

    dateUtility = dateUtil.DateUtil()
    dateUtility.record_start_time("attach Disk")

    async_disk_attach = getComputeClientWithSessionOrNot().virtual_machines.begin_create_or_update(
        RESOURCE_GROUP_NAME,
        virtual_machine.name,
        virtual_machine
    )

    try:
        async_disk_attach.result()
    except Exception as e:
        print(e)
    finally:
        dateUtility.record_end_time_and_total_time_elapsed("attaching Disk")

def detach_data_disk_to_vm():
    compute_client_with_no_session = azure.mgmt.compute.ComputeManagementClient(
        azure.identity.AzureCliCredential(),
        subscription_id)

    virtual_machine = compute_client_with_no_session.virtual_machines.get(
        RESOURCE_GROUP_NAME,
        VM_NAME
    )

    # Detach data disk
    data_disks = virtual_machine.storage_profile.data_disks
    if (len(data_disks) == 0):
        print("No disks found")
        return

    # remove last disk
    data_disks.pop()

    dateUtility = dateUtil.DateUtil()
    dateUtility.record_start_time("detach Disk")

    async_disk_detach = getComputeClientWithSessionOrNot().virtual_machines.begin_create_or_update(
        RESOURCE_GROUP_NAME,
        VM_NAME,
        virtual_machine
    )

    try:
        async_disk_detach.result()
    except Exception as e:
        print(e)
    finally:
        dateUtility.record_end_time_and_total_time_elapsed("detaching Disk")

def getComputeClientWithSessionOrNot():
    compute_client = any
    if (lrpInput == 0):
        compute_client = azure.mgmt.compute.ComputeManagementClient(
            azure.identity.AzureCliCredential(),
            subscription_id,
            session=session)
    else:
        # apply here so regular compute clients don't log polling as well
        apply_magic_to_log_polling()
        compute_client = azure.mgmt.compute.ComputeManagementClient(
            azure.identity.AzureCliCredential(),
            subscription_id)
    return compute_client

if __name__ == '__main__':
    try:
        # AzBlitz-Stage-Canary-Test subscription
        os.environ['AZURE_SUBSCRIPTION_ID'] = '05f99a57-dea7-4683-bf91-840aca3514d7'
        subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
    except KeyError:
        print('Missing required environment variable "AZURE_SUBSCRIPTION_ID"')
        exit()
    
    lrpInput = int(input("Choose to run with LRP[0] or without LRP[1]:\n"))
    crudOperation = int(input("Choose one compute operation from Attach Disk[0], Detach Disk[1], Create VM[2]:\n"))

    if (lrpInput == 0):
        session = GrpcDemoSession('lrp-rg-eastus.eastus.cloudapp.azure.com', subscription_id, session_id='02ae0c33-08e4-4a89-ae9e-e5f9c7fb65ff')
        apply_magic_to_make_faster()

    if (crudOperation == 0):
        attach_data_disk_to_vm()
    elif(crudOperation == 1):
        detach_data_disk_to_vm()
    elif(crudOperation == 2):
        create_virtual_machine()
