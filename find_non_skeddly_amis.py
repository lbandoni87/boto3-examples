import boto3
import pprint
import datetime
from datetime import datetime, timezone
import csv
from itertools import groupby

pp=pprint.PrettyPrinter(depth=4)


def get_ec2_conn():
    return boto3.client('ec2', region_name='eu-west-1')


def describe_amis(ec2):
    amis = ec2.describe_images(
        Owners = ['self']
    )
    return [
        ami
        for ami in amis['Images']
        if 'SKEDDLY' not in ami['Name']
    ]


def create_report(non_skeddly_amis, filename):
    with open(filename, 'wt') as result:
        fields = ["Name",
                  "AMI",
                  "Description",
                  "CreationDate"]
        w = csv.writer(result, delimiter=',',
                       quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(fields)
        for amis in non_skeddly_amis:
            imageid = amis.get('ImageId')
            name = amis.get('Name')
            description = amis.get('Description')
            if description is not None:
                description = description.replace(',', '')
            creationdate = amis.get('CreationDate')[:10]
            row = [
                name,
                imageid,
                description,
                creationdate
            ]
            result.write('{0}\n'.format(str(row)[1:-1].replace('\'', '')))
    return result


def main():
    ec2 = get_ec2_conn()
    now = datetime.now()
    non_skeddly_amis = describe_amis(ec2)
    filename = '/home/Documents/non-skeddly-report.'+now.strftime("%d:%m:%Y")+'.csv'
    create_report(non_skeddly_amis,filename)

if __name__ == '__main__':
    main()