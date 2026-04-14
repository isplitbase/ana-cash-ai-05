from __future__ import annotations

import os
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple
from zoneinfo import ZoneInfo

import google.auth
import google.auth.transport.requests
from google.cloud import storage as gcs_storage


JST = ZoneInfo("Asia/Tokyo")


def make_timestamp_jst() -> str:
    return datetime.now(JST).strftime("%Y%m%d%H%M%S")


def make_random_token(n: int = 15) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def get_expires_in_seconds(payload: Dict[str, Any], default_seconds: int = 3600) -> int:
    """
    署名付きURLのExpires（秒）を取得。
    payload.expires_sec / payload.expires を優先し、未指定なら default_seconds。
    GCS v4 署名URLの上限（7日）を超える値は 604800 秒に丸める。
    """
    raw = payload.get("expires_sec", None)
    if raw is None:
        raw = payload.get("expires", None)

    try:
        seconds = int(raw) if raw is not None else int(default_seconds)
    except Exception:
        seconds = int(default_seconds)

    if seconds <= 0:
        seconds = int(default_seconds)

    # 7 days cap for signed URL
    return min(seconds, 604800)


def get_gcs_bucket(payload: Dict[str, Any]) -> str:
    """
    GCS バケット名を payload か環境変数から取得する。
    """
    bucket = str(payload.get("gcs_bucket") or os.environ.get("GCS_BUCKET") or "").strip()
    if not bucket:
        raise ValueError(
            "GCS bucket が未指定です。payload.gcs_bucket か環境変数 GCS_BUCKET を指定してください。"
        )
    return bucket


def make_gcs_key(ai_case_id: Any, filename: str, prefix: str = "cash-ai-05") -> str:
    """
    GCS オブジェクトキーを生成する。
    仕様: cash-ai-05/<ai_case_id>/<filename>
    """
    case = str(ai_case_id).strip() if ai_case_id is not None else "unknown"
    return f"{prefix}/{case}/{filename}"


def upload_html_and_presign(
    local_html_path: Path,
    bucket_name: str,
    key: str,
    expires_in: int,
) -> Tuple[str, str]:
    """
    HTMLファイルをGCSへアップロードし、署名付きURLを返す。
    戻り値: (key, presigned_url)

    Cloud Run ADC（Application Default Credentials）対応：
    - JSONキーファイル不要
    - IAM SignBlob API 経由で署名付きURL生成
    - Cloud Runのサービスアカウントに roles/iam.serviceAccountTokenCreator が必要
    """
    # ADC で認証情報を取得・更新（Cloud Run では Compute Engine credentials が使われる）
    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    client = gcs_storage.Client(credentials=credentials, project=project)
    blob = client.bucket(bucket_name).blob(key)
    blob.upload_from_filename(
        str(local_html_path),
        content_type="text/html; charset=utf-8",
    )

    # IAM SignBlob API 経由で署名付きURL生成（秘密鍵不要）
    presigned = blob.generate_signed_url(
        expiration=timedelta(seconds=expires_in),
        method="GET",
        version="v4",
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )
    return key, presigned
