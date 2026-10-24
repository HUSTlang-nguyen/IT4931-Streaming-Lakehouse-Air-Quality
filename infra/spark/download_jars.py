"""Build dependency Java từ Maven Central, pin version và kiểm checksum nguồn.

Kafka POM 3.5.6 yêu cầu token provider, Kafka3.4.1, pool2; jsr305/tags/Hadoop
đã có trong PySpark nên không chép thêm version xung đột. SHA-256 bản tải được
lưu trong image để xuất thành lock sau kiểm chứng. Runtime không tải Maven nữa.
"""

import hashlib
import json
import time
from pathlib import Path
from urllib.request import urlopen

import pyspark


COORDINATES = [
    ("org.apache.iceberg", "iceberg-spark-runtime-3.5_2.12", "1.9.2"),
    ("org.apache.iceberg", "iceberg-aws-bundle", "1.9.2"),
    ("org.apache.spark", "spark-sql-kafka-0-10_2.12", "3.5.6"),
    ("org.apache.spark", "spark-token-provider-kafka-0-10_2.12", "3.5.6"),
    ("org.apache.kafka", "kafka-clients", "3.4.1"),
    ("org.apache.commons", "commons-pool2", "2.11.1"),
]


def install_jars() -> None:
    """Tải có retry hữu hạn; chỉ đặt file vào Spark jars sau checksum hợp lệ."""
    destination = Path(pyspark.__file__).parent / "jars"
    locked = {item["artifact"]: item["sha256"] for item in json.loads(Path("/tmp/java-artifacts.lock.json").read_text())}
    records = []
    for group, artifact, version in COORDINATES:
        filename = f"{artifact}-{version}.jar"
        url = f"https://repo.maven.apache.org/maven2/{group.replace('.', '/')}/{artifact}/{version}/{filename}"
        for attempt in range(3):
            try:
                with urlopen(url, timeout=180) as response:
                    content = response.read()
                with urlopen(url + ".sha1", timeout=30) as response:
                    expected = response.read().decode().split()[0]
                if hashlib.sha1(content).hexdigest() != expected:
                    raise ValueError(f"Maven checksum mismatch: {filename}")
                coordinate = f"{group}:{artifact}:{version}"
                if hashlib.sha256(content).hexdigest() != locked[coordinate]:
                    raise ValueError(f"Pinned SHA-256 mismatch: {filename}")
                (destination / filename).write_bytes(content)
                records.append({"artifact": f"{group}:{artifact}:{version}", "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
                print(f"Installed {filename}", flush=True)
                break
            except (OSError, ValueError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    Path("/opt/java-artifacts.lock.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    install_jars()
