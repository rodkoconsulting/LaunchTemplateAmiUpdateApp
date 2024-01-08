import boto3


IMAGE_NAME_KEY = 'Name'
LAUNCH_TEMPLATE_KEY = 'aws:ec2launchtemplate:id'


def create_ec2_client():
    return boto3.client('ec2')


def create_ec2_resource():
    return boto3.resource('ec2')


def extract_ami_id(event):
    ami_id = event["ami"]
    if not ami_id:
        raise Exception("No AMI found in event")
    return ami_id


def fetch_ami_image(ec2_client, ami_id):
    ami_images = ec2_client.describe_images(ImageIds=[ami_id])
    ami_list = ami_images.get("Images")
    ami_image = ami_list[0] if len(ami_list) > 0 else None
    if not ami_image:
        raise Exception("No AMI image found in AWS")
    return ami_image


def extract_ami_name_tag(ami_image):
    ami_tag = next((item['Value'] for item in ami_image['Tags'] if item['Key'] == IMAGE_NAME_KEY), None)
    if not ami_tag:
        raise Exception("No Name tag found in AMI")
    return ami_tag


def fetch_instance_tags(ec2_client, ami_tag):
    instances = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [ami_tag]}])
    if not instances:
        raise Exception(f"Instance not found with {ami_tag} Name tag")
    return instances.get("Reservations")[0].get("Instances")[0].get("Tags")


def extract_launch_template_id(instance_tags):
    launch_template_id = next(
        (item['Value'] for item in instance_tags if item['Key'] == LAUNCH_TEMPLATE_KEY), None)
    if not launch_template_id:
        raise Exception(f"Launch template not not found in instance tags")
    return launch_template_id


def handle_errors(action):
    try:
        return action()
    except Exception as e:
        print(f'Error: {e}')
        raise


def update_launch_template(event, source_version):
    if event["state"] != "available":
        return
    ec2_client = create_ec2_client()
    ami_id = extract_ami_id(event)
    ami_image = fetch_ami_image(ec2_client, ami_id)
    ami_tag = extract_ami_name_tag(ami_image)
    instance_tags = fetch_instance_tags(ec2_client, ami_tag)
    launch_template_id = extract_launch_template_id(instance_tags)
    ec2_client.create_launch_template_version(LaunchTemplateId=launch_template_id, SourceVersion=source_version,
                                              LaunchTemplateData={"ImageId": ami_id})


def lambda_handler(event, context):
    handle_errors(lambda: update_launch_template(event, "$Latest"))


