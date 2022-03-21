import boto3
import pprint

pp = pprint.PrettyPrinter(depth=4)

def dict_to_json_tags(tag_dict):
    """convert single dictionary indexed on name to boto3 json std list of name value pairs """

    return [{'Key': i.strip(), 'Value': tag_dict[i].strip()} for i in tag_dict]

# tag_dic=json_tags_to_dict(tags)

def get_ec2_conn():
    return boto3.client('ec2')

def describe_ec2_instances(ec2):
    return ec2.describe_instances()

def get_security_groups(instances):
    open_sgs_dic={}
    for res in instances['Reservations']:
        for instance in res['Instances']:
            InstanceId=instance.get('InstanceId')
            Tags=instance.get('Tags')
            tag_dic=dict_to_json_tags(Tags)
            pp.pprint(tag_dic)
            SecurityGroups=instance.get('SecurityGroups')
            open_sgs_dic[InstanceId]=SecurityGroups
    return open_sgs_dic

def get_sg_rules(security_groups,ec2):
    inst_dic={}
    for ins,sgs in security_groups.items():
        for sg in sgs:
            instance=ins
            SecurityGroup=sg.get('GroupId')
            sg_details=ec2.describe_security_groups(
                GroupIds=[SecurityGroup]
            )
            for sgs in sg_details['SecurityGroups']:
                process_sg_rules(SecurityGroup, inst_dic, instance, sgs)
    return inst_dic

def process_sg_rules(SecurityGroup, inst_dic, instance, sgs):
    IpPermissions = sgs.get('IpPermissions')
    Description = sgs.get('Description')
    GroupName = sgs.get('GroupName')
    for IpRanges in IpPermissions:
        FromPort = IpRanges.get('FromPort')
        IpRanges = IpRanges.get('IpRanges')
        for CidrIp in IpRanges:
            process_ipranges(CidrIp, SecurityGroup, inst_dic,
                             instance, Description, GroupName,
                             FromPort)

def process_ipranges(CidrIp, SecurityGroup, inst_dic,
                     instance, Description, GroupName,
                     FromPort):
    CidrIp = CidrIp.get('CidrIp')
    if CidrIp == '0.0.0.0/0' and SecurityGroup is not 'sg-665d691e':
        inst_dic[instance] = {'SecurityGroup': SecurityGroup, 'CidrIp': CidrIp,
                              'Description': Description, 'GroupName': GroupName,
                              'FromPort': FromPort}

def main():
    ec2=get_ec2_conn()
    instances=describe_ec2_instances(ec2)
    security_groups=get_security_groups(instances)
    sgs=get_sg_rules(security_groups,ec2)
    pp.pprint(sgs)

if __name__ == '__main__':
    main()