"""Exercise the real HTTP API against a temporary SQLite database.

Run from any directory: python3 tests/api_integration.py
The .NET 10 SDK must be on PATH (or set DOTNET to its executable).
"""

import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "aspnetcore-student-results"
DOTNET = os.environ.get("DOTNET") or shutil.which("dotnet")


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DOTNET:
            raise RuntimeError("Install the .NET 10 SDK or set DOTNET to the dotnet executable.")
        subprocess.run([DOTNET, "build", str(PROJECT), "-c", "Release", "--nologo"], check=True)
        cls.temp = tempfile.TemporaryDirectory()
        cls.temp_path = Path(cls.temp.name)
        cls.process = None
        with socket.socket() as connection:
            connection.bind(("127.0.0.1", 0))
            cls.port = connection.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.start_server()

    @classmethod
    def start_server(cls):
        cls.log = (cls.temp_path / "server.log").open("a", encoding="utf-8")
        environment = {
            **os.environ,
            "ASPNETCORE_URLS": cls.base,
            "ASPNETCORE_ENVIRONMENT": "Production",
            "ConnectionStrings__Results": f"Data Source={cls.temp_path / 'results.db'};Default Timeout=10",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        }
        cls.process = subprocess.Popen(
            [DOTNET, str(PROJECT / "bin/Release/net10.0/StudentResults.Api.dll")],
            cwd=PROJECT, env=environment, stdout=cls.log, stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if cls.process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(cls.base + "/health", timeout=1) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        cls.stop_server()
        raise RuntimeError((cls.temp_path / "server.log").read_text(encoding="utf-8")[-4000:])

    @classmethod
    def stop_server(cls):
        if cls.process is not None and cls.process.poll() is None:
            cls.process.terminate()
            try:
                cls.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.process.kill()
                cls.process.wait(timeout=5)
        cls.log.close()

    @classmethod
    def tearDownClass(cls):
        cls.stop_server()
        cls.temp.cleanup()

    @classmethod
    def request(cls, method, path, data=None):
        body = None if data is None else json.dumps(data).encode("utf-8")
        headers = {} if body is None else {"Content-Type": "application/json"}
        request = urllib.request.Request(cls.base + path, data=body, headers=headers, method=method)
        try:
            response = urllib.request.urlopen(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None, response.headers

    def setUp(self):
        _, page, _ = self.request("GET", "/api/results?pageSize=100")
        for row in page["items"]:
            self.request("DELETE", f"/api/results/{row['id']}")

    def create(self, student="STU001", subject="Mathematics", score=75):
        return self.request("POST", "/api/results", {
            "studentId": student, "subject": subject, "score": score,
        })

    def test_create_read_update_delete(self):
        status, created, headers = self.create()
        self.assertEqual(status, 201)
        location = headers["Location"]
        self.assertEqual(created["studentId"], "STU001")
        self.assertTrue(created["passed"])
        self.assertNotIn("subjectKey", created)
        self.assertEqual(self.request("GET", location)[1], created)
        status, updated, _ = self.request("PUT", location, {
            "studentId": "STU001", "subject": "Mathematics", "score": 40,
        })
        self.assertEqual(status, 200)
        self.assertFalse(updated["passed"])
        self.assertEqual(updated["createdAtUtc"], created["createdAtUtc"])
        self.assertEqual(self.request("DELETE", location)[0], 204)
        self.assertEqual(self.request("GET", location)[0], 404)

    def test_invalid_scores_and_missing_fields(self):
        for score in (-1, 101, None, 45.5, True, "75"):
            with self.subTest(score=score):
                self.assertEqual(self.create(score=score)[0], 400)
        self.assertEqual(self.request("POST", "/api/results", {})[0], 400)
        self.assertEqual(self.request("GET", "/api/results")[1]["total"], 0)

    def test_invalid_identifiers_and_subjects(self):
        for student, subject in [("", "Math"), ("bad id", "Math"), ("A" * 33, "Math"), ("STU1", " "), ("STU1", "A" * 81)]:
            with self.subTest(student=student, subject=subject):
                self.assertEqual(self.create(student, subject)[0], 400)

    def test_duplicate_keys_are_normalised(self):
        self.assertEqual(self.create(" stu001 ", " Mathematics ")[0], 201)
        self.assertEqual(self.create("STU001", "mathematics")[0], 409)
        page = self.request("GET", "/api/results?studentId=stu001&subject=MATHEMATICS")[1]
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["items"][0]["subject"], "Mathematics")

    def test_conflicting_update_does_not_change_existing_row(self):
        _, first, _ = self.create("S1", "Math", 60)
        _, second, _ = self.create("S1", "Science", 70)
        self.assertEqual(self.request("PUT", f"/api/results/{second['id']}", {
            "studentId": "S1", "subject": "math", "score": 90,
        })[0], 409)
        self.assertEqual(self.request("GET", f"/api/results/{second['id']}")[1]["score"], 70)
        self.assertEqual(self.request("GET", f"/api/results/{first['id']}")[1]["score"], 60)

    def test_summary_and_pass_boundary(self):
        self.create("S1", "Math", 0)
        self.create("S2", "math", 50)
        self.create("S1", "Science", 100)
        status, summary, _ = self.request("GET", "/api/results/summary")
        self.assertEqual(status, 200)
        self.assertEqual(summary["totalResults"], 3)
        self.assertEqual(summary["totalStudents"], 2)
        self.assertEqual(summary["averageScore"], 50)
        self.assertEqual(summary["passedResults"], 2)
        self.assertEqual(summary["failedResults"], 1)
        self.assertEqual(summary["passRatePercent"], 66.67)
        self.assertEqual(len(summary["bySubject"]), 2)

    def test_empty_summary_has_no_fabricated_average(self):
        summary = self.request("GET", "/api/results/summary")[1]
        self.assertEqual(summary["totalResults"], 0)
        self.assertIsNone(summary["averageScore"])
        self.assertIsNone(summary["passRatePercent"])
        self.assertEqual(summary["bySubject"], [])

    def test_pagination_and_summary_filters(self):
        self.create("S1", "Math", 40)
        self.create("S2", "Math", 80)
        self.create("S3", "Science", 90)
        page = self.request("GET", "/api/results?page=2&pageSize=1")[1]
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["items"][0]["studentId"], "S2")
        summary = self.request("GET", "/api/results/summary?subject=math")[1]
        self.assertEqual(summary["totalResults"], 2)
        self.assertEqual(summary["averageScore"], 60)

    def test_pagination_limits(self):
        for query in ("page=0", "page=-1", "page=1000001", "pageSize=0", "pageSize=101"):
            with self.subTest(query=query):
                self.assertEqual(self.request("GET", "/api/results?" + query)[0], 400)

    def test_missing_updates_and_deletes_return_404(self):
        self.assertEqual(self.request("PUT", "/api/results/999999", {
            "studentId": "S1", "subject": "Math", "score": 60,
        })[0], 404)
        self.assertEqual(self.request("DELETE", "/api/results/999999")[0], 404)

    def test_concurrent_duplicates_produce_one_record(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(lambda _: self.create("CONCURRENT", "Math")[0], range(6)))
        self.assertEqual(sorted(statuses), [201, 409, 409, 409, 409, 409])
        self.assertEqual(self.request("GET", "/api/results")[1]["total"], 1)

    def test_data_survives_a_process_restart(self):
        _, row, _ = self.create("PERSIST", "Math", 88)
        self.stop_server()
        self.start_server()
        self.assertEqual(self.request("GET", f"/api/results/{row['id']}")[1]["score"], 88)


if __name__ == "__main__":
    unittest.main(verbosity=2)
