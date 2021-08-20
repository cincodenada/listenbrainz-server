import os
import uuid
import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import tarfile

import listenbrainz_spark
import listenbrainz_spark.utils.mapping as mapping_utils
from listenbrainz_spark.hdfs.upload import ListenbrainzDataUploader
from listenbrainz_spark.path import LISTENBRAINZ_NEW_DATA_DIRECTORY
from listenbrainz_spark.recommendations import dataframe_utils
from listenbrainz_spark import hdfs_connection, utils, config, schema
from listenbrainz_spark.recommendations.dataframe_utils import save_dataframe
from listenbrainz_spark.recommendations.recording import train_models

from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, IntegerType

from listenbrainz_spark.utils import get_listens_from_new_dump

TEST_PLAYCOUNTS_PATH = '/tests/playcounts.parquet'
TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'testdata')
PLAYCOUNTS_COUNT = 100


class SparkNewTestCase(unittest.TestCase):

    uploader = None
    # create a very long time window to fetch all listens from storage
    begin_date = datetime(2005, 1, 1)
    end_date = datetime(2025, 1, 1)

    @classmethod
    def setUpClass(cls) -> None:
        listenbrainz_spark.init_test_session(f"spark-test-run-{uuid.uuid4()}")
        hdfs_connection.init_hdfs(config.HDFS_HTTP_URI)
        cls.uploader = ListenbrainzDataUploader()

    @classmethod
    def tearDownClass(cls):
        listenbrainz_spark.context.stop()

    @classmethod
    def delete_dir(cls):
        walk = utils.hdfs_walk('/', depth=1)
        # dirs in '/'
        dirs = next(walk)[1]
        for directory in dirs:
            utils.delete_dir(os.path.join('/', directory), recursive=True)

    @staticmethod
    def create_temp_listens_tar(name: str):
        """ Create a temporary tar file containing test listens data.
            Args:
                name: the name of the directory inside testdata
                    which contains test listens data
            Returns:
                the tar file containing the listens
        """
        full_dump_path = os.path.join(TEST_DATA_PATH, name)
        files = os.listdir(full_dump_path)
        with NamedTemporaryFile('wb', suffix='.tar', delete=False) as dump_tar:
            dump_name = Path(dump_tar.name).stem
            with tarfile.open(fileobj=dump_tar, mode='w') as tar:
                for filename in files:
                    src_path = os.path.join(full_dump_path, filename)
                    dest_path = os.path.join(dump_name, filename)
                    tar.add(src_path, arcname=dest_path)
        return dump_tar

    @classmethod
    def upload_test_listens(cls):
        full_dump_tar = cls.create_temp_listens_tar('full-dump')
        inc_dump1_tar = cls.create_temp_listens_tar('incremental-dump-1')
        inc_dump2_tar = cls.create_temp_listens_tar('incremental-dump-2')
        cls.uploader.upload_new_listens_full_dump(full_dump_tar.name)
        cls.uploader.upload_new_listens_incremental_dump(inc_dump1_tar.name)
        cls.uploader.upload_new_listens_incremental_dump(inc_dump2_tar.name)

    @staticmethod
    def delete_uploaded_listens():
        if utils.path_exists(LISTENBRAINZ_NEW_DATA_DIRECTORY):
            utils.delete_dir(LISTENBRAINZ_NEW_DATA_DIRECTORY, recursive=True)

    @staticmethod
    def path_to_data_file(file_name):
        """ Returns the path of the test data file relative to listenbrainz_spark/test/__init__.py.

            Args:
                file_name: the name of the data file
        """
        return os.path.join(TEST_DATA_PATH, file_name)

    @classmethod
    def get_all_test_listens(cls):
        return get_listens_from_new_dump(cls.begin_date, cls.end_date)


class SparkTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        listenbrainz_spark.init_test_session('spark-test-run-{}'.format(str(uuid.uuid4())))
        hdfs_connection.init_hdfs(config.HDFS_HTTP_URI)
        cls.date = datetime(2019, 1, 21)

    @classmethod
    def tearDownClass(cls):
        listenbrainz_spark.context.stop()

    @classmethod
    def delete_dir(cls):
        walk = utils.hdfs_walk('/', depth=1)
        # dirs in '/'
        dirs = next(walk)[1]
        for directory in dirs:
            utils.delete_dir(os.path.join('/', directory), recursive=True)

    @classmethod
    def upload_test_playcounts(cls):
        schema = StructType(
            [
                StructField("user_id", IntegerType()),
                StructField("recording_id", IntegerType()),
                StructField("count", IntegerType())
            ]
        )
        test_playcounts = []
        for i in range(1, PLAYCOUNTS_COUNT // 2 + 1):
            test_playcounts.append([1, 1, 1])
        for i in range(PLAYCOUNTS_COUNT // 2 + 1, PLAYCOUNTS_COUNT + 1):
            test_playcounts.append([2, 2, 1])
        test_playcounts_df = listenbrainz_spark.session.createDataFrame(test_playcounts, schema=schema)
        utils.save_parquet(test_playcounts_df, TEST_PLAYCOUNTS_PATH)

    @classmethod
    def split_playcounts(cls):
        test_playcounts_df = utils.read_files_from_HDFS(TEST_PLAYCOUNTS_PATH)
        training_data, validation_data, test_data = train_models.preprocess_data(test_playcounts_df)
        return training_data, validation_data, test_data

    @classmethod
    def get_users_df(cls):
        df = utils.create_dataframe(
            Row(
                user_name='vansika',
                user_id=1
            ),
            schema=None
        )
        users_df = df.union(utils.create_dataframe(
            Row(
                user_name='rob',
                user_id=2
            ),
            schema=None
        ))
        return users_df

    @classmethod
    def get_recordings_df(cls):
        return listenbrainz_spark.session.createDataFrame([
            Row(artist_credit_id=1,
                artist_credit_mbids=["181c4177-f33a-441d-b15d-910acaf18b07"],
                recording_mbid="3acb406f-c716-45f8-a8bd-96ca3939c2e5",
                release_mbid="xxxxxx",
                recording_id=1),
            Row(artist_credit_id=2,
                artist_mbids=["281c4177-f33a-441d-b15d-910acaf18b07"],
                recording_mbid="2acb406f-c716-45f8-a8bd-96ca3939c2e5",
                release_mbid="xxxxxx",
                recording_id=2)
            ])

    @classmethod
    def get_candidate_set(cls):
        return listenbrainz_spark.session.createDataFrame([
            Row(user_id=1, recording_id=1, user_name='vansika'),
            Row(user_id=2, recording_id=2, user_name='rob')
        ])

    @classmethod
    def path_to_data_file(cls, file_name):
        """ Returns the path of the test data file relative to listenbrainz_spark/test/__init__.py.

            Args:
                file_name: the name of the data file
        """
        return os.path.join(TEST_DATA_PATH, file_name)

    @classmethod
    def get_dataframe_metadata(cls, df_id):
        metadata = {
            'dataframe_id': df_id,
            'from_date': datetime.utcnow(),
            'listens_count': 100,
            'playcounts_count': 100,
            'recordings_count': 100,
            'to_date': datetime.utcnow(),
            'users_count': 100,
        }
        return metadata

    @classmethod
    def get_model_metadata(cls, model_id):
        metadata = {
            'dataframe_id': 'xxxxx',
            'model_id': model_id,
            'alpha': 3.0,
            'lmbda': 2.0,
            'iteration': 2,
            'rank': 4,
            'test_data_count': 3,
            'test_rmse': 2.0,
            'training_data_count': 4,
            'validation_data_count': 3,
            'validation_rmse': 2.0,
        }
        return metadata

    @classmethod
    def upload_test_listen_to_hdfs(cls, listens_path):

        with open(cls.path_to_data_file('listens.json')) as f:
            data = json.load(f)

        listens_df = None
        for row in data:
            row['listened_at'] = datetime.strptime(row['listened_at'], '%d-%m-%Y')
            df = utils.create_dataframe(schema.convert_to_spark_json(row), schema=schema.listen_schema)
            listens_df = listens_df.union(df) if listens_df else df

        utils.save_parquet(listens_df, listens_path + '/{}/{}.parquet'.format(cls.date.year, cls.date.month))

    @classmethod
    def upload_test_mapping_to_hdfs(cls, mapping_path):
        with open(cls.path_to_data_file('msid_mbid_mapping.json')) as f:
            data = json.load(f)

        mapping_df = None
        for row in data:
            df = utils.create_dataframe(schema.convert_mapping_to_row(row), schema=schema.msid_mbid_mapping_schema)
            mapping_df = mapping_df.union(df) if mapping_df else df

        utils.save_parquet(mapping_df, mapping_path)

    @classmethod
    def upload_test_mapped_listens_to_hdfs(cls, listens_path, mapping_path, mapped_listens_path):
        partial_listen_df = dataframe_utils.get_listens_for_training_model_window(cls.date, cls.date, listens_path)
        df = utils.read_files_from_HDFS(mapping_path)
        mapping_df = mapping_utils.get_unique_rows_from_mapping(df)

        mapped_listens_df = dataframe_utils.get_mapped_artist_and_recording_mbids(partial_listen_df, mapping_df)
        save_dataframe(mapped_listens_df, mapped_listens_path)
