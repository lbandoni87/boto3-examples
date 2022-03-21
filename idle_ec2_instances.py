import boto3
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

def get_ec2_conn():
    session = boto3.Session(profile_name='read')
    return session.client('ec2',region_name='eu-west-1')

def get_cw_conn():
    session = boto3.Session(profile_name='read')
    return session.client('cloudwatch',region_name='eu-west-1')

def get_ec2_instances(ec2):
    instances=[]
    response=ec2.describe_instances()
    for res in response['Reservations']:
        for instance in res['Instances']:
            InstanceId=instance.get('InstanceId')
            State=instance.get('State')
            state=State.get('Name')
            if state == 'running':
                instances.append(InstanceId)
    return instances

def get_ec2_cpu(cloudwatch,instances):
    results={}
    for ins in instances:
        kwargs={'Namespace':'AWS/EC2',
                'MetricName':'CPUUtilization',
                'Dimensions':[
                    {
                        'Name': 'InstanceId',
                        'Value': ins
                    }
                ],
                'Period': 3600,
                'Statistics': ['Average'],
                'StartTime':datetime.datetime.utcnow() - timedelta(seconds=604800),
                'EndTime':datetime.datetime.utcnow()
                }
        result=paginated_call(cloudwatch.get_metric_statistics, 'Datapoints', kwargs)
        find_average(ins, result, results,'CPUUtilization')
    return results

def get_ec2_networkin(cloudwatch,instances):
    results={}
    for ins in instances:
        kwargs={'Namespace':'AWS/EC2',
                'MetricName':'NetworkIn',
                'Dimensions':[
                    {
                        'Name': 'InstanceId',
                        'Value': ins
                    }
                ],
                'Period': 3600,
                'Statistics': ['Average'],
                'StartTime':datetime.datetime.utcnow() - timedelta(seconds=604800),
                'EndTime':datetime.datetime.utcnow()
                }
        result=paginated_call(cloudwatch.get_metric_statistics, 'Datapoints', kwargs)
        find_average(ins, result, results,'NetworkIn')
    return results

def get_ec2_networkOut(cloudwatch,instances):
    results={}
    for ins in instances:
        kwargs={'Namespace':'AWS/EC2',
                'MetricName':'NetworkOut',
                'Dimensions':[
                    {
                        'Name': 'InstanceId',
                        'Value': ins
                    }
                ],
                'Period': 3600,
                'Statistics': ['Average'],
                'StartTime':datetime.datetime.utcnow() - timedelta(seconds=604800),
                'EndTime':datetime.datetime.utcnow()
                }
        result=paginated_call(cloudwatch.get_metric_statistics, 'Datapoints', kwargs)
        find_average(ins, result, results,'NetworkOut')
    return results

def find_average(ins, result, results,metric):
    average_list = []
    for avr in result:
        average = avr.get('Average')
        average_list.append(average)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        al = numpy.array(average_list, numpy.float)
        Average = numpy.mean(al)
        results[ins] = {metric:Average}

def combine_results(ec2_cpu,networkIn,NetworkOut):
    dic_list=[ec2_cpu,networkIn,NetworkOut]
    dic={}
    for k in ec2_cpu.keys():
        dic[k]=tuple(dic[k] for dic in dic_list)
    return dic

def create_report(complete_results,filename):
    with open(filename,'wt') as result:
        fields=[
            'instances',
            'Average CPU (2 weeks)',
            'Average NetworkIn (2 weeks)',
            'Average NetworkOut (2 weeks)'
        ]
        w = csv.writer(result, delimiter=',', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(fields)
        for instance,metrics in complete_results.items():
            row = write_metric_row(instance, metrics)
            result.write('{0}\n'.format(str(row)[1:-1].replace('\'', '')))
    return result

def write_metric_row(instance, metrics):
    for metric, mvalue in metrics[0].items():
        CPU = mvalue
    for metric, mvalue in metrics[1].items():
        networkIn = mvalue
    for metric, mvalue in metrics[2].items():
        networkOut = mvalue
    row = [
        instance,
        CPU,
        networkIn,
        networkOut
    ]
    return row

def main():
    ec2=get_ec2_conn()
    cloudwatch=get_cw_conn()
    instances=get_ec2_instances(ec2)
    ec2_cpu=get_ec2_cpu(cloudwatch,instances)
    networkIn=get_ec2_networkin(cloudwatch,instances)
    NetworkOut=get_ec2_networkOut(cloudwatch,instances)
    complete_results=combine_results(ec2_cpu,networkIn,NetworkOut)
    date = datetime.date.today()
    filename='/home/Documents/inactive_instances-'+str(date)+'.csv'
    create_report(complete_results,filename)

if __name__ == '__main__':
    main()