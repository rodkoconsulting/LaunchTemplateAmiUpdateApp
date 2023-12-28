import unittest
from LaunchTemplateAmiUpdate import app
from pathlib import Path
import boto3


class IntegrationTestHandlerCase(unittest.TestCase):

    def test_response(self):
        print("Testing calls from lambda function")
        path = Path(__file__).parent / "../../events/event.json"
        with path.open as f:
            event = f.read()
        ami_id = app.extract_ami_id(event)
        self.assertIs(ami_id, event["ami"])
        ec2_client = app.create_ec2_client()
        ami_image = app.fetch_ami_image(ec2_client, ami_id)
        self.assertIsNotNone(ami_image)
        ami_tag = app.extract_ami_name_tag(ami_image)
        self.assertIsNotNone(ami_tag)
        instance_tags = app.fetch_instance_tags(ec2_client, ami_tag)
        self.assertIsNotNone(instance_tags)
        launch_template_id = app.extract_launch_template_id(instance_tags)
        self.assertIsNotNone(launch_template_id)


if __name__ == '__main__':
    unittest.main()
