import boto3, pprint, json

def get_iam_conn(region):
    return boto3.client('iam', region_name=region)


def lambda_conn(region):
    return boto3.client('lambda', region_name=region)


def create_role(iam, trust_policy):
    iam_role = iam.create_role(
        Path='/',
        RoleName='leos-params-for-lambda',
        AssumeRolePolicyDocument=json.dumps(trust_policy, indent=2)
    )
    return iam_role


def attach_lambda_policy(iam,iam_role):
    RoleName = iam_role['Role'].get('RoleName')
    attach_policy = iam.attach_role_policy(
        RoleName=RoleName,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )
    return attach_policy


def get_iam_role_arn(iam_role):
    arn = iam_role['Role'].get('Arn')
    return arn

def create_function(Lambda, role_arn,zfile):
    with open(zfile, 'rb') as zipfile:
        lambda_function = Lambda.create_function(
            FunctionName='test-lambda',
            Runtime='python3.7',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={
                "ZipFile": zipfile.read()
            }
        )
        return lambda_function


def main():
    region="eu-west-1"
    iam = get_iam_conn(region)
    Lambda = lambda_conn(region)
    trust_policy={
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    iam_role = create_role(iam, trust_policy)
    attach_lambda_policy(iam, iam_role)
    role_arn = get_iam_role_arn(iam_role)
    create_function(Lambda, role_arn, 'hello_parameters.zip')

if __name__ == '__main__':
    main()