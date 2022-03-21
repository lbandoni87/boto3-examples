import boto3
import pprint
import datetime
import csv
from datetime import datetime, timezone

pp=pprint.PrettyPrinter(depth=4)

def get_ec2_conn():
    session = boto3.Session(profile_name='read')
    return session.client('ec2',region_name='eu-west-1')

def get_snapshots(ec2, ownerId):
    SnapshotIdList={}
    snapshots=ec2.describe_snapshots(
        OwnerIds=[ownerId]
    )
    for snap in snapshots['Snapshots']:
        filter_snapshots(SnapshotIdList, snap)
    return SnapshotIdList

def filter_snapshots(SnapshotIdList, snap):
    SnapshotId = snap.get('SnapshotId')
    StartTime = snap.get('StartTime')
    VolumeId = snap.get('VolumeId')
    if VolumeId in SnapshotIdList:
        SnapshotIdList[VolumeId].append({'SnapshotId':SnapshotId,'StartTime':StartTime})
    if VolumeId not in SnapshotIdList:
        SnapshotIdList[VolumeId]=[{'SnapshotId':SnapshotId,'StartTime':StartTime}]

def get_vol_set(snapshots):
    vol_set=set()
    for vol in  snapshots.keys():
        vol_set.add(vol)
    return list(vol_set)

def get_all_volumes(ec2):
    all_vols=set()
    response=ec2.describe_volumes()
    for res in response['Volumes']:
        VolumeId=res.get('VolumeId')
        all_vols.add(VolumeId)
    return all_vols

def get_instanceIds(ec2,vols):
    instanceIds=set()
    response=ec2.describe_volumes(
        VolumeIds=vols
    )
    for res in response['Volumes']:
        Attachments=res.get('Attachments')
        for attachment in Attachments:
            InstanceId=attachment.get('InstanceId')
            instanceIds.add(InstanceId)
    return instanceIds

def get_instance_info(ec2,instanceIds):
    instance_info={}
    response=ec2.describe_instances(
        InstanceIds=instanceIds
    )
    for res in response['Reservations']:
        get_instance_name(instance_info, res)
    return instance_info

def get_instance_name(instance_info, res):
    for instance in res['Instances']:
        InstanceId = instance.get('InstanceId')
        tags = instance['Tags']
        tag_dic = convert_tags_to_dic(tags)
        Name = tag_dic.get('Name')
        instance_info[InstanceId] = Name

def convert_tags_to_dic(tags):
    tag_dic = {}
    for tag in tags:
        Key = tag.get('Key')
        Value = tag.get('Value')
        tag_dic[Key] = Value
    return tag_dic

def create_report(instance_info,filename):
    with open(filename,'wt') as result:
        fields=[
            'Instance ID',
            'Instance Name'
        ]
        w = csv.writer(result, delimiter=',', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(fields)
        for instance, instance_name in instance_info.items():
            row = [
                instance,
                instance_name
            ]
            result.write('{0}\n'.format(str(row)[1:-1].replace('\'', '')))
    return result

def main():
    ownerId = boto3.client('iam').get_user()['User']['Arn'].split(':')[4]
    date = datetime.today()
    filename='/home/Documents/instances_with_volume_snapshots-'+str(date)+'.csv'
    ec2=get_ec2_conn()
    snapshots=get_snapshots(ec2,ownerId)
    vols=get_vol_set(snapshots)
    all_vol=get_all_volumes(ec2)
    used_volumes=set(all_vol).intersection(vols)
    used_volumes=list(used_volumes)
    instanceIds=get_instanceIds(ec2,used_volumes)
    instanceIds=list(instanceIds)
    instance_info=get_instance_info(ec2,instanceIds)
    create_report(instance_info,filename)

if __name__ == '__main__':
    main()