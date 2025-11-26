import boto3
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AWSScanner:
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key
    
    def get_all_regions(self) -> List[str]:
        """Get all enabled AWS regions"""
        try:
            ec2 = boto3.client(
                'ec2',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name='us-east-1'
            )
            regions = ec2.describe_regions()['Regions']
            return [region['RegionName'] for region in regions]
        except Exception as e:
            logger.error(f"Error getting regions: {e}")
            return ['us-east-1', 'ap-south-1']
    
    def scan_region(self, region: str) -> Dict:
        """Scan a specific region"""
        results = {
            'region': region,
            'ec2': self._scan_ec2(region),
            's3': self._scan_s3(region) if region == 'us-east-1' else {},
            'rds': self._scan_rds(region),
            'lambda': self._scan_lambda(region),
            'vpc': self._scan_vpc(region),
            'iam': self._scan_iam(region) if region == 'us-east-1' else {},
            'cloudwatch': self._scan_cloudwatch(region),
        }
        return results
    
    def _scan_ec2(self, region: str) -> Dict:
        """Scan EC2 instances"""
        try:
            ec2 = boto3.client(
                'ec2',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            instances = ec2.describe_instances()
            
            instance_data = []
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_data.append({
                        'instance_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'monitoring': instance.get('Monitoring', {}).get('State', 'disabled'),
                        'public_ip': instance.get('PublicIpAddress'),
                    })
            
            return {'instances': instance_data, 'count': len(instance_data)}
        except Exception as e:
            logger.error(f"Error scanning EC2 in {region}: {e}")
            return {'instances': [], 'count': 0, 'error': str(e)}
    
    def _scan_s3(self, region: str) -> Dict:
        """Scan S3 buckets"""
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            buckets = s3.list_buckets()
            
            bucket_data = []
            for bucket in buckets['Buckets']:
                try:
                    encryption = s3.get_bucket_encryption(Bucket=bucket['Name'])
                    encrypted = True
                except:
                    encrypted = False
                
                try:
                    versioning = s3.get_bucket_versioning(Bucket=bucket['Name'])
                    versioning_enabled = versioning.get('Status') == 'Enabled'
                except:
                    versioning_enabled = False
                
                bucket_data.append({
                    'name': bucket['Name'],
                    'encrypted': encrypted,
                    'versioning': versioning_enabled,
                })
            
            return {'buckets': bucket_data, 'count': len(bucket_data)}
        except Exception as e:
            logger.error(f"Error scanning S3: {e}")
            return {'buckets': [], 'count': 0, 'error': str(e)}
    
    def _scan_rds(self, region: str) -> Dict:
        """Scan RDS instances"""
        try:
            rds = boto3.client(
                'rds',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            instances = rds.describe_db_instances()
            
            db_data = []
            for db in instances['DBInstances']:
                db_data.append({
                    'identifier': db['DBInstanceIdentifier'],
                    'engine': db['Engine'],
                    'instance_class': db['DBInstanceClass'],
                    'multi_az': db['MultiAZ'],
                    'encrypted': db.get('StorageEncrypted', False),
                    'backup_retention': db.get('BackupRetentionPeriod', 0),
                })
            
            return {'databases': db_data, 'count': len(db_data)}
        except Exception as e:
            logger.error(f"Error scanning RDS in {region}: {e}")
            return {'databases': [], 'count': 0, 'error': str(e)}
    
    def _scan_lambda(self, region: str) -> Dict:
        """Scan Lambda functions"""
        try:
            lambda_client = boto3.client(
                'lambda',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            functions = lambda_client.list_functions()
            
            func_data = []
            for func in functions['Functions']:
                func_data.append({
                    'name': func['FunctionName'],
                    'runtime': func['Runtime'],
                    'memory': func['MemorySize'],
                    'timeout': func['Timeout'],
                })
            
            return {'functions': func_data, 'count': len(func_data)}
        except Exception as e:
            logger.error(f"Error scanning Lambda in {region}: {e}")
            return {'functions': [], 'count': 0, 'error': str(e)}
    
    def _scan_vpc(self, region: str) -> Dict:
        """Scan VPC configuration"""
        try:
            ec2 = boto3.client(
                'ec2',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            vpcs = ec2.describe_vpcs()
            security_groups = ec2.describe_security_groups()
            
            return {
                'vpcs': len(vpcs['Vpcs']),
                'security_groups': len(security_groups['SecurityGroups']),
            }
        except Exception as e:
            logger.error(f"Error scanning VPC in {region}: {e}")
            return {'vpcs': 0, 'security_groups': 0, 'error': str(e)}
    
    def _scan_iam(self, region: str) -> Dict:
        """Scan IAM configuration"""
        try:
            iam = boto3.client(
                'iam',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            users = iam.list_users()
            roles = iam.list_roles()
            
            return {
                'users': len(users['Users']),
                'roles': len(roles['Roles']),
            }
        except Exception as e:
            logger.error(f"Error scanning IAM: {e}")
            return {'users': 0, 'roles': 0, 'error': str(e)}
    
    def _scan_cloudwatch(self, region: str) -> Dict:
        """Scan CloudWatch alarms"""
        try:
            cloudwatch = boto3.client(
                'cloudwatch',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region
            )
            alarms = cloudwatch.describe_alarms()
            
            return {'alarms': len(alarms['MetricAlarms'])}
        except Exception as e:
            logger.error(f"Error scanning CloudWatch in {region}: {e}")
            return {'alarms': 0, 'error': str(e)}
