import boto3

ec2_client = boto3.client('ec2')
ec2_res = boto3.resource('ec2')


def get_ami_id(event):
    ami_id = event["ami"]
    if not ami_id or ami_id is None:
        raise Exception("No AMI found in event")
    return ami_id


def get_ami_image(ami_id):
    ami_images = ec2_client.describe_images(ImageIds=[ami_id])
    ami_list = ami_images.get("Images")
    ami_image = ami_list[0] if len(ami_list) > 0 else None
    if not ami_image or ami_image is None:
        raise Exception("No AMI image found in AWS")
    return ami_image


def get_ami_tag(ami_image):
    ami_tag = next((item['Value'] for item in ami_image['Tags'] if item['Key'] == 'Name'), None)
    if not ami_tag or ami_tag is None:
        raise Exception("No Name tag found in AMI")
    return ami_tag


def get_instance_tags(ami_tag):
    instances = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [ami_tag]}])
    if not instances or instances is None:
        raise Exception(f"Instance not found with {ami_tag} Name tag")
    return instances.get("Reservations")[0].get("Instances")[0].get("Tags")


def get_launch_template_id(instance_tags):
    launch_template_id = next(
        (item['Value'] for item in instance_tags if item['Key'] == 'aws:ec2launchtemplate:id'), None)
    if not launch_template_id:
        raise Exception(f"Launch template not not found in instance tags")


def update_launch_template(event):
    if event["state"] != "available":
        return
    ami_id = get_ami_id(event)
    ami_image = get_ami_image(ami_id)
    ami_tag = get_ami_tag(ami_image)
    instance_tags = get_instance_tags(ami_tag)
    launch_template_id = get_launch_template_id(instance_tags)
    ec2_client.create_launch_template_version(LaunchTemplateId=launch_template_id, SourceVersion="$Latest",
                                              LaunchTemplateData={"ImageId": ami_id})


def handle_errors(action):
    try:
        return action()
    except Exception as e:
        print(f'Error: {e}')
        raise


def lambda_handler(event, context):
    handle_errors(lambda: update_launch_template(event))
