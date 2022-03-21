import boto3
import boto3.utils
import pprint
import datetime
import csv
from datetime import timedelta
import numpy
import warnings

pp=pprint.PrettyPrinter(depth=4)

def paginated_call(func, response_filter, kwargs):
    result = []
    while True:
        response = func(**kwargs)
        result.extend(response[response_filter])
        next_token = response.get('NextToken')
        kwargs.update({"NextToken": next_token})
        if not next_token:
            break
    return result

def get_cw_conn(region):
    return boto3.client('cloudwatch',region_name=region)

def get_rds_conn(region):
    return boto3.client('rds',region_name=region)

def get_rds_names(rds):
    dbinstances={}
    rdss=rds.describe_db_instances()
    for rds in rdss['DBInstances']:
        DBInstanceIdentifier=rds.get('DBInstanceIdentifier')
        DBInstanceType = rds.get('DBInstanceClass')
        Engine = rds.get('Engine')
        if rds['DBInstanceStatus'] == 'available':
            dbinstances[DBInstanceIdentifier]={'instance type' : DBInstanceType, 'Engine': Engine}
    return dbinstances

def get_dbconnections(cloudwatch,databases):
    results={}
    for db in databases:
        kwargs={'Namespace':'AWS/RDS',
                'MetricName':'DatabaseConnections',
                'Dimensions':[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db
                    }
                ],
                'Period': 3000,
                'Statistics': ['Average'],
                'StartTime':datetime.datetime.utcnow() - timedelta(seconds=604800),
                'EndTime':datetime.datetime.utcnow()
                }
        result=paginated_call(cloudwatch.get_metric_statistics, 'Datapoints', kwargs)
        find_average(db, result, results,'DatabaseConnections')
    return results

def get_readIOPS(cloudwatch,databases):
    results={}
    for db in databases:
        kwargs={'Namespace':'AWS/RDS',
                'MetricName':'ReadIOPS',
                'Dimensions':[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db
                    }
                ],
                'Period': 3000,
                'Statistics': ['Average'],
                'StartTime':datetime.datetime.utcnow() - timedelta(seconds=604800),
                'EndTime':datetime.datetime.utcnow()
                }
        result=paginated_call(cloudwatch.get_metric_statistics, 'Datapoints', kwargs)
        find_average(db, result, results,'ReadIOPS')
    return results

def get_writeIOPS(cloudwatch,databases):
    results={}
    for db in databases:
        kwargs={'Namespace':'AWS/RDS',
                'MetricName':'WriteIOPS',
                'Dimensions':[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db
                    }
                ],
                'Period': 3000,
                'Statistics': ['Average'],
                'StartTime':datetime.datetime.utcnow() - timedelta(seconds=604800),
                'EndTime':datetime.datetime.utcnow()
                # 'StartTime' : datetime.datetime(2019, 11, 4),
                # 'EndTime' : datetime.datetime(2019, 11, 18)
                }
        result=paginated_call(cloudwatch.get_metric_statistics, 'Datapoints', kwargs)
        find_average(db, result, results,'WriteIOPS')
    return results

def find_average(db, result, results, metric):
    average_list = []
    for avr in result:
        average = avr.get('Average')
        average_list.append(average)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        al = numpy.array(average_list, numpy.float)
        Average = numpy.mean(al)
        results[db] = {metric:Average}

def combine_results(dbconnections,readIOPS,writeIOPS,databases):
    dic_list=[dbconnections,readIOPS,writeIOPS,databases]
    dic={}
    for k in databases.keys():
        dic[k]=tuple(dic[k] for dic in dic_list)
    return dic

def create_report(complete_results, filename):
    with open(filename,'wt') as result:
        fields=[
            'Database Identifer',
            'Average Database Connections (2 weeks)',
            'Average Read IOPS (2 weeks)',
            'Average Write IOPS (2 weeks)',
            'Instance Type',
            'Database Type'
        ]
        w = csv.writer(result, delimiter=',', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(fields)
        for db, metrics in complete_results.items():
            row = write_metric_row(db, metrics)
            result.write('{0}\n'.format(str(row)[1:-1].replace('\'', '')))
    return result

def write_metric_row(db, metrics):
    DatabaseConnections = metrics[0].get('DatabaseConnections')
    readIOPS = metrics[1].get('ReadIOPS')
    writeIOPS = metrics[2].get('WriteIOPS')
    instance_type = metrics[3].get('instance type')
    engine = metrics[3].get('Engine')
    row = [
        db,
        DatabaseConnections,
        readIOPS,
        writeIOPS,
        instance_type,
        engine
    ]
    return row

def main():
    date = datetime.date.today()
    region=input('Region, eu-west-1 or us-west-2: ')
    cloudwwatch=get_cw_conn(region)
    rds=get_rds_conn(region)
    databases=get_rds_names(rds)
    dbconnections=get_dbconnections(cloudwwatch,databases)
    readIOPS=get_readIOPS(cloudwwatch,databases)
    writeIOPS=get_writeIOPS(cloudwwatch,databases)
    complete_results=combine_results(dbconnections,readIOPS,writeIOPS,databases)
    filename='/home/Documents/inactive_rds-busy-'+region+'-'+str(date)+'.csv'
    create_report(complete_results,filename)

if __name__ == '__main__':
    main()