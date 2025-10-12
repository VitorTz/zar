from botocore.config import Config
from dotenv import load_dotenv
from pathlib import Path
import aioboto3
import os


load_dotenv()


SESSION = aioboto3.Session()


R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PREFIX = os.getenv("R2_PREFIX")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"


class S3Exception(Exception):

    def __init__(self, message: str):
        super().__init__(f"[S3 EXCEPTION] => {message}")


class S3:

    def __init__(self, bucket_name: str = R2_BUCKET_NAME, prefix: str = R2_PREFIX):
        self.__bucket_name = bucket_name
        self.__prefix = prefix
        self.__session = SESSION
        
    async def upload_qrcode(self, file: Path, url_id: str) -> str:
        if not file.exists() or not file.is_file():
            raise S3Exception(f"[{file} IS NOT A FILE OR NOT EXISTS]")
        name = f"zar/qrcode/{url_id}.png"
        async with self.__session.client(
            service_name="s3",
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="enam"
        ) as s3:
            await s3.upload_file(file, self.__bucket_name, name)
            return self.__prefix + name
