import boto3
import pprint

pp=pprint.PrettyPrinter(depth=4)

def get_route53_conn():
    session = boto3.Session(profile_name='read')
    return session.client('route53',region_name='eu-west-1')

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

def get_hosted_zone_id(route53):
    hosted_zones = route53.list_hosted_zones()
    return [
        hz_value
        for hosted_zone in hosted_zones['HostedZones']
        for hz_key, hz_value in hosted_zone.items()
        if hz_key == 'Id'
    ]

def describe_record_sets(route53,hosted_zone_ids):
    rs_list=[]
    for hosted_zone_id in hosted_zone_ids:
        record_sets = route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id
        )
        rs_item = {
            record_set['Name'] : record_set.get("AliasTarget")
            if record_set['Name'] not in record_sets['ResourceRecordSets']
            else
            record_set['Name'].append(record_set.get("AliasTarget"))
            for record_set in record_sets['ResourceRecordSets']
        }
        rs_list.append(rs_item)
    return rs_list

def main():
    route53 = get_route53_conn()
    hosted_zones_ids = get_hosted_zone_id(route53)
    record_sets = describe_record_sets(route53, hosted_zones_ids)
    pp.pprint(record_sets)

if __name__ == '__main__':
    main()