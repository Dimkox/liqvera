"""Build and inspect the three Stage A wheels."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

from tools.conformance.runner import ConformanceError, require_clean_exact_head

DISTRIBUTIONS: tuple[tuple[str, Path], ...] = (
    ("liqvera-contracts", Path("packages/contracts")),
    ("liqvera-public-capture", Path("packages/public-capture")),
    ("liqvera-readonly-analyzer", Path("packages/readonly-analyzer")),
)

ALLOWED_NAMESPACES: dict[str, frozenset[str]] = {
    "liqvera-contracts": frozenset({"liqvera_contracts"}),
    "liqvera-public-capture": frozenset({"liqvera_contracts", "liqvera_public_capture"}),
    "liqvera-readonly-analyzer": frozenset({"liqvera_contracts", "liqvera_readonly_analyzer"}),
}

FORBIDDEN_SHARED: frozenset[str] = frozenset({"liqvera"})


@dataclass(frozen=True, slots=True)
class BuiltArtifact:
    distribution: str
    path: Path
    sha256: str


@dataclass(frozen=True, slots=True)
class InstalledDistribution:
    distribution: str
    namespaces: frozenset[str]
    files: tuple[str, ...]
    dependencies: tuple[str, ...]
    entry_points: tuple[str, ...]


def build_all(
    source_sha: str,
    output: Path,
    *,
    root: Path | None = None,
    require_clean: bool = True,
) -> tuple[BuiltArtifact, ...]:
    repository = (root or Path.cwd()).resolve()
    output = output.resolve()
    if require_clean:
        require_clean_exact_head(source_sha, repository)
    output.mkdir(parents=True, exist_ok=True)
    # Resolve into a fresh wheelhouse. Existing higher-version dependencies
    # must never override the audited lock after a branch switch or downgrade.
    with tempfile.TemporaryDirectory(prefix=".wheelhouse-", dir=output) as temporary:
        staging = Path(temporary)
        built = tuple(
            _build_wheel(repository / package, staging, name)
            for name, package in DISTRIBUTIONS
        )
        _download_pinned_wheels(staging, repository)
        wheels = tuple(staging.glob("*.whl"))
        published_names = {wheel.name for wheel in wheels}
        for wheel in wheels:
            wheel.replace(output / wheel.name)
        for stale in output.glob("*.whl"):
            if stale.name not in published_names:
                stale.unlink()
        return tuple(
            BuiltArtifact(item.distribution, output / item.path.name, item.sha256)
            for item in built
        )


def inspect_installed(python: Path, distribution: str) -> InstalledDistribution:
    payload = _probe(python, distribution)
    files = tuple(payload["files"])
    return InstalledDistribution(
        distribution=distribution,
        namespaces=_environment_namespaces(python),
        files=files,
        dependencies=tuple(payload["requires"]),
        entry_points=tuple(payload["entry_points"]),
    )


def install_one(python: Path, wheels: Path, distribution: str) -> InstalledDistribution:
    command = [
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-cache-dir",
        "--no-index",
        "--find-links",
        str(wheels),
        distribution,
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise ConformanceError(completed.stderr or completed.stdout or "pip install failed")
    return inspect_installed(python, distribution)


def make_venv(path: Path) -> Path:
    venv.create(path, with_pip=True, clear=True)
    python = path / "bin" / "python"
    if not python.exists():
        python = path / "Scripts" / "python.exe"
    if not python.exists():
        raise ConformanceError(f"venv python missing at {path}")
    return python


def _build_wheel(package: Path, output: Path, distribution: str) -> BuiltArtifact:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hatchling",
            "build",
            "--target",
            "wheel",
            "--directory",
            str(output),
        ],
        cwd=package,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ConformanceError(completed.stderr or completed.stdout or "wheel build failed")
    matching = [
        item for item in output.glob("*.whl") if _wheel_name_matches(item.name, distribution)
    ]
    if not matching:
        raise ConformanceError(f"expected one wheel for {distribution}, got {matching}")
    wheel = max(matching, key=lambda item: item.stat().st_mtime_ns)
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    return BuiltArtifact(distribution, wheel, digest)


def _environment_namespaces(python: Path) -> frozenset[str]:
    script = r"""
import json, sysconfig
from pathlib import Path
root = Path(sysconfig.get_path("purelib"))
names = []
for item in root.iterdir():
    name = item.name
    if name.endswith(".dist-info") or name.endswith(".data"):
        continue
    if item.is_dir() and (name.startswith("liqvera_") or name == "liqvera"):
        names.append(name)
    elif name.endswith(".py") and name.startswith("liqvera_"):
        names.append(name[:-3])
print(json.dumps(names))
"""
    completed = subprocess.run(
        [str(python), "-I", "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ConformanceError(completed.stderr or "namespace probe failed")
    names = json.loads(completed.stdout)
    return frozenset(str(item) for item in names)


def _wheel_name_matches(filename: str, distribution: str) -> bool:
    prefix = distribution.replace("-", "_") + "-"
    return filename.startswith(prefix) and filename.endswith(".whl")


def _download_pinned_wheels(output: Path, repository: Path) -> None:
    commands = (
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--dest",
            str(output),
            "--only-binary=:all:",
            "-r",
            str(repository / "requirements.lock"),
        ],
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--dest",
            str(output),
            "--only-binary=:all:",
            "--python-version",
            "312",
            "--implementation",
            "cp",
            "--abi",
            "cp312",
            "--platform",
            "musllinux_1_2_x86_64",
            "-r",
            str(repository / "requirements.lock"),
        ],
    )
    for command in commands:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise ConformanceError(completed.stderr or "pinned wheel download failed")


def _probe(python: Path, distribution: str) -> dict[str, object]:
    script = r"""
import importlib.metadata
import json
import sys

name = sys.argv[1]
dist = importlib.metadata.distribution(name)
requires = tuple(str(item) for item in (dist.requires or ()))
top_level = []
text = dist.read_text("top_level.txt")
if text:
    top_level = [line.strip() for line in text.splitlines() if line.strip()]
files = [str(item) for item in (dist.files or ()) if str(item).endswith(".py")]
entries = []
eps = importlib.metadata.entry_points()
select = eps.select(group="console_scripts") if hasattr(eps, "select") else eps.get("console_scripts", [])
for item in select:
    if item.dist is not None and item.dist.name == name:
        entries.append(item.name)
print(json.dumps({"requires": requires, "top_level": top_level, "files": files, "entry_points": entries}))
"""
    completed = subprocess.run(
        [str(python), "-I", "-c", script, distribution],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ConformanceError(completed.stderr or "installed distribution probe failed")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ConformanceError("probe returned a non-object")
    return payload
