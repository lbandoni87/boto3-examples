import boto3
import argparse
import pprint
import csv

pp=pprint.PrettyPrinter(depth=4)

def parse_entry():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--dir', help='path to the directory to store the ssm parameters report, defaults to tmp directory', default='/tmp/')
    args_parser.add_argument('--prefix', help='ssm prefix, for example /OSM/ or /NGSS/ \'/\' will show all parameters and is the default', default='/')
    return args_parser.parse_args()

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

def get_ssm_conn():
    session = boto3.Session(profile_name='read')
    return session.client('ssm',region_name='eu-west-1')

def get_file_prefix(prefix):
    file_prefix=prefix.replace('/','-')[1:-1]
    if file_prefix == '-':
        file_prefix = ''
    return file_prefix

def get_parameters(ssm,prefix):
    kwargs={
        'Path': prefix,
        'Recursive' : True,
        'MaxResults' : 10
    }
    return paginated_call(ssm.get_parameters_by_path, 'Parameters', kwargs)

def filter_parameters(parameters):
    return {
        str(parameter['Name']) : { 'Value': str(parameter['Value'].replace(',', '')),
                              'Type': str(parameter['Type'])}
        for parameter in parameters
    }

def create_report(parameters,filename):
    with open(filename,'wt') as result:
        fields=[
            'Parameter',
            'Value',
            'Type'
        ]
        w = csv.writer(result, delimiter=',', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(fields)
        for parameter_name ,parameter_value in parameters.items():
            row = write_metric_row(parameter_name, parameter_value)
            result.write('{0}\n'.format(str(row)[1:-1].replace('\'', '')))
    return result

def write_metric_row(parameter_name, parameter_value):
    row = [
        parameter_name,
        parameter_value['Value'],
        parameter_value['Type']
    ]
    return row

def main():
    arguments = parse_entry()
    prefix = arguments.prefix
    dir = arguments.dir
    file_prefix=get_file_prefix(prefix)
    filename=dir+str(file_prefix)+'ssm-parameters.csv'
    ssm=get_ssm_conn()
    parameters=get_parameters(ssm,prefix)
    parameters=filter_parameters(parameters)
    create_report(parameters,filename)

if __name__ == '__main__':
    main()