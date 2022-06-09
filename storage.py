from google.cloud import storage
import os

def bucket(fileobject, filename, readers=[], owners=[]):
    print('Uploading object..')
    bucket = os.environ["BUCKET"]
    url = os.environ["URL"]
    upload_object(bucket, url, fileobject, filename, readers, owners)
    #print(json.dumps(resp, indent=2))

    #print('Fetching object..')
    #with tempfile.TemporaryFile(mode='w+b') as tmpfile:
    #    get_object(bucket, filename, out_file=tmpfile)

    #print('Deleting object..')
    #resp = delete_object(bucket, filename)
    #if resp:
    #    print(json.dumps(resp, indent=2))
    print('Done')


def create_service():
    # Construct the service object for interacting with the Cloud Storage API -
    # the 'storage' service, at version 'v1'.
    # You can browse other available api services and versions here:
    #     http://g.co/dv/api-client-library/python/apis/
    return storage.Client()


def upload_object(bucket, url, fileobject, filename, readers, owners):
    client = create_service()

    # https://console.cloud.google.com/storage/browser/[bucket-id]/
    bucket = client.get_bucket(bucket)
    # Then do other things...
    #blob = bucket.get_blob('remote/path/to/file.txt')
    #print(blob.download_as_bytes())
    #blob.upload_from_string('New contents!')
    blob2 = bucket.blob(url+filename)
    blob2.upload_from_string(fileobject.getvalue(),content_type='text/csv')
