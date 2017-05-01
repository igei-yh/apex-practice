# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class AutoBackup(object):
    """Create and Delete Image of ec2 instance

    Create Image of ec2 instance for backup.
    Delete Image and snapshot.

    Attributes:
        backup_tag: Tag for filtering instances to be backup.
        rotation_tag: Tag for identifying the number of backup generations.
    """
    def __init__(self):
        """ Inits of service request at boto3 """
        self.ec2 = boto3.resource('ec2')
        self.__backup_tag = 'AutoBackup'
        self.__rotation_tag = 'Backup'

    def work_backup(self):
        """Main function of AutoBackup"""
        start_time = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info('AutoBackup Started at %s', start_time)
        instances = self._filter_instances()
        try:
            for instance in instances:
                logger.info('AutoBackup Target Instance : %s', instance.id)
                image = self._create_image(instance)
                self._tagging_resource(image)

                rotation = self._get_rotation_tag(instance)
                images = self._filter_images(instance)
                self._delete_image(images, rotation)

        except Exception as e:
            print(type(e))
            print('AutoBackup Error : %s', e.message)
            raise

        end_time = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info('AutoBackup End at %s', end_time)
        return True

    def _filter_instances(self):
        filter = []
        f = {'Name': 'tag-key', 'Values': [self.__backup_tag]}
        filter.append(f)
        instances = self.ec2.instances.filter(Filters=filter)
        return instances

    def _create_image(self, instance):
        dt = datetime.now().strftime('%Y%m%d%H%M%S')
        image = instance.create_image(
            Name=self.__backup_tag + '-' + instance.id + '-' + dt,
            NoReboot=True
        )
        return image

    def _tagging_resource(self, image):
        tags = []
        t = {'Key': 'Name', 'Value': image.name}
        tags.append(t)
        image.create_tags(Tags=tags)
        logger.info('Tagging resource %s', image.id)
        for b in image.block_device_mappings:
            if 'Ebs' in b:
                snapshot = self.ec2.Snapshot(b['Ebs']['SnapshotId'])
                snapshot.create_tags(Tags=tags)

    def _get_rotation_tag(self, instance):
        for tag in instance.tags:
            if not (self.__rotation_tag == tag['Key']):
                continue

            return tag['Value']

    def _filter_images(self, instance):
        filter = []
        f = {'Name': 'name', 'Values': ['*' + instance.id + '*']}
        filter.append(f)
        images = self.ec2.images.filter(Filters=filter)
        return images

    def _delete_image(self, images, rotation):
        target_images = self._sort_image(images, rotation)
        for image in target_images:
            snapshots = self.get_snapshots(image)
            image.deregister()
            for snapshot in snapshots:
                snapshot.delete()

    def _sort_image(self, images, rotation):
        images = []
        sorted_images = []
        for image in images:
            images.append((image.id, image.creation_date))
        sorted(images, key=lambda x: x[1])

        delete_count = len(images) - int(rotation)
        if delete_count <= 0:
            return sorted_images

        for i in range(delete_count):
            sorted_images.append(self.ec2.Image(images[i][0]))
        return sorted_images

    def _get_snapshots(self, image):
        snapshots = []
        for b in image.block_device_mappings:
            if 'Ebs' not in b:
                continue
            s = self.ec2.Snapshot(b['Ebs']['SnapshotId'])
            snapshots.append(s)
        return snapshots


def handle(event, context):

    backup = AutoBackup()
    message = backup.work_backup()

    return {
        'message': message
    }
