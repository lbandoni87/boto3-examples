import boto3
import boto3.utils
import pprint

pp=pprint.PrettyPrinter(depth=4)

def get_rds_conn(region):
    return boto3.client('rds',region_name=region)


def list_psql_rds(rds):
    rds_list=[]
    response = rds.describe_db_instances()
    for res in response['DBInstances']:
        if 'production' in res['DBInstanceIdentifier'] and 'read-replica' not in res['DBInstanceIdentifier'] and res['EngineVersion'] == '10.17':
            rds_list.append(res['DBInstanceIdentifier'])
    return rds_list

def list_mysql_rds(rds):
    rds_list=[]
    response = rds.describe_db_instances()
    for res in response['DBInstances']:
        if 'prod' in res['DBInstanceIdentifier'] and 'read-replica' not in res['DBInstanceIdentifier'] and '5.6' in res['EngineVersion']:
            rds_list.append(res['DBInstanceIdentifier'])
    return rds_list

def add_new_parameter_groups(rds,psql_list):
    for psql in psql_list:
        response = rds.modify_db_instance(
            DBInstanceIdentifier=psql,
            ApplyImmediately=True,
            DBParameterGroupName='default.postgres10',
            CloudwatchLogsExportConfiguration={
                'DisableLogTypes': [
                    'postgresql'
                ]
            }
        )
        pp.pprint(response)

def remove_audit_logs(rds,psql_list):
    for psql in psql_list:
        response = rds.modify_db_instance(
            DBInstanceIdentifier=psql,
            ApplyImmediately=True,
            CloudwatchLogsExportConfiguration={
                'DisableLogTypes': [
                    'audit'
                ]
            }
        )
        pp.pprint(response)

def main():
    region='eu-west-1'
    rds=get_rds_conn(region)
    psql_rds=list_psql_rds(rds)
    mysql_rds=list_mysql_rds(rds)
    # change_result=add_new_parameter_groups(rds,psql_rds)
    # remove_audit=remove_audit_logs(rds,mysql_rds)

if __name__ == '__main__':
    main()