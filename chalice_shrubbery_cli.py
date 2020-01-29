import click
import datetime
import json
import subprocess
import botocore.session
import os

def run_process(label, command):
    print(label)
    print()
    print(' '.join(command))
    print()
    output = subprocess.check_output(command, shell=False)
    print(output.decode())

def get_config_json():
    with open('.chalice/config.json') as json_file:
        return json.load(json_file)

def get_s3_bucket_name(stage, profile):

    config = get_config_json()

    if 'stages' in config:
        if stage in config['stages']:
            stage_config = config['stages'][stage]
            if 'shrubbery.s3_bucket' in stage_config:
                return stage_config['shrubbery.s3_bucket']

    if 'shrubbery.s3_bucket' in config:
        return config['shrubbery.s3_bucket']

    session = botocore.session.get_session()
    client = session.create_client('sts')

    account_id = client.get_caller_identity()['Account']
    s3_bucket = 'chalice-shrubbery-' + account_id

    return s3_bucket

def get_stack_name(stage):

    config = get_config_json()

    if 'stages' in config:
        if stage in config['stages']:
            stage_config = config['stages'][stage]
            if 'shrubbery.stack_name' in stage_config:
                return stage_config['shrubbery.stack_name']

    if 'shrubbery.stack_name' in config:
        return config['shrubbery.stack_name']

    return config['app_name']

@click.group()
def cli():
    pass

def apply_transformations(chalice_template_file, stack_name):
    with open(chalice_template_file) as json_file:
        template_json = json.load(json_file)

    if 'Outputs' in template_json:
        for output in template_json['Outputs']:
            output_config = template_json['Outputs'][output]
            output_config['Export'] = {
                'Name': stack_name + ':' + output
            }
    
    if 'Resources' in template_json:
        for resource in template_json['Resources']:
            resource_config = template_json['Resources'][resource]
            if resource_config['Type'] == 'AWS::Serverless::Function':
                resource_config['Properties']['FunctionName'] = stack_name + '-' + resource
    
    config = get_config_json()

    if 'validation' in config:
        definition = template_json['Resources']['RestAPI']['Properties']['DefinitionBody']
        definition['x-amazon-apigateway-request-validators'] = {"all": {"validateRequestBody": True, "validateRequestParameters": True},"params-only": {"validateRequestBody": False,"validateRequestParameters": True}}
        definition['definitions'] = config['validation']['definitions']
        params = config['validation']['parameters']
        for path in params:
            for method in params[path]:
                definition['paths'][path][method]["x-amazon-apigateway-request-validator"] = "all"
                definition['paths'][path][method]['parameters'] = params[path][method]

    with open(chalice_template_file, 'w') as outfile:
        json.dump(template_json, outfile)

@click.command(help='Deploy a Chalice project to AWS using CloudFormation')
@click.option('--stage', required=True, default='dev', help='Specify the Chalice stage to operate upon')
@click.option('--profile', help='Provide the name of an AWS CLI profile to use for operations')
@click.option('--merge-template', default=None, help='Specify a JSON template to be merged into the generated template. This is useful for adding resources to a Chalice template or modify values in the template. CloudFormation Only.')
def deploy(stage, profile, merge_template):

    if profile is not None:
        os.environ['AWS_PROFILE'] = profile

    s3_bucket_name = get_s3_bucket_name(stage, profile)
    stack_name = get_stack_name(stage)

    chalice_package_output_folder = '.chalice/deployments/shrubbery/{0}'.format(stage)
    chalice_template_file = '{0}/sam.json'.format(chalice_package_output_folder)
    packaged_template_file = '{0}/packaged.json'.format(chalice_package_output_folder)
    s3_prefix = 'chalice-shrubbery/{0}/{1}/{2}'.format(stack_name, stage, datetime.datetime.now().isoformat())
    s3_template_file = 's3://{0}/{1}/packaged.json'.format(s3_bucket_name, s3_prefix)

    chalice_command = [
        'chalice', 'package',
        '--stage', stage,
        chalice_package_output_folder
    ]

    if merge_template:
        chalice_command = [
            'chalice', 'package',
            '--stage', stage,
            '--merge-template', merge_template,
            chalice_package_output_folder
        ]

    run_process('Using chalice to create deployment package template...', chalice_command)

    apply_transformations(chalice_template_file, stack_name)

    aws_package_command = [
        'aws', 'cloudformation', 'package', 
        '--template-file', chalice_template_file,
        '--s3-bucket', s3_bucket_name,
        '--s3-prefix', s3_prefix,
        '--output-template-file', packaged_template_file,
        '--use-json'
    ]
    run_process('Running cloud formation package on deployment template...', aws_package_command)

    aws_s3_command = [
        'aws', 's3', 'cp', 
        packaged_template_file,
        s3_template_file
    ]
    run_process('Uploading cloud formation package to S3...', aws_s3_command)

    aws_deploy_command = [
        'aws', 'cloudformation', 'deploy', 
        '--template-file', packaged_template_file,
        '--stack-name', stack_name,
        '--capabilities', 'CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM',
        '--s3-bucket', s3_bucket_name
    ]
    run_process('Deploying cloud formation change set...', aws_deploy_command)
 
@click.command(help='Delete a deployed Chalice project CloudFormation stack')
@click.option('--stage', required=True, default='dev', help='Specify the Chalice stage to operate upon')
@click.option('--profile', help='Provide the name of an AWS CLI profile to use for operations')
def delete(stage, profile):

    if profile is not None:
        os.environ['AWS_PROFILE'] = profile

    stack_name = get_stack_name(stage)

    aws_delete_command = [
        'aws', 'cloudformation', 'delete-stack', 
        '--stack-name', stack_name
    ]
    run_process('Deleting cloud formation stack...', aws_delete_command)

@click.command(help='Describe an existing Chalice project CloudFormation stack')
@click.option('--stage', required=True, default='dev', help='Specify the Chalice stage to operate upon')
@click.option('--profile', help='Provide the name of an AWS CLI profile to use for operations')
def describe(stage, profile):

    if profile is not None:
        os.environ['AWS_PROFILE'] = profile

    stack_name = get_stack_name(stage)

    aws_describe_command = [
        'aws', 'cloudformation', 'describe-stacks', 
        '--stack-name', stack_name
    ]
    subprocess.run(aws_describe_command)

cli.add_command(deploy)
cli.add_command(delete)
cli.add_command(describe)

if __name__ == "__main__":
    cli()
