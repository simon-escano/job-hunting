import os
from engine.db import supabase

def upload_pdf(local_path: str, remote_filename: str) -> str:
    bucket_name = "resumes"
    with open(local_path, "rb") as f:
        supabase.storage.from_(bucket_name).upload(
            file=f,
            path=remote_filename,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
    return get_public_url(remote_filename)

def get_public_url(remote_filename: str) -> str:
    bucket_name = "resumes"
    res = supabase.storage.from_(bucket_name).get_public_url(remote_filename)
    return res
