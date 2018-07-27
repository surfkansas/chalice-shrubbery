import click
import datetime
import json
import subprocess

def apply_profile_to_aws_command(aws_command, profile):
    if profile is not None:
        aws_command.append('--profile')
        aws_command.append(profile)

def run_process(label, command):
    print(label)
    print()
    print(' '.join(command))
    print()
    output = subprocess.check_output(command, shell=False)
    print(output.decode())

def get_config(stage, config_name):
    with open('.chalice/config.json') as json_file:
        config = json.load(json_file)
        return config['stages'][stage]['shrubbery.' + config_name]

@click.group()
def cli():
    pass

@click.command(help='Deploy a Chalice project to AWS using CloudFormation')
@click.option('--stage', required=True, help='Specify the Chalice stage to operate upon')
@click.option('--profile', help='Provide the name of an AWS CLI profile to use for operations')
def deploy(stage, profile):

    s3_bucket_name = get_config(stage, 's3_bucket')
    stack_name = get_config(stage, 'stack_name')

    chalice_package_output_folder = '.chalice/deployments/shrubbery/{0}'.format(stage)
    chalice_template_file = '{0}/sam.json'.format(chalice_package_output_folder)
    packaged_template_file = '{0}/packaged.yml'.format(chalice_package_output_folder)
    s3_prefix = 'chalice-shrubbery/{0}/{1}/{2}'.format(stack_name, stage, datetime.datetime.now().isoformat())
    s3_template_file = 's3://{0}/{1}/packaged.yml'.format(s3_bucket_name, s3_prefix)

    chalice_command = [
        'chalice', 'package',
        '--stage', stage,
        chalice_package_output_folder
    ]
    run_process('Using chalice to create deployment package template...', chalice_command)

    aws_package_command = [
        'aws', 'cloudformation', 'package', 
        '--template-file', chalice_template_file,
        '--s3-bucket', s3_bucket_name,
        '--s3-prefix', s3_prefix,
        '--output-template-file', packaged_template_file 
    ]
    apply_profile_to_aws_command(aws_package_command, profile)
    run_process('Running cloud formation package on deployment template...', aws_package_command)

    aws_s3_command = [
        'aws', 's3', 'cp', 
        packaged_template_file,
        s3_template_file
    ]
    apply_profile_to_aws_command(aws_s3_command, profile)
    run_process('Uploading cloud formation package to S3...', aws_s3_command)

    aws_deploy_command = [
        'aws', 'cloudformation', 'deploy', 
        '--template-file', packaged_template_file,
        '--stack-name', stack_name,
        '--capabilities', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'
    ]
    apply_profile_to_aws_command(aws_deploy_command, profile)
    run_process('Deploying cloud formation change set...', aws_deploy_command)
 
@click.command(help='Delete a deployed Chalice project CloudFormation stack')
@click.option('--stage', required=True, help='Specify the Chalice stage to operate upon')
@click.option('--profile', help='Provide the name of an AWS CLI profile to use for operations')
def delete(stage, profile):

    stack_name = get_config(stage, 'stack_name')

    aws_delete_command = [
        'aws', 'cloudformation', 'delete-stack', 
        '--stack-name', stack_name
    ]
    apply_profile_to_aws_command(aws_delete_command, profile)
    run_process('Deleting cloud formation stack...', aws_delete_command)

@click.command(help='Describe an existing Chalice project CloudFormation stack')
@click.option('--stage', required=True, help='Specify the Chalice stage to operate upon')
@click.option('--profile', help='Provide the name of an AWS CLI profile to use for operations')
def describe(stage, profile):

    stack_name = get_config(stage, 'stack_name')

    aws_describe_command = [
        'aws', 'cloudformation', 'describe-stacks', 
        '--stack-name', stack_name
    ]
    apply_profile_to_aws_command(aws_describe_command, profile)
    subprocess.run(aws_describe_command)

cli.add_command(deploy)
cli.add_command(delete)
cli.add_command(describe)

if __name__ == "__main__":
    cli()